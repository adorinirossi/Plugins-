# Estúdio de Vídeo Three Minds

Plugin de produção de vídeo da Three Minds Publishing (RedVelvet, Sophia, Three Minds Editions, FannyBooks, PrismaBooks): booktrailers, Reels/TikTok/Shorts, YouTube longo, anúncios pagos e novelinha vertical (microdrama).

## Habilidades

| Habilidade | O que faz |
|---|---|
| `padroes-da-casa` | Ficha do projeto, especificações por plataforma, identidade dos selos, checklist de direitos e políticas (conteúdo adulto) |
| `cinema-work` | Tutor e condutor de trailers e vídeos narrativos com IA, uma tarefa por vez, com registro do projeto |
| `roteiro-video` | Roteiros, ganchos, lista de planos e lista de cortes por formato |
| `novelinha-vertical` | Bíblia, escaleta, mapa de cliffhangers e roteiros de episódios de 2–3 min |
| `adobe-criativo` | **Motor principal**: montagem e render na nuvem pelo conector Adobe, reenquadramento, limpeza de voz, Stock, Photoshop/Lightroom, Fonts, Firefly Boards, Express |
| `geracao-cinematografica` | Imagens e vídeos ultrarrealistas: GPT Image 2 (API OpenAI), Runway Gen-4.5 / Gen-4 Image (API) e modelos do Firefly (Veo 3.1, Kling 3.0, Nano Banana); prompts de câmera, consistência de personagem, custo e registro |
| `premiere-after-effects` | XML de sequência para o Premiere, títulos animados (.jsx) no After Effects, presets |
| `capcut` | Pacote de montagem pronto para o CapCut e operação do app pelo computador |
| `operacao-de-canal` | Canal contínuo em ciclo fechado ("usina"): ficha do canal, pauta em lote 70/20/10, produção em lote, calendário e kit diário de postagem, análise de métricas das exportações gratuitas, aprendizados, painel e tarefas agendadas; trava de originalidade com teste de semelhança, ciclo de retenção, versão por rede e controle de voz/pronúncia |
| `editor-falado` | Vídeo falado gravado (Reels, TikTok, Shorts, anúncio, aula, vlog) editado por conversa: tira pausas, hesitações e tomadas repetidas (fica a melhor tomada), legenda palavra por palavra, gancho, cartões animados, enquadramento seguindo o rosto, .srt, versões por gancho e formato |
| `edicao-automatica` | ffmpeg: cortes, vertical com fundo desfocado, legendas queimadas, cartelas, −14 LUFS com ducking, exportação múltipla |

## Requisitos

- **Conector Adobe** (Adobe for Creativity) conectado nas configurações de conectores do Claude, com a conta Creative Cloud da editora.
- **CapCut**: sem conector oficial. Para operação automática, abrir a tarefa no app desktop do Claude ligado ao computador onde o CapCut está instalado.
- **Premiere Pro / After Effects**: instalados no computador da equipe; os arquivos gerados (XML, .jsx, .srt) são abertos por lá.
- Os scripts locais usam Python 3. Para edição automática, confira `ffmpeg` e `ffprobe` no PATH. As cartelas e legendas exigem os filtros `drawtext` e `subtitles`, respectivamente.
- **Editor falado**: Python 3 com `faster-whisper`, `numpy` e `opencv-python-headless` (`pip install --break-system-packages faster-whisper numpy "opencv-python-headless<5"` — o OpenCV 5 não traz mais o detector de rosto) e ffmpeg com `libass`. Na primeira análise, o modelo de transcrição `large-v3-turbo` (~1,6 GB) é baixado uma vez; gravações acima de 10 min usam o `small` (~460 MB). O download exige o acesso à rede liberado nas configurações de Capacidades do Claude.
- **Geração com OpenAI e Runway**: chaves de API configuradas como variáveis de ambiente no computador onde os scripts rodam — nunca dentro do plugin:
  - `OPENAI_API_KEY` (platform.openai.com, com faturamento ativo)
  - `RUNWAYML_API_SECRET` (dev.runwayml.com — créditos de API são separados da assinatura do app Runway)
  - Mac: adicionar `export OPENAI_API_KEY="..."` e `export RUNWAYML_API_SECRET="..."` ao `~/.zshrc`; Windows: Configurações → Variáveis de ambiente.
  - Os scripts rodam no computador da equipe (sessão ligada ao computador). O ambiente de nuvem do Claude bloqueia essas APIs, a menos que os domínios `api.openai.com` e `api.dev.runwayml.com` sejam liberados nas configurações de Capacidades.
- **Conector Runway (MCP)**: o plugin declara o servidor oficial hospedado `https://mcp.runwayml.com/mcp`. Ele entra com a conta do app Runway e usa os créditos do plano (não da API), sem chave. No primeiro uso, autorizar o login quando o Claude pedir; no ambiente de nuvem, o domínio `mcp.runwayml.com` precisa estar liberado na rede. Sem o conector, a geração segue pelos scripts da API.

- **Operação de canal**: pasta do canal no Google Drive (conector Google Drive) para as tarefas agendadas rodarem sem o computador. Publicação pelos agendadores nativos gratuitos (Meta Business Suite, TikTok Studio, YouTube Studio); Metricool/Buffer opcionais.

## Primeiros passos

1. Preencher a identidade dos selos em `skills/padroes-da-casa/references/identidade-selos.md` (cores, fontes, logos, tom) e reempacotar — ou responder quando o Claude perguntar no primeiro projeto.
2. Pedir, por exemplo: "vamos começar o trailer do livro X", "transforma o livro Y em novelinha", "monta esse reels na Adobe", "edita essa gravação e legenda", "prepara o pacote do CapCut", "cria o canal do selo Sophia", "liga a usina do canal".

## Limites conhecidos

- O conector Adobe não gera imagens/vídeos novos por texto nem remove objetos; a geração vai pelas APIs OpenAI/Runway ou pelo app Firefly (o plugin escreve os prompts e depois busca as gerações).
- Geradores bloqueiam nudez e conteúdo sexual; peças do RedVelvet trabalham sugestão.
- A timeline do render na nuvem não tem camada de texto: cartelas e legendas são feitas como clipes (Express ou ffmpeg) ou no After/CapCut.
- Regras e limites das plataformas mudam; o plugin confere na web quando a peça estiver perto do limite.


## Versão 0.5.0

- O calendário e o kit conferem a aprovação final do vídeo. Novas entradas ocupam horários livres e respeitam o limite diário. Registre as capas em `capa` ou `capa_<rede>` em `pautas.csv`.
- O índice de desempenho redistribui o peso de métricas ausentes entre as disponíveis. Campos com zero registrado continuam participando do cálculo.
- O editor aceita adicionar trilha a vídeos sem faixa de áudio, preserva faixas silenciosas e renderiza texto literal nas cartelas. O conversor Adobe valida duração, posição, FPS e lista de cortes vazia.

## Versão 0.5.1

- Nova habilidade `editor-falado`, que substitui a antiga `editora-de-retencao`. Edita gravações faladas por conversa, com o motor em `skills/editor-falado/scripts/editor_falado.py`.
- Transcrição com `large-v3-turbo` em gravações de até 10 min. Se o modelo falhar, o motor cai para o `small` e avisa.
- Tomadas repetidas: fica a melhor (`--tomada melhor`, padrão) ou a última (`--tomada ultima`). Uma tentativa descartada que traga informação nova é mantida e sinalizada.
- Frases divididas por pontuação, por pausa longa e por recomeço. "É" arrastado e isolado é cortado como hesitação.
- `ajustar --abrir N` abre o vídeo com a frase mais forte.
- `--modo auto|rosto|crop|blur`: no reenquadramento, o corte segue o rosto (OpenCV) e usa fundo desfocado quando a proporção é muito diferente.
- Cada render grava também o `.srt` da versão editada.
- `operacao-de-canal`, `edicao-automatica`, `capcut` e `roteiro-video` encaminham vídeo falado gravado para o `editor-falado`.

## Versão 0.6.0

- **Edição (ffmpeg)**: novos comandos `conferir` (checa resolução, fps, codec, duração, −14 LUFS/−1 dBTP e nome do arquivo contra o padrão da casa) e `quadros` (folha de contato para revisão). Corrigidos: legenda queimada falhava com aspas, dois-pontos ou espaços no caminho; `cortar` quebrava sem duração; `srt` aceita timecode (`01:02.5`) e avisa legenda curta ou sobreposta; `exportar` valida o formato; `concatenar` mantém áudio e vídeo com a mesma duração em cada clipe (sem dessincronia acumulada); cartelas com linhas centralizadas.
- **Adobe**: o conversor da lista de cortes recusa clipes sobrepostos na mesma trilha, escala inválida, números malformados e cortes além do fim da mídia (`--duracoes`), e alinha os tempos ao quadro. Mapa de ferramentas atualizado (seleção + ajuste local, Firefly Boards existentes).
- **Premiere**: o XML declarava a mídia depois de referenciá-la em alguns casos (importação quebrada); agora a ordem é sempre válida, vídeo e áudio vêm vinculados, e trilhas, ganho, sobreposição e marcadores são validados.
- **After Effects**: títulos longos encolhem até caber na zona segura, durações curtas não quebram a animação, aviso de fonte ausente e geração de uma composição por episódio (`EPISODIOS`).
- **Geração**: nenhuma geração sobrescreve outra (`_v2`, `_v3`); Runway texto→vídeo usa a rota `text_to_video`; a espera repete falhas de rede passageiras; `runway.py status ID --saida` recupera uma tarefa já paga. Skill documenta o conector Runway (MCP).
- **Editor falado**: `ajustar --manter` agora devolve tomadas e hesitações (antes, uma pausa por cima continuava cortando); vídeo de celular gravado em pé (metadado de rotação) não sai mais esticado; vídeo HDR de iPhone vira SDR BT.709 sozinho; loudness conferido e corrigido após o render; legenda funciona em pastas com aspas ou dois-pontos e em Windows (UTF-8); chaves no texto não quebram mais a legenda; cartões aceitam gatilho de várias palavras, só disparam na fala que fica e não duplicam (`--limpar`); filtro de anúncio sem falso positivo ("curadoria", "procura", "dia 18") e aplicado também ao gancho; validação de `--abrir`, `--cortar`, `--manter`, `corrigir`, `--palavras` e formatos. O OpenCV fica fixo em `<5`.
- **Maquiagem**: virou `scripts/maquiagem.py` (estava colada no SKILL.md); mantém proporção e rotação, não fica em câmera lenta com vídeo de 60 fps e avisa quando quase não encontrou rosto.
- **Selos**: FannyBooks e PrismaBooks entram na identidade dos selos, na ficha do projeto e na ficha do canal, com cores provisórias até terem identidade própria.
- **Canal**: views comparadas dentro de cada rede no índice, empates com nota justa, status aceita maiúsculas, kit com link UTM (`link`/`link_<rede>`), bottom 3 sem repetir o top 3, painel com tema claro/escuro correto no celular.
