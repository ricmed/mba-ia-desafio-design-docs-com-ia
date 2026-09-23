# Architectural Decision Records

Este diretório armazena os ADRs (Architectural Decision Records) do projeto.
Cada decisão arquitetural relevante é registrada aqui em um arquivo individual, nomeado no formato
`ADR-NNN-titulo-em-kebab-case.md`.

Os ADRs seguem o formato MADR, com as seções **Status**, **Contexto**, **Decisão**,
**Alternativas Consideradas** e **Consequências** (positivas e negativas, com o trade-off explícito).

## Índice

| ADR | Título | Status | Origem na transcrição |
|---|---|---|---|
| [ADR-001](ADR-001-outbox-no-mysql.md) | Padrão Outbox no MySQL para publicação de eventos de pedido | Aceito | [09:03]–[09:08] |
| [ADR-002](ADR-002-worker-processo-separado-polling.md) | Worker de entrega em processo separado, com polling de 2 segundos | Aceito | [09:08]–[09:13], [09:30] |
| [ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md) | Retry com backoff exponencial de 5 tentativas e DLQ em tabela separada | Aceito | [09:14]–[09:18], [09:35]–[09:37] |
| [ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md) | HMAC-SHA256 com secret única por endpoint e rotação com grace de 24h | Aceito | [09:19]–[09:23], [09:44] |
| [ADR-005](ADR-005-entrega-at-least-once-com-x-event-id.md) | Entrega at-least-once com deduplicação pelo cliente via `X-Event-Id` | Aceito | [09:24]–[09:26] |
| [ADR-006](ADR-006-reuso-dos-padroes-existentes-do-projeto.md) | Reuso máximo dos padrões existentes do projeto no módulo de webhooks | Aceito | [09:27]–[09:30], [09:36] |
| [ADR-007](ADR-007-payload-snapshot-na-insercao-do-outbox.md) | Payload do evento renderizado como snapshot na inserção do outbox | Aceito | [09:43], [09:51]–[09:52] |

## Escopo destes ADRs

Os sete registros acima cobrem as decisões arquiteturais fechadas na reunião técnica do
**Sistema de Webhooks de Notificação de Pedidos** (`TRANSCRICAO.md`).

Pontos discutidos na reunião que **não** viraram ADR, por decisão explícita dos participantes ou por
não constituírem decisão arquitetural:

- **HTTPS obrigatório na URL do webhook** — Sofia registrou que "nem é decisão arquitetural, é só uma
  validação no schema Zod" ([09:23]). Está no FDD, como contrato e regra de validação.
- **Limite de 64KB de payload** — Larissa classificou como requisito não funcional, não como decisão
  arquitetural separada ([09:24]). Está no PRD e no FDD.
- **Timeout de 10s, formato do payload e headers de envio** — detalhes de implementação decididos
  ([09:42]–[09:44]) e documentados no FDD; o formato do payload aparece no [ADR-007](ADR-007-payload-snapshot-na-insercao-do-outbox.md)
  apenas na medida em que a decisão de snapshot depende dele.

Os pontos deixados **em aberto** na reunião (rate limiting de saída, estratégia de escala do worker,
retenção/arquivamento da outbox e endurecimento de papéis no CRUD) não têm ADR porque não houve
decisão: estão registrados na seção "Questões em aberto" do [RFC](../RFC.md).
