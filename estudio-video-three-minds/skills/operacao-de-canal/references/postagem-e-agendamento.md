# Postagem e agendamento — sem agendador pago

O plugin faz o que um agendador pago faria (calendário, fila, melhor horário, conferência, relatório) com ferramentas gratuitas. A equipe faz **uma ação manual por dia** (ou uma por semana, se preferir agendar tudo de uma vez nos agendadores nativos). Só entram vídeos com status `aprovado` e um "pode agendar" explícito para o lote.

## O que substitui cada função de um agendador pago

| Função | Como o plugin faz |
|---|---|
| Calendário e fila | `canal.py calendario` → `calendario.csv` + painel HTML |
| Kit pronto para postar | `canal.py kit` → pasta do dia com vídeo, capa, legenda por rede e horário |
| Publicar/agendar | equipe, nos agendadores nativos gratuitos (abaixo) — 5–10 min por dia |
| Lembrete | tarefa agendada da manhã avisa que o kit do dia está pronto |
| Melhor horário | `canal.py analisar` calcula por rede, dia e faixa de horário com os dados do próprio canal |
| Métricas | exportação gratuita das plataformas (CSV) ou prints → `canal.py analisar` |
| Relatório e painel | `relatorios/AAAA-MM-DD.md` + `canal.py painel` (HTML) |
| Conferir se postou | equipe marca no kit (`publicado` + link); a tarefa da noite cobra o que faltar |
| Link com rastreio | coluna `link` (ou `link_<rede>`) em `pautas.csv`; o kit escreve o link com UTM (`utm_source=<rede>&utm_medium=social&utm_campaign=<id>`) no `postar.md` |
| Pesquisa de hashtags/tendências | pesquisa na web na etapa de pauta |

## 1. Calendário
`python scripts/canal.py calendario --pautas pautas.csv --inicio AAAA-MM-DD --por-dia 1 --horarios 12:00,19:30 --redes instagram,tiktok,youtube --saida calendario.csv`
- O calendário e o kit exigem status `aprovado` em `pautas.csv`, após revisão do vídeo final. A autorização explícita é exigida para agendar ou publicar.
- Ao ampliar um calendário, o script conserva as linhas existentes e usa horários livres a partir da data inicial. Informe pelo menos tantos horários distintos quanto vídeos por dia.
- Horários: começar pelos da ficha; depois de 2 rodadas de análise, usar a tabela de melhor horário do relatório.
- Evitar dois vídeos do mesmo formato seguidos quando houver alternativa (o script alterna sozinho).

## 2. Kit do dia (ou da semana)
`python scripts/canal.py kit --pautas pautas.csv --calendario calendario.csv --data AAAA-MM-DD --lotes lotes/ --saida kits/`
Gera `kits/AAAA-MM-DD/` com o vídeo final, a capa quando registrada, `postar.md` (por rede: horário, legenda pronta para colar, hashtags, lembrete do rótulo de IA, título do Shorts) e checklist. Com `--ate AAAA-MM-DD` cobre o intervalo informado. Em `pautas.csv`, use `capa` para a capa padrão e `capa_instagram`, `capa_tiktok` ou `capa_youtube` para substituições por rede. Os caminhos relativos são resolvidos em `--lotes`. Em uma pasta reutilizada, confira o `postar.md` da execução atual antes de usar as mídias.

## 3. Onde a equipe publica (gratuito)
- **Instagram (e Facebook):** Meta Business Suite → Criar Reel → Agendar. Permite agendar com semanas de antecedência, então dá para fazer a semana numa sentada.
- **TikTok:** TikTok Studio no navegador (computador) → Enviar → Agendar. A antecedência máxima é curta (cerca de 10 dias; conferir no momento).
- **YouTube Shorts:** YouTube Studio → Enviar → Visibilidade → Programar.
- Ligar o rótulo de conteúdo de IA em cada rede quando o vídeo for sintético realista.
Prazos e menus mudam; se algo não bater, pesquisar na web antes de orientar.

## 4. Opcional — a IA faz o passo manual
Com o app desktop do Claude ligado ao computador (navegador embutido ou Claude in Chrome já logado nas contas), a IA pode agendar nos agendadores nativos. Usar só sob pedido; um conector de agendamento (Metricool, Buffer) segue possível se a equipe decidir pagar.

## 5. Registro
`calendario.csv`: `id,rede,data,hora,status,link,observacao`. Status: `pendente` → `publicado`/`agendado` (com link) → `falhou` (com motivo). Atualizar `pautas.csv` (`publicado`, `data_post`).
