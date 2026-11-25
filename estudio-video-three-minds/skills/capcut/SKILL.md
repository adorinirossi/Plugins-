---
name: capcut
description: "Trabalha com o CapCut de duas formas: prepara o pacote de montagem pronto para importar (mídias numeradas na ordem, legendas .srt, lista de cortes legível, textos de cartela, trilha e roteiro de efeitos) e, quando o computador estiver ligado ao Claude, opera o app CapCut desktop pela tela para montar, legendar e exportar. Esta skill deve ser usada quando a equipe disser \"monta no CapCut\", \"prepara para o CapCut\", \"pacote do CapCut\", \"legenda no CapCut\", \"usa os efeitos do CapCut\", \"template do CapCut\" ou \"exporta pelo CapCut\".\n"
metadata:
  version: "0.6.0"
---

# CapCut

O CapCut não tem conector nem importação de sequência (XML). Trabalhar em dois modos, conforme o que estiver disponível.

Para vídeo falado gravado (cortes de pausas e tomadas, legenda palavra por palavra), a skill `editor-falado` entrega o vídeo pronto aqui mesmo, sem o CapCut. Usar o CapCut quando a equipe pedir o app, os efeitos ou os templates dele.

## Modo 1 — Pacote de montagem (sempre possível)

Entregar uma pasta zipada `SELO_TITULO_CAPCUT_vNN/`:

```
01_gancho.mp4 · 02_mundo.mp4 · ...      mídias renomeadas na ordem da timeline (já cortadas, se possível)
trilha.mp3                               com licença registrada
legendas.srt                             gerado de roteiro ou transcrição
cartelas.txt                             texto de cada cartela + tempo de entrada/saída
MONTAGEM.md                              passo a passo da timeline (ver modelo abaixo)
licencas.md                              checklist de padroes-da-casa
```

Pré-cortar os clipes para que a montagem no CapCut seja só arrastar na ordem:
`python3 ../edicao-automatica/scripts/video_tools.py cortar cortes.csv --saida pacote/` (ou render dos trechos pela Adobe em `adobe-criativo`).

**Modelo de MONTAGEM.md**

```
Projeto: 9:16 · 30 fps · duração-alvo 0:45
1. Importe todos os arquivos e arraste 01→NN na timeline principal, sem espaços.
2. Áudio: trilha.mp3 na faixa de áudio; volume 30% sob a narração, 80% no clímax (00:32).
3. Legendas: Texto → Legendas → Importar arquivo .srt (se a versão não oferecer, Legendas automáticas em português e conferir com legendas.srt).
4. Cartelas: conforme cartelas.txt — fonte <selo>, tamanho grande, centro da zona segura.
5. Transições: corte seco; "flash branco" só no corte para o título (00:38).
6. Efeitos sugeridos: <ex.: leve zoom-in em 03 e 07; filtro único em todos os clipes>.
7. Exportar: 1080p, 30 fps, taxa recomendada; desmarcar marca d'água se a conta permitir.
```

Avisar: músicas da biblioteca comercial do CapCut podem não valer fora do app ou em anúncios — conferir licença.

## Modo 2 — Operar o CapCut no computador

Só quando a sessão estiver ligada ao computador da equipe com controle de tela disponível. Carregar antes a skill de uso do computador (`computer-use`) e seguir suas regras de acesso.

1. Confirmar que o pacote do Modo 1 está numa pasta do computador (enviar os arquivos para a pasta conectada, se necessário).
2. Abrir o CapCut, criar projeto, importar a pasta, montar na ordem, aplicar trilha, legendas e cartelas conforme MONTAGEM.md.
3. Tirar captura de tela após cada etapa grande para conferir; parar e perguntar se algo inesperado aparecer (login, pagamento, recurso Pro).
4. Nunca aceitar cobranças, assinar recursos pagos ou publicar em redes pela conta da equipe sem confirmação explícita.
5. Exportar para a pasta do projeto com o nome padrão da casa.

Operar por tela é mais lento e sujeito a mudanças de interface do app; quando falhar duas vezes na mesma etapa, entregar o pacote do Modo 1 e listar o que falta fazer à mão.
