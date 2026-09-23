# ADR-007 — Payload do evento renderizado como snapshot na inserção do outbox

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Larissa (Tech Lead), Diego (Eng. Sênior, Plataforma), Bruno (Eng. Pleno, Pedidos)
- **Origem:** `TRANSCRICAO.md` [09:51]–[09:52], [09:43]
- **Relacionado:** [ADR-001](ADR-001-outbox-no-mysql.md), [ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md)

## Contexto

Ao final da reunião, já com o desenho fechado, Bruno levantou a última dúvida de modelagem: a linha da outbox guarda o **payload já renderizado**, ou guarda apenas o `order_id` e o payload é montado na hora do envio? ([09:51])

A pergunta tem consequência real porque as duas coisas acontecem em momentos diferentes. A inserção ocorre dentro da transação de `changeStatus` em `src/modules/orders/order.service.ts`; o envio ocorre no worker, no mínimo 2 segundos depois ([ADR-002](ADR-002-worker-processo-separado-polling.md)) e, em caso de retry, até cerca de 15 horas depois ([ADR-003](ADR-003-retry-backoff-exponencial-e-dlq.md)). Nesse intervalo o pedido pode ter mudado de status de novo — a máquina de estados em `src/modules/orders/order.status.ts` permite sequências rápidas como `PAID → PROCESSING → SHIPPED`, cenário que a própria reunião discutiu ([09:12] Larissa).

O conteúdo do evento já havia sido definido: JSON com `event_id`, `event_type` (`order.status_changed`), timestamp ISO 8601, `order_id`, `order_number`, `from_status`, `to_status`, `customer_id` e campos básicos do pedido como `total_cents`, deliberadamente **sem os itens** para não inflar a mensagem ([09:43] Diego).

## Decisão

**O payload é renderizado no momento da inserção na outbox e persistido como snapshot** ([09:52] Larissa, confirmado por Diego e Bruno).

O evento carrega o estado do pedido **no instante em que a mudança de status aconteceu**, e não o estado do pedido no instante do envio. Se o pedido mudar depois, o evento pendente continua refletindo a transição que o originou ([09:52] Larissa).

Consequências diretas do desenho:

- A linha da outbox contém o corpo JSON completo, pronto para envio.
- O worker não precisa consultar `orders` nem nenhuma outra tabela de domínio para montar a mensagem: ele lê a linha, assina e envia.
- Uma reentrega de retry envia exatamente os mesmos bytes da primeira tentativa, o que torna a assinatura HMAC ([ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md)) estável entre tentativas e coerente com a deduplicação por `X-Event-Id` ([ADR-005](ADR-005-entrega-at-least-once-com-x-event-id.md)).
- A mesma payload é o que fica registrado na DLQ em caso de falha permanente ([09:18] Diego).

## Alternativas Consideradas

### A. Guardar apenas `order_id` e renderizar o payload no momento do envio — **descartada**

A outbox armazenaria uma referência mínima, e o worker buscaria o pedido para montar o corpo.

- Trade-off que motivou o descarte: o evento passaria a descrever o estado **atual** do pedido, não o da transição que o gerou. Larissa apontou o caso esquisito ([09:52]): um evento de `PAID` entregue depois que o pedido já virou `SHIPPED` levaria dados inconsistentes com o próprio `to_status` da mensagem. Com retry de até ~15 horas, essa divergência deixa de ser exceção rara. A alternativa economizaria espaço em disco e permitiria "corrigir" o formato do payload de eventos ainda não enviados, mas ao custo de tornar o conteúdo do evento não determinístico.

### B. Enviar o pedido completo, com itens — **descartada**

Incluir a lista de itens do pedido no payload.

- Trade-off que motivou o descarte: infla a mensagem sem necessidade. Quem precisar de detalhe consulta `GET /orders/:id` depois ([09:43] Diego); Bruno reforçou o ponto de manter o payload enxuto ([09:44]). Um payload enxuto também ajuda a respeitar o teto de 64KB definido como requisito não funcional ([09:24] Diego, [09:24] Larissa).

## Consequências

### Positivas

- O evento é **imutável e autocontido**: o que foi registrado na transação é exatamente o que o cliente recebe, mesmo horas depois.
- O worker fica desacoplado do domínio de pedidos — não lê `orders`, `order_items` nem `customers` no caminho de envio, o que reduz carga de leitura no banco e simplifica o processamento.
- Reentregas são byte a byte idênticas, o que mantém a assinatura HMAC consistente e evita que um cliente veja payloads diferentes sob o mesmo `X-Event-Id`.
- O histórico de entregas e a DLQ guardam evidência fiel do que foi efetivamente enviado, o que torna o debug conclusivo.

### Negativas (trade-offs aceitos)

- **Duplicação de dados:** o mesmo conteúdo passa a existir na tabela de pedidos e na linha da outbox, aumentando o volume armazenado. Agravado pela ausência de política de arquivamento, deixada fora do escopo desta feature ([09:08] Diego).
- **O payload pode chegar "velho":** em retry longo, o cliente recebe um evento que já não descreve o estado atual do pedido. É o comportamento desejado, mas precisa estar documentado no portal de desenvolvedor para não ser lido como bug.
- **Mudança no formato do payload não alcança eventos já enfileirados:** um evento inserido antes de uma alteração de contrato será enviado no formato antigo. Qualquer evolução do payload precisa ser retrocompatível ou considerar a fila em trânsito.
- O custo de renderizar o JSON entra dentro da transação de `changeStatus`, alongando-a marginalmente — coerente com o trade-off já aceito em [ADR-001](ADR-001-outbox-no-mysql.md).
