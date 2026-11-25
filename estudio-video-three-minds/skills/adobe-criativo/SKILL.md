---
name: adobe-criativo
description: "Executa a produção de vídeo e imagem pelo conector Adobe (Adobe for Creativity): montagem de timeline e renderização na nuvem, reenquadramento 9:16/16:9/4:5, highlight reel automático, limpeza de voz, conversão de formato, frames de prévia, Adobe Stock, Photoshop/Lightroom para thumbnails e capas, Adobe Fonts, Firefly Boards para storyboard e moodboard, Adobe Express para cartelas e posts, e envio ao Firefly Video Editor. Esta skill deve ser usada como caminho principal de execução do estúdio sempre que a equipe disser \"use a Adobe\", \"monte o vídeo\", \"renderize\", \"corta esses clipes\", \"faça a versão vertical\", \"limpa o áudio\", \"busca no Adobe Stock\", \"faz a thumbnail\", \"monta o moodboard\", \"manda para o Firefly\" ou \"anima no Express\".\n"
metadata:
  version: "0.6.0"
---

# Adobe criativo — motor de execução do estúdio

Usar o conector Adobe como caminho padrão para executar o que as outras skills planejam. Ler antes a skill `padroes-da-casa` (ficha do projeto, especificações, checklist de direitos).

## 0. Inicializar e checar ferramentas

1. Chamar `adobe_mandatory_init` uma vez por conversa, antes de qualquer outra ferramenta Adobe.
2. As ferramentas do conector costumam vir adiadas: carregar as necessárias por busca de ferramentas (todas de uma vez) antes de concluir que alguma não existe.
3. Se o conector não estiver conectado, avisar em uma linha que a equipe pode conectá-lo nas configurações de conectores do Claude, e seguir com a skill `edicao-automatica` (ffmpeg) como alternativa.

## 1. Levar os arquivos para a Adobe

As ferramentas de vídeo e áudio exigem `assetId` (URN) ou URL pré-assinada — nunca caminho local.
- Arquivo anexado na conversa: upload programático (`asset_initialize_file_upload` → envio dos blocos → `asset_finalize_file_upload`), se a rede permitir; se falhar duas vezes, abrir o seletor com `asset_add_file`.
- Arquivo já no Creative Cloud: `asset_search` (`CCAsset`, `GenAIAsset` para gerações do Firefly) ou `asset_add_file`.
- Adobe Stock: `asset_search` com `StockAsset` → mostrar opções → `asset_license_and_download_stock` só após a equipe aceitar a cotação/licença. Nunca editar a partir de miniaturas.
- Registrar cada mídia (nome, assetId, origem, licença) na lista de materiais do projeto.

## 2. Mapa de tarefas → ferramenta

| Tarefa | Ferramenta |
|---|---|
| Ler duração, resolução e fps | `video_metadata` |
| Montar timeline (cortes, ordem, trilha, volume) e renderizar | `video_render` (ver `references/timeline-adobe.md`) |
| Prévia de um quadro antes de renderizar | `video_render_frame` |
| Highlight reel automático a partir de brutos | `video_create_quick_cut` (critério visual, não entende a fala) |
| Reenquadrar para 1080×1920, 1920×1080, 1080×1350 | `video_resize` |
| Converter para MP4/MOV/GIF | `video_export` |
| Limpar voz e separar trilha/ambiente | `media_enhance_speech` |
| Resumir entrevista ou live (para YouTube longo, cortes) | `media_summarize` |
| Thumbnails, capas, recortes, fundo | `image_remove_background` (com `backgroundColor` para fundo sólido), `image_crop_and_resize`, `image_apply_adjustments`, `image_apply_preset`, `image_generative_expand` |
| Ajuste só numa região (escurecer o fundo para o título, realçar o rosto, cor do figurino) | `image_select_subject` / `image_select_by_prompt` → (`image_invert_selection`) → `image_apply_adjustments` ou `image_fill_area` com a máscara |
| Prova rápida de quadro-chave: fundo desfocado, tom automático, endireitar | `image_apply_lens_blur`, `image_apply_auto_tone`, `image_auto_straighten` |
| Fontes da identidade | `font_recommend`, `font_search`, `font_activate` |
| Storyboard/moodboard visual | `create_firefly_board` (um `temp_uuid` por projeto); para um board já existente: `boards_read` e `boards_add_items_to_board` (até 12 itens por chamada; gerações do Firefly como `generationUrn`, arquivos do CC como `cloudAsset`) |
| Cartelas, posts e capas de episódio desenhados | fluxo HTML → Express (`create_visual_design_express_skill` → `html_export_readiness_skill` → `export_html_to_express`) |
| Animar um design do Express | `animate_design` |
| Levar um MP4 pronto para ajuste fino no Firefly Video Editor | `import-claude-motion-from-url` |

As ferramentas de vídeo são assíncronas: quando retornarem `working`, aguardar o widget de progresso concluir; não ficar consultando.

## 3. Fluxo padrão de montagem

1. Ficha do projeto e roteiro/lista de planos aprovados (skills `roteiro-video`, `cinema-work` ou `novelinha-vertical`).
2. Upload/seleção das mídias; `video_metadata` em cada clipe.
3. Converter a lista de cortes em documento de timeline com `scripts/lista_para_timeline.py cortes.csv --ids midias.json --duracoes duracoes.json` (durações tiradas do `video_metadata`). O script recusa sobreposição na mesma trilha, cortes além do fim da mídia, escala inválida e timeline acima de 10 min, e alinha os tempos ao quadro.
4. Conferir 2–3 quadros-chave com `video_render_frame` (início, clímax, cartela final).
5. `video_render` → revisar → `video_resize` para os demais formatos → `video_export` se precisar de MOV/GIF.
6. Voz gravada: passar por `media_enhance_speech` antes de entrar na timeline.

## 4. O que a Adobe não faz por aqui — e o caminho

- **Texto em tela, legendas e títulos animados**: a timeline não tem camada de texto. Fazer as cartelas como imagens/vídeos curtos (Express ou `edicao-automatica`) e inseri-las como clipes; legendas queimadas via `edicao-automatica`; títulos animados avançados via After Effects (`premiere-after-effects`) ou CapCut.
- **Gerar imagens/vídeo novos com IA (texto → imagem/vídeo)**: indisponível pelo conector. Usar a skill `geracao-cinematografica` (APIs OpenAI e Runway, ou prompts para os modelos do Firefly — Veo, Kling, Nano Banana, GPT Image); gerações feitas no Firefly são buscadas depois com `asset_search` (`GenAIAsset`).
- **Remover objetos, trocar fundo por prompt, preenchimento generativo, upscale**: indisponível (as ferramentas de seleção só criam máscaras para ajustes e preenchimento com cor sólida); indicar Photoshop/Firefly no app.
- **Lotes acima de ~20 arquivos**: dividir ou indicar Bridge/Actions.
- Se uma ferramenta falhar e trouxer link de documentação, mostrar o link à equipe.

## 5. Entrega

Apresentar o resultado com `asset_preview_file`, informar formatos gerados, e anexar o checklist de direitos de `padroes-da-casa` preenchido. Nomear arquivos pelo padrão da casa. Se o MP4 final estiver disponível localmente, rodar `edicao-automatica/scripts/video_tools.py conferir` antes de entregar.
