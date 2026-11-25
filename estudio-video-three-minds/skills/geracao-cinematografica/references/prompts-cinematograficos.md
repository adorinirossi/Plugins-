# Prompts cinematográficos

Escrever os prompts em inglês (os modelos respondem melhor), mantendo nomes próprios. Guardar a versão aprovada no registro.

## Estrutura da imagem (quadro-chave)
```
[SUJEITO — ficha fixa] [ação/emoção específica],
[enquadramento], [lente e abertura], [ângulo],
[luz: fonte, direção, temperatura, contraste],
[cenário e época], [paleta],
[bloco de estilo fixo], [proporção/composição: espaço livre para texto no terço inferior se houver cartela]
```

**Exemplo fictício, só para ilustrar:**
> A woman in her early thirties, shoulder-length dark wavy hair, olive skin, small scar above left eyebrow, wearing a burgundy silk blouse — she grips the edge of a marble sink, jaw tight, eyes on the mirror. Medium close-up, 50mm lens at f/1.8, eye level. Single tungsten practical from the left, deep shadows, warm 3200K against cool blue spill from a window. Luxury apartment bathroom at night. Shot on 35mm film, Kodak Vision3 500T, fine grain, subtle halation, anamorphic bokeh, natural skin texture. Vertical frame, headroom for title.

## Vocabulário útil
- **Enquadramento:** extreme close-up, close-up, medium close-up, medium shot, cowboy shot, wide shot, extreme wide, over-the-shoulder, insert/detail
- **Lente:** 24mm (espaço, distorção), 35mm (natural, documental), 50mm (olho humano), 85mm (retrato, compressão), anamorphic (flares horizontais, bokeh oval)
- **Ângulo:** eye level, low angle (poder), high angle (vulnerável), dutch angle (tensão), top-down
- **Luz:** Rembrandt, split light, rim light, practical lights, golden hour, blue hour, neon spill, candlelight, overcast soft light, hard noon sun, chiaroscuro
- **Look de filme:** Kodak Vision3 500T/250D, Portra 400, Cinestill 800T, film grain, halation, teal-and-orange grade, bleach bypass, low saturation
- **Clima de gênero:** romance (golden hour, soft rim, shallow focus); máfia/dark (low key, sodium streetlight, wet asphalt, smoke); suspense (cold palette, hard shadows); acadêmico/Sophia (clean daylight, library, natural)

## Estrutura do vídeo (imagem → vídeo)
Descrever só o movimento — a imagem já define o visual:
```
[movimento de câmera] + [ação do sujeito] + [movimento do ambiente] + [ritmo]
```
Ex.: `Slow push-in. She exhales and lifts her eyes to the mirror. Curtain moves slightly in the breeze. Calm, tense.`
- Câmera: static, slow push-in, pull-out, pan left/right, tilt up, handheld subtle, orbit, crane up, dolly zoom
- Pedir movimentos pequenos e físicos; evitar várias ações num só plano de 5 s.
- Mãos, bocas falando e textos são os pontos mais frágeis — preferir ângulos que os evitem.

## Consistência de personagem
1. Gerar uma **imagem-âncora** por personagem (rosto de frente, luz neutra) e aprová-la.
2. Runway `gen4_image`: passar a âncora como referência com tag (`--ref ana=ancora_ana.png`) e citar `@ana` no prompt.
3. GPT Image 2: usar `editar` com a âncora como referência e a frase "keep the same person, same face and hair as the reference".
4. Repetir a ficha textual inteira em todos os prompts.
5. Após gerar, comparar com a âncora; se o rosto derivar, regerar a partir da âncora, não do último resultado.

## Negativos (o que evitar escrever)
Clichês vazios ("masterpiece, 8k, ultra hd, hyperrealistic"), nomes de atores ou artistas vivos, marcas registradas, conteúdo sexual explícito, aparência juvenil em romance.
