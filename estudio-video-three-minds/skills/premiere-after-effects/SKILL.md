---
name: premiere-after-effects
description: "Prepara projetos para Premiere Pro e After Effects no computador da equipe: gera a sequência pronta para importar no Premiere (XML com cortes, trilhas e marcadores), legendas .srt, scripts .jsx do After Effects para títulos animados, lower thirds, cartelas e templates de episódio, e orienta exportação e presets. Esta skill deve ser usada quando a equipe disser \"monta no Premiere\", \"gera o XML da sequência\", \"abre isso no Premiere\", \"faz o título animado no After\", \"script do After Effects\", \"template de cartela\", \"lower third\", \"preset de exportação\" ou quando a peça precisar de acabamento que o render na nuvem da Adobe não faz (texto animado, cor, efeitos).\n"
metadata:
  version: "0.6.0"
---

# Premiere Pro + After Effects

Usar quando o acabamento exigir os apps desktop. Para montagens simples, preferir `adobe-criativo` (render na nuvem).

## Premiere Pro — sequência pronta

1. Partir da lista de cortes CSV (mesmo formato de `adobe-criativo`).
2. Pedir à equipe a pasta onde as mídias estão no computador dela (ou usar nomes de arquivo; o Premiere oferece "Localizar" para religar).
3. Gerar o XML: `python3 scripts/gerar_xml_premiere.py cortes.csv --formato 9:16 --pasta "/Users/.../Midia" --nome "RV_TRAILER_v01" > sequencia.xml`
4. Instruir: Premiere → Arquivo → Importar → `sequencia.xml`. Mídias offline → botão direito → Vincular mídia. Vídeo e áudio dos clipes da trilha principal vêm vinculados (movem juntos). O script recusa trilha desconhecida e clipes sobrepostos na mesma trilha — corrigir a lista de cortes e gerar de novo.
5. Legendas: gerar `.srt` (`edicao-automatica/scripts/video_tools.py srt`) e importar como faixa de legenda; ou usar a transcrição automática do Premiere (Texto → Transcrever) e ajustar estilo.
6. Exportação: seguir `padroes-da-casa/references/especificacoes-plataformas.md`; sugerir salvar presets "TM_Reels_1080x1920" e "TM_YouTube_1080p".

Para automação além do XML (painéis, scripts internos do Premiere), checar a versão instalada: versões recentes usam UXP; ExtendScript só nas versões que ainda o aceitam. Na dúvida, ficar no XML, que funciona em qualquer versão.

## After Effects — títulos e templates

1. Usar `scripts/titulos_ae.jsx` como base: cria composição 1080×1920 (ou 1920×1080), camada de fundo opcional, título com animação de entrada (fade + subida + leve escala), subtítulo e saída.
2. Antes de entregar, editar no topo do script as variáveis `TITULO`, `SUBTITULO`, `FONTE`, `COR`, `FORMATO`, `DURACAO` com a identidade do selo (`padroes-da-casa/references/identidade-selos.md`). A fonte precisa estar ativa no Adobe Fonts (`font_activate` em `adobe-criativo`); se não estiver, o script avisa no console do ExtendScript qual fonte o After usou. Títulos longos encolhem sozinhos até caber em `LARGURA_MAX` (84% da largura, zona segura).
3. Instruir: After Effects → Arquivo → Scripts → Executar arquivo de script → `titulos_ae.jsx`. Renderizar pela Fila de Renderização ou Media Encoder (ProRes 4444 com alfa se for sobrepor no Premiere/CapCut).
4. Para novelinha vertical: preencher `EPISODIOS = ["O contrato", "A primeira noite", ...]` e `EP_INICIAL`; o script cria uma composição por episódio (`TM_TITULO_9x16_EP01`…) com o subtítulo "EP. 01 — O contrato".

## Boas práticas de acabamento

- Cor: aplicar um LUT/ajuste único em camada de ajuste para unificar planos gerados por IA.
- Áudio: −14 LUFS; voz limpa antes (`media_enhance_speech`).
- Salvar o projeto com o nome padrão da casa e versionar (`_v01`, `_v02`).
