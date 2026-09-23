# ADR-002 — Worker de entrega em processo separado, consumindo a outbox por polling de 2 segundos

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Diego (Eng. Sênior, Plataforma), Larissa (Tech Lead), Bruno (Eng. Pleno, Pedidos)
- **Origem:** `TRANSCRICAO.md` [09:08]–[09:13], [09:30]
- **Relacionado:** [ADR-001](ADR-001-outbox-no-mysql.md), [ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md)

## Contexto

Definido o outbox ([ADR-001](ADR-001-outbox-no-mysql.md)), restava decidir **quem** lê a tabela e **como** o consumidor é acordado quando há evento novo ([09:08] Larissa).

Duas restrições delimitavam o espaço de solução:

- **Latência aceitável:** os clientes B2B definiram "tempo real" como qualquer coisa **abaixo de 10 segundos**; o que não pode acontecer é a notificação ficar pendurada exigindo atualização manual ([09:02] Marcos).
- **O banco é MySQL:** não existe mecanismo nativo de notificação de processo externo equivalente ao `NOTIFY`/`LISTEN` do PostgreSQL ([09:09] Diego).

Havia também a questão de onde o consumidor roda. Hoje `src/server.ts` é o único entrypoint do projeto: faz `bootstrap()`, `buildApp({ prisma })`, `app.listen(env.PORT)` e trata shutdown gracioso em SIGINT/SIGTERM com `prisma.$disconnect()`. Não existe nenhum processo de background no repositório.

## Decisão

O consumidor da outbox será um **worker em processo separado da API**, com laço de **polling a cada 2 segundos**.

- **Processo separado, não um timer dentro da API** ([09:11] Diego): se a API reinicia, o worker não pode ser perdido junto. Concretamente, um novo entrypoint `src/worker.ts`, espelhando o padrão de `src/server.ts`, exposto por um script `npm run worker` ([09:11] Larissa).
- **Mesmo banco, mesma stack, instância própria de Prisma:** o worker usa a mesma `DATABASE_URL`, mas instancia seu próprio `PrismaClient`, porque o client é por processo ([09:11] Bruno, [09:30] Bruno).
- **Polling de 2 segundos:** a cada ciclo, busca os eventos pendentes mais antigos em batch pequeno, processa e marca o resultado ([09:09] Diego). O pior caso de latência introduzido pelo polling é de 2 segundos, aceito explicitamente ([09:10] Larissa) e confortavelmente dentro do teto de 10 segundos do requisito ([09:10] Marcos).
- **Um único worker ativo:** enquanto houver apenas um worker, o processamento segue a ordem de `created_at` da outbox, o que entrega ordering por `order_id` ([09:12] Diego).

## Alternativas Consideradas

### A. Rodar o consumidor dentro do próprio processo da API — **descartada**

Um timer dentro do mesmo processo que serve HTTP.

- Trade-off que motivou o descarte: o ciclo de vida do worker fica amarrado ao da API. Um restart, um deploy ou um crash do servidor HTTP levaria o consumidor junto ([09:11] Diego). Escalar a API horizontalmente também multiplicaria consumidores sem coordenação, quebrando a premissa de worker único.

### B. Trigger de banco para notificar o worker — **descartada**

Bruno perguntou se um trigger no MySQL não tornaria a solução mais reativa que polling ([09:09]).

- Trade-off que motivou o descarte: MySQL não tem listener nativo para processo externo, diferentemente do `NOTIFY`/`LISTEN` do PostgreSQL. Um trigger só executa SQL; para avisar o worker seria necessário improvisar algo como escrever em arquivo ou chamar um endpoint HTTP a partir do banco, o que Diego classificou como esquisito ([09:09]). Como o polling de 2 segundos já atende o requisito de latência com folga, a complexidade extra não se paga.

### C. Múltiplos workers em paralelo desde o início — **descartada para esta fase**

- Trade-off que motivou o descarte: paralelismo quebra a garantia de ordenação. Com um worker, os eventos de um mesmo pedido saem em ordem de `created_at`; com vários, essa garantia se perde ([09:12] Diego). Marcos confirmou que os clientes nunca pediram ordering global — só querem saber quando cada pedido deles muda ([09:14]). As estratégias para escalar mantendo ordem (particionar por `order_id`, lock pessimista) foram reconhecidas e adiadas ([09:13] Diego).

## Consequências

### Positivas

- O ciclo de vida do worker é independente do da API: deploy, restart ou crash de um não derruba o outro.
- Implementação simples, sem broker, sem coordenação distribuída e sem dependência de recurso específico de banco.
- A ordem de entrega por pedido é preservada naturalmente pelo processamento sequencial por `created_at`.
- Reaproveita integralmente a stack existente: mesmo Prisma, mesmo MySQL, mesmo logger Pino.

### Negativas (trade-offs aceitos)

- **Latência mínima de até 2 segundos** mesmo com tudo saudável. Aceito ([09:10] Larissa) — o requisito é "abaixo de 10 segundos".
- **Consulta constante ao banco** mesmo sem eventos pendentes: o polling gera carga de baixa intensidade porém contínua. Mitigado pelos índices em status e `created_at` e pelo batch pequeno ([09:08] Diego).
- **Ponto único de processamento:** com um único worker, se ele cai, nenhum evento é entregue até voltar. Os eventos não se perdem (continuam pendentes na outbox), mas a latência degrada enquanto durar a indisponibilidade.
- **Throughput limitado a um processo:** um cliente lento que consome os 10 segundos de timeout ([09:42] Diego) ocupa o worker e atrasa os eventos seguintes da fila. É a limitação mais relevante deste desenho, registrada como risco no PRD e no FDD.
- **Escalar exige decisão nova:** o caminho para múltiplos workers (partição por `order_id` ou lock pessimista) permanece questão em aberto ([09:13] Diego).
