# ADR-005 — Garantia de entrega at-least-once com deduplicação pelo cliente via X-Event-Id

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Diego (Eng. Sênior, Plataforma), Larissa (Tech Lead), Sofia (Eng. Segurança), Marcos (PM)
- **Origem:** `TRANSCRICAO.md` [09:24]–[09:26], [09:44], [09:51]
- **Relacionado:** [ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md), [ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md)

## Contexto

Com retry automático em cima de chamadas HTTP ([ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md)), a duplicação de entrega deixa de ser hipótese e vira certeza estatística: sempre que a resposta do cliente se perde depois de ele já ter processado o evento — timeout de rede, resposta lenta cortada pelo timeout de 10 segundos, queda logo após o processamento — o worker considera falha e reenvia.

Diego trouxe a questão de forma explícita: a plataforma vai garantir at-least-once, então pode acontecer de o cliente receber o mesmo evento duas vezes, e ele tem que estar preparado para isso ([09:24]).

Bruno fez a pergunta prática que faltava: como o cliente diferencia um evento novo de uma reentrega do mesmo evento? ([09:25])

Sofia levantou a objeção legítima de que essa abordagem joga responsabilidade para o cliente ([09:25]).

## Decisão

**Entrega com garantia at-least-once, com identificador único de evento transportado no header `X-Event-Id`, e deduplicação de responsabilidade do cliente** ([09:26] Larissa).

- Cada evento recebe um **UUID gerado no momento em que entra na outbox** ([09:25] Diego). O identificador é único por evento e estável entre tentativas: uma reentrega carrega o mesmo `X-Event-Id` da primeira tentativa.
- O identificador é enviado no header **`X-Event-Id`** ([09:25] Diego), ao lado de `X-Signature`, `X-Timestamp` e `X-Webhook-Id` ([09:44] Diego, [09:44] Sofia).
- O mesmo identificador também compõe o corpo do evento, no campo `event_id` ([09:43] Diego).
- O uso de UUID como identificador segue o padrão do restante do schema ([09:51] Larissa) — em `prisma/schema.prisma` todo model usa `id String @id @default(uuid()) @db.Char(36)`.
- **O cliente deduplica do lado dele** pelo `event_id` ([09:25] Diego). Isso precisa estar documentado com destaque no portal de desenvolvedor, compromisso assumido por Marcos ([09:26]).

## Alternativas Consideradas

### A. Garantia exactly-once — **descartada**

Assegurar que cada evento chegue exatamente uma vez ao cliente.

- Trade-off que motivou o descarte: exigiria coordenação entre os dois lados — algum protocolo de confirmação com estado compartilhado — o que torna a solução significativamente mais complexa para ambas as partes ([09:25] Diego). Com um canal HTTP unidirecional sobre a internet pública, a ausência de resposta é indistinguível de falha de processamento, e não há como decidir com segurança entre reenviar e não reenviar. At-least-once com identificador de evento resolve a esmagadora maioria dos casos ([09:25] Diego).

### B. At-most-once (sem retry) — não proposta formalmente, incompatível com o escopo

Enviar uma vez e desistir.

- Eliminaria a duplicação, mas violaria o requisito de resiliência: um cliente momentaneamente fora do ar perderia o evento em definitivo. A reunião foi na direção oposta, decidindo cinco tentativas ao longo de ~15 horas ([09:17] Diego).

### C. Deduplicação do lado da plataforma, antes do envio — não discutida explicitamente

Manter estado de "já entregue" por evento para impedir reenvio.

- Não resolve o problema real: a duplicação nasce justamente do caso em que a plataforma **não sabe** se a entrega foi concluída (timeout, resposta perdida). Qualquer estado local seria inconclusivo exatamente na situação que causa a duplicata.

## Consequências

### Positivas

- Nenhum evento é perdido por falha transitória de rede ou indisponibilidade curta do cliente.
- O desenho fica simples dos dois lados: nenhum protocolo de confirmação, nenhuma máquina de estado distribuída.
- Alinhamento com o padrão de mercado — Stripe e GitHub adotam o mesmo modelo ([09:25] Diego) —, o que reduz atrito de integração porque os clientes provavelmente já implementaram deduplicação por id de evento para outros provedores.
- O `X-Event-Id` serve também como chave de correlação em logs e tracing, ligando a linha da outbox, a tentativa de entrega e o registro do lado do cliente.

### Negativas (trade-offs aceitos)

- **A responsabilidade da deduplicação é do cliente** ([09:25] Sofia). Um cliente que não implemente a verificação pode processar o mesmo evento mais de uma vez — com efeito colateral no negócio dele, não no nosso.
- Cria uma obrigação de documentação: o comportamento precisa estar destacado no portal de desenvolvedor ([09:26] Marcos). Se essa documentação falhar, o problema aparece como incidente de integração.
- O contrato público passa a ter uma garantia mais fraca do que "entregue exatamente uma vez", o que precisa ser comunicado com clareza na negociação com clientes B2B.
- Combinado com o retry longo ([ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md)), um cliente pode receber a duplicata de um evento **horas** depois da primeira tentativa, e não segundos — a janela de deduplicação do lado dele precisa cobrir isso.
