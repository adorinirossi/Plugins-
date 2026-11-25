# Trava de originalidade

Plataformas avaliam o canal inteiro. O YouTube corta a monetização de conteúdo genérico, feito em modelo, que parece produção em massa; o TikTok tira do For You material reaproveitado sem nada novo; o Instagram tira de recomendação contas que publicam sobretudo conteúdo não original. O risco não é usar IA: é **mesmice**. Toda rodada passa por esta trava antes da aprovação do lote.

## 1. Ganho de informação (obrigatório por vídeo)
Cada pauta tem a coluna `ganho_informacao`: a frase que diz o que a pessoa sai sabendo que não sabia, com fonte. Pauta sem ganho claro é cortada ou reescrita. Fontes preferidas: livros do catálogo da editora (trecho, dado, argumento), pesquisa primária, obra de referência citada com autor e ano.

## 2. Rodízio dentro do kit
A identidade (voz, paleta, fonte, assinatura) é fixa; a forma varia. Colunas da pauta:
- `abertura_tipo` — rodar entre: pergunta · dado surpreendente · contradição · cena/história · objeto em close · citação · "erro comum" · resposta antes da pergunta. **Nunca o mesmo tipo em 2 vídeos seguidos nem mais de 30% do lote.**
- `visual_variacao` — ao menos 2 de: enquadramento de abertura, cenário, paleta secundária, tipo de movimento, recurso gráfico (mapa, linha do tempo, documento, diagrama).
- `estrutura` — rodar entre: lista · narrativa · comparação · pergunta-e-resposta · mito vs fato · processo passo a passo.
Ao montar a pauta, conferir a distribuição; ao montar o calendário, não encadear aberturas iguais.

## 3. Teste de semelhança (automático)
Antes de pedir aprovação do lote:
`python scripts/canal.py similaridade --novos lotes/<lote>/roteiros --anteriores lotes --limite 0.45`
Compara cada roteiro novo (arquivos .md/.txt) com os anteriores e entre si (trigramas de palavras, Jaccard). Acima do limite → reescrever abertura, estrutura ou ângulo e rodar de novo. O relatório lista os pares mais parecidos e a frase de abertura de cada um.

## 4. Checklist de originalidade (por vídeo, antes da aprovação 2)
- [ ] Ganho de informação explícito e com fonte
- [ ] Abertura diferente da do vídeo anterior no calendário
- [ ] Semelhança < limite
- [ ] Nada de trecho, imagem, bordão ou estrutura copiados de canais de referência
- [ ] Há um elemento editorial da casa (curadoria, comentário, conexão com um livro, contexto) que um gerador sozinho não teria
- [ ] Rótulo de IA ligado quando houver imagem/voz sintética realista (o rótulo não reduz alcance; não rotular pode)
- [ ] Nenhuma persona de IA se apresentando como especialista em saúde, direito ou finanças
