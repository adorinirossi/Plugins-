---
name: editor-falado
description: "Edita vídeo falado gravado (Reels, TikTok, Shorts, anúncio, aula, vlog) por conversa, sem CapCut: tira pausas, hesitações e tomadas repetidas (fica a melhor tomada ou a última), legenda palavra por palavra, gancho na tela, cartões animados, enquadramento seguindo o rosto, zoom, .srt e versões por gancho e formato. Esta skill deve ser usada quando a equipe enviar uma gravação e disser \"edita esse vídeo\", \"tira as pausas\", \"corta os erros\", \"fica com a melhor tomada\", \"legenda palavra por palavra\", \"põe o gancho\", \"deixa vertical no rosto\" ou \"faz as versões do anúncio\"."
metadata:
  version: "0.6.0"
---

# Editor de vídeo falado — Three Minds

Você grava, a IA edita. Recebe a gravação bruta e um pedido em português e devolve o vídeo cortado, legendado e no formato da plataforma. Testado ponta a ponta em nov/2026: 33 s de bruto viram 17 s em cerca de 12 s de análise e 15 s de render por versão.

## 1. Preparar o motor (uma vez por sessão)

1. Copiar os scripts desta skill para a pasta de trabalho: `mkdir -p ~/editor-falado && cp "<pasta desta skill>"/scripts/*.py ~/editor-falado/` (a pasta da skill aparece como "Base directory" ao carregá-la; no plugin, `${CLAUDE_PLUGIN_ROOT}/skills/editor-falado/scripts/`). Sobrescrever a cópia antiga se houver: o arquivo do plugin é sempre a versão vigente.
2. `pip install --break-system-packages -q faster-whisper numpy "opencv-python-headless<5"` e conferir `ffmpeg -version`. O OpenCV é o detector de rosto do enquadramento; sem ele, o vertical sai pelo centro (o motor avisa). **Manter o `<5`:** o OpenCV 5 deixou de trazer o arquivo do detector de rosto, e o motor teria de baixá-lo do GitHub (se a rede bloquear, o enquadramento cai para o centro).
3. Na primeira análise o modelo de transcrição é baixado uma vez: `large-v3-turbo` (~1,6 GB), o padrão para gravações de até 10 min, porque erra bem menos nomes e palavras que o `small`. Acima de 10 min o motor usa o `small` (~460 MB). Se o download for bloqueado, dizer à usuária que o acesso à internet do Claude precisa estar liberado nas configurações (Recursos/Capabilities, permitir acesso à rede) e seguir pela rota da skill `capcut` enquanto isso. Se o `large-v3-turbo` falhar (memória ou download), o motor cai sozinho para o `small` e avisa: nesse caso, revisar a fala com mais cuidado no passo 4.

Trabalhar sempre numa cópia da gravação; nunca alterar o arquivo enviado.

## 2. Fluxo

1. **Ficha rápida** (perguntar só o que faltar, sem travar): selo, livro, formato/plataforma, objetivo do vídeo, se quer gancho na tela. Seguir `padroes-da-casa` para plataforma, direitos e conteúdo adulto.
2. **Áudio ruim?** Chiado ou volume irregular: `--limpar-voz` no render. Eco ou ruído forte: limpar antes com o conector Adobe (`media_enhance_speech`, skill `adobe-criativo`) e usar o arquivo limpo.
3. **Analisar** com contexto — nomes próprios melhoram muito a transcrição:
   `python3 ~/editor-falado/editor_falado.py analisar BRUTO.mp4 --saida edicao --contexto "Título, autora, selo RedVelvet, nomes dos personagens, termos"`
   O modelo é escolhido sozinho (`--modelo auto`: `large-v3-turbo` até 10 min, `small` acima). Para aula de 1–2 h, `--modelo base`.
   **Tomadas repetidas:** quando a mesma frase foi recomeçada, fica a **melhor tomada** (a mais completa e limpa; empate → a mais recente). Se a usuária pedir "fica com a última tomada", analisar com `--tomada ultima`. Se uma tentativa descartada trouxer informação que a outra não tem, ela aparece como "tomada c/ info nova" e **fica** no vídeo; avisar e perguntar.
   Quando houver roteiro exato (narração gerada ou texto lido em câmera), passar `--roteiro roteiro.txt`: a legenda usa a grafia do roteiro (RedVelvet, nomes de personagens) e o que for falado fora dele aparece como "fora do roteiro" (cortado só no começo e no fim; no meio fica, e pode ser cortado com `ajustar --recortar N`).
4. **Revisar a fala que fica** e corrigir a legenda (homófonos e nomes: sem/cem, celo/selo, céu/CEO, bio/Bill). Só corrige texto, nunca os cortes, e nunca muda o sentido do que foi dito:
   `python3 ~/editor-falado/editor_falado.py corrigir edicao/plano.json "sem leitoras=cem leitoras" "sela=CEO"`
5. **Mostrar à usuária**, curto: bruto → editado, a lista numerada de cortes (tipo, tempo, o que sai) e qualquer aviso de anúncio. Nenhuma palavra some sem aparecer nessa lista.
   **Revisar como editora de retenção** antes de renderizar:
   - O vídeo abre na primeira palavra com conteúdo, nunca em "oi", "então", "bom", "gente".
   - Se a frase mais forte (promessa, número, contraste, pergunta direta) estiver no meio, levá-la para a abertura com `ajustar edicao/plano.json --abrir N` (N = número da frase na lista "FRASES"). Fazer direto quando o pedido for "abre com a frase mais forte"; nos outros casos, sugerir. Conferir se a frase seguinte faz sentido sem a que subiu ("como eu disse…" quebra) e avisar.
   - O "é" verbo ("é isso", "é simples") nunca sai; o motor só corta o "éééé" arrastado e isolado entre pausas ("hesitação (é)"). Conferir esses itens.
   - Pausa curta antes de uma revelação é dramática: devolver com `ajustar --manter N` em vez de cortar.
6. **Renderizar** a primeira versão já com o kit do selo (item 4), sem esperar aprovação, salvo se o bruto passar de 3 min:
   `python3 ~/editor-falado/editor_falado.py renderizar edicao/plano.json final_9x16.mp4 --formato 9:16 --gancho "TEXTO" --destaque "#HEX" --caixa-alta`
   **Enquadramento:** `--modo auto` (padrão) segue o rosto quando o formato de saída é parecido com o da gravação e usa fundo desfocado quando não é. Gravação **horizontal** de uma pessoa para vertical: usar `--modo rosto`, que corta acompanhando o rosto (olhos perto do terço superior) em vez de cortar pelo centro. Duas pessoas, ou rosto não encontrado: `--modo blur` mantém o quadro inteiro.
   O motor cuida sozinho de: vídeo de celular gravado em pé (metadado de rotação), vídeo HDR de iPhone (sai SDR BT.709, sem cor lavada) e loudness (mede o final e, se sair de −14 ±1 LUFS, refaz só o áudio). Avisa quando a fonte pedida não está instalada e quando o gancho tem termo de risco para anúncio.
   Todo render grava também `final_9x16.srt` (legenda da versão editada, frases de até 2 linhas de 32 caracteres), para quem for continuar no CapCut ou no Premiere. Entregar o .srt quando pedirem material editável.
   Para dar ritmo, criar 2 a 4 **cartões animados** antes do render: cada um entra com efeito pop quando a palavra-gatilho é dita. Escolher números, datas e promessas (preço, brinde, dia da pré-venda, nome do livro):
   `python3 ~/editor-falado/editor_falado.py cartao edicao/plano.json "pré-venda=SEGUNDA|pré-venda aberta" "brinde=100|brindes exclusivos"`
   O gatilho pode ter várias palavras (`"dia doze=12/12"`) e tem que aparecer na fala que fica; se não aparecer, o comando avisa e não cria o cartão. Refazer um cartão com o mesmo gatilho substitui o anterior; `cartao edicao/plano.json --limpar` apaga todos. Não usar cartão nos primeiros 3 s quando houver gancho (o motor pula esses).
7. **Conferir antes de entregar** com as ferramentas da skill `edicao-automatica` (`<plugin>/skills/edicao-automatica/scripts/video_tools.py`):
   - `video_tools.py quadros final_9x16.mp4 --n 4 --saida revisao` e olhar `revisao/folha.png` com Read: gancho inteiro dentro da tela, legenda sem sobreposição, rosto enquadrado, cartões legíveis. (Os quadros saem distribuídos pela duração real; não usar números de quadro fixos, que passam do fim em vídeo curto.)
   - `video_tools.py conferir final_9x16.mp4 --plataforma reels` (resolução, fps, loudness, true peak). O alerta de nome fora do padrão só vale para a entrega final: renomear para `SELO_TITULO-LIVRO_FORMATO_PLATAFORMA_vNN.mp4`.
8. **Entregar** com SendUserFile e uma linha de contexto; oferecer ajustes.

## 3. Ajustes por conversa

| Pedido | Comando |
|---|---|
| "volta o corte 5" / "deixa aquela pausa" / "volta aquela tomada" | `ajustar edicao/plano.json --manter 5` (vale também para tomada e hesitação) |
| "fica com a última tomada" / "com a melhor" | `analisar BRUTO.mp4 --saida edicao --tomada ultima` (ou `melhor`) e refazer correções e cartões |
| "abre com a frase mais forte" / "começa pela frase 4" | `ajustar edicao/plano.json --abrir 4` (`--abrir 0` desfaz) |
| "corta de novo o 5" | `ajustar edicao/plano.json --recortar 5` |
| "tira de 12 a 13,5 s" (tempo do bruto) | `ajustar edicao/plano.json --cortar 12-13.5` (várias faixas: `12-13.5,20-21`) |
| "a legenda errou o nome" | `corrigir edicao/plano.json "errado=certo"` |
| legenda maior/menor quantidade de palavras | `--palavras 2` (máx. 3) |
| sem zoom / zoom mais forte | `--zoom 0` / `--zoom 0.12` |
| vertical com fundo desfocado em vez de corte | `--modo blur` |
| "a pessoa ficou cortada" / gravação horizontal | `--modo rosto` |
| "manda a legenda em arquivo" | o `.srt` sai junto com cada render (mesmo nome do vídeo) |
| voz com chiado, ruído grave ou volume irregular | `--limpar-voz` |
| "põe um cartão quando eu falar X" | `cartao edicao/plano.json "X=TÍTULO|subtítulo"` |
| cartão mais longo / mais curto | `--dur-cartao 2.2` |
| "tira os cartões" | `cartao edicao/plano.json --limpar` |
| fonte do selo (arquivo enviado pela equipe) | `--pasta-fontes PASTA --fonte "Nome da família"` |

Depois de cada ajuste, renderizar de novo e reentregar. O plano fica salvo em `edicao/plano.json`, então nada precisa ser reprocessado.

## 4. Kit dos selos

Valores **provisórios** até a equipe preencher `references/identidade-selos.md` da skill `padroes-da-casa`. Ao usar, avisar uma vez que são provisórios e perguntar as cores e fontes oficiais; quando a usuária responder, usar as dela.

| Selo | `--destaque` | `--fundo-gancho` | Estilo |
|---|---|---|---|
| RedVelvet | `#E0245E` | `#120A0F` | `--caixa-alta`, gancho provocativo, nunca explícito |
| Sophia | `#2F6FED` | `#0B1F3A` | caixa alta e baixa, `--zoom 0.04`, tom sóbrio |
| Three Minds Editions | `#F2A900` | `#1A1A1A` | caixa alta e baixa |
| FannyBooks / PrismaBooks | `#FFD400` | `#000000` | até ter identidade própria |

Fonte padrão: Inter (o motor avisa se ela não estiver instalada no computador). Fontes da Adobe Fonts não viram arquivo para o render; para usar a fonte oficial, pedir o .ttf/.otf com licença para vídeo.

Regras dos padrões que valem aqui: logo do selo no fim do vídeo e capa legível por 2 s ou mais (montar a cartela com a skill `edicao-automatica` e juntar com `concatenar`); no máximo 2 famílias tipográficas.

## 5. Versões (anúncio e teste A/B)

Pedir 3 a 5 ganchos à skill `roteiro-video` (ou escrever, a partir da fala) e gerar tudo de uma vez:
`python3 ~/editor-falado/editor_falado.py versoes edicao/plano.json --ganchos "Gancho 1" "Gancho 2" "Gancho 3" --formatos 9:16,4:5,16:9 --pasta versoes --base NOME_DO_LIVRO --destaque "#HEX"`
O 16:9 a partir de gravação vertical sai automaticamente com fundo desfocado.

## Narração e vídeo sem gravação

Sem gravação, ou para usar a voz de alguém cadastrado (com autorização), seguir a skill `configuracao-de-voz` (skill da conta; se não estiver instalada, avisar e usar a narração entregue pela equipe): `voz.py narrar` → `voz.py video-narrado` → aqui, `analisar --roteiro roteiro.txt --pausa 0.9` → cartões → `renderizar`. Nomes em inglês são falados em inglês ("Red Vélvet") e a legenda mantém a grafia original.

## 5b. Modo viral — montagem de reacts (estilo Buzzy, feito aqui)

Quando a usuária mandar vários takes curtos (reações, leituras, bastidores) e pedir algo "chamativo", "viral" ou "que prenda no Instagram", não editar take por take: montar uma peça só, com ritmo de Reels. Testado em nov/2026 com 24 takes da Andrea ("Os 24 estágios de ler um RedVelvet").

**Agente de garimpo (o "Proactive Agent" do Buzzy):** transcrever TODOS os takes com tempos por palavra (faster-whisper small, `word_timestamps=True`; para fala baixa ou murmurada, rodar de novo sem VAD, com `-af loudnorm` e `initial_prompt="Leitura de romance em voz alta."`) e listar as frases fortes de cada um: leituras do livro, exclamações, perguntas à câmera, risadas. Olhar 4–6 quadros de cada take antes de escolher (rosto, expressão, capa à vista; descartar ilustração explícita, bocejo aparente, mão cobrindo a boca no começo).

**Formatos que funcionam (oferecer 1 ou 2, não perguntar demais):**
- **Contagem** — "OS N ESTÁGIOS DE…": um take por estágio, número grande no topo ("17/24"), rótulo-meme curto; adesivo de isca na abertura ("o 17 é real demais").
- **Só reacts com virada** — sequência de reações que termina numa pergunta ("com quem eu vou falar sobre esse livro?") e a resposta vira o convite ("COM A GENTE!").
- **POV / checklist** — "Checklist de bookstan" com itens marcados por take.

**Ritmo:** primeiro som falado em até 1 s (cortar silêncio inicial); cada take aparado à frase mais forte (1–3 s; uma leitura engraçada pode ter até 6 s); acelerar tudo 10% com `setpts=PTS/1.1` + `atempo=1.1` (voz mantém o tom); jump cut alternando enquadramento 1.0/1.1–1.2; em cada troca de cena: punch-zoom de entrada (`scale=w='trunc(1080*(Z+0.3*pow(max(0,1-t/0.18),2))/2)*2':h=-2:eval=frame,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.36`), flash branco de 2 quadros (`eq=brightness='if(lt(t,0.06),0.45,0)':eval=frame`), whoosh e pop. Mosaico 3×3 com zoom-out por `zoompan` (z de 3→1 com easing) para a virada. Trilha: batida própria sintetizada (sem direitos de terceiros) com `sidechaincompress` sob a voz, respiro + riser + impacto antes da virada; entregar também versão sem trilha para música do Instagram (volume 15–20%).

**Letreiros:** fonte Anton (baixar de `raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf` para `~/fonts`, junto com Poppins e DejaVu) em caixas pretas/do selo, girados ±2–4°, entrada com pop (`\fscx40\fscy40\t(0,120,\fscx115\fscy115)\t(120,220,\fscx100\fscy100)`), tremida nos de alerta, legenda de 2 palavras com a palavra falada colorida, barra de progresso. Em ASS, `\N` vai FORA das chaves `{}` (dentro delas some e cola as palavras).

**Censura ("piii"):** para palavrão, duplo sentido forte ou trecho murmurado: zerar o áudio no intervalo (`volume=enable='between(t,A,B)':volume=0`), somar seno de 1 kHz no mesmo tempo, legenda `#@$!` e tarja preta "CENSURADO" sobre a boca (boca ≈ `0.6*1920*z − (1920*z−1920)*yf` no quadro final). O RedVelvet pode brincar com o duplo sentido censurado, nunca mostrar.

**CTA de DM sem @:** se a peça vai ao perfil do selo e o @ não estiver confirmado, usar "MANDA 'PALAVRA' NA DM" — leva direto ao perfil onde foi postado.

### Vídeo de iPhone (HDR) — corrigir sempre
Takes de iPhone vêm em HLG/BT.2020 10 bits. Sem conversão, a saída fica marcada como HDR e aparece lavada ou alaranjada em alguns aparelhos. Decodificar pelo ffmpeg (que respeita a matriz BT.2020) e gravar como SDR BT.709: `-vf "...,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" -colorspace bt709 -color_primaries bt709 -color_trc bt709`. Nunca ler HLG com OpenCV direto (troca a matriz e deixa tudo laranja).

### Maquiagem leve (olheiras e pele)
A pedido ("filtro de maquiagem", "tira as olheiras"), aplicar por take, antes dos letreiros: corretivo só abaixo dos olhos puxado para a cor da bochecha e pele suavizada preservando olhos, sobrancelhas e boca. Setup: `pip install --break-system-packages mediapipe "opencv-python-headless<5"` e baixar `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task` para `~/editor-falado/`. Rodar `python3 ~/editor-falado/maquiagem.py take.mp4 take_mq.mp4 [--forca 0.6–1.4]` (script em `scripts/maquiagem.py`; ≈3–4 quadros/s por núcleo; usar `xargs -P` em lote). Mantém a proporção e a rotação da gravação, entrega 30 fps sem perder a sincronia com o áudio e já converte para SDR BT.709. Mostrar um antes/depois recortado no rosto antes de processar tudo; o script avisa se o rosto apareceu em menos da metade dos quadros.

## 6. Limites e cuidados

- O aviso de anúncio ("⚠ ANÚNCIO") aponta termos que costumam ser barrados; é alerta, não garantia. Peças do RedVelvet seguem `padroes-da-casa`: sugerir, nunca mostrar; personagens sempre inequivocamente adultos.
- A transcrição erra nomes e números. Sempre revisar a fala que fica antes de renderizar.
- Fora do escopo deste motor: remover fundo sem tela verde, logos girando em 3D, painéis de interface animados, correção de cor fina e títulos animados complexos. Para esses, usar `premiere-after-effects` ou `adobe-criativo`.
- Gravações muito longas (aula de 1–2 h): analisar com `--modelo base`, entregar primeiro a lista de cortes e o vídeo depois; avisar que o render demora.
- O detector de rosto é simples (OpenCV): encontra rosto de frente e razoavelmente iluminado. De perfil, no escuro ou com mais de uma pessoa, conferir os quadros e, se a pessoa sair cortada, usar `--modo blur`.

## 7. Código do motor

O motor fica em `scripts/editor_falado.py` desta skill e a maquiagem em `scripts/maquiagem.py` (copiados para `~/editor-falado/` no passo 1). Não reescrever nem resumir o código: se faltar uma função, corrigir no arquivo do plugin e reempacotar.
