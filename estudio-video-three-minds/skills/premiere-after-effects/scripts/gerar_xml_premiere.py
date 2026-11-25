#!/usr/bin/env python3
"""Gera um XML (Final Cut Pro 7 / xmeml v4) importável no Premiere Pro a partir da lista de cortes CSV.

CSV: trilha,midia,inicio,duracao,posicao,ganho,escala  (ver adobe-criativo/scripts/lista_para_timeline.py)
  - midia = nome do arquivo (ex.: plano01.mp4). Com --pasta, vira caminho completo.
Uso:
  python3 gerar_xml_premiere.py cortes.csv --formato 9:16 --fps 30 --pasta "/Users/eu/Midia" --nome SEQ > seq.xml
  Marcadores opcionais: --marcadores "0:Gancho,12.5:Virada,40:Título"
"""
import argparse, csv, sys
from pathlib import PurePosixPath, PureWindowsPath
from urllib.parse import quote
from xml.sax.saxutils import escape

FORMATOS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "4:5": (1080, 1350), "1:1": (1080, 1080)}


def seg(v, padrao=None, linha=None, campo="valor"):
    v = (v or "").strip().replace(",", ".")
    if not v:
        return padrao
    try:
        return float(v)
    except ValueError:
        sys.exit(f"linha {linha}: {campo} '{v}' não é número")


def pathurl(pasta, nome):
    if not pasta:
        return "file://localhost/" + quote(nome)
    if "\\" in pasta or (len(pasta) > 1 and pasta[1] == ":"):
        p = PureWindowsPath(pasta) / nome
        return "file://localhost/" + quote(p.as_posix())
    return "file://localhost" + quote(str(PurePosixPath(pasta) / nome))


def rate(fps):
    return f"<rate><timebase>{fps}</timebase><ntsc>FALSE</ntsc></rate>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--formato", default="9:16", choices=FORMATOS)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--pasta", default="")
    ap.add_argument("--nome", default="Sequencia Three Minds")
    ap.add_argument("--marcadores", default="")
    a = ap.parse_args()
    if a.fps <= 0:
        ap.error("--fps deve ser positivo")
    fps = a.fps
    fr = lambda s: int(round(s * fps))
    w, h = FORMATOS[a.formato]

    linhas, cursor = [], {}
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            t = (row.get("trilha") or "principal").strip().lower()
            if t not in ("principal", "sobreposicao", "audio"):
                sys.exit(f"linha {i}: trilha '{t}' inválida (use principal, sobreposicao ou audio)")
            m = (row.get("midia") or "").strip()
            if not m:
                sys.exit(f"linha {i}: coluna midia vazia")
            dur = seg(row.get("duracao"), None, i, "duração")
            if not dur or dur <= 0:
                sys.exit(f"linha {i}: duração inválida")
            ini = seg(row.get("inicio"), 0.0, i, "início")
            pos = seg(row.get("posicao"), cursor.get(t, 0.0), i, "posição")
            if ini < 0 or pos < 0:
                sys.exit(f"linha {i}: início e posição devem ser não negativos")
            g = seg(row.get("ganho"), 1.0, i, "ganho")
            if not 0 <= g <= 2:
                sys.exit(f"linha {i}: ganho deve ficar entre 0 e 2")
            cursor[t] = pos + dur
            linhas.append({"linha": i, "t": t, "m": m, "ini": ini, "dur": dur, "pos": pos, "g": g})
    if not linhas:
        sys.exit("A lista de cortes não contém clipes.")
    for t in ("principal", "sobreposicao", "audio"):
        xs = sorted((l for l in linhas if l["t"] == t), key=lambda l: l["pos"])
        for x, y in zip(xs, xs[1:]):
            if fr(x["pos"] + x["dur"]) > fr(y["pos"]):
                sys.exit(f"trilha {t}: linha {y['linha']} começa antes do fim da linha {x['linha']} — clipes não podem se sobrepor")

    # Ordem de emissão no XML: vídeo (principal, sobreposição) e depois áudio (principal, audio).
    # Cada <file> é declarado por completo no PRIMEIRO uso emitido; depois, só referência.
    arquivos, declarados = {}, set()

    def file_el(m):
        fid = arquivos.setdefault(m, f"file-{len(arquivos)+1}")
        if fid in declarados:
            return f'<file id="{fid}"/>'
        declarados.add(fid)
        return (f'<file id="{fid}"><name>{escape(m)}</name><pathurl>{escape(pathurl(a.pasta, m))}</pathurl>'
                f'{rate(fps)}<media><video/><audio/></media></file>')

    def base(l):
        return (f"<name>{escape(l['m'])}</name><enabled>TRUE</enabled>{rate(fps)}"
                f"<start>{fr(l['pos'])}</start><end>{fr(l['pos'] + l['dur'])}</end>"
                f"<in>{fr(l['ini'])}</in><out>{fr(l['ini'] + l['dur'])}</out>")

    def link(ref, tipo, trilha, idx):
        return (f"<link><linkclipref>{ref}</linkclipref><mediatype>{tipo}</mediatype>"
                f"<trackindex>{trilha}</trackindex><clipindex>{idx}</clipindex></link>")

    vt_ordem = [t for t in ("principal", "sobreposicao") if any(l["t"] == t for l in linhas)]
    at_ordem = [t for t in ("principal", "audio") if any(l["t"] == t for l in linhas)]
    trilhas = {("v", t): sorted([l for l in linhas if l["t"] == t], key=lambda l: l["pos"]) for t in vt_ordem}
    trilhas.update({("a", t): sorted([l for l in linhas if l["t"] == t], key=lambda l: l["pos"]) for t in at_ordem})
    # índices (trilha, posição) para os links vídeo↔áudio dos clipes da trilha principal
    vidx = {id(l): (vt_ordem.index("principal") + 1, k + 1) for k, l in enumerate(trilhas.get(("v", "principal"), []))}
    aidx = {id(l): (at_ordem.index("principal") + 1, k + 1) for k, l in enumerate(trilhas.get(("a", "principal"), []))}

    vt = ""
    for t in vt_ordem:
        itens = []
        for l in trilhas[("v", t)]:
            n = l["linha"]
            links = ""
            if t == "principal":
                links = link(f"v{n}", "video", *vidx[id(l)]) + link(f"a{n}", "audio", *aidx[id(l)])
            itens.append(f'<clipitem id="v{n}">{base(l)}{file_el(l["m"])}{links}</clipitem>')
        vt += f"<track>{''.join(itens)}</track>"
    at = ""
    for t in at_ordem:
        itens = []
        for l in trilhas[("a", t)]:
            n = l["linha"]
            nivel = (f"<filter><effect><name>Audio Levels</name><effectid>audiolevels</effectid><effecttype>audiolevels</effecttype>"
                     f"<mediatype>audio</mediatype><parameter><parameterid>level</parameterid><name>Level</name>"
                     f"<value>{l['g']:.3f}</value></parameter></effect></filter>")
            links = ""
            if t == "principal":
                links = link(f"v{n}", "video", *vidx[id(l)]) + link(f"a{n}", "audio", *aidx[id(l)])
            itens.append(f'<clipitem id="a{n}">{base(l)}{file_el(l["m"])}'
                         f'<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>{nivel}{links}</clipitem>')
        at += f"<track>{''.join(itens)}</track>"

    duracao = max(l["pos"] + l["dur"] for l in linhas)
    marc = ""
    for item in filter(None, (x.strip() for x in a.marcadores.split(","))):
        tempo, _, nome = item.partition(":")
        t = seg(tempo, None, "--marcadores", "tempo do marcador")
        if t is None or not nome.strip():
            sys.exit(f"marcador '{item}' inválido; use segundos:nome, ex.: 12.5:Virada")
        marc += f"<marker><name>{escape(nome.strip())}</name><in>{fr(t)}</in><out>-1</out></marker>"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
<sequence id="seq-1">
<name>{escape(a.nome)}</name>
<duration>{fr(duracao)}</duration>
{rate(fps)}
{marc}
<media>
<video><format><samplecharacteristics>{rate(fps)}<width>{w}</width><height>{h}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>{vt}</video>
<audio>{at}</audio>
</media>
</sequence>
</xmeml>
"""
    sys.stdout.write(xml)


if __name__ == "__main__":
    main()
