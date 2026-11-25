---
name: padroes-da-casa
description: "Padrões de vídeo da Three Minds Publishing (selos RedVelvet, Sophia, Three Minds Editions, FannyBooks e PrismaBooks): especificações técnicas por plataforma, identidade visual dos selos, checagem de direitos de música/imagem e de políticas de anúncio para conteúdo adulto. Esta skill deve ser usada sempre que outra skill do estúdio de vídeo for iniciar um projeto, e quando a equipe perguntar \"qual o tamanho do Reels?\", \"que formato exporto para o YouTube?\", \"posso usar essa música?\", \"esse trailer passa no Meta Ads?\", \"quais as cores do RedVelvet?\", \"configure a identidade do selo\" ou \"confira se o vídeo está dentro do padrão\".\n"
metadata:
  version: "0.6.0"
---

# Padrões da casa — vídeo

Aplicar estes padrões a todo vídeo produzido pelo estúdio. As demais skills do plugin consultam esta antes de começar.

## 1. Abrir todo projeto com uma ficha

Antes de roteirizar ou editar, preencher (perguntando só o que faltar):

| Campo | Exemplo |
|---|---|
| Selo | RedVelvet / Sophia / Three Minds Editions / FannyBooks / PrismaBooks / serviço avulso |
| Livro e autora | título, autora, data de lançamento |
| Formato | booktrailer, Reels/TikTok/Shorts, YouTube longo, anúncio, novelinha vertical |
| Plataformas de destino | definem proporção, duração e exportação |
| Objetivo e CTA | pré-venda, lançamento, link na bio, Amazon/KDP |
| Ferramenta de montagem | Adobe na nuvem (padrão, skill `adobe-criativo`), edição automática (ffmpeg), editor falado (gravação com pessoa falando), Premiere/After Effects, CapCut |
| Canal (se for série contínua) | ler a ficha do canal (skill `operacao-de-canal`) |
| Classificação do conteúdo | livre / sensual / explícito no livro (o vídeo nunca é explícito) |

## 2. Especificações técnicas

Consultar `references/especificacoes-plataformas.md` para proporção, resolução, duração, áreas seguras e loudness por plataforma. Limites de duração e regras das plataformas mudam com frequência: antes de exportar a versão final, conferir na web o limite atual da plataforma quando o vídeo estiver perto do limite.

## 3. Identidade dos selos

Ler `references/identidade-selos.md`. Os campos de cores, fontes e logos começam em branco.
- Se o selo do projeto ainda tiver campos vazios, perguntar à equipe uma vez (cores em hex, fontes, logo, tom) e oferecer registrar a resposta no arquivo de identidade para os próximos projetos. Se ninguém responder, usar uma escolha neutra e coerente com o gênero do livro e avisar que é provisória.
- Usar a capa do livro como fonte principal de paleta quando a identidade do selo não bastar.

## 4. Direitos e políticas

Ler `references/direitos-e-politicas.md` e rodar a checagem antes de entregar qualquer peça:
- Música, efeitos sonoros, fontes, imagens e vídeos de banco: licença compatível com uso comercial e com a plataforma.
- Conteúdo gerado com IA: sinalizar quando a plataforma exigir rótulo.
- Romance adulto (RedVelvet): o vídeo sugere, nunca mostra. Nada de nudez, ato sexual ou texto explícito em tela; em anúncios pagos, seguir a versão mais restritiva.
- Todos os personagens retratados são inequivocamente adultos — idade, aparência e contexto. Não usar elementos escolares, infantis ou de aparência juvenil em peças de romance.

## 5. Entrega

Entregar sempre: arquivo final (ou pacote de montagem), legenda/descrição do post com hashtags, lista de créditos e licenças usadas, e checklist de conformidade preenchido.

Conferência técnica automática do arquivo final: `python3 ../edicao-automatica/scripts/video_tools.py conferir ARQUIVO.mp4 --plataforma reels|tiktok|shorts|youtube|feed|anuncio` (resolução, fps, codec, duração, loudness, true peak e nome padrão). Corrigir os alertas ou registrar por que ficam.
