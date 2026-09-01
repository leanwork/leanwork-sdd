# Checklist de Review — Perguntas-Guia por Eixo

Cada eixo abaixo lista as perguntas que o reviewer deve responder ao percorrer o diff. Não é necessário gerar um R-XX para cada pergunta — só para os pontos onde houver problema. Perguntas atendidas em silêncio ficam atendidas.

A severidade é atribuída pelo reviewer com base no impacto. As tabelas abaixo trazem **default sugerido** — não regra rígida. Justificar quando subir ou descer a severidade default.

---

## Eixo 1 — Aderência ao plano

A implementação faz **o que T-XX prometeu**?

### Perguntas-guia

| Pergunta | Default se "não" |
|----------|------------------|
| Os arquivos modificados batem com `Camadas/arquivos afetados` da tarefa? | Importante (escopo expandido) ou Bloqueante (escopo trocado) |
| Todos os itens de `Critério de aceite (testável)` da tarefa estão atendidos? | Bloqueante |
| A tarefa foi marcada como `Status: Concluído` no plano? Se sim, está coerente com o estado real do código? | Importante |
| A descrição em "Descrição:" da tarefa está coerente com o que foi feito? | Sugestão (ou Importante se houver divergência grande) |

### Sinais de problema

- **Escopo expandido sem justificativa**: PR mexe em 10 arquivos enquanto a tarefa lista 3. Pode ser legítimo (refactoring oportuno) ou problema (creep). Sempre pedir justificativa.
- **Escopo reduzido**: PR mexe em menos arquivos que o esperado. Pode ser legítimo (tarefa foi quebrada) ou problema (entrega parcial sem atualizar plano).
- **Critério de aceite vazio ou trivial**: se a tarefa não tinha critério de aceite testável, esse é um problema do plano, não do código. Apontar como nota ao processo.
- **Implementação cobre mais do que T-XX**: provável que T-XX foi pequena demais ou outras tarefas foram silenciosamente entregues. Apontar.

### O que NÃO levantar aqui

- Detalhes de implementação dentro do escopo (vai para Eixo 5)
- Faltas de teste (vai para Eixo 4)
- Críticas a regras de negócio do PRD (não é escopo de review — virou comentário ao PRD)

---

## Eixo 2 — Rastreabilidade

A implementação preserva os elos da matriz SDD?

### Perguntas-guia

| Pergunta | Default se "não" |
|----------|------------------|
| Mensagem(ns) de commit referencia(m) `T-XX`? | Sugestão |
| Nome da branch contém `T-XX`? (se a convenção do projeto exige) | Sugestão |
| Nomes de teste seguem o padrão `CA_XX_descricao`? | Importante |
| Há teste para cada `CA-XX` listado em `Valida:` da tarefa? | Bloqueante (se CA-XX é parte da tarefa) |
| Comentários no código referenciam `RN-XX` ou `ADR-XX` em pontos não-óbvios? | Sugestão |

### Sinais de problema

- **Implementa: RN-05 mas o código não tem nada que indique RN-05**: nem nome de método, nem comentário, nem teste. Aceitável quando a regra é parte do fluxo natural; suspeito quando a regra é específica e sutil.
- **Valida: CA-04, CA-06 mas só existe teste `CA_04_*`**: falta cobertura prometida — Bloqueante.
- **Teste com nome genérico (`Should_work_correctly`)** sem o ID do CA: perde rastreabilidade — Importante.

---

## Eixo 3 — Aderência ao spec (PRD + Arquitetura)

A implementação respeita o que o pipeline determinou?

### Perguntas-guia

| Pergunta | Default se "não" |
|----------|------------------|
| Cada `RN-XX` listado em `Implementa:` está concretizado no código? | Bloqueante (RN é regra de negócio — não pode faltar) |
| O comportamento implementado bate com a redação atual do `RN-XX` (não com o que o dev "achou que era")? | Bloqueante se diverge; Importante se ambíguo |
| Cada `CA-XX` listado em `Valida:` tem teste correspondente que efetivamente exercita o cenário Gherkin? | Bloqueante (teste vazio ou que valida coisa diferente é pior que ausência) |
| A `Decisão arquitetural` em `Decisões base:` foi materializada? (ex.: ADR-002 = lock pessimista → código realmente usa lock pessimista) | Bloqueante |
| Há divergências silenciosas onde o código optou por outro caminho sem ADR atualizado? | Bloqueante |
| Quando há ambiguidade no PRD, o código toma decisão razoável e documenta? | Importante (sem documentação) ou OK (com comentário/note) |

### Sinais de problema

- **Implementação faz mais do que a RN exige**: aceitável geralmente, mas se for "verificação extra" que muda comportamento esperado pelo PO, abrir como Importante para confirmar.
- **Implementação faz menos do que a RN exige**: Bloqueante. Regra de negócio incompleta entrega valor errado.
- **Implementação adota padrão diferente do ADR**: ex.: ADR-002 fala lock pessimista, código usa Redis com Lua script. Bloqueante até reconciliar (ou atualizar ADR, ou voltar ao padrão).
- **Implementação adiciona regra não documentada**: ex.: código rejeita compras menores que R$10 mas isso não está em RN nem CA. Pode ser legítimo (validação técnica) ou perigoso (regra de negócio escondida). Apontar como Importante.

### Casos especiais

- **Regra ambígua no PRD**: se a redação da `RN-XX` permite mais de uma interpretação e o código escolhe uma, isso é um bug no PRD, não no código. Apontar como nota para revisar o PRD.
- **ADR vago**: se ADR-XX é genérico demais para validar implementação concreta, apontar como nota ao processo (ADR precisa ser mais específico).

---

## Eixo 4 — Cobertura de teste

Os testes existem, cobrem o que importa, e passam?

### Perguntas-guia

| Pergunta | Default se "não" |
|----------|------------------|
| Cada item de `Testes a escrever:` na tarefa foi criado? | Bloqueante (testes prometidos não entregues) |
| Cenários `CA-XX` críticos têm teste de integração, não só unit? | Importante (depende da complexidade do CA) |
| Casos de borda das `RN-XX` estão cobertos? (timeout, payload inválido, concorrência) | Importante |
| Há teste que valida especificamente a decisão arquitetural? (ex.: stress test para ADR de concorrência) | Importante (Bloqueante se a decisão é central à tarefa) |
| Testes passam localmente / em CI? | Bloqueante (teste que não passa não é teste) |
| Há testes que dependem de ordem ou de estado externo? | Importante |
| Há mock excessivo escondendo problema real? (ex.: mockando a coisa que deveria ser testada) | Importante |
| Cobertura cai abaixo de threshold do projeto (se houver)? | Importante |

### Sinais de problema

- **Teste cobre o teste**: assertions tautológicas como `Assert.Equal(result, result)`. Bloqueante.
- **Teste comentado ou marcado com `Skip` sem justificativa**: Bloqueante. Test com skip precisa de justificativa em comentário (referência a issue, motivo).
- **Teste sem assertion**: arrange/act sem verificação. Bloqueante.
- **Teste de integração que não vai ao banco/serviço real**: é teste de unit travestido. Importante.
- **Apenas caminho feliz coberto**: faltam cenários de erro listados em CA. Importante a Bloqueante.

### Calibragem por tipo de tarefa

- **Tarefa estrutural** (entity, migration): testes podem ser N/A, mas o reviewer deve confirmar que isso está declarado na tarefa
- **Tarefa de lógica**: cobertura ampla esperada
- **Tarefa de UI**: testes de componente + alguns E2E para fluxos críticos; nem todos os CA precisam virar E2E
- **Tarefa de observabilidade**: testes podem ser leves; cobertura via log assertion ou métrica exposta

---

## Eixo 5 — Qualidade do código

Calibrado pela stack descoberta na Fase 2 + padrões do `CLAUDE.md` do projeto. Princípios universais sempre aplicam; padrões específicos só quando declarados.

### Princípios universais

| Pergunta | Default se "não" |
|----------|------------------|
| Nomes (variáveis, métodos, classes) seguem convenção do projeto? | Importante (se sistemático) ou Sugestão (pontual) |
| Tratamento de erro é coerente com padrão do projeto? | Importante |
| Há PII (CPF, e-mail, telefone, nome completo) em logs? | Bloqueante |
| Há segredos hardcoded (senhas, tokens, conexão)? | Bloqueante |
| Há dead code dentro do diff? (variáveis não usadas, métodos não chamados, comentários // TODO sem dono) | Sugestão a Importante |
| Há código duplicado óbvio? | Importante (se substancial) |
| Async/concurrent está correto? (sem deadlock, sem `.Result`/`.Wait()`, sem fire-and-forget acidental) | Importante a Bloqueante |
| Há `console.log`, `printf`, `Console.WriteLine` de debug esquecidos? | Importante |
| Há `magic numbers` ou strings sem constante? | Sugestão |
| Inputs externos são validados antes de uso? | Importante a Bloqueante |
| Operações de escrita são idempotentes onde apropriado? | Importante |
| Logging estruturado nos pontos críticos? | Importante |
| Há acoplamento desnecessário entre camadas? | Importante |
| Documentação inline existe onde a lógica é não-óbvia? | Sugestão |

### Critérios específicos da stack

Lidos do `CLAUDE.md` do projeto. Exemplos do que pode estar declarado e virar critério:

- "Todos os comandos passam por MediatR" → controller que cria handler direto é Importante
- "Errors de negócio via BusinessException, technical via subir exception" → mistura de Result com exception é Importante
- "Repositórios isolam EF Core, nunca expor IQueryable" → vazamento é Importante
- "Componentes React funcionais com hooks, sem classes" → classe nova é Importante
- "Estado global via Zustand, evitar Context para estado mutável" → uso de Context é Importante
- "Toda função pública tem teste unitário" → função sem teste é Importante

### Não fazer

- **Não comentar formatação** (linter/formatter cobre). Indentação, ponto-e-vírgula, aspas, quebras de linha = não é review.
- **Não impor preferência pessoal** que não está no `CLAUDE.md`. Se o projeto não declara que prefere `for` a `forEach`, não criticar.
- **Não rabiscar refactorings amplos** — abrir tarefa nova, não embutir no review.
- **Não otimizar prematuramente**: performance só vira issue se foi atributo prioritário no PRD/arquitetura.
- **Não inventar regras de segurança** que não fazem parte do contexto. Aplicar princípios universais (PII, segredos), não OWASP completo a menos que o projeto exija.

### Quando subir severidade

- Default `Sugestão` vira `Importante` se: o problema repete em vários pontos do diff (sistemático) ou está em código que vai ser referência para tarefas futuras.
- Default `Importante` vira `Bloqueante` se: o problema causa risco direto (dados perdidos, vazamento de PII, comportamento errado em produção).
- Default `Bloqueante` vira `Importante` se: foi documentado como dívida consciente em algum ADR ou comentário, e a justificativa é defensável.

---

## Eixo 6 — Conformidade de interface *(apenas quando existe SPEC-UI)*

Aplicável somente a tarefas com o campo `Telas:` preenchido. Se o projeto não tem SPEC-UI ou a tarefa não é de interface, pular o eixo inteiro — não inventar findings de UI onde não há especificação.

### Perguntas-guia

| Pergunta | Default se "não" |
|----------|------------------|
| Todos os estados listados em `Telas:` foram implementados? | Bloqueante (estado ausente vira bug em produção) |
| Os campos e controles batem com o especificado na SPEC-UI? | Importante |
| Componentes marcados como reutilizáveis foram consumidos em vez de reimplementados? | Importante |
| Estado de erro de formulário preserva os dados digitados, quando especificado? | Bloqueante |
| Estado vazio distingue "vazio inicial" de "vazio por filtro", quando a SPEC-UI especifica? | Importante |
| Restrições de interface (acessibilidade, tema escuro, i18n) foram respeitadas? | Importante a Bloqueante |
| A tela implementa comportamento não especificado na SPEC-UI? | Importante (pedir justificativa — pode ser lacuna da spec) |

### Limite deste eixo

O review avalia **estrutura, estados e comportamento**. Não avalia estética.

**Não levantar como finding:**
- Escolha de cor, espaçamento, tamanho de fonte, composição visual
- Preferência de layout que a SPEC-UI não especifica
- "Ficaria melhor se..." sobre aparência

Divergência visual sem impacto funcional é assunto de design review, não de code review. Se o desvio for grande a ponto de sugerir que a implementação ignorou o protótipo, levantar como um único finding `Importante` apontando o padrão, não um finding por detalhe.

### Sinais de problema

- **Só o caminho feliz implementado**: `Telas: UI-02 (default, limite, esgotado)` mas o código só trata `default`. Bloqueante.
- **Estado implementado mas inalcançável**: existe o componente de erro, mas nenhuma condição o renderiza. Importante.
- **Componente duplicado**: `CardOferta` reimplementado na tela de admin em vez de importado. Importante.
- **Estado derivado tratado como validado**: a SPEC-UI marca um estado como "Derivado do PRD" (não validado por design) e a implementação seguiu literalmente. Não é finding — mas vale nota ao processo sugerindo validação.

---

## Eixos transversais (registrar como nota se aplicar)

Não são parte dos 6 eixos mas vale registrar quando aparece:

- **Plano precisa de atualização**: implementação revelou que T-XX foi mal dimensionada ou que outras tarefas precisam ser criadas
- **PRD ambíguo**: a redação de RN-XX ou CA-XX permitiu interpretação dupla, e a divergência só apareceu agora
- **ADR ausente**: implementação tomou decisão arquitetural que merecia ser ADR e não foi documentada
- **Padrão emergente**: o time está estabelecendo um padrão que ainda não está no `CLAUDE.md`. Sugerir documentar.
- **SPEC-UI incompleta**: a implementação precisou de um estado que a especificação não previu. Sugerir atualizar a SPEC-UI — é sinal de que a fase de protótipo deixou lacuna.

Esses pontos vão na seção "Notas ao processo" do relatório, não viram R-XX.

---

## Tabela rápida de severidade

| Categoria | Bloqueante | Importante | Sugestão |
|-----------|------------|------------|----------|
| Critério de aceite não atendido | ✓ | | |
| Teste prometido faltando (CA crítico) | ✓ | | |
| ADR violado sem nova ADR | ✓ | | |
| RN não concretizada | ✓ | | |
| PII em log | ✓ | | |
| Segredo hardcoded | ✓ | | |
| Teste comentado/Skip sem justificativa | ✓ | | |
| Teste sem assertion | ✓ | | |
| Escopo expandido sem justificativa | | ✓ | |
| Teste de edge case faltando | | ✓ | |
| Padrão do CLAUDE.md violado sistematicamente | | ✓ | |
| Async/concurrent suspeito | | ✓ | |
| Tratamento de erro inconsistente | | ✓ | |
| Dead code | | ✓ | ✓ |
| Magic numbers | | | ✓ |
| Nome de variável melhorável | | | ✓ |
| Comentário de debug esquecido | | ✓ | |
| Documentação inline ausente em lógica complexa | | | ✓ |
| Falta referência a T-XX no commit | | | ✓ |
| Nome de teste não segue convenção CA_XX | | ✓ | |
| Estado de tela especificado não implementado | ✓ | | |
| Erro de formulário perde dados digitados | ✓ | | |
| Componente reutilizável reimplementado | | ✓ | |
| Campo divergente da SPEC-UI | | ✓ | |
| Detalhe visual (cor, espaçamento) | | | — não é finding |
