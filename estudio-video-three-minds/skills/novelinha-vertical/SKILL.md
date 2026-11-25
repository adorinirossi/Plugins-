---
name: novelinha-vertical
description: "Adapta livros da editora em novelinha vertical (microdrama) de episódios de 2–3 minutos para apps de microdrama, no estilo de temporadas de 50–100 episódios com gancho no fim de cada um: bíblia da série, escaleta, mapa de cliffhangers, roteiros de episódio, lista de planos e capas de episódio. Esta skill deve ser usada quando a equipe disser \"transforma o livro em novelinha\", \"microdrama\", \"série vertical\", \"escaleta da temporada\", \"roteiro do episódio 12\", \"onde corto os episódios?\", \"capa dos episódios\" ou \"piloto da novelinha\".\n"
metadata:
  version: "0.6.0"
---

# Novelinha vertical (microdrama)

Formato padrão da casa: 9:16, episódios de 2–3 min, temporadas de 50–100 episódios, gancho forte no fim de cada um. Os primeiros episódios costumam ser gratuitos e os seguintes, pagos — por isso os ganchos dos episódios de "paywall" são os mais fortes.

## Fluxo (uma etapa por vez, salvo autorização para seguir direto)

1. **Base da obra.** Ler o manuscrito ou sinopse fornecidos. Não inventar fatos, nomes ou traços; o que faltar vira pendência. Confirmar direitos audiovisuais com a autora/contrato antes de produzir.
2. **Bíblia da série** (`references/estrutura-temporada.md` § Bíblia): premissa, protagonistas e antagonista (só traços da obra; todos adultos inequívocos), mundo, tom, regras visuais.
3. **Escaleta da temporada:** dividir a história em arcos de 10–15 episódios; marcar os episódios-chave (piloto, ep. de paywall, viradas, final).
4. **Mapa de cliffhangers:** um gancho por episódio, sem repetir o mesmo tipo três vezes seguidas (tipos em `references/estrutura-temporada.md`).
5. **Roteiro de episódio:** formato abaixo. Escrever em lotes de 3–5 episódios, revisando continuidade.
6. **Produção:** lista de planos por episódio → execução via `cinema-work` (imagens/animação com IA), `adobe-criativo` (montagem/render), `capcut` (legendas e efeitos de app) ou gravação com atores.
7. **Capas de episódio:** 1080×1920 com título da série + nº do episódio, via fluxo Express em `adobe-criativo`.

## Formato do roteiro de episódio

```
EP. 07 — "<título>"  · duração-alvo 2:30
RECAP (0:00–0:08): <1 frase visual do gancho anterior>
CENA 1 — INT. <LOCAL> — NOITE
<ação em frases curtas, pensadas em plano vertical: rostos, mãos, objetos>
PERSONAGEM: <fala curta>
...
GANCHO (últimos 10–15 s): <revelação / ameaça / escolha / chegada>
TELA FINAL: "Continua…" + nº do próximo episódio
```

## Regras de linguagem vertical

- Uma cena de 20–45 s por vez; 3–5 cenas por episódio.
- Planos fechados (close, médio-close) dominam; plano geral só para situar.
- Conflito nos primeiros 10 s de todo episódio.
- Falas curtas; legendas sempre (episódios são vistos sem som).
- Romance adulto: tensão e beijo sim; nada explícito. Seguir o checklist de `padroes-da-casa`.
