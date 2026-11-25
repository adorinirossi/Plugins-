# Retenção — do gráfico para a regra de roteiro

Retenção é o sinal mais pesado dos três feeds. Em canal sem rosto, ela se resolve primeiro na edição e no roteiro.

## Regras de partida (até haver dados do canal)
- **0–2 s:** imagem em movimento + texto em tela que entrega a promessa; sem logo, sem "olá".
- **Abertura fria:** começar pelo resultado, pela tensão ou pela pergunta, nunca pelo contexto.
- **Troca visual a cada 3–5 s**, no tempo da ênfase da narração.
- **Reinício de atenção** a cada 8–12 s: nova pergunta, contraste, exemplo ou mini-recompensa.
- **Payoff antes do fim:** a promessa da abertura é cumprida antes dos últimos 20% do vídeo; CTA curto depois.
- **Duração:** a menor que entrega o ganho de informação; começar em 25–45 s nos curtos.

## Coleta (a cada rodada)
O Instagram (Insights do Reel), o YouTube Studio (Retenção do público) e o TikTok Studio (Retenção) mostram o gráfico por vídeo. Pedir à equipe prints dos 3 melhores e 3 piores da rodada, ou ler pelo navegador se o computador estiver ligado. Preencher em `metricas/AAAA-MM-DD-manual.csv` as colunas:
- `retencao_3s` — % que passou dos 3 primeiros segundos (YouTube/TikTok mostram; no Instagram, ler do gráfico)
- `retencao` — % que viu até o fim (ou % médio visto)
- `queda_seg` — segundo da maior queda depois da abertura
- `queda_motivo` — o que acontecia na tela naquele segundo (preenchido pela IA olhando o roteiro e o vídeo)

`canal.py analisar` lê essas colunas e reporta, por formato e por tipo de abertura: retenção média aos 3 s, retenção final e segundo médio de queda.

## Do dado para a regra
Depois de 10–20 vídeos, transformar padrões em regras do modelo de roteiro, em `aprendizados.md`, por exemplo:
- "Formato B perde 30% entre 6 e 9 s — a explicação de contexto está entrando cedo demais; mover para depois do primeiro exemplo."
- "Aberturas com objeto em close seguram 3 s melhor que texto sobre fundo liso (+12 p.p., n=8)."
O roteiro (skill `roteiro-video`) recebe as regras vigentes do canal como restrições: cada roteiro novo indica, na coluna Som/Notas, onde estão o gancho, os reinícios e o payoff, com tempo.
