---
name: edicao-automatica
description: "Edita vídeos diretamente no ambiente do Claude com ffmpeg, como complemento ao conector Adobe: corta trechos a partir da lista de cortes, reenquadra para 9:16/4:5/16:9 com fundo desfocado, queima legendas no estilo da casa, gera .srt a partir do roteiro, cria cartelas de texto, normaliza áudio a −14 LUFS com ducking, concatena e exporta em vários formatos. Esta skill deve ser usada quando a equipe pedir \"queima a legenda\", \"gera o srt\", \"cria a cartela\", \"deixa vertical com fundo desfocado\", \"normaliza o áudio\", \"exporta em todos os formatos\", quando o conector Adobe não estiver disponível, ou quando a timeline da Adobe não cobrir texto e legendas.\n"
metadata:
  version: "0.6.0"
---

# Edição automática (ffmpeg)

Usar para o que a timeline da Adobe não faz (texto, legendas queimadas, cartelas) e como alternativa quando o conector não estiver disponível. Para gravação falada (pessoa falando em câmera ou narração) que precise de cortes de pausa, hesitação e tomada repetida, legenda palavra por palavra ou enquadramento no rosto, usar `editor-falado`. Arquivos anexados são originais: trabalhar em cópias e entregar o resultado como arquivo novo.

## Ferramenta

`scripts/video_tools.py` (requer ffmpeg/ffprobe). Subcomandos:

| Comando | Faz |
|---|---|
| `info VIDEO` | duração, resolução, fps, áudio, loudness |
| `conferir VIDEO [--plataforma reels\|tiktok\|shorts\|youtube\|feed\|anuncio]` | confere resolução, fps, codec, duração, −14 LUFS/−1 dBTP e nome do arquivo contra o padrão da casa; sai com código 2 se houver alerta |
| `quadros VIDEO [--n 4 \| --tempos 0.5,12,40] --saida PASTA` | extrai quadros com o tempo carimbado e uma `folha.png` para revisar com Read |
| `cortar CORTES.csv --midias PASTA --saida PASTA` | exporta cada linha da lista de cortes como clipe numerado |
| `reenquadrar VIDEO SAIDA --formato 9:16 [--modo blur\|crop]` | vertical/4:5/16:9; `blur` mantém tudo com fundo desfocado |
| `srt ROTEIRO.csv SAIDA.srt` | CSV `inicio,fim,texto` → SRT (quebra em 2 linhas de até 32 caracteres; avisa legenda curta demais ou sobreposta) |
| `legendar VIDEO SRT SAIDA [--fonte F --tamanho N --cor HEX --contorno HEX]` | queima legendas na zona segura |
| `cartela SAIDA --texto "..." [--fundo HEX --cor HEX --fonte F --duracao 2.5 --formato 9:16]` | cartela de texto em vídeo |
| `concatenar SAIDA A.mp4 B.mp4 ...` | junta clipes (normaliza resolução/fps) |
| `audio VIDEO SAIDA [--trilha T.mp3 --volume-trilha 0.3 --ducking]` | −14 LUFS, mixa trilha com ducking sob a voz |
| `exportar VIDEO --formatos 9:16,4:5,16:9 --saida PASTA --base NOME` | versões por formato com nome padrão |

Executar `python3 scripts/video_tools.py COMANDO -h` para ver todas as opções. Tempos aceitam segundos (`2.5`, `2,5`) ou timecode (`01:02.5`, `00:01:02,500`). Caminhos com espaços, aspas ou dois-pontos funcionam em todos os comandos.

## Fluxo típico (booktrailer vertical)

1. `info` em cada mídia → montar `cortes.csv` (skill `roteiro-video`).
2. `cortar` → `cartela` para título/CTA → `concatenar`.
3. `srt` a partir do roteiro → `legendar`.
4. `audio` com trilha e ducking → `exportar` nos formatos da peça.
5. Conferir antes de entregar: `quadros final.mp4 --n 4` e olhar `folha.png` com Read (legenda na zona segura, cartela legível, sem tela preta); `conferir final.mp4 --plataforma reels` e resolver todo alerta (ou explicar à equipe por que fica).

Encode padrão: H.264 `-preset veryfast -crf 19`, AAC 320 kbps, `+faststart`. Usar preset mais lento só se pedirem qualidade máxima.

Fontes: usar arquivos de fonte que a equipe fornecer (licença de uso em vídeo); sem fonte da identidade, usar uma livre (ex.: família DejaVu/Noto instalada) e avisar.
