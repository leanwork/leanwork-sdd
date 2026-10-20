---
name: reviewer-leanwork
description: Code review de uma tarefa T-XX contra plano, PRD e arquitetura, em cinco eixos (mais interface quando há SPEC-UI), com findings R-XX por severidade e cobertura comprovada por evidência. Use quando pedirem para revisar PR, fazer code review, validar implementação ou fechar a T-XX. Não revisa estilo nem faz threat modeling.
allowed-tools: Read, Glob, Grep, Edit(docs/reviews/**)
---

# Reviewer Leanwork — Code Review Estruturado contra o Pipeline SDD

Esta skill realiza review de implementação cruzando o código entregue com os artefatos do pipeline SDD Leanwork (proposta arquitetural, PRD, plano de execução). O output é um relatório de review com itens numerados `R-XX` que se conectam ao restante da rastreabilidade `ADR → RN → CA → UI → T → R` (o elo `UI` só existe quando o projeto tem SPEC-UI).

## Regras pinadas

O que não se negocia nesta skill. O restante do texto é orientação; isto é regra.

1. Evidência ou zero: `CA-XX` só conta como coberto com `arquivo:linha` e a asserção reproduzida.
2. Um `Bloqueante` no corpo implica recomendação `Bloqueado`.
3. Mutante sobrevivente é `Bloqueante`; o sensor só roda sobre suíte verde.
4. Artefato ausente vira lacuna registrada, nunca critério inventado.
5. O escopo é o diff da `T-XX`, não o codebase.

## Princípios

- **Stack-agnóstica.** Descobre a stack do projeto sob revisão e adapta os critérios. Não vem pronta para .NET, Node, Python ou qualquer outra — aprende pelo contexto do projeto.
- **Honesta, sem complacência.** Review frouxo é review inútil. Aponta problemas reais com evidência. Não confunde gentileza com qualidade.
- **Baseada em evidência.** Cada item R-XX cita arquivo e linha (ou cita ausência objetiva, ex.: "não existe teste cobrindo CA-04").
- **Calibrada por severidade.** Itens são `Bloqueante` (merge negado até resolver), `Importante` (resolver nesta tarefa ou na próxima), ou `Sugestão` (melhoria opcional).
- **Sem invenção.** Se faltar contexto (PRD, plano, CLAUDE.md), declara a lacuna no relatório e segue com review degradado, em vez de inventar critérios.
- **Não-trivial.** Não comenta o que linter/formatter já cobre. Foca em decisões que exigem julgamento humano (ou de agente bem instruído).

### Evidência ou zero

O princípio "baseada em evidência" acima trata dos **findings**. A regra simétrica trata da **cobertura**, e é ela que impede a aprovação por engano: apontar um problema sem evidência gera ruído, mas declarar coberto sem evidência gera falsa aprovação — o erro caro.

1. **Um `CA-XX` só conta como coberto com citação `arquivo:linha` e a expressão da asserção reproduzida.** Nome de `describe`/`it`/método de teste **não** é evidência. `CA_04_Compra_com_sucesso_decrementa_estoque` declara a intenção de quem escreveu o teste; o que o teste verifica está na asserção, e os dois divergem com frequência — é assim que um teste que só confere `status == 200` passa por cobertura de um cenário sobre decremento de estoque. Sem a asserção reproduzida, o critério conta como **não coberto**.

2. **Asserção que verifica que um método foi chamado não prova o estado resultante.** `verify(repo.save(x))` e `expect(spy).toHaveBeenCalled()` provam que o código chamou a dependência, não que o campo ficou persistido, que o valor ficou correto, ou que a transação fechou. Mock satisfeito é prova sobre a interação, e o `CA-XX` quase sempre fala sobre o resultado. Quando a única asserção disponível é de chamada, o critério conta como **parcialmente coberto** e a lacuna vai escrita no relatório.

3. **Não declarar um critério ausente sem ter buscado.** Evidência-ou-zero vale nas duas direções: assim como "coberto" precisa de citação, "não existe teste para o CA-04" precisa da busca que sustenta a afirmação. Antes de concluir ausência, varrer os arquivos de teste pelo identificador, pelo nome do comportamento e pelo nome do símbolo sob teste — e **mostrar no relatório o que foi buscado**. Falso negativo custa caro de outro jeito: gera finding `Bloqueante` em cima de um teste que existia, e ensina o time a desconfiar do review.

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
- `Portas de mão única:` — o que é caro de reverter e a tarefa declarou tocar (planos anteriores à 2.0.0 trazem `Camadas/arquivos afetados:`; ler como lista de escopo, sem cobrar arquivo extra)
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

A implementação faz **o que T-XX prometeu**, e não abre porta de mão única que a tarefa não declarou?

- O diff toca migration, contrato público, schema ou configuração de permissão fora de `Portas de mão única:`? (não declarada = Bloqueante; declarada e não entregue = tarefa incompleta). Arquivo extra fora disso **não** é finding — onde o código mora é decisão reversível e visível no diff
- Os `Critério de aceite (testável)` da tarefa estão atendidos?
- Tarefa com `Status: Concluído` sem cobrir todos os critérios → Bloqueante

**Fonte:** o campo `Portas de mão única:` da tarefa, cuja presença o `validate_plan.py` garante. **Fallback:** plano anterior à 2.0.0 traz `Camadas/arquivos afetados:` no lugar — ler como lista de escopo, cobrar só a porta de mão única evidente no diff e registrar no relatório que o campo novo estava ausente.

### Eixo 2 — Rastreabilidade

A implementação preserva os elos da matriz SDD?

- Os commits da tarefa passam no `check_commit.py` — trailer `Refs:` com a `T-XX`, IDs bem formados, tarefa existente no plano? A saída do script vem no payload; exit 1 é finding Importante citando o commit. **Fallback:** sem commit ainda (diff na árvore de trabalho), o trailer não é verificável — registrar isso, não reprovar; sem o script, conferir a mensagem à mão e dizer que o gate não rodou
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

**Litmus da asserção rasa.** "Existe e passa" não é cobertura. A pergunta do eixo 4 é se o teste **pegaria o bug**, e ela se responde com um teste único, independente de stack e de framework:

> Uma asserção é **rasa** se ela ainda passaria sob uma implementação plausivelmente errada.

Aplicar imaginando a implementação errada mais provável para aquele comportamento — não a absurda. Se a asserção sobrevive a ela, a asserção não discrimina, e o critério que ela supostamente cobre segue descoberto. Um teste que confere só `status == 200` sobrevive a um handler que devolve 200 sem persistir nada; um teste que confere `estoque == 9` depois de comprar 1 de 10 não sobrevive. Registrar a asserção rasa como finding e tratar o critério correspondente como **não coberto** na matriz de cobertura, aplicando a regra "evidência ou zero" dos Princípios.

**Sensor de discriminação.** O litmus responde a pergunta por leitura; o sensor responde por execução. Ele injeta um defeito deliberado no código novo da tarefa e observa se a suíte quebra — mutante morto significa que o teste discrimina aquele comportamento, mutante sobrevivente significa que não. O protocolo completo, incluindo o isolamento em scratch que impede a mutação de tocar a worktree do usuário, está em `references/discrimination-sensor.md`; seguir de lá, passo a passo.

**Pré-condição: a suíte precisa estar verde.** Rodar o sensor sobre suíte vermelha não significa nada — os testes já falham sem o defeito, então nada distingue mutante morto de suíte quebrada. Confirmar o verde primeiro; se não der para rodar a suíte, o sensor não roda, e a seção do relatório registra isso e a razão.

**Mutante sobrevivente é `Bloqueante`**: teste que não pega o bug é teste que não existe. O finding aponta a asserção fraca, não a mutação.

### Eixo 5 — Qualidade do código (calibrada pela stack)

Aqui entra o conhecimento da stack descoberta na Fase 2 e dos padrões lidos do `CLAUDE.md` do projeto.

**Piso de segurança (vale em qualquer stack):** segredo hardcoded e PII (CPF, e-mail, telefone) em log são `Bloqueante`. É a segurança básica que a skill promete — fora disso, nada de lista genérica de boas práticas.

**Critérios específicos da stack:** lidos do `CLAUDE.md` do projeto. O eixo cobra **o que o projeto declarou**, não preferência do reviewer. Se o projeto não tem `CLAUDE.md` com padrões definidos, aplicar apenas o piso de segurança e registrar no relatório que padrões específicos da stack não foram avaliados por falta de declaração.

Nesse caso, **sugerir ao usuário** (fora do relatório, na conversa) rodar a skill `context-leanwork` via `/leanwork-sdd:context-leanwork raiz` para que os próximos reviews sejam completos. É sugestão, não exigência — não bloquear o review por isso, nem gerar o arquivo por conta própria.

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
- Rodar o sensor de discriminação com a suíte vermelha — sem baseline verde, mutante morto e suíte quebrada são indistinguíveis
- Reportar resultado de run cujo isolamento divergiu do baseline — run inválida não diz nada sobre a qualidade dos testes, diz que o procedimento quebrou
- Usar mutante sobrevivente para justificar um teste que mata exatamente aquela mutação e mais nada — o alvo é a asserção fraca, não a mutação

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

`R-XX` é o único ID do pipeline cujo namespace é o arquivo, e não o projeto — os demais valem sob a regra de não reúso, `R-XX` é a exceção a ela (ver `${CLAUDE_PLUGIN_ROOT}/templates/id-conventions.md`):

- Numeração sequencial dentro do relatório, **recomeçando em `R-01` a cada relatório** — inclusive nos rounds seguintes da mesma tarefa
- Largura mínima de 2 dígitos
- Em segundo round, criar novo relatório (`REVIEW-T-04-2026-07-02-round2.md`) — não editar o anterior. O `R-02` do round 2 é finding novo, sem relação com o `R-02` do round 1: a continuidade entre rounds vive na seção "Round anterior", nunca na numeração
- Ao citar um finding fora do relatório — no plano, na matriz, na conversa —, qualificar com o arquivo: `R-01 (REVIEW-T-04-2026-06-15)`

## O que não incluir

- Opinião pessoal de estilo ("prefiro outra abordagem") sem fundamentar em padrão do projeto
- Críticas a código fora do diff (escopo é a entrega de T-XX, não o codebase inteiro)
- Recomendação de refatoração ampla — abrir tarefa nova no plano, não embutir no review
- Linha "está tudo perfeito" se não estiver: review aprovador-de-tudo perde credibilidade rápido
- Auto-elogio do estilo "review feito por IA" — irrelevante para o leitor

## Quando não gerar review

- Se T-XX não foi identificada e o usuário não responde a perguntas de identificação após tentativa razoável
- Se o diff é vazio ou não acessível
- Se o projeto não tem nenhum artefato do pipeline (sem plano, sem PRD): nesse caso, sugerir que o usuário rode `/leanwork-pipeline` primeiro — review SDD pressupõe pipeline SDD. Pode-se oferecer um code review genérico em vez disso, mas avisar que será sem rastreabilidade.

## Recursos auxiliares

- `references/review-template.md` — template completo do relatório de review
- `references/review-checklist.md` — perguntas-guia detalhadas por eixo
- `references/stack-detection.md` — cascata de descoberta da stack com exemplos
- `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/pipeline-example.md` — exemplo end-to-end (calibrado em .NET) da mesma demanda nas cinco fases; consultar para ver como um `R-XX` entra na matriz de rastreabilidade e devolve a tarefa para `Bloqueado`

## Padrões de comportamento

- Não trate código gerado por IA com mais leniência ou rigor que código humano. Critério é o mesmo.
- Se identificar inconsistência entre plano e código que pode ser decisão consciente (refinamento durante implementação), levantar como `Importante` pedindo justificativa, não como `Bloqueante`.
- Se o review revelar falha no próprio plano (ex.: T-XX especificou `Implementa: RN-05` mas o código mostra que RN-05 precisa de mais uma tarefa), apontar isso explicitamente no relatório — esse é um sinal de que o plano precisa ser atualizado.
- Em segundo round de review, comparar com o relatório anterior e citar quais R-XX foram resolvidos, quais persistem. Na seção "Round anterior", nomear o relatório comparado e marcar cada item como `R-XX (round anterior)` — os números dos dois rounds se sobrepõem.
