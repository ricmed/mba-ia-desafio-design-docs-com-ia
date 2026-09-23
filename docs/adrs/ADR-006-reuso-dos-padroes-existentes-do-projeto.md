# ADR-006 — Reuso máximo dos padrões existentes do projeto no módulo de webhooks

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Bruno (Eng. Pleno, Pedidos), Larissa (Tech Lead), Diego (Eng. Sênior, Plataforma)
- **Origem:** `TRANSCRICAO.md` [09:27]–[09:30], [09:36]
- **Relacionado:** [ADR-001](ADR-001-outbox-no-mysql.md), [ADR-002](ADR-002-worker-processo-separado-polling.md), [ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md)

> Este é o ADR que ancora o módulo novo no código existente. Todos os caminhos e identificadores citados abaixo foram verificados no repositório.

## Contexto

O OMS já está em produção e tem convenções estabelecidas e consistentes em todos os módulos. Bruno abriu o bloco de estrutura de código afirmando que existe um padrão claro na codebase e que webhooks deve segui-lo igual ([09:27]).

O que existe hoje, verificado no repositório:

- **Organização por módulo de domínio** em `src/modules/`, cada um com controller, service, repository, routes e schemas — o mesmo quinteto aparece em `src/modules/orders/`, `src/modules/products/`, `src/modules/customers/`, `src/modules/users/`.
- **Hierarquia de erros própria**: `AppError(message, statusCode, errorCode, details?)` em `src/shared/errors/app-error.ts`, e as classes HTTP em `src/shared/errors/http-errors.ts` — `BadRequestError`, `ValidationError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ConflictError`, `UnprocessableEntityError`. O padrão para erro de domínio é estender uma delas fixando o código, como fazem `InvalidStatusTransitionError` (código `INVALID_STATUS_TRANSITION`) e `InsufficientStockError` (código `INSUFFICIENT_STOCK`).
- **Middleware de erro centralizado** em `src/middlewares/error.middleware.ts`, que já trata `AppError`, `ZodError` e os erros conhecidos do Prisma (`P2002`, `P2025`), e serializa tudo no envelope `{ error: { code, message, details? } }`.
- **Logger Pino** instanciado em `src/shared/logger/index.ts`, com campos base `{ service, env }` e lista de `redact` para `authorization`, `*.password`, `*.token` e `*.accessToken`.
- **Validação com Zod** via `validate({ body, query, params })` em `src/middlewares/validate.middleware.ts`.
- **Autorização por papel** com `requireRole(...roles)` em `src/middlewares/auth.middleware.ts` (papéis `ADMIN` e `OPERATOR`), hoje usado em `src/modules/users/user.routes.ts`.
- **Wiring manual de dependências** em `src/app.ts` (`buildControllers`) e registro de rotas em `src/routes/index.ts` (`buildApiRouter`), sob o prefixo `/api/v1`.

A decisão a tomar era se o módulo de webhooks introduziria estruturas próprias — logger, hierarquia de erros, formato de resposta — ou se se encaixaria nas existentes.

## Decisão

**Reuso máximo do que já existe. O módulo de webhooks é mais um módulo igual aos outros, sem introduzir dependência nova de infraestrutura transversal** ([09:30] Larissa).

Concretamente:

| Padrão existente | Como o módulo de webhooks reusa |
|---|---|
| `src/modules/<dominio>/` com controller/service/repository/routes/schemas | Novo `src/modules/webhooks/` com a mesma estrutura ([09:27] Bruno); a lógica de processamento fica em um arquivo do próprio módulo, do tipo `webhook.worker.ts` ou `webhook.processor.ts` ([09:28] Bruno) |
| `AppError` e subclasses em `src/shared/errors/` | Novas classes de erro de webhook estendendo as existentes, no molde de `InvalidStatusTransitionError`, com **todos os códigos prefixados por `WEBHOOK_`** — `WEBHOOK_NOT_FOUND`, `WEBHOOK_INVALID_URL`, `WEBHOOK_SECRET_REQUIRED` etc. ([09:28] Bruno, [09:29] Larissa) |
| `src/middlewares/error.middleware.ts` | **Nenhuma alteração.** Como os erros novos estendem `AppError`, o middleware já os serializa corretamente ([09:29] Bruno) |
| Logger Pino de `src/shared/logger/index.ts` | Usado como está, na API e no worker; nada de biblioteca de log nova ([09:29] Bruno) |
| `validate()` + schemas Zod | Schemas do módulo seguindo o padrão de `src/modules/orders/order.schemas.ts`, incluindo a validação de URL `https` ([09:23] Sofia) |
| `requireRole` de `src/middlewares/auth.middleware.ts` | Reaproveitado para exigir `ADMIN` no replay de DLQ ([09:36] Larissa) |
| `buildControllers` em `src/app.ts` e `buildApiRouter` em `src/routes/index.ts` | Registro do módulo pelo mesmo mecanismo dos demais |
| Convenções de `prisma/schema.prisma` | Novas tabelas com `id String @id @default(uuid()) @db.Char(36)` e `@@map` em snake_case, como os models existentes ([09:51] Larissa) |
| `PrismaClient` | O worker abre **instância própria** — mesmo banco e mesma `DATABASE_URL`, processo diferente ([09:30] Bruno) |

## Alternativas Consideradas

### A. Módulo de webhooks com infraestrutura própria — **descartada**

Hierarquia de erros própria, logger próprio ou formato de resposta próprio para o módulo novo.

- Trade-off que motivou o descarte: quebraria a consistência de um sistema em produção, forçaria alteração no middleware de erro centralizado — que hoje funciona sem saber de domínio nenhum — e produziria duas formas de fazer a mesma coisa na mesma codebase. Bruno foi explícito ao dizer que o logger Pino já está no projeto inteiro e que nada de novo entra ([09:29]).

### B. Extrair os webhooks para um serviço separado — não proposta na reunião

Um serviço autônomo com repositório e deploy próprios.

- Incompatível com a decisão de outbox ([ADR-001](ADR-001-outbox-no-mysql.md)): a garantia transacional depende de a inserção do evento acontecer na **mesma transação** da mudança de status, o que exige compartilhar o banco e o processo de escrita. Também contradiz o argumento de time pequeno que descartou infraestrutura nova ([09:07] Diego).

## Consequências

### Positivas

- Custo de entendimento próximo de zero para quem já trabalha no projeto: o módulo novo é lido como os que já existem.
- O middleware de erro, o logger e o mecanismo de validação **não precisam de alteração alguma** — o que reduz o risco de regressão nos módulos existentes ([09:29] Bruno).
- O prefixo `WEBHOOK_` torna imediatamente identificável, em logs e respostas de erro, que a falha veio do módulo de webhooks.
- A cobertura de testes segue o harness existente: `tests/setup.ts` e `tests/helpers/factories.ts` já dão o padrão de teste de integração com MySQL real.

### Negativas (trade-offs aceitos)

- O módulo herda também as limitações do padrão atual: wiring manual de dependências em `src/app.ts` cresce a cada módulo, e a ausência de envelope padronizado para respostas de recurso individual (só listas usam `paginated()` de `src/shared/http/response.ts`) se propaga para os endpoints novos.
- O prefixo `WEBHOOK_` é uma convenção **nova** — nenhum código de erro existente hoje usa namespace por módulo (`INSUFFICIENT_STOCK`, `INVALID_STATUS_TRANSITION` não têm prefixo). Cria uma inconsistência deliberada com o que já existe, aceita em troca da rastreabilidade do módulo novo.
- O reuso não é total: o projeto **não tem cliente HTTP** em `package.json` — não há axios nem node-fetch —, então o worker precisa introduzir alguma forma de chamada HTTP de saída, e essa é a única dependência realmente nova da feature.
- `src/config/env.ts` precisará crescer com as variáveis do worker, e o `redact` de `src/shared/logger/index.ts` precisará cobrir o campo da secret — duas alterações pequenas em arquivos compartilhados.
