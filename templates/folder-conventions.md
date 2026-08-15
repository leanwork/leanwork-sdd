# Convenções de Pasta — Projetos com Pipeline SDD Leanwork

Estrutura recomendada para organizar os artefatos do pipeline dentro de um repositório de projeto.

## Estrutura padrão

```
projeto-x/
├── docs/
│   ├── architecture/
│   │   ├── proposta-arquitetural.md
│   │   └── adrs/                         # opcional, se ADRs viram arquivos separados
│   │       ├── ADR-001-monolito-modular.md
│   │       └── ADR-002-lock-pessimista-estoque.md
│   ├── prds/
│   │   ├── PRD-001-flash-sales.md
│   │   └── PRD-002-checkout-pix.md
│   ├── prototype/
│   │   ├── SPEC-UI-001-flash-sales.md
│   │   └── assets/                       # protótipo HTML, imagens, exports
│   ├── plans/
│   │   ├── PLAN-001-flash-sales.md
│   │   └── PLAN-002-checkout-pix.md
│   ├── reviews/
│   │   ├── REVIEW-T-04-2026-06-15.md
│   │   ├── REVIEW-T-04-2026-06-17-round2.md
│   │   └── REVIEW-T-05-2026-06-16.md
│   └── traceability/                     # gerado pelo /leanwork-trace
│       └── MATRIX-001-flash-sales.md
├── src/
├── tests/
├── CLAUDE.md                             # instrução de leitura do pipeline
└── README.md
```

## Convenções de nomenclatura

### Arquitetura

- **Um arquivo de proposta arquitetural por projeto** (ou por bounded context, se o projeto for grande). Nome: `proposta-arquitetural.md`.
- **ADRs podem ficar inline** no documento principal (seção 5, padrão da skill `architect-leanwork`) **ou como arquivos separados** em `architecture/adrs/`. Para projetos com muitas decisões evolutivas, arquivos separados versionam melhor.
- **Nome de ADR como arquivo**: `ADR-XXX-titulo-em-kebab-case.md` — número com 3 dígitos para permitir até 999 ADRs sem renumeração visual.

### PRDs

- **Um PRD por Epic ou Feature grande**. Nome: `PRD-XXX-tema-em-kebab-case.md`.
- Numeração sequencial global ao projeto, não reinicia por ano ou trimestre.
- Sufixo opcional `-v2`, `-v3` se o PRD passou por revisão estrutural grande (mudança de escopo). Para revisões pequenas, basta atualizar in-place e bumpar a data no cabeçalho.

### Planos

- **Um plano por PRD**, na proporção 1:1. Nome: `PLAN-XXX-tema-em-kebab-case.md` — usar o **mesmo número** do PRD correspondente. Facilita encontrar o par.
- Planos não são reescritos; são atualizados durante a execução (campo `Status` de cada tarefa, tabela de Histórico de execução).

### SPEC-UI (especificação de interface)

- **Um documento por PRD que tenha interface.** Nome: `SPEC-UI-XXX-tema-em-kebab-case.md`, usando **o mesmo número do PRD** correspondente.
- **Opcional por natureza.** PRD de integração, job ou API pura não tem SPEC-UI — e a ausência não é lacuna.
- **Artefatos visuais** (HTML do protótipo, imagens exportadas, código do Lovable/v0) ficam em `docs/prototype/assets/` ou são referenciados por URL quando externos (Figma).
- Diferente do PRD, a SPEC-UI **é regenerável**: quando o protótipo muda, o documento é refeito sem tocar no PRD aprovado.

### Matrizes de rastreabilidade

- **Geradas sob demanda** pelo `/leanwork-trace`, ficam em `docs/traceability/`.
- Nome: `MATRIX-XXX-tema-em-kebab-case.md`, mesmo número do PRD/plano.
- Não são fonte de verdade — são snapshot. Quando o PRD ou plano mudar, a matriz precisa ser regerada.

### Reviews

- **Um relatório por tarefa revisada**. Nome: `REVIEW-T-XX-AAAA-MM-DD.md`.
- Round adicional (re-review após correções) usa sufixo: `REVIEW-T-XX-AAAA-MM-DD-round2.md`.
- Reviews são versionáveis — não são reescritos, são novos arquivos por round.
- A pasta `docs/reviews/` pode ficar pesada ao longo do tempo. Considerar arquivar reviews aprovados de tarefas concluídas há mais de N semanas em `docs/reviews/archive/` para manter foco nos ativos.
- Em projetos com PR review nativo (GitHub, GitLab, Azure DevOps), o relatório do `reviewer-leanwork` pode ser colado como comentário no PR em vez de versionado. Decidir uma política por projeto.

## CLAUDE.md do projeto

Recomenda-se que o projeto tenha um `CLAUDE.md` na raiz indicando ao agente como navegar o pipeline.

> A skill `context-leanwork` gera e mantém esse arquivo (raiz e módulos), detectando stack e comandos reais do repositório. Rode com `/leanwork-context`. A skill nunca é automática nem sobrescreve conteúdo humano — as demais skills do pipeline apenas a sugerem quando faz sentido.

Estrutura mínima do arquivo (a skill produz uma versão mais completa, com Resumo, Stack, Comandos, Convenções e Restrições):

```markdown
# Projeto X — Instruções para agentes de IA

Este projeto usa o pipeline SDD Leanwork. Antes de implementar qualquer feature:

1. Verifique se existe um plano em `docs/plans/PLAN-XXX-*.md`
2. Identifique a próxima tarefa pendente sem bloqueio (campo `Status: Pendente` e `Depende de` satisfeito)
3. Leia a tarefa inteira: campos `Implementa:`, `Valida:`, `Decisões base:`
4. Abra os artefatos referenciados:
   - Para entender as regras: `docs/prds/PRD-XXX.md` (procure os `RN-XX` listados em `Implementa:`)
   - Para entender o critério de aceite: o mesmo PRD (procure `Cenário [CA-XX]:` listados em `Valida:`)
   - Para entender a decisão arquitetural base: `docs/architecture/proposta-arquitetural.md` (procure `ADR-XX`)
5. Implemente respeitando os pontos de validação humana marcados no plano

Padrão de nomeação de testes: `CA_XX_descricao_do_cenario` (ver `templates/id-conventions.md` do plugin).
```

## Múltiplos sistemas / mono-repo

Em mono-repo com vários sistemas independentes, replicar a estrutura por sistema:

```
monorepo/
├── apps/
│   ├── ecommerce/
│   │   └── docs/
│   │       ├── architecture/
│   │       ├── prds/
│   │       └── plans/
│   └── admin/
│       └── docs/
│           ├── architecture/
│           ├── prds/
│           └── plans/
└── packages/
    └── shared/
```

Cada sistema tem o seu pipeline SDD independente. IDs são locais a cada sistema (o `RN-01` do `ecommerce` não conflita com o `RN-01` do `admin`).

## O que **não** colocar em `docs/`

- Especificações de UI/UX (fluxos de design, mockups Figma) → pasta própria (`design/` ou link externo)
- Documentação de API gerada (Swagger, etc.) → output de build, não versionar
- Notas de reunião e brainstorm → não viram parte do pipeline; ficam em outro local (Notion, Confluence)
- READMEs de bibliotecas internas → ficam junto do código, não em `docs/`
