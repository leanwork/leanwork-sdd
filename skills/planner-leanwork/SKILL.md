---
name: planner-leanwork
description: Quebra de PRD em plano de execução incremental para devs (humanos ou agentes de IA), no padrão Leanwork. Use sempre que o usuário pedir para "criar plano de execução", "quebrar PRD em tarefas", "planejar implementação", "montar plan", "decompor feature", "fazer planning técnico" ou variações. Também use quando o usuário trouxer um PRD pronto e indicar que precisa transformar em tarefas executáveis, ou quando descrever uma feature já bem definida e pedir o plano. A skill conduz entrevista estruturada se o PRD vier incompleto, e produz markdown com tarefas em checkbox, granularidade calibrada (mistura de tarefas pequenas e médias), critérios de aceite testáveis por tarefa, dependências, riscos, testes a escrever e complexidade. Cada tarefa declara explicitamente o que **implementa** (RN-XX do PRD), o que **valida** (CA-XX do Gherkin) e quais **decisões base** (ADR-XX da arquitetura) materializa — fechando a matriz de rastreabilidade SDD. O plano é o artefato que o agente de IA (Claude Code, Codex, Cursor) consome para executar tarefa a tarefa. NÃO inclui cronograma, datas, alocação de pessoas ou estimativa em horas — o foco é "o que fazer, em que ordem, validado como".
allowed-tools: Read, Glob, Grep, Edit(docs/plans/**)
---

# Planner Leanwork — Plano de Execução

Esta skill transforma um PRD aprovado em um plano de execução técnico, incremental e rastreável. O plano é o artefato consumido pelo dev (humano ou agente de IA) durante a execução: cada tarefa é pequena o suficiente para virar 1 commit, tem critério de aceite verificável, e sabe quais testes precisa escrever.

O público-alvo do plano são os executores: devs do time e agentes de IA (Claude Code, Codex, Cursor, Gemini CLI). O documento precisa ser preciso ao ponto de um agente conseguir pegar uma tarefa, executar e marcar como concluída sem ambiguidade. Cronograma, datas e alocação ficam **fora** — isso é gestão de projeto, não plano técnico. O plano responde "o que fazer, em que ordem, e como saberemos que ficou pronto".

## Fluxo geral

A skill opera em duas fases:

1. **Entrevista estruturada** — verificar se o PRD está completo o suficiente para virar plano. Se faltar informação crítica para decidir ordem, dependências ou testes, perguntar. Não inventar.
2. **Geração do plano** — produzir markdown completo seguindo o template abaixo, com tarefas em checkbox, granularidade calibrada pelo contexto, e tudo o que um executor precisa para não travar.

## Fase 1 — Entrevista estruturada

O PRD já respondeu "o quê" e "por quê". A entrevista do planner foca em "como vamos quebrar isso de forma segura e executável". Se o PRD veio completo (no padrão `prd-leanwork`), a maioria das informações já está lá — não repetir perguntas cuja resposta está no PRD.

Perguntar em blocos lógicos, somente o que estiver faltando:

### Bloco 1 — Contexto técnico

- Qual é a stack do projeto? (versões de .NET, EF Core, banco, frontend, etc. — se já tem `CLAUDE.md` ou `README`, consultar antes de perguntar)
- Qual a estrutura de solution/projetos? (Clean Architecture? Modular monolith? Microsserviço? Pasta única?)
- Há código legado ou base existente onde a feature vai entrar? (greenfield muda bastante a quebra)
- Existem convenções específicas do projeto que afetam a quebra? (ex.: toda feature começa pela migration, ou pelo handler, ou pelo contrato da API)

### Bloco 2 — Estratégia de entrega

- A feature vai ser entregue em uma única release ou incrementalmente? (afeta se precisamos de feature flag, dark launch, etc.)
- Há partes da feature que podem ir para produção isoladamente, ou tudo precisa ir junto?
- Existe alguma dependência externa que pode atrasar parte da entrega? (API de terceiros não pronta, design não entregue, decisão de negócio pendente)

### Bloco 3 — Testes e validação

- Qual é o padrão de testes do projeto? (xUnit/NUnit/MSTest, com qual mock library, qual padrão de integration test)
- Há cobertura mínima exigida? Há áreas que dispensam teste (ex.: DTOs puros)?
- Existe ambiente de homologação/staging onde a feature será validada antes de produção?
- Quem valida o critério de aceite final? (PO, QA, cliente, próprio dev)
- Em que costura (seam) a feature deve ser testada — comportamento externo (API, handler, use case) ou existe ponto já usado em features parecidas? Preferir a costura mais alta possível e a existente à nova; quanto menos costuras diferentes no plano, mais fácil o teste sobreviver a refactors internos.

### Bloco 4 — Riscos e bloqueios conhecidos

- Há partes do código existente que são frágeis e podem quebrar com essa mudança? (legado sem teste, integração crítica, etc.)
- Existe alguma decisão arquitetural ainda em aberto que pode mudar a quebra? (se sim, sugerir resolver antes via skill `architect-leanwork` — que cobre tanto a proposta completa quanto o ADR avulso em `docs/architecture/adrs/`)
- A feature toca dados em produção que precisam de migração/backfill?

### Quando parar de perguntar

Material suficiente significa: dá para definir ordem das tarefas, critério de aceite por tarefa e estratégia de teste sem inventar. Algumas perguntas podem legitimamente não se aplicar (ex.: greenfield não tem código frágil pré-existente). O sinal de "pode gerar" é: **nenhuma tarefa do plano dependeria de uma decisão ainda não tomada**.

Se o usuário disser "gera assim mesmo, depois ajusto", respeitar — gerar com o que tem e marcar premissas explicitamente no formato `> ⚠️ **Premissa:** [descrição]` na seção de Premissas, e referenciar nas tarefas afetadas.

## Fase 2 — Geração do plano

Use o template completo em `references/plan-template.md`. Leia o arquivo antes de gerar o plano; ele contém a estrutura exata com todas as seções obrigatórias (resumo executivo, estratégia de entrega, fases com tarefas T-XX, checklist de prontidão, pontos de validação humana) e opcionais (premissas, mapa de dependências em Mermaid, testes transversais, rollback, questões em aberto, histórico de execução).

### Orientação da fatia: horizontal (padrão) ou vertical (seletiva)

O padrão do pipeline é fatiar por camada técnica (Fundação → Lógica de negócio → Exposição → Interface → Qualidade). A justificativa e o trade-off assumido nessa escolha estão registrados em `REFERENCES.md`, seção "Fatiamento horizontal por camada" — vale ler antes de desviar dela.

Desviar quando a entrevista já sinalizou um dos dois:

- **Bloco 2** respondeu que partes da feature **precisam** ir a produção isoladamente, ou que a entrega é incremental de verdade (não "podemos, mas não vamos").
- **Bloco 4** apontou risco de integração concreto (dependência externa instável, contrato entre times ainda não validado na prática).

Quando um desses sinais aparece, fatiar **a parte afetada do plano** — não necessariamente o plano inteiro — em fatias verticais: cada `T-XX` atravessa as camadas necessárias para fechar um `CA-XX` específico ponta a ponta, começando pelo caminho feliz e deixando erro/edge case para fatias seguintes. Ver `references/task-examples.md`, Exemplo 6, para o formato.

Duas ressalvas a comunicar ao usuário ao propor:

1. Fatia vertical tende a gerar **mais tarefas**, não menos — o teto de 4h força cortar por comportamento (caminho feliz → erro → edge case) em vez de cortar por camada inteira de uma vez. O ganho é demonstrabilidade cedo e menos risco de integração tardia, não redução de tarefas.
2. Na stack de referência do pipeline (Clean Architecture com projetos separados — Domain/Application/Infrastructure/Api), cada fatia vertical carrega contexto de múltiplos projetos numa única execução de `/leanwork-execute`. O sinal de "grande demais" de `task-examples.md` ("mexe em mais de 3 camadas → separar por camada") não se aplica a essas tarefas — a exceção está registrada lá, junto do exemplo.

Fora desses gatilhos, seguir o padrão horizontal: é a orientação default do pipeline, não uma opção equivalente que se escolhe por preferência.

Recursos auxiliares:

- `${CLAUDE_PLUGIN_ROOT}/templates/pipeline-example.md` — exemplo end-to-end da mesma demanda nas cinco fases; consultar para ver de onde vêm os valores dos campos `Implementa`, `Valida`, `Decisões base` e `Telas`.
- `references/task-examples.md` — exemplos calibrados de tarefas para diferentes contextos (estrutural, lógica de negócio, exposição, observabilidade, feature flag), mostrando como preencher os campos de rastreabilidade (`Implementa`, `Valida`, `Decisões base`) corretamente em cada caso. Inclui guia de granularidade (sinais de "grande demais" e "pequena demais") e tabela de quando cada campo fica vazio.

Manter hierarquia de headings e ordem das seções. Seções não aplicáveis podem ser omitidas, exceto as marcadas como obrigatórias.

## Convenções Leanwork

- **Idioma:** todo o plano em português (Brasil). Termos técnicos consagrados (handler, migration, endpoint, command, query) podem ficar em inglês.
- **Numeração de tarefas:** `T-01`, `T-02`, ..., `T-NN`. Sequencial e global ao plano inteiro — não reinicia por fase. Facilita referência cruzada.
- **Status da tarefa:** o campo `**Status:**` de cada `T-XX` é a fonte de verdade do estado e aceita exatamente quatro valores, por extenso e sem emoji: `Pendente` | `Em andamento` | `Concluído` | `Bloqueado`. Toda tarefa nasce `Pendente`. `/leanwork-next` e `/leanwork-trace` leem esse campo literalmente — outra grafia torna a tarefa invisível para eles. Ver `templates/id-conventions.md`.
- **Checkbox markdown:** usar `- [ ]` / `- [x]` nos itens de *critério de aceite*, testes transversais, checklist de prontidão e questões em aberto. **Não** usar checkbox no campo `**Status:**` — o estado da tarefa tem uma representação só, e duas se contradizem na primeira vez que alguém atualizar apenas uma delas.
- **Granularidade mista:** a skill decide caso a caso, dentro do teto único de **4 horas por tarefa** declarado em `templates/id-conventions.md` (regra de `T-XX`). Heurísticas:
  - Tarefa pequena (1 commit, ~30min-2h): quando a mudança é isolada e tem teste óbvio. Ex.: "Criar entity Foo com propriedades X, Y, Z".
  - Tarefa média (1 PR pequeno, 2h-4h): quando há acoplamento natural que separar atrapalha. Ex.: "Implementar handler + validator + testes unitários do CriarFoo".
  - **Acima de 4h, quebrar** — sem exceção. Tarefa de mais de um dia não existe no plano.
  - A faixa é calibragem mental para dimensionar a quebra, não estimativa: ela não vai escrita na tarefa. Ver "O que NÃO incluir".
- **Complexidade:** classificar como `Baixa`, `Média` ou `Alta` baseado em risco técnico e desconhecido, não em tamanho. Uma tarefa pequena pode ser Alta se mexe com legado frágil; uma tarefa média pode ser Baixa se é CRUD trivial. Não é estimativa de tempo.
- **Mermaid:** usar no mapa de dependências sempre que houver mais de 5 tarefas. Para planos pequenos, lista textual basta.
- **Referência à SPEC-UI (quando existir):** tarefas de interface preenchem o campo `Telas:` com os `UI-XX` e os estados que implementam (ex.: `UI-02 (default, limite, esgotado)`). Antes de decompor a fase de Interface, ler `docs/prototype/SPEC-UI-XXX-*.md`: o inventário de telas dimensiona as tarefas, e a seção de componentes reutilizáveis evita criar tarefas duplicadas para o mesmo componente. Se o projeto não tem SPEC-UI, omitir o campo e decompor a fase de Interface a partir dos fluxos do PRD.
- **Referência ao PRD e arquitetura (rastreabilidade SDD):** toda tarefa que implementa regra de negócio precisa preencher o campo **Implementa:** com os códigos das regras (RN-XX). Toda tarefa cuja conclusão valida cenário(s) Gherkin precisa preencher **Valida:** com os códigos dos cenários (CA-XX). Tarefas que materializam uma decisão arquitetural específica devem preencher **Decisões base:** com o(s) ADR-XX correspondente(s). Isso fecha a matriz `ADR → RN → CA → UI → T → teste` (o elo `UI` só entra quando há SPEC-UI), permitindo análise de impacto reversa (mudou RN-05, quais tarefas e testes são afetados?).

## O que NÃO incluir

- **Cronograma, datas, prazos.** O plano é sobre ordem e dependências, não sobre quando. Datas pertencem ao Azure DevOps / gestão de projeto.
- **Alocação de pessoas.** "T-03: João" não vai no plano. Quem pega a tarefa é decisão de planning/daily.
- **Estimativa em horas.** Complexidade qualitativa é suficiente — horas mentem. A faixa de 30min-4h existe só para dimensionar a quebra enquanto o plano é escrito; ela é heurística de quem planeja, não campo do artefato nem compromisso com ninguém.
- **Código pronto.** O plano direciona, não implementa. Nomes de classes/arquivos sugeridos sim, código não.
- **Decisões arquiteturais novas.** Se durante o planejamento aparecer necessidade de decidir algo arquitetural relevante, pausar e sugerir a skill `architect-leanwork` — ela cobre os dois casos: revisitar a proposta inteira, ou registrar um ADR avulso em `docs/architecture/adrs/` quando a decisão for isolada. O plano consome decisões; não cria. Registrar a pendência na seção "Questões em aberto" do plano, com o `bloqueia: T-XX` correspondente, em vez de escolher por conta própria e seguir.
- **Redundância com o PRD.** Não repetir regras de negócio detalhadas — referenciar por código (RN-XX).

## Padrões de comportamento

**Quando o usuário cola um PRD como entrada:** ler o PRD inteiro antes de perguntar. Identificar lacunas técnicas (stack, estrutura, padrão de testes) e fazer apenas perguntas que o PRD não responde. Não pedir informação que já está no PRD.

**Quando o usuário não tem PRD ainda:** sugerir rodar a skill `prd-leanwork` primeiro. Planejar sem PRD leva a tarefas que descobrem requisitos durante a execução — caro e arriscado. Se o usuário insistir, deixar registrado em premissas que o plano foi gerado sem PRD formal.

**Quando o usuário pede plano para feature pequena (1-3 tarefas):** ainda assim manter o template, mas comprimir. Fases viram opcional, mapa de dependências pode ser textual, mas critérios de aceite e testes por tarefa permanecem obrigatórios.

**Quando o usuário pede para revisar/atualizar um plano existente:** ler o plano atual, identificar tarefas concluídas (checkbox marcado), e propor diff explícito antes de reescrever. Nunca apagar histórico de execução sem confirmar.

**Quando aparece tarefa parecendo grande durante a quebra:** quebrar antes de gerar. Sinal de "está grande demais": mais de 3 critérios de aceite na mesma tarefa, ou critério de aceite que precisa de mais de 2 testes para validar, ou descrição que precisa de "e também" / "além disso" para descrever, ou mais de 4 horas estimadas mentalmente. A lista completa está em `references/task-examples.md`.

**Quando a feature toca código legado sem teste:** sugerir tarefa preliminar de caracterização (escrever testes que documentam o comportamento atual) antes das tarefas de modificação. Isso previne regressões silenciosas.

**Quando a quebra encontra um refactor de alto impacto** (renomear coluna usada por várias queries, retipar um símbolo compartilhado, mudar contrato consumido por múltiplos chamadores): não force uma tarefa monolítica — ela quebra tudo de uma vez e não cabe em 4h. Sequencie como **expandir → migrar → contrair**: uma tarefa expande (forma nova ao lado da antiga, nada quebra ainda), uma ou mais tarefas migram os chamadores em lotes (por módulo/pasta, cada lote sua própria tarefa com `Depende de:` a tarefa de expansão), e uma tarefa final contrai (remove a forma antiga, `Depende de:` todos os lotes de migração). Cada tarefa fica com CI verde standalone, ao custo de mais tarefas no plano do que uma mudança mecânica única exigiria.

**Quando o plano será consumido por agente de IA (Claude Code, Codex, etc.):** ser ainda mais explícito nos critérios de aceite e nos pontos de validação humana. Agentes não têm o instinto de "isso parece estranho, melhor confirmar" — precisam de gates explícitos no plano.

**Atualização durante a execução:** se o usuário pedir para "marcar T-XX como concluída" ou "atualizar status", aplicar a mudança preservando todo o resto do plano. Adicionar entrada na tabela de Histórico de execução com commit hash quando disponível.
