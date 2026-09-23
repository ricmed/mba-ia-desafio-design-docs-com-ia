# PRD — Sistema de Webhooks de Notificação de Pedidos

| Campo | Valor |
|---|---|
| **Produto** | Order Management System (OMS) |
| **Feature** | Sistema de Webhooks de Notificação de Pedidos |
| **Autor** | Ricardo Medeiros |
| **Status** | Aprovado para implementação |
| **Data** | 2026-09-23 |
| **Stakeholders** | Marcos (Product Manager), Larissa (Tech Lead), Bruno (Eng. Pleno — Pedidos), Diego (Eng. Sênior — Plataforma), Sofia (Eng. Segurança) |
| **Fonte** | `TRANSCRICAO.md` — reunião técnica de ~55 min |
| **Documentos relacionados** | [RFC](RFC.md) · [FDD](FDD.md) · [ADRs](adrs/README.md) · [Tracker](TRACKER.md) |

---

## 1. Resumo e contexto da feature

O OMS passará a **notificar clientes B2B automaticamente sempre que o status de um pedido mudar**, enviando uma requisição HTTP assinada para uma URL que o próprio cliente cadastra.

A notificação é **outbound apenas** — a plataforma envia, o cliente recebe ([09:02] Sofia, [09:02] Marcos). Cada cliente pode cadastrar endpoints, escolher quais status quer ouvir, consultar o histórico do que foi enviado e rotacionar a credencial de assinatura, tudo pela API já existente, autenticado com o JWT do sistema ([09:32] Marcos).

O sistema hoje não tem nenhum mecanismo de notificação externa. A feature preenche esse vazio.

---

## 2. Problema e motivação

Três clientes B2B — **Atlas Comercial, MaxDistribuição e Nova Cargo** — fizeram um pedido formal para serem notificados em tempo real sobre mudanças de status dos pedidos deles ([09:00] Marcos).

Hoje esses clientes não têm alternativa: ficam consultando o `GET /orders` de tempos em tempos para descobrir se algo mudou. O efeito, nas palavras do PM, é que "isso tá deixando a integração lenta e cara pra eles" ([09:00] Marcos).

Há uma consequência comercial concreta e com prazo: **a Atlas indicou que pode migrar para um concorrente** se a entrega não sair até o fim do trimestre ([09:00] Marcos), e o prazo pedido é fim de novembro ([09:45] Marcos).

O parâmetro de "tempo real" foi negociado e é explícito: **qualquer latência abaixo de 10 segundos atende**; o inaceitável é a informação ficar pendurada, obrigando o cliente a atualizar manualmente ([09:02] Marcos).

---

## 3. Público-alvo e cenários de uso

### 3.1 Público-alvo

| Público | Necessidade |
|---|---|
| **Clientes B2B integrados via API** (Atlas Comercial, MaxDistribuição, Nova Cargo) | Saber, sem consultar, quando um pedido deles muda de status ([09:00] Marcos) |
| **Times de desenvolvimento desses clientes** | Integrar uma vez, com credencial própria e capacidade de verificar autenticidade das mensagens ([09:19] Sofia) |
| **Operadores internos do OMS** | Diagnosticar por que uma notificação não chegou |
| **Administradores da plataforma** | Reprocessar entregas que falharam em definitivo ([09:35] Diego) |

### 3.2 Cenários de uso

**C1 — Integração inicial.** O time do cliente cadastra a URL do endpoint dele e escolhe os status que quer ouvir — por exemplo, "só quero saber quando vira `SHIPPED` e `DELIVERED`" ([09:33] Marcos). Recebe a credencial de assinatura na resposta do cadastro ([09:31] Marcos) e passa a receber notificações a partir da próxima mudança de status.

**C2 — Operação normal.** Um pedido da Atlas muda de `PROCESSING` para `SHIPPED`. Em até 10 segundos, o sistema da Atlas recebe a notificação assinada e atualiza a tela do cliente final, sem nenhuma consulta ao `GET /orders`.

**C3 — Cliente temporariamente fora do ar.** O endpoint do cliente entra em manutenção planejada de duas horas — cenário já observado na plataforma ([09:16] Diego). As notificações são retentadas automaticamente ao longo de até ~15 horas e chegam quando ele volta, sem perda e sem intervenção.

**C4 — Investigação de reclamação.** O cliente afirma que não recebeu a notificação de um pedido. O time dele consulta o histórico de entregas e vê sucesso ou falha, o que foi enviado, o que o endpoint respondeu e quanto tempo levou ([09:34] Marcos).

**C5 — Rotação de credencial.** O cliente suspeita que a secret dele vazou — cenário com precedente real na plataforma ([09:22] Diego). Solicita uma nova pela API e tem 24 horas com as duas válidas para migrar os sistemas dele ([09:21] Sofia).

**C6 — Recuperação de falha permanente.** Uma indisponibilidade prolongada esgota as tentativas de um evento. Um administrador identifica o caso e reprocessa manualmente ([09:35] Diego), com registro de quem executou ([09:36] Sofia).

---

## 4. Objetivos e métricas de sucesso

| # | Objetivo | Métrica | Meta | Origem |
|---|---|---|---|---|
| **OBJ-01** | Entregar notificação dentro do que o cliente considera tempo real | Latência entre o commit da mudança de status e a chegada da notificação | **< 10 segundos** | [09:02] Marcos |
| **OBJ-02** | Manter a latência introduzida pela arquitetura previsível | Atraso máximo do ciclo de consulta de eventos pendentes | **≤ 2 segundos** no pior caso | [09:09] Diego, [09:10] Larissa |
| **OBJ-03** | Absorver indisponibilidade dos clientes sem perder evento | Janela de retentativa automática | **5 tentativas ao longo de ~15 horas** (1m/5m/30m/2h/12h) | [09:15] Diego, [09:17] Diego |
| **OBJ-04** | Eliminar o polling no `GET /orders` como forma de acompanhar status | Clientes migrados do polling para webhooks | **Os 3 clientes solicitantes** (Atlas, MaxDistribuição, Nova Cargo) | [09:00] Marcos |
| **OBJ-05** | Não degradar a operação de pedidos | A transação de mudança de status não faz chamada de rede | **Zero** chamadas HTTP dentro da transação | [09:04] Bruno, [09:06] Diego |
| **OBJ-06** | Entregar dentro do prazo comercial | Prazo de implementação | **3 sprints**, incluída a revisão de segurança | [09:46] Larissa |

> **Métricas não definidas na reunião.** Não foi acordada meta numérica de taxa de sucesso de entrega, de volume de eventos por minuto nem de disponibilidade do worker. Esses alvos devem ser estabelecidos após a primeira medição em produção — a mesma lógica que Larissa aplicou ao adiar o e-mail de aviso "depois que a gente medir o impacto" ([09:37]).

---

## 5. Escopo

### 5.1 Incluso

- Cadastro, listagem, edição e remoção de endpoints de webhook por cliente ([09:31], [09:33]).
- Filtro por status: cada endpoint escolhe quais mudanças quer receber ([09:33] Marcos).
- Geração da credencial de assinatura pela plataforma, entregue na criação ([09:31] Marcos).
- Rotação da credencial pelo cliente, com 24 horas de convivência entre a antiga e a nova ([09:21] Sofia).
- Envio automático e assinado da notificação a cada mudança de status ([09:20] Sofia).
- Retentativa automática com espaçamento crescente e desistência após o teto ([09:17] Diego).
- Histórico consultável das entregas ([09:34] Marcos).
- Reprocessamento manual, restrito a administradores, das entregas que falharam em definitivo ([09:35] Diego, [09:36] Sofia).

### 5.2 Fora de escopo

| Item | Situação | Origem |
|---|---|---|
| **Notificação por e-mail ao cliente quando o webhook dele falha** | **Descartado nesta fase.** Marcos pediu; Larissa respondeu "Não. Email tá fora de escopo dessa fase. Talvez próxima fase, depois que a gente medir o impacto" | [09:37] Larissa |
| **Dashboard visual para o cliente acompanhar seus webhooks** | **Descartado.** "Não, agora não. Só endpoints. Painel é projeto separado do time de frontend" | [09:40] Larissa |
| **Webhooks inbound (cliente enviando para a plataforma)** | **Fora de escopo.** "Só saindo da gente pra eles. Eles querem receber, não mandar" | [09:02] Marcos |
| **Arquivamento/expurgo dos eventos já entregues** | **Adiado.** Diego mencionou arquivar após ~30 dias e colocou explicitamente fora do escopo da feature | [09:08] Diego |
| **Rate limiting de saída por cliente** | **Adiado — em observação.** "A gente observa e implementa se virar problema. Mas vale registrar como ponto em aberto" | [09:39] Diego, [09:39] Larissa |
| **Garantia de ordem global entre pedidos diferentes** | **Não será implementado.** A ordem é garantida por pedido; ordering global exigiria escalar com particionamento, tratado como "problema do futuro" | [09:12]–[09:13] Diego |
| **Eventos de outros domínios** (produtos, clientes, criação de pedido) | Apenas mudança de status de pedido foi especificada | [09:43] Diego |

---

## 6. Requisitos funcionais

| ID | Requisito | Origem |
|---|---|---|
| **RF-01** | O cliente deve poder **cadastrar** um endpoint de webhook, informando a URL de destino, o cliente a que pertence e a lista de status que deseja receber | [09:31] Marcos |
| **RF-02** | A plataforma deve **gerar a credencial de assinatura** e devolvê-la ao cliente no momento da criação do endpoint | [09:31] Marcos |
| **RF-03** | O cliente deve poder **listar** os endpoints de webhook de um cliente | [09:33] Bruno |
| **RF-04** | O cliente deve poder **editar** um endpoint já cadastrado | [09:33] Bruno |
| **RF-05** | O cliente deve poder **remover** um endpoint cadastrado | [09:33] Bruno |
| **RF-06** | Cada endpoint deve ter um **filtro de eventos** — a lista de status que quer ouvir; eventos de status fora da lista não são gerados para aquele endpoint | [09:33] Marcos, [09:34] Bruno |
| **RF-07** | O cliente deve poder **rotacionar a credencial** de assinatura pela API, com a credencial antiga permanecendo válida por 24 horas em paralelo | [09:21] Sofia |
| **RF-08** | O cliente deve poder **consultar o histórico de entregas** de um endpoint, vendo sucesso ou falha, o conteúdo enviado, a resposta recebida e o tempo de resposta | [09:34] Marcos |
| **RF-09** | O sistema deve **registrar o evento de notificação na mesma transação** que muda o status do pedido; se o registro falhar, a mudança de status é desfeita | [09:06] Diego, [09:40] Bruno |
| **RF-10** | O sistema deve **enviar a notificação assinada** ao endpoint do cliente, contendo identificador do evento, tipo, timestamp, identificação do pedido, status de origem e destino, identificação do cliente e o valor total | [09:20] Sofia, [09:43] Diego |
| **RF-11** | O sistema deve **retentar automaticamente** as entregas que falharem, com espaçamento crescente, até o teto de 5 tentativas | [09:15], [09:17] Diego |
| **RF-12** | Esgotadas as tentativas, o evento deve ser **preservado com o motivo da falha** para diagnóstico e reprocessamento | [09:18] Diego |
| **RF-13** | Um **administrador** deve poder **reprocessar manualmente** um evento que falhou em definitivo, recolocando-o na fila de entrega | [09:35] Diego |
| **RF-14** | O reprocessamento deve **registrar quem o executou**, para auditoria | [09:36] Sofia |
| **RF-15** | Todos os endpoints de configuração devem exigir **autenticação** com o JWT do sistema; o identificador do cliente **não** é derivado do token | [09:32] Marcos, [09:32] Larissa |

---

## 7. Requisitos não funcionais

| ID | Requisito | Valor | Origem |
|---|---|---|---|
| **RNF-01** | Latência de entrega em operação normal | **< 10 segundos** | [09:02] Marcos |
| **RNF-02** | Atraso máximo do mecanismo de consulta de eventos pendentes | **2 segundos** | [09:09] Diego, [09:10] Larissa |
| **RNF-03** | Tempo limite de resposta do endpoint do cliente | **10 segundos**; acima disso é falha | [09:42] Diego |
| **RNF-04** | Tamanho máximo do conteúdo de uma notificação | **64KB**; acima disso o envio é recusado com erro, **sem truncamento** | [09:23] Sofia, [09:24] Diego, [09:24] Larissa |
| **RNF-05** | Transporte | **TLS obrigatório** — URL cadastrada precisa ser `https`; `http` é recusado na validação | [09:23] Sofia |
| **RNF-06** | Autenticidade e integridade | Assinatura **HMAC-SHA256** sobre o corpo enviado | [09:20] Sofia |
| **RNF-07** | Isolamento de credenciais | **Uma credencial por endpoint**, nunca global à plataforma | [09:21] Sofia |
| **RNF-08** | Garantia de entrega | **At-least-once** — o cliente pode receber o mesmo evento mais de uma vez e é responsável por deduplicar pelo identificador do evento | [09:24]–[09:26] |
| **RNF-09** | Ordenação | Garantida **por pedido**, não globalmente | [09:12] Diego, [09:14] Marcos |
| **RNF-10** | Isolamento operacional | O envio roda em **processo separado** da API | [09:11] Diego |
| **RNF-11** | Impacto na operação de pedidos | **Nenhuma chamada de rede** dentro da transação de mudança de status | [09:04] Bruno |
| **RNF-12** | Consistência com o sistema existente | Nenhuma tecnologia nova de infraestrutura; reuso dos padrões já adotados | [09:07] Diego, [09:30] Larissa |
| **RNF-13** | Segurança pré-deploy | **Dois dias úteis** reservados para revisão de segurança antes da subida | [09:46] Sofia |

---

## 8. Decisões e trade-offs principais

Cada decisão tem registro próprio em [`docs/adrs/`](adrs/README.md). Resumo do que foi decidido e do que se aceitou pagar por isso:

| Decisão | Trade-off aceito | ADR |
|---|---|---|
| Registrar o evento no banco, na mesma transação, e entregar de forma assíncrona | Entrega deixa de ser instantânea; a transação de pedidos ganha mais um ponto de falha | [ADR-001](adrs/ADR-001-outbox-no-mysql.md) |
| Processo separado consultando eventos pendentes a cada 2 segundos | Latência mínima de até 2s e um segundo processo a operar e monitorar | [ADR-002](adrs/ADR-002-worker-processo-separado-polling.md) |
| 5 tentativas espaçadas ao longo de ~15 horas, depois desistência | Cliente que volta do ar pode receber evento bastante antigo; após o teto, o evento só volta por ação manual | [ADR-003](adrs/ADR-003-retry-backoff-exponencial-e-dlq.md) |
| Credencial única por endpoint, rotacionável com 24h de convivência | Duas credenciais válidas durante a janela de rotação; mais estado para gerenciar | [ADR-004](adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md) |
| Entrega at-least-once com identificador de evento | A deduplicação é responsabilidade do cliente — exige documentação clara no portal | [ADR-005](adrs/ADR-005-entrega-at-least-once-com-x-event-id.md) |
| Reuso integral dos padrões do projeto | O módulo herda também as limitações do padrão atual | [ADR-006](adrs/ADR-006-reuso-dos-padroes-existentes-do-projeto.md) |
| Conteúdo da notificação congelado no momento da mudança de status | Duplicação de dados e possibilidade de o cliente receber um retrato "antigo" em retentativas longas | [ADR-007](adrs/ADR-007-payload-snapshot-na-insercao-do-outbox.md) |

Duas decisões de produto merecem destaque por delimitarem o escopo:

- **Enxugar o conteúdo da notificação.** A notificação não leva os itens do pedido; quem precisar de detalhe consulta o pedido depois ([09:43] Diego). Mantém a mensagem pequena e o contrato estável.
- **Só endpoints, nada de interface.** Marcos assumiu documentar a integração no portal do desenvolvedor ([09:40] Marcos), no lugar de uma tela.

---

## 9. Dependências

| Dependência | Natureza | Detalhe |
|---|---|---|
| **Banco de dados MySQL existente** | Interna | O registro dos eventos usa o banco já em produção; nenhuma infraestrutura nova de mensageria ([09:07] Diego) |
| **Módulo de pedidos** | Interna | A emissão do evento depende da alteração no fluxo de mudança de status ([09:40] Bruno) |
| **Autenticação e papéis existentes** | Interna | Os endpoints usam o JWT atual, e o reprocessamento reusa o controle de papel `ADMIN` já implementado ([09:36] Larissa) |
| **Novo processo em produção** | Operacional | É preciso provisionar, monitorar e reiniciar um segundo processo além da API ([09:11] Diego) |
| **Biblioteca de chamada HTTP de saída** | Técnica | O projeto não possui nenhuma hoje; escolha em aberto, registrada no [RFC](RFC.md) §5.5 |
| **Revisão de segurança da Sofia** | Processo | Bloqueante para o deploy; dois dias úteis reservados ([09:46] Sofia) |
| **Documentação no portal do desenvolvedor** | Externa | Marcos assumiu documentar a integração e, com destaque, a possibilidade de entrega duplicada ([09:26], [09:40] Marcos) |
| **Disponibilidade dos endpoints dos clientes** | Externa | Fora do controle da plataforma; tratada por retentativa ([09:17] Diego) |

---

## 10. Riscos e mitigação

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| **R-01** | **Um cliente lento congestiona a fila de todos.** Com um único processo de envio e 10 segundos de tolerância por tentativa, um destinatário ruim atrasa os eventos dos demais | Média | **Alto** — quebra o acordo de 10 segundos para clientes que estão saudáveis | Tempo limite curto e agressivo ([09:42] Diego); monitorar a idade do evento pendente mais antigo; o caminho de escala (particionar por pedido ou lock) está mapeado e pode ser acionado ([09:13] Diego) |
| **R-02** | **Vazamento da credencial de um cliente**, permitindo que um terceiro forje notificações. Há precedente: um cliente já vazou secret em log de aplicação dele | Média | **Alto** — notificações falsas aceitas como legítimas | Credencial por endpoint, não global, limitando o raio ([09:21] Sofia); rotação autoatendida com 24h de convivência; revisão de segurança bloqueante antes do deploy ([09:46] Sofia) |
| **R-03** | **Crescimento indefinido da base de eventos**, já que o arquivamento ficou fora do escopo | Alta | Médio — degradação progressiva da performance de entrega | Índices definidos desde a modelagem ([09:08] Diego); métrica de volume pendente; política de retenção é questão em aberto no [RFC](RFC.md) §5.3 |
| **R-04** | **Regressão no fluxo de pedidos.** A feature altera o caminho crítico de mudança de status, que está em produção | Baixa | **Alto** — afeta a operação central do produto | Alteração mínima e localizada ([09:41] Bruno); critérios de aceite exigem que a suíte de testes existente continue passando e cobrem explicitamente o rollback |
| **R-05** | **Cliente não implementar a deduplicação** e processar o mesmo evento duas vezes | Média | Médio — efeito no negócio do cliente, não no nosso | Identificador único em toda notificação; documentação destacada no portal ([09:26] Marcos) |
| **R-06** | **Atraso na entrega e perda comercial.** A Atlas sinalizou possível migração para concorrente | Baixa | **Alto** — perda de cliente B2B | Escopo deliberadamente enxuto — e-mail, dashboard e rate limiting ficaram fora ([09:37], [09:39], [09:40] Larissa); estimativa de 3 sprints com a revisão de segurança já incluída ([09:47] Larissa) |

---

## 11. Critérios de aceitação

| # | Critério |
|---|---|
| **CA-01** | Um cliente consegue cadastrar um endpoint informando URL, cliente e lista de status, e recebe a credencial de assinatura na resposta |
| **CA-02** | Endpoint cadastrado com URL sem TLS é recusado com erro de validação |
| **CA-03** | Mudança de status de um pedido gera notificação apenas para os endpoints do cliente que pediram aquele status |
| **CA-04** | A notificação chega ao endpoint do cliente em menos de 10 segundos com o sistema em operação normal |
| **CA-05** | A notificação chega assinada e com identificador único de evento, permitindo ao cliente verificar origem e deduplicar |
| **CA-06** | Endpoint fora do ar recebe a notificação após voltar, dentro da janela de retentativas |
| **CA-07** | Evento que esgota as tentativas é preservado com o motivo da falha e não é perdido |
| **CA-08** | Um administrador consegue reprocessar um evento que falhou em definitivo; um usuário não administrador recebe erro de permissão |
| **CA-09** | O reprocessamento fica registrado com a identificação de quem executou |
| **CA-10** | O cliente consegue consultar o histórico de entregas com sucesso/falha, conteúdo, resposta e tempo |
| **CA-11** | Após rotacionar a credencial, a anterior continua válida por exatamente 24 horas |
| **CA-12** | A mudança de status de um pedido **sem** nenhum webhook cadastrado se comporta exatamente como hoje |
| **CA-13** | Nenhuma credencial de cliente aparece em log, em nenhum nível |

Os critérios técnicos correspondentes, com o detalhe de verificação, estão no [FDD](FDD.md) §12.

---

## 12. Estratégia de testes e validação

### 12.1 Abordagem

O projeto usa **Vitest com banco MySQL real** e testes no estilo integração, através de requisições HTTP à aplicação montada (`tests/orders.test.ts`, `tests/auth.test.ts`, com apoio de `tests/helpers/factories.ts`). A feature segue o mesmo caminho, sem introduzir framework novo — coerente com a decisão de reuso ([09:30] Larissa).

### 12.2 Camadas de teste

| Camada | O que cobre |
|---|---|
| **Unitário** | Geração e verificação da assinatura; cálculo dos intervalos de retentativa; validação de URL com TLS; limite de tamanho da notificação; filtro de status |
| **Integração** | Cadastro, listagem, edição, remoção e rotação de credencial; consulta ao histórico; reprocessamento com e sem papel de administrador; emissão do evento na mudança de status; comportamento de rollback |
| **Regressão** | A suíte existente de pedidos e autenticação precisa continuar passando sem alteração — a feature altera o caminho crítico de mudança de status ([09:40] Bruno) |
| **Ponta a ponta** | Um servidor de teste recebendo as notificações valida headers, assinatura, latência abaixo de 10 segundos, retentativa após falha e destino final após esgotar as tentativas |

### 12.3 Validação de cenários críticos

- **Rollback transacional:** forçar falha no registro do evento e verificar que o status do pedido **não** mudou — é o requisito mais forte da feature ([09:40] Bruno, [09:41] Diego).
- **Cliente lento:** servidor de teste que demora mais de 10 segundos, para validar o tempo limite e a contagem de tentativa ([09:42] Diego).
- **Cliente instável:** servidor que falha nas primeiras tentativas e responde com sucesso depois, validando a progressão do espaçamento ([09:17] Diego).
- **Retentativa idêntica:** confirmar que a reentrega carrega o mesmo identificador e o mesmo conteúdo da primeira tentativa ([09:25] Diego, [09:52] Larissa).
- **Sem webhook cadastrado:** garantir que nada muda no comportamento atual do fluxo de pedidos ([09:34] Bruno).

### 12.4 Validação fora do código

- **Revisão de segurança dedicada,** bloqueante para o deploy: dois dias úteis para Sofia revisar a assinatura e a geração de credenciais ([09:46] Sofia).
- **Revisão do design pelo time:** Larissa marcaria uma sessão com Bruno e Diego para revisar o documento antes de começar a codar ([09:50] Larissa) — este PRD, o [RFC](RFC.md) e o [FDD](FDD.md) são o insumo dessa sessão.
- **Validação com o cliente:** Marcos confirma o prazo com a Atlas ([09:47]) e documenta a integração no portal do desenvolvedor ([09:40]).
