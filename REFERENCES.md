# Referências

Este documento expõe a base de engenharia de software por trás de cada etapa do pipeline Leanwork SDD: de onde vem cada conceito, quem o publicou primeiro, e o que aqui é adaptação, reprodução ou contribuição própria.

O plugin foi escrito na voz de praticante — os arquivos de skill quase nunca citam autor ou livro. Isso é bom para quem executa e ruim para quem quer estudar, auditar ou discordar. Este arquivo corrige a segunda parte sem inchar a primeira.

## Como ler este documento

Cada item recebe uma marca:

| Marca | Significado |
|---|---|
| **Reprodução** | O repositório usa a definição canônica, ou copia vocabulário/estrutura da fonte. Crédito obrigatório. |
| **Adaptação** | O conceito é reconhecível, mas o recorte, os limiares ou a aplicação são próprios. O desvio está declarado. |
| **Autoral** | Não identificamos antecedente publicado. Reivindicado como contribuição do pipeline. |

Duas seções ao final merecem leitura antes das demais: [Divergências deliberadas](#divergências-deliberadas-com-a-literatura), onde o pipeline se afasta do cânone de propósito, e [Lacunas conhecidas](#lacunas-conhecidas), onde ele simplesmente ainda não chegou.

---

## Fundamentos transversais

### Spec-Driven Development

O termo e o formato de pipeline vêm de duas implementações recentes:

- **[GitHub Spec Kit](https://github.com/github/spec-kit)** — pipeline `/specify → /plan → /tasks → /implement`, spec como artefato executável versionado.
- **[AWS Kiro](https://kiro.dev)** — tríade `requirements.md` / `design.md` / `tasks.md`, com requisitos em EARS e hooks de agente.

**Adaptação.** O Leanwork SDD reordena para `arquitetura → requisitos → interface → plano → review → contexto`, adota Gherkin em PT-BR no lugar de EARS, e acrescenta duas fases que nenhuma das duas ferramentas tem: **protótipo como especificação** e **review rastreável**. A hierarquia de backlog é a do Azure Boards, não a genérica.

A raiz mais antiga da ideia — requisito escrito antes do código, verificável, separado de design — é **[ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html)** (sucessora da IEEE Std 830-1998) e **Michael Jackson**, *Problem Frames* (2001), sobre a distinção requisito × especificação.

### Rastreabilidade bidirecional — a espinha do pipeline

A cadeia `ADR → RN → CA → UI → T → R` é uma **matriz de rastreabilidade de requisitos (RTM)**.

- **[ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html)**, §5.2.8 — traceability forward e backward; §5.2.5 — cada requisito registra sua origem.
- **CMMI-DEV, REQM SP 1.4** — "manter rastreabilidade bidirecional entre requisitos e produtos de trabalho".
- **DO-178C** (aviônica) e **IEC 62304** (dispositivos médicos) — onde a RTM é obrigatória por certificação.

**Adaptação.** A norma exige rastreabilidade; ela não prescreve prefixos, formato de ID nem o elo com o finding de review. O que o pipeline faz de próprio: seis níveis de ID num único grafo, com o **review como elo terminal** e o comando `/leanwork-trace` como verificador automático de buracos.

O elo `ADR ↔ CA` — amarrar um cenário Gherkin a uma decisão arquitetural — não tem equivalente publicado que conheçamos. Ver [O que é autoral](#o-que-é-autoral).

### Progressive disclosure

SKILL.md curta + `references/` carregadas sob demanda.

- **Jakob Nielsen / NN Group** — [progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) como princípio de interface (1994).
- **[Anthropic — Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)** — o padrão específico de SKILL.md + arquivos de referência, e o `description` com frases-gatilho como mecanismo de seleção.

**Reprodução** do formato de produto; **adaptação** do princípio de UI para economia de contexto de agente.

### Ferramentas e formatos citados

| Item | Fonte |
|---|---|
| **Mermaid** | Knut Sveidqvist — [mermaid.js.org](https://mermaid.js.org), licença MIT. Sintaxes usadas: `flowchart`, `sequenceDiagram`, `stateDiagram-v2` |
| **Model Context Protocol (MCP)** | Anthropic, 2024 — [modelcontextprotocol.io](https://modelcontextprotocol.io). Usado na ingestão de Figma |
| **Azure Boards — processo Scrum** | Microsoft — [hierarquia Epic → Feature → PBI](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/scrum-process) |
| **settings.json / permissões** | [Anthropic — Claude Code settings](https://docs.claude.com/en/docs/claude-code/settings) |
| **ISO 8601** | Formato de data nos nomes de arquivo de review |

---

## 1. `architect-leanwork` — Arquitetura

### C4 Model

- **Simon Brown** — [c4model.com](https://c4model.com). Os quatro níveis (Context, Container, Component, Code), a regra de que Context é caixa-preta, e a proibição de misturar níveis no mesmo diagrama.

**Reprodução** dos níveis e das regras de abstração. **Adaptação** na notação: os templates usam `flowchart` do Mermaid com estilo próprio, não a notação C4 canônica nem o `C4Context` nativo do Mermaid.

O `stateDiagram-v2` incluído em `c4-mermaid-templates.md` **não pertence ao C4** — é extensão do repositório, ver Statecharts abaixo.

### Architecture Decision Records

- **Michael Nygard** — ["Documenting Architecture Decisions"](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) (2011). Origem do formato Context / Decision / Status / Consequences e do status *superseded*.
- **[MADR](https://adr.github.io/madr/)** — Markdown ADR. Origem da tricotomia de consequências Positivas / Negativas / Neutras e da seção "Opções consideradas".
- **Nat Pryce** — [adr-tools](https://github.com/npryce/adr-tools). Convenção de numeração sequencial e nome de arquivo.
- **Olaf Zimmermann** — Y-statements, formato condensado alternativo.

**Reprodução.** O `adr-template.md` é fiel a Nygard + MADR. O que é próprio: a exigência de que cada ADR seja citado por ID no PRD, no plano e no review — o ADR deixa de ser documento morto e vira ponto de costura.

### Estrutura da proposta arquitetural

- **[arc42](https://arc42.org)** — Gernot Starke e Peter Hruschka. Template de documentação arquitetural em 12 seções.

**Adaptação.** A ordem e o recorte das seções ecoam arc42, mas o pipeline omite a *deployment view* (arc42 §7) e acrescenta seções de dívida técnica e de riscos com formato próprio.

### Cynefin

- **Dave Snowden e Mary Boone** — ["A Leader's Framework for Decision Making"](https://hbr.org/2007/11/a-leaders-framework-for-decision-making), Harvard Business Review, 2007.

**Reprodução** dos quatro domínios (simples, complicado, complexo, caótico). O repositório omite *disorder*, o quinto domínio.

### Catálogo de estilos arquiteturais

Dez estilos, na ordem em que aparecem em `architectural-styles.md`:

| Estilo | Fonte canônica | Fidelidade |
|---|---|---|
| **Monolito em camadas** | Padrão *Layers* — Buschmann et al., *Pattern-Oriented Software Architecture* vol. 1 (1996); Fowler, *[PoEAA](https://martinfowler.com/books/eaa.html)* (2002) | **Adaptação** — o repo não descreve as camadas; o conteúdo é argumentação de praticante a favor do estilo |
| **Modular Monolith** | Simon Brown (talk *Modular Monoliths*, ~2015); [Kamil Grzybek](https://www.kamilgrzybek.com); Bounded Context de Eric Evans, *DDD* (2003) | **Reprodução** da definição; trade-offs próprios |
| **Microsserviços** | [James Lewis e Martin Fowler](https://martinfowler.com/articles/microservices.html) (2014); Sam Newman, *Building Microservices* (2015) | **Adaptação** — características canônicas + limiar "< 15 devs", que é heurística própria sem lastro na literatura |
| **Pipes & Filters** | Garlan & Shaw (1994); *POSA* vol. 1; Hohpe & Woolf, *[EIP](https://www.enterpriseintegrationpatterns.com)* (2003) | **Reprodução** |
| **Event-Driven Architecture** | Roy Schulte / Gartner (~2003); Hohpe & Woolf; Fowler, *What do you mean by Event-Driven?* (2017) | **Reprodução** do vocabulário de desacoplamento temporal/estrutural |
| **CQRS** | **Greg Young** (2010), derivado do CQS de **Bertrand Meyer**, *Object-Oriented Software Construction* (1988); ver [Fowler](https://martinfowler.com/bliki/CQRS.html) | **Reprodução** |
| **Event Sourcing** | [Martin Fowler](https://martinfowler.com/eaaDev/EventSourcing.html) (2005); Greg Young | **Reprodução** da definição; as fraquezas de versionamento de evento seguem Young |
| **Microkernel / Plugin** | Padrão *Microkernel* — *POSA* vol. 1 (1996); nomenclatura difundida por Mark Richards, *Software Architecture Patterns* (O'Reilly, 2015) | **Reprodução** minimalista |
| **Serverless / FaaS** | [Mike Roberts e Martin Fowler](https://martinfowler.com/articles/serverless.html) (2016) | **Adaptação** — os números de cold start e limite de execução são dados de provider, não literatura |
| **REST + API Gateway + Adapters** | REST — [Roy Fielding](https://ics.uci.edu/~fielding/pubs/dissertation/top.htm) (2000); API Gateway — Chris Richardson, [microservices.io](https://microservices.io); Adapter — GoF (1994); BFF — Phil Calçado / SoundCloud (2015) | **Autoral na composição** — não é um estilo canônico, é um agrupamento pragmático de três padrões |

Outros conceitos citados no mesmo arquivo, sem crédito no original:

- **Lei de Conway** — [Melvin Conway](https://www.melconway.com/Home/Committees_Paper.html), 1968. Ver [divergências](#lei-de-conway-usada-de-forma-prescritiva).
- **Circuit Breaker**, **Bulkhead**, **Timeout**, **Retry** — Michael Nygard, *[Release It!](https://pragprog.com/titles/mnee2/release-it-second-edition/)* (2007); ver também [Fowler](https://martinfowler.com/bliki/CircuitBreaker.html).
- **Saga** — Hector Garcia-Molina e Kenneth Salem, SIGMOD 1987; reaplicado a microsserviços por [Chris Richardson](https://microservices.io/patterns/data/saga.html).
- **"Boring technology"** — [Dan McKinley](https://mcfunley.com/choose-boring-technology), 2015. Aparece entre aspas no repositório, sem atribuição.
- **Domain-Driven Design** — Eric Evans (2003). Citado por sigla ao longo de todo o repositório.
- **Clean Architecture** — [Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) (2012); **Onion Architecture** — [Jeffrey Palermo](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/) (2008). O template de diagrama de Component reproduz esse layering.
- **Mediator** — GoF, *Design Patterns* (1994); a biblioteca MediatR (Jimmy Bogard) aparece no exemplo.
- **Repository** — Evans (2003) e Fowler, *PoEAA* (2002).

### Catálogo de atributos de qualidade

O catálogo tem **sete** atributos. Ele **não é ISO/IEC 25010** e não corresponde ao conjunto de **Bass, Clements & Kazman**, *Software Architecture in Practice*. Afirmar conformidade seria incorreto. O mapeamento honesto:

| Atributo no repo | [ISO/IEC 25010](https://www.iso.org/standard/78176.html) | Bass/Clements/Kazman |
|---|---|---|
| Performance | = *Performance Efficiency* | Capítulo próprio |
| Escalabilidade | Não é característica de topo (em 25010:2023 é sub-característica de *Flexibility*) | Sem capítulo próprio |
| Disponibilidade | Sub-característica de *Reliability* | Capítulo próprio — "quantos noves" é vocabulário deles |
| Resiliência | **Não existe** como termo; mais próximo é *Fault Tolerance* + *Recoverability* | **Não é QA de Bass** — vem de Nygard e da cultura SRE/Netflix |
| Segurança | = *Security* | Capítulo próprio (tríade CIA) |
| Manutenibilidade | = *Maintainability* | Corresponde a dois capítulos: *Modifiability* + *Testability* |
| Observabilidade | **Não existe** em 25010 | **Não é QA de Bass** — teoria de controle (Kálmán, 1960) → SRE, Charity Majors, Cindy Sridharan |

**Veredito: adaptação declarada.** Quatro dos sete casam com a norma. Três (Escalabilidade, Resiliência, Observabilidade) são vocabulário de indústria promovido a atributo de primeira classe por escolha do autor. Ausentes em relação à ISO 25010: *Functional Suitability*, *Compatibility*, *Usability*, *Portability*.

A estrutura de cenário de atributo de qualidade em três campos é **adaptação** do *Quality Attribute Scenario* de Bass/Clements/Kazman, que tem seis (source, stimulus, artifact, environment, response, response measure). A regra "toda decisão precisa apontar para um atributo priorizado" é a lógica do **ATAM** (SEI, CMU/SEI-2000-TR-004) sem o método — não há *utility tree* nem sessão de avaliação.

Padrões táticos citados dentro dos atributos:

- **Cache-aside**, **Health Endpoint Monitoring**, **Materialized View** — [Microsoft Cloud Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/).
- **Stateless services** — *[The Twelve-Factor App](https://12factor.net)*, fator VI (Adam Wiggins, Heroku, 2011).
- **Blue-green** e **canary** — [Fowler](https://martinfowler.com/bliki/BlueGreenDeployment.html); Humble & Farley, *[Continuous Delivery](https://continuousdelivery.com)* (2010).
- **Retry com exponential backoff e jitter** — [AWS Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/); Marc Brooker (2015). *O repositório cita backoff exponencial sem jitter — omissão que importa em produção.*
- **Outbox** — [Chris Richardson](https://microservices.io/patterns/data/transactional-outbox.html); Gunnar Morling (Debezium).
- **Idempotência** — [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) §9.2.2; Hohpe & Woolf (*Idempotent Receiver*).
- **Dependency Injection** — [Fowler](https://martinfowler.com/articles/injection.html) (2004).
- **Threat modeling** — Adam Shostack, *Threat Modeling: Designing for Security* (2014); STRIDE (Kohnfelder & Garg, Microsoft, 1999).
- **Menor privilégio** — [Saltzer & Schroeder](https://web.mit.edu/Saltzer/www/publications/protection/) (1975).
- **Alertas por SLO** — Betsy Beyer et al., *[Google SRE Book](https://sre.google/sre-book/table-of-contents/)* (2016) e *The Site Reliability Workbook* (2018).
- **Três pilares da observabilidade** — Cindy Sridharan, *Distributed Systems Observability* (2018); linhagem de tracing em Dapper (Google, 2010) → [OpenTelemetry](https://opentelemetry.io).
- Ferramentas nomeadas: [Polly](https://github.com/App-vNext/Polly), [Resilience4j](https://github.com/resilience4j/resilience4j), [Serilog](https://serilog.net), Prometheus, Datadog, Application Insights, Redis, Kubernetes.
- Normas nomeadas: [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm), PCI DSS, ISO 27001, SOC 2, ANVISA, BACEN, [WCAG](https://www.w3.org/TR/WCAG22/).

### Práticas ágeis citadas de passagem

- **Spike solution**, **pair programming**, **integração contínua** — Kent Beck, *Extreme Programming Explained* (1999).
- **Sprint** — Ken Schwaber e Jeff Sutherland, *[Scrum Guide](https://scrumguides.org)*.
- **MVP** — Frank Robinson (2001), popularizado por Eric Ries, *The Lean Startup* (2011).
- **Continuous Delivery** — Jez Humble e David Farley (2010).
- **Feature toggles** — [Pete Hodgson](https://martinfowler.com/articles/feature-toggles.html) (2017). Usado sem a taxonomia release/ops/experiment/permission.

---

## 2. `prd-leanwork` — Requisitos

### BDD e Gherkin

- **Dan North** — *[Introducing BDD](https://dannorth.net/introducing-bdd/)* (2006). Inventor de Given-When-Then e do termo BDD, com Chris Matts.
- **Aslak Hellesøy e Matt Wynne** — Cucumber e a linguagem Gherkin; *The Cucumber Book* (2012).
- **[Referência da linguagem Gherkin](https://cucumber.io/docs/gherkin/reference/)**.

**Reprodução literal.** As palavras-chave em português — `Funcionalidade`, `Cenário`, `Esquema do Cenário`, `Exemplos`, `Dado`, `Quando`, `Então`, `E`, `Mas` — são a localização `pt` oficial do [`gherkin-languages.json`](https://github.com/cucumber/gherkin/blob/main/gherkin-languages.json). Não são tradução autoral.

**Autoral:** a convenção `Cenário [CA-01]: ...` e a citação inline `(RN-XX)` / `(ADR-XX)` nos passos. Nada disso existe no Gherkin padrão. Ver [divergências](#id-no-nome-do-cenário-em-vez-de-tag).

### Specification by Example e anti-padrões de cenário

- **Gojko Adzic** — *[Specification by Example](https://gojko.net/books/specification-by-example/)* (2011). Antes dele, as tabelas do FIT/FitNesse de **Ward Cunningham**.
- **Matt Wynne e Aslak Hellesøy**, com **Liz Keogh** — cenário declarativo × imperativo; "`Dado` afirma estado, não ação".
- **Eric Evans** — *Ubiquitous Language* (DDD, 2003), base do "manter linguagem de negócio".
- **Mike Cohn** — *Succeeding with Agile* (2009), pirâmide de testes; ver [Fowler](https://martinfowler.com/bliki/TestPyramid.html). Fundamenta "reservar UI para testes E2E".

**Adaptação.** A lista de anti-padrões é síntese condensada de material amplamente publicado pela comunidade Cucumber.

### Narrativa de feature

O formato `Para... / Como... / Eu quero...` é a variante **In order to / As a / I want** de **Chris Matts e Dan North** (Feature Injection), adotada como narrativa padrão do Cucumber — não o `As a / I want / So that` original da **Connextra** (2001), popularizado por **Mike Cohn**, *User Stories Applied* (2004).

**Reprodução**, traduzida.

### Hierarquia Epic → Feature → PBI

**Reprodução** do modelo de dados do [processo Scrum do Azure Boards](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/scrum-process). O próprio arquivo declara a motivação: facilitar o cadastro. "PBI" vem do *Scrum Guide*.

O critério "executável em poucos dias" é o **S** de **[INVEST](https://xp123.com/invest-in-good-stories-and-smart-tasks/)** (Bill Wake, 2003), usado sem ser nomeado.

### Estrutura de 17 seções do PRD

Não segue nenhum template público único. É composição derivada de várias fontes:

| Seção | Origem provável |
|---|---|
| Fora do escopo | *Non-Goals* — [Joel Spolsky](https://www.joelonsoftware.com/2000/10/03/painless-functional-specifications-part-1-why-bother/) (2000); replicado nos design docs do Google e nos RFCs de Rust/Kubernetes |
| Questões em aberto | *Open Issues* — mesma fonte |
| Restrições e premissas + Riscos e dependências + Questões em aberto | Correspondem ao **RAID log** (Risks, Assumptions, Issues, Dependencies) da gestão de projetos; *assumptions* e *risk register* do **PMBOK (PMI)** |
| Problema e contexto / Objetivo | Blueprint *Product Requirements* do Atlassian Confluence |
| Personas | **Alan Cooper**, *The Inmates Are Running the Asylum* (1998) — inventor de personas |
| Fluxo principal + alternativos/erro | Casos de uso: **Ivar Jacobson** (OOSE, 1992) e **Alistair Cockburn**, *Writing Effective Use Cases* (2000) |
| Regras de negócio numeradas | *Business Rules Approach* — **Ronald G. Ross**; **[Business Rules Manifesto](https://www.businessrulesgroup.org/brmanifesto.htm)** (2003). "Clara e verificável" são os atributos *unambiguous* e *verifiable* da IEEE 830 §4.3 |
| Permissionamento | **[RBAC](https://csrc.nist.gov/projects/role-based-access-control)** — Ferraiolo & Kuhn (NIST, 1992), INCITS 359 |
| Integrações e dados | *External Interface Requirements* — IEEE 830 §3.1 |
| Diagrama de estados | **Statecharts** — David Harel, *A Visual Formalism for Complex Systems* (1987) → UML State Machine (OMG) |
| Arquitetura técnica | Na prática um **C4 Container diagram** (Simon Brown) sem o nome |

**Adaptação.** A *combinação* — RN numerada + CA em Gherkin + Mermaid + ADR cruzado + proibição explícita de estimativa — não corresponde a template público conhecido.

### Exclusão deliberada de estimativa

Story points e t-shirt sizing vêm de **Mike Cohn**, *Agile Estimating and Planning* (2005). Removê-los do documento de requisito ecoa o movimento **#NoEstimates** (Woody Zuill, Vasco Duarte, ~2012), embora o pipeline apenas separe fases em vez de abolir estimativa.

A doutrina "requisito diz o quê, não o como" é **IEEE 830 §4.2** ("A SRS should not specify design") e **David Parnas** / **Michael Jackson**.

**Autoral na formulação**, fundamentado em princípio publicado.

### Elicitação por entrevista estruturada

Técnica canônica catalogada em **ISO/IEC/IEEE 29148**, no **BABOK v3 (IIBA)** e em **Ian Sommerville**, *Software Engineering*.

A regra "nunca fazer pergunta aberta; oferecer 2-3 direções nomeadas" segue **Rob Fitzpatrick**, *[The Mom Test](https://www.momtestbook.com)* (2013) e **Erika Hall**, *Just Enough Research* (2013). O pano de fundo é **Fred Brooks**, *No Silver Bullet* (1987): *"the hardest single part of building a software system is deciding precisely what to build"*.

**Autoral:** o mecanismo "Pula quando" — suprimir perguntas já respondidas por artefatos anteriores do pipeline.

---

## 3. `prototype-leanwork` — Interface como especificação

### Catálogo de estados de tela — atribuição principal

- **Scott Hurff** — *[The UI Stack](https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/)*, e *Designing Products People Love* (O'Reilly, 2015).

Os cinco estados de Hurff são **Ideal, Empty, Error, Partial, Loading**. Os estados universais de `screen-states.md` são `.default`, `.vazio`, `.erro`, `.parcial`, `.carregando`. A correspondência é **1:1, incluindo o estado parcial** — que é raro em outras taxonomias e torna a derivação praticamente certa.

**Adaptação de fonte identificada.** Extensões próprias do repositório: `.semPermissao`, a subdivisão vazio-inicial × vazio-por-filtro, as tabelas de obrigatoriedade por tipo de tela, e os estados derivados de regra de negócio.

Este é o item deste documento que mais exigia crédito explícito.

Referências secundárias no mesmo catálogo:

| Conceito | Fonte |
|---|---|
| *Blank slate* educativo, com ação sugerida | 37signals, *[Getting Real](https://basecamp.com/gettingreal)* (2006), capítulo "Blank Slates" |
| Skeleton preferível a spinner | **Luke Wroblewski**, *[Avoid The Spinner](https://www.lukew.com/ff/entry.asp?1797)* (2013); base em **Jakob Nielsen**, [limites de 0,1s / 1s / 10s](https://www.nngroup.com/articles/response-times-3-important-limits/) |
| Oculto × desabilitado comunicam coisas diferentes | NN Group; heurística #6 *Recognition rather than recall* |
| `.enviando` previne envio duplo | Post/Redirect/Get (Michael Jouravlev, 2004); idempotência em [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) |
| `.conflito` — edição concorrente | *Lost update problem*; Kung & Robinson, *On Optimistic Methods for Concurrency Control* (1981); ETag/If-Match |
| `.erroEnvio` preserva os dados digitados | **[Heurísticas de Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/)** #5 (prevenção) e #9 (recuperação de erro); [WCAG 3.3.4](https://www.w3.org/TR/WCAG22/) |
| `.naoEncontrado` distinto de `.erro` | Semântica HTTP 4xx × 5xx — RFC 9110 |
| Fluxo multi-etapa | Padrão *Wizard* — **Jenifer Tidwell**, *Designing Interfaces* (2005) |
| "Há desfazer?" em ação destrutiva | **Aza Raskin**, *[Never Use a Warning When You Mean Undo](https://alistapart.com/article/neveruseawarning/)* (2010); **Jef Raskin**, *The Humane Interface* (2000) |
| Texto longo, zero e negativo | *Boundary value analysis* — **Glenford Myers**, *The Art of Software Testing* (1979) |
| A lista "estados que costumam faltar" | *Stress cases* — **Eric Meyer e Sara Wachter-Boettcher**, *[Design for Real Life](https://abookapart.com/products/design-for-real-life)* (2016) |

### Protótipo como especificação

Ancoragem principal:

- **Larry Constantine e Lucy Lockwood** — *Software for Use* (1999), **Usage-Centered Design**. É a correspondência mais precisa: derivar formalmente conteúdo e estrutura de tela a partir de casos de uso essenciais, com rastreabilidade. O procedimento do pipeline — cada `Então` de rejeição num cenário Gherkin vira um estado de tela — é o método deles aplicado a Gherkin em vez de use case.

Referências contrastivas e complementares:

- **37signals**, *Getting Real* (2006), capítulos *No Functional Spec* e *Interface First* — origem popular do slogan "o protótipo é a spec". **O pipeline diverge de propósito:** aqui o protótipo não substitui o documento, ele alimenta um documento (a SPEC-UI).
- **Bill Buxton**, *Sketching User Experiences* (2007) — a distinção sketch (explorar) × prototype (refinar) fundamenta a escolha wireframe × alta fidelidade.
- **Jeff Gothelf e Josh Seiden**, *Lean UX* (2013).
- **Barry Boehm** (modelo espiral, 1988) e **Fred Brooks** (*plan to throw one away*) — prototipagem como técnica de elicitação; formalizada na ISO/IEC/IEEE 29148.
- **Carolyn Snyder**, *Paper Prototyping* (2003); **Rudd, Stern & Isensee**, *Low vs. high-fidelity prototyping debate* (interactions, 1996).

**Adaptação** do conceito; **autoral** na mecânica protótipo → SPEC-UI → matriz `UI ↔ RN ↔ CA` com lacuna declarada.

### Design tokens

- Termo cunhado por **Jina Anne** no **[Salesforce Lightning Design System](https://www.lightningdesignsystem.com)** (~2014); hoje formalizado pelo **[W3C Design Tokens Community Group](https://www.w3.org/community/design-tokens/)**.

**Reprodução** do conceito. A regra "referenciar, nunca duplicar em markdown" é **DRY / Single Source of Truth** — Andy Hunt e Dave Thomas, *The Pragmatic Programmer* (1999). **Autoral:** a coluna *Origem* marcando token extraído de imagem como aproximado.

### Inventário de componentes

- **Brad Frost** — *[Interface Inventory](https://bradfrost.com/blog/post/interface-inventory/)* (2013).

**Atenção à precisão:** o repositório faz *interface inventory*, **não Atomic Design**. Não há hierarquia átomo/molécula/organismo em lugar nenhum. Citar Atomic Design aqui seria impreciso.

**Autoral:** a justificativa — evitar que o planner crie duas tarefas para o mesmo componente em telas diferentes. É uma ponte incomum entre design system e planejamento de execução.

### Acessibilidade e responsividade

- **[WCAG 2.2](https://www.w3.org/TR/WCAG22/)** (W3C) — o requisito de contraste é [SC 1.4.3 nível AA](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), razão 4.5:1.
- **Progressive enhancement** — Steven Champeon e Nick Finck (SXSW, 2003).
- **Responsive Web Design** — **[Ethan Marcotte](https://alistapart.com/article/responsive-web-design/)** (A List Apart, 2010).
- **Mobile First** — **Luke Wroblewski** (A Book Apart, 2011).

**Reprodução** de vocabulário e norma. *Lacuna:* dado o foco em cliente brasileiro, faltam **LBI (Lei 13.146/2015)** e **eMAG**.

### Arquétipos de interface

Os cinco arquétipos (Admin/Dashboard, Ferramenta interna, E-commerce/Consumer, Portal, Site institucional) são **autorais** — não identificamos taxonomia publicada correspondente. Os princípios sob eles têm fonte:

- Densidade de informação — **Edward Tufte**, *The Visual Display of Quantitative Information* (1983).
- Atalhos para usuário treinado — heurística de Nielsen #7, *Flexibility and efficiency of use*; distinção novato/especialista de **Alan Cooper**, *About Face*.
- Hierarquia tipográfica — **Robert Bringhurst**, *The Elements of Typographic Style* (1992).
- Consistência com telas existentes — heurística de Nielsen #4.

### Conteúdo real em vez de placeholder

- **Kristina Halvorson**, *Content Strategy for the Web* (2009); **Karen McGrane**; **Jeffrey Zeldman** — *content precedes design*. Origem da crítica ao lorem ipsum em protótipo.

---

## 4. `planner-leanwork` — Plano de execução

- **Decomposição em tarefas com fase e dependência** — *Work Breakdown Structure*, **PMBOK (PMI)**; ISO/IEC 12207.
- **Definition of Done** — Scrum; os critérios de conclusão por fase são DoD sem o nome.
- **Teste de caracterização** — **Michael Feathers**, *Working Effectively with Legacy Code* (2004). **Reprodução** de terminologia proprietária.
- **Arrange-Act-Assert** — **[Bill Wake](https://xp123.com/3a-arrange-act-assert/)** (2001).
- **Deployment pipeline, staging, smoke test** — Humble & Farley, *Continuous Delivery* (2010); *daily build and smoke test* em **Steve McConnell**, *Rapid Development* (1996).
- **Logging estruturado e correlation ID** — [Serilog](https://serilog.net) (Nicholas Blumhardt); *Correlation Identifier* em Hohpe & Woolf, *EIP*.
- **Cardinalidade de métricas** — a advertência sobre usar `customerId` como tag reproduz fielmente a orientação do **[Prometheus](https://prometheus.io/docs/practices/naming/)** e do OpenTelemetry.
- **Feature flags** — Pete Hodgson (2017).
- **Parallel Change / Expand-Contract** — **[Fowler](https://martinfowler.com/bliki/ParallelChange.html)**. **Reprodução** das três fases (expandir, migrar, contrair) para sequenciar refactors de alto *blast radius* dentro do plano, mantendo CI verde tarefa a tarefa.

**Autoral:** os sinais de "tarefa grande demais / pequena demais", a tabela de campos legitimamente vazios, e todos os limiares de calibragem (30min-4h por tarefa, 3 critérios de aceite, > 5 tarefas → diagrama Mermaid). São números de praticante, sem fonte externa.

---

## 5. `reviewer-leanwork` — Code review

- **Modern Code Review** — **[Google Engineering Practices](https://google.github.io/eng-practices/review/)**. Origem direta de duas regras do repositório: não comentar o que o linter cobre, e não pedir "como eu faria". Também **Mäntylä & Lassenius** (2009) sobre taxonomia de defeitos encontrados em review, e **IEEE 1028** sobre inspeção formal (linhagem **Michael Fagan**, IBM, 1976).
- **Conventional Comments** — [conventionalcomments.org](https://conventionalcomments.org/), e as labels do Gerrit. Antecedente da ideia de rotular severidade do comentário.
- **Code smells** — **Martin Fowler** e Kent Beck, *Refactoring* (1999).
- **Test smells** — **Gerard Meszaros**, *[xUnit Test Patterns](https://xunitpatterns.com)* (2007); van Deursen et al. (2001). Origem do catálogo de problemas de teste, incluindo "teste de integração que não vai ao banco real".
- **Mocks Aren't Stubs** — [Fowler](https://martinfowler.com/articles/mocksArentStubs.html) (2007), distinção sociable × solitary. **[Testcontainers](https://testcontainers.com)** como resposta de indústria ao smell.
- **Quadrante de dívida técnica** — [Fowler](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html) (2009), origem de "consciente" × "acidental".
- **Async/await** — **Stephen Cleary**, *[Async/Await Best Practices](https://learn.microsoft.com/en-us/archive/msdn-magazine/2013/march/async-await-best-practices-in-asynchronous-programming)* (MSDN Magazine, 2013). O item sobre `.Result` / `.Wait()` e deadlock é o checklist dele condensado em uma linha.
- **Validação de input** — CWE-20; OWASP Input Validation Cheat Sheet.
- **PII em log** — **[LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)** art. 6º; GDPR art. 5(1)(c); **[OWASP Top 10](https://owasp.org/Top10/)** A09; **[CWE-532](https://cwe.mitre.org/data/definitions/532.html)**.
- **Idempotência** — RFC 9110; *Idempotent Receiver* em Hohpe & Woolf.
- **Monorepo** — Potvin & Levenberg, *Why Google Stores Billions of Lines of Code in a Single Repository* (CACM, 2016).

**Escopo declarado:** a skill afirma explicitamente que **não faz threat modeling completo** nem aplica o OWASP Top 10 como checklist ativo — apenas princípios universais (segredos, PII). É delimitação honesta e está registrada aqui como tal.

**Autoral:**
- Os **eixos 1 (aderência ao plano) e 2 (rastreabilidade)** — não têm contrapartida em Google eng-practices, Mäntylä & Lassenius ou IEEE 1028. Só existem porque existe um plano com IDs para aderir.
- A **tabela de severidade default por categoria** e as três regras de escalonamento.
- A escala Bloqueante / Importante / Sugestão é convergente com a prática de indústria, sem fonte única atribuível.

---

## 6. `context-leanwork` — CLAUDE.md e permissões

- **Formato de plugin e Agent Skills** — [Anthropic](https://docs.claude.com/en/docs/claude-code/skills).
- **Escopos de configuração** (`.claude/settings.json` versionado × `settings.local.json` pessoal) — [documentação do Claude Code](https://docs.claude.com/en/docs/claude-code/settings). O princípio subjacente é a convenção `.editorconfig` / `.vscode` e o fator III do *[Twelve-Factor App](https://12factor.net)*.
- **Docs as code** — Documentação versionada junto ao código; linhagem Write the Docs / **Anne Gentle**, *Docs Like Code* (2017).
- **Blocos delimitados e não-destrutividade** — a técnica de marcadores `<!-- start -->` / `<!-- end -->` é convenção difundida (Prettier, all-contributors, GitHub Actions de README). **Adaptação.**

### Catálogo de permissões — princípios de segurança

- **Menor privilégio** e **fail-safe defaults** — **[Saltzer & Schroeder](https://web.mit.edu/Saltzer/www/publications/protection/)**, *The Protection of Information in Computer Systems* (1975), princípios #1 e #2.
- **Aceitabilidade psicológica** — mesmo artigo, princípio #8. É a base de "não bloquear o que o pipeline precisa".
- **Fadiga de confirmação** — a afirmação de que uma lista `ask` grande demais treina o dev a aprovar no automático **não é opinião, tem base experimental**: Akhawe & Felt, *Alice in Warningland* (USENIX Security, 2013); Sunshine et al., *Crying Wolf* (USENIX Security, 2009); Cranor, *A Framework for Reasoning About the Human in the Loop* (2008).
- **Supply chain de dependências** — OWASP Top 10 A06 e A08; **[SLSA](https://slsa.dev)** (OpenSSF); NIST SP 800-218 (SSDF). Incidentes canônicos: `event-stream` (2018), `ua-parser-js` (2021), `colors`/`faker` (2022).
- **Proteção de histórico compartilhado** — a *golden rule of rebasing* e `--force-with-lease` em **[Pro Git](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)** (Chacon & Straub).
- **Classificação por reversibilidade** — *two-way vs one-way door decisions* (Jeff Bezos, carta aos acionistas de 2015); *blast radius* no **Google SRE Book**; a separação leitura × escrita ecoa o CQS de Bertrand Meyer.

**Autoral:** a tabela de três perguntas que decide o balde `allow` / `ask` / `deny`. É a peça mais reutilizável do catálogo e não tem antecedente publicado que conheçamos.

---

## Divergências deliberadas com a literatura

Pontos em que o pipeline se afasta do cânone. Todos são escolhas, não descuidos — mas quem adota o plugin precisa saber que está adotando o desvio junto.

### Fatiamento horizontal por camada

O `plan-template.md` organiza fases por camada técnica (domínio → persistência → API → UI). Isso contraria o **vertical slice** e o **walking skeleton** de **[Alistair Cockburn](https://alistair.cockburn.us/walking-skeleton/)**, e o **story mapping** de **[Jeff Patton](https://www.jpattonassociates.com/story-mapping/)**, que defendem entregar valor fim-a-fim desde a primeira fatia.

**Justificativa do pipeline:** com um PRD e uma arquitetura já fechados antes do plano, o risco de descoberta tardia — o principal argumento a favor do vertical slice — é menor. **Contra-argumento honesto:** o risco de integração continua real, e fatia horizontal o empurra para o fim.

**Exceção seletiva (v1.8.0):** quando a entrevista do planner sinaliza entrega incremental real (Bloco 2) ou risco de integração concreto (Bloco 4), a fatia vertical volta a valer — não para o plano inteiro, só para a parte afetada. `planner-leanwork/SKILL.md`, seção "Orientação da fatia", e `task-examples.md`, Exemplo 6. O horizontal continua sendo o default; a exceção é condicionada a sinal explícito da entrevista, não a preferência.

### Numeração sequencial global de tarefas

`T-01`, `T-02`... numeradas linearmente. A **WBS** do PMBOK usa codificação hierárquica (`1.2.3`), que carrega a estrutura de decomposição no próprio ID. A escolha aqui privilegia ID curto e estável para citação em commit e review.

### ID no nome do cenário em vez de tag

`Cenário [CA-01]: ...` contraria a convenção do Cucumber, que usa **tags** (`@CA-01`) justamente porque são filtráveis pelo runner (`--tags @CA-01`). O ID no nome não é filtrável e quebra se alguém reescrever o título.

### Lei de Conway usada de forma prescritiva

O catálogo de estilos trata a lei de Conway como orientação de desenho ("organize a arquitetura conforme os times"). O artigo original de **Conway (1968)** é **descritivo** — constata que sistemas espelham a estrutura de comunicação da organização. Usá-la prescritivamente é o **Inverse Conway Maneuver** (ThoughtWorks; **Skelton & Pais**, *[Team Topologies](https://teamtopologies.com)*, 2019), que merece o nome.

### CAP apresentado como trade-off permanente

A leitura clássica "escolha 2 de 3" foi corrigida pelo próprio **Eric Brewer** em *[CAP Twelve Years Later](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)* (2012): o trade-off só vale durante partição. Fora dela, o dilema real é latência × consistência — que é o modelo **PACELC** (Daniel Abadi, 2010), ausente do repositório.

### Stack-agnóstico com exemplos .NET (mitigado na v1.9.0)

As skills se declaram stack-agnósticas, e a arquitetura de resolução (proposta → CLAUDE.md → inspeção → pergunta) sustenta isso. Até a v1.8.0, porém, os exemplos didáticos do núcleo eram fortemente .NET: MediatR, FluentValidation, EF Core, Serilog, xUnit apareciam direto em `templates/pipeline-example.md`, `planner-leanwork/references/task-examples.md` e nos templates de preenchimento (`plan-template.md`, `prd-template.md`, `proposal-template.md`, `claude-md-root-template.md`).

A v1.9.0 segrega esse conteúdo: o exemplo end-to-end e os exemplos de tarefa viram pseudocódigo agnóstico no núcleo, com a versão .NET completa movida para `stacks/dotnet/` e referenciada por link explícito. Os placeholders `.NET` soltos nos templates de preenchimento viram genéricos.

**O que não foi resolvido nesta passagem:** o catálogo de detecção de stack (`reviewer-leanwork/references/stack-detection.md`) e o checklist de review (`reviewer-leanwork/references/review-checklist.md`) ainda usam .NET como exemplo ilustrativo em alguns pontos — inclusive um item específico de anti-padrão async (`.Result`/`.Wait()`) que não tem equivalente descrito para outras stacks. Ficou fora do escopo desta rodada porque `stack-detection.md` já é multi-stack por natureza (a cascata de descoberta é o mecanismo agnóstico; o exemplo é só ilustração de como ela fica preenchida) — mas o item do checklist é viés real, ainda não corrigido.

### O exemplo canônico contradiz a postura declarada (mitigado na v1.9.0)

A skill de arquitetura lista Clean Architecture entre os modismos que não se deve adotar por moda, e o catálogo de atributos afirma que DDD/Clean é overkill para CRUD simples. Até a v1.8.0, porém, o **único** template de diagrama de Component fornecido era uma Clean/Onion Architecture completa com MediatR — sem nenhuma ressalva.

A v1.9.0 troca o diagrama de `c4-mermaid-templates.md` por uma versão com nomes de padrão genéricos (sem biblioteca), e move a versão com MediatR/FluentValidation/EF Core para `stacks/dotnet/c4-component-example.md`, com uma nota explícita de que é "um caso entre vários", não recomendação. A divergência apontada aqui está resolvida; o diagrama de exemplo já não contradiz a postura declarada da skill.

### `grep` verifica menção, não execução

A convenção de rastrear cenários por `grep -r "CA-01" tests/` confirma que o ID foi *citado* num teste — não que o teste existe, roda e passa. É verificação de nomenclatura, não de cobertura.

---

## O que é autoral

Contribuições para as quais não identificamos antecedente publicado. Reivindicadas como próprias do Leanwork SDD:

1. **A cadeia de seis IDs `ADR → RN → CA → UI → T → R` como grafo único**, com o finding de review como elo terminal e um comando (`/leanwork-trace`) que audita buracos nos dois sentidos.
2. **Amarrar cenário Gherkin a decisão arquitetural** (`Cenário [CA-06]: ... (ADR-002)`). Particularmente útil em concorrência, consistência e falha. Não conhecemos publicação que proponha isso.
3. **Protótipo como artefato rastreável do pipeline** — SPEC-UI com matriz `UI ↔ RN ↔ CA` e lacuna declarada em vez de preenchida.
4. **O princípio de origem sempre declarada** — cada informação marca se veio do protótipo, do PRD ou do usuário. "Fechar matriz com invenção é pior que matriz honestamente incompleta." É a contribuição mais original da fase de protótipo.
5. **Sufixo de estado com ponto** (`UI-02.erroEnvio`) e a semântica `Telas: UI-02 (default, erro)` no plano.
6. **Os eixos de aderência ao plano e de rastreabilidade** no code review, e o **eixo 6 de conformidade de interface** — que verifica estados de tela contra a SPEC-UI e declara explicitamente que estética não é território de code review.
7. **A tabela de três perguntas** que classifica uma permissão em `allow` / `ask` / `deny` por reversibilidade e blast radius.
8. **O mecanismo "Pula quando"** na entrevista — o agente suprime perguntas já respondidas por artefatos anteriores.
9. **Os cinco arquétipos de interface** e a regra de nunca fazer pergunta aberta sobre estética.
10. **A divisão de conteúdo raiz × módulo** no CLAUDE.md, e os critérios para *não* criar um arquivo de módulo.
11. **Todos os limiares de calibragem** — 7-12 ADRs, 60-120 linhas, 30min-4h por tarefa, < 15 devs para microsserviços, ~15 linhas úteis mínimas por módulo. São opinião de praticante, sem fonte externa, e devem ser lidos assim.

---

## Lacunas conhecidas

Conceitos que o pipeline tangencia sem cruzar. Registrados aqui como roadmap honesto, não como defeito escondido.

| Lacuna | O que resolveria |
|---|---|
| **Fitness functions** — Ford, Parsons & Kua, *Building Evolutionary Architectures* (2017) | O catálogo reconhece que "enforcement de boundaries é fraco" — que é exatamente o que ArchUnit/NetArchTest/dependency-cruiser resolvem como teste automatizado de arquitetura |
| **Ports & Adapters** — [Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/) (2005) | O termo "adapters" é usado; o padrão e o autor nunca são nomeados |
| **Strangler Fig** — [Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html) (2004) | Migração incremental de legado é discutida sem o padrão que a nomeia |
| **Deployment view** — arc42 §7, C4 Deployment diagram | Multi-AZ, Kubernetes e serverless são decididos sem diagrama de topologia física |
| **Golden Signals / RED / USE** — Google SRE, Tom Wilkie, Brendan Gregg | Observabilidade lista ferramentas, mas não adota método de métrica |
| **DORA / Accelerate** — [dora.dev](https://dora.dev) | Nada mede se a arquitetura proposta melhorou a entrega |
| **STRIDE / ASVS** | Threat modeling é prescrito como atividade, sem método |
| **ATAM / utility tree** — SEI | A lógica decisão↔atributo está lá; o método de avaliação não |
| **RTO / RPO** | DR é citado sem as duas métricas que o definem |
| **Jitter no retry** | Backoff exponencial sem jitter sincroniza clientes e mantém o thundering herd |
| **eMAG e LBI (Lei 13.146/2015)** | Acessibilidade cita WCAG, mas não a norma brasileira |
| **Conventional Commits** | O pipeline exige citar `T-XX` no commit, mas não adota convenção de tipo/escopo |
| **Impact Mapping, Event Storming, Story Mapping** | Técnicas de descoberta que antecederiam bem a fase de arquitetura |

---

## Bibliografia consolidada

### Livros

| Autor | Obra | Ano |
|---|---|---|
| Bass, Clements & Kazman | *Software Architecture in Practice* | 2021 (4ª ed.) |
| Kent Beck | *Extreme Programming Explained* | 1999 |
| Kent Beck & Martin Fowler | *Refactoring* | 1999 |
| Betsy Beyer et al. | *Site Reliability Engineering* | 2016 |
| Robert Bringhurst | *The Elements of Typographic Style* | 1992 |
| Fred Brooks | *The Mythical Man-Month* / *No Silver Bullet* | 1975 / 1987 |
| Buschmann et al. | *Pattern-Oriented Software Architecture*, vol. 1 | 1996 |
| Bill Buxton | *Sketching User Experiences* | 2007 |
| Chacon & Straub | *Pro Git* | 2014 |
| Mike Cohn | *User Stories Applied* / *Agile Estimating and Planning* | 2004 / 2005 |
| Alistair Cockburn | *Writing Effective Use Cases* | 2000 |
| Constantine & Lockwood | *Software for Use* | 1999 |
| Alan Cooper | *The Inmates Are Running the Asylum* / *About Face* | 1998 / 1995 |
| Eric Evans | *Domain-Driven Design* | 2003 |
| Michael Feathers | *Working Effectively with Legacy Code* | 2004 |
| Martin Fowler | *Patterns of Enterprise Application Architecture* | 2002 |
| Forsgren, Humble & Kim | *Accelerate* | 2018 |
| Gamma, Helm, Johnson & Vlissides | *Design Patterns* | 1994 |
| Gothelf & Seiden | *Lean UX* | 2013 |
| Erika Hall | *Just Enough Research* | 2013 |
| Kristina Halvorson | *Content Strategy for the Web* | 2009 |
| Hohpe & Woolf | *Enterprise Integration Patterns* | 2003 |
| Humble & Farley | *Continuous Delivery* | 2010 |
| Hunt & Thomas | *The Pragmatic Programmer* | 1999 |
| Scott Hurff | *Designing Products People Love* | 2015 |
| Michael Jackson | *Problem Frames* | 2001 |
| Steve McConnell | *Rapid Development* | 1996 |
| Bertrand Meyer | *Object-Oriented Software Construction* | 1988 |
| Meyer & Wachter-Boettcher | *Design for Real Life* | 2016 |
| Gerard Meszaros | *xUnit Test Patterns* | 2007 |
| Glenford Myers | *The Art of Software Testing* | 1979 |
| Sam Newman | *Building Microservices* | 2015 |
| Jakob Nielsen | *Usability Engineering* | 1993 |
| Michael Nygard | *Release It!* | 2007 / 2018 (2ª ed.) |
| Jef Raskin | *The Humane Interface* | 2000 |
| Mark Richards | *Software Architecture Patterns* | 2015 |
| Eric Ries | *The Lean Startup* | 2011 |
| Adam Shostack | *Threat Modeling: Designing for Security* | 2014 |
| Skelton & Pais | *Team Topologies* | 2019 |
| Carolyn Snyder | *Paper Prototyping* | 2003 |
| Cindy Sridharan | *Distributed Systems Observability* | 2018 |
| Starke & Hruschka | *arc42* | contínuo |
| Jenifer Tidwell | *Designing Interfaces* | 2005 |
| Edward Tufte | *The Visual Display of Quantitative Information* | 1983 |
| Wynne & Hellesøy | *The Cucumber Book* | 2012 |
| 37signals | *Getting Real* | 2006 |

### Artigos e ensaios

- Akhawe & Felt — *Alice in Warningland* (USENIX Security, 2013)
- Eric Brewer — *[CAP Twelve Years Later](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)* (2012)
- Melvin Conway — *[How Do Committees Invent?](https://www.melconway.com/Home/Committees_Paper.html)* (1968)
- Stephen Cleary — *[Async/Await Best Practices](https://learn.microsoft.com/en-us/archive/msdn-magazine/2013/march/async-await-best-practices-in-asynchronous-programming)* (2013)
- Roy Fielding — *[Architectural Styles and the Design of Network-based Software Architectures](https://ics.uci.edu/~fielding/pubs/dissertation/top.htm)* (2000)
- Martin Fowler — bliki: [CQRS](https://martinfowler.com/bliki/CQRS.html), [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html), [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html), [Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html), [Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html), [Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html), [Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html), [Dependency Injection](https://martinfowler.com/articles/injection.html)
- Garcia-Molina & Salem — *Sagas* (SIGMOD, 1987)
- David Harel — *Statecharts: A Visual Formalism for Complex Systems* (1987)
- Pete Hodgson — *[Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)* (2017)
- Kung & Robinson — *On Optimistic Methods for Concurrency Control* (ACM TODS, 1981)
- Lewis & Fowler — *[Microservices](https://martinfowler.com/articles/microservices.html)* (2014)
- Ethan Marcotte — *[Responsive Web Design](https://alistapart.com/article/responsive-web-design/)* (2010)
- Dan McKinley — *[Choose Boring Technology](https://mcfunley.com/choose-boring-technology)* (2015)
- Jakob Nielsen — *[10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)* (1994)
- Dan North — *[Introducing BDD](https://dannorth.net/introducing-bdd/)* (2006)
- Michael Nygard — *[Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)* (2011)
- Jeffrey Palermo — *[The Onion Architecture](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/)* (2008)
- Potvin & Levenberg — *Why Google Stores Billions of Lines of Code in a Single Repository* (CACM, 2016)
- Aza Raskin — *[Never Use a Warning When You Mean Undo](https://alistapart.com/article/neveruseawarning/)* (2010)
- Roberts & Fowler — *[Serverless Architectures](https://martinfowler.com/articles/serverless.html)* (2016)
- Saltzer & Schroeder — *[The Protection of Information in Computer Systems](https://web.mit.edu/Saltzer/www/publications/protection/)* (1975)
- Snowden & Boone — *[A Leader's Framework for Decision Making](https://hbr.org/2007/11/a-leaders-framework-for-decision-making)* (2007)
- Joel Spolsky — *[Painless Functional Specifications](https://www.joelonsoftware.com/2000/10/03/painless-functional-specifications-part-1-why-bother/)* (2000)
- Sunshine et al. — *Crying Wolf: An Empirical Study of SSL Warning Effectiveness* (USENIX Security, 2009)
- Bill Wake — *[INVEST](https://xp123.com/invest-in-good-stories-and-smart-tasks/)* (2003), *[Arrange-Act-Assert](https://xp123.com/3a-arrange-act-assert/)* (2001)
- Luke Wroblewski — *[Avoid The Spinner](https://www.lukew.com/ff/entry.asp?1797)* (2013)

### Normas, frameworks e sites de referência

- [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) — Requirements engineering
- [ISO/IEC 25010](https://www.iso.org/standard/78176.html) — SQuaRE, modelo de qualidade de produto
- IEEE Std 830-1998 — SRS (superseda pela 29148)
- IEEE Std 1028 — Software reviews and audits
- CMMI-DEV — REQM, CM
- [PMBOK (PMI)](https://www.pmi.org) — WBS, risk register, assumptions log
- [Scrum Guide](https://scrumguides.org) — Schwaber & Sutherland
- [C4 Model](https://c4model.com) — Simon Brown
- [MADR](https://adr.github.io/madr/) e [adr-tools](https://github.com/npryce/adr-tools)
- [arc42](https://arc42.org)
- [Gherkin reference](https://cucumber.io/docs/gherkin/reference/) e [gherkin-languages.json](https://github.com/cucumber/gherkin/blob/main/gherkin-languages.json)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) e [Design Tokens CG](https://www.w3.org/community/design-tokens/) — W3C
- [OWASP Top 10](https://owasp.org/Top10/) · [CWE](https://cwe.mitre.org) · [SLSA](https://slsa.dev) · NIST SP 800-218 · [NIST RBAC](https://csrc.nist.gov/projects/role-based-access-control)
- [Google Engineering Practices](https://google.github.io/eng-practices/review/) · [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [Microsoft Cloud Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/) · [Azure Boards Scrum process](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/scrum-process)
- [microservices.io](https://microservices.io) — Chris Richardson
- [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com) — Hohpe & Woolf
- [The Twelve-Factor App](https://12factor.net) · [Continuous Delivery](https://continuousdelivery.com) · [DORA](https://dora.dev) · [Team Topologies](https://teamtopologies.com)
- [Conventional Comments](https://conventionalcomments.org/) · [Conventional Commits](https://www.conventionalcommits.org)
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) — HTTP Semantics
- [LGPD — Lei 13.709/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [GitHub Spec Kit](https://github.com/github/spec-kit) · [AWS Kiro](https://kiro.dev)
- [Anthropic — Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills) e [Settings](https://docs.claude.com/en/docs/claude-code/settings) · [Model Context Protocol](https://modelcontextprotocol.io)
- [Mermaid](https://mermaid.js.org) · [xUnit Test Patterns](https://xunitpatterns.com) · [Testcontainers](https://testcontainers.com) · [Prometheus naming practices](https://prometheus.io/docs/practices/naming/) · [OpenTelemetry](https://opentelemetry.io)

### Referência declarada no README

- **Elemar Júnior** — *Manual do Arquiteto de Software*. Filosofia arquitetural: decisão contextual em vez de padrão universal, e ceticismo com adoção por moda.

---

## Correções e contribuições

Se alguma atribuição aqui estiver errada, incompleta ou injusta com o autor original, abra uma issue. Crédito mal dado é pior que crédito ausente.
