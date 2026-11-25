#!/usr/bin/env python3
"""Converte uma lista de cortes (CSV) no documento de timeline do video_render da Adobe.

CSV (cabeçalho obrigatório):
  trilha,midia,inicio,duracao,posicao,ganho,escala
  - trilha: principal | sobreposicao | audio
  - midia: nome/apelido da mídia (a ordem de primeira aparição define o mediaIndex)
  - inicio/duracao/posicao: segundos (aceita 2.5 ou 2,5). posicao vazia = logo após o clipe anterior da mesma trilha
  - ganho: 0 a 2 (vazio = 1; use 0 para silenciar o áudio do clipe)
  - escala: fill | fit (vazio = fill)

Uso:
  python3 lista_para_timeline.py cortes.csv --formato 9:16 --fps 30 \
      --ids midias.json > timeline.json
  midias.json (opcional): {"apelido": "urn:aaid:sc:..."} para preencher assetIds.
  --duracoes duracoes.json (opcional): {"apelido": segundos} lidos do video_metadata; o script
      recusa cortes que passem do fim da mídia.

Validações: trilha, números, escala, ganho, sobreposição de clipes na mesma trilha, limite de 10 min.
Tempos são alinhados ao quadro (--fps) para evitar cortes no meio de um frame.
"""
import argparse, csv, json, sys
from fractions import Fraction

FORMATOS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "4:5": (1080, 1350), "1:1": (1080, 1080)}
TIPOS = {"principal": "video-audio", "sobreposicao": "video", "audio": "audio"}


def num(v, padrao=None, linha=None, campo="valor"):
    v = (v or "").strip().replace(",", ".")
    if not v:
        return padrao
    try:
        return Fraction(v)
    except (ValueError, ZeroDivisionError):
        sys.exit(f"linha {linha}: {campo} '{v}' não é número (use segundos, ex.: 2.5)")


FPS = 30


def rac(x: Fraction):
    """Racional alinhado ao quadro: n/(fps) — o video_render aceita qualquer denominador."""
    q = round(Fraction(x) * FPS)
    return {"n": int(q), "d": FPS}


def seg(r):
    return Fraction(r["n"], r["d"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--formato", default="9:16", choices=FORMATOS)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--ids", help="JSON apelido -> assetId")
    ap.add_argument("--duracoes", help="JSON apelido -> duração em segundos (de video_metadata)")
    a = ap.parse_args()
    if a.fps <= 0:
        ap.error("--fps deve ser positivo")
    global FPS
    FPS = a.fps

    ids = json.load(open(a.ids, encoding="utf-8")) if a.ids else {}
    duracoes = json.load(open(a.duracoes, encoding="utf-8")) if a.duracoes else {}
    midias, trilhas, cursor = [], {}, {}
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            t = (row.get("trilha") or "principal").strip().lower()
            if t not in TIPOS:
                sys.exit(f"linha {i}: trilha '{t}' inválida (use principal, sobreposicao ou audio)")
            m = (row.get("midia") or "").strip()
            if not m:
                sys.exit(f"linha {i}: coluna midia vazia")
            if m not in midias:
                midias.append(m)
            dur = num(row.get("duracao"), None, i, "duração")
            if not dur or dur <= 0:
                sys.exit(f"linha {i}: duração inválida")
            pos = num(row.get("posicao"), cursor.get(t, Fraction(0)), i, "posição")
            inicio = num(row.get("inicio"), Fraction(0), i, "início")
            if inicio < 0 or pos < 0:
                sys.exit(f"linha {i}: início e posição devem ser não negativos")
            if rac(dur)["n"] == 0:
                sys.exit(f"linha {i}: duração menor que 1 quadro")
            if m in duracoes and inicio + dur > Fraction(str(duracoes[m])) + Fraction(1, 1000):
                sys.exit(f"linha {i}: corte {float(inicio):.3f}+{float(dur):.3f}s passa do fim de {m} ({duracoes[m]}s)")
            ganho = float(num(row.get("ganho"), Fraction(1), i, "ganho"))
            if not 0 <= ganho <= 2:
                sys.exit(f"linha {i}: ganho deve ficar entre 0 e 2")
            clip = {
                "mediaIndex": midias.index(m),
                "sourceStart": rac(inicio),
                "sourceDuration": rac(dur),
                "editStart": rac(pos),
            }
            if t != "audio":
                esc = (row.get("escala") or "fill").strip().lower()
                if esc not in ("fill", "fit"):
                    sys.exit(f"linha {i}: escala '{esc}' inválida (use fill ou fit)")
                clip["visualTransform"] = {"mode": "simple", "scale": esc, "rotateDegrees": 0}
            if t != "sobreposicao":
                clip["audioTransform"] = {"gain": ganho}
            clip["_linha"] = i
            trilhas.setdefault(t, []).append(clip)
            cursor[t] = pos + dur

    if not trilhas:
        sys.exit("A lista de cortes não contém clipes.")
    for t, clips in trilhas.items():
        clips.sort(key=lambda c: seg(c["editStart"]))
        for x, y in zip(clips, clips[1:]):
            if seg(x["editStart"]) + seg(x["sourceDuration"]) > seg(y["editStart"]):
                sys.exit(f"trilha {t}: clipe da linha {y['_linha']} começa antes do fim do clipe da linha {x['_linha']} "
                         "(clipes de uma trilha não podem se sobrepor; use a trilha sobreposicao)")
        for c in clips:
            del c["_linha"]
    faltam = [m for m in midias if m not in ids]
    if ids and faltam:
        print(f"aviso: sem assetId para {', '.join(faltam)} — preencha antes do video_render", file=sys.stderr)
    w, h = FORMATOS[a.formato]
    ordem = [t for t in ("principal", "sobreposicao", "audio") if t in trilhas]
    doc = {
        "version": 1, "width": w, "height": h,
        "framerate": {"n": a.fps, "d": 1},
        "tracks": [{"type": TIPOS[t], "clips": trilhas[t]} for t in ordem],
    }
    total = max(seg(c["editStart"]) + seg(c["sourceDuration"]) for t in trilhas.values() for c in t)
    if total > 600:
        sys.exit("timeline passa de 10 min — limite do video_render")
    saida = {"document": doc, "assetIds": [ids.get(m, f"<assetId de {m}>") for m in midias], "midias": midias,
             "duracao_total_s": float(total)}
    json.dump(saida, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
