#!/usr/bin/env python3
"""Ferramentas de edição do Estúdio de Vídeo Three Minds (ffmpeg).

Subcomandos: info, conferir, quadros, cortar, reenquadrar, srt, legendar, cartela, concatenar, audio, exportar.
Use `python3 video_tools.py COMANDO -h` para ajuda.
"""
import argparse, csv, json, math, os, re, shutil, subprocess, sys, tempfile, textwrap

FORMATOS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "4:5": (1080, 1350), "1:1": (1080, 1080)}
SIGLA = {"9:16": "VERT", "16:9": "HORIZ", "4:5": "FEED45", "1:1": "QUAD"}
ENC_V = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p"]
ENC_A = ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
FIM = ["-movflags", "+faststart"]
# Referência rápida para `conferir` (padroes-da-casa/references/especificacoes-plataformas.md).
# Durações máximas mudam: confira na web quando a peça estiver perto do limite.
PLATAFORMAS = {
    "reels":   {"formato": "9:16", "dur_max": 180},
    "tiktok":  {"formato": "9:16", "dur_max": 600},
    "shorts":  {"formato": "9:16", "dur_max": 180},
    "youtube": {"formato": "16:9", "dur_max": None},
    "feed":    {"formato": "4:5",  "dur_max": 60},
    "anuncio": {"formato": None,   "dur_max": 60},
}


def run(cmd, sair=True):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit(f"{cmd[0]} não encontrado no PATH.")
    if r.returncode != 0 and sair:
        sys.exit(f"{cmd[0]} falhou:\n" + r.stderr[-2000:])
    return r


def formato_valido(f):
    f = f.strip()
    if f not in FORMATOS:
        sys.exit(f"formato '{f}' inválido; use {', '.join(FORMATOS)}")
    return f


def fps_de(v):
    for campo in ("avg_frame_rate", "r_frame_rate"):
        n, _, den = (v.get(campo) or "0/0").partition("/")
        try:
            if int(den or 1) and int(n):
                return round(int(n) / int(den or 1), 3)
        except ValueError:
            pass
    return None


def dur_video(path):
    """Duração do fluxo de vídeo (cai para a do contêiner)."""
    d = probe(path)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    try:
        return float(v.get("duration") or d["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        sys.exit(f"não consegui ler a duração de {path}")


def probe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path]).stdout
    return json.loads(out)


def tem_audio(path):
    return any(s["codec_type"] == "audio" for s in probe(path)["streams"])


def num(v, padrao=None, campo="valor"):
    """Segundos: aceita 2.5, 2,5, 01:02.5, 00:01:02,500."""
    v = (v or "").strip()
    if not v:
        return padrao
    m = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:[.,]\d+)?)", v)
    try:
        if m:
            h, mi, s = m.groups()
            return int(h or 0) * 3600 + int(mi) * 60 + float(s.replace(",", "."))
        return float(v.replace(",", "."))
    except ValueError:
        sys.exit(f"{campo} inválido: '{v}' (use segundos, ex.: 2.5, ou mm:ss)")


def hexcor(h, alfa=None):
    h = h.lstrip("#")
    return f"0x{h}" + (f"@{alfa}" if alfa is not None else "")


def ass_cor(h):  # #RRGGBB -> &H00BBGGRR
    h = h.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ts(s):
    ms = int(round(s * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"


def fit_filter(w, h, modo):
    if modo == "crop":
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    return (f"split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=30:3,eq=brightness=-0.08[bg];"
            f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")


# ---------- comandos ----------

def c_info(a):
    d = probe(a.video)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    info = {"duracao_s": round(float(d["format"]["duration"]), 3)}
    if v:
        info.update(largura=v["width"], altura=v["height"], fps=fps_de(v))
    info["audio"] = tem_audio(a.video)
    if info["audio"]:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True)
        try:
            j, _ = json.JSONDecoder().raw_decode(r.stderr[r.stderr.rindex("{"):])
            for campo, chave in (("loudness_lufs", "input_i"), ("true_peak_db", "input_tp")):
                valor = float(j[chave])
                info[campo] = valor if math.isfinite(valor) else None
        except (ValueError, KeyError):
            pass
    print(json.dumps(info, ensure_ascii=False, indent=2))


def medir_loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    try:
        j, _ = json.JSONDecoder().raw_decode(r.stderr[r.stderr.rindex("{"):])
        i, tp = float(j["input_i"]), float(j["input_tp"])
        return (i if math.isfinite(i) else None), (tp if math.isfinite(tp) else None)
    except (ValueError, KeyError):
        return None, None


def c_conferir(a):
    """Confere o arquivo final contra o padrão da casa e devolve ok/alertas."""
    d = probe(a.video)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    alvo = PLATAFORMAS[a.plataforma]
    alertas, ok = [], []
    if not v:
        sys.exit("arquivo sem vídeo")
    w, h, fps = v["width"], v["height"], fps_de(v)
    dur = float(d["format"]["duration"])
    fmt = a.formato or alvo["formato"]
    if fmt:
        ew, eh = FORMATOS[fmt]
        (ok if (w, h) == (ew, eh) else alertas).append(f"resolução {w}x{h} (esperado {ew}x{eh} para {fmt})")
    if fps and not (23.9 <= fps <= 60.1):
        alertas.append(f"fps {fps} fora de 24–60")
    else:
        ok.append(f"fps {fps}")
    if v.get("codec_name") != "h264":
        alertas.append(f"codec de vídeo {v.get('codec_name')} (padrão da casa: H.264)")
    if v.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
        alertas.append(f"pix_fmt {v.get('pix_fmt')} — alguns apps recusam; use yuv420p")
    if alvo["dur_max"] and dur > alvo["dur_max"]:
        alertas.append(f"duração {dur:.1f}s acima de {alvo['dur_max']}s de referência — confira o limite atual na web")
    else:
        ok.append(f"duração {dur:.1f}s")
    if tem_audio(a.video):
        i, tp = medir_loudness(a.video)
        if i is None:
            alertas.append("áudio sem medição (silêncio?)")
        else:
            (ok if abs(i + 14) <= 1 else alertas).append(f"loudness {i:.1f} LUFS (alvo −14 ±1)")
            (ok if tp is not None and tp <= -1 else alertas).append(f"true peak {tp} dBTP (máx. −1)")
    else:
        alertas.append("sem faixa de áudio (redes tocam o vídeo mudo; confira se é intencional)")
    nome = os.path.basename(a.video)
    if not re.fullmatch(r"[A-Z0-9]+_[A-Z0-9-]+_[A-Z0-9-]+_[A-Z0-9-]+_v\d{2}\.(mp4|mov)", nome):
        alertas.append(f"nome '{nome}' fora do padrão SELO_TITULO-LIVRO_FORMATO_PLATAFORMA_vNN.mp4")
    print(json.dumps({"arquivo": a.video, "plataforma": a.plataforma, "ok": ok, "alertas": alertas},
                     ensure_ascii=False, indent=2))
    if alertas:
        sys.exit(2)


def c_quadros(a):
    """Extrai N quadros distribuídos e monta uma folha de contato para revisão (Read na imagem)."""
    if a.n < 1:
        sys.exit("--n deve ser pelo menos 1")
    dur = dur_video(a.video)
    os.makedirs(a.saida, exist_ok=True)
    tempos = [dur * (i + 0.5) / a.n for i in range(a.n)] if not a.tempos else [num(t, campo="tempo") for t in a.tempos.split(",")]
    arquivos = []
    for i, t in enumerate(tempos, 1):
        out = os.path.join(a.saida, f"quadro_{i:02d}.png")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{min(t, max(dur - 0.05, 0)):.3f}", "-i", a.video, "-frames:v", "1",
             "-vf", f"scale={a.largura}:-2,drawtext=text='{t:.1f}s':x=10:y=10:fontcolor=white:fontsize=28:box=1:boxcolor=black@0.6",
             out])
        arquivos.append(out)
    folha = os.path.join(a.saida, "folha.png")
    if len(arquivos) == 1:
        shutil.copy(arquivos[0], folha)
    else:
        entradas = sum((["-i", f] for f in arquivos), [])
        pilha = "".join(f"[{i}:v]" for i in range(len(arquivos))) + f"hstack=inputs={len(arquivos)}"
        run(["ffmpeg", "-y", "-v", "error"] + entradas + ["-filter_complex", pilha, folha])
    print("\n".join(arquivos + [folha]))


def c_cortar(a):
    os.makedirs(a.saida, exist_ok=True)
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        linhas = [r for r in csv.DictReader(f) if (r.get("trilha") or "principal").strip().lower() != "audio"]
    if not linhas:
        sys.exit("A lista de cortes não tem clipes de vídeo.")
    for i, r in enumerate(linhas, 1):
        src = os.path.join(a.midias, (r.get("midia") or "").strip())
        ini, dur = num(r.get("inicio"), 0.0, "início"), num(r.get("duracao"), None, "duração")
        if not dur or dur <= 0:
            sys.exit(f"clipe {i} ({r.get('midia')}): duração ausente ou inválida")
        if not os.path.isfile(src):
            sys.exit(f"clipe {i}: mídia não encontrada: {src}")
        base = os.path.splitext(os.path.basename(r["midia"].strip()))[0]
        out = os.path.join(a.saida, f"{i:02d}_{base}.mp4")
        cmd = ["ffmpeg", "-y", "-ss", str(ini), "-i", src, "-t", str(dur)]
        if a.formato:
            w, h = FORMATOS[a.formato]
            cmd += ["-filter_complex", f"[0:v]{fit_filter(w, h, a.modo)}[v]", "-map", "[v]", "-map", "0:a?"]
        else:
            cmd += ["-map", "0:v:0", "-map", "0:a?"]
        run(cmd + ENC_V + ENC_A + FIM + [out])
        print(out)


def c_reenquadrar(a):
    w, h = FORMATOS[a.formato]
    run(["ffmpeg", "-y", "-i", a.video, "-filter_complex", f"[0:v]{fit_filter(w, h, a.modo)}[v]", "-map", "[v]", "-map", "0:a?"]
        + ENC_V + ENC_A + FIM + [a.saida])
    print(a.saida)


def c_srt(a):
    blocos, anterior = [], 0.0
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        for i, r in enumerate(csv.DictReader(f), 1):
            ini, fim = num(r.get("inicio"), None, f"início da legenda {i}"), num(r.get("fim"), None, f"fim da legenda {i}")
            if ini is None or fim is None or fim <= ini:
                sys.exit(f"legenda {i}: informe início e fim, com fim maior que início")
            if blocos and ini < anterior:
                print(f"aviso: legenda {i} começa antes do fim da anterior ({ts(anterior)})", file=sys.stderr)
            anterior = fim
            linhas = textwrap.wrap((r.get("texto") or "").strip(), a.largura)
            if len(linhas) > 2:
                print(f"aviso: legenda {i} passa de 2 linhas — considere dividir", file=sys.stderr)
            if (fim - ini) < 0.8:
                print(f"aviso: legenda {i} fica só {fim - ini:.2f}s na tela (mínimo confortável ≈ 0,8–1 s)", file=sys.stderr)
            blocos.append(f"{i}\n{ts(ini)} --> {ts(fim)}\n" + "\n".join(linhas) + "\n")
    with open(a.saida, "w", encoding="utf-8") as f:
        f.write("\n".join(blocos))
    print(a.saida)


def c_legendar(a):
    d = probe(a.video); v = next(s for s in d["streams"] if s["codec_type"] == "video")
    # unidades do libass: altura de referência 288 (PlayResY padrão do SRT)
    vertical = v["height"] > v["width"]
    margem = 60 if vertical else 22          # ≈ 21% / 8% da altura: acima da interface dos apps
    tamanho = a.tamanho or (9 if vertical else 16)
    estilo = (f"FontName={a.fonte},FontSize={tamanho},PrimaryColour={ass_cor(a.cor)},OutlineColour={ass_cor(a.contorno)},"
              f"BorderStyle=1,Outline=1.2,Shadow=0,Bold=1,Alignment=2,MarginV={margem},MarginL=12,MarginR=12")
    if not os.path.isfile(a.srt):
        sys.exit(f"legenda não encontrada: {a.srt}")
    # Copia legenda e fontes para uma pasta temporária de nome simples: caminhos com aspas,
    # dois-pontos ou espaços quebram a sintaxe de filtros do ffmpeg.
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(a.srt, os.path.join(tmp, "leg.srt"))
        fontsdir = ""
        if a.pasta_fontes:
            shutil.copytree(a.pasta_fontes, os.path.join(tmp, "fontes"))
            fontsdir = ":fontsdir=fontes"
        vf = f"subtitles=leg.srt{fontsdir}:force_style='{estilo}'"
        saida, video = os.path.abspath(a.saida), os.path.abspath(a.video)
        r = subprocess.run(["ffmpeg", "-y", "-i", video, "-vf", vf] + ENC_V + ["-c:a", "copy"] + FIM + [saida],
                           capture_output=True, text=True, cwd=tmp)
        if r.returncode != 0:
            sys.exit("ffmpeg falhou:\n" + r.stderr[-2000:])
    print(a.saida)


def c_cartela(a):
    if a.duracao <= 0:
        sys.exit("--duracao deve ser positiva")
    w, h = FORMATOS[a.formato]
    fonte = f"fontfile='{a.fonte}':" if a.fonte and os.path.exists(a.fonte) else (f"font='{a.fonte}':" if a.fonte else "")
    tam = a.tamanho or int(w * 0.075)
    fade = min(0.4, a.duracao / 4)
    with tempfile.TemporaryDirectory() as pasta:
        texto = os.path.join(pasta, "cartela.txt")
        with open(texto, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(textwrap.wrap(a.texto, a.largura)))
        def montar(alinhar):
            return (f"drawtext={fonte}textfile='{texto}':expansion=none:{alinhar}fontcolor={hexcor(a.cor)}:"
                    f"fontsize={tam}:line_spacing={int(tam * 0.25)}:x=(w-text_w)/2:y=(h-text_h)/2,"
                    f"fade=t=in:st=0:d={fade},fade=t=out:st={a.duracao-fade}:d={fade}")
        base = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={hexcor(a.fundo)}:s={w}x{h}:r={a.fps}:d={a.duracao}",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(a.duracao)]
        fim = ["-shortest"] + ENC_V + ENC_A + FIM + [a.saida]
        # text_align=C centraliza cada linha (ffmpeg ≥ 6.1); versões antigas caem no alinhamento à esquerda.
        if run(base + ["-vf", montar("text_align=C:")] + fim, sair=False).returncode != 0:
            run(base + ["-vf", montar("")] + fim)
    print(a.saida)


def c_concatenar(a):
    v0 = next(s for s in probe(a.clipes[0])["streams"] if s["codec_type"] == "video")
    w, h = (FORMATOS[a.formato] if a.formato else (v0["width"], v0["height"]))
    entradas, partes = [], []
    for i, c in enumerate(a.clipes):
        entradas += ["-i", c]
        if not os.path.isfile(c):
            sys.exit(f"clipe não encontrado: {c}")
        dur = dur_video(c)
        partes.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={a.fps},format=yuv420p[v{i}];")
        if tem_audio(c):
            # apad+atrim: áudio com a mesma duração do vídeo de cada clipe, senão a sincronia escorrega nos cortes seguintes
            partes.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{dur}[a{i}];")
        else:
            partes.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur}[a{i}];")
        partes[-2] = partes[-2].replace(f"format=yuv420p[v{i}]", f"format=yuv420p,trim=0:{dur},setpts=PTS-STARTPTS[v{i}]")
    junta = "".join(f"[v{i}][a{i}]" for i in range(len(a.clipes)))
    fc = "".join(partes) + f"{junta}concat=n={len(a.clipes)}:v=1:a=1[v][a]"
    run(["ffmpeg", "-y"] + entradas + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]"] + ENC_V + ENC_A + FIM + [a.saida])
    print(a.saida)


def medir(fc_pre, extra_in):
    """1ª passada do loudnorm: mede o áudio já mixado."""
    base = "loudnorm=I=-14:TP=-1:LRA=11"
    r = run(["ffmpeg", "-hide_banner"] + extra_in + ["-filter_complex", fc_pre + base + ":print_format=json[o]",
            "-map", "[o]", "-f", "null", "-"])
    try:
        j, _ = json.JSONDecoder().raw_decode(r.stderr[r.stderr.rindex("{"):])
    except ValueError:
        sys.exit("O ffmpeg não retornou a medição de loudness.")
    if any(not math.isfinite(float(j[k])) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")):
        print("Áudio sem medição finita; preservando o sinal.", file=sys.stderr)
        return "anull"
    return (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
            f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")


def c_audio(a):
    entradas = ["-i", a.video] + (["-stream_loop", "-1", "-i", a.trilha] if a.trilha else [])
    if not tem_audio(a.video):
        if not a.trilha:
            sys.exit("O vídeo não tem faixa de áudio. Informe --trilha para adicionar uma.")
        duracao = float(probe(a.video)["format"]["duration"])
        pre = f"[1:a]aresample=48000,volume={a.volume_trilha},atrim=duration={duracao}[m];[m]"
    elif a.trilha:
        voz = "[0:a]aresample=48000,asplit=2[voz][sc];" if a.ducking else "[0:a]aresample=48000[voz];"
        trilha = f"[1:a]aresample=48000,volume={a.volume_trilha}[tr];"
        if a.ducking:
            mix = "[tr][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[trd];[voz][trd]amix=inputs=2:duration=first:normalize=0[m];"
        else:
            mix = "[voz][tr]amix=inputs=2:duration=first:normalize=0[m];"
        pre = voz + trilha + mix + "[m]"
    else:
        pre = "[0:a]aresample=48000[m];[m]"
    norm = medir(pre, entradas)
    run(["ffmpeg", "-y"] + entradas + ["-filter_complex", pre + norm + "[out]", "-map", "0:v?", "-map", "[out]",
         "-c:v", "copy", "-shortest"] + ENC_A + FIM + [a.saida])
    print(a.saida)


def c_exportar(a):
    os.makedirs(a.saida, exist_ok=True)
    formatos = [formato_valido(f) for f in a.formatos.split(",") if f.strip()]
    for f in formatos:
        w, h = FORMATOS[f]
        out = os.path.join(a.saida, f"{a.base}_{SIGLA[f]}.mp4")
        run(["ffmpeg", "-y", "-i", a.video, "-filter_complex", f"[0:v]{fit_filter(w, h, a.modo)}[v]", "-map", "[v]", "-map", "0:a?"]
            + ENC_V + ENC_A + FIM + [out])
        print(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("info"); s.add_argument("video"); s.set_defaults(f=c_info)
    s = sp.add_parser("conferir", help="confere resolução, fps, codec, duração, loudness e nome contra o padrão da casa")
    s.add_argument("video"); s.add_argument("--plataforma", default="reels", choices=PLATAFORMAS)
    s.add_argument("--formato", choices=FORMATOS, help="sobrepõe o formato esperado da plataforma"); s.set_defaults(f=c_conferir)
    s = sp.add_parser("quadros", help="extrai quadros e uma folha de contato para revisão")
    s.add_argument("video"); s.add_argument("--n", type=int, default=4); s.add_argument("--tempos", help="ex.: 0.5,12,40")
    s.add_argument("--largura", type=int, default=360); s.add_argument("--saida", default="revisao"); s.set_defaults(f=c_quadros)
    s = sp.add_parser("cortar"); s.add_argument("csv"); s.add_argument("--midias", default=".")
    s.add_argument("--saida", default="cortes"); s.add_argument("--formato", choices=FORMATOS)
    s.add_argument("--modo", default="blur", choices=["blur", "crop"]); s.set_defaults(f=c_cortar)
    s = sp.add_parser("reenquadrar"); s.add_argument("video"); s.add_argument("saida")
    s.add_argument("--formato", default="9:16", choices=FORMATOS); s.add_argument("--modo", default="blur", choices=["blur", "crop"]); s.set_defaults(f=c_reenquadrar)
    s = sp.add_parser("srt"); s.add_argument("csv"); s.add_argument("saida"); s.add_argument("--largura", type=int, default=32); s.set_defaults(f=c_srt)
    s = sp.add_parser("legendar"); s.add_argument("video"); s.add_argument("srt"); s.add_argument("saida")
    s.add_argument("--fonte", default="DejaVu Sans"); s.add_argument("--pasta-fontes", default="")
    s.add_argument("--tamanho", type=float, help="escala libass (altura 288); padrão 9 vertical, 16 horizontal"); s.add_argument("--cor", default="#FFFFFF"); s.add_argument("--contorno", default="#000000"); s.set_defaults(f=c_legendar)
    s = sp.add_parser("cartela"); s.add_argument("saida"); s.add_argument("--texto", required=True)
    s.add_argument("--fundo", default="#000000"); s.add_argument("--cor", default="#FFFFFF"); s.add_argument("--fonte", default="")
    s.add_argument("--tamanho", type=int); s.add_argument("--largura", type=int, default=18)
    s.add_argument("--duracao", type=float, default=2.5); s.add_argument("--formato", default="9:16", choices=FORMATOS)
    s.add_argument("--fps", type=int, default=30); s.set_defaults(f=c_cartela)
    s = sp.add_parser("concatenar"); s.add_argument("saida"); s.add_argument("clipes", nargs="+")
    s.add_argument("--formato", choices=FORMATOS); s.add_argument("--fps", type=int, default=30); s.set_defaults(f=c_concatenar)
    s = sp.add_parser("audio"); s.add_argument("video"); s.add_argument("saida"); s.add_argument("--trilha")
    s.add_argument("--volume-trilha", type=float, default=0.3); s.add_argument("--ducking", action="store_true"); s.set_defaults(f=c_audio)
    s = sp.add_parser("exportar"); s.add_argument("video"); s.add_argument("--formatos", default="9:16,4:5,16:9")
    s.add_argument("--saida", default="export"); s.add_argument("--base", default="VIDEO"); s.add_argument("--modo", default="blur", choices=["blur", "crop"]); s.set_defaults(f=c_exportar)

    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
