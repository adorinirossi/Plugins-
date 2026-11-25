---
name: geracao-cinematografica
description: "Gera imagens e vídeos cinematográficos e ultrarrealistas para trailers, novelinhas e anúncios, escolhendo o melhor gerador para cada plano: OpenAI GPT Image 2 (API), Runway Gen-4.5 e Gen-4 Image (API) e os modelos do Adobe Firefly (Veo 3.1, Kling 3.0, Nano Banana, GPT Image, FLUX) pelos créditos da Creative Cloud. Escreve prompts com linguagem de câmera, mantém personagens consistentes com imagens de referência, estima custo, baixa e registra cada geração. Esta skill deve ser usada quando a equipe disser \"gera a imagem do plano\", \"cria o quadro-chave\", \"anima essa imagem\", \"gera o vídeo do plano 3\", \"faz no GPT\", \"faz na Runway\", \"qual modelo uso?\", \"mantém o rosto da personagem\", \"gera as variações\" ou \"quanto vai custar gerar o trailer\".\n"
metadata:
  version: "0.6.0"
---

# Geração cinematográfica (imagem e vídeo com IA)

Antes de gerar: ficha do projeto e checklist de `padroes-da-casa`; lista de planos aprovada (`roteiro-video`, `cinema-work` ou `novelinha-vertical`); bíblia visual com fichas de personagem e bloco de estilo (etapa 5 de `cinema-work`). Não inventar traços de personagens: o que não estiver na obra ou aprovado vira pendência.

## 1. Escolher o gerador por plano

| Necessidade do plano | 1ª escolha | Alternativa |
|---|---|---|
| Quadro-chave fotorrealista (rosto, pele, luz) | GPT Image 2 (API OpenAI) | Nano Banana Pro / GPT Image 2.5 no Firefly |
| Mesmo personagem em vários planos | Runway Gen-4 Image com referências | GPT Image 2 edição com referências; Nano Banana no Firefly |
| Imagem → vídeo com controle de câmera | Runway Gen-4.5 | Kling 3.0 no Firefly |
| Plano de ambiente ultrarrealista com som | Veo 3.1 no Firefly | Runway Gen-4.5 (sem som) |
| Pessoas em movimento, várias tomadas | Kling 3.0 no Firefly | Runway Gen-4.5 |
| Teste rápido e barato | Runway gen4_turbo / gen4_image_turbo; Veo 3.1 Fast no Firefly | GPT Image 2 qualidade média |

Detalhes, custos e formatos: `references/modelos-e-custos.md`. Verificar na web se surgiu versão nova quando o projeto for grande — esses modelos mudam a cada poucos meses.

## 2. Onde a geração roda

**Conector Runway (MCP oficial, `mcp.runwayml.com`)** — declarado no plugin. Usa o login e os créditos do **plano do app Runway** (não a API), sem chave. Antes de concluir que não existe, buscar as ferramentas da Runway por busca de ferramentas. Se o servidor não conectar (rede bloqueada, login não feito), avisar a equipe em uma linha (autorizar o conector nas configurações do Claude ou liberar o domínio na rede do ambiente) e seguir pelos scripts abaixo. Preferir o conector para gerações avulsas pelo chat; preferir os scripts quando for preciso lote, registro automático em `registro.csv` ou faturamento pela API.

**Scripts (API)**

- Os scripts `scripts/openai_imagem.py` e `scripts/runway.py` leem as chaves das variáveis de ambiente `OPENAI_API_KEY` e `RUNWAYML_API_SECRET`. Nunca gravar chaves em arquivos do projeto, no plugin, no registro ou em mensagens. Se alguém colar uma chave no chat, recomendar trocá-la (revogar e gerar outra) e configurá-la como variável de ambiente.
- Rodar no computador da equipe (sessão ligada ao computador, pelo shell do dispositivo) — é onde as chaves ficam. O ambiente de nuvem do Claude bloqueia `api.openai.com` e `api.dev.runwayml.com` por padrão; só usar a nuvem se o administrador liberar esses domínios nas configurações de Capacidades do Claude.
- A API da Runway é cobrada em créditos de desenvolvedor (dev.runwayml.com), separados da assinatura do app Runway. A API da OpenAI exige faturamento ativo na conta da API.
- Firefly: a geração acontece no app/web do Firefly, pela equipe, com créditos da Creative Cloud. O conector Adobe não dispara essas gerações; depois, buscar os resultados com `asset_search` (`GenAIAsset`) pela skill `adobe-criativo`.

## 3. Escrever o prompt

Usar a estrutura de `references/prompts-cinematograficos.md`:
`[ficha do personagem] + [ação] + [enquadramento e lente] + [luz] + [cenário] + [bloco de estilo] + [proporção]`
- Reaproveitar a ficha e o bloco de estilo literalmente em todos os planos.
- Para vídeo: descrever só o movimento (câmera + sujeito), curto e físico; a imagem já define o visual.
- Mudar uma variável por vez entre tentativas.
- Evitar clichês ("8K, hiper-realista, obra-prima"); preferir câmera, lente, filme, luz reais.

## 4. Gerar

**OpenAI — quadro-chave e edição com referência**
```
python3 scripts/openai_imagem.py gerar --prompt-arquivo p01.txt --formato vertical --qualidade high --saida geracoes/P01
python3 scripts/openai_imagem.py editar --prompt-arquivo p02.txt --ref geracoes/P01_1.png --ref ficha_rosto.png --formato vertical --saida geracoes/P02
```

**Runway — imagem com referências e vídeo**
```
python3 scripts/runway.py imagem --prompt "@ana olha pela janela..." --ref ana=ficha_ana.png --proporcao 1080:1920 --saida geracoes/P03
python3 scripts/runway.py video --imagem geracoes/P01_1.png --prompt "slow push-in, she turns her head toward the door" --proporcao 720:1280 --duracao 5 --saida geracoes/P01_mov
python3 scripts/runway.py custo --modelo gen4.5 --segundos 40
```
O script espera a tarefa terminar e baixa o resultado na hora (os links da Runway expiram em 24 h). Sem `--imagem`, `gen4.5` gera texto→vídeo (rota `text_to_video`). Quedas de rede durante a espera são repetidas sozinhas; se a espera cair, a tarefa já paga continua na Runway — recuperar com `python3 scripts/runway.py status ID --saida geracoes/P01_mov` (o ID aparece no início da execução).

Nenhum dos scripts sobrescreve arquivo existente: uma nova tentativa com o mesmo `--saida` vira `P01_v2.mp4`, `P01_1_v2.png`… — a versão aprovada nunca é perdida.

Os dois scripts registram cada geração em `geracoes/registro.csv` (data, ferramenta, modelo, prompt, referências, arquivo, custo estimado). Copiar o prompt aprovado para o registro do projeto (`cinema-work`).

## 5. Revisar antes de seguir

Abrir cada resultado (Read na imagem; para vídeo, `edicao-automatica/scripts/video_tools.py quadros clipe.mp4 --n 3` e Read na `folha.png`) e checar: rosto e figurino iguais à âncora, mãos e dentes, texto indesejado, luz coerente com o bloco de estilo, adulto inequívoco, nada explícito. Apontar uma correção prioritária e gerar de novo só o necessário.

## 6. Conteúdo e direitos

- Os geradores bloqueiam nudez e conteúdo sexual; para RedVelvet, trabalhar tensão, olhar, mãos, respiração, tecido, luz — nunca tentar contornar filtros.
- Não gerar rostos de pessoas reais nem imitar atores, sem autorização por escrito.
- Rotular como conteúdo de IA onde a plataforma exigir. Para anúncios de clientes, preferir modelos com uso comercial claro (Firefly) quando houver dúvida.

## 7. Entregar para a montagem

Renomear os aprovados na ordem dos planos (`P01_final.mp4`…), subir para a Adobe e seguir em `adobe-criativo` (timeline), `capcut` (pacote) ou `premiere-after-effects`.
