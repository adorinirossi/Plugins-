"""Registro de gerações compartilhado pelos scripts (geracoes/registro.csv ao lado da saída)."""
import csv, datetime, os

CAMPOS = ["data", "ferramenta", "modelo", "prompt", "referencias", "parametros", "arquivo", "custo_estimado"]


def registrar(saida_base, **dados):
    pasta = os.path.dirname(os.path.abspath(saida_base)) or "."
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, "registro.csv")
    novo = not os.path.exists(caminho)
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        linha = {k: dados.get(k, "") for k in CAMPOS}
        linha["data"] = datetime.datetime.now().isoformat(timespec="seconds")
        w.writerow(linha)
    return caminho


def destino_livre(base, ext):
    """Nunca sobrescreve uma geração anterior (pode ser a aprovada): base.ext, base_v2.ext, base_v3.ext..."""
    caminho = f"{base}{ext}"
    n = 2
    while os.path.exists(caminho):
        caminho = f"{base}_v{n}{ext}"
        n += 1
    return caminho


def ler_prompt(args):
    if getattr(args, "prompt_arquivo", None):
        with open(args.prompt_arquivo, encoding="utf-8") as f:
            return f.read().strip()
    if getattr(args, "prompt", None):
        return args.prompt.strip()
    raise SystemExit("informe --prompt ou --prompt-arquivo")
