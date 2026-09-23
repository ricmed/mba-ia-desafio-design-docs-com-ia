# ADR-003 — Retry com backoff exponencial de 5 tentativas e DLQ em tabela separada

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Diego (Eng. Sênior, Plataforma), Larissa (Tech Lead), Bruno (Eng. Pleno, Pedidos), Marcos (PM), Sofia (Eng. Segurança)
- **Origem:** `TRANSCRICAO.md` [09:14]–[09:18], [09:35]–[09:37], [09:42]
- **Relacionado:** [ADR-002](ADR-002-worker-processo-separado-polling.md), [ADR-005](ADR-005-entrega-at-least-once-com-x-event-id.md)

## Contexto

A entrega de um webhook depende de um sistema de terceiro que pode estar fora do ar, lento ou respondendo erro. A pergunta colocada foi direta: "Se o cliente tá offline, o que a gente faz?" ([09:14] Larissa).

Duas informações operacionais moldaram a resposta:

- Já houve cliente da plataforma com **indisponibilidade de duas horas** em manutenção planejada ([09:16] Diego).
- Um cliente que fique fora do ar por muitas horas "já tá com problema sério dele" — perder o evento nesse cenário é aceitável do ponto de vista de produto ([09:17] Marcos).

Também era preciso decidir o destino do evento que esgota as tentativas e se o operador teria como reprocessá-lo ([09:17] Larissa, [09:18] Bruno).

## Decisão

**Retry com backoff exponencial, teto de 5 tentativas, e DLQ persistida em tabela separada.**

- **Progressão do backoff:** 1 minuto, 5 minutos, 30 minutos, 2 horas, 12 horas — quase 15 horas entre a primeira falha e a última tentativa ([09:17] Diego, confirmado por [09:17] Larissa).
- **Teto de 5 tentativas** ([09:15] Diego, fechado em [09:16] Larissa).
- **Critério de falha:** resposta de erro do cliente ou **timeout de 10 segundos** sem resposta ([09:42] Diego).
- **DLQ em tabela separada** `webhook_dead_letter`, guardando a payload, o motivo da falha e o timestamp ([09:18] Diego). Esgotadas as tentativas, o evento sai da outbox principal e vai para lá.
- **Reprocessamento manual** via endpoint administrativo `POST /admin/webhooks/dead-letter/:id/replay`, que recoloca o evento na outbox como pendente ([09:18] Diego, [09:35] Diego).
- **Replay exige role `ADMIN`** e **registra em log quem executou**, para auditoria ([09:36] Sofia, [09:36] Larissa). O controle reaproveita o `requireRole` já existente em `src/middlewares/auth.middleware.ts`.

## Alternativas Consideradas

### A. 3 tentativas em vez de 5 — **descartada**

Bruno propôs uma política mais agressiva, com 3 tentativas ([09:16]).

- Trade-off que motivou o descarte: 3 tentativas na progressão proposta esgotariam a janela em cerca de 30 minutos. Um cliente com indisponibilidade matinal — cenário já observado, de até duas horas em manutenção planejada — teria seus eventos descartados sem necessidade ([09:16] Diego). Cinco tentativas cobrem uma janela de 12 a 24 horas e absorvem esse caso ([09:15] Diego).

### B. Retry indefinido com backoff — **descartada**

Diego registrou que há quem defenda retentar para sempre com intervalos crescentes ([09:15]).

- Trade-off que motivou o descarte: um evento cujo destinatário sumiu permanentemente ficaria pendurado para sempre, consumindo recurso do worker e poluindo a fila indefinidamente ([09:15] Diego). O teto torna o estado do sistema finito e previsível.

### C. DLQ como flag `failed` na própria tabela outbox — **descartada**

Larissa perguntou explicitamente se não bastaria marcar o evento como "failed" na própria outbox ([09:17]).

- Trade-off que motivou o descarte: a tabela separada mantém limpa a leitura da outbox principal — o worker varre apenas eventos vivos — e preserva o evento morto como evidência para debug e reprocessamento, com o motivo da falha registrado ([09:18] Diego). O custo é uma tabela e uma movimentação de linha a mais, considerado barato.

### D. Notificar o cliente por e-mail após falhas seguidas — **descartada nesta fase**

Marcos perguntou se seria possível avisar o cliente por e-mail quando o webhook dele falhasse três vezes seguidas ([09:37]).

- Decisão: **não entra nesta fase**. Larissa adiou para uma fase futura, após medição do impacto ([09:37]). Registrado aqui para deixar explícito que foi avaliado e descartado — não é requisito desta entrega.

## Consequências

### Positivas

- Absorve indisponibilidades reais dos clientes, inclusive manutenções planejadas de várias horas, sem intervenção humana.
- O estado de cada evento é finito: ou entregue, ou na DLQ. Não existe evento em retry perpétuo.
- A DLQ funciona como evidência: payload, motivo e timestamp permitem diagnosticar por que a entrega falhou.
- O replay manual dá caminho de recuperação sem acesso direto ao banco, com trilha de auditoria de quem acionou.

### Negativas (trade-offs aceitos)

- **Até ~15 horas** entre a primeira falha e a desistência: o cliente que voltou do ar pode receber um evento bastante antigo. Aceito ([09:17] Marcos).
- Eventos em retry longo ocupam linhas da outbox por até 15 horas, aumentando o volume que o worker varre a cada ciclo.
- O replay é **manual** — não existe reprocessamento automático da DLQ. Um incidente com muitos eventos mortos exige ação operacional evento a evento ([09:18] Diego).
- Não há alerta proativo ao cliente quando suas entregas começam a falhar (o e-mail ficou fora de escopo), então a descoberta depende de o cliente consultar o histórico de entregas ou de monitoramento interno.
- A ordem de entrega dos eventos de um mesmo pedido pode se inverter quando um evento entra em retry longo e os seguintes são entregues normalmente — consequência direta de não bloquear a fila por um destinatário problemático.
