# Documento de timeline para `video_render`

Tempos são racionais `{ "n": numerador, "d": denominador }` = n/d segundos. Usar `d` = fps para alinhar ao quadro (2,5 s a 30 fps → `{ "n": 75, "d": 30 }`) ou `d` = 1000 para milissegundos. O script `lista_para_timeline.py` já alinha ao quadro. Duração máxima do render: 10 min.

```json
{
  "document": {
    "version": 1,
    "width": 1080,
    "height": 1920,
    "framerate": { "n": 30, "d": 1 },
    "tracks": [
      {
        "type": "video-audio",
        "clips": [
          {
            "mediaIndex": 0,
            "sourceStart":    { "n": 4000, "d": 1000 },
            "sourceDuration": { "n": 3000, "d": 1000 },
            "editStart":      { "n": 0,    "d": 1000 },
            "visualTransform": { "mode": "simple", "scale": "fill", "rotateDegrees": 0 },
            "audioTransform": { "gain": 0.0 }
          }
        ]
      },
      {
        "type": "audio",
        "clips": [
          {
            "mediaIndex": 3,
            "sourceStart":    { "n": 0,     "d": 1000 },
            "sourceDuration": { "n": 30000, "d": 1000 },
            "editStart":      { "n": 0,     "d": 1000 },
            "audioTransform": { "gain": 0.6 }
          }
        ]
      }
    ]
  },
  "assetIds": ["urn:aaid:sc:...clipe0", "urn:...clipe1", "urn:...cartela", "urn:...trilha"]
}
```

## Regras

- `mediaIndex` aponta para a posição em `assetIds`.
- Tipos de trilha: `video` (só imagem), `audio`, `video-audio` (clipe com som).
- `scale`: `fill` preenche o quadro cortando bordas (use para reenquadrar 16:9 → 9:16); `fit` mostra tudo com barras. O padrão da ferramenta é `fit`: sempre declarar `visualTransform` completo (`mode`, `scale`, `rotateDegrees`).
- `rotateDegrees`: só 0, 90, 180 ou 270 (útil para celular gravado deitado).
- `gain` de 0 a 2 (1 = original). Ducking simples: trilha 0,25–0,4 sob narração; 0,7–1 sem fala.
- Para cortar, use `sourceStart` + `sourceDuration`; para posicionar, `editStart`. Clipes de uma trilha não devem se sobrepor.
- Ordem das trilhas: trilhas posteriores ficam por cima. Cartelas (imagem/vídeo curto) numa trilha `video` acima da principal.
- Antes de renderizar, conferir que nenhum `sourceStart + sourceDuration` passa da duração do clipe (`video_metadata`).
- Prévia de quadro: `video_render_frame` com o mesmo `document`, `assetIds` e `timecode`.
