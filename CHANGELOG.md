# Changelog

Histórico de versões do plugin `leanwork-sdd`. Formato: versão, data quando registrada, e o que mudou com o motivo.

## 2.0.0 — 2026-10-19

Enxugamento do pipeline, executado pelo `docs/plans/PLAN-002-enxugamento-pipeline.md`. A premissa: os modelos atuais seguem instrução concisa e inferem contexto do repositório, mas continuam declarando conclusão sem prova e escrevendo teste raso. Por isso o corte é assimétrico — **sai a coreografia, fica a verificação**. Gates, sub-agente verificador, sensor de discriminação e "evidência ou zero" não mudaram.

### Quebras de contrato

| O que mudou | Antes (1.10.0) | Agora (2.0.0) | O que fazer com artefato antigo |
|---|---|---|---|
| Comandos de entrada | `/leanwork-start` e `/leanwork-next` | `/leanwork-pipeline`, sem alias | Nada — só trocar o comando |
| Comandos de skill | `/leanwork-prototype` e `/leanwork-context` | Removidos; as skills são chamadas por `/leanwork-sdd:prototype-leanwork` e `/leanwork-sdd:context-leanwork` | Nada |
| Estado da tarefa | `Status:` + tabela de Histórico de execução | Só `Status:`; a trilha vem do git pelo trailer `Refs: T-XX, CA-XX` | A tabela de Histórico é ignorada pelos scripts, sem erro |
| Escopo da tarefa | Campo `Camadas/arquivos afetados:` | Campo `Portas de mão única:` (migration, contrato público, schema, permissão) | O campo antigo continua aceito, com WARN; o review lê como escopo |
| Unidade de trabalho | Fatia horizontal por camada, teto de 4h | Fatia vertical por `CA-XX`, medida por caber num ciclo de execute + review | Plano antigo continua válido |
| Critério de aceite | Checkbox, mais checklist de prontidão obrigatório | Lista simples; prontidão genérica é a Definition of Done do `CLAUDE.md` | Plano antigo continua válido |

Rollback: reinstalar a 1.10.0 a partir do commit `c5c3f63`. Planos no formato antigo passam nos gates da 2.0.0, então a ida não exige migrar artefatos.

### Métricas antes e depois

Linha de base medida em 2026-10-16 (seção 3 do PLAN-002).

| Métrica | Como se mede | 1.10.0 | 2.0.0 | Variação |
|---|---|---|---|---|
| Ciclo execute + review | Linhas de `leanwork-execute.md` + `leanwork-review.md` + `reviewer-leanwork/SKILL.md` + `reviewer-leanwork/references/*` | 1.258 | 1.234 | −2% |
| Descriptions das skills | Soma dos caracteres do campo `description` das seis skills | 6.683 | 2.006 | −70% |
| README | Linhas do `README.md` | 425 | 197 | −54% |
| Passagens repetidas | Arquivos com cada passagem por extenso: "Degradação silenciosa" / "Sombra de prefixo" / tabela "Quem sugere" | 4 / 4 / 3 | 1 / 1 / 1 | uma cópia de cada |

**O ciclo quase não encolheu, e isso foi escolha.** Das 1.234 linhas, 758 são as `references/` do reviewer (checklist, template, detecção de stack, sensor), que o plano decidiu não tocar. O ganho de custo vem de haver **menos ciclos**: no teste A/B do planner, o mesmo PRD virou 21 tarefas em vez de 35.

### Testes A/B contra a 1.10.0 (2026-10-19)

Cada skill rodou nas duas versões, com a mesma entrada, por `claude -p --plugin-dir`, numa rodada. É evidência de um caso por skill, não estatística.

| Skill | Resultado | Ajuste feito |
|---|---|---|
| architect | Proposta equivalente (12 seções, 7 ADRs, mesmas decisões). Entrevista ficou rasa: 2 perguntas contra 7 na primeira rodada | Listas de trade-offs e isomorfismo e regra do jargão devolvidas; entrevista volta a um bloco inteiro por rodada nas quatro skills |
| planner | 21 tarefas contra 35, mesma cobertura (9/9 `CA`, 8/8 `RN`), mesmo detalhe por tarefa. Tela entra junto do cenário; a 1.10.0 deixava as tarefas de tela sem `CA` e decidiu sozinha uma questão arquitetural aberta que a 2.0.0 marcou como pendente | Nenhum |
| prd | Entrevista melhor (leu a arquitetura e pulou o já respondido). Regras e cenários equivalentes. Perdeu os diagramas dos fluxos secundários | Seção 7 do template recuperada: outros fluxos e mapa de desvios |
| prototype | Entrevista melhor (recomendou o modo pela busca). SPEC-UI equivalente: 4 telas, 28 estados contra 27, 20 lacunas contra 17 | Nenhum |
| reviewer, context | Não testados. A verificação do reviewer não mudou; o context mudou só de forma | — |

### Estado em fonte única, trilha rápida e fatia por `CA` (T-01 a T-13)

- A tabela de Histórico de execução sai de plano, template, skills e comandos. O campo `**Status:**` é a única fonte de estado; `validate_plan.py` ignora a tabela em plano antigo.
- `scripts/check_commit.py`: confere o trailer `Refs:` da mensagem de commit — pelo menos uma `T-XX`, IDs bem formados e, com `--plan`, tarefa existente. Funciona também como hook `commit-msg` do git.
- O checklist de prontidão deixa de ser seção obrigatória do plano e vira Definition of Done do `CLAUDE.md` do projeto.
- **Trilha rápida**: mudança com menos de ~3 arquivos e nenhuma porta de mão única vira plano de uma tarefa, com os cenários dentro dela (`plan-template-quick.md`). Uma segunda tarefa reprova no gate.
- **Fatia vertical por `CA-XX`** como padrão, revertendo o padrão horizontal da 1.8.0 (aprovado antes da T-07). Horizontal fica para fundação, migrations e expandir → migrar → contrair. O WARN de tarefa grande passa de 3 para 5 critérios de aceite.
- Campo `**Portas de mão única:**` substitui `Camadas/arquivos afetados:`; campo `**Bloqueio:**` obrigatório com `Status: Bloqueado`.
- `scripts/status.py` (estado do pipeline e próxima tarefa elegível) e `scripts/trace.py` (matriz e lacunas) substituem a leitura feita pelo modelo em `/leanwork-pipeline` e `/leanwork-trace`.
- `/leanwork-start` e `/leanwork-next` se fundem em `/leanwork-pipeline`; `/leanwork-prototype` e `/leanwork-context` saem.
- O suporte a hooks em plugin foi verificado na documentação oficial do Claude Code antes da Fase 5 (T-13).

### Gates disparados por hook (T-14)

- `hooks/hooks.json` registra um hook `PostToolUse` (`Write|Edit`) que roda `scripts/hook_gate.py`. Edição em `docs/plans/*.md` dispara `validate_plan.py`; em `docs/reviews/*.md`, `validate_review.py`. Reprovação sai com exit 2 e o stderr volta ao modelo, que corrige o artefato. `validate_ids.py` continua chamado por `/leanwork-execute`, porque não depende de edição.
- Planner, `/leanwork-execute` e `/leanwork-review` descrevem o gate em três linhas: hook, fallback por linha de comando, fallback manual declarado.
- **Teste manual (2026-10-19, Claude Code 2.1.292, Windows 11):** `claude -p --plugin-dir .` num projeto descartável com um plano válido.
  - Edição que troca `Status: Pendente` por `Status: Feito` → o modelo recebeu `hook_gate: validate_plan.py reprovou PLAN-001-fixture.md` com o `ERROR T-01 (linha 17): Status 'Feito' fora do vocabulario fixo`.
  - Edição seguinte para `Status: Em andamento` → nenhum retorno do hook.
- `selftest.py` ganha cinco casos do hook: plano válido, plano inválido, review inválido, arquivo fora do escopo e entrada ilegível.

### Justificativas escritas uma vez (T-15)

- "Degradação silenciosa é pior que gate nenhum" fica por extenso no README (seção dos gates). Planner, `/leanwork-execute` e `/leanwork-review` mantêm a regra em uma linha, com remissão.
- "Sombra de prefixo entre baldes" fica só no `permission-catalog.md`. Os três arquivos com gate guardam a regra operacional em uma linha: confirmar ou ajustar as settings, nunca pular a validação.
- A tabela "Quem sugere" fica no README, unificada para `context-leanwork` e `prototype-leanwork`. As duas skills apontam para ela e mantêm a regra de nunca rodar como efeito colateral.

### Descriptions curtas e regras pinadas (T-16)

- A `description` de cada skill fica só com gatilhos e exclusões. A soma das seis caiu de 6.437 para 2.006 caracteres; a linha de base de 2026-10-16 era 6.683.
- Cada SKILL ganha uma seção **Regras pinadas**, com 4 ou 5 itens: o que não se negocia na skill. O restante do texto perde caixa alta e negrito de alarme: `NUNCA`/`PARE`/`NÃO` em caixa alta caem de 18 ocorrências para 0 fora das regras pinadas.

### Entrevistas: busca antes de pergunta (T-17)

- Architect, PRD, planner e prototype declaram a mesma regra. Fato se busca no repositório, no `CLAUDE.md`, nos artefatos e na conversa. O que a busca não responde se pergunta um bloco de dimensões inteiro por rodada, e toda pergunta de decisão traz opções concretas e a recomendação marcada.
- **Revisão após teste A/B (2026-10-19).** A primeira versão desta regra limitava a duas decisões por vez. Com um briefing curto, a skill da 1.10.0 abriu com sete perguntas detalhadas e a cortada com duas. A cobertura levaria 3 a 4 vezes mais rodadas e o detalhe por rodada caía. A regra passou a um bloco inteiro por rodada.
- Os blocos de perguntas viraram **dimensões a cobrir**. Cada dimensão termina respondida ou marcada `n/a — motivo`; sem isso, é lacuna e impede a geração. Todas as dimensões anteriores foram mantidas.
- Na prototype, a pergunta de modo (ingestão, geração, híbrido) vem com a recomendação tirada do que a busca encontrou.

### Architect e PRD sem conteúdo de livro-texto (T-18)

- `skills/architect-leanwork/SKILL.md`: 248 → 147 linhas. Saíram a explicação de Cynefin (fica a consequência prática), a lista genérica de trade-offs, a lista de isomorfismos (está em `architectural-styles.md`), a explicação dos níveis do C4 e os princípios de escrita genéricos. Ficaram as posições Leanwork: restrição como restrição, sem modismo, sem estimativa, regra de escolha do nível C4 e o checklist final. Os catálogos em `references/` não mudaram.
- PRD: a hierarquia Epic → Feature → PBI passa a opcional, para quem cadastra no Azure DevOps, na SKILL e no template. A seção 7.2 do template (fluxos alternativos e de erro), que redescrevia os cenários `CA-XX`, virou um mapa de desvios: uma linha por desvio, citando a `RN` e o `CA`, com o desvio operacional sem cenário também listado. Um teste A/B mostrou que a primeira versão do corte, que reduzia a seção 7 a "Fluxo principal", fazia o PRD perder os diagramas dos outros fluxos (confirmação assíncrona, importação). A seção voltou a ser "Fluxos", com 7.2 "Outros fluxos" e 7.3 "Desvios e erros". A numeração das seções foi mantida porque `id-conventions.md` cita as seções 8 e 9.
- `REFERENCES.md`: a entrada de Cynefin passa de reprodução a adaptação.
- **Revisão após teste A/B (2026-10-19).** A mesma demanda foi rodada pela skill da 1.10.0 e pela cortada, com briefing completo. As propostas saíram equivalentes: mesma estrutura, 7 ADRs, mesmas decisões, sumário em linguagem de negócio, nenhuma estimativa. Ainda assim, três itens voltaram: a lista de trade-offs candidatos, a lista de isomorfismo domínio → estilo e a regra de explicar jargão no sumário. Elas funcionam como checklist, custam 18 linhas e o risco de cortá-las aparece em domínio menos óbvio que o testado. A SKILL fica com 165 linhas, acima da meta de 150 da T-18.

### README enxuto e CHANGELOG (T-19)

- A seção Versionamento do README migrou inteira para este arquivo: as 21 entradas, de 1.0.0 a 1.10.0, com o texto original.
- O README descreve o pipeline 2.0 (comandos atuais, trilha rápida, fatia por `CA`, scripts e hooks) e passa de 425 para 197 linhas. A árvore de diretórios e a lista de templates por skill saíram: cada SKILL lista os próprios recursos.

### Exemplo end-to-end no formato novo (T-20)

- O plano de `stacks/dotnet/pipeline-example.md` virou um plano completo e curto: fundação horizontal (`T-01`, migration) e três fatias por `CA-XX`. Usa `**Portas de mão única:**`, `**Bloqueio:**` com `R-01 (REVIEW-T-03-2026-06-15)` e o commit com trailer `Refs:`, sem tabela de Histórico. O review passou a ser da `T-03` e ganhou a seção do sensor de discriminação.
- A matriz do exemplo é a saída literal do `trace.py` sobre os cinco fragmentos. A selftest ganha quatro casos que extraem os fragmentos e rodam `validate_plan.py`, `validate_ids.py`, `validate_review.py` e `trace.py`. O último falha se a matriz publicada divergir da saída do script; a falha foi conferida alterando a matriz de propósito.
- Correção no `trace.py`: a regra `RN-XX` que quebra em várias linhas perdia o `(ADR-XX)` da linha de continuação. A `RN-05` do exemplo expôs isso.

### Site e manifesto (T-21)

- `plugin.json` e `marketplace.json` em 2.0.0. O `site/index.html` passa a listar os quatro comandos atuais e deixa de afirmar que o Bash não é pré-autorizado em lugar nenhum, o que já era falso desde a 1.10.0.
- `REFERENCES.md` credita o `tlc-spec-lean` v1.1.0 (Tech Leads Club, CC-BY-4.0): portas de mão única, trilha curta, "granularidade não é qualidade" e pergunta com recomendação, como adaptação; registra o que não foi adotado e o que é contribuição própria.

## 1.10.0

a camada de verificação do pipeline era prosa inteira: nenhuma regra falhava, tudo dependia de o agente lembrar. Um plano sem `Testes a escrever:` era apresentado, uma tarefa citando `RN-42` inexistente virava código contra um requisito imaginário, e um relatório de review aprovava com "coberto por `CA_04_compra_decrementa_estoque`" — nome de método como evidência. Três frentes fecham isso. **(1) Gates determinísticos:** nova pasta `scripts/` com `validate_plan.py`, `validate_ids.py` e `validate_review.py`, chamados pela skill ou comando que produz o artefato antes de apresentá-lo — exit diferente de zero é PARE. Os três arquivos que os invocam passam a declarar `Bash(python:*)`, revisão parcial da decisão da `1.6.4`: a alternativa era manter a pureza da regra e a regra não rodar. **(2) Autor ≠ verificador:** `/leanwork-review` despacha um sub-agente de contexto limpo, com payload autossuficiente de sete itens e três exclusões nomeadas — o raciocínio da implementação fica de fora de propósito, porque quem recebe a justificativa julga se ela convence, não se o código cumpre o spec. **(3) Sensor de discriminação:** o eixo 4 deixa de perguntar só se o teste existe e passa, e passa a perguntar se ele **pegaria o bug** — injeta um defeito no código novo e observa se a suíte quebra, com isolamento em scratch fora da árvore do usuário. Mutante sobrevivente é `Bloqueante`. Junto vem a regra "evidência ou zero": cobertura sem `arquivo:linha` **e** sem a asserção reproduzida conta como não coberta

## 1.9.0

os exemplos .NET saem do núcleo agnóstico e ganham endereço próprio em `stacks/dotnet/`. `templates/pipeline-example.md` (exemplo end-to-end das cinco fases) muda de lugar inteiro, e as cinco skills que produzem artefato repontam para lá. `task-examples.md` do planner e o diagrama C4 Nível 3 do architect (que usava MediatR/FluentValidation/EF Core numa Clean Architecture completa — a mesma combinação que a skill lista entre os modismos a não adotar por moda) passam a ter versão agnóstica no lugar original e versão calibrada em `stacks/dotnet/`. Placeholders `.NET` soltos em templates de preenchimento (`proposal-template.md`, `prd-template.md`, `plan-template.md`, `claude-md-root-template.md`) viram genéricos. `id-conventions.md` troca o bloco xUnit por pseudocódigo e aponta para a versão .NET. Novo `stacks/README.md` documenta a convenção para futuras stacks

## 1.8.0

a divergência de fatiamento horizontal registrada em `REFERENCES.md` ganha exceção seletiva: quando a entrevista do planner sinaliza entrega incremental real (Bloco 2) ou risco de integração concreto (Bloco 4), a fatia vertical passa a valer para a parte afetada do plano — não para o plano inteiro. `planner-leanwork/SKILL.md` ganha a seção "Orientação da fatia" com os dois gatilhos e duas ressalvas (fatia vertical gera mais tarefas, não menos; e carrega contexto de múltiplos projetos por execução na stack de referência em Clean Architecture). `task-examples.md` ganha o Exemplo 6 e uma exceção explícita ao sinal de "mexe em mais de 3 camadas → separar", e `plan-template.md` referencia a alternativa sem substituir o padrão. Horizontal continua default

## 1.7.0

três práticas de engenharia entram no pipeline sem skill nova. `planner-leanwork` ganha o padrão **expandir-migrar-contrair** para refactors de alto *blast radius* (renomear coluna, retipar símbolo compartilhado) que não cabem em uma tarefa monolítica de 4h, e uma pergunta de entrevista sobre a **costura de teste** (seam) preferencial antes de quebrar em tarefas. `/leanwork-execute` passa a escrever o teste antes do código de produção na costura, quando praticável, e a rodar typecheck/build antes da suíte — typecheck quebrado bloqueia `Concluído` do mesmo jeito que teste vermelho. Fatiamento vertical por tarefa (tracer bullet) foi avaliado e **não adotado**: o `plan-template.md` fatia por camada técnica de propósito, divergência já registrada em `REFERENCES.md` com justificativa própria — trocar isso exige decisão explícita, não é ganho a implementar de passagem

## 1.6.10

os oito templates de `references/` param de se fechar sozinhos. Cada um envolve o documento-modelo numa cerca de código, e o conteúdo tem blocos `mermaid`, `gherkin`, `bash` e `csharp` na mesma largura de três crases: pelo CommonMark, o primeiro bloco interno encerra o externo. A renderização quebrava no meio do template e o agente que o lê para gerar o artefato precisava adivinhar onde o modelo termina — bem no ponto em que nascem os `CA-XX` do PRD. O envelope passa a quatro crases, e cada template agora diz por escrito que essa cerca é andaime e não entra no documento gerado

## 1.6.9

`R-XX` deixa de ser exceção não declarada. A regra geral de IDs proibia reúso, e a regra de `R-XX` recomeça em `R-01` a cada relatório: a exceção agora está escrita no ponto da regra geral, junto com o motivo — relatórios de review são o único artefato que existe muitas vezes no mesmo projeto. Corrigido o efeito colateral disso na skill de review, que anunciava "as mesmas regras dos demais IDs" e dava exemplo de numeração continuando entre rounds. E o número passa a vir com o arquivo: `R-01 (REVIEW-T-04-2026-06-15)` em todo lugar fora do relatório de origem — plano, matriz do `/leanwork-trace`, sugestão do `/leanwork-next` e conversa

## 1.6.8

o único ponto do pipeline que podia produzir número financeiro por acidente de template deixa de produzi-lo. O sumário executivo da proposta arquitetural pedia "custo e prazo de cara, em ordem de grandeza" enquanto o apêndice do mesmo arquivo já mandava cronograma e estimativa para o planejamento de sprint — e o campo vencia, porque é o que o agente preenche. Agora o sumário só ecoa **restrição declarada pelo cliente**, que é entrada e vive na seção 4; estimativa gerada pela proposta some, e o checklist final passa a barrá-la explicitamente

## 1.6.7

o parâmetro que dimensiona o plano inteiro passa a ter um número só. O tamanho de tarefa aparecia com seis redações em quatro arquivos — 4h, 2h, meio dia, "nunca mais de 1 dia" — e dois planos do mesmo PRD saíam estruturalmente diferentes conforme qual regra o modelo lesse primeiro. Teto único de **30min-4h**, declarado em `templates/id-conventions.md` na regra de `T-XX`, com o planner e os exemplos de tarefa apontando para lá. Fica explícito que a faixa é calibragem mental de quem planeja, não estimativa: ela nunca vira campo do plano, que continua registrando só `Complexidade` qualitativa

## 1.6.6

o opt-in de `prototype-leanwork` e `context-leanwork` passa a dizer o que de fato promete. "Nunca se auto-invoca" usava o termo com sentido diferente do que ele tem no Claude Code, e travar a invocação pelo modelo — o caminho que o campo `disable-model-invocation` abriria — quebraria `/leanwork-prototype` e `/leanwork-context`, que delegam para essas skills. As duas continuam invocáveis; a promessa, agora escrita, é não rodar sem pedido direto ou aceite explícito do usuário

## 1.6.5

`templates/` sai da v1.0 e volta a descrever o pipeline que existe. O exemplo end-to-end ganha os dois artefatos que faltavam — SPEC-UI e relatório de review —, mais colunas `UI` e `R` na matriz e um `R-01` que devolve a tarefa para `Bloqueado`. Deixa de ser documentação solta: as cinco skills que produzem artefato passam a apontar para ele. `folder-conventions.md` para de mandar tirar a SPEC-UI de `docs/`, e o sufixo de estado se unifica em `.limiteExcedido`

## 1.6.4

o plugin passa a calibrar as próprias permissões, não só as dos outros: os 13 comandos e skills declaram `allowed-tools`, cada um pré-aprovando leitura mais a pasta do artefato que ele mesmo produz (`Edit(docs/prds/**)` no PRD, `Edit(docs/reviews/**)` no review, e assim por diante). `Bash` não é pré-autorizado em lugar nenhum, e quem escreve fora de `docs/` — `/leanwork-execute`, que gera código, e `/leanwork-context`, que grava `.claude/settings.json` — continua pedindo confirmação. *(Revisto parcialmente na `1.10.0`: três arquivos passaram a declarar `Bash(python:*)` para rodar os gates. O resto da decisão continua valendo.)*

## 1.6.3

receita de Docker recalibrada: `docker compose down` sai do `allow` porque `down -v` remove volumes nomeados e anônimos — banco local, seed, fixtures —, e `stop`/`start` cobrem o ciclo cotidiano sem tocar em nada persistente. `docker volume rm` e `docker volume prune` entram no `deny`, rota mais curta para a mesma perda. Fica escrito por que estreitar o `allow` vence tentar negar só a flag, e qual buraco permanece

## 1.6.2

a outra metade da mesma mecânica: qual regra decide. A precedência `deny` → `ask` → `allow` ignora especificidade, então regra estreita no `allow` sob regra larga no `ask` é código morto. `Bash(npx tsc:*)` removido da receita de Node, a nota que prescrevia esse padrão reescrita, e o catálogo ganha a seção "Sombra de prefixo entre baldes" com o procedimento de conferência

## 1.6.1

catálogo de permissões corrigido na semântica de casamento do `Bash`: o `:*` equivale a ` *` e o espaço faz parte da regra, o que torna toda regra de prefixo dependente da ordem dos argumentos. O `deny` de force push passa de uma regra para seis, cobrindo `-f` e a flag depois do remote; `--force-with-lease` segue no `ask`, agora por escrito

## 1.6.0

a execução ganha dono: novo comando `/leanwork-execute`, que carrega o contexto declarado pela tarefa e devolve o estado ao plano. Vocabulário de status unificado (`Pendente` / `Em andamento` / `Concluído` / `Bloqueado`) como contrato entre o plano e os comandos que o leem. Review passa a fechar o loop — finding Bloqueante volta como `Status: Bloqueado` na tarefa — e o re-review de round N+1 entra no fluxo principal. Instalação por marketplace local

## 1.5.0

adição do `REFERENCES.md`: as fontes de engenharia de software por trás de cada fase, com marcação de reprodução/adaptação/autoria, divergências deliberadas com a literatura e lacunas conhecidas. README realinhado ao pipeline de seis skills

## 1.4.0

adição da skill `prototype-leanwork` + comando `/leanwork-prototype`: protótipo vira especificação rastreável (SPEC-UI) com `UI-XX` e estados. Rastreabilidade estendida para `ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R`, novo eixo 6 no reviewer, campo `Telas:` no plano. Fase opcional — projeto sem interface pula inteira e o `/leanwork-trace` não reclama

## 1.3.0

geração de permissões: `.claude/settings.json` calibrado pela stack via `/leanwork-context permissoes`, com o catálogo `allow`/`ask`/`deny` por ecossistema e detecção de drift entre o `CLAUDE.md` e a realidade do repositório

## 1.2.0

adição da skill `context-leanwork` + comando `/leanwork-context` para gerar `CLAUDE.md` (raiz e módulos). Sempre opt-in: `architect-leanwork`, `reviewer-leanwork` e `/leanwork-next` apenas sugerem, nunca geram automaticamente

## 1.1.0

adição da skill `reviewer-leanwork` + comando `/leanwork-review` + extensão de `/leanwork-trace` e `/leanwork-next` para considerar reviews + rastreabilidade estendida com `R-XX`

## 1.0.0

três skills (architect, prd, planner) + três comandos + rastreabilidade ADR/RN/CA/T + templates segregados
