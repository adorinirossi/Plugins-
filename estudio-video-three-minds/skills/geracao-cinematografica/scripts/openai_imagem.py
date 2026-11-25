#!/usr/bin/env python3
"""Gera e edita imagens com a API da OpenAI (GPT Image). Só biblioteca padrão.

Chave: variável de ambiente OPENAI_API_KEY (nunca passe a chave como argumento).

  gerar   --prompt "..." | --prompt-arquivo p.txt  [--formato vertical|horizontal|quadrado|auto]
          [--qualidade low|medium|high] [--n 1] [--modelo gpt-image-2] --saida geracoes/P01
  editar  (mesmos) + --ref imagem.png [--ref outra.png ...]   (até 16 referências)

Saída: geracoes/P01_1.png, _2.png ... e linha em geracoes/registro.csv.
Se o arquivo já existir (ex.: a versão aprovada), grava P01_1_v2.png — nada é sobrescrito.
"""
import argparse, base64, json, mimetypes, os, sys, uuid, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registro import registrar, ler_prompt, destino_livre  # noqa: E402

API = "https://api.openai.com/v1/images"
TAMANHOS = {"vertical": "1024x1536", "horizontal": "1536x1024", "quadrado": "1024x1024", "auto": "auto"}


def chave():
    k = os.environ.get("OPENAI_API_KEY")
    if not k:
        sys.exit("OPENAI_API_KEY não definida. Configure a variável de ambiente no computador onde o script roda.")
    return k


def chamar(req):
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(corpo)["error"]["message"]
        except Exception:
            msg = corpo[:800]
        sys.exit(f"Erro da OpenAI ({e.code}): {msg}")
    except urllib.error.URLError as e:
        sys.exit(f"Sem conexão com a OpenAI: {e.reason}. Se estiver no ambiente de nuvem do Claude, rode no computador da equipe.")


def multipart(campos, arquivos):
    limite = uuid.uuid4().hex
    partes = []
    for nome, valor in campos.items():
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'.encode())
    for nome, caminho in arquivos:
        tipo = mimetypes.guess_type(caminho)[0] or "image/png"
        with open(caminho, "rb") as f:
            dados = f.read()
        cab = (f'--{limite}\r\nContent-Disposition: form-data; name="{nome}"; filename="{os.path.basename(caminho)}"\r\n'
               f"Content-Type: {tipo}\r\n\r\n").encode()
        partes.append(cab + dados + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    return b"".join(partes), f"multipart/form-data; boundary={limite}"


def salvar(resp, saida):
    os.makedirs(os.path.dirname(os.path.abspath(saida)) or ".", exist_ok=True)
    arquivos = []
    for i, item in enumerate(resp.get("data", []), 1):
        destino = destino_livre(f"{saida}_{i}", ".png")
        if item.get("b64_json"):
            with open(destino, "wb") as f:
                f.write(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            urllib.request.urlretrieve(item["url"], destino)
        else:
            continue
        arquivos.append(destino)
    if not arquivos:
        sys.exit("A API não devolveu imagens (pode ter sido bloqueada pelo filtro de conteúdo).")
    return arquivos


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    for nome in ("gerar", "editar"):
        s = sp.add_parser(nome)
        s.add_argument("--prompt"); s.add_argument("--prompt-arquivo")
        s.add_argument("--formato", default="vertical", choices=TAMANHOS)
        s.add_argument("--qualidade", default="high", choices=["low", "medium", "high", "auto"])
        s.add_argument("--n", type=int, default=1)
        s.add_argument("--modelo", default="gpt-image-2")
        s.add_argument("--saida", required=True, help="prefixo do arquivo, ex.: geracoes/P01")
        if nome == "editar":
            s.add_argument("--ref", action="append", required=True, help="imagem de referência (repita até 16)")
    a = p.parse_args()
    if not 1 <= a.n <= 10:
        sys.exit("--n deve ficar entre 1 e 10")
    prompt = ler_prompt(a)
    k = chave()
    params = {"model": a.modelo, "prompt": prompt, "size": TAMANHOS[a.formato], "quality": a.qualidade, "n": a.n}

    if a.cmd == "gerar":
        req = urllib.request.Request(f"{API}/generations", data=json.dumps(params).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
        refs = []
    else:
        if len(a.ref) > 16:
            sys.exit("máximo de 16 referências")
        for r in a.ref:
            if not os.path.exists(r):
                sys.exit(f"referência não encontrada: {r}")
        corpo, tipo = multipart({k2: str(v) for k2, v in params.items()}, [("image[]", r) for r in a.ref])
        req = urllib.request.Request(f"{API}/edits", data=corpo, method="POST",
                                     headers={"Authorization": f"Bearer {k}", "Content-Type": tipo})
        refs = a.ref

    arquivos = salvar(chamar(req), a.saida)
    for arq in arquivos:
        registrar(a.saida, ferramenta=f"openai:{a.cmd}", modelo=a.modelo, prompt=prompt, referencias=";".join(refs),
                  parametros=f"size={params['size']} quality={a.qualidade}", arquivo=arq,
                  custo_estimado="ver calculadora OpenAI")
        print(arq)


if __name__ == "__main__":
    main()
