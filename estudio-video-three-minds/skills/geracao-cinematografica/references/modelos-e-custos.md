# Modelos, formatos e custos (referência de nov/2026 — conferir antes de projetos grandes)

## OpenAI — API de imagens
- Modelo: `gpt-image-2` (endpoint `/v1/images/generations`; edição com até 16 imagens de referência em `/v1/images/edits`)
- Tamanhos seguros: `1024x1536` (vertical), `1536x1024` (horizontal), `1024x1024`, `auto`. Para 1080×1920, gerar 1024×1536 e reenquadrar/expandir (Adobe `image_generative_expand` ou `image_crop_and_resize`).
- Qualidade: `low` | `medium` | `high` — rascunho em `medium`, final em `high`.
- Cobrança por tokens de imagem; conferir a calculadora de custo da OpenAI.
- Imagens sinalizadas como explícitas não são entregues (e podem ser cobradas).

## Runway — API (dev.runwayml.com)
Cabeçalho obrigatório `X-Runway-Version: 2024-11-06`; base `https://api.dev.runwayml.com/v1`.

Rotas: `POST /v1/text_to_image`, `POST /v1/image_to_video` (com `promptImage`), `POST /v1/text_to_video` (sem imagem; `gen4.5`), `GET /v1/tasks/{id}`. A tabela de créditos abaixo é referência local: fontes públicas divergem (há listagens de 12 e de 40 créditos/s para `gen4.5`), então confirmar em dev.runwayml.com antes de orçar.

| Modelo | Uso | Custo |
|---|---|---|
| `gen4.5` | texto→vídeo e imagem→vídeo, melhor qualidade | 12 créditos/s |
| `gen4_turbo` | imagem→vídeo rápido para testes | 5 créditos/s |
| `gen4_image` | imagem com referências (consistência de personagem) | 5 (720p) / 8 (1080p) créditos |
| `gen4_image_turbo` | imagem rápida | 2 créditos |

1 crédito ≈ US$ 0,01. Proporções de vídeo: `1280:720`, `720:1280`, `1104:832`, `832:1104`, `960:960`, `1584:672`, `672:1584`. Proporções de imagem comuns: `1920:1080`, `1080:1920`, `1024:1024`, `1360:768`, `1080:1440`.
A API da Runway também oferece modelos de outros laboratórios; conferir os ids em dev.runwayml.com/models e passar em `--modelo` (o script envia o id como está; se o modelo exigir parâmetros diferentes, a API devolve o erro explicando).

## Adobe Firefly (créditos da Creative Cloud)
Modelos parceiros no Firefly (exigem plano com recursos premium — Firefly ou Creative Cloud Pro; aceitar o aviso de modelos parceiros no primeiro uso):
- Imagem: GPT Image 2 / 2.5, Nano Banana Pro e Nano Banana 2, FLUX.2, Imagen 4, Runway Gen-4 Image, Ideogram, Firefly Image
- Vídeo: Veo 3.1 e Veo 3.1 Fast (com áudio), Kling 3.0 / 3.0 Omni, Runway Aleph (vídeo→vídeo), Luma, Pika, Firefly Video
- Custos variam e têm promoções temporárias (ex.: Veo 3.1 ~50 créditos/s em 1080p; Veo 3.1 Fast ~10 créditos/s). Ver a página "Partner models in Adobe products" da Adobe antes de orçar.
- Vantagem: tudo numa conta, e o Firefly Video Editor/Boards organizam as gerações.

## Estimativa rápida de um booktrailer de 45 s (15 planos de 3 s)
- 15 quadros-chave (GPT Image 2 high) + ~10 refações
- 15 animações de 5 s em gen4_turbo para teste (375 créditos ≈ US$ 3,75) + finais em gen4.5 (900 créditos ≈ US$ 9)
- Reservar 30–50% a mais para refações.
