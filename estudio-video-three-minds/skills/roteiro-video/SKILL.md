---
name: roteiro-video
description: "Cria roteiro, briefing e lista de planos para os vídeos da editora: booktrailer, Reels/TikTok/Shorts, YouTube longo e anúncios pagos com variações de gancho. Esta skill deve ser usada quando a equipe pedir \"escreve o roteiro do trailer\", \"faz um reels do lançamento\", \"ideias de vídeo para o livro X\", \"roteiro para o YouTube\", \"cria 5 ganchos para o anúncio\", \"transforma esse capítulo em vídeo\", \"lista de planos\" ou \"briefing de vídeo\". Para condução didática passo a passo, usar `cinema-work`; para série vertical em episódios, `novelinha-vertical`.\n"
metadata:
  version: "0.6.0"
---

# Roteiro e briefing de vídeo

1. Abrir a ficha do projeto (skill `padroes-da-casa`). Pedir só o indispensável: livro, selo, formato, plataforma, objetivo/CTA.
2. Basear tudo na sinopse oficial, no texto do livro ou em material fornecido. Não inventar fatos da obra nem traços de personagens; marcar como **pendência** o que faltar. Rotular exemplos fictícios.
3. Escolher a estrutura do formato em `references/estruturas.md`.
4. Entregar no formato abaixo — ele alimenta direto as skills de execução (`adobe-criativo`, `edicao-automatica`, `editor-falado` para roteiro lido em câmera ou narrado, `premiere-after-effects`, `capcut`).

## Formato de entrega

**Cabeçalho:** título · selo · formato · plataforma · duração-alvo · CTA

**Gancho (0–3 s):** 3 opções (texto em tela + imagem)

**Roteiro em tabela:**

| # | Tempo | Imagem / plano | Texto em tela | Narração / fala | Som |
|---|---|---|---|---|---|

**Lista de cortes (CSV)** quando a mídia já existir — mesmo cabeçalho de `adobe-criativo/scripts/lista_para_timeline.py`:
`trilha,midia,inicio,duracao,posicao,ganho,escala`

**Legenda do post:** 1ª linha com gancho, corpo curto, CTA, 3–8 hashtags (#booktok, #romance, gênero, título).

**Materiais necessários:** imagens, clipes, trilha (com origem/licença), fontes, logo.

## Regras de escrita

- Texto em tela: ≤ 8 palavras por cartela, 1 ideia por cartela.
- Narração: ~2,5 palavras por segundo em PT-BR; cronometrar.
- Romance adulto: sugerir tensão (olhares, mãos, respiração, cenário), nunca explicitar. Personagens claramente adultos.
- Anúncios: cada variação muda só o gancho; corpo e CTA iguais para comparar resultados.
