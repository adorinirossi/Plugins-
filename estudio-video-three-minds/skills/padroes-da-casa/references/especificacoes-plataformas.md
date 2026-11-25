# Especificações por plataforma

Valores de referência (out/2026). Limites de duração mudam: confirmar na web quando a peça estiver perto do limite.

## Vertical 9:16 — Reels, TikTok, Shorts, microdrama

- Resolução: 1080×1920 (H.264, 30 fps; 24/25 fps aceitos para visual "cinema")
- Áreas seguras: manter texto e rostos fora dos ~250 px do topo e dos ~400 px da base (interface do app) e ~120 px nas laterais. Zona segura prática: retângulo central 840×1270 a partir de y=250.
- Gancho visual e textual nos primeiros 1–2 s.
- Legendas sempre queimadas ou nativas — a maioria assiste sem som.
- Durações usuais: Reels/TikTok/Shorts 15–90 s para alcance; até ~3 min nos três para conteúdo mais longo. Microdrama: 2–3 min por episódio (ver skill novelinha-vertical).

## Horizontal 16:9 — YouTube longo

- 1920×1080 ou 3840×2160, H.264/H.265, taxa de quadros igual à da captação
- Thumbnail: 1280×720, JPG/PNG, texto grande (até 4 palavras), rosto ou capa do livro
- Capítulos: descrição com marcações 00:00
- Legendas: enviar .srt separado (melhor que queimar)

## Quadrado e 4:5 — feed e anúncios

- 1080×1080 (1:1) e 1080×1350 (4:5)
- Anúncios Meta: produzir 9:16 + 4:5 + 1:1 da mesma peça; texto em tela curto

## Anúncios pagos — regras práticas

- Produzir 3 a 5 variações de gancho (primeiros 3 s) por peça
- Duração: 6 s (bumper), 15 s, 30 s
- Logo/selo visível até 3 s e no fim; CTA explícito nos últimos 3 s

## Áudio

- Redes sociais e YouTube: −14 LUFS integrado, true peak ≤ −1 dBTP
- Voz sempre acima da trilha: trilha cerca de 12–18 dB abaixo da voz durante a fala (ducking)

## Exportação padrão

| Destino | Container | Vídeo | Áudio |
|---|---|---|---|
| Redes 9:16 | MP4 | H.264 High, CRF 18–20 ou ~12–16 Mbps | AAC 48 kHz 320 kbps |
| YouTube 1080p | MP4 | H.264, ~16–20 Mbps | AAC 48 kHz 320 kbps |
| Master para arquivo | MOV | ProRes 422 HQ | PCM 48 kHz |

Nome de arquivo: `SELO_TITULO-LIVRO_FORMATO_PLATAFORMA_vNN.mp4` (ex.: `RV_FEITICO-DOURADO_TRAILER_REELS_v03.mp4`).
