#!/usr/bin/env python3
"""Gera imagens e vídeos com a API da Runway (dev.runwayml.com). Só biblioteca padrão.

Chave: variável de ambiente RUNWAYML_API_SECRET (nunca passe a chave como argumento).

  imagem  --prompt "..." [--ref tag=arquivo.png ...] [--proporcao 1080:1920] [--modelo gen4_image] --saida geracoes/P03
  video   --imagem quadro.png | (sem imagem: texto→vídeo, só gen4.5)  --prompt "movimento..."
          [--proporcao 720:1280] [--duracao 5] [--modelo gen4.5|gen4_turbo] --saida geracoes/P01_mov
  status  ID_DA_TAREFA [--saida geracoes/P01_mov]   (com --saida, baixa o resultado de uma tarefa concluída)
  custo   --modelo gen4.5 --segundos 40      (ou --modelo gen4_image --imagens 10 [--resolucao 1080])

Espera a tarefa terminar e baixa o resultado na hora — os links da Runway expiram em 24 h.
Falhas de rede passageiras durante a espera são repetidas; se a espera cair, a tarefa (já paga)
continua na Runway: recupere com `status ID --saida ...`. Nada é sobrescrito (P01_v2.mp4...).
"""
import argparse, base64, json, mimetypes, os, socket, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registro import registrar, ler_prompt, destino_livre  # noqa: E402

API = "https://api.dev.runwayml.com/v1"
VERSAO = "2024-11-06"
CREDITOS_S = {"gen4.5": 12, "gen4_turbo": 5}
CREDITOS_IMG = {"gen4_image": {720: 5, 1080: 8}, "gen4_image_turbo": {720: 2, 1080: 2}}
PROP_VIDEO = ["1280:720", "720:1280", "1104:832", "832:1104", "960:960", "1584:672", "672:1584"]


def chave():
    k = os.environ.get("RUNWAYML_API_SECRET")
    if not k:
        sys.exit("RUNWAYML_API_SECRET não definida. Crie a chave em dev.runwayml.com e configure a variável de ambiente.")
    return k


def http(metodo, caminho, corpo=None, tentativas=1):
    """tentativas > 1 só para chamadas idempotentes (GET de status): repete 429/5xx e quedas de rede."""
    for n in range(1, tentativas + 1):
        req = urllib.request.Request(API + caminho, method=metodo,
                                     data=json.dumps(corpo).encode() if corpo is not None else None,
                                     headers={"Authorization": f"Bearer {chave()}", "X-Runway-Version": VERSAO,
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = r.read()
                return json.loads(txt) if txt else {}
        except urllib.error.HTTPError as e:
            corpo_erro = e.read().decode("utf-8", "replace")[:800]
            if n < tentativas and (e.code == 429 or e.code >= 500):
                time.sleep(min(60, 5 * 2 ** (n - 1)))
                continue
            sys.exit(f"Erro da Runway ({e.code}): {corpo_erro}")
        except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
            if n < tentativas:
                time.sleep(min(60, 5 * 2 ** (n - 1)))
                continue
            sys.exit(f"Sem conexão com a Runway: {getattr(e, 'reason', e)}. "
                     "Se estiver no ambiente de nuvem do Claude, rode no computador da equipe.")


def uri(caminho):
    if caminho.startswith(("http://", "https://", "data:")):
        return caminho
    if not os.path.exists(caminho):
        sys.exit(f"arquivo não encontrado: {caminho}")
    tipo = mimetypes.guess_type(caminho)[0] or "image/png"
    with open(caminho, "rb") as f:
        dados = f.read()
    if len(dados) > 5 * 1024 * 1024:
        print("aviso: imagem acima de ~5 MB; se a API recusar, reduza o arquivo ou use uma URL https.", file=sys.stderr)
    return f"data:{tipo};base64,{base64.b64encode(dados).decode()}"


def esperar(tid, intervalo=6, limite=1800):
    inicio = time.time()
    while True:
        t = http("GET", f"/tasks/{tid}", tentativas=6)
        st = t.get("status")
        if st == "SUCCEEDED":
            return t
        if st in ("FAILED", "CANCELLED"):
            sys.exit(f"Tarefa {tid} terminou com {st}: {t.get('failure') or t.get('failureCode') or t}")
        if time.time() - inicio > limite:
            sys.exit(f"Tempo esgotado; a tarefa segue na Runway. Baixe depois com: runway.py status {tid} --saida <prefixo>")
        print(f"  {st or 'aguardando'}… {t.get('progress', '')}", file=sys.stderr)
        time.sleep(intervalo)


def baixar(urls, saida, ext):
    os.makedirs(os.path.dirname(os.path.abspath(saida)) or ".", exist_ok=True)
    arquivos = []
    for i, u in enumerate(urls, 1):
        destino = destino_livre(f"{saida}_{i}" if len(urls) > 1 else saida, ext)
        urllib.request.urlretrieve(u, destino)
        arquivos.append(destino)
    return arquivos


def c_imagem(a):
    prompt = ler_prompt(a)
    corpo = {"model": a.modelo, "promptText": prompt, "ratio": a.proporcao}
    refs = []
    for r in a.ref or []:
        tag, _, arq = r.partition("=")
        if not arq:
            sys.exit("use --ref tag=arquivo.png (e cite @tag no prompt)")
        refs.append({"uri": uri(arq), "tag": tag})
    if refs:
        corpo["referenceImages"] = refs
    if a.seed is not None:
        corpo["seed"] = a.seed
    t = http("POST", "/text_to_image", corpo)
    print(f"tarefa {t['id']}", file=sys.stderr)
    fim = esperar(t["id"])
    res = 1080 if max(int(x) for x in a.proporcao.split(":")) >= 1440 else 720
    custo = CREDITOS_IMG.get(a.modelo, {}).get(res)
    for arq in baixar(fim.get("output", []), a.saida, ".png"):
        registrar(a.saida, ferramenta="runway:imagem", modelo=a.modelo, prompt=prompt,
                  referencias=";".join(r.split("=", 1)[1] for r in a.ref or []),
                  parametros=f"ratio={a.proporcao} seed={a.seed}", arquivo=arq,
                  custo_estimado=f"{custo} créditos" if custo else "ver tabela Runway")
        print(arq)


def c_video(a):
    prompt = ler_prompt(a)
    if a.proporcao not in PROP_VIDEO:
        print(f"aviso: proporção {a.proporcao} fora da lista conhecida {PROP_VIDEO}", file=sys.stderr)
    if not 2 <= a.duracao <= 10:
        sys.exit("--duracao deve ficar entre 2 e 10 s")
    if a.modelo == "gen4_turbo" and a.duracao not in (5, 10):
        print("aviso: gen4_turbo costuma aceitar só 5 ou 10 s; a API explica se recusar.", file=sys.stderr)
    corpo = {"model": a.modelo, "promptText": prompt, "ratio": a.proporcao, "duration": a.duracao}
    if a.imagem:
        corpo["promptImage"] = uri(a.imagem)
        rota = "/image_to_video"
    elif a.modelo != "gen4.5":
        sys.exit("texto→vídeo sem imagem só com --modelo gen4.5")
    else:
        rota = "/text_to_video"
    if a.seed is not None:
        corpo["seed"] = a.seed
    t = http("POST", rota, corpo)
    print(f"tarefa {t['id']}", file=sys.stderr)
    fim = esperar(t["id"])
    custo = CREDITOS_S.get(a.modelo)
    for arq in baixar(fim.get("output", []), a.saida, ".mp4"):
        registrar(a.saida, ferramenta="runway:video", modelo=a.modelo, prompt=prompt, referencias=a.imagem or "",
                  parametros=f"ratio={a.proporcao} duracao={a.duracao}s seed={a.seed}", arquivo=arq,
                  custo_estimado=f"{custo * a.duracao} créditos" if custo else "ver tabela Runway")
        print(arq)


def c_status(a):
    t = http("GET", f"/tasks/{a.id}", tentativas=3)
    if not a.saida:
        print(json.dumps(t, ensure_ascii=False, indent=2))
        return
    if t.get("status") != "SUCCEEDED":
        sys.exit(f"tarefa {a.id} está {t.get('status')}; nada para baixar ainda")
    saidas = t.get("output", [])
    ext = ".mp4" if any(".mp4" in u.split("?")[0] for u in saidas) else ".png"
    for arq in baixar(saidas, a.saida, ext):
        registrar(a.saida, ferramenta="runway:recuperado", modelo="", prompt="", referencias="",
                  parametros=f"tarefa={a.id}", arquivo=arq, custo_estimado="já cobrado na tarefa original")
        print(arq)


def c_custo(a):
    if a.modelo in CREDITOS_S:
        cr = CREDITOS_S[a.modelo] * a.segundos
    elif a.modelo in CREDITOS_IMG:
        cr = CREDITOS_IMG[a.modelo][a.resolucao] * a.imagens
    else:
        sys.exit("modelo sem tabela local; confira em docs.dev.runwayml.com/guides/pricing")
    if cr <= 0:
        sys.exit("informe --segundos (vídeo) ou --imagens (imagem)")
    print(f"{cr} créditos ≈ US$ {cr * 0.01:.2f} (tabela local de referência; confira os preços atuais em dev.runwayml.com)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("imagem"); s.add_argument("--prompt"); s.add_argument("--prompt-arquivo")
    s.add_argument("--ref", action="append"); s.add_argument("--proporcao", default="1080:1920")
    s.add_argument("--modelo", default="gen4_image"); s.add_argument("--seed", type=int); s.add_argument("--saida", required=True)
    s.set_defaults(f=c_imagem)
    s = sp.add_parser("video"); s.add_argument("--imagem"); s.add_argument("--prompt"); s.add_argument("--prompt-arquivo")
    s.add_argument("--proporcao", default="720:1280"); s.add_argument("--duracao", type=int, default=5)
    s.add_argument("--modelo", default="gen4.5"); s.add_argument("--seed", type=int); s.add_argument("--saida", required=True)
    s.set_defaults(f=c_video)
    s = sp.add_parser("status"); s.add_argument("id"); s.add_argument("--saida", help="baixa o resultado com este prefixo")
    s.set_defaults(f=c_status)
    s = sp.add_parser("custo"); s.add_argument("--modelo", required=True); s.add_argument("--segundos", type=int, default=0)
    s.add_argument("--imagens", type=int, default=0); s.add_argument("--resolucao", type=int, default=1080, choices=[720, 1080])
    s.set_defaults(f=c_custo)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
