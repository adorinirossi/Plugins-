# Pauta em lote

## Entrada
- `ficha-do-canal.md` (pilares, formatos, ganchos, cadência)
- `aprendizados.md` (regras vigentes e hipóteses em teste)
- `pautas.csv` (para não repetir tema, título ou gancho)
- Opcional: pesquisa na web de assuntos em alta no nicho; datas do calendário editorial (lançamentos do selo, datas comemorativas)

## Tamanho
Padrão: cadência × 14 dias (ex.: 1 por dia em 3 redes com o mesmo vídeo = 14 vídeos). Ajustar ao que a equipe consegue revisar.

## Distribuição 70/20/10
- **70% — explorar:** formatos, ganchos e temas que os aprendizados mostram acima da média.
- **20% — variar:** o que funciona, com uma única variável mudada (gancho, duração ou visual).
- **10% — testar:** ideia nova com hipótese escrita na coluna `hipotese` ("gancho de contradição retém mais que pergunta").
Antes da primeira análise (canal novo): distribuir igualmente entre pilares e formatos para gerar dados comparáveis.

## pautas.csv — colunas
```
id,lote,pilar,formato,gancho_tipo,abertura_tipo,estrutura,visual_variacao,titulo,gancho_texto,ganho_informacao,fonte,duracao_alvo,trilha,hipotese,status,arquivo_final,data_post,legenda
```
- `legenda`: preenchida na produção (gancho na 1ª linha, CTA, 3–8 hashtags); colunas opcionais `legenda_instagram`, `legenda_tiktok`, `legenda_youtube` quando a legenda mudar por rede. O kit do dia usa essas colunas.
- `arquivo_final`: caminho do vídeo-base, relativo a `lotes/`. Versões por rede em `arquivo_<rede>`, `texto_inicial_<rede>`, `titulo_youtube` (ver `versao-por-rede.md`).
- `abertura_tipo`, `estrutura`, `visual_variacao`, `ganho_informacao`: ver `originalidade.md`. Conferir o rodízio antes de entregar a pauta (nenhum tipo de abertura em mais de 30% do lote).
- `id`: `<slug>-<lote>-<nn>` (ex.: `sophia-20261130-03`); é a chave que liga pauta, calendário e métricas
- `status`: `proposta` → `aprovada` → `produzida` → `aprovado` → `agendado` → `publicado` (ou `cortada`)
- `fonte`: livro/página, artigo, dado — obrigatório quando houver fato ou citação
- `link` (opcional; ou `link_instagram`, `link_tiktok`, `link_youtube`): destino no site da editora; o kit acrescenta UTM

## Entrega para aprovação
Tabela curta (id, pilar, formato, gancho, título) agrupada por 70/20/10, com 1 linha explicando o que mudou em relação ao lote anterior e por quê (qual aprendizado foi aplicado).
