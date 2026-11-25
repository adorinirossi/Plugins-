#!/usr/bin/env python3
"""Operação de canal — calendário, kit do dia, análise de métricas e painel.

Só biblioteca padrão. Subcomandos:
  calendario  monta calendario.csv a partir das pautas aprovadas
  kit         gera a pasta do dia (ou intervalo) com vídeo, capa e postar.md
  analisar    normaliza exportações (Meta, TikTok, YouTube, manual), calcula índice,
              atributos e melhor horário; escreve relatório .md e .json
  painel      gera painel HTML de uma página a partir do .json
  similaridade compara roteiros novos com os anteriores (trava de originalidade)
"""
import argparse, csv, glob, html, json, math, os, re, shutil, statistics, sys, tempfile, unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

# ---------- utilidades ----------

def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096); f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(f, dialect=dialect))

def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    pasta = os.path.dirname(os.path.abspath(path))
    with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", dir=pasta, delete=False) as f:
        temporario = f.name
        try:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
            f.close()
            os.replace(temporario, path)
        finally:
            if os.path.exists(temporario):
                os.unlink(temporario)

def num(v):
    if v is None: return None
    s = str(v).strip().replace("%", "")
    if not s or s in {"-", "--"}: return None
    mult = 1
    if s[-1:].lower() in "km" and re.match(r"^[\d.,]+[kKmM]$", s):
        mult = 1000 if s[-1].lower() == "k" else 1_000_000; s = s[:-1]
    if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", s):  # 1.234,5
        s = s.replace(".", "").replace(",", ".")
    elif re.match(r"^\d+,\d+$", s):
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        valor = float(s) * mult
        return valor if math.isfinite(valor) else None
    except ValueError:
        return None

def parse_dt(v):
    s = str(v or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
                "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p",
                "%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%d %b %Y"):
        for cand in (s, s[:19], s[:16], s[:10]):
            try: return datetime.strptime(cand.strip(), fmt)
            except ValueError: pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", s)
    if m: return datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M")
    return None

# ---------- calendario ----------

def video_aprovado(pauta):
    return norm(pauta.get("status")) == "aprovado"

def cmd_calendario(a):
    pautas = [p for p in read_csv(a.pautas) if video_aprovado(p)]
    if not pautas: sys.exit("Nenhum vídeo com aprovação final em " + a.pautas)
    # alterna formatos para não repetir seguidos
    fila, restantes = [], pautas[:]
    while restantes:
        ult = fila[-1] if fila else {}
        dif = lambda p: p.get("formato") != ult.get("formato") and (not p.get("abertura_tipo") or p.get("abertura_tipo") != ult.get("abertura_tipo"))
        idx = next((i for i, p in enumerate(restantes) if dif(p)),
                   next((i for i, p in enumerate(restantes) if p.get("formato") != ult.get("formato")), 0))
        fila.append(restantes.pop(idx))
    try:
        horarios = list(dict.fromkeys(datetime.strptime(h.strip(), "%H:%M").strftime("%H:%M")
                                     for h in a.horarios.split(",")))
        dia = datetime.strptime(a.inicio, "%Y-%m-%d").date()
    except ValueError:
        sys.exit("Use horários HH:MM e data inicial AAAA-MM-DD.")
    if not 1 <= a.por_dia <= len(horarios):
        sys.exit("--por-dia deve ser positivo e caber nos horários distintos informados.")
    redes = list(dict.fromkeys(r.strip() for r in a.redes.split(",") if r.strip()))
    if not redes:
        sys.exit("Informe ao menos uma rede.")
    existentes = read_csv(a.saida) if os.path.exists(a.saida) else []
    ja = {(r["id"], r["rede"]) for r in existentes}
    ocupados = defaultdict(set)
    for r in existentes:
        ocupados[r["data"]].add(r["hora"])
    linhas = list(existentes)
    for p in fila:
        pendentes = [r for r in redes if (p["id"], r) not in ja]
        if not pendentes:
            continue
        while True:
            usados = ocupados[dia.isoformat()]
            livres = [h for h in horarios if h not in usados]
            if len(usados) < a.por_dia and livres:
                break
            dia += timedelta(days=1)
        hora = livres[0]
        usados.add(hora)
        for r in pendentes:
            linhas.append({"id": p["id"], "rede": r, "data": dia.isoformat(), "hora": hora,
                           "status": "pendente", "link": "", "observacao": ""})
            ja.add((p["id"], r))
    linhas.sort(key=lambda r: (r["data"], r["hora"], r["rede"]))
    campos = dict.fromkeys(["id", "rede", "data", "hora", "status", "link", "observacao"])
    for r in existentes:
        campos.update(dict.fromkeys(r))
    write_csv(a.saida, linhas, campos)
    print(f"{a.saida}: {len(linhas)} linhas ({len(linhas) - len(existentes)} novas)")

# ---------- kit ----------

LIMITE_IA = "Ligar o rótulo de conteúdo gerado por IA se o vídeo tiver imagens/vozes sintéticas realistas."

def com_utm(link, rede, pid):
    """Acrescenta UTM ao link do site da editora (preserva parâmetros existentes)."""
    partes = urlsplit(link.strip())
    if not partes.scheme.startswith("http"):
        return link
    q = [(k, v) for k, v in parse_qsl(partes.query) if not k.startswith("utm_")]
    q += [("utm_source", rede), ("utm_medium", "social"), ("utm_campaign", pid)]
    return urlunsplit(partes._replace(query=urlencode(q)))

def cmd_kit(a):
    pautas = {p["id"]: p for p in read_csv(a.pautas)}
    cal = read_csv(a.calendario)
    ini = datetime.strptime(a.data, "%Y-%m-%d").date()
    fim = datetime.strptime(a.ate, "%Y-%m-%d").date() if a.ate else ini
    if fim < ini:
        sys.exit("--ate deve ser igual ou posterior a --data.")
    dias = defaultdict(list)
    for r in cal:
        try:
            dd = datetime.strptime((r.get("data") or "").strip(), "%Y-%m-%d").date()
        except ValueError:
            print(f"Kit ignorou linha do calendário com data inválida: {r}", file=sys.stderr); continue
        if ini <= dd <= fim and norm(r.get("status") or "pendente") == "pendente":
            if video_aprovado(pautas.get(r["id"], {})):
                dias[dd].append(r)
            else:
                print(f"Kit ignorou {r['id']} ({r['rede']}): falta aprovação final.", file=sys.stderr)
    if not dias: print("Nada pendente no período."); return
    for dd, linhas in sorted(dias.items()):
        pasta = os.path.join(a.saida, dd.isoformat()); os.makedirs(pasta, exist_ok=True)
        md = [f"# Kit de postagem — {dd.strftime('%d/%m/%Y')}", ""]
        for pid in dict.fromkeys(l["id"] for l in linhas):
            p = pautas.get(pid, {})
            md += [f"## {pid} — {p.get('titulo', '(sem título)')}", ""]
            for l in [x for x in linhas if x["id"] == pid]:
                rede = l["rede"]
                arq = p.get(f"arquivo_{rede}") or p.get("arquivo_final", "")
                md += [f"### {rede.capitalize()} — {l['hora']}", ""]
                if any(c in pid or c in rede for c in ("/", "\\", "\x00")):
                    sys.exit(f"ID ou rede inválidos para o kit: {pid!r}, {rede!r}")
                if arq:
                    src = arq if os.path.isabs(arq) else os.path.join(a.lotes, arq)
                    if os.path.isfile(src):
                        dst = f"{pid}-{rede}{os.path.splitext(src)[1]}"
                        shutil.copy2(src, os.path.join(pasta, dst)); md.append(f"Arquivo: `{dst}`")
                    else:
                        md.append(f"> ⚠️ arquivo não encontrado: {arq}")
                else:
                    md.append("> ⚠️ sem arquivo final registrado")
                if not p.get(f"arquivo_{rede}") and arq:
                    md.append("> ℹ️ mesmo arquivo-base das outras redes — confira se o texto inicial foi trocado")
                capa = p.get(f"capa_{rede}") or p.get("capa")
                if capa:
                    src = os.path.join(a.lotes, capa)
                    if os.path.isfile(src):
                        dst = f"{pid}-{rede}-capa{os.path.splitext(src)[1]}"
                        shutil.copy2(src, os.path.join(pasta, dst))
                        md.append(f"Capa: `{dst}`")
                    else:
                        md.append(f"> ⚠️ capa não encontrada: {capa}")
                ti = p.get(f"texto_inicial_{rede}")
                if ti: md.append(f"Texto inicial na tela: **{ti}**")
                leg = p.get(f"legenda_{rede}") or p.get("legenda") or p.get("gancho_texto", "")
                if not p.get(f"legenda_{rede}"): md.append("> ⚠️ legenda genérica — escrever versão para esta rede")
                md += ["", "```", leg.strip(), "```", ""]
                if rede == "youtube":
                    md += [f"Título do Shorts: {(p.get('titulo_youtube') or p.get('titulo', ''))[:60]}", ""]
                link = p.get(f"link_{rede}") or p.get("link")
                if link:
                    md += [f"Link com rastreio (bio/descrição): {com_utm(link, rede, pid)}", ""]
            if p.get("fonte"): md += [f"Fonte (descrição/comentário fixado): {p['fonte']}", ""]
            md += [f"- [ ] {LIMITE_IA}", "- [ ] Publicado/agendado em todas as redes acima", "- [ ] Links colados no calendário", ""]
        with open(os.path.join(pasta, "postar.md"), "w", encoding="utf-8") as f: f.write("\n".join(md))
        print("kit:", pasta)

# ---------- analisar ----------

SINONIMOS = {
    "id": ["id", "id pauta", "pauta"],
    "titulo": ["titulo", "titulo do video", "title", "video title", "descricao", "description", "legenda", "caption", "conteudo", "content"],
    "data": ["horario de publicacao", "publish time", "post time", "data de publicacao", "data", "date", "published", "hora de publicacao", "horario da publicacao"],
    "hora": ["hora"],
    "rede": ["rede", "plataforma", "platform", "network"],
    "views": ["visualizacoes", "views", "video views", "reproducoes", "plays", "impressoes", "impressions"],
    "alcance": ["alcance", "reach", "contas alcancadas"],
    "curtidas": ["curtidas", "likes", "reacoes", "gostei", "reactions"],
    "comentarios": ["comentarios", "comments"],
    "compartilhamentos": ["compartilhamentos", "shares", "compartilhados"],
    "salvamentos": ["salvamentos", "saves", "salvos", "favoritos", "favorites"],
    "seguidores": ["seguidores", "seguimentos", "follows", "new followers", "inscritos", "subscribers", "subscribers gained", "seguidores ganhos"],
    "retencao": ["retencao", "assistiram ao video completo", "watched full video", "full video watched", "percentual medio visualizado", "average percentage viewed"],
    "retencao_3s": ["retencao 3s", "retencao_3s", "3 second", "3s"],
    "queda_seg": ["queda seg", "queda_seg"],
    "tempo_medio": ["tempo medio", "average watch time", "duracao media da visualizacao", "average view duration", "tempo medio de visualizacao"],
}

def mapear_colunas(header):
    m = {}
    nh = {h: norm(h) for h in header}
    for alvo, sins in SINONIMOS.items():
        for s in sins:  # exato primeiro
            hit = next((h for h, n in nh.items() if n == s and h not in m.values()), None)
            if hit: m[alvo] = hit; break
        if alvo not in m and alvo not in ("id", "hora", "rede"):
            for s in sins:
                hit = next((h for h, n in nh.items() if s in n and h not in m.values()), None)
                if hit: m[alvo] = hit; break
    return m

def rede_do_arquivo(path, header):
    n = norm(os.path.basename(path)) + " " + " ".join(norm(h) for h in header)
    for r, chaves in (("tiktok", ["tiktok"]), ("youtube", ["youtube", "inscritos", "subscribers"]),
                      ("instagram", ["instagram", "meta", "reel"]), ("facebook", ["facebook"])):
        if any(k in n for k in chaves): return r
    return ""

def faixa(h):
    return "madrugada" if h < 6 else "manha" if h < 11 else "almoco" if h < 14 else "tarde" if h < 18 else "noite"

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

def cmd_analisar(a):
    pautas = {p["id"]: p for p in read_csv(a.pautas)}
    cal = read_csv(a.calendario) if a.calendario and os.path.exists(a.calendario) else []
    por_rede_data = defaultdict(list)
    for c in cal: por_rede_data[(c["rede"], c["data"])].append(c["id"])
    arquivos = sorted({f for g in a.metricas for f in glob.glob(g)})
    if not arquivos: sys.exit("Nenhum arquivo de métricas encontrado.")
    registros, sem_vinculo = {}, []
    for path in arquivos:
        rows = read_csv(path)
        if not rows: continue
        mp = mapear_colunas(rows[0].keys())
        rede_padrao = rede_do_arquivo(path, rows[0].keys())
        for r in rows:
            g = lambda k: r.get(mp[k]) if k in mp else None
            rede = norm(g("rede")) or rede_padrao or "?"
            dt = parse_dt(f"{g('data') or ''} {g('hora') or ''}".strip()) or parse_dt(g("data"))
            pid = (g("id") or "").strip()
            if pid not in pautas: pid = ""
            if not pid and dt:
                cands = por_rede_data.get((rede, dt.date().isoformat()), [])
                if len(cands) == 1: pid = cands[0]
            if not pid:
                t = norm(g("titulo"))
                if t:
                    for k, p in pautas.items():
                        for campo in ("titulo", "gancho_texto"):
                            v = norm(p.get(campo))
                            if v and len(v) > 8 and (v[:40] in t or t[:40] in v): pid = k; break
                        if pid: break
            m = {k: num(g(k)) for k in ("views", "alcance", "curtidas", "comentarios", "compartilhamentos", "salvamentos", "seguidores", "retencao", "retencao_3s", "queda_seg", "tempo_medio")}
            if m["views"] is None: m["views"] = m["alcance"]
            if m["views"] is None and all(m[c] is None for c in ("retencao", "retencao_3s", "queda_seg")): continue
            if not pid:
                sem_vinculo.append({"arquivo": os.path.basename(path), "titulo": (g("titulo") or "")[:60], "rede": rede}); continue
            if not dt:
                c = next((c for c in cal if c["id"] == pid and c["rede"] == rede), None)
                if c: dt = parse_dt(f"{c['data']} {c['hora']}")
            prev = registros.get((pid, rede), {})
            novo = {"id": pid, "rede": rede, "dt": dt or prev.get("dt"), **m}
            for k, v in prev.items():  # arquivos complementares (ex.: manual com retenção) somam campos
                if novo.get(k) is None and v is not None: novo[k] = v
            registros[(pid, rede)] = novo
    regs = [r for r in registros.values() if r.get("views")]
    if not regs: sys.exit("Nenhuma linha de métricas ligada a uma pauta. Confira ids/calendário.")

    # índice relativo ao canal (percentil por componente)
    def taxa(r, k):
        return r[k] / r["views"] if r[k] is not None else None
    comps = {
        "views": (0.30, lambda r: r["views"]),
        "comp": (0.25, lambda r: taxa(r, "compartilhamentos")),
        "salv": (0.20, lambda r: taxa(r, "salvamentos")),
        "seg": (0.15, lambda r: taxa(r, "seguidores")),
        "ret": (0.10, lambda r: r["retencao"] if r["retencao"] is not None else None),
    }
    def pct(v, vals):
        # percentil de posição média: empates recebem a mesma nota, sem inflar todos para 100
        abaixo = sum(1 for x in vals if x < v); iguais = sum(1 for x in vals if x == v)
        return 100 * (abaixo + 0.5 * iguais) / len(vals)
    por_rede = defaultdict(list)
    for r in regs: por_rede[r["rede"]].append(r)
    for nome, (peso, f) in comps.items():
        vals = sorted(v for v in (f(r) for r in regs) if v is not None)
        for r in regs:
            v = f(r)
            grupo = vals
            if nome == "views" and len(por_rede[r["rede"]]) >= 3:
                # views comparadas dentro da mesma rede (o TikTok costuma ter mais views que as outras)
                grupo = sorted(x["views"] for x in por_rede[r["rede"]])
            r["_" + nome] = None if v is None or not grupo else pct(v, grupo)
    for r in regs:
        tot = sum(p for n, (p, _) in comps.items() if r["_" + n] is not None)
        r["indice"] = round(sum(r["_" + n] * p for n, (p, _) in comps.items() if r["_" + n] is not None) / tot, 1) if tot else 0
        p = pautas.get(r["id"], {})
        for k in ("pilar", "formato", "gancho_tipo", "abertura_tipo", "estrutura", "duracao_alvo", "trilha", "titulo", "hipotese"):
            r[k] = p.get(k, "")
    media = statistics.mean(r["indice"] for r in regs)

    def agrupa(chave):
        g = defaultdict(list)
        for r in regs:
            v = r.get(chave) or "—"
            g[v].append(r["indice"])
        return sorted(({"valor": k, "n": len(v), "media": round(statistics.mean(v), 1),
                        "dif": round(statistics.mean(v) - media, 1),
                        "leitura": "hipótese (n<3)" if len(v) < 3 else ("empate" if abs(statistics.mean(v) - media) < 15 else ("acima" if statistics.mean(v) > media else "abaixo"))}
                       for k, v in g.items()), key=lambda x: -x["media"])

    atributos = {k: agrupa(k) for k in ("rede", "formato", "gancho_tipo", "abertura_tipo", "estrutura", "pilar", "duracao_alvo", "trilha")}
    atributos = {k: v for k, v in atributos.items() if not (len(v) == 1 and v[0]["valor"] == "—")}
    retencao = {}
    for chave in ("formato", "abertura_tipo", "gancho_tipo"):
        g = defaultdict(list)
        for r in regs:
            if any(r.get(c) is not None for c in ("retencao_3s", "retencao", "queda_seg")):
                g[r.get(chave) or "—"].append(r)
        linhas = []
        for v, rs in g.items():
            med = lambda c: round(statistics.mean([x[c] for x in rs if x.get(c) is not None]), 1) if any(x.get(c) is not None for x in rs) else None
            linhas.append({"valor": v, "n": len(rs), "ret3s": med("retencao_3s"), "ret_final": med("retencao"), "queda_seg": med("queda_seg")})
        if linhas and not (len(linhas) == 1 and linhas[0]["valor"] == "—"): retencao[chave] = sorted(linhas, key=lambda x: -(x["ret3s"] or 0))
    horario = defaultdict(lambda: defaultdict(list))
    for r in regs:
        if r["dt"]:
            horario[r["rede"]][f"{DIAS[r['dt'].weekday()]} {faixa(r['dt'].hour)}"].append(r["indice"])
    melhor = {rede: sorted(({"quando": k, "n": len(v), "media": round(statistics.mean(v), 1)} for k, v in d.items()), key=lambda x: -x["media"])[:5]
              for rede, d in horario.items()}
    ordem = sorted(regs, key=lambda r: -r["indice"])
    testes = [r for r in regs if r.get("hipotese")]

    out = {"gerado_em": datetime.now().isoformat(timespec="minutes"), "n_videos": len({r['id'] for r in regs}),
           "n_registros": len(regs), "media_indice": round(media, 1),
           "totais": {k: int(sum(r[k] or 0 for r in regs)) for k in ("views", "curtidas", "comentarios", "compartilhamentos", "salvamentos", "seguidores")},
           "videos": [{k: (v.isoformat(timespec="minutes") if isinstance(v, datetime) else v) for k, v in r.items() if not k.startswith("_")} for r in ordem],
           "atributos": atributos, "retencao": retencao, "melhor_horario": melhor, "sem_vinculo": sem_vinculo}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, indent=1)

    L = [f"# Relatório do canal — {date.today().strftime('%d/%m/%Y')}", "",
         f"{out['n_videos']} vídeos · {out['n_registros']} posts · índice médio {out['media_indice']}", "",
         "| Total | " + " | ".join(out["totais"].keys()) + " |", "|---|" + "---|" * len(out["totais"]),
         "| | " + " | ".join(f"{v:,}".replace(",", ".") for v in out["totais"].values()) + " |", "",
         "## Top 3", ""]
    fmt = lambda r: f"- **{r['id']}** ({r['rede']}) índice {r['indice']} · {int(r['views']):,} views · {r['formato']} / {r['gancho_tipo']} / {r['pilar']} — {r['titulo']}".replace(",", ".")
    L += [fmt(r) for r in ordem[:3]] + ["", "## Bottom 3", ""] + ([fmt(r) for r in ordem[max(3, len(ordem) - 3):]] or ["- (menos de 4 posts — sem bottom separado)"]) + [""]
    for k, linhas in atributos.items():
        L += [f"## Por {k}", "", "| valor | n | índice | dif. | leitura |", "|---|---|---|---|---|"]
        L += [f"| {x['valor']} | {x['n']} | {x['media']} | {x['dif']:+} | {x['leitura']} |" for x in linhas] + [""]
    for k, linhas in retencao.items():
        L += [f"## Retenção por {k}", "", "| valor | n | passou de 3 s (%) | até o fim (%) | queda média (s) |", "|---|---|---|---|---|"]
        L += [f"| {x['valor']} | {x['n']} | {x['ret3s'] if x['ret3s'] is not None else '—'} | {x['ret_final'] if x['ret_final'] is not None else '—'} | {x['queda_seg'] if x['queda_seg'] is not None else '—'} |" for x in linhas] + [""]
    L += ["## Melhor horário (por rede)", ""]
    for rede, xs in melhor.items():
        L.append(f"- **{rede}:** " + "; ".join(f"{x['quando']} ({x['media']}, n={x['n']})" for x in xs))
    if testes:
        L += ["", "## Testes do lote", ""]
        L += [f"- {r['id']}: {r['hipotese']} → índice {r['indice']} ({r['indice'] - media:+.1f} vs média)" for r in testes]
    if sem_vinculo:
        L += ["", f"## Sem vínculo com pauta ({len(sem_vinculo)})", ""] + [f"- {s['rede']} · {s['titulo']} ({s['arquivo']})" for s in sem_vinculo[:20]]
    L += ["", "_Índice 0–100 relativo ao próprio canal: 30% views (comparadas dentro da mesma rede quando ela tem 3+ posts), 25% compartilhamentos/view, 20% salvamentos/view, 15% seguidores/view, 10% retenção. Métricas ausentes têm o peso redistribuído entre os componentes disponíveis. n<3 = hipótese; diferença <15 = empate._"]
    os.makedirs(os.path.dirname(os.path.abspath(a.saida)), exist_ok=True)
    with open(a.saida, "w", encoding="utf-8") as f: f.write("\n".join(L))
    print(f"relatório: {a.saida} ({out['n_registros']} posts, {len(sem_vinculo)} sem vínculo)")

# ---------- painel ----------

def cmd_painel(a):
    d = json.load(open(a.json, encoding="utf-8"))
    cal = read_csv(a.calendario) if a.calendario and os.path.exists(a.calendario) else []
    hoje = date.today().isoformat()
    fila = [c for c in cal if c["data"] >= hoje][:21]
    e = html.escape
    def barra(v): return f'<div class="bar"><span style="width:{max(2, min(100, v))}%"></span></div>'
    vids = "".join(f"<tr><td>{e(v['id'])}<small>{e(v.get('titulo',''))}</small></td><td>{e(v['rede'])}</td><td>{int(v['views']):,}</td><td>{barra(v['indice'])}{v['indice']}</td></tr>".replace(",", ".") for v in d["videos"][:15])
    attrs = ""
    for k, linhas in d["atributos"].items():
        if len(linhas) < 2: continue
        attrs += f"<h3>{e(k)}</h3><table>" + "".join(f"<tr><td>{e(str(x['valor']))}</td><td>{barra(x['media'])}</td><td>{x['media']}</td><td class='{ 'pos' if x['dif']>0 else 'neg'}'>{x['dif']:+}</td><td><small>n={x['n']}</small></td></tr>" for x in linhas) + "</table>"
    hor = "".join(f"<li><b>{e(r)}</b>: " + ", ".join(f"{e(x['quando'])} ({x['media']})" for x in xs[:3]) + "</li>" for r, xs in d["melhor_horario"].items())
    fl = "".join(f"<tr><td>{e(c['data'][8:10])}/{e(c['data'][5:7])} {e(c['hora'])}</td><td>{e(c['rede'])}</td><td>{e(c['id'])}</td><td class='st-{e(c['status'])}'>{e(c['status'])}</td></tr>" for c in fila)
    tot = "".join(f"<div class='kpi'><b>{v:,}</b><span>{e(k)}</span></div>".replace(",", ".") for k, v in d["totais"].items())
    page = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(a.titulo)}</title><style>
:root{{--bg:#faf7f2;--fg:#2b2530;--mut:#7a7180;--ac:#6b4a8a;--ok:#3f8f5a;--bad:#b4534b;--line:#e7e0d8}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#1d1a21;--fg:#eee8f2;--mut:#a79fae;--ac:#a98bd0;--ok:#6cc08a;--bad:#e08a82;--line:#38323f}}}}
:root[data-theme=dark]{{--bg:#1d1a21;--fg:#eee8f2;--mut:#a79fae;--ac:#a98bd0;--ok:#6cc08a;--bad:#e08a82;--line:#38323f}}
body{{font:15px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0 auto;padding:20px 16px;max-width:760px}}
td{{overflow-wrap:anywhere}}@media(max-width:420px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
h1{{font-size:22px;margin:0 0 4px}}h2{{font-size:17px;margin:28px 0 8px}}h3{{font-size:13px;text-transform:uppercase;color:var(--mut);margin:16px 0 4px}}
.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}.kpi{{border:1px solid var(--line);border-radius:10px;padding:10px}}.kpi b{{display:block;font-size:19px}}.kpi span{{color:var(--mut);font-size:12px}}
table{{width:100%;border-collapse:collapse}}td{{padding:6px 4px;border-bottom:1px solid var(--line);vertical-align:middle}}td small{{display:block;color:var(--mut)}}
.bar{{display:inline-block;width:70px;height:6px;background:var(--line);border-radius:3px;margin-right:6px;vertical-align:middle}}.bar span{{display:block;height:100%;background:var(--ac);border-radius:3px}}
.pos{{color:var(--ok)}}.neg{{color:var(--bad)}}.st-publicado,.st-agendado{{color:var(--ok)}}.st-pendente{{color:var(--mut)}}.st-falhou{{color:var(--bad)}}
.mut{{color:var(--mut);font-size:13px}}</style></head><body>
<h1>{e(a.titulo)}</h1><div class="mut">Atualizado em {e(d['gerado_em'].replace('T',' '))} · {d['n_videos']} vídeos · índice médio {d['media_indice']}</div>
<h2>Totais</h2><div class="kpis">{tot}</div>
<h2>Próximos posts</h2><table>{fl or '<tr><td class=mut>Fila vazia</td></tr>'}</table>
<h2>Vídeos por índice</h2><table>{vids}</table>
<h2>O que funciona</h2>{attrs}
<h2>Melhor horário</h2><ul>{hor}</ul>
<p class="mut">Índice 0–100 relativo ao próprio canal. Grupos com n&lt;3 são hipótese; diferença &lt;15 é empate.</p>
</body></html>"""
    with open(a.saida, "w", encoding="utf-8") as f: f.write(page)
    print("painel:", a.saida)

# ---------- similaridade ----------

def _tokens(t):
    return norm(t).split()

def _shingles(t, k=3):
    w = _tokens(t)
    return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}

def _abertura(t):
    for linha in t.splitlines():
        l = linha.strip().strip("#|*- ")
        if len(l) > 15: return l[:90]
    return ""

def _ler_roteiros(pasta, excluir=None):
    out = {}
    for f in glob.glob(os.path.join(pasta, "**", "*"), recursive=True):
        if f.lower().endswith((".md", ".txt")) and os.path.isfile(f):
            if excluir and os.path.abspath(f).startswith(os.path.abspath(excluir) + os.sep): continue
            if os.path.basename(f).lower() in ("postar.md",): continue
            out[f] = open(f, encoding="utf-8", errors="ignore").read()
    return out

def cmd_similaridade(a):
    novos = _ler_roteiros(a.novos)
    antigos = _ler_roteiros(a.anteriores, excluir=a.novos) if a.anteriores else {}
    if not novos: sys.exit("Nenhum roteiro .md/.txt em " + a.novos)
    sh = {f: _shingles(t) for f, t in {**novos, **antigos}.items()}
    pares = []
    nl = list(novos)
    for i, f in enumerate(nl):
        alvos = nl[i + 1:] + list(antigos)
        for g in alvos:
            A, B = sh[f], sh[g]
            if not A or not B: continue
            j = len(A & B) / len(A | B)
            pares.append((j, f, g))
    pares.sort(reverse=True)
    acima = [p for p in pares if p[0] >= a.limite]
    rel = os.path.relpath
    L = [f"# Teste de semelhança — {date.today().strftime('%d/%m/%Y')}", "",
         f"{len(novos)} roteiros novos comparados com {len(antigos)} anteriores · limite {a.limite}", "",
         f"**{len(acima)} par(es) acima do limite** — reescrever abertura, estrutura ou ângulo." if acima else "Nenhum par acima do limite.", "",
         "| semelhança | novo | comparado com | abertura do novo | abertura do outro |", "|---|---|---|---|---|"]
    for j, f, g in pares[:15]:
        L.append(f"| {j:.2f}{' ⚠️' if j >= a.limite else ''} | {rel(f)} | {rel(g)} | {_abertura(novos[f])} | {_abertura(novos.get(g) or antigos.get(g, ''))} |")
    # aberturas repetidas (mesmas 5 primeiras palavras)
    ini = defaultdict(list)
    for f, t in novos.items():
        ini[" ".join(_tokens(_abertura(t))[:5])].append(rel(f))
    rep = {k: v for k, v in ini.items() if k and len(v) > 1}
    if rep:
        L += ["", "## Aberturas com o mesmo começo", ""] + [f"- “{k}…”: {', '.join(v)}" for k, v in rep.items()]
    txt = "\n".join(L)
    if a.saida:
        os.makedirs(os.path.dirname(os.path.abspath(a.saida)), exist_ok=True)
        open(a.saida, "w", encoding="utf-8").write(txt)
    print(txt)
    if acima: sys.exit(2)

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("calendario"); c.add_argument("--pautas", required=True); c.add_argument("--inicio", required=True)
    c.add_argument("--por-dia", type=int, default=1); c.add_argument("--horarios", default="12:00,19:30")
    c.add_argument("--redes", default="instagram,tiktok,youtube"); c.add_argument("--saida", default="calendario.csv")
    k = sp.add_parser("kit"); k.add_argument("--pautas", required=True); k.add_argument("--calendario", required=True)
    k.add_argument("--data", required=True); k.add_argument("--ate"); k.add_argument("--lotes", default="lotes"); k.add_argument("--saida", default="kits")
    n = sp.add_parser("analisar"); n.add_argument("--pautas", required=True); n.add_argument("--calendario")
    n.add_argument("--metricas", nargs="+", required=True); n.add_argument("--saida", required=True); n.add_argument("--json")
    p = sp.add_parser("painel"); p.add_argument("--json", required=True); p.add_argument("--calendario")
    p.add_argument("--saida", default="painel.html"); p.add_argument("--titulo", default="Painel do canal")
    s2 = sp.add_parser("similaridade"); s2.add_argument("--novos", required=True); s2.add_argument("--anteriores")
    s2.add_argument("--limite", type=float, default=0.45); s2.add_argument("--saida")
    a = ap.parse_args()
    {"calendario": cmd_calendario, "kit": cmd_kit, "analisar": cmd_analisar, "painel": cmd_painel, "similaridade": cmd_similaridade}[a.cmd](a)

if __name__ == "__main__":
    main()
