# Tracker de Rastreabilidade — Sistema de Webhooks de Notificação de Pedidos

Este tracker é a referência cruzada do pacote de documentação. Cada item registrado no [PRD](PRD.md), no [RFC](RFC.md), no [FDD](FDD.md) e nos [ADRs](adrs/README.md) tem aqui a sua origem: um trecho da transcrição da reunião (`TRANSCRICAO.md`) ou um arquivo real do código.

**Regra aplicada na produção dos documentos:** item sem origem identificável não entra. Itens que são proposta de desenho e não têm origem na reunião estão marcados nos documentos como **(inferência de desenho)** e aparecem aqui com a base que os motivou.

**Legenda das colunas**

- **Fonte `TRANSCRICAO`** → Localização no formato `[hh:mm] Nome`, correspondendo à fala em `TRANSCRICAO.md`.
- **Fonte `CODIGO`** → Localização é o caminho do arquivo no repositório.

---

## 1. PRD — Requisitos funcionais

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| PRD-FR-01 | docs/PRD.md | Requisito Funcional | Cadastrar endpoint de webhook com URL, cliente e lista de status | TRANSCRICAO | [09:31] Marcos |
| PRD-FR-02 | docs/PRD.md | Requisito Funcional | Plataforma gera a secret e a devolve na criação do endpoint | TRANSCRICAO | [09:31] Marcos |
| PRD-FR-03 | docs/PRD.md | Requisito Funcional | Listar os webhooks de um customer | TRANSCRICAO | [09:33] Bruno |
| PRD-FR-04 | docs/PRD.md | Requisito Funcional | Editar endpoint de webhook (PATCH) | TRANSCRICAO | [09:33] Bruno |
| PRD-FR-05 | docs/PRD.md | Requisito Funcional | Remover endpoint de webhook (DELETE) | TRANSCRICAO | [09:33] Bruno |
| PRD-FR-06 | docs/PRD.md | Requisito Funcional | Filtro de eventos por endpoint: lista de status que quer ouvir | TRANSCRICAO | [09:33] Marcos |
| PRD-FR-06b | docs/PRD.md | Restrição | Filtro aplicado na inserção do outbox, não no envio | TRANSCRICAO | [09:34] Bruno |
| PRD-FR-07 | docs/PRD.md | Requisito Funcional | Rotação de secret pela API com grace period de 24h | TRANSCRICAO | [09:21] Sofia |
| PRD-FR-08 | docs/PRD.md | Requisito Funcional | Histórico de entregas com sucesso/falha, payload, response e tempo | TRANSCRICAO | [09:34] Marcos |
| PRD-FR-09 | docs/PRD.md | Requisito Funcional | Evento registrado na mesma transação da mudança de status | TRANSCRICAO | [09:06] Diego |
| PRD-FR-09b | docs/PRD.md | Restrição | Falha ao inserir o evento causa rollback da mudança de status | TRANSCRICAO | [09:40] Bruno |
| PRD-FR-10 | docs/PRD.md | Requisito Funcional | Envio da notificação assinada com os campos do evento | TRANSCRICAO | [09:43] Diego |
| PRD-FR-11 | docs/PRD.md | Requisito Funcional | Retentativa automática com backoff até o teto de 5 tentativas | TRANSCRICAO | [09:15] Diego |
| PRD-FR-12 | docs/PRD.md | Requisito Funcional | Evento esgotado preservado com motivo da falha (DLQ) | TRANSCRICAO | [09:18] Diego |
| PRD-FR-13 | docs/PRD.md | Requisito Funcional | Replay manual de evento morto por administrador | TRANSCRICAO | [09:35] Diego |
| PRD-FR-14 | docs/PRD.md | Requisito Funcional | Replay registra quem executou, para auditoria | TRANSCRICAO | [09:36] Sofia |
| PRD-FR-15 | docs/PRD.md | Requisito Funcional | Endpoints autenticados com JWT; customer_id não vem do token | TRANSCRICAO | [09:32] Larissa |
| PRD-FR-15b | docs/PRD.md | Restrição | JWT atual é do usuário operador, não do cliente | TRANSCRICAO | [09:32] Bruno |

## 2. PRD — Requisitos não funcionais

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| PRD-RNF-01 | docs/PRD.md | Requisito Não Funcional | Latência de entrega abaixo de 10 segundos | TRANSCRICAO | [09:02] Marcos |
| PRD-RNF-02 | docs/PRD.md | Requisito Não Funcional | Ciclo de polling de 2 segundos; latência mínima aceita | TRANSCRICAO | [09:10] Larissa |
| PRD-RNF-03 | docs/PRD.md | Requisito Não Funcional | Timeout de 10 segundos na chamada ao cliente | TRANSCRICAO | [09:42] Diego |
| PRD-RNF-04 | docs/PRD.md | Requisito Não Funcional | Limite de 64KB de payload, com erro e sem truncamento | TRANSCRICAO | [09:24] Diego |
| PRD-RNF-04b | docs/PRD.md | Trade-off | Preferência explícita por erro em vez de truncar payload grande | TRANSCRICAO | [09:23] Sofia |
| PRD-RNF-05 | docs/PRD.md | Restrição | TLS obrigatório: URL precisa ser https, http é recusado | TRANSCRICAO | [09:23] Sofia |
| PRD-RNF-06 | docs/PRD.md | Requisito Não Funcional | Assinatura HMAC-SHA256 sobre o corpo enviado | TRANSCRICAO | [09:20] Sofia |
| PRD-RNF-07 | docs/PRD.md | Restrição | Uma secret por endpoint, nunca global à plataforma | TRANSCRICAO | [09:21] Sofia |
| PRD-RNF-08 | docs/PRD.md | Requisito Não Funcional | Garantia at-least-once, com dedup do lado do cliente | TRANSCRICAO | [09:26] Larissa |
| PRD-RNF-09 | docs/PRD.md | Restrição | Ordenação garantida por order_id, não globalmente | TRANSCRICAO | [09:12] Diego |
| PRD-RNF-09b | docs/PRD.md | Restrição | Clientes nunca pediram garantia de ordering global | TRANSCRICAO | [09:14] Marcos |
| PRD-RNF-10 | docs/PRD.md | Restrição | Envio roda em processo separado da API | TRANSCRICAO | [09:11] Diego |
| PRD-RNF-11 | docs/PRD.md | Restrição | Nenhuma chamada de rede dentro da transação de mudança de status | TRANSCRICAO | [09:04] Bruno |
| PRD-RNF-12 | docs/PRD.md | Restrição | Nenhuma tecnologia nova de infraestrutura | TRANSCRICAO | [09:07] Diego |
| PRD-RNF-13 | docs/PRD.md | Restrição | Dois dias úteis de revisão de segurança antes do deploy | TRANSCRICAO | [09:46] Sofia |

## 3. PRD — Contexto, objetivos, escopo e riscos

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| PRD-CTX-01 | docs/PRD.md | Contexto | Pedido formal de três clientes B2B: Atlas, MaxDistribuição, Nova Cargo | TRANSCRICAO | [09:00] Marcos |
| PRD-CTX-02 | docs/PRD.md | Contexto | Clientes fazem polling no GET /orders; integração lenta e cara | TRANSCRICAO | [09:00] Marcos |
| PRD-CTX-03 | docs/PRD.md | Risco de negócio | Atlas pode migrar para concorrente se não entregar no trimestre | TRANSCRICAO | [09:00] Marcos |
| PRD-CTX-04 | docs/PRD.md | Restrição | Escopo é outbound apenas: cliente recebe, não envia | TRANSCRICAO | [09:02] Marcos |
| PRD-CTX-05 | docs/PRD.md | Contexto | Aplicação não tem endpoint, tabela ou dependência de notificação externa | CODIGO | src/routes/index.ts |
| PRD-OBJ-01 | docs/PRD.md | Métrica | Latência de notificação < 10 segundos | TRANSCRICAO | [09:02] Marcos |
| PRD-OBJ-02 | docs/PRD.md | Métrica | Atraso máximo do ciclo de leitura de pendentes ≤ 2 segundos | TRANSCRICAO | [09:09] Diego |
| PRD-OBJ-03 | docs/PRD.md | Métrica | Janela de retentativa de 5 tentativas ao longo de ~15 horas | TRANSCRICAO | [09:17] Diego |
| PRD-OBJ-04 | docs/PRD.md | Métrica | Migrar os 3 clientes solicitantes do polling para webhooks | TRANSCRICAO | [09:00] Marcos |
| PRD-OBJ-05 | docs/PRD.md | Métrica | Zero chamadas HTTP dentro da transação de mudança de status | TRANSCRICAO | [09:06] Diego |
| PRD-OBJ-06 | docs/PRD.md | Métrica | Prazo de 3 sprints, com a revisão de segurança incluída | TRANSCRICAO | [09:46] Larissa |
| PRD-OBJ-06b | docs/PRD.md | Restrição | Prazo comercial pedido pela Atlas: fim de novembro | TRANSCRICAO | [09:45] Marcos |
| PRD-OUT-01 | docs/PRD.md | Fora de escopo | E-mail de aviso ao cliente após falhas: adiado para próxima fase | TRANSCRICAO | [09:37] Larissa |
| PRD-OUT-01b | docs/PRD.md | Fora de escopo | Pedido original do e-mail de aviso após 3 falhas seguidas | TRANSCRICAO | [09:37] Marcos |
| PRD-OUT-02 | docs/PRD.md | Fora de escopo | Dashboard visual para o cliente: projeto separado do frontend | TRANSCRICAO | [09:40] Larissa |
| PRD-OUT-02b | docs/PRD.md | Fora de escopo | Pergunta original sobre painel visual para o cliente | TRANSCRICAO | [09:39] Marcos |
| PRD-OUT-03 | docs/PRD.md | Fora de escopo | Webhooks inbound (cliente enviando para a plataforma) | TRANSCRICAO | [09:02] Marcos |
| PRD-OUT-04 | docs/PRD.md | Fora de escopo | Arquivamento das linhas entregues após ~30 dias | TRANSCRICAO | [09:08] Diego |
| PRD-OUT-05 | docs/PRD.md | Fora de escopo | Rate limiting de saída por cliente: observar e decidir depois | TRANSCRICAO | [09:39] Larissa |
| PRD-OUT-06 | docs/PRD.md | Fora de escopo | Ordering global entre pedidos diferentes | TRANSCRICAO | [09:13] Larissa |
| PRD-RSK-01 | docs/PRD.md | Risco | Cliente lento congestiona a fila do worker único | TRANSCRICAO | [09:12] Diego |
| PRD-RSK-02 | docs/PRD.md | Risco | Vazamento de secret de cliente; há precedente real | TRANSCRICAO | [09:22] Diego |
| PRD-RSK-03 | docs/PRD.md | Risco | Crescimento indefinido da outbox sem política de arquivamento | TRANSCRICAO | [09:08] Diego |
| PRD-RSK-04 | docs/PRD.md | Risco | Regressão no fluxo de pedidos: a feature altera o caminho crítico | CODIGO | src/modules/orders/order.service.ts |
| PRD-RSK-05 | docs/PRD.md | Risco | Cliente não implementar dedup e processar evento duplicado | TRANSCRICAO | [09:25] Sofia |
| PRD-RSK-06 | docs/PRD.md | Risco | Atraso na entrega e perda comercial da Atlas | TRANSCRICAO | [09:00] Marcos |
| PRD-TST-01 | docs/PRD.md | Estratégia de teste | Vitest com MySQL real, testes de integração via HTTP | CODIGO | tests/orders.test.ts |
| PRD-TST-02 | docs/PRD.md | Estratégia de teste | Suíte existente precisa continuar passando sem alteração | CODIGO | tests/auth.test.ts |
| PRD-TST-03 | docs/PRD.md | Estratégia de teste | Factories e bootstrap de usuário autenticado reaproveitados | CODIGO | tests/helpers/factories.ts |
| PRD-TST-04 | docs/PRD.md | Validação | Sessão de revisão do design com Bruno e Diego antes de codar | TRANSCRICAO | [09:50] Larissa |
| PRD-TST-05 | docs/PRD.md | Validação | Marcos documenta a integração no portal do desenvolvedor | TRANSCRICAO | [09:40] Marcos |

## 4. RFC — Proposta, alternativas e questões em aberto

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| RFC-PROP-01 | docs/RFC.md | Decisão | Padrão outbox no MySQL, inserção na mesma transação | TRANSCRICAO | [09:06] Diego |
| RFC-PROP-02 | docs/RFC.md | Decisão | Worker separado lendo a outbox em polling de 2 segundos | TRANSCRICAO | [09:09] Diego |
| RFC-PROP-03 | docs/RFC.md | Decisão | Retry com backoff, 5 tentativas, depois DLQ | TRANSCRICAO | [09:17] Larissa |
| RFC-PROP-04 | docs/RFC.md | Decisão | HMAC-SHA256 com secret por endpoint e rotação de 24h | TRANSCRICAO | [09:22] Sofia |
| RFC-PROP-05 | docs/RFC.md | Decisão | Entrega at-least-once com X-Event-Id | TRANSCRICAO | [09:26] Larissa |
| RFC-PROP-06 | docs/RFC.md | Decisão | Módulo em src/modules/webhooks/ (a criar) seguindo o padrão do projeto | TRANSCRICAO | [09:27] Bruno |
| RFC-PROP-07 | docs/RFC.md | Decisão | Integração via publishWebhookEvent(tx, order, from, to) | TRANSCRICAO | [09:41] Bruno |
| RFC-PROP-08 | docs/RFC.md | Restrição | Função pura recebendo o tx, sem injetar repository no service | TRANSCRICAO | [09:41] Diego |
| RFC-ALT-01 | docs/RFC.md | Alternativa descartada | Disparo HTTP síncrono no service de orders — trava mudança de status | TRANSCRICAO | [09:04] Bruno |
| RFC-ALT-01b | docs/RFC.md | Trade-off | Cliente fora do ar exigiria rollback da mudança de status | TRANSCRICAO | [09:04] Bruno |
| RFC-ALT-02 | docs/RFC.md | Alternativa descartada | Redis Streams / fila externa — overengineering para time pequeno | TRANSCRICAO | [09:07] Diego |
| RFC-ALT-02b | docs/RFC.md | Trade-off | Alternativa exigiria subir mais infraestrutura | TRANSCRICAO | [09:07] Larissa |
| RFC-ALT-03 | docs/RFC.md | Alternativa descartada | Trigger de banco — MySQL não tem NOTIFY/LISTEN | TRANSCRICAO | [09:09] Diego |
| RFC-ALT-03b | docs/RFC.md | Trade-off | Proposta original de usar trigger para ser mais reativo | TRANSCRICAO | [09:09] Bruno |
| RFC-ALT-04 | docs/RFC.md | Alternativa descartada | 3 tentativas de retry — janela curta demais (~30 min) | TRANSCRICAO | [09:16] Diego |
| RFC-ALT-04b | docs/RFC.md | Trade-off | Proposta original de política mais agressiva com 3 tentativas | TRANSCRICAO | [09:16] Bruno |
| RFC-ALT-05 | docs/RFC.md | Alternativa descartada | DLQ como flag "failed" na própria outbox | TRANSCRICAO | [09:17] Larissa |
| RFC-ALT-05b | docs/RFC.md | Trade-off | Tabela separada mantém a outbox limpa e serve de evidência | TRANSCRICAO | [09:18] Diego |
| RFC-ALT-06 | docs/RFC.md | Alternativa descartada | Secret global da plataforma — "se vaza uma, vaza tudo" | TRANSCRICAO | [09:21] Sofia |
| RFC-ALT-07 | docs/RFC.md | Alternativa descartada | Garantia exactly-once — exigiria coordenação dos dois lados | TRANSCRICAO | [09:25] Diego |
| RFC-OPEN-01 | docs/RFC.md | Questão em aberto | Rate limiting de saída: observar e implementar se virar problema | TRANSCRICAO | [09:39] Diego |
| RFC-OPEN-01b | docs/RFC.md | Questão em aberto | Cenário: 50 pedidos mudando de status em um minuto | TRANSCRICAO | [09:38] Diego |
| RFC-OPEN-02 | docs/RFC.md | Questão em aberto | Escalar para múltiplos workers preservando ordering | TRANSCRICAO | [09:13] Diego |
| RFC-OPEN-03 | docs/RFC.md | Questão em aberto | Política de retenção/arquivamento das linhas entregues | TRANSCRICAO | [09:08] Diego |
| RFC-OPEN-04 | docs/RFC.md | Questão em aberto | Endurecer papéis no CRUD de configuração mais adiante | TRANSCRICAO | [09:37] Sofia |
| RFC-OPEN-05 | docs/RFC.md | Questão em aberto | Escolha do cliente HTTP: projeto não tem nenhum hoje | CODIGO | package.json |
| RFC-IMP-01 | docs/RFC.md | Impacto | Middleware de erro, logger e validação não sofrem alteração | TRANSCRICAO | [09:29] Bruno |
| RFC-IMP-02 | docs/RFC.md | Impacto | Novo processo a provisionar e monitorar em produção | TRANSCRICAO | [09:11] Larissa |
| RFC-IMP-03 | docs/RFC.md | Impacto | Nenhuma tabela existente é alterada; só criação de tabelas novas | CODIGO | prisma/schema.prisma |
| RFC-RSK-01 | docs/RFC.md | Risco | Deploy condicionado à revisão de segurança da Sofia | TRANSCRICAO | [09:46] Sofia |

## 5. FDD — Modelo de dados, fluxos e contratos

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| FDD-DADOS-01 | docs/FDD.md | Decisão | Tabela de configuração com url, secret, customer_id e estado ativo | TRANSCRICAO | [09:21] Bruno |
| FDD-DADOS-02 | docs/FDD.md | Decisão | Outbox com índice em status e em created_at | TRANSCRICAO | [09:08] Diego |
| FDD-DADOS-03 | docs/FDD.md | Decisão | Estados do evento: pendente, processando, falhou, entregue | TRANSCRICAO | [09:08] Diego |
| FDD-DADOS-04 | docs/FDD.md | Decisão | Id da outbox é UUID, seguindo o padrão do projeto | TRANSCRICAO | [09:51] Larissa |
| FDD-DADOS-05 | docs/FDD.md | Restrição | Convenção uuid @db.Char(36) e @@map snake_case nos models | CODIGO | prisma/schema.prisma |
| FDD-DADOS-06 | docs/FDD.md | Decisão | Tabela webhook_dead_letter com payload, motivo e timestamp | TRANSCRICAO | [09:18] Diego |
| FDD-DADOS-07 | docs/FDD.md | Decisão | Payload persistido como snapshot renderizado na inserção | TRANSCRICAO | [09:52] Larissa |
| FDD-DADOS-08 | docs/FDD.md | Trade-off | Fan-out de uma linha por endpoint destinatário (inferência) | TRANSCRICAO | [09:44] Sofia |
| FDD-FLUXO-01 | docs/FDD.md | Restrição | Inserção do evento dentro da transação de changeStatus | TRANSCRICAO | [09:40] Bruno |
| FDD-FLUXO-02 | docs/FDD.md | Restrição | Ponto de inserção logo após tx.orderStatusHistory.create | CODIGO | src/modules/orders/order.service.ts |
| FDD-FLUXO-03 | docs/FDD.md | Restrição | Worker lê pendentes mais antigos em batch pequeno | TRANSCRICAO | [09:08] Diego |
| FDD-FLUXO-04 | docs/FDD.md | Restrição | Processamento em ordem de created_at do outbox | TRANSCRICAO | [09:12] Diego |
| FDD-FLUXO-05 | docs/FDD.md | Decisão | Worker abre PrismaClient próprio, mesma DATABASE_URL | TRANSCRICAO | [09:30] Bruno |
| FDD-FLUXO-06 | docs/FDD.md | Decisão | Backoff 1m/5m/30m/2h/12h, total de quase 15 horas | TRANSCRICAO | [09:17] Diego |
| FDD-FLUXO-07 | docs/FDD.md | Decisão | Replay recoloca o evento na outbox como pendente | TRANSCRICAO | [09:18] Diego |
| FDD-CONTRATO-01 | docs/FDD.md | Contrato | POST /webhooks — cadastro com url, eventos; secret na resposta | TRANSCRICAO | [09:31] Marcos |
| FDD-CONTRATO-02 | docs/FDD.md | Contrato | GET /webhooks — listar webhooks de um customer | TRANSCRICAO | [09:33] Bruno |
| FDD-CONTRATO-03 | docs/FDD.md | Contrato | PATCH /webhooks/:id — editar endpoint | TRANSCRICAO | [09:33] Bruno |
| FDD-CONTRATO-04 | docs/FDD.md | Contrato | DELETE /webhooks/:id — remover endpoint | TRANSCRICAO | [09:33] Bruno |
| FDD-CONTRATO-05 | docs/FDD.md | Contrato | POST /webhooks/:id/rotate-secret — rotação com grace de 24h | TRANSCRICAO | [09:21] Sofia |
| FDD-CONTRATO-06 | docs/FDD.md | Contrato | GET /webhooks/:id/deliveries — histórico das últimas entregas | TRANSCRICAO | [09:34] Marcos |
| FDD-CONTRATO-07 | docs/FDD.md | Contrato | POST /admin/webhooks/dead-letter/:id/replay — exige ADMIN | TRANSCRICAO | [09:35] Diego |
| FDD-CONTRATO-08 | docs/FDD.md | Restrição | Prefixo /api/v1 em todas as rotas do projeto | CODIGO | src/app.ts |
| FDD-CONTRATO-09 | docs/FDD.md | Restrição | Envelope paginado {data, pagination} nas listagens | CODIGO | src/shared/http/response.ts |
| FDD-CONTRATO-10 | docs/FDD.md | Restrição | DELETE responde 204 sem corpo, como nos módulos existentes | CODIGO | src/modules/orders/order.controller.ts |
| FDD-PAYLOAD-01 | docs/FDD.md | Contrato | Corpo do evento: event_id, event_type, timestamp, order_id, order_number, from/to_status, customer_id, total_cents | TRANSCRICAO | [09:43] Diego |
| FDD-PAYLOAD-02 | docs/FDD.md | Restrição | Payload não inclui os itens do pedido, para não inflar | TRANSCRICAO | [09:43] Diego |
| FDD-PAYLOAD-03 | docs/FDD.md | Trade-off | Cliente que quiser detalhes consulta GET /orders/:id depois | TRANSCRICAO | [09:44] Bruno |
| FDD-HEADER-01 | docs/FDD.md | Contrato | Headers X-Event-Id, X-Signature, X-Timestamp e Content-Type | TRANSCRICAO | [09:44] Diego |
| FDD-HEADER-02 | docs/FDD.md | Contrato | Header X-Webhook-Id com o id do cadastro de webhook | TRANSCRICAO | [09:44] Sofia |
| FDD-HEADER-03 | docs/FDD.md | Trade-off | X-Timestamp permite ao cliente detectar replay attack | TRANSCRICAO | [09:44] Diego |

## 6. FDD — Erros, resiliência, observabilidade e integração

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| FDD-ERR-01 | docs/FDD.md | Restrição | Todos os códigos do módulo usam o prefixo WEBHOOK_ | TRANSCRICAO | [09:29] Larissa |
| FDD-ERR-02 | docs/FDD.md | Decisão | WEBHOOK_NOT_FOUND, WEBHOOK_INVALID_URL, WEBHOOK_SECRET_REQUIRED | TRANSCRICAO | [09:28] Bruno |
| FDD-ERR-03 | docs/FDD.md | Restrição | Classes seguem o padrão de AppError e subclasses existentes | CODIGO | src/shared/errors/http-errors.ts |
| FDD-ERR-04 | docs/FDD.md | Restrição | Envelope de erro {error:{code,message,details}} já implementado | CODIGO | src/middlewares/error.middleware.ts |
| FDD-ERR-05 | docs/FDD.md | Decisão | WEBHOOK_PAYLOAD_TOO_LARGE acima de 64KB, sem truncar | TRANSCRICAO | [09:23] Sofia |
| FDD-ERR-06 | docs/FDD.md | Decisão | WEBHOOK_DELIVERY_TIMEOUT após 10 segundos sem resposta | TRANSCRICAO | [09:42] Diego |
| FDD-ERR-07 | docs/FDD.md | Decisão | WEBHOOK_MAX_RETRIES_EXCEEDED ao esgotar as 5 tentativas | TRANSCRICAO | [09:15] Diego |
| FDD-ERR-08 | docs/FDD.md | Restrição | NotFoundError não aceita código customizado — ponto de atenção | CODIGO | src/shared/errors/http-errors.ts |
| FDD-RES-01 | docs/FDD.md | Decisão | Timeout de 10 segundos por tentativa de entrega | TRANSCRICAO | [09:42] Diego |
| FDD-RES-02 | docs/FDD.md | Decisão | Teto de 5 tentativas antes da DLQ | TRANSCRICAO | [09:15] Diego |
| FDD-RES-03 | docs/FDD.md | Trade-off | Ausência de canal de fallback: e-mail ficou fora de escopo | TRANSCRICAO | [09:37] Larissa |
| FDD-OBS-01 | docs/FDD.md | Restrição | Logger Pino já presente no projeto; nada novo é introduzido | TRANSCRICAO | [09:29] Bruno |
| FDD-OBS-02 | docs/FDD.md | Restrição | Padrão de log estruturado com requestId e duração | CODIGO | src/middlewares/request-logger.middleware.ts |
| FDD-OBS-03 | docs/FDD.md | Decisão | Redaction precisa cobrir secret e assinatura nos logs | TRANSCRICAO | [09:22] Diego |
| FDD-OBS-04 | docs/FDD.md | Restrição | Lista redact atual cobre authorization, password e tokens | CODIGO | src/shared/logger/index.ts |
| FDD-OBS-05 | docs/FDD.md | Decisão | Log de auditoria do replay com o autor da operação | TRANSCRICAO | [09:36] Sofia |
| FDD-OBS-06 | docs/FDD.md | Métrica | Idade do evento pendente mais antigo vigia o acordo de 10s | TRANSCRICAO | [09:02] Marcos |
| FDD-INT-01 | docs/FDD.md | Restrição | Alteração crítica no método changeStatus do service de orders | TRANSCRICAO | [09:40] Bruno |
| FDD-INT-02 | docs/FDD.md | Restrição | Transação atual atualiza order, insere history e mexe em estoque | CODIGO | src/modules/orders/order.service.ts |
| FDD-INT-03 | docs/FDD.md | Restrição | Máquina de estados define as transições válidas do pedido | CODIGO | src/modules/orders/order.status.ts |
| FDD-INT-04 | docs/FDD.md | Restrição | Reuso das classes de erro existentes como base das novas | CODIGO | src/shared/errors/app-error.ts |
| FDD-INT-05 | docs/FDD.md | Restrição | requireRole('ADMIN') reaproveitado no endpoint de replay | TRANSCRICAO | [09:36] Larissa |
| FDD-INT-06 | docs/FDD.md | Restrição | Implementação de requireRole e do papel ADMIN | CODIGO | src/middlewares/auth.middleware.ts |
| FDD-INT-07 | docs/FDD.md | Restrição | Precedente de uso de requireRole('ADMIN') no projeto | CODIGO | src/modules/users/user.routes.ts |
| FDD-INT-08 | docs/FDD.md | Restrição | Registro do módulo em buildControllers e buildApiRouter | CODIGO | src/routes/index.ts |
| FDD-INT-09 | docs/FDD.md | Decisão | Novo entrypoint src/worker.ts (a criar) e script npm run worker | TRANSCRICAO | [09:11] Larissa |
| FDD-INT-10 | docs/FDD.md | Restrição | Padrão de bootstrap e shutdown gracioso a espelhar no worker | CODIGO | src/server.ts |
| FDD-INT-11 | docs/FDD.md | Decisão | Lógica de processamento em webhook.worker.ts dentro do módulo | TRANSCRICAO | [09:28] Bruno |
| FDD-INT-12 | docs/FDD.md | Restrição | Validação de https é schema Zod, não decisão arquitetural | TRANSCRICAO | [09:23] Sofia |
| FDD-INT-13 | docs/FDD.md | Restrição | Padrão de schemas Zod e middleware validate do projeto | CODIGO | src/middlewares/validate.middleware.ts |
| FDD-INT-14 | docs/FDD.md | Restrição | Convenções de schema a seguir nos schemas do módulo | CODIGO | src/modules/orders/order.schemas.ts |
| FDD-INT-15 | docs/FDD.md | Restrição | Novas variáveis de ambiente seguem o padrão fail-fast com Zod | CODIGO | src/config/env.ts |
| FDD-INT-16 | docs/FDD.md | Restrição | createPrismaClient usado pelo worker para instância própria | CODIGO | src/config/database.ts |
| FDD-INT-17 | docs/FDD.md | Restrição | Limpeza FK-safe de tabelas precisa incluir as novas tabelas | CODIGO | tests/setup.ts |
| FDD-INT-18 | docs/FDD.md | Restrição | Migration existente serve de precedente para a nova | CODIGO | prisma/migrations/20260519182739_init/migration.sql |
| FDD-CA-01 | docs/FDD.md | Critério de aceite | Rollback da transação quando a inserção do evento falha | TRANSCRICAO | [09:41] Diego |
| FDD-CA-02 | docs/FDD.md | Critério de aceite | Sem webhook interessado, nenhuma linha é criada na outbox | TRANSCRICAO | [09:34] Bruno |
| FDD-CA-03 | docs/FDD.md | Critério de aceite | Reentrega usa o mesmo X-Event-Id e a mesma payload | TRANSCRICAO | [09:25] Diego |
| FDD-CA-04 | docs/FDD.md | Critério de aceite | Replay com papel não-ADMIN é recusado | TRANSCRICAO | [09:36] Sofia |

## 7. ADRs

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| ADR-001 | docs/adrs/ADR-001-outbox-no-mysql.md | Decisão | Padrão outbox no MySQL, evento inserido na mesma transação | TRANSCRICAO | [09:06] Diego |
| ADR-001b | docs/adrs/ADR-001-outbox-no-mysql.md | Decisão | Confirmação da decisão de outbox em MySQL | TRANSCRICAO | [09:08] Larissa |
| ADR-002 | docs/adrs/ADR-002-worker-processo-separado-polling.md | Decisão | Worker em processo separado, polling de 2 segundos | TRANSCRICAO | [09:11] Diego |
| ADR-002b | docs/adrs/ADR-002-worker-processo-separado-polling.md | Decisão | Registro formal da decisão de polling de 2s e latência aceita | TRANSCRICAO | [09:10] Larissa |
| ADR-003 | docs/adrs/ADR-003-retry-backoff-exponencial-e-dlq.md | Decisão | 5 tentativas com backoff 1m/5m/30m/2h/12h e DLQ separada | TRANSCRICAO | [09:17] Larissa |
| ADR-003b | docs/adrs/ADR-003-retry-backoff-exponencial-e-dlq.md | Trade-off | Justificativa das 5 tentativas: cliente com indisponibilidade de 2h | TRANSCRICAO | [09:16] Diego |
| ADR-004 | docs/adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md | Decisão | HMAC-SHA256, secret por endpoint, rotação com grace de 24h | TRANSCRICAO | [09:22] Sofia |
| ADR-004b | docs/adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md | Decisão | Escolha do algoritmo SHA-256 como padrão de mercado | TRANSCRICAO | [09:20] Sofia |
| ADR-005 | docs/adrs/ADR-005-entrega-at-least-once-com-x-event-id.md | Decisão | At-least-once com X-Event-Id para dedup do lado do cliente | TRANSCRICAO | [09:26] Larissa |
| ADR-005b | docs/adrs/ADR-005-entrega-at-least-once-com-x-event-id.md | Trade-off | Padrão de mercado: Stripe e GitHub adotam o mesmo modelo | TRANSCRICAO | [09:25] Diego |
| ADR-006 | docs/adrs/ADR-006-reuso-dos-padroes-existentes-do-projeto.md | Decisão | Reuso máximo dos padrões do projeto no módulo de webhooks | TRANSCRICAO | [09:30] Larissa |
| ADR-006b | docs/adrs/ADR-006-reuso-dos-padroes-existentes-do-projeto.md | Restrição | Estrutura de módulo controller/service/repository/routes/schemas | CODIGO | src/modules/orders/order.routes.ts |
| ADR-007 | docs/adrs/ADR-007-payload-snapshot-na-insercao-do-outbox.md | Decisão | Payload renderizado e congelado na inserção do outbox | TRANSCRICAO | [09:52] Larissa |
| ADR-007b | docs/adrs/ADR-007-payload-snapshot-na-insercao-do-outbox.md | Decisão | Confirmação do snapshot pelos demais participantes | TRANSCRICAO | [09:52] Diego |

---

## 8. Cobertura e verificação

| Métrica | Valor |
|---|---|
| Total de itens rastreados | **178** |
| Itens com Fonte = `TRANSCRICAO` | **147** (82,6%) |
| Itens com Fonte = `CODIGO` | **31** (17,4%) |
| Arquivos distintos do código referenciados | **26** |
| Documentos cobertos | PRD, RFC, FDD e os 7 ADRs |

> Os números acima foram apurados por script sobre este arquivo, e não estimados: o script
> valida também que **todo** timestamp existe em `TRANSCRICAO.md` com o falante correto, e que
> **todo** caminho na coluna Localização existe no repositório. Ambas as verificações passam sem
> exceção. O procedimento está descrito no [README](../README.md).

### Itens deliberadamente sem origem na transcrição

Os pontos abaixo aparecem nos documentos marcados como **(inferência de desenho)**. Não foram discutidos na reunião e são proposta desta documentação, sujeitos a revisão. Estão listados aqui para que fiquem visíveis em vez de se confundirem com decisões tomadas:

| Item | Documento | Base que o motivou |
|---|---|---|
| Fan-out de uma linha de outbox por endpoint destinatário | docs/FDD.md §4.2 | Decorre de X-Event-Id único por envio ([09:25] Diego) e X-Webhook-Id por cadastro ([09:44] Sofia) |
| Tamanho do batch do worker (20) | docs/FDD.md §5.2 | "batch pequeno" ([09:08] Diego), sem número definido |
| Recuperação de eventos travados em PROCESSING após restart | docs/FDD.md §8 | Consequência operacional do worker único ([09:12] Diego) |
| Lista de métricas de observabilidade | docs/FDD.md §9.2 | Derivada dos limites numéricos fixados na reunião |
| Estratégia de correlação para tracing | docs/FDD.md §9.3 | `requestId` já existente em src/middlewares/request-logger.middleware.ts |
| Nomes e defaults das variáveis de ambiente | docs/FDD.md §10.2 | Valores vêm da reunião; os nomes são proposta |
| Índices compostos e campos auxiliares das tabelas | docs/FDD.md §4 | Índices em status e created_at são da reunião ([09:08] Diego); o resto é desenho |
| `WEBHOOK_ALREADY_REPLAYED` | docs/FDD.md §7.1 | Torna o replay ([09:35] Diego) idempotente |
| Semântica de remoção de endpoint com eventos em trânsito | docs/FDD.md §6.4 | Não discutida; consequência do modelo de dados |
