# Leanwork SDD Plugin

Pipeline **Spec-Driven Development** para projetos Leanwork. Empacota arquitetura, levantamento de requisitos, planejamento técnico e code review em quatro skills coordenadas, com templates segregados em arquivos de referência, comandos de orquestração e rastreabilidade cruzada por IDs.

## Estrutura

```
leanwork-sdd/
├── .claude-plugin/
│   └── plugin.json
├── README.md
├── commands/
│   ├── leanwork-start.md           # /leanwork-start
│   ├── leanwork-next.md            # /leanwork-next
│   ├── leanwork-trace.md           # /leanwork-trace
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
└── templates/                       # convenções compartilhadas
    ├── id-conventions.md
    ├── folder-conventions.md
    └── pipeline-example.md
```

### Por que templates em arquivos separados?

Padrão **progressive disclosure** do Claude Code: a SKILL.md fica curta (instrução do "como conduzir a conversa"), e os templates grandes ficam em `references/`, carregados pelo agente apenas quando vai gerar o documento. Vantagens:

- **Menos tokens em contexto** quando a skill está só "ativa" mas ainda em fase de entrevista
- **Templates versionáveis isoladamente** — você ajusta o `proposal-template.md` sem mexer na lógica da skill
- **Templates reutilizáveis fora do plugin** — devs podem copiar `references/proposal-template.md` direto para um repositório e usar manualmente
- **Convenções compartilhadas centralizadas** em `templates/` na raiz (IDs, pastas, exemplo end-to-end)

## O que vem dentro

### Skills

| Skill | Fase | Entrada | Saída | IDs que produz |
|-------|------|---------|-------|----------------|
| `architect-leanwork` | 1 — Arquitetura | Briefing de negócio | Proposta arquitetural + ADRs + C4 | `ADR-XX` |
| `prd-leanwork` | 2 — Requisitos | Demanda (com ou sem arquitetura) | PRD com regras + Gherkin | `RN-XX`, `CA-XX` |
| `planner-leanwork` | 3 — Plano | PRD aprovado | Plano com tarefas executáveis | `T-XX` |
| `reviewer-leanwork` | 5 — Review | Diff/PR + plano + PRD + arquitetura | Relatório de review por tarefa | `R-XX` |
| `context-leanwork` | Transversal | Artefatos do pipeline + repositório | `CLAUDE.md` raiz e módulos | — |

Todas as skills são **stack-agnósticas**. A stack vem da decisão arquitetural e do `CLAUDE.md` do projeto, nunca da skill.

### Comandos

| Comando | O que faz |
|---------|-----------|
| `/leanwork-start` | Inicia o pipeline e identifica em que fase começar |
| `/leanwork-next` | Inspeciona artefatos existentes e sugere a próxima ação (incluindo reviews pendentes) |
| `/leanwork-review` | Invoca `reviewer-leanwork` sobre uma tarefa específica |
| `/leanwork-trace` | Gera a matriz de rastreabilidade `ADR ↔ RN ↔ CA ↔ T ↔ R` e aponta gaps |
| `/leanwork-context` | Gera ou atualiza `CLAUDE.md` (raiz e módulos). Nunca automático, nunca destrutivo |

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

**planner-leanwork/references/**
- `plan-template.md` — template completo do plano com fases e estrutura de tarefa
- `task-examples.md` — 5 exemplos de tarefas + guia de granularidade

**reviewer-leanwork/references/**
- `review-template.md` — template completo do relatório de review
- `review-checklist.md` — perguntas-guia detalhadas por eixo + tabela de severidade
- `stack-detection.md` — cascata de descoberta da stack do projeto

**prototype-leanwork/references/**
- `spec-ui-template.md` — template do documento SPEC-UI
- `ingestion-guide.md` — extração por formato (HTML, imagens, Figma via MCP, Lovable/v0)
- `generation-guide.md` — arquétipos de interface, entrevista e delegação do craft visual
- `screen-states.md` — catálogo de estados de tela e quais são obrigatórios por tipo

**context-leanwork/references/**
- `claude-md-root-template.md` — template do `CLAUDE.md` da raiz
- `claude-md-module-template.md` — template do `CLAUDE.md` de módulo
- `command-detection.md` — como detectar comandos reais de build/test por ecossistema
- `permission-catalog.md` — receitas de `allow`/`ask`/`deny` por ecossistema

### Convenções compartilhadas (raiz `templates/`)

- `id-conventions.md` — como numerar `ADR-XX`, `RN-XX`, `CA-XX`, `T-XX`, `R-XX`, regras de revogação, convenção de nome de teste
- `folder-conventions.md` — estrutura `docs/architecture/`, `docs/prds/`, `docs/plans/`, `docs/reviews/`, `docs/traceability/`, mais variantes para mono-repo
- `pipeline-example.md` — exemplo end-to-end completo (Ofertas Relâmpago da Ultrafarma)

## A ideia central — rastreabilidade cruzada completa

```
ADR-002 (arquitetura: lock pessimista para estoque)
   ↓ justifica
RN-05 (PRD: estoque decrementado atomicamente)
   ↓ valida em
CA-01 (PRD: Cenário Gherkin de compra com sucesso)
   ↓ implementado em
T-07 (plano: handler de compra em flash sale)
   ↓ validado por
R-XX (review: findings da implementação de T-07)
   ↓ verificado por
Teste CA_01_compra_com_sucesso (código)
```

Cada artefato declara seus elos explicitamente:

- **Proposta arquitetural**: `ADR-001`, `ADR-002`, ... numerados, sem reúso
- **PRD**: cenários começam com `Cenário [CA-01]: ...`, passos citam `(RN-XX)` e `(ADR-XX)`
- **Plano**: cada tarefa preenche `**Implementa:** RN-XX`, `**Valida:** CA-XX`, `**Decisões base:** ADR-XX`
- **Review**: cada finding `R-XX` cita o eixo e as referências cruzadas (RN/CA/ADR) afetadas

O `/leanwork-trace` percorre todos esses elos e monta a matriz completa, incluindo estado de execução e status de review por tarefa.

## A skill `reviewer-leanwork` em detalhe

### Filosofia

- **Stack-agnóstica.** Detecta a stack do projeto via cascata (proposta arquitetural → `CLAUDE.md` → inspeção de repo → pergunta). Não vem pronta para .NET ou qualquer outra stack.
- **Honesta, sem complacência.** Aponta problemas reais com evidência. Não confunde gentileza com qualidade.
- **Baseada em evidência.** Cada finding cita arquivo e linha. Sem "achismos".
- **Calibrada por severidade.** `Bloqueante` (merge negado), `Importante` (resolver agora ou na próxima), `Sugestão` (opcional).

### Os 5 eixos de avaliação

1. **Aderência ao plano** — a tarefa T-XX foi entregue como prometida?
2. **Rastreabilidade** — commits, testes e código preservam os IDs?
3. **Aderência ao spec** — cada RN listada em `Implementa:` foi concretizada? Cada CA em `Valida:` tem teste? ADR em `Decisões base:` foi respeitada?
4. **Cobertura de teste** — testes prometidos foram criados? Casos de borda cobertos?
5. **Qualidade do código** — princípios universais + padrões específicos lidos do `CLAUDE.md` do projeto.

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

As quatro skills do pipeline produzem documentos escritos **para humanos**. O `CLAUDE.md` é a ponte para o agente: o que ele precisa saber em toda sessão sem reler 400 linhas de proposta arquitetural.

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
  → planner → T-01..T-12

[dev/agente executa T-04]
  → /leanwork-review T-04
  → reviewer → REVIEW-T-04-2026-06-15.md (R-01..R-03)

[após correções]
  → /leanwork-review T-04
  → reviewer → REVIEW-T-04-2026-06-17-round2.md
```

### Retomar trabalho

```
/leanwork-next
  → identifica que T-04 está Done mas sem review
  → sugere: "rodar /leanwork-review T-04 antes de avançar"
```

### Auditar rastreabilidade completa

```
/leanwork-trace docs/prds/PRD-001-flash-sales.md
  → gera matriz ADR ↔ RN ↔ CA ↔ T ↔ R
  → aponta:
    - T-04 marcada como Done mas review pendente
    - T-05 com review Bloqueado em aberto
    - CA-09 sem tarefa que valide
    - ADR-003 nunca referenciado
```

## Filosofia geral

- **SDD pragmático, não ortodoxo.** Adaptamos princípios do Spec Kit / Kiro para o contexto Leanwork: Azure DevOps (Epic→Feature→PBI), Gherkin em PT-BR, agentes de IA (Claude Code, Codex, Cursor) como executores naturais.
- **Português é padrão.** Todos os artefatos saem em PT-BR. Termos técnicos consagrados podem ficar em inglês.
- **IA-friendly por design.** Cada artefato é otimizado para ser consumido por agente de IA, com IDs estáveis, pontos de validação humana explícitos e critérios de aceite testáveis.
- **Sem cronograma, sem estimativa.** O pipeline produz "o quê", "por quê" e "em que ordem". "Quando" e "quanto" são responsabilidade do planejamento de sprint.
- **Stack-agnóstico onde dá.** Nenhuma das 4 skills traz tecnologia pré-definida. Stack vem do projeto.
- **Progressive disclosure.** SKILL.md curta = conversa e direção. References carregadas sob demanda = templates e catálogos.

## Instalação

```bash
# Local (desenvolvimento):
claude --plugin-dir /caminho/para/leanwork-sdd

# Marketplace (se você publicar):
claude plugin install leanwork-sdd
```

Depois de instalar, abrir o Claude Code e rodar `/plugin` para confirmar que as skills foram carregadas. As 4 skills aparecem com prefixo `(leanwork-sdd)` quando autoinvocadas.

## Versionamento

- `1.0.0` — três skills (architect, prd, planner) + três comandos + rastreabilidade ADR/RN/CA/T + templates segregados
- `1.1.0` — adição da skill `reviewer-leanwork` + comando `/leanwork-review` + extensão de `/leanwork-trace` e `/leanwork-next` para considerar reviews + rastreabilidade estendida com `R-XX`
- `1.2.0` — adição da skill `context-leanwork` + comando `/leanwork-context` para gerar `CLAUDE.md` (raiz e módulos). Sempre opt-in: `architect-leanwork`, `reviewer-leanwork` e `/leanwork-next` apenas sugerem, nunca geram automaticamente

## Crédito e inspiração

Pipeline desenhado por Mick Banagouro (Leanwork). Princípios SDD inspirados em GitHub Spec Kit e Amazon Kiro. Filosofia arquitetural inspirada no Manual do Arquiteto de Software de Elemar Júnior.
