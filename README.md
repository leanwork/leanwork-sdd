# Leanwork SDD Plugin

Pipeline **Spec-Driven Development** para projetos Leanwork. Empacota arquitetura, levantamento de requisitos, especificação de interface, planejamento técnico, execução guiada e code review em seis skills coordenadas, com templates segregados em arquivos de referência, comandos de orquestração e rastreabilidade cruzada por IDs.

```
1. Architect  →  2. PRD  →  3. Protótipo*  →  4. Planner  →  5. Execução  ⇄  6. Review
                                                             └─ uma tarefa por ciclo ─┘

context-leanwork — transversal ao pipeline inteiro, sempre opt-in

* opcional — só para PRDs com interface
```

A execução é uma fase do pipeline, não um intervalo entre fases. `/leanwork-execute` pega uma tarefa por vez, carrega o contexto que o plano declarou (`RN` / `CA` / `ADR` / `UI`) e devolve o estado ao plano; `/leanwork-review` valida e, se bloquear, devolve o bloqueio ao plano também. Os dois se alternam tarefa a tarefa até o plano fechar — e o plano é o único lugar onde o estado de execução vive.

## Estrutura

```
leanwork-sdd/
├── .claude-plugin/
│   └── plugin.json
├── README.md
├── REFERENCES.md                   # fontes de engenharia por trás de cada fase
├── commands/
│   ├── leanwork-start.md           # /leanwork-start
│   ├── leanwork-next.md            # /leanwork-next
│   ├── leanwork-trace.md           # /leanwork-trace
│   ├── leanwork-execute.md         # /leanwork-execute
│   ├── leanwork-review.md          # /leanwork-review
│   ├── leanwork-context.md         # /leanwork-context
│   └── leanwork-prototype.md       # /leanwork-prototype
├── skills/
│   ├── architect-leanwork/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── proposal-template.md
│   │       ├── adr-template.md
│   │       ├── c4-mermaid-templates.md
│   │       ├── quality-attributes.md
│   │       └── architectural-styles.md
│   ├── prd-leanwork/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── prd-template.md
│   │       └── gherkin-examples.md
│   ├── prototype-leanwork/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── spec-ui-template.md
│   │       ├── ingestion-guide.md
│   │       ├── generation-guide.md
│   │       └── screen-states.md
│   ├── planner-leanwork/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── plan-template.md
│   │       └── task-examples.md
│   ├── reviewer-leanwork/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── review-template.md
│   │       ├── review-checklist.md
│   │       └── stack-detection.md
│   └── context-leanwork/
│       ├── SKILL.md
│       └── references/
│           ├── claude-md-root-template.md
│           ├── claude-md-module-template.md
│           ├── command-detection.md
│           └── permission-catalog.md
├── templates/                       # convenções compartilhadas, stack-agnósticas
│   ├── id-conventions.md
│   └── folder-conventions.md
└── stacks/                          # exemplos calibrados por stack (ver stacks/README.md)
    └── dotnet/
        ├── pipeline-example.md
        ├── task-examples.md
        └── c4-component-example.md
```

### Por que templates em arquivos separados?

Padrão **progressive disclosure** do Claude Code: a SKILL.md fica curta (instrução do "como conduzir a conversa"), e os templates grandes ficam em `references/`, carregados pelo agente apenas quando vai gerar o documento. Vantagens:

- **Menos tokens em contexto** quando a skill está só "ativa" mas ainda em fase de entrevista
- **Templates versionáveis isoladamente** — você ajusta o `proposal-template.md` sem mexer na lógica da skill
- **Templates reutilizáveis fora do plugin** — devs podem copiar `references/proposal-template.md` direto para um repositório e usar manualmente
- **Convenções compartilhadas centralizadas** em `templates/` na raiz (IDs, pastas) — sempre stack-agnósticas
- **Exemplos calibrados por stack isolados** em `stacks/` — quem quer ver código real de uma stack específica sabe onde procurar, sem misturar com o núcleo agnóstico

## O que vem dentro

### Skills

| Skill | Fase | Entrada | Saída | IDs que produz |
|-------|------|---------|-------|----------------|
| `architect-leanwork` | 1 — Arquitetura | Briefing de negócio | Proposta arquitetural + ADRs + C4 | `ADR-XX` |
| `prd-leanwork` | 2 — Requisitos | Demanda (com ou sem arquitetura) | PRD com regras + Gherkin | `RN-XX`, `CA-XX` |
| `prototype-leanwork` | 3 — Interface *(opcional)* | PRD com interface + protótipo (se houver) | SPEC-UI com telas e estados | `UI-XX`, `UI-XX.estado` |
| `planner-leanwork` | 4 — Plano | PRD aprovado (+ SPEC-UI, se houver) | Plano com tarefas executáveis | `T-XX` |
| `reviewer-leanwork` | 5 — Review | Diff/PR + plano + PRD + arquitetura + SPEC-UI | Relatório de review por tarefa | `R-XX` |
| `context-leanwork` | Transversal | Artefatos do pipeline + repositório | `CLAUDE.md` raiz e módulos, `settings.json` | — |

Todas as skills são **stack-agnósticas**. A stack vem da decisão arquitetural e do `CLAUDE.md` do projeto, nunca da skill. A fase 3 é ainda **design-agnóstica**: decide quais telas e estados existem, e delega o craft visual para skills de frontend do ambiente.

### Comandos

| Comando | O que faz |
|---------|-----------|
| `/leanwork-start` | Inicia o pipeline e identifica em que fase começar |
| `/leanwork-next` | Inspeciona artefatos existentes e sugere a próxima ação (incluindo reviews pendentes) |
| `/leanwork-prototype` | Invoca `prototype-leanwork`: indexa protótipo existente ou gera um, e produz a SPEC-UI |
| `/leanwork-execute` | Executa uma tarefa do plano carregando o contexto declarado (RN/CA/ADR/UI) e atualiza o `Status` ao final |
| `/leanwork-review` | Invoca `reviewer-leanwork` sobre uma tarefa específica. Finding bloqueante volta como `Status: Bloqueado` no plano |
| `/leanwork-trace` | Gera a matriz de rastreabilidade `ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R` e aponta gaps |
| `/leanwork-context` | Gera ou atualiza `CLAUDE.md` (raiz e módulos) e `.claude/settings.json`. Nunca automático, nunca destrutivo |

### Templates de referência (skill-specific)

**architect-leanwork/references/**
- `proposal-template.md` — template completo da proposta arquitetural
- `adr-template.md` — template standalone de ADR
- `c4-mermaid-templates.md` — diagramas C4 em Mermaid para os 4 níveis + sequence + state
- `quality-attributes.md` — catálogo de 7 atributos de qualidade
- `architectural-styles.md` — catálogo de 10 estilos arquiteturais

**prd-leanwork/references/**
- `prd-template.md` — template completo do PRD com 17 seções
- `gherkin-examples.md` — 5 exemplos calibrados de Gherkin com IDs cruzados

**prototype-leanwork/references/**
- `spec-ui-template.md` — template do documento SPEC-UI
- `ingestion-guide.md` — extração por formato (HTML, imagens, Figma via MCP, Lovable/v0)
- `generation-guide.md` — arquétipos de interface, entrevista e delegação do craft visual
- `screen-states.md` — catálogo de estados de tela e quais são obrigatórios por tipo

**planner-leanwork/references/**
- `plan-template.md` — template completo do plano com fases e estrutura de tarefa
- `task-examples.md` — 6 exemplos de tarefas (pseudocódigo agnóstico) + guia de granularidade; versão com código real em .NET em `stacks/dotnet/task-examples.md`

**reviewer-leanwork/references/**
- `review-template.md` — template completo do relatório de review
- `review-checklist.md` — perguntas-guia detalhadas pelos 6 eixos + tabela de severidade
- `stack-detection.md` — cascata de descoberta da stack do projeto

**context-leanwork/references/**
- `claude-md-root-template.md` — template do `CLAUDE.md` da raiz
- `claude-md-module-template.md` — template do `CLAUDE.md` de módulo
- `command-detection.md` — como detectar comandos reais de build/test por ecossistema
- `permission-catalog.md` — receitas de `allow`/`ask`/`deny` por ecossistema

### Convenções compartilhadas (raiz `templates/`)

- `id-conventions.md` — como numerar `ADR-XX`, `RN-XX`, `CA-XX`, `UI-XX`, `T-XX`, `R-XX`, sufixo de estado (`UI-02.erro`), regras de revogação, convenção de nome de teste
- `folder-conventions.md` — estrutura `docs/architecture/`, `docs/prds/`, `docs/prototype/`, `docs/plans/`, `docs/reviews/`, `docs/traceability/`, mais variantes para mono-repo

> **Regra de manutenção.** `templates/` descreve o pipeline inteiro, então toda skill nova ou fase nova obriga uma varredura dos dois arquivos antes do release. A contagem de skills e as colunas da matriz são os pontos que envelhecem primeiro.

### Exemplos calibrados por stack (raiz `stacks/`)

`templates/` e `references/` são stack-agnósticos por convenção — pseudocódigo, nomes de padrão genéricos, placeholders entre colchetes. Quem quer ver a mesma convenção com código real de uma stack específica encontra em `stacks/<nome-da-stack>/`. Ver [`stacks/README.md`](stacks/README.md) para a convenção completa.

- `stacks/dotnet/pipeline-example.md` — exemplo end-to-end completo (Ofertas Relâmpago da Contoso), calibrado em .NET: a mesma demanda atravessando os cinco artefatos — proposta arquitetural, PRD, SPEC-UI, plano e relatório de review — com os IDs cruzados preenchidos. As cinco skills que produzem artefato apontam para ele em "Recursos auxiliares"
- `stacks/dotnet/task-examples.md` — os 6 exemplos de tarefas de `planner-leanwork/references/task-examples.md` com código real em .NET (MediatR, EF Core, xUnit, FluentValidation, LaunchDarkly, Serilog)
- `stacks/dotnet/c4-component-example.md` — o diagrama C4 Nível 3 de `architect-leanwork/references/c4-mermaid-templates.md` com uma Clean/Onion Architecture real em .NET, marcado como um exemplo entre vários — não recomendação de estilo

### Documentação de referência

- [`REFERENCES.md`](REFERENCES.md) — a base de engenharia de software por trás de cada fase, marcando o que é reprodução, adaptação ou contribuição própria, mais as divergências deliberadas com a literatura e as lacunas conhecidas

## A ideia central — rastreabilidade cruzada completa

```
ADR-002 (arquitetura: lock pessimista para estoque)
   ↓ justifica
RN-05 (PRD: estoque decrementado atomicamente)
   ↓ valida em
CA-06 (PRD: Cenário Gherkin de estoque esgotando durante compras concorrentes)
   ↓ acontece em
UI-02.esgotado (SPEC-UI: estado da tela de confirmação)   ← opcional
   ↓ implementado em
T-07 (plano: handler de compra em flash sale)
   ↓ validado por
R-XX (review: findings da implementação de T-07)
   ↓ verificado por
Teste CA_06_estoque_esgota_durante_compra (código)
```

Cada artefato declara seus elos explicitamente:

- **Proposta arquitetural**: `ADR-001`, `ADR-002`, ... numerados, sem reúso
- **PRD**: cenários começam com `Cenário [CA-01]: ...`, passos citam `(RN-XX)` e `(ADR-XX)`
- **SPEC-UI**: cada tela `UI-XX` mapeia as `RN-XX` e `CA-XX` que manifesta, e cada estado ganha sufixo (`UI-02.esgotado`)
- **Plano**: cada tarefa preenche `**Implementa:** RN-XX`, `**Valida:** CA-XX`, `**Decisões base:** ADR-XX` e, em tarefas de interface, `**Telas:** UI-XX (estados)`
- **Review**: cada finding `R-XX` cita o eixo e as referências cruzadas (RN/CA/UI/ADR) afetadas

O `/leanwork-trace` percorre todos esses elos e monta a matriz completa, incluindo estado de execução e status de review por tarefa.

## A skill `reviewer-leanwork` em detalhe

### Filosofia

- **Stack-agnóstica.** Detecta a stack do projeto via cascata (proposta arquitetural → `CLAUDE.md` → inspeção de repo → pergunta). Não vem pronta para .NET ou qualquer outra stack.
- **Honesta, sem complacência.** Aponta problemas reais com evidência. Não confunde gentileza com qualidade.
- **Baseada em evidência.** Cada finding cita arquivo e linha. Sem "achismos".
- **Calibrada por severidade.** `Bloqueante` (merge negado), `Importante` (resolver agora ou na próxima), `Sugestão` (opcional).

### Os 6 eixos de avaliação

Os eixos 1 a 5 aplicam sempre. O eixo 6 só entra quando o projeto tem SPEC-UI e a tarefa é de interface.

1. **Aderência ao plano** — a tarefa T-XX foi entregue como prometida?
2. **Rastreabilidade** — commits, testes e código preservam os IDs?
3. **Aderência ao spec** — cada RN listada em `Implementa:` foi concretizada? Cada CA em `Valida:` tem teste? ADR em `Decisões base:` foi respeitada?
4. **Cobertura de teste** — testes prometidos foram criados? Casos de borda cobertos?
5. **Qualidade do código** — princípios universais + padrões específicos lidos do `CLAUDE.md` do projeto.
6. **Conformidade de interface** *(condicional)* — todos os estados listados em `Telas:` existem no código? Componentes reutilizáveis foram consumidos ou reimplementados? **Estrutura, estados e comportamento — nunca estética.** Estado ausente é Bloqueante; detalhe visual não vira finding.

### O reviewer não faz

- Code review de formatação (linter cobre)
- Threat modeling completo (segurança básica apenas)
- Otimização de performance se não foi atributo prioritário
- Imposição de preferências pessoais não declaradas no projeto

## A skill `prototype-leanwork` — interface como especificação

Protótipo tem dois papéis: **descoberta** (desenhar para entender o problema, descartável) e **especificação** (as telas são o contrato que o dev implementa). Esta skill trata do segundo — e por isso o protótipo vira artefato do pipeline, com ID e rastreabilidade, não insumo externo solto.

### Ingestão primeiro, geração como fallback

Se você já prototipa, a skill **não substitui** seu processo. Ela indexa o que existe:

| Formato | Qualidade da extração |
|---|---|
| HTML/React no repositório | Alta — rotas, componentes, campos, estados no código |
| Imagens (PNG/screenshots) | Média — layout, campos, cores aproximadas |
| Figma via MCP | Alta — frames, variantes, tokens exatos |
| Lovable/v0 exportado para GitHub | Alta — idêntico ao caso HTML/React |

O modo geração existe para quando não há protótipo: deriva telas e estados do PRD, herda tokens já presentes no repositório e **delega o craft visual** para skills de frontend do ambiente. O plugin fica design-agnóstico do mesmo jeito que é stack-agnóstico.

### O valor está nos estados

Protótipo cobre o caminho feliz. A maioria dos bugs de interface nasce nos estados que ninguém desenhou — vazio por filtro, erro de envio que perde os dados digitados, conflito de edição concorrente, sessão expirada no meio do fluxo.

A skill percorre os cenários Gherkin do PRD: todo `CA-XX` cujo `Então` descreve rejeição ou mensagem de erro corresponde a um estado de tela. Cada estado ganha ID (`UI-02.esgotado`), o plano declara quais implementa, e o review verifica um a um.

### Opcional de verdade

Projeto sem interface — API, worker, CLI, biblioteca — pula a fase inteira, e o `/leanwork-trace` não reclama de ausência. A SPEC-UI é **por PRD**, não por projeto: `PRD-001` (checkout) pode ter especificação de telas enquanto `PRD-002` (job de sincronização) não tem nenhuma.

## A skill `context-leanwork` — contexto para o agente

As cinco skills do pipeline produzem documentos escritos **para humanos**. O `CLAUDE.md` é a ponte para o agente: o que ele precisa saber em toda sessão sem reler 400 linhas de proposta arquitetural.

### Sempre opt-in

Nenhuma skill gera `CLAUDE.md` automaticamente. O arquivo é território do dev — sobrescrever sem pedir queima confiança. As outras partes do pipeline apenas **sugerem** quando faz sentido:

| Momento | Quem sugere |
|---------|-------------|
| Proposta arquitetural concluída | `architect-leanwork` |
| Review rodou degradado por falta de `CLAUDE.md` | `reviewer-leanwork` |
| Review detectou padrão emergente não documentado | `reviewer-leanwork` |
| Projeto tem artefatos do pipeline mas nenhum `CLAUDE.md` | `/leanwork-next` |
| Módulo novo apareceu no repositório | `/leanwork-next` |

### Nunca destrutiva

Blocos delimitados por `<!-- leanwork-context:start -->` e `<!-- leanwork-context:end -->` são os únicos que a skill atualiza. Tudo fora deles é preservado. Arquivo escrito 100% à mão (sem marcadores) nunca é sobrescrito — a skill propõe alternativas e deixa a decisão com o usuário. Diff sempre mostrado antes de gravar.

### Comandos vêm de inspeção real

A seção **Comandos** é a única sem fonte nos artefatos do pipeline. A skill extrai de `package.json`, `Makefile`, `.csproj`, `pyproject.toml`, `go.mod` e afins — nunca inventa. Sem comando de teste no repo, o resultado é um TODO explícito, não um `dotnet test` chutado.

### Permissões também saem daqui

`/leanwork-context permissoes` gera um `.claude/settings.json` calibrado pela stack detectada — os comandos reais de build e teste já entram no `allow`. A classificação em `allow` / `ask` / `deny` segue reversibilidade e blast radius: leitura ou operação local reversível libera; altera estado externo mas recuperável pergunta; irreversível, destrutivo ou que expõe segredo bloqueia.

Lista `ask` grande demais é contraproducente — treina o dev a aprovar no automático e anula a proteção. Sempre em `.claude/settings.json` versionado: é política do time, não preferência pessoal.

### Módulos são opt-in

Projeto LMA com 8 módulos renderia 8 arquivos, vários deles ruído. A skill detecta, lista e deixa o usuário escolher. Módulo que ficaria com menos de ~15 linhas úteis recebe recomendação de não criar.

### Raiz e módulo não se repetem

Módulo nunca repete stack nem comandos globais — só responsabilidade, domínio, boundaries e convenções que **divergem** do padrão da raiz. Duplicação vira divergência silenciosa em poucas semanas.

## Fluxo típico

### Projeto novo (greenfield)

```
/leanwork-start "Sistema de gestão de tickets multi-tenant"
  → architect → ADR-001..ADR-005
  → prd → RN-01..RN-08, CA-01..CA-15
  → /leanwork-prototype → UI-01..UI-06 + estados   (opcional — tem interface)
  → planner → T-01..T-12

/leanwork-execute T-04
  → carrega RN-03, RN-05, CA-01, CA-03, ADR-002, UI-02 (default, esgotado)
  → implementa, escreve CA_01_* e CA_03_*, roda os testes
  → T-04: Status Concluído + linha no Histórico

  → /leanwork-review T-04
  → reviewer → REVIEW-T-04-2026-06-15.md (R-01..R-03, 1 Bloqueante)
  → T-04 volta para Status: Bloqueado no plano

[após correções]
  → /leanwork-review T-04
  → reviewer → REVIEW-T-04-2026-06-17-round2.md
```

### Retomar trabalho

```
/leanwork-next
  → identifica que T-04 está Concluído mas sem review
  → sugere: "rodar /leanwork-review T-04 antes de avançar"
```

### Auditar rastreabilidade completa

```
/leanwork-trace docs/prds/PRD-001-flash-sales.md
  → gera matriz ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R
  → aponta:
    - T-04 com Status: Concluído mas review pendente
    - T-05 com review Bloqueado em aberto
    - CA-09 sem tarefa que valide
    - UI-03.erroEnvio especificado mas nenhuma tarefa declara em Telas:
    - ADR-003 nunca referenciado
```

Sem SPEC-UI no projeto, as colunas de UI são omitidas da matriz — ausência não vira gap.

## Filosofia geral

- **SDD pragmático, não ortodoxo.** Adaptamos princípios do Spec Kit / Kiro para o contexto Leanwork: Azure DevOps (Epic→Feature→PBI), Gherkin em PT-BR, agentes de IA (Claude Code, Codex, Cursor) como executores naturais.
- **Português é padrão.** Todos os artefatos saem em PT-BR. Termos técnicos consagrados podem ficar em inglês.
- **IA-friendly por design.** Cada artefato é otimizado para ser consumido por agente de IA, com IDs estáveis, pontos de validação humana explícitos e critérios de aceite testáveis.
- **Sem cronograma, sem estimativa.** O pipeline produz "o quê", "por quê" e "em que ordem". "Quando" e "quanto" são responsabilidade do planejamento de sprint.
- **Stack-agnóstico no núcleo.** Nenhuma skill traz tecnologia pré-definida, e `templates/`/`references/` usam pseudocódigo. Stack vem do projeto — e design vem das skills de frontend do ambiente. Exemplos com código real de uma stack específica ficam isolados em `stacks/` (ver `stacks/README.md`), nunca misturados ao núcleo.
- **Progressive disclosure.** SKILL.md curta = conversa e direção. References carregadas sob demanda = templates e catálogos.
- **Lacuna declarada vale mais que lacuna preenchida.** Nenhuma skill inventa para fechar matriz, e toda informação gerada declara a origem. Matriz honestamente incompleta é informação; matriz fechada com suposição é armadilha.
- **Fontes na mesa.** O [`REFERENCES.md`](REFERENCES.md) credita a literatura por trás de cada fase e registra onde o pipeline diverge dela de propósito.

## Instalação

O plugin é distribuído internamente: o próprio repositório é o marketplace, adicionado por caminho local. Não há publicação pública, e nada aqui depende de rede além do `git clone`.

**Uso permanente (equipe):**

```bash
git clone https://github.com/leanwork/leanwork-sdd.git
claude plugin marketplace add ./leanwork-sdd
claude plugin install leanwork-sdd@leanwork
```

O `install` usa a sintaxe `plugin@marketplace`: `leanwork-sdd` é o nome do plugin e `leanwork` é o nome do marketplace. Para atualizar depois de um `git pull`, rodar `claude plugin marketplace update leanwork`.

**Desenvolvimento do próprio plugin:**

```bash
claude --plugin-dir /caminho/para/leanwork-sdd
```

> A flag `--plugin-dir` carrega o plugin direto do diretório, sem instalar — conveniente para editar uma skill e testar na hora. Ela **vale apenas pela sessão atual**: ao reabrir o Claude Code é preciso repassá-la. Para a instalação que persiste, usar o caminho de marketplace acima.

Depois de instalar, abrir o Claude Code e rodar `/plugin` para confirmar que as skills foram carregadas. Skill de plugin vive no namespace do plugin, então as 6 também podem ser chamadas direto pela barra — `/leanwork-sdd:prd-leanwork`, `/leanwork-sdd:prototype-leanwork` e assim por diante.

Nenhuma delas usa `disable-model-invocation`: o modelo pode carregá-las quando o pedido do usuário casa com a `description`. É isso que permite a `/leanwork-context` e `/leanwork-prototype` delegarem para a skill correspondente. O opt-in do pipeline é uma promessa de **não rodar sem que o usuário peça ou aceite** — não uma trava de invocação.

## Versionamento

- `1.0.0` — três skills (architect, prd, planner) + três comandos + rastreabilidade ADR/RN/CA/T + templates segregados
- `1.1.0` — adição da skill `reviewer-leanwork` + comando `/leanwork-review` + extensão de `/leanwork-trace` e `/leanwork-next` para considerar reviews + rastreabilidade estendida com `R-XX`
- `1.2.0` — adição da skill `context-leanwork` + comando `/leanwork-context` para gerar `CLAUDE.md` (raiz e módulos). Sempre opt-in: `architect-leanwork`, `reviewer-leanwork` e `/leanwork-next` apenas sugerem, nunca geram automaticamente
- `1.3.0` — geração de permissões: `.claude/settings.json` calibrado pela stack via `/leanwork-context permissoes`, com o catálogo `allow`/`ask`/`deny` por ecossistema e detecção de drift entre o `CLAUDE.md` e a realidade do repositório
- `1.4.0` — adição da skill `prototype-leanwork` + comando `/leanwork-prototype`: protótipo vira especificação rastreável (SPEC-UI) com `UI-XX` e estados. Rastreabilidade estendida para `ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R`, novo eixo 6 no reviewer, campo `Telas:` no plano. Fase opcional — projeto sem interface pula inteira e o `/leanwork-trace` não reclama
- `1.5.0` — adição do `REFERENCES.md`: as fontes de engenharia de software por trás de cada fase, com marcação de reprodução/adaptação/autoria, divergências deliberadas com a literatura e lacunas conhecidas. README realinhado ao pipeline de seis skills
- `1.6.0` — a execução ganha dono: novo comando `/leanwork-execute`, que carrega o contexto declarado pela tarefa e devolve o estado ao plano. Vocabulário de status unificado (`Pendente` / `Em andamento` / `Concluído` / `Bloqueado`) como contrato entre o plano e os comandos que o leem. Review passa a fechar o loop — finding Bloqueante volta como `Status: Bloqueado` na tarefa — e o re-review de round N+1 entra no fluxo principal. Instalação por marketplace local
- `1.6.1` — catálogo de permissões corrigido na semântica de casamento do `Bash`: o `:*` equivale a ` *` e o espaço faz parte da regra, o que torna toda regra de prefixo dependente da ordem dos argumentos. O `deny` de force push passa de uma regra para seis, cobrindo `-f` e a flag depois do remote; `--force-with-lease` segue no `ask`, agora por escrito
- `1.6.2` — a outra metade da mesma mecânica: qual regra decide. A precedência `deny` → `ask` → `allow` ignora especificidade, então regra estreita no `allow` sob regra larga no `ask` é código morto. `Bash(npx tsc:*)` removido da receita de Node, a nota que prescrevia esse padrão reescrita, e o catálogo ganha a seção "Sombra de prefixo entre baldes" com o procedimento de conferência
- `1.6.3` — receita de Docker recalibrada: `docker compose down` sai do `allow` porque `down -v` remove volumes nomeados e anônimos — banco local, seed, fixtures —, e `stop`/`start` cobrem o ciclo cotidiano sem tocar em nada persistente. `docker volume rm` e `docker volume prune` entram no `deny`, rota mais curta para a mesma perda. Fica escrito por que estreitar o `allow` vence tentar negar só a flag, e qual buraco permanece
- `1.6.4` — o plugin passa a calibrar as próprias permissões, não só as dos outros: os 13 comandos e skills declaram `allowed-tools`, cada um pré-aprovando leitura mais a pasta do artefato que ele mesmo produz (`Edit(docs/prds/**)` no PRD, `Edit(docs/reviews/**)` no review, e assim por diante). `Bash` não é pré-autorizado em lugar nenhum, e quem escreve fora de `docs/` — `/leanwork-execute`, que gera código, e `/leanwork-context`, que grava `.claude/settings.json` — continua pedindo confirmação
- `1.6.5` — `templates/` sai da v1.0 e volta a descrever o pipeline que existe. O exemplo end-to-end ganha os dois artefatos que faltavam — SPEC-UI e relatório de review —, mais colunas `UI` e `R` na matriz e um `R-01` que devolve a tarefa para `Bloqueado`. Deixa de ser documentação solta: as cinco skills que produzem artefato passam a apontar para ele. `folder-conventions.md` para de mandar tirar a SPEC-UI de `docs/`, e o sufixo de estado se unifica em `.limiteExcedido`
- `1.6.6` — o opt-in de `prototype-leanwork` e `context-leanwork` passa a dizer o que de fato promete. "Nunca se auto-invoca" usava o termo com sentido diferente do que ele tem no Claude Code, e travar a invocação pelo modelo — o caminho que o campo `disable-model-invocation` abriria — quebraria `/leanwork-prototype` e `/leanwork-context`, que delegam para essas skills. As duas continuam invocáveis; a promessa, agora escrita, é não rodar sem pedido direto ou aceite explícito do usuário
- `1.6.7` — o parâmetro que dimensiona o plano inteiro passa a ter um número só. O tamanho de tarefa aparecia com seis redações em quatro arquivos — 4h, 2h, meio dia, "nunca mais de 1 dia" — e dois planos do mesmo PRD saíam estruturalmente diferentes conforme qual regra o modelo lesse primeiro. Teto único de **30min-4h**, declarado em `templates/id-conventions.md` na regra de `T-XX`, com o planner e os exemplos de tarefa apontando para lá. Fica explícito que a faixa é calibragem mental de quem planeja, não estimativa: ela nunca vira campo do plano, que continua registrando só `Complexidade` qualitativa
- `1.6.8` — o único ponto do pipeline que podia produzir número financeiro por acidente de template deixa de produzi-lo. O sumário executivo da proposta arquitetural pedia "custo e prazo de cara, em ordem de grandeza" enquanto o apêndice do mesmo arquivo já mandava cronograma e estimativa para o planejamento de sprint — e o campo vencia, porque é o que o agente preenche. Agora o sumário só ecoa **restrição declarada pelo cliente**, que é entrada e vive na seção 4; estimativa gerada pela proposta some, e o checklist final passa a barrá-la explicitamente
- `1.6.9` — `R-XX` deixa de ser exceção não declarada. A regra geral de IDs proibia reúso, e a regra de `R-XX` recomeça em `R-01` a cada relatório: a exceção agora está escrita no ponto da regra geral, junto com o motivo — relatórios de review são o único artefato que existe muitas vezes no mesmo projeto. Corrigido o efeito colateral disso na skill de review, que anunciava "as mesmas regras dos demais IDs" e dava exemplo de numeração continuando entre rounds. E o número passa a vir com o arquivo: `R-01 (REVIEW-T-04-2026-06-15)` em todo lugar fora do relatório de origem — plano, matriz do `/leanwork-trace`, sugestão do `/leanwork-next` e conversa
- `1.6.10` — os oito templates de `references/` param de se fechar sozinhos. Cada um envolve o documento-modelo numa cerca de código, e o conteúdo tem blocos `mermaid`, `gherkin`, `bash` e `csharp` na mesma largura de três crases: pelo CommonMark, o primeiro bloco interno encerra o externo. A renderização quebrava no meio do template e o agente que o lê para gerar o artefato precisava adivinhar onde o modelo termina — bem no ponto em que nascem os `CA-XX` do PRD. O envelope passa a quatro crases, e cada template agora diz por escrito que essa cerca é andaime e não entra no documento gerado
- `1.7.0` — três práticas de engenharia entram no pipeline sem skill nova. `planner-leanwork` ganha o padrão **expandir-migrar-contrair** para refactors de alto *blast radius* (renomear coluna, retipar símbolo compartilhado) que não cabem em uma tarefa monolítica de 4h, e uma pergunta de entrevista sobre a **costura de teste** (seam) preferencial antes de quebrar em tarefas. `/leanwork-execute` passa a escrever o teste antes do código de produção na costura, quando praticável, e a rodar typecheck/build antes da suíte — typecheck quebrado bloqueia `Concluído` do mesmo jeito que teste vermelho. Fatiamento vertical por tarefa (tracer bullet) foi avaliado e **não adotado**: o `plan-template.md` fatia por camada técnica de propósito, divergência já registrada em `REFERENCES.md` com justificativa própria — trocar isso exige decisão explícita, não é ganho a implementar de passagem
- `1.8.0` — a divergência de fatiamento horizontal registrada em `REFERENCES.md` ganha exceção seletiva: quando a entrevista do planner sinaliza entrega incremental real (Bloco 2) ou risco de integração concreto (Bloco 4), a fatia vertical passa a valer para a parte afetada do plano — não para o plano inteiro. `planner-leanwork/SKILL.md` ganha a seção "Orientação da fatia" com os dois gatilhos e duas ressalvas (fatia vertical gera mais tarefas, não menos; e carrega contexto de múltiplos projetos por execução na stack de referência em Clean Architecture). `task-examples.md` ganha o Exemplo 6 e uma exceção explícita ao sinal de "mexe em mais de 3 camadas → separar", e `plan-template.md` referencia a alternativa sem substituir o padrão. Horizontal continua default
- `1.9.0` — os exemplos .NET saem do núcleo agnóstico e ganham endereço próprio em `stacks/dotnet/`. `templates/pipeline-example.md` (exemplo end-to-end das cinco fases) muda de lugar inteiro, e as cinco skills que produzem artefato repontam para lá. `task-examples.md` do planner e o diagrama C4 Nível 3 do architect (que usava MediatR/FluentValidation/EF Core numa Clean Architecture completa — a mesma combinação que a skill lista entre os modismos a não adotar por moda) passam a ter versão agnóstica no lugar original e versão calibrada em `stacks/dotnet/`. Placeholders `.NET` soltos em templates de preenchimento (`proposal-template.md`, `prd-template.md`, `plan-template.md`, `claude-md-root-template.md`) viram genéricos. `id-conventions.md` troca o bloco xUnit por pseudocódigo e aponta para a versão .NET. Novo `stacks/README.md` documenta a convenção para futuras stacks

## Crédito e inspiração

Pipeline desenhado por Mick Banagouro (Leanwork). Princípios SDD inspirados em [GitHub Spec Kit](https://github.com/github/spec-kit) e [AWS Kiro](https://kiro.dev). Filosofia arquitetural inspirada no *Manual do Arquiteto de Software* de Elemar Júnior.

Nenhuma fase deste pipeline foi inventada do zero. **[REFERENCES.md](REFERENCES.md)** documenta a base de engenharia de software por trás de cada uma — C4 e ADR na arquitetura, BDD/Gherkin e rastreabilidade ISO 29148 nos requisitos, a UI Stack de Scott Hurff no catálogo de estados de tela, Google Engineering Practices no review, Saltzer & Schroeder no catálogo de permissões — marcando o que é reprodução, o que é adaptação e o que é contribuição própria.

O mesmo documento registra, de propósito, onde o pipeline **diverge** da literatura (fatiamento horizontal contra vertical slice, ID no nome do cenário em vez de tag do Cucumber) e onde ele ainda tem **lacunas** (fitness functions, deployment view, método de threat modeling). Discordar é mais fácil quando a fonte está na mesa.
