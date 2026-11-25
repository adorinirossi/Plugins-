#!/usr/bin/env python3
"""Editor de vídeo falado — Three Minds.
analisar  : transcreve por palavra e monta o plano de cortes (pausas, hesitações, tomadas repetidas —
            fica a melhor tomada ou a última)
corrigir  : conserta palavras da legenda (não mexe nos cortes)
ajustar   : muda o plano por conversa (manter itens, cortar trechos, abrir com a frase mais forte, tomada)
renderizar: corta, reenquadra seguindo o rosto, legenda palavra por palavra, gancho, zoom, limpeza de voz,
            áudio −14 LUFS; grava também o .srt da versão editada
cartao    : cartão animado que entra quando uma palavra é dita ("1 PROMPT", "100 BRINDES")
versoes   : um vídeo por gancho
"""
import argparse, json, os, re, shutil, subprocess, sys, unicodedata
from difflib import SequenceMatcher

HESIT = {"ãh", "ah", "ahn", "aham", "aum", "eh", "éé", "hã", "hm", "hmm", "hum", "uhm", "uh", "mm"}
# Termos que costumam barrar anúncio (Meta/TikTok). Regex em texto normalizado (sem acento), por início de palavra,
# para não acusar "procura", "curadoria" ou "segurança".
RISCO_ANUNCIO = [r"\bsexo\b", r"\bsexua", r"\bnud(e|es|ez)\b", r"\bpelad", r"\btesao\b", r"\bgoz(ar|ei|ou|ando)\b",
                 r"\borgasm", r"\bsafad", r"\bputaria\b", r"\bexplicit", r"\btransa(r|mos|ram|ndo)?\b",
                 r"\berotic", r"\bfetiche", r"\bgarantid", r"\bcura(r|do|da)?\b", r"\bemagrec", r"\bganhe dinheiro\b",
                 r"\bvoce esta solteir"]


def riscos_anuncio(texto):
    t = norm(texto)
    achados = [r.replace("\\b", "").replace("\\", "") for r in RISCO_ANUNCIO if re.search(r, t)]
    if re.search(r"\+\s?18\b|\b18\s?\+", texto):  # "+18" no texto original (norm tira o "+"; "dia 18" passa)
        achados.append("+18")
    return achados


def ass_txt(t):
    """Texto literal no ASS: chaves e barra invertida viram comandos se não forem trocadas."""
    return t.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"plano não encontrado: {caminho} (rode `analisar` antes)")
FORMATOS = {"9:16": (1080, 1920), "4:5": (1080, 1350), "16:9": (1920, 1080), "1:1": (1080, 1080)}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ERRO ffmpeg:\n" + r.stderr[-2500:])
    return r.stdout


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def duracao(v):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v]))


def info_video(v):
    """Largura/altura como o ffmpeg entrega os quadros (já girados) e se o vídeo é HDR.
    Celular grava vertical como 1920x1080 + metadado de rotação: sem trocar, o corte sai torto."""
    d = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,color_transfer,color_primaries:stream_side_data=rotation:stream_tags=rotate",
                        "-of", "json", v]))
    st = (d.get("streams") or [{}])[0]
    if not st.get("width"):
        sys.exit(f"{v}: sem faixa de vídeo")
    w, h = int(st["width"]), int(st["height"])
    rot = st.get("tags", {}).get("rotate")
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = sd["rotation"]
    try:
        if int(float(rot or 0)) % 180:
            w, h = h, w
    except ValueError:
        pass
    hdr = st.get("color_transfer") in ("arib-std-b67", "smpte2084") or st.get("color_primaries") == "bt2020"
    return w, h, hdr


def dims(v):
    w, h, _ = info_video(v)
    return w, h


HAAR_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml"


def detector_rosto():
    """Haar do OpenCV: usa o que vem com o opencv-python; se faltar, baixa o XML uma vez para ~/editor-falado."""
    try:
        import cv2
    except ImportError:
        return None
    caminhos = []
    if getattr(cv2, "data", None) is not None and getattr(cv2.data, "haarcascades", ""):
        caminhos.append(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    local = os.path.expanduser("~/editor-falado/haarcascade_frontalface_default.xml")
    caminhos.append(local)
    for c in caminhos:
        if os.path.exists(c):
            d = cv2.CascadeClassifier(c)
            if not d.empty():
                return d
    try:
        import urllib.request
        os.makedirs(os.path.dirname(local), exist_ok=True)
        urllib.request.urlretrieve(HAAR_URL, local)
        d = cv2.CascadeClassifier(local)
        return None if d.empty() else d
    except Exception:
        return None


def centro_rosto(video, i, f, vw, vh, det):
    """Centro (x, y) do rosto principal no trecho [i, f], em fração do quadro; None se não achar."""
    import cv2, numpy as np
    pts = []
    for t in (i + (f - i) * q for q in (0.2, 0.5, 0.8)):
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                              "-vf", "scale=480:-2,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
        h = int(round(480 * vh / vw / 2) * 2)
        if len(raw) < 480 * h:
            continue
        img = np.frombuffer(raw[:480 * h], np.uint8).reshape(h, 480)
        fs = det.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(max(24, h // 12),) * 2)
        if len(fs):
            altos = [r for r in fs if r[1] + r[3] / 2 < 0.6 * h] or list(fs)  # rosto fica no alto; evita falso positivo
            x, y, w, hh = max(altos, key=lambda r: r[2] * r[3])
            pts.append(((x + w / 2) / 480, (y + hh / 2) / h))
    if not pts:
        return None
    pts.sort()
    return pts[len(pts) // 2]


# ---------------------------------------------------------------- analisar
def escolher_modelo(nome, dur):
    if nome != "auto":
        return nome
    return "large-v3-turbo" if dur <= 600 else "small"


def c_analisar(a):
    os.makedirs(a.saida, exist_ok=True)
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", a.video, "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    if len(audio) < 16000 * 0.5:
        sys.exit("A gravação não tem áudio (ou tem menos de meio segundo) — o editor falado precisa da fala.")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper não instalado: pip install --break-system-packages faster-whisper")
    modelo = escolher_modelo(a.modelo, len(audio) / 16000)
    try:
        m = WhisperModel(modelo, device="cpu", compute_type="int8")
    except Exception as e:  # download bloqueado ou pouca memória: cai para o small e avisa
        if modelo == "small":
            raise
        print(f"⚠ modelo {modelo} indisponível ({str(e)[:80]}); usando small — confira nomes e números com mais cuidado")
        modelo = "small"
        m = WhisperModel(modelo, device="cpu", compute_type="int8")
    print(f"transcrição: modelo {modelo}")
    segs, _ = m.transcribe(audio, language="pt", word_timestamps=True, vad_filter=False,
                           initial_prompt="Ãh, aham, hum, né. Fala natural com hesitações. " + a.contexto)
    frases = []
    for s in segs:
        ws = []
        for w in s.words:
            t = w.word.strip()
            if not t:
                continue
            if ws and (t.startswith("-") or not w.word.startswith(" ")):  # "pré" + "-venda" → uma palavra
                ws[-1]["t"] += t; ws[-1]["f"] = round(w.end, 3)
            else:
                ini = w.start if w.end - w.start <= 1.0 else w.end - 0.55  # silêncio colado na palavra
                ws.append({"t": t, "i": round(ini, 3), "f": round(w.end, 3)})
        cur = []
        for j, w in enumerate(ws):
            cur.append(w)
            prox = ws[j + 1] if j + 1 < len(ws) else None
            recomeco = (prox is not None and len(cur) >= 3 and
                        [norm(x["t"]) for x in ws[j + 1:j + 3]] == [norm(x["t"]) for x in cur[:2]])
            if prox is None or re.search(r"[.!?…]$", w["t"]) or prox["i"] - w["f"] > 1.2 or recomeco:
                frases.append({"texto": " ".join(x["t"] for x in cur), "i": cur[0]["i"], "f": cur[-1]["f"],
                               "palavras": cur})
                cur = []
    dur = duracao(a.video)
    itens = []  # cortes propostos
    if a.roteiro:
        with open(a.roteiro, encoding="utf-8") as f:
            itens += alinhar_roteiro(frases, f.read())

    # 1) tomadas repetidas: frases seguidas que recomeçam igual formam um grupo; fica uma só
    descartadas = set()
    hs = {norm(h) for h in HESIT}

    def parecidas(k):
        A, B = norm(frases[k]["texto"]).split(), norm(frases[k + 1]["texto"]).split()
        if len(A) < 2 or len(B) < 2:
            return False
        n = min(len(A), len(B), 6)
        return SequenceMatcher(None, A[:n], B[:n]).ratio() >= 0.7

    def nota(fr):  # mais completa e mais limpa; empate → a mais recente
        ws = [norm(w["t"]) for w in fr["palavras"]]
        conteudo = [w for w in ws if w and w not in hs]
        final = 1 if re.search(r"[.!?…]$", fr["texto"].strip()) else 0
        return len(conteudo) - 2 * (len(ws) - len(conteudo)) + final

    k = 0
    while k < len(frases) - 1:
        if not parecidas(k):
            k += 1; continue
        g = [k]
        while g[-1] < len(frases) - 1 and parecidas(g[-1]):
            g.append(g[-1] + 1)
        fica = g[-1] if a.tomada == "ultima" else max(g, key=lambda j: (nota(frases[j]), j))
        vocab_fica = set(norm(frases[fica]["texto"]).split())
        for j in g:
            if j == fica:
                continue
            novas = [w for w in norm(frases[j]["texto"]).split() if w not in vocab_fica and w not in hs and len(w) > 2]
            info_nova = len(novas) >= 4
            if not info_nova:
                descartadas.add(j)
            fim = frases[j + 1]["i"] if j + 1 < len(frases) else frases[j]["f"]
            itens.append({"tipo": "tomada repetida" if not info_nova else "tomada c/ info nova",
                          "i": frases[j]["i"], "f": fim, "texto": frases[j]["texto"], "_cortar": not info_nova})
        k = g[-1] + 1
    # 2) frases só de hesitação / hesitações soltas
    for k, fr in enumerate(frases):
        if k in descartadas:
            continue
        ws = fr["palavras"]
        if all(norm(w["t"]) in {norm(h) for h in HESIT} or len(norm(w["t"])) == 0 for w in ws) or \
                re.search(r"\b(deixa eu ver|peraí|pera aí|esqueci|de novo|vou repetir)\b", norm(fr["texto"])):
            descartadas.add(k)
            itens.append({"tipo": "hesitação/erro", "i": fr["i"], "f": fr["f"], "texto": fr["texto"]})
            continue
        for j, w in enumerate(ws):
            if norm(w["t"]) in hs:
                itens.append({"tipo": "hesitação", "i": w["i"], "f": w["f"], "texto": w["t"]})
            elif norm(w["t"]) == "e" and w["f"] - w["i"] >= 0.35:  # "éééé" arrastado e isolado; o "é" verbo fica
                antes = w["i"] - (ws[j - 1]["f"] if j else fr["i"] - 1)
                depois = (ws[j + 1]["i"] if j + 1 < len(ws) else w["f"] + 1) - w["f"]
                if antes > 0.25 and depois > 0.25:
                    itens.append({"tipo": "hesitação (é)", "i": w["i"], "f": w["f"], "texto": w["t"]})
    # 3) pausas longas: silêncio entre QUALQUER palavra dita. Tomadas e hesitações já têm item próprio;
    # assim, `ajustar --manter N` devolve a tomada sem que um item de pausa por cima continue cortando.
    mantidas = sorted((w for fr in frases for w in fr["palavras"]), key=lambda w: w["i"])
    PAD = a.respiro
    prev = 0.0
    for w in mantidas + [{"i": dur, "f": dur}]:
        if w["i"] - prev > a.pausa:
            itens.append({"tipo": "pausa", "i": round(prev + PAD, 3), "f": round(w["i"] - PAD, 3),
                          "texto": f"{w['i'] - prev:.1f} s"})
        prev = max(prev, w["f"])
    itens.sort(key=lambda x: x["i"])
    for n, it in enumerate(itens, 1):
        it["n"], it["cortar"] = n, it.pop("_cortar", True)
    plano = {"video": os.path.abspath(a.video), "duracao": dur, "frases": frases, "itens": itens, "extras": [],
             "modelo": modelo, "tomada": a.tomada}
    salvar(plano, a.saida)
    resumo(plano)


def alinhar_roteiro(frases, roteiro):
    """Troca o texto transcrito pelo texto exato do roteiro (nomes, grafia, pontuação), mantendo os tempos."""
    ws = [w for fr in frases for w in fr["palavras"]]
    toks = roteiro.split()
    A, B = [norm(w["t"]) for w in ws], [norm(t) for t in toks]
    itens = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op in ("equal", "replace"):
            n, m = i2 - i1, j2 - j1
            for k in range(n):  # distribui os tokens do roteiro pelas palavras faladas
                a0, a1 = round(k * m / n), round((k + 1) * m / n)
                ws[i1 + k]["t"] = " ".join(toks[j1 + a0:j1 + a1])
        elif op == "insert" and i1 > 0:  # está no roteiro mas não foi ouvido: mantém na legenda
            ws[i1 - 1]["t"] += " " + " ".join(toks[j1:j2])
        elif op == "delete":  # falado fora do roteiro
            borda = i1 == 0 or i2 == len(ws)
            for w in ws[i1:i2]:
                itens.append({"tipo": "fora do roteiro", "i": w["i"], "f": w["f"], "texto": w["t"],
                              "_cortar": borda})
                w["t"] = w["t"] if not borda else ""
    for fr in frases:
        fr["texto"] = " ".join(w["t"] for w in fr["palavras"] if w["t"])
    return itens


def salvar(plano, pasta):
    with open(os.path.join(pasta, "plano.json"), "w", encoding="utf-8") as f:
        json.dump(plano, f, ensure_ascii=False, indent=1)


def trechos(plano):
    cortes = sorted([(it["i"], it["f"]) for it in plano["itens"] if it["cortar"] and it["f"] > it["i"]] +
                    [tuple(x) for x in plano["extras"]])
    keep, t = [], 0.0
    for i, f in cortes:
        if i > t + 0.05:
            keep.append([round(t, 3), round(i, 3)])
        t = max(t, f)
    if plano["duracao"] - t > 0.05:
        keep.append([round(t, 3), round(plano["duracao"], 3)])
    return keep


def resumo(plano):
    k = trechos(plano)
    final = sum(f - i for i, f in k)
    print(f"Bruto {plano['duracao']:.1f} s → editado {final:.1f} s ({plano['duracao'] - final:.1f} s a menos)\n")
    print("CORTES PROPOSTOS (n · tipo · tempo · o que sai):")
    for it in plano["itens"]:
        st = "✂" if it["cortar"] else "↺ mantido"
        print(f" {it['n']:>2} {st} {it['tipo']:<16} {it['i']:6.2f}–{it['f']:6.2f}  {it['texto']}")
    for i, f in plano["extras"]:
        print(f"  + corte manual {i:.2f}–{f:.2f}")
    print("\nFALA QUE FICA:")
    print(" ".join(w["t"] for w in palavras_mantidas(plano) if w["t"]))
    k_ = trechos(plano)
    print("\nFRASES (use o número em `ajustar --abrir N`):")
    for n, fr in enumerate(plano["frases"], 1):
        if any(i <= (fr["i"] + fr["f"]) / 2 <= f for i, f in k_):
            print(f" F{n:<3} {fr['texto']}")
    if plano.get("abrir"):
        print(f"\nABRE COM: F{plano['abrir']} — confira se a frase seguinte faz sentido sem ela")
    riscos = riscos_anuncio(" ".join(w["t"] for w in palavras_mantidas(plano)))
    if riscos:
        print("\n⚠ ANÚNCIO: termos que costumam ser barrados no Meta/TikTok Ads:", ", ".join(riscos))


def ordem_render(plano):
    """Trechos na ordem do vídeo final: a frase escolhida em `abrir` vem primeiro, o resto segue o tempo."""
    keep = trechos(plano)
    n = plano.get("abrir")
    if not n:
        return keep
    if not 1 <= n <= len(plano["frases"]):
        sys.exit(f"--abrir {n}: não existe a frase F{n} (há {len(plano['frases'])})")
    fr = plano["frases"][n - 1]
    a0, b0 = fr["i"] - 0.08, fr["f"] + 0.15
    dentro, fora = [], []
    for i, f in keep:
        if f <= a0 or i >= b0:
            fora.append([i, f]); continue
        if i < a0:
            fora.append([i, round(a0, 3)])
        dentro.append([round(max(i, a0), 3), round(min(f, b0), 3)])
        if f > b0:
            fora.append([round(b0, 3), f])
    if not dentro:
        print(f"⚠ a frase F{n} está toda cortada; o vídeo abre na ordem normal (devolva os cortes dela com --manter)")
    return [s for s in dentro + fora if s[1] - s[0] > 0.05]


def palavras_mantidas(plano):
    k = trechos(plano)
    out = []
    for fr in plano["frases"]:
        for w in fr["palavras"]:
            mid = (w["i"] + w["f"]) / 2
            if any(i <= mid <= f for i, f in k):
                out.append(w)
    return out


# ---------------------------------------------------------------- ajustar
def numeros(txt, opcao):
    out = []
    for n in (txt or "").replace(";", ",").split(","):
        if n.strip():
            try:
                out.append(int(n))
            except ValueError:
                sys.exit(f"{opcao}: '{n.strip()}' não é número de item (ex.: {opcao} 3,7)")
    return out


def c_ajustar(a):
    p = ler_json(a.plano)
    existentes = {it["n"] for it in p["itens"]}
    for opcao, lista, valor in (("--manter", a.manter, False), ("--recortar", a.recortar, True)):
        for n in numeros(lista, opcao):
            if n not in existentes:
                print(f"⚠ {opcao}: não há item {n} na lista de cortes")
            for it in p["itens"]:
                if it["n"] == n:
                    it["cortar"] = valor
    if a.abrir is not None:
        if a.abrir and not 1 <= a.abrir <= len(p["frases"]):
            sys.exit(f"--abrir {a.abrir}: não existe a frase F{a.abrir}")
        p["abrir"] = a.abrir or None
    if a.tomada and a.tomada != p.get("tomada"):
        print("⚠ para trocar entre melhor tomada e última tomada, rode `analisar` de novo com --tomada " + a.tomada)
    for faixa in re.split(r"[;\s]+|,(?=\s*\d+(?:[.,]\d+)?\s*-)", (a.cortar or "").strip()):
        if faixa.strip():
            m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*", faixa)
            if not m:
                sys.exit(f"--cortar: faixa '{faixa}' inválida; use INÍCIO-FIM em segundos do bruto (ex.: 12-13.5,20-21)")
            i, f = (float(x.replace(",", ".")) for x in m.groups())
            if not 0 <= i < f <= p["duracao"] + 0.01:
                sys.exit(f"--cortar {faixa}: o fim deve ser maior que o início e caber nos {p['duracao']:.1f} s do bruto")
            p["extras"].append([i, f])
    salvar(p, os.path.dirname(os.path.abspath(a.plano)))
    resumo(p)


def c_corrigir(a):
    p = ler_json(a.plano)
    for tr in a.trocas:
        src, sep, dst = tr.partition("=")
        S, D = [norm(x) for x in src.split()], dst.split()
        if not sep or not S or not D or not all(S):
            sys.exit(f"troca '{tr}' inválida; use \"errado=certo\" (os dois lados preenchidos)")
        feitas = 0
        for fr in p["frases"]:
            ws = fr["palavras"]
            for k in range(len(ws) - len(S) + 1):
                if [norm(w["t"]) for w in ws[k:k + len(S)]] == S:
                    pont = re.findall(r"[.,!?…]+$", ws[k + len(S) - 1]["t"])
                    if len(D) == len(S):
                        for j in range(len(S)):
                            ws[k + j]["t"] = D[j]
                    else:
                        ws[k]["t"] = dst
                        for j in range(1, len(S)):
                            ws[k + j]["t"] = ""
                    if pont and not re.search(r"[.,!?…]$", dst):
                        last = max(j for j in range(len(S)) if ws[k + j]["t"])
                        ws[k + last]["t"] += pont[0]
                    feitas += 1
            fr["texto"] = " ".join(w["t"] for w in ws if w["t"])
        print(f"{src} → {dst}: {feitas}x" + ("  ⚠ não encontrado na transcrição" if not feitas else ""))
    salvar(p, os.path.dirname(os.path.abspath(a.plano)))
    print("\nFALA QUE FICA:\n" + " ".join(w["t"] for w in palavras_mantidas(p) if w["t"]))


def c_cartao(a):
    p = ler_json(a.plano)
    p.setdefault("cartoes", [])
    if a.limpar:
        p["cartoes"] = []
        print("cartões anteriores removidos")
    ws = [w for w in palavras_mantidas(p) if w["t"]]  # só a fala que fica no vídeo
    for c in a.cartoes:
        gat, sep, txt = c.partition("=")
        tit, _, sub = txt.partition("|")
        G = [norm(x) for x in gat.split() if norm(x)]
        if not sep or not G or not tit.strip():
            print(f"⚠ '{c}' inválido; use \"palavra dita=TÍTULO|subtítulo\""); continue
        hit = next((ws[k] for k in range(len(ws) - len(G) + 1)
                    if [norm(w["t"]) for w in ws[k:k + len(G)]] == G), None)
        if hit is None:
            print(f"⚠ '{gat}' não aparece na fala que fica; cartão não criado"); continue
        p["cartoes"] = [x for x in p["cartoes"] if norm(x.get("gatilho", "")) != norm(gat)]  # refazer substitui
        p["cartoes"].append({"t": hit["i"], "titulo": tit.strip(), "sub": sub.strip(), "gatilho": gat.strip()})
        print(f"cartão '{tit.strip()}' quando diz '{gat.strip()}' ({hit['i']:.2f} s do bruto)")
    salvar(p, os.path.dirname(os.path.abspath(a.plano)))


# ---------------------------------------------------------------- renderizar
def ass_cor(h, alfa="00"):
    h = h.lstrip("#")
    return f"&H{alfa}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ts(s):
    cs = int(round(max(s, 0) * 100))  # arredonda antes de dividir: 59,996 s vira 1:00.00, não 0:59:60.00
    h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000)
    return f"{h}:{m:02d}:{cs // 100:02d}.{cs % 100:02d}"


def legenda_ass(plano, keep, W, H, a, gancho):
    # mapeia tempo bruto → tempo editado
    def novo(t):
        acc = 0.0
        for i, f in keep:  # keep já está na ordem do vídeo final
            if i <= t <= f:
                return acc + t - i
            acc += f - i
        melhor = min(keep, key=lambda s: min(abs(t - s[0]), abs(t - s[1])))
        acc = 0.0
        for s in keep:
            if s is melhor:
                return acc + (0 if t < s[0] else s[1] - s[0])
            acc += s[1] - s[0]
        return acc

    def dentro(t):
        return any(i <= t <= f for i, f in keep)

    ws = sorted([w for w in palavras_mantidas(plano) if w["t"] and dentro((w["i"] + w["f"]) / 2)],
                key=lambda w: novo((w["i"] + w["f"]) / 2))
    tam = int(H * (0.045 if H > W else 0.06))
    y = int(H * 0.70) if H > W else int(H * 0.85)
    st = (f"Style: Leg,{a.fonte},{tam},{ass_cor(a.cor)},{ass_cor(a.destaque)},{ass_cor('#000000')},"
          f"{ass_cor('#000000', '80')},-1,0,0,0,100,100,0,0,1,{max(3, tam // 12)},2,5,60,60,0,1\n"
          f"Style: Gancho,{a.fonte},{int(tam * 1.25)},{ass_cor(a.cor)},{ass_cor(a.destaque)},"
          f"{ass_cor('#000000')},{ass_cor(a.fundo_gancho, '20')},-1,0,0,0,100,100,0,0,3,18,0,8,70,70,"
          f"{int(H * 0.12)},1\n"
          f"Style: Cartao,{a.fonte},{int(tam * 2.4)},{ass_cor(a.destaque)},{ass_cor(a.cor)},"
          f"{ass_cor(a.fundo_gancho)},{ass_cor(a.fundo_gancho, '10')},-1,0,0,0,100,100,0,0,3,28,0,5,60,60,0,1\n"
          f"Style: CartaoSub,{a.fonte},{int(tam * 0.9)},{ass_cor(a.cor)},{ass_cor(a.cor)},"
          f"{ass_cor(a.fundo_gancho)},{ass_cor(a.fundo_gancho, '10')},-1,0,0,0,100,100,2,0,3,16,0,5,60,60,0,1\n")
    ev = []
    if gancho:
        lim = 16 if H > W else 30
        linhas, cur_l = [], ""
        for pal in ass_txt(gancho.upper() if a.caixa_alta else gancho).split():
            if cur_l and len(cur_l) + 1 + len(pal) > lim:
                linhas.append(cur_l); cur_l = pal
            else:
                cur_l = (cur_l + " " + pal).strip()
        linhas.append(cur_l)
        ev_g = f"Dialogue: 1,{ts(0)},{ts(a.dur_gancho)},Gancho,,0,0,0,,{{\\fad(120,200)}}" + "\\N".join(linhas)
    # blocos de até N palavras; a palavra falada acende
    blocos, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= a.palavras or re.search(r"[.!?,]$", w["t"]):
            blocos.append(cur); cur = []
    if cur:
        blocos.append(cur)
    leg = []
    for b in blocos:
        for j, w in enumerate(b):
            ini = novo(w["i"])
            fim = novo(b[j + 1]["i"]) if j + 1 < len(b) else novo(b[-1]["f"]) + 0.15
            txt = []
            for q, x in enumerate(b):
                p = ass_txt(x["t"].upper() if a.caixa_alta else x["t"])
                txt.append(f"{{\\c{ass_cor(a.destaque)}\\fscx108\\fscy108}}{p}{{\\r}}" if q == j else p)
            leg.append([ini, max(fim, ini + 0.08), " ".join(txt)])
    for k in range(len(leg) - 1):  # nunca sobrepor dois blocos
        leg[k][1] = min(leg[k][1], leg[k + 1][0])
    for ini, fim, txt in leg:
        if fim - ini > 0.02:
            ev.append(f"Dialogue: 0,{ts(ini)},{ts(fim)},Leg,,0,0,0,,{{\\an5\\pos({W // 2},{y})}}{txt}")
    cy = int(H * 0.30)
    cs = sorted(plano.get("cartoes", []), key=lambda c: c["t"])
    for n, c in enumerate(cs):
        t0 = novo(c["t"])
        if t0 < (a.dur_gancho if gancho else 0) or not any(i <= c["t"] <= f for i, f in keep):
            continue
        t1 = t0 + a.dur_cartao
        if n + 1 < len(cs):  # um cartão sai antes do próximo entrar
            t1 = min(t1, novo(cs[n + 1]["t"]) - 0.05)
        pop = "\\fad(80,180)\\fscx40\\fscy40\\t(0,160,\\fscx112\\fscy112)\\t(160,260,\\fscx100\\fscy100)"
        tit = ass_txt(c["titulo"].upper() if a.caixa_alta else c["titulo"])
        fs = int(min(tam * 2.4, (W * 0.80) / (0.62 * max(len(tit), 1))))  # título longo encolhe
        ev.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},Cartao,,0,0,0,,{{\\an5\\pos({W // 2},{cy})\\fs{fs}{pop}}}{tit}")
        if c.get("sub"):
            ev.append(f"Dialogue: 2,{ts(t0 + 0.12)},{ts(t1)},CartaoSub,,0,0,0,,"
                      f"{{\\an5\\pos({W // 2},{cy + int(tam * 2.1)}){pop}}}{ass_txt(c['sub'].upper())}")
    if gancho:
        ev.append(ev_g)
    plano["_srt"] = srt_texto(ws, novo)
    return ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\n\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
            "MarginL,MarginR,MarginV,Encoding\n%s\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,"
            "MarginV,Effect,Text\n%s\n") % (W, H, st, "\n".join(ev))


def srt_texto(ws, novo):
    """Legenda .srt da versão editada (frases de até 2 linhas de 32 caracteres) para CapCut/Premiere."""
    def t(s):
        ms = int(round(max(s, 0) * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000)
        return f"{h:02d}:{m:02d}:{ms // 1000:02d},{ms % 1000:03d}"
    blocos, cur = [], []
    for w in ws:
        cur.append(w)
        if len(" ".join(x["t"] for x in cur)) > 58 or re.search(r"[.!?]$", w["t"]):
            blocos.append(cur); cur = []
    if cur:
        blocos.append(cur)
    out = []
    for n, b in enumerate(blocos, 1):
        txt = " ".join(x["t"] for x in b)
        if len(txt) > 32:
            pal, l1 = txt.split(), ""
            while pal and len(l1 + " " + pal[0]) <= 32:
                l1 = (l1 + " " + pal.pop(0)).strip()
            txt = l1 + "\n" + " ".join(pal)
        out.append(f"{n}\n{t(novo(b[0]['i']))} --> {t(novo(b[-1]['f']) + 0.1)}\n{txt}\n")
    return "\n".join(out)


def aviso_fonte(fonte, pasta_fontes):
    if pasta_fontes or not shutil.which("fc-match"):
        return
    r = subprocess.run(["fc-match", "-f", "%{family}", fonte], capture_output=True, text=True)
    if r.returncode == 0 and fonte.lower() not in r.stdout.lower():
        print(f"⚠ fonte '{fonte}' não instalada; a legenda sairá em '{r.stdout.split(',')[0]}'. "
              "Use --pasta-fontes com o .ttf/.otf do selo.")


def medir_loudness(arq):
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", arq, "-vn", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    try:
        j, _ = json.JSONDecoder().raw_decode(r.stderr[r.stderr.rindex("{"):])
        float(j["input_i"])
        return j
    except (ValueError, KeyError):
        return None


def corrigir_loudness(saida):
    """O loudnorm de uma passada erra em vídeos curtos. Mede o final e, se sair de −14 ±1 LUFS,
    refaz só o áudio com a medição (o vídeo é copiado, sem perder qualidade)."""
    j = medir_loudness(saida)
    if not j or abs(float(j["input_i"]) + 14) <= 1:
        return float(j["input_i"]) if j else None
    tmp = saida + ".loud.mp4"
    filtro = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
              f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    run(["ffmpeg", "-nostdin", "-y", "-i", saida, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af",
         filtro + ",aresample=48000", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", tmp])
    os.replace(tmp, saida)
    j2 = medir_loudness(saida)
    return float(j2["input_i"]) if j2 else None


def render(a, gancho, saida):
    p = ler_json(a.plano)
    keep = ordem_render(p)
    if not keep:
        sys.exit("Todos os trechos estão cortados — devolva algum item com `ajustar --manter N`.")
    W, H = FORMATOS[a.formato]
    vw, vh, hdr = info_video(p["video"])
    if gancho and riscos_anuncio(gancho):
        print("⚠ ANÚNCIO: o gancho tem termos que costumam ser barrados:", ", ".join(riscos_anuncio(gancho)))
    aviso_fonte(a.fonte, a.pasta_fontes)
    pasta = os.path.dirname(os.path.abspath(a.plano))
    saida = os.path.abspath(saida)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    nome_ass = "leg_%s.ass" % re.sub(r"\W", "", os.path.basename(saida))
    with open(os.path.join(pasta, nome_ass), "w", encoding="utf-8") as f:
        f.write(legenda_ass(p, keep, W, H, a, gancho))
    with open(os.path.splitext(saida)[0] + ".srt", "w", encoding="utf-8") as f:
        f.write(p.pop("_srt", ""))
    r_asp = (W / H) / (vw / vh)
    modo_base = a.modo
    if modo_base == "auto":
        modo_base = "rosto" if 0.7 <= r_asp <= 1.45 else "blur"
    det = detector_rosto() if modo_base == "rosto" else None
    if modo_base == "rosto" and det is None:
        print("⚠ detector de rosto indisponível (pip install opencv-python-headless); enquadrando pelo centro")
    centros = []
    for i, f in keep:
        c = centro_rosto(p["video"], i, f, vw, vh, det) if det is not None else None
        centros.append(c)
    vistos = [c for c in centros if c]
    if det is not None and not vistos:
        print("⚠ rosto não encontrado; enquadrando pelo centro (para mostrar o quadro inteiro, use --modo blur)")
    padrao = (sorted(x for x, _ in vistos)[len(vistos) // 2], sorted(y for _, y in vistos)[len(vistos) // 2]) \
        if vistos else (0.5, 0.42)
    fc, cat = [], ""
    for k, (i, f) in enumerate(keep):
        z = 1.0 + (a.zoom if (a.zoom and k % 2 == 1) else 0)
        d = f - i
        fd = min(0.03, d / 3)
        # encaixe: preenche o quadro seguindo o rosto (rosto), pelo centro (crop) ou com fundo desfocado (blur)
        modo = "crop" if modo_base in ("rosto", "crop") else "blur"
        if modo == "crop":
            fx, fy = (centros[k] or padrao) if modo_base == "rosto" else (0.5, 0.5)
            s = max(W / vw, H / vh) * z  # escala única: preenche e aplica o zoom
            sw, sh = int(vw * s / 2) * 2, int(vh * s / 2) * 2
            x = int(min(max(fx * sw - W / 2, 0), sw - W))
            alvo_y = 0.38 if modo_base == "rosto" else 0.5  # olhos perto do terço superior
            y = int(min(max(fy * sh - H * alvo_y, 0), sh - H)) if modo_base == "rosto" else (sh - H) // 2
            fit = f"scale={sw}:{sh},crop={W}:{H}:{x}:{y}"
            fc.append(f"[0:v]trim={i}:{f},setpts=PTS-STARTPTS,{fit},setsar=1,fps=30[v{k}]")
        else:
            fc.append(f"[0:v]trim={i}:{f},setpts=PTS-STARTPTS,split[a{k}][b{k}];"
                      f"[a{k}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30[bg{k}];"
                      f"[b{k}]scale={W}*{z}:{H}*{z}:force_original_aspect_ratio=decrease[fg{k}];"
                      f"[bg{k}][fg{k}]overlay=(W-w)/2:(H-h)/2,crop={W}:{H},setsar=1,fps=30[v{k}]")
        fc.append(f"[0:a]atrim={i}:{f},asetpts=PTS-STARTPTS,afade=t=in:d={fd},afade=t=out:st={d - fd}:d={fd}[s{k}]")
        cat += f"[v{k}][s{k}]"
    fc.append(f"{cat}concat=n={len(keep)}:v=1:a=1[vc][ac]")
    # ffmpeg roda dentro da pasta do plano com nomes simples: caminhos com aspas, dois-pontos ou
    # espaços quebram a sintaxe dos filtros. As fontes do selo são copiadas para "_fontes_render".
    fd_opt = ""
    if a.pasta_fontes:
        if not os.path.isdir(a.pasta_fontes):
            sys.exit(f"--pasta-fontes não encontrada: {a.pasta_fontes}")
        destino = os.path.join(pasta, "_fontes_render")
        shutil.rmtree(destino, ignore_errors=True)
        shutil.copytree(a.pasta_fontes, destino)
        fd_opt = ":fontsdir=_fontes_render"
    # vídeo de celular em HDR (HLG/PQ, BT.2020) sai como SDR BT.709; sem isso fica lavado ou alaranjado
    cor = "scale=out_color_matrix=bt709:out_range=tv," if hdr else ""
    if hdr:
        print("vídeo HDR detectado: convertendo para SDR BT.709")
    fc.append(f"[vc]{cor}ass={nome_ass}{fd_opt},format=yuv420p[vo]")
    limpa = ("highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
             if a.limpar_voz else "")
    fc.append(f"[ac]{limpa}loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]")
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", p["video"], "-filter_complex", ";".join(fc), "-map", "[vo]",
                        "-map", "[ao]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", saida],
                       capture_output=True, text=True, cwd=pasta)
    if r.returncode:
        sys.exit("ERRO ffmpeg:\n" + r.stderr[-2500:])
    lufs = corrigir_loudness(saida)
    extra = f", {lufs:.1f} LUFS" if lufs is not None else ""
    print(f"OK {saida}  ({duracao(saida):.1f} s, {W}x{H}{extra})  + {os.path.splitext(saida)[0]}.srt")


def c_renderizar(a):
    render(a, a.gancho, a.saida)


def c_versoes(a):
    os.makedirs(a.pasta, exist_ok=True)
    formatos = [f.strip() for f in a.formatos.split(",") if f.strip()]
    for f in formatos:
        if f not in FORMATOS:
            sys.exit(f"formato '{f}' inválido; use {', '.join(FORMATOS)}")
    for n, g in enumerate(a.ganchos, 1):
        for fmt in formatos:
            a.formato = fmt
            render(a, g, os.path.join(a.pasta, f"{a.base}_gancho{n}_{fmt.replace(':', 'x')}.mp4"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("analisar"); s.add_argument("video"); s.add_argument("--saida", default="edicao")
    s.add_argument("--modelo", default="auto",
                   help="auto = large-v3-turbo até 10 min, small acima; ou base/small/medium/large-v3-turbo")
    s.add_argument("--tomada", choices=["melhor", "ultima"], default="melhor",
                   help="frase repetida: fica a mais completa e limpa (melhor) ou a última")
    s.add_argument("--pausa", type=float, default=0.55)
    s.add_argument("--respiro", type=float, default=0.12)
    s.add_argument("--contexto", default="", help="nomes e termos: título, autora, selo, personagens")
    s.add_argument("--roteiro", help="texto exato lido/narrado: a legenda passa a usar a grafia do roteiro")
    s.set_defaults(fn=c_analisar)
    s = sp.add_parser("corrigir"); s.add_argument("plano")
    s.add_argument("trocas", nargs="+", help='"errado=certo", aceita várias palavras: "sem leitoras=cem leitoras"')
    s.set_defaults(fn=c_corrigir)
    s = sp.add_parser("cartao"); s.add_argument("plano")
    s.add_argument("cartoes", nargs="*", help='"palavra dita=TÍTULO|subtítulo", ex.: "pré-venda=SEGUNDA|pré-venda aberta"; '
                   'aceita várias palavras: "dia doze=12/12"')
    s.add_argument("--limpar", action="store_true", help="apaga os cartões anteriores antes de criar os novos")
    s.set_defaults(fn=c_cartao)
    s = sp.add_parser("ajustar"); s.add_argument("plano"); s.add_argument("--manter", help="itens a devolver: 3,7")
    s.add_argument("--recortar", help="itens a cortar de novo"); s.add_argument("--cortar", help="faixas brutas: 12.4-13.0,20-21")
    s.add_argument("--abrir", type=int, help="nº da frase (F) que abre o vídeo; 0 desfaz")
    s.add_argument("--tomada", choices=["melhor", "ultima"], help="(lembra de reanalisar)")
    s.set_defaults(fn=c_ajustar)
    for nome, fn in (("renderizar", c_renderizar), ("versoes", c_versoes)):
        s = sp.add_parser(nome); s.add_argument("plano")
        if nome == "renderizar":
            s.add_argument("saida"); s.add_argument("--gancho", default="")
            s.add_argument("--formato", default="9:16", choices=list(FORMATOS))
        else:
            s.add_argument("--ganchos", nargs="+", required=True); s.add_argument("--formatos", default="9:16")
            s.add_argument("--pasta", default="versoes"); s.add_argument("--base", default="video")
        s.add_argument("--modo", choices=["auto", "rosto", "crop", "blur"], default="auto",
                       help="auto: segue o rosto quando dá para preencher, senão fundo desfocado")
        s.add_argument("--zoom", type=float, default=0.08, help="punch-in a cada trecho alternado (0 desliga)")
        s.add_argument("--pasta-fontes", default="", help="pasta com .ttf/.otf do selo")
        s.add_argument("--fonte", default="Inter"); s.add_argument("--cor", default="#FFFFFF")
        s.add_argument("--destaque", default="#FFD400"); s.add_argument("--fundo-gancho", default="#000000")
        s.add_argument("--palavras", type=int, default=3); s.add_argument("--dur-gancho", type=float, default=3.0)
        s.add_argument("--dur-cartao", type=float, default=1.6)
        s.add_argument("--limpar-voz", action="store_true", help="tira chiado/ruído grave e iguala o volume da fala")
        s.add_argument("--caixa-alta", action="store_true"); s.set_defaults(fn=fn)
    a = ap.parse_args()
    if getattr(a, "palavras", 1) not in (1, 2, 3):
        ap.error("--palavras deve ser 1, 2 ou 3")
    a.fn(a)


if __name__ == "__main__":
    main()
