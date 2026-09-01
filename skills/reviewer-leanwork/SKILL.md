---
name: reviewer-leanwork
description: Code review estruturado de implementação contra plano + PRD + arquitetura, no padrão Leanwork. Stack-agnóstico — descobre a stack do projeto via proposta arquitetural, CLAUDE.md ou inspeção do repositório, e aplica padrões específicos do projeto. Use sempre que o usuário pedir "revisar PR", "code review", "validar implementação", "review da tarefa T-XX", "verificar se o código atende a tarefa", "fechar T-XX" ou variações. Também use quando o usuário trouxer um diff/PR e indicar qual tarefa do plano ele entrega, ou quando pedir auditoria pós-execução de uma feature. A skill avalia em 5 eixos (aderência ao plano, rastreabilidade, aderência ao spec, cobertura de teste, qualidade do código calibrada pela stack), mais um sexto eixo de conformidade de interface quando o projeto tem SPEC-UI, produz documento com itens R-XX categorizados em Bloqueante/Importante/Sugestão, e fecha o último elo da matriz de rastreabilidade SDD (ADR → RN → CA → UI → T → R). NÃO faz code review de estilo (formatação automática), NÃO faz threat modeling completo (só segurança básica), NÃO inventa críticas quando faltar contexto — sinaliza lacuna.
---

# Reviewer Leanwork — Code Review Estruturado contra o Pipeline SDD

Esta skill realiza review de implementação cruzando o código entregue com os artefatos do pipeline SDD Leanwork (proposta arquitetural, PRD, plano de execução). O output é um relatório de review com itens numerados `R-XX` que se conectam ao restante da rastreabilidade `ADR → RN → CA → UI → T → R` (o elo `UI` só existe quando o projeto tem SPEC-UI).

## Princípios

- **Stack-agnóstica.** Descobre a stack do projeto sob revisão e adapta os critérios. Não vem pronta para .NET, Node, Python ou qualquer outra — aprende pelo contexto do projeto.
- **Honesta, sem complacência.** Review frouxo é review inútil. Aponta problemas reais com evidência. Não confunde gentileza com qualidade.
- **Baseada em evidência.** Cada item R-XX cita arquivo e linha (ou cita ausência objetiva, ex.: "não existe teste cobrindo CA-04").
- **Calibrada por severidade.** Itens são `Bloqueante` (merge negado até resolver), `Importante` (resolver nesta tarefa ou na próxima), ou `Sugestão` (melhoria opcional).
- **Sem invenção.** Se faltar contexto (PRD, plano, CLAUDE.md), declara a lacuna no relatório e segue com review degradado, em vez de inventar critérios.
- **Não-trivial.** Não comenta o que linter/formatter já cobre. Foca em decisões que exigem julgamento humano (ou de agente bem instruído).

## Fluxo geral

1. **Identificar a tarefa sob revisão (T-XX)** — pelo input do usuário, branch, commit message, ou pergunta direta
2. **Localizar artefatos** do pipeline no projeto (plano, PRD, arquitetura, CLAUDE.md)
3. **Descobrir a stack** do projeto em cascata
4. **Carregar o diff ou os arquivos modificados**
5. **Avaliar nos eixos aplicáveis** (5 sempre; o 6º apenas quando existe SPEC-UI)
6. **Gerar o relatório** seguindo o template

## Fase 1 — Identificar a tarefa e os artefatos

### Identificação da tarefa (T-XX)

Em ordem de preferência:

1. Usuário forneceu `T-XX` explicitamente → usar
2. Usuário forneceu nome de branch ou commit → procurar padrão `T-\d+` na string
3. Usuário forneceu PR/diff → procurar padrão `T-\d+` na mensagem do commit ou descrição do PR
4. Nada disso → perguntar diretamente: "Qual tarefa do plano essa implementação entrega? (ex.: T-04)"

Se houver múltiplas tarefas no mesmo PR (legítimo quando agrupadas por commit), revisar uma por vez, gerando um relatório por T-XX.

### Localização dos artefatos do pipeline

Buscar nas convenções padrão de pasta (ver `${CLAUDE_PLUGIN_ROOT}/templates/folder-conventions.md`):

- **Plano** — `docs/plans/PLAN-*.md` (ou padrão `PLAN-*.md` em qualquer lugar). Achar o plano que contém a tarefa T-XX.
- **PRD** — referenciado no cabeçalho do plano (campo `**PRD de referência:**`). Se ausente, procurar `docs/prds/PRD-*.md` com o mesmo número do plano.
- **Proposta arquitetural** — `docs/architecture/proposta-arquitetural.md` ou variações.
- **CLAUDE.md do projeto** — raiz do repositório.
- **SPEC-UI** — `docs/prototype/SPEC-UI-XXX-*.md`, com o mesmo número do PRD. Só existe em projetos com interface; ausência não é problema.

Extrair da tarefa T-XX no plano:

- `Implementa: RN-XX, RN-YY` — lista de regras que devem estar concretizadas
- `Valida: CA-XX, CA-YY` — lista de cenários Gherkin que devem ter teste passando
- `Decisões base: ADR-XX` — decisões arquiteturais que precisam ser respeitadas
- `Telas: UI-XX (estados)` — telas e estados da SPEC-UI que a tarefa implementa (quando houver)
- `Camadas/arquivos afetados:` — escopo declarado
- `Critério de aceite (testável):` — checklist específico da tarefa
- `Testes a escrever:` — testes que deveriam existir

Do PRD, extrair o texto completo dos `RN-XX` e `CA-XX` listados. Do `proposta-arquitetural.md`, extrair os `ADR-XX` listados.

**Se algum artefato não for encontrado**, registrar no relatório como lacuna e seguir com o review degradado. Não inventar.

## Fase 2 — Descobrir a stack do projeto

A skill é stack-agnóstica. A stack vem do projeto, não da skill. Aplicar a cascata descrita em `references/stack-detection.md`:

1. **Proposta arquitetural** (preferência) — seção 6 (Visão arquitetural / Containers) lista tecnologias
2. **CLAUDE.md do projeto** — frequentemente declara stack e padrões
3. **Inspeção do repositório** — `*.csproj`, `package.json`, `pom.xml`, `Cargo.toml`, `pyproject.toml`, `go.mod`, etc.
4. **Pergunta ao usuário** — última opção: "Qual a stack principal deste projeto? (linguagem, framework principal, banco)"

Documentar a stack descoberta no preâmbulo do relatório, citando a fonte (ex.: "Stack inferida da proposta arquitetural seção 6.2: .NET 8 + EF Core 8 + SQL Server 2022 + React 18").

**Padrões específicos do projeto** vêm do `CLAUDE.md` (ou da proposta arquitetural). A skill não traz padrões pré-definidos — lê do projeto e aplica.

Exemplo: se o `CLAUDE.md` diz "usamos MediatR para todos os handlers, naming `XxxCommand` / `XxxHandler`, errors via `BusinessException`", então o reviewer aplica isso como critério. Se outro projeto disser "handlers diretos no controller, sem MediatR, errors via Result pattern", aplica esse outro.

## Fase 3 — Carregar o diff

Em ordem de preferência:

1. Usuário forneceu path do diff ou patch — usar diretamente
2. Usuário forneceu URL/identificador de PR — pedir os arquivos modificados (ou navegação se for via browser tool)
3. Usuário pediu review da última implementação local — rodar `git diff` em ambiente local, se disponível
4. Nada disso → perguntar: "Como prefere que eu acesse o código? (paste do diff aqui, path local, branch para comparar, ou abrir os arquivos um a um)"

## Fase 4 — Avaliação nos eixos

Aplicar os eixos 1 a 5 sempre; o eixo 6 apenas quando o projeto tem SPEC-UI e a tarefa é de interface. Cada finding vira um item `R-XX` no relatório, com severidade.

Detalhes de critérios e perguntas-guia por eixo em `references/review-checklist.md`. Resumo:

### Eixo 1 — Aderência ao plano

A implementação faz **exatamente o que T-XX prometeu**, nada mais, nada menos?

- Arquivos modificados batem com `Camadas/arquivos afetados`? (extra = escopo expandido sem justificativa; falta = tarefa incompleta)
- Os `Critério de aceite (testável)` da tarefa estão atendidos?
- Tarefa com `Status: Concluído` sem cobrir todos os critérios → Bloqueante

### Eixo 2 — Rastreabilidade

A implementação preserva os elos da matriz SDD?

- Mensagem de commit cita `T-XX`?
- Nome de teste segue convenção `CA_XX_descricao` (ver `${CLAUDE_PLUGIN_ROOT}/templates/id-conventions.md`)?
- Comentários no código referenciam `RN-XX` ou `ADR-XX` quando útil (não obrigatório, mas valorizado)?

### Eixo 3 — Aderência ao spec (PRD + Arquitetura)

A implementação respeita o que o pipeline determinou?

- Cada `RN-XX` listado em `Implementa:` está concretizado no código? Como?
- Cada `CA-XX` listado em `Valida:` tem teste correspondente que passa?
- A decisão arquitetural em `Decisões base:` (ADR-XX) foi respeitada? (ex.: se ADR-002 diz "lock pessimista", o código realmente faz isso?)
- Há divergências silenciosas onde o código optou por outro caminho sem ADR atualizado? → Bloqueante

### Eixo 4 — Cobertura de teste

Os testes existem, cobrem o que importa, e passam?

- Cada item de `Testes a escrever:` foi criado?
- Casos de borda das `RN-XX` estão cobertos? (timeout, concorrência, payload inválido, etc.)
- Há testes de integração para os cenários `CA-XX`?
- Há teste que valida a decisão arquitetural `ADR-XX` (ex.: stress test para CA com concorrência)?
- Testes faltando para regras críticas → Bloqueante; faltando para edge cases → Importante

### Eixo 5 — Qualidade do código (calibrada pela stack)

Aqui entra o conhecimento da stack descoberta na Fase 2 e dos padrões lidos do `CLAUDE.md` do projeto.

**Critérios universais (aplicam em qualquer stack):**

- Nomes consistentes com o resto do projeto (ler convenções existentes antes de criticar)
- Tratamento de erro coerente com padrão do projeto
- Ausência de PII (CPF, e-mail, telefone) em logs
- Logging estruturado nos pontos críticos (entradas, falhas, decisões de negócio relevantes)
- Async/concurrent correto onde aplicável (sem deadlock, sem fire-and-forget acidental)
- Sem segredos hardcoded
- Sem dead code dentro do diff
- Funções/métodos não excessivamente longos (calibrar pelo padrão do projeto)

**Critérios específicos da stack:** lidos do `CLAUDE.md` do projeto. Se o projeto não tem `CLAUDE.md` com padrões definidos, aplicar apenas os universais e registrar no relatório que padrões específicos da stack não foram avaliados por falta de declaração.

Nesse caso, **sugerir ao usuário** (fora do relatório, na conversa) rodar a skill `context-leanwork` via `/leanwork-context raiz` para que os próximos reviews sejam completos. É sugestão, não exigência — não bloquear o review por isso, nem gerar o arquivo por conta própria.

### Eixo 6 — Conformidade de interface *(apenas quando existe SPEC-UI)*

Aplicável somente a tarefas com o campo `Telas:` preenchido. Pular inteiramente quando o projeto não tem SPEC-UI ou a tarefa não é de interface.

- Todos os estados listados em `Telas:` foram implementados? (`UI-02 (default, limite, esgotado)` → os três existem no código?)
- Os campos e controles da tela batem com o especificado na SPEC-UI?
- Componentes marcados como reutilizáveis foram consumidos, ou houve reimplementação duplicada?
- Estados de erro preservam os dados do formulário, quando a SPEC-UI especifica isso?
- Restrições de interface declaradas (acessibilidade, tema escuro, i18n) foram respeitadas?

**Limite deste eixo:** o review avalia **estrutura, estados e comportamento** — não estética. Não comentar escolha de cor, espaçamento ou composição visual: isso é território de design, não de code review. Estado ausente é `Bloqueante`; divergência estrutural é `Importante`; detalhe visual não vira finding.

**Não fazer:**
- Code review de formatação (linter/formatter cobre)
- Otimização de performance se performance não foi atributo prioritário no PRD/arquitetura
- Reescrever a abordagem para "como eu faria" — review é sobre adequação ao plano e qualidade objetiva, não preferência

## Fase 5 — Geração do relatório

Use o template em `references/review-template.md`. O relatório:

- Cabeçalho identificando T-XX, PRD/Plano de referência, stack detectada, autor da review (Claude), data
- Sumário executivo: total de findings por severidade, recomendação final (Aprovado / Aprovado com ressalvas / Bloqueado)
- Findings agrupados por severidade, cada um com ID `R-XX`, eixo, evidência, sugestão
- Anexo: matriz de cobertura por RN/CA da tarefa

Salvar como `docs/reviews/REVIEW-{T-XX}-{data-iso}.md` (perguntar caminho se a convenção for outra).

**Recomendação final:**
- `Bloqueado` se houver pelo menos 1 finding `Bloqueante`
- `Aprovado com ressalvas` se só houver `Importante` ou `Sugestão`
- `Aprovado` se não houver finding nenhum (raro — geralmente algo aparece)

## Convenções de IDs

`R-XX` segue as mesmas regras dos demais IDs do pipeline (ver `${CLAUDE_PLUGIN_ROOT}/templates/id-conventions.md`):

- Numeração sequencial global ao relatório (R-01, R-02, ..., R-NN)
- Largura mínima de 2 dígitos
- Sem reúso entre revisões (se segundo round abre R-04, o R-04 é novo, não retomada)
- Em segundo round, criar novo relatório (`REVIEW-T-04-2026-07-02-round2.md`) — não editar o anterior

## O que NÃO incluir

- Opinião pessoal de estilo ("prefiro outra abordagem") sem fundamentar em padrão do projeto
- Críticas a código fora do diff (escopo é a entrega de T-XX, não o codebase inteiro)
- Recomendação de refatoração ampla — abrir tarefa nova no plano, não embutir no review
- Linha "está tudo perfeito" se não estiver: review aprovador-de-tudo perde credibilidade rápido
- Auto-elogio do estilo "review feito por IA" — irrelevante para o leitor

## Quando NÃO gerar review

- Se T-XX não foi identificada e o usuário não responde a perguntas de identificação após tentativa razoável
- Se o diff é vazio ou não acessível
- Se o projeto não tem nenhum artefato do pipeline (sem plano, sem PRD): nesse caso, sugerir que o usuário rode `/leanwork-start` primeiro — review SDD pressupõe pipeline SDD. Pode-se oferecer um code review genérico em vez disso, mas avisar que será sem rastreabilidade.

## Recursos auxiliares

- `references/review-template.md` — template completo do relatório de review
- `references/review-checklist.md` — perguntas-guia detalhadas por eixo
- `references/stack-detection.md` — cascata de descoberta da stack com exemplos

## Padrões de comportamento

- Não trate código gerado por IA com mais leniência ou rigor que código humano. Critério é o mesmo.
- Se identificar inconsistência entre plano e código que pode ser decisão consciente (refinamento durante implementação), levantar como `Importante` pedindo justificativa, não como `Bloqueante`.
- Se o review revelar falha no próprio plano (ex.: T-XX especificou `Implementa: RN-05` mas o código mostra que RN-05 precisa de mais uma tarefa), apontar isso explicitamente no relatório — esse é um sinal de que o plano precisa ser atualizado.
- Em segundo round de review, comparar com o relatório anterior e citar quais R-XX foram resolvidos, quais persistem.
