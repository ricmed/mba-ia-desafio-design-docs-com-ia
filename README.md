# Da Reunião ao Documento — Design Docs Gerados por IA

Pacote de documentação técnica do **Sistema de Webhooks de Notificação de Pedidos**, produzido a partir da transcrição de uma reunião técnica e do código de um Order Management System em produção.

> O enunciado original do desafio está preservado, sem alterações, em [`docs/ENUNCIADO.md`](docs/ENUNCIADO.md).
> Repositório base: [devfullcycle/mba-ia-desafio-design-docs-com-ia](https://github.com/devfullcycle/mba-ia-desafio-design-docs-com-ia).

---

## 1. Sobre o desafio

O ponto de partida são dois artefatos e nenhum documento: um OMS funcional em Node.js + TypeScript, com máquina de estados de pedido, controle transacional de estoque e auditoria de mudanças de status — e a transcrição literal de uma call de ~55 minutos (`TRANSCRICAO.md`) em que cinco pessoas decidem como construir uma feature de webhooks de notificação. A decisão técnica foi tomada ali, mas não sobrou registro nenhum além da gravação. A tarefa é transformar essa conversa em um pacote de design docs acionável o suficiente para o time começar a codar: PRD, RFC, FDD, ADRs, um tracker de rastreabilidade e este README.

O que torna o desafio interessante não é escrever os documentos — é **filtrar**. A transcrição mistura decisão fechada, ideia descartada, tema adiado, detalhe secundário e pergunta sem resposta, tudo no mesmo fluxo de conversa. Quatro coisas foram explicitamente excluídas do escopo (e-mail de aviso, dashboard, webhooks inbound, arquivamento da outbox) e outras seis foram propostas e descartadas com argumento (disparo síncrono, Redis Streams, trigger de banco, 3 tentativas de retry, DLQ como flag, secret global). Colocar qualquer uma dessas como requisito é erro grave, e é exatamente o tipo de coisa que uma IA sem freio faz ao "resumir uma reunião". A regra que organizou o trabalho inteiro foi simples: **todo item documentado precisa apontar para um timestamp da transcrição ou para um arquivo real do código** — e essa regra não ficou no nível da boa intenção, virou script executável.

---

## 2. Ferramentas de IA utilizadas

| Ferramenta | Papel no trabalho |
|---|---|
| **Claude Opus 5, via Claude Code** | Ferramenta principal. Leitura da transcrição e do código, extração e classificação das decisões, redação de todos os documentos e execução das verificações. |
| **Subagente `Explore` (Claude Code)** | Varredura inicial do repositório em paralelo à leitura da transcrição: mapear módulos, padrões de erro, middlewares, schema Prisma, testes e dependências, devolvendo caminhos e identificadores reais. |
| **Modo de planejamento (Claude Code)** | Antes de escrever qualquer documento, produzir o inventário de decisões com timestamp e a fronteira entre PRD / RFC / FDD / ADR, submetido a aprovação antes da execução. |
| **Scripts Python gerados pela IA** | Verificação mecânica do resultado — [`docs/verificar-rastreabilidade.py`](docs/verificar-rastreabilidade.py) confere timestamps, caminhos, links e cobertura do tracker. |

Nenhuma ferramenta adicional de IA foi usada. A escolha por uma só ferramenta com acesso direto ao repositório foi deliberada: o gargalo deste desafio é precisão factual sobre o código, e colar trechos em um chat sem acesso ao filesystem multiplica a chance de inventar um caminho de arquivo ou um nome de classe.

---

## 3. Workflow adotado

A ordem de produção seguiu a lógica de que **decisão vem antes de proposta, e proposta vem antes de detalhe**:

```
Exploração  →  Inventário  →  ADRs  →  RFC  →  FDD  →  PRD  →  Tracker  →  Verificação  →  README
```

| Etapa | O que foi feito | Por que nesta ordem |
|---|---|---|
| **1. Exploração** | Leitura integral da transcrição, em paralelo a uma varredura do repositório feita por subagente. Depois, leitura direta dos arquivos críticos (`order.service.ts`, `http-errors.ts`) para conferir o relatório. | Sem conhecer `changeStatus` e a hierarquia de erros, qualquer documento sai genérico. |
| **2. Inventário** | Construção de uma tabela única com toda decisão, exclusão e questão em aberto, cada uma com timestamp e falante — separando **fechado**, **descartado**, **adiado** e **em aberto**. | É o antídoto contra alucinação: os documentos são escritos a partir do inventário, não da transcrição crua. |
| **3. ADRs** | Sete ADRs em formato MADR. | As decisões são o esqueleto; escrever primeiro impede que RFC e FDD divirjam entre si. |
| **4. RFC** | Proposta em nível de arquitetura, com alternativas descartadas e questões em aberto, linkando os ADRs. | Com as decisões prontas, o RFC vira consolidação, não invenção. |
| **5. FDD** | Modelo de dados, fluxos, contratos, matriz de erros, observabilidade e a seção de integração com o código. | Documento mais profundo; depende de tudo o que veio antes. |
| **6. PRD** | Produto e negócio, escrito por último entre os grandes. | Com RFC e FDD em mãos, o PRD é consolidação de alto nível. |
| **7. Tracker** | Varredura dos documentos prontos, item a item. | Feito no fim, funciona como auditoria de tudo o que foi escrito. |
| **8. Verificação** | Script conferindo timestamps, caminhos, links e cobertura. | Transforma a regra de rastreabilidade em teste executável. |
| **9. README** | Escrito por último, com as iterações reais já registradas. | Só dá para documentar o processo depois de vivê-lo. |

### Como a interação com a IA foi organizada

Três princípios sustentaram o trabalho:

1. **Contexto antes de geração.** Nenhum documento foi pedido antes de a IA ter lido o código e a transcrição por inteiro. Prompt sem contexto produz documento genérico — e documento genérico não é corrigível, é descartável.
2. **Fronteira explícita entre documentos.** Antes de escrever, ficou definido o que cada documento pode conter: o RFC não leva payload de exemplo nem matriz de erro; o PRD não leva SQL nem header HTTP; o FDD é o único lugar com detalhe de implementação. Sem essa regra, a IA repete o mesmo conteúdo nos três, que é o modo de falha mais comum deste tipo de pacote.
3. **Verificação mecânica em vez de releitura.** Revisar 20 mil palavras à mão procurando um timestamp errado não funciona. O que funciona é extrair todas as marcações e conferir contra a fonte — foi assim que os erros reais apareceram.

---

## 4. Prompts customizados

### 4.1 Mapeamento do código com exigência de literalidade

Prompt do subagente de exploração. O detalhe que importa é a instrução repetida de **citar nomes e caminhos reais e priorizar acurácia sobre completude** — sem isso, o relatório vem plausível e errado, com nomes de método verossímeis que não existem.

```text
Explore a codebase Node.js + TypeScript deste OMS (ignore node_modules, .git).
Preciso de um mapa factual e preciso para escrever design docs sobre a adição de
um módulo de webhooks. Seja minucioso e reporte com CAMINHOS DE ARQUIVO REAIS e
NOMES DE IDENTIFICADOR REAIS — não adivinhe.

Reporte sobre:
1. src/modules/orders/ — order.service.ts (especialmente changeStatus / transição
   de status, uso de $transaction, controle de estoque), order.status.ts (máquina
   de estados), repository, controller, routes, schemas. Cite as assinaturas dos
   métodos e como as transações são usadas.
2. src/shared/errors/ — nomes das classes, assinaturas dos construtores,
   convenção dos códigos de erro.
3. src/shared/http/response.ts e src/shared/logger/index.ts — formato do envelope
   de resposta, biblioteca e API do logger.
4. src/middlewares/ — auth (JWT? papéis?), validate (zod?), error, request-logger.
5. prisma/schema.prisma — todos os models, enums, campos notáveis, índices.
6. src/config/env.ts e .env.example — nomes das variáveis e forma de validação.
7. package.json + app.ts + server.ts + routes/index.ts — scripts, dependências
   com versões, e como módulos e rotas são registrados.
8. tests/ — framework e padrões.

Devolva um documento organizado com caminhos exatos, nomes exatos e trechos
VERBATIM curtos das partes mais importantes (máquina de estados, changeStatus,
classes de erro, models de Order e de auditoria).
PRIORIZE ACURÁCIA SOBRE COMPLETUDE.
```

### 4.2 Extração e classificação do que a reunião decidiu — e do que ela recusou

Este é o prompt central do desafio. Ele não pede "resuma a reunião": pede uma **classificação em quatro baldes**, exige timestamp em cada linha e proíbe explicitamente a inferência silenciosa.

```text
Leia TRANSCRICAO.md por inteiro. NÃO resuma. Produza um inventário classificando
CADA item em exatamente um destes quatro baldes, com [hh:mm] e nome do falante
em todas as linhas:

A) DECIDIDO — a reunião fechou. Inclua o valor exato acordado (número, algoritmo,
   nome de header, caminho de endpoint).
B) DESCARTADO — foi proposto e recusado. Registre QUEM propôs, QUEM recusou e o
   ARGUMENTO que motivou a recusa. Um item descartado sem o trade-off registrado
   está incompleto.
C) ADIADO / FORA DE ESCOPO — reconhecido como válido, mas explicitamente deixado
   para outra fase. Cite a frase que o coloca fora.
D) EM ABERTO — levantado e não resolvido. Não invente a resolução.

Regras:
- Se algo não tem timestamp identificável, NÃO entra no inventário.
- Não promova um item de C ou D para A. Se a reunião disse "a gente observa",
  isso é D, não é requisito.
- Distinga o que foi chamado de decisão arquitetural do que os próprios
  participantes classificaram como detalhe de implementação ou requisito não
  funcional — eles fazem essa distinção em voz alta mais de uma vez.
- Ao final, liste separadamente as decisões que dependem de um arquivo ou padrão
  do código existente, indicando o caminho.
```

### 4.3 Auditoria adversarial do que foi gerado

Usado depois de os documentos prontos. A instrução é para **procurar erro**, não para confirmar qualidade — pedir "revise" produz elogio; pedir "encontre o que está errado, com critério mecânico" produz achado.

```text
Aja como revisor cético do pacote em docs/. Não elogie e não resuma: procure
defeito. Para cada item abaixo, produza evidência executável, não opinião.

1. Extraia TODA marcação [hh:mm] Nome dos documentos e confira contra
   TRANSCRICAO.md. Aponte toda marcação em que aquele falante não fala naquele
   minuto.
2. Extraia TODO caminho src/, prisma/ ou tests/ citado e verifique existência no
   repositório. Distinga "não existe" de "é artefato que a feature vai criar".
3. Procure os itens que a reunião DESCARTOU (e-mail, dashboard, inbound, Redis,
   trigger, 3 tentativas) aparecendo como requisito ou capacidade em qualquer
   documento.
4. Verifique se o RFC duplica detalhe que pertence ao FDD (payload de exemplo,
   matriz de erro, schema de tabela).
5. Confira os números que os documentos afirmam sobre si mesmos (cobertura do
   tracker, quantidade de itens). Conte de fato; não aceite o que está escrito.
6. Cheque se todo link relativo entre documentos resolve.
```

---

## 5. Iterações e ajustes

Foram **cinco ciclos principais** de geração, crítica e correção. Os achados abaixo são reais — vieram das verificações descritas acima, e cada um resultou em alteração no pacote.

### Iteração 1 — O relatório do subagente estava certo no geral e errado no detalhe que importava

A varredura inicial do código veio bem estruturada, e teria sido cômodo escrever o FDD em cima dela. Ao reler `src/shared/errors/http-errors.ts` diretamente, apareceu um detalhe que o resumo não destacava: **`NotFoundError` tem a assinatura `constructor(resource = 'Resource')` e fixa o código `NOT_FOUND`** — diferente de `ConflictError` e `UnprocessableEntityError`, que aceitam um parâmetro `code`.

Isso é decisivo, porque a reunião determinou o prefixo `WEBHOOK_` em **todos** os códigos do módulo ([09:29] Larissa). Um `WebhookNotFoundError extends NotFoundError` simplesmente não consegue emitir `WEBHOOK_NOT_FOUND` sem alterar a classe base. O FDD ganhou um ponto de atenção explícito na seção de integração, avisando o implementador de que a hierarquia atual não acomoda esse caso sem uma escolha consciente. Um documento gerado sem essa conferência teria mandado o time por um caminho que não compila.

**Lição aplicada:** relatório de subagente é ponto de partida, não fonte. Os arquivos que sustentam decisões de desenho foram lidos na íntegra, diretamente.

### Iteração 2 — O tracker afirmava números sobre si mesmo que eram chute

A primeira versão do `TRACKER.md` fechava com uma tabela de cobertura: **123 itens, 97 com origem na transcrição (78,9%), 26 no código**. Números redondos, plausíveis, escritos com confiança — e inventados. Eu os escrevi estimando, não contando.

Ao rodar a contagem de verdade: **178 itens, 147 na transcrição (82,6%), 31 no código, 26 arquivos distintos**. O erro era de 45 itens, quase 30% do total. Nenhuma das linhas do tracker estava errada; a *afirmação sobre elas* estava.

É o modo de falha mais traiçoeiro deste tipo de trabalho, porque o número errado estava justamente no documento cuja função é garantir precisão. A correção foi dupla: ajustar os valores e **transformar a conferência em script** — [`docs/verificar-rastreabilidade.py`](docs/verificar-rastreabilidade.py), que passou a rodar a cada rodada de alteração.

**Lição aplicada:** número que um documento afirma sobre si mesmo é código, não prosa. Tem que ser executado.

### Iteração 3 — Uma notação ambígua virou atribuição falsa

O verificador de timestamps acusou `[09:24] Sofia` no FDD. Fui à transcrição: às 09:24 falam **Diego** ("Acho que 64KB já é um teto generoso") e **Larissa** ("64KB de limite, erro caso ultrapasse"). Sofia não fala nesse minuto — a fala dela sobre limite de tamanho é às 09:23.

A origem era uma notação que eu tinha escrito como `[09:23]–[09:24] Sofia e Diego`. O conteúdo estava correto (Sofia às 09:23, Diego às 09:24), mas a forma permite ler "Sofia às 09:24", que é falso. Em um documento cujo valor inteiro está na rastreabilidade, uma citação que pode ser lida errado **é** um erro.

Toda a notação do pacote foi normalizada para **um falante por marcação**: `[09:23] Sofia, [09:24] Diego`. A varredura alcançou os quatro documentos principais e cinco dos sete ADRs. Hoje as **583 marcações** do pacote passam na verificação sem uma exceção sequer — e o script falha se alguma deixar de passar.

### Iteração 4 — Arquivos que a feature vai criar pareciam arquivos existentes

A verificação de caminhos acusou `src/worker.ts` e `src/modules/webhooks/` como inexistentes — corretamente, já que são justamente o que a feature cria. Mas os documentos citavam esses caminhos com a mesma naturalidade com que citavam `src/modules/orders/order.service.ts`, que existe. Um leitor — ou um avaliador rodando uma checagem automática — não tem como distinguir "arquivo que estou propondo" de "arquivo que eu inventei".

Os dois passaram a aparecer sempre marcados como **(a criar)**, e tanto o RFC quanto o FDD ganharam uma frase declarando explicitamente que são as **únicas** duas exceções do pacote. O script trata os dois como exceção conhecida e falharia se um terceiro caminho fantasma aparecesse.

### Iteração 5 — Um endpoint da transcrição não batia com a montagem real das rotas

A reunião definiu o endpoint de replay como `POST /admin/webhooks/dead-letter/:id/replay` ([09:35] Diego). Transcrito literalmente, ficaria errado: `src/app.ts` monta toda a API sob `app.use('/api/v1', buildApiRouter(controllers))`, e nenhum mount `/admin` existe hoje no projeto.

A correção não foi escolher um dos dois. Foi documentar o caminho completo — `/api/v1/admin/webhooks/dead-letter/:id/replay` — e registrar no tracker **duas linhas de origem distintas**: o endpoint vem da transcrição ([09:35] Diego), o prefixo vem do código (`src/app.ts`). O FDD ainda registra que o mount `/admin` é criado por esta feature.

Esse padrão se repetiu em outros pontos e virou método: quando transcrição e código se encontram, a rastreabilidade se divide em vez de escolher um lado.

### Achados menores

- **Link interno quebrado:** `ADR-001` apontava para `ADR-007-payload-snapshot-na-insercao.md`, mas o arquivo foi salvo como `ADR-007-payload-snapshot-na-insercao-do-outbox.md`. O verificador de links pegou; hoje os 89 links relativos do pacote resolvem.
- **Inferências separadas de decisões:** nove pontos do FDD são proposta de desenho sem origem na reunião — o fan-out de uma linha de outbox por endpoint, o tamanho do batch, a lista de métricas, entre outros. Em vez de apagá-los (empobreceria o documento) ou deixá-los passar por decisão (seria alucinação), todos foram marcados **(inferência de desenho)** no texto e listados em uma seção própria do tracker.
- **Duplicação entre RFC e FDD:** a primeira versão do RFC trazia a tabela de backoff e exemplos de header. Ambos foram removidos do RFC e mantidos só no FDD, respeitando a altura de cada documento.

---

## 6. Como navegar a entrega

```
.
├── README.md                    ← este arquivo (processo de produção)
├── TRANSCRICAO.md               ← fonte primária, não alterada
└── docs/
    ├── PRD.md                   ← por que e o quê (produto)
    ├── RFC.md                   ← como pretendemos resolver (arquitetura)
    ├── FDD.md                   ← como construir (implementação)
    ├── TRACKER.md               ← de onde veio cada coisa
    ├── ENUNCIADO.md             ← enunciado original do desafio
    ├── verificar-rastreabilidade.py
    └── adrs/
        ├── README.md            ← índice dos ADRs
        ├── ADR-001-outbox-no-mysql.md
        ├── ADR-002-worker-processo-separado-polling.md
        ├── ADR-003-retry-backoff-exponencial-e-dlq.md
        ├── ADR-004-hmac-sha256-com-secret-por-endpoint.md
        ├── ADR-005-entrega-at-least-once-com-x-event-id.md
        ├── ADR-006-reuso-dos-padroes-existentes-do-projeto.md
        └── ADR-007-payload-snapshot-na-insercao-do-outbox.md
```

### Ordem de leitura sugerida

| # | Documento | O que você leva dele |
|---|---|---|
| 1 | [`docs/PRD.md`](docs/PRD.md) | O problema, quem pediu, o que entra, o que ficou de fora e as métricas de sucesso. |
| 2 | [`docs/RFC.md`](docs/RFC.md) | A solução em nível de arquitetura, as alternativas recusadas com o motivo e o que segue em aberto. |
| 3 | [`docs/adrs/`](docs/adrs/README.md) | Cada decisão isolada, com contexto, alternativas e consequências. Comece pelo índice. |
| 4 | [`docs/FDD.md`](docs/FDD.md) | O detalhe de implementação: modelo de dados, fluxos, contratos, erros e — principalmente — a §11, que amarra a feature aos arquivos reais do projeto. |
| 5 | [`docs/TRACKER.md`](docs/TRACKER.md) | A auditoria: 178 itens ligados à sua origem. Use para conferir qualquer afirmação dos outros documentos. |

**Se você tem cinco minutos:** leia o TL;DR do [RFC](docs/RFC.md) e a §11 do [FDD](docs/FDD.md) — juntos, dão a solução e o ponto exato do código onde ela encosta.

**Se você vai implementar:** [FDD](docs/FDD.md) §5 (fluxos), §6 (contratos) e §11 (integração), com os [ADRs](docs/adrs/README.md) ao lado para entender o porquê de cada restrição.

**Se você vai avaliar a integridade do pacote:**

```bash
python docs/verificar-rastreabilidade.py
```

O script confere as 583 marcações de timestamp contra `TRANSCRICAO.md`, a existência dos 32 caminhos de código citados, os 89 links entre documentos e os limiares de cobertura do tracker.

---

## 7. Nota sobre o código da aplicação

A entrega é **puramente documental**. Nenhum arquivo em `src/`, `prisma/`, `tests/` ou de configuração foi alterado — o código serve exclusivamente como contexto e referência, e é citado nos documentos por caminho real.

Fora de `docs/`, o único arquivo tocado é este `README.md`, substituído conforme o requisito 6 do enunciado, cujo conteúdo original está preservado em [`docs/ENUNCIADO.md`](docs/ENUNCIADO.md). `TRANSCRICAO.md` permanece intacto.

```bash
git diff --stat main --name-only
```

confirma que a alteração se limita a `README.md` e a `docs/`.
