---
name: operacao-de-canal
description: "Opera um canal contínuo de vídeos (com ou sem rosto) para um selo da Three Minds ou para cliente, em ciclo fechado: ficha do canal, pauta em lote, produção em lote pelas outras skills do estúdio, calendário e agendamento da postagem, leitura das métricas e aprendizados que alimentam a próxima pauta. Esta skill deve ser usada quando a equipe disser \"cria o canal do selo X\", \"monta a ficha do canal\", \"gera a pauta da semana\", \"produz o lote\", \"agenda os vídeos\", \"monta o calendário\", \"posta no Metricool/Buffer\", \"como foram os vídeos?\", \"analisa as métricas\", \"o que funcionou?\", \"próxima rodada\" ou \"liga a esteira\". Para um vídeo avulso de lançamento, usar `roteiro-video`; para série em episódios de um livro, `novelinha-vertical`."
metadata:
  version: "0.6.0"
---

# Operação de canal — o ciclo da esteira

Um canal é uma operação recorrente, não um vídeo. Toda etapa lê a **ficha do canal** e toda rodada termina gravando **aprendizados** que mudam a próxima pauta.

```
Canal → Pauta → Roteiro → Voz → Visual → Montagem → Postagem → Análise ─┐
  ↑                                                                     │
  └──────────────────────── aprendizados.md ←───────────────────────────┘
```

## 0. Pasta do canal (memória da operação)

O ambiente de trabalho do Claude não guarda arquivos entre conversas. Na primeira vez, perguntar onde fica a pasta do canal e usar sempre o mesmo lugar:
1. pasta no computador da equipe (sessão ligada ao computador), ou
2. pasta no Google Drive (conector Google Drive).

Estrutura (criar o que faltar; nunca apagar histórico):

```
canal-<slug>/
  ficha-do-canal.md        ← fonte da verdade (references/ficha-do-canal.md)
  aprendizados.md          ← regras vivas, datadas, com evidência
  pautas.csv               ← uma linha por vídeo, com atributos para análise
  calendario.csv           ← data/hora/rede/status de cada post
  lotes/AAAA-MM-DD/        ← roteiros, áudios, mídias, finais, legendas
  metricas/AAAA-MM-DD.csv  ← exportações brutas, nunca editadas
  relatorios/AAAA-MM-DD.md ← análise de cada rodada
```

No início de qualquer pedido, ler `ficha-do-canal.md` e `aprendizados.md`. Se a pasta não existir, começar pela etapa 1.

## 1. Canal — ficha

Conduzir uma conversa curta e preencher `references/ficha-do-canal.md`: selo, público, promessa, nicho e subtemas, formatos fixos, voz, estilo visual, trilha (animação / avatar / imagens com movimento), cadência, redes, CTA e monetização, limites. Usar `padroes-da-casa` para identidade do selo e políticas.
- Pesquisar na web 5–10 canais de referência do tema e registrar **o que** funciona (estrutura, ritmo, tipo de gancho), nunca copiar roteiro, imagem ou bordão.
- Mostrar a ficha para aprovação antes de produzir. Ficha aprovada = versão 1, datada.

## 2. Pauta em lote

Seguir `references/pauta-em-lote.md`. Gerar o lote (padrão: 2 semanas de cadência) direto em `pautas.csv`, com os atributos que a análise vai cruzar (formato, tipo de gancho, abertura, estrutura, tema, duração-alvo, trilha) e o **ganho de informação** de cada vídeo, seguindo o rodízio de `references/originalidade.md`. Regra 70/20/10: 70% do que os aprendizados mostram que funciona, 20% variações, 10% testes novos com hipótese escrita.

**Ponto de aprovação 1:** a equipe aprova, corta ou troca pautas antes de roteirizar.

## 3–6. Produção em lote (usar as skills do estúdio)

| Etapa | Skill | Observação de canal |
|---|---|---|
| Roteiro | `roteiro-video` | regras de retenção (`references/retencao.md`) + regras vigentes de `aprendizados.md`; marcar gancho, reinícios e payoff com tempo |
| Voz | voz da ficha (ElevenLabs ou motor local) | `references/voz-e-pronuncia.md`: glossário aplicado antes de gerar, ~10% mais lenta, escuta obrigatória |
| Visual | `geracao-cinematografica` / `adobe-criativo` (Stock, Firefly) | kit fixo da ficha + variação de abertura/visual da pauta; troca visual a cada 3–5 s |
| Montagem | `adobe-criativo` (padrão) ou `edicao-automatica`; vídeo falado gravado (rosto em câmera) → `editor-falado` | legenda da casa, −14 LUFS, 9:16; **3 versões por rede** (`references/versao-por-rede.md`) |

Produzir em lote, mas revisar cada vídeo. Antes de pedir a aprovação do lote:
1. Rodar `scripts/canal.py similaridade --novos lotes/<lote>/roteiros --anteriores lotes` e reescrever o que passar do limite.
2. Preencher o checklist de originalidade (`references/originalidade.md`) e a escuta de voz.
3. Conferir fatos e fontes; registrar arquivos por rede e legendas por rede na linha da pauta.

**Ponto de aprovação 2:** a equipe assiste ao lote e aprova vídeo a vídeo (status `aprovado` em `pautas.csv`). Vídeo não aprovado não entra no calendário.

## 7. Postagem e agendamento

Seguir `references/postagem-e-agendamento.md`. O plugin cobre as funções de um agendador pago com ferramentas gratuitas:
1. `scripts/canal.py calendario` monta a fila (alternando formatos, nos horários da ficha ou da análise).
2. `scripts/canal.py kit` gera o kit do dia (ou da semana): vídeo, capa e `postar.md` com legenda pronta por rede, horário, título do Shorts e lembrete do rótulo de IA.
3. A equipe publica ou agenda nos agendadores nativos gratuitos (Meta Business Suite, TikTok Studio, YouTube Studio) — uma ação por dia, ou a semana de uma vez — e marca `publicado` + link.
Opcional: com o computador ligado, a IA agenda pelo navegador, sob pedido. Conector pago (Metricool/Buffer) só se a equipe decidir.

**Nunca publicar ou agendar sem a aprovação da etapa 6 e um "pode agendar" explícito para o lote.**

## 8. Análise → aprendizados

Seguir `references/analise-e-aprendizado.md`. Ao menos 72 h depois do último post da rodada:
1. Puxar métricas pela exportação gratuita das plataformas (CSV) ou por prints, e salvar em `metricas/`. Para os 3 melhores e 3 piores, registrar retenção aos 3 s, retenção final e segundo da maior queda (`references/retencao.md`).
2. Rodar `scripts/canal.py analisar --pautas pautas.csv --calendario calendario.csv --metricas metricas/*.csv --saida relatorios/<data>.md --json relatorios/<data>.json` e, se a equipe acompanha pelo celular, `scripts/canal.py painel` (publicar como artifact).
3. Ler o relatório (inclui retenção por formato e por abertura) e propor no máximo 3 aprendizados novos ou revisados, cada um com evidência (n de vídeos, diferença medida) e nível de confiança. Amostra pequena = hipótese, não regra.
4. Gravar em `aprendizados.md` após a equipe concordar, e já usar na próxima pauta.

Entregar à equipe: 3 linhas de resumo (o que subiu, o que caiu, o que muda), o relatório e a proposta da próxima rodada.

## Modo usina — o ciclo rodando sozinho

Quando a equipe pedir para "ligar a usina" ou automatizar o canal, seguir `references/automacao-usina.md`: criar tarefas agendadas (pauta quinzenal, produção quando houver pauta aprovada, kit do dia de manhã, cobrança à noite, análise semanal), com a pasta do canal no Google Drive. As tarefas param nos dois pontos de aprovação (pauta e lote) e nunca publicam. Explicar à equipe que a "usina" é lote + fila + leitura periódica, não uma IA ligada 24 horas.

## Regras da operação

- Views não são resultado: reportar sempre junto com seguidores ganhos, salvamentos, compartilhamentos e cliques/vendas quando houver.
- Não prometer renda nem alcance.
- Mesmice é o maior risco do canal: plataformas avaliam o canal inteiro e cortam alcance ou monetização de conteúdo em série. A trava de originalidade é obrigatória em toda rodada.
- Para canais novos, priorizar autoridade, seguidores qualificados e venda de livros e serviços. Conferir os requisitos vigentes na documentação oficial do Programa de Parcerias e a elegibilidade no YouTube Studio antes de definir uma meta de receita publicitária.
- Conteúdo sintético realista recebe o rótulo de IA da plataforma.
- Fatos, citações e dados de livros conferidos na fonte; citação de autor sempre com referência.
- Canal de selo acadêmico (Sophia): rigor acima de viralização; nada de títulos sensacionalistas que o conteúdo não sustente.
