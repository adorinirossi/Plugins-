# Análise e aprendizado

## 1. Coletar (gratuito)
Salvar em `metricas/AAAA-MM-DD-<rede>.csv`, sem editar o bruto:
- **Instagram/Facebook:** Meta Business Suite → Insights → Conteúdo → Exportar dados (CSV).
- **TikTok:** TikTok Studio → Análises → Conteúdo → exportar; se não houver exportação, prints da lista de vídeos.
- **YouTube:** YouTube Studio → Análises → Avançado → Conteúdo → Exportar (CSV).
- **Prints:** ler as imagens e preencher `metricas/AAAA-MM-DD-manual.csv` com o cabeçalho `id,rede,data,hora,views,alcance,curtidas,comentarios,compartilhamentos,salvamentos,seguidores,retencao,retencao_3s,queda_seg,queda_motivo,tempo_medio`. Um arquivo só de retenção (`id,rede,retencao_3s,retencao,queda_seg`) também serve: o script soma aos números das exportações.
O script reconhece colunas em português e inglês das três plataformas e liga cada linha à pauta por `id`; sem `id`, pela rede + data (calendário) e, em último caso, pelo título/legenda.

## 2. Rodar
`python scripts/canal.py analisar --pautas pautas.csv --calendario calendario.csv --metricas metricas/*.csv --saida relatorios/AAAA-MM-DD.md --json relatorios/AAAA-MM-DD.json`

O relatório traz:
- **Índice por vídeo** (0–100, relativo ao próprio canal): 30% views, 25% compartilhamentos/views, 20% salvamentos/views, 15% seguidores ganhos/views, 10% retenção quando houver. Taxas evitam premiar só o alcance. As views são comparadas dentro da mesma rede (quando ela tem 3+ posts), para o TikTok não engolir Instagram e Shorts; empates recebem a mesma nota.
- **Por atributo** (formato, gancho_tipo, abertura_tipo, estrutura, pilar, duração, trilha, rede)
- **Retenção** por formato, abertura e gancho: % que passou de 3 s, % até o fim, segundo médio da maior queda: média do índice, n e diferença contra a média do canal.
- **Melhor horário** por rede × dia da semana × faixa (manhã/almoço/tarde/noite).
- **Top 3 e bottom 3** com os atributos de cada um.
- **Hipóteses do lote**: resultado de cada vídeo de teste (10%) contra a média.

## 3. Ler com rigor
- n < 3 vídeos num grupo → hipótese, nunca regra.
- Diferença < 15% do índice → empate.
- Separar efeito da rede (TikTok costuma ter mais views) antes de concluir sobre formato.
- Um viral isolado não muda a estratégia sozinho; repetir o padrão no próximo lote para confirmar.
- Views sem seguidores/salvamentos = conteúdo que entretém mas não constrói canal.

## 4. aprendizados.md — formato
```
## Regras vigentes
- [AAAA-MM-DD] Gancho de contradição > pergunta (+32% índice, n=6 vs 5). Confiança: média. Aplicar em 70%.
## Em teste
- [AAAA-MM-DD] Vídeos de 25–35 s retêm mais que 50 s? Teste: 3 vídeos no próximo lote.
## Descartadas
- [AAAA-MM-DD] Horário das 7h — sem diferença após 2 rodadas.
```
No máximo 3 mudanças por rodada, sempre com evidência. A equipe aprova antes de gravar.

## 5. Painel
`python scripts/canal.py painel --json relatorios/AAAA-MM-DD.json --calendario calendario.csv --saida painel.html` gera um painel HTML de uma página (índice dos vídeos, atributos, melhor horário, fila dos próximos dias). Publicar como artifact quando a equipe quiser acompanhar pelo celular.
