# Modo usina — automação com tarefas agendadas

A "usina" não é uma IA ligada 24 horas: é produção em lote + fila de postagem + leitura periódica. Aqui o ciclo roda sozinho com **tarefas agendadas do Claude** (ferramentas de agendamento da sessão; chamar de "tarefas agendadas" com a equipe). Cada execução começa do zero, então cada tarefa lê a pasta do canal antes de agir.

## Pré-requisitos
- **Pasta do canal no Google Drive** (as execuções rodam na nuvem e alcançam o Drive pelo conector). Pasta só no computador exige a tarefa marcada como dependente do computador, e o computador ligado.
- Conector **Adobe** conectado (montagem/render na nuvem).
- Geração de imagem/vídeo por API (OpenAI/Runway) só roda no computador da equipe ou com os domínios liberados nas Capacidades; sem isso, a tarefa de produção usa Adobe Stock/Firefly e avisa o que ficou pendente.
- Aprovação: **pauta e lote** (padrão da casa). Nenhuma tarefa publica nem agenda.

## As tarefas (fuso America/Sao_Paulo)

| Tarefa | Quando | O que faz | Para e espera |
|---|---|---|---|
| Pauta da rodada | a cada 14 dias, segunda 7h40 | lê ficha + aprendizados + pautas; gera o lote 70/20/10 em `pautas.csv` (status `proposta`); avisa a equipe | aprovação da pauta |
| Produção do lote | diária 13h10, só age se houver pauta `aprovada` sem produzir | roteiro → voz → visual → montagem dos aprovados; status `produzida`; avisa | aprovação do lote |
| Kit do dia | diária 6h50 | monta o kit dos posts do dia (ou da semana às segundas) com vídeos `aprovado`; avisa "kit pronto" | — (a equipe publica) |
| Cobrança da noite | diária 21h20 | confere no `calendario.csv` o que ficou `pendente` hoje; avisa só se faltar algo | — |
| Análise semanal | segunda 8h20 | se houver métricas novas em `metricas/`, roda `analisar`, gera relatório e painel, propõe até 3 aprendizados; se não houver, lembra a equipe de exportar | aprovação dos aprendizados |

Ajustar horários ao que a equipe preferir; evitar minuto 0 e 30 (filas mais lentas).

## Modelo de instrução de cada tarefa
Cada instrução deve ser autossuficiente, por exemplo (pauta):

> Você opera o canal "<nome>" da Three Minds com a skill operacao-de-canal do plugin estudio-video-three-minds. Abra a pasta do canal no Google Drive "<caminho>", leia ficha-do-canal.md, aprendizados.md e pautas.csv. Gere a pauta da próxima rodada seguindo references/pauta-em-lote.md (14 dias de cadência, 70/20/10, sem repetir títulos/ganchos), grave as linhas com status "proposta" e escreva relatorios/pauta-AAAA-MM-DD.md com a tabela para aprovação. Não produza nem publique nada. Termine com uma mensagem curta: quantas pautas, o que mudou em relação ao lote anterior e o pedido de aprovação.

As demais seguem o mesmo padrão: pasta, arquivos a ler, uma ação, o limite ("não publique", "só vídeos com status aprovado") e a mensagem final.

## Como a equipe aprova
Responder na conversa da tarefa ("aprovo, corta a 4 e a 9") ou editar o status em `pautas.csv`. Gravar `aprovada` para liberar a produção e `aprovado` após a revisão do vídeo final. O kit diário usa a aprovação final registrada no CSV.

## Ao criar as tarefas
- Conferir as tarefas já existentes para não duplicar.
- Informar à equipe, em uma frase por tarefa, quando roda e se pede aprovação ao executar ações.
- Notificação por push ligada; e-mail só se a equipe pedir.
