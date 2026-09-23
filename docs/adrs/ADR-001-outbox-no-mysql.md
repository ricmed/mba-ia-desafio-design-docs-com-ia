# ADR-001 — Padrão Outbox no MySQL para publicação de eventos de pedido

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Larissa (Tech Lead), Diego (Eng. Sênior, Plataforma), Bruno (Eng. Pleno, Pedidos)
- **Origem:** `TRANSCRICAO.md` [09:03]–[09:08]
- **Relacionado:** [ADR-002](ADR-002-worker-processo-separado-polling.md), [ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md), [ADR-007](ADR-007-payload-snapshot-na-insercao-do-outbox.md)

## Contexto

A plataforma precisa notificar clientes B2B sempre que o status de um pedido muda. Hoje não existe nenhum mecanismo de notificação externa no sistema: uma varredura por `webhook`, `outbox`, `queue` ou `EventEmitter` em `src/`, `prisma/` e `tests/` não retorna nenhuma ocorrência.

A mudança de status acontece em `src/modules/orders/order.service.ts`, no método `changeStatus`, que executa tudo dentro de `this.prisma.$transaction(async (tx) => ...)`: valida a transição com `canTransition`, debita ou repõe estoque, faz `tx.order.update` e insere a linha de auditoria com `tx.orderStatusHistory.create`.

A primeira pergunta da reunião foi se o disparo do webhook aconteceria de forma síncrona dentro desse service ou através de algum mecanismo assíncrono ([09:03] Larissa). Bruno levantou dois problemas concretos com o disparo síncrono ([09:04]):

1. a transação de mudança de status já é pesada — atualiza `orders`, insere em `order_status_history` e decrementa `stock_quantity` dos produtos; acrescentar uma chamada HTTP no meio faria qualquer cliente lento travar a mudança de status de outros pedidos;
2. se o cliente estivesse fora do ar, não haveria resposta razoável — dar rollback na mudança de status por causa de uma notificação não é aceitável.

Havia ainda o requisito de não perder eventos: não pode existir caso em que o status muda no banco e o evento não é emitido ([09:40] Bruno).

## Decisão

Adotar o **padrão Outbox sobre o próprio MySQL da aplicação**.

Quando o status de um pedido muda, **dentro da mesma transação SQL** que atualiza `orders` e `order_status_history`, o sistema insere uma linha numa tabela `webhook_outbox` com o evento a ser entregue ([09:06] Diego). Um processo separado lê essa tabela e executa as chamadas HTTP.

A garantia resultante é transacional: se a transação principal commitou, o evento está registrado; se deu rollback, o evento desaparece junto. Não há janela de inconsistência entre o estado do pedido e a emissão do evento ([09:06] Diego). Falha ao inserir na outbox implica rollback da mudança de status ([09:40] Bruno, [09:41] Diego).

A tabela terá índice no campo de status do evento (pendente, processando, falhou, entregue) e em `created_at`, para que a leitura dos pendentes mais antigos seja eficiente ([09:08] Diego). O identificador da linha é UUID, seguindo o padrão do restante do schema ([09:51] Larissa; ver `prisma/schema.prisma`, onde todo model usa `id String @id @default(uuid()) @db.Char(36)`).

## Alternativas Consideradas

### A. Disparo HTTP síncrono dentro de `order.service.ts` — **descartada**

Chamar o endpoint do cliente diretamente dentro de `changeStatus`.

- Trade-off que motivou o descarte: acopla a latência da operação de negócio à disponibilidade e ao tempo de resposta de terceiros. Um cliente lento degradaria a mudança de status de todos os pedidos, e um cliente fora do ar forçaria a escolha entre perder o evento ou dar rollback numa transação de negócio legítima ([09:04] Bruno). Diego foi categórico: "Síncrono está fora de questão" ([09:06]).

### B. Fila externa — Redis Streams ou equivalente — **descartada**

Publicar o evento em um broker/stream fora do banco e consumir de lá.

- Trade-off que motivou o descarte: exige subir e operar infraestrutura nova. O time é pequeno, e subir um Redis Cluster só para essa finalidade foi classificado como overengineering ([09:07] Diego). Além disso, publicar em um sistema externo reintroduz o problema de dual write: a transação do MySQL e a publicação no broker não são atômicas entre si, que é exatamente o problema que o outbox resolve. O MySQL já existente atende ([09:07] Diego).

### C. Tabela única com flag de "evento pendente" na própria `orders` — não discutida explicitamente

Marcar a order como "notificação pendente" em vez de ter uma tabela de eventos.

- Não sobreviveria ao requisito de histórico: uma mudança `PAID → PROCESSING → SHIPPED` em sequência rápida geraria três eventos distintos que precisam ser entregues individualmente ([09:12] Larissa), e uma flag única na order não os representa.

## Consequências

### Positivas

- Atomicidade real entre mudança de status e emissão do evento, sem dual write e sem janela de perda.
- Nenhuma infraestrutura nova: usa o MySQL já provisionado em `docker-compose.yml` e o mesmo `PrismaClient` já configurado em `src/config/database.ts`.
- A outbox é auditável e inspecionável por SQL comum, o que ajuda no debug de entregas.
- A transação de negócio permanece rápida: o custo acrescentado é um `INSERT` local, não uma chamada de rede.

### Negativas (trade-offs aceitos)

- A transação de `changeStatus` fica marginalmente mais longa e passa a ter mais um ponto de falha: erro no `INSERT` da outbox derruba a mudança de status. Aceito conscientemente — é o preço da garantia de não perder evento ([09:41] Diego).
- A entrega deixa de ser imediata: passa a existir latência entre o commit e o envio, limitada pelo intervalo de polling do worker (ver [ADR-002](ADR-002-worker-processo-separado-polling.md)).
- A tabela cresce indefinidamente se nada arquivar as linhas já entregues. A política de arquivamento (sugerido ~30 dias) foi explicitamente deixada **fora do escopo desta feature** ([09:08] Diego) e permanece como questão em aberto no RFC.
- Usar o banco transacional como fila tem teto de escala menor que um broker dedicado. Aceito para o volume atual; a migração para fila externa continua possível sem mudar o contrato externo.
