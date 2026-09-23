# ADR-004 — Autenticação da entrega por HMAC-SHA256 com secret única por endpoint e rotação com grace period de 24h

- **Status:** Aceito
- **Data da decisão:** reunião técnica "Sistema de Webhooks de Notificação de Pedidos" (quinta-feira, 09:00 — data não registrada na transcrição)
- **Decisores:** Sofia (Eng. Segurança), Bruno (Eng. Pleno, Pedidos), Diego (Eng. Sênior, Plataforma), Larissa (Tech Lead)
- **Origem:** `TRANSCRICAO.md` [09:19]–[09:23], [09:44]
- **Relacionado:** [ADR-005](ADR-005-entrega-at-least-once-com-x-event-id.md), [ADR-006](ADR-006-reuso-dos-padroes-existentes-do-projeto.md)

## Contexto

A feature expõe dados de pedidos para um endpoint HTTP fora da infraestrutura da plataforma. Sofia colocou o problema de segurança nos termos exatos: o cliente precisa conseguir validar que a requisição veio realmente da plataforma e que ninguém adulterou o payload no caminho ([09:19]).

Sem um mecanismo de autenticação da origem, qualquer ator capaz de descobrir a URL do endpoint do cliente poderia forjar notificações de mudança de status — por exemplo, anunciar um pedido como `DELIVERED` sem que isso tenha acontecido.

Um segundo problema apareceu na sequência: a plataforma já teve um caso de cliente que vazou uma secret em log de aplicação do próprio lado dele ([09:22] Diego). Ou seja, comprometimento de credencial não é hipotético — é histórico, e o desenho precisa suportar troca de credencial sem quebrar a integração.

## Decisão

**HMAC-SHA256 sobre o corpo do request, com secret única por endpoint e suporte a rotação com grace period de 24 horas** ([09:22] Sofia).

- **Algoritmo:** HMAC-SHA256. É o padrão de mercado e todo cliente sério tem biblioteca disponível para verificá-lo ([09:20] Sofia).
- **O que é assinado:** o corpo do request enviado ao cliente ([09:20], [09:22] Sofia).
- **Transporte da assinatura:** header `X-Signature` ([09:20] Sofia), acompanhado de `X-Timestamp` com o timestamp do envio, para que o cliente que quiser possa detectar replay attack ([09:44] Diego).
- **Uma secret por endpoint de webhook, não uma secret global da plataforma** ([09:21] Sofia): a configuração de cada webhook armazena url, secret, `customer_id` e estado ativo ([09:21] Bruno). O raciocínio é de contenção de raio de explosão — "se vaza uma, vaza tudo" no modelo global ([09:21] Sofia).
- **Secret gerada pela plataforma** e devolvida ao cliente no momento da criação do webhook ([09:31] Marcos).
- **Rotação sob demanda do cliente, via API**, com a secret antiga permanecendo válida em paralelo por **24 horas** para dar tempo de migrar os sistemas do lado dele; passado esse período, a antiga é invalidada ([09:21] Sofia).
- **TLS obrigatório:** a URL cadastrada precisa ser `https`. Se o cliente cadastrar `http`, a criação é recusada com erro de validação. Sofia registrou explicitamente que isso **não é decisão arquitetural**, e sim uma validação de schema Zod ([09:23]) — está aqui apenas como contexto de segurança, e o detalhe fica no FDD.

## Alternativas Consideradas

### A. Secret global da plataforma, compartilhada por todos os endpoints — **descartada**

Uma única chave de assinatura para toda a saída de webhooks.

- Trade-off que motivou o descarte: o vazamento de uma única credencial comprometeria a assinatura de **todos** os clientes simultaneamente ([09:21] Sofia). O ganho seria apenas operacional (uma chave para gerenciar), e não compensa o raio de explosão — ainda mais com histórico real de vazamento de secret do lado do cliente ([09:22] Diego).

### B. Rotação imediata, sem grace period — **descartada**

Invalidar a secret antiga no instante em que a nova é emitida.

- Trade-off que motivou o descarte: a troca instantânea quebra a integração do cliente entre o momento em que ele pede a nova secret e o momento em que consegue implantá-la nos sistemas dele. O grace period de 24 horas mantém as duas válidas em paralelo e torna a rotação uma operação sem downtime ([09:21] Sofia). O custo é uma janela de 24 horas em que uma secret possivelmente comprometida ainda produz assinatura válida — aceito em troca de tornar a rotação viável na prática.

### C. Autenticação por token estático em header (tipo Bearer) — não discutida explicitamente

Enviar um segredo fixo em header em vez de assinar o corpo.

- Não atende ao requisito colocado: um token estático prova origem, mas **não prova integridade do payload** — não permite detectar adulteração do corpo no caminho ([09:19] Sofia). HMAC cobre os dois.

## Consequências

### Positivas

- O cliente consegue verificar tanto a **origem** quanto a **integridade** do payload recebido, sem precisar de infraestrutura adicional.
- O comprometimento de uma secret afeta um único endpoint, não a base de clientes.
- A rotação é uma operação autoatendida pelo cliente, sem downtime e sem intervenção do time da plataforma.
- Escolha alinhada ao mercado (HMAC-SHA256 em header), o que reduz o atrito de integração para os clientes B2B.

### Negativas (trade-offs aceitos)

- Durante a rotação, **duas secrets ficam válidas por 24 horas** — janela em que uma credencial comprometida ainda produz assinatura aceita. Aceito para viabilizar a migração do cliente ([09:21] Sofia).
- O sistema passa a armazenar material secreto por endpoint, o que cria obrigação de proteção em repouso e de nunca expor a secret em log — o `redact` do logger em `src/shared/logger/index.ts` precisa ser estendido para cobrir os novos campos.
- A verificação é responsabilidade do cliente: a plataforma assina, mas não tem como garantir que o cliente de fato valida a assinatura.
- A rotação acrescenta estado ao modelo de dados do endpoint (secret vigente, secret anterior e o instante de expiração da anterior), aumentando a complexidade do CRUD de configuração.
- Sofia condicionou o deploy a uma revisão de segurança dedicada: **dois dias úteis** reservados para ela revisar HMAC e geração de secret antes de subir ([09:46]).
