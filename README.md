# Leanwork SDD Plugin

Pipeline **Spec-Driven Development** para projetos Leanwork. Seis skills coordenadas — arquitetura, requisitos, interface, plano, review e contexto do agente —, quatro comandos, gates determinísticos disparados por hook e rastreabilidade cruzada por IDs, do requisito ao commit.

```
1. Architect  →  2. PRD  →  3. Protótipo*  →  4. Planner  →  5. Execução  ⇄  6. Review
                                                             └── uma fatia por ciclo ──┘
Trilha rápida:  plano de uma tarefa (cenários na própria tarefa)  →  Execução  ⇄  Review

context-leanwork — transversal, sempre opt-in          * opcional — só para PRDs com interface
```

A execução é uma fase do pipeline, não um intervalo entre fases. `/leanwork-execute` pega uma tarefa por vez, carrega o contexto que o plano declarou (`RN` / `CA` / `ADR` / `UI`), devolve o estado ao plano e sugere o commit com o trailer; `/leanwork-review` valida num sub-agente de contexto limpo e, se bloquear, devolve o bloqueio ao plano também. O campo `**Status:**` da tarefa é o único lugar onde o estado vive; a trilha de auditoria vem do `git log`, pelo trailer `Refs: T-XX, CA-XX` de cada commit.

O que separa este pipeline de um conjunto de prompts é a camada de verificação: gates com exit code, autor diferente do verificador, sensor de discriminação nos testes e a regra "evidência ou zero" na cobertura. A coreografia em volta foi enxugada na 2.0.0 ([`CHANGELOG.md`](CHANGELOG.md)); a verificação não.

## Comandos

| Comando | O que faz |
|---------|-----------|
| `/leanwork-pipeline` | Ponto de entrada. Sem artefatos, conduz a entrada — fluxo completo, trilha rápida ou ponto de partida. Com artefatos, lê o estado via `status.py` e sugere a próxima ação |
| `/leanwork-execute` | Executa uma tarefa carregando o contexto declarado e atualiza o `Status`. Antes de implementar, `validate_ids.py` barra ID citado que não existe na origem |
| `/leanwork-review` | Roda `reviewer-leanwork` num sub-agente de contexto limpo. Finding `Bloqueante` volta como `Status: Bloqueado` no plano |
| `/leanwork-trace` | Matriz `ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R` e lacunas, gerada pelo `trace.py` |

As skills também são invocáveis direto pelo namespace do plugin: `/leanwork-sdd:prd-leanwork`, `/leanwork-sdd:prototype-leanwork`, `/leanwork-sdd:context-leanwork` e assim por diante.

## Skills

| Skill | Fase | Entrada | Saída | IDs que produz |
|-------|------|---------|-------|----------------|
| `architect-leanwork` | 1 — Arquitetura | Briefing de negócio | Proposta arquitetural + ADRs + C4 | `ADR-XX` |
| `prd-leanwork` | 2 — Requisitos | Demanda (com ou sem arquitetura) | PRD com regras + Gherkin | `RN-XX`, `CA-XX` |
| `prototype-leanwork` | 3 — Interface *(opcional)* | PRD com interface + protótipo (se houver) | SPEC-UI com telas e estados | `UI-XX`, `UI-XX.estado` |
| `planner-leanwork` | 4 — Plano | PRD aprovado (+ SPEC-UI) ou mudança pequena | Plano com fatias executáveis | `T-XX` |
| `reviewer-leanwork` | 6 — Review | Diff + plano + PRD + arquitetura + SPEC-UI | Relatório de review por tarefa | `R-XX` |
| `context-leanwork` | Transversal | Artefatos do pipeline + repositório | `CLAUDE.md` raiz e módulos, `settings.json` | — |

Todas são **stack-agnósticas**: a stack vem da decisão arquitetural e do `CLAUDE.md` do projeto, nunca da skill. Cada SKILL.md abre com uma seção de **regras pinadas** — o que não se negocia —, e as entrevistas seguem a mesma regra: fato se busca no repositório e nos artefatos; decisão se pergunta, no máximo duas por vez, com a recomendação.

Templates e catálogos ficam em `references/` de cada skill e só carregam quando o agente vai gerar o documento (progressive disclosure). Convenções compartilhadas ficam em `templates/` — `id-conventions.md` e `folder-conventions.md`.

> **Regra de manutenção.** `templates/` descreve o pipeline inteiro, então toda skill ou fase nova obriga uma varredura dos dois arquivos antes do release. A contagem de skills e as colunas da matriz são os pontos que envelhecem primeiro.

## Fatia vertical por `CA-XX`

A unidade de trabalho é a **fatia**: uma `T-XX` fecha um ou mais cenários `CA-XX` ponta a ponta, atravessando as camadas que aquele comportamento precisa, e termina com o cenário verde. Começa pelo caminho feliz; erro e borda vêm nas fatias seguintes. O tamanho se mede por caber num ciclo de `/leanwork-execute` + `/leanwork-review` com a suíte verde, não em horas.

Fatia horizontal (uma camada por tarefa) fica para três exceções: fundação, migrations e refactor **expandir → migrar → contrair**. O motivo da inversão, que reverte o padrão da 1.8.0, está em [`REFERENCES.md`](REFERENCES.md): granularidade compra ordem, não correção, e tarefa de camada passa pelo review sem cenário para o sensor atacar.

Cada tarefa declara `**Portas de mão única:**` — migration, contrato público, schema, permissão. É o que o review cobra como escopo: arquivo extra não é finding, porta de mão única não declarada é `Bloqueante`.

## Trilha rápida

Mudança pequena e reversível não precisa de PRD nem de plano completo. A trilha rápida é **um plano de uma tarefa**, com cabeçalho `**PRD de referência:** nenhum — trilha rápida` e os cenários `CA-XX` em Gherkin dentro da própria tarefa (template em `planner-leanwork/references/plan-template-quick.md`).

- **Entrada:** menos de ~3 arquivos e nenhuma porta de mão única
- **Saída:** se a mudança crescer, a tarefa vira `Bloqueado` e o fluxo completo assume. Uma `T-02` no plano de trilha rápida reprova no gate — é o sinal de que a mudança não cabe nela
- **Review continua obrigatório:** a trilha encurta o planejamento, não a verificação

## Gates e scripts (`scripts/`)

Python 3.8+, stdlib apenas, contrato uniforme: **exit 0** aprova, **1** reprova por conteúdo, **2** por uso errado. `--strict` promove warning a erro.

| Script | Papel |
|---|---|
| `validate_plan.py` | Gate do plano: campos obrigatórios, vocabulário de `Status`, sequência de `T-XX`, dependência para frente, trilha rápida com uma tarefa só |
| `validate_review.py` | Gate do review: finding sem `arquivo:linha`, cobertura sem asserção reproduzida, `Bloqueante` com recomendação diferente de `Bloqueado` |
| `validate_ids.py` | Gate de rastreabilidade: `RN`/`CA`/`ADR`/`UI` citado que não existe no artefato de origem |
| `check_commit.py` | Trailer `Refs:` do commit — também instalável como hook `commit-msg` do git |
| `hook_gate.py` | Hook `PostToolUse` do plugin: escolhe o validador pelo caminho editado |
| `status.py` | Estado do pipeline e próxima tarefa elegível (relatório, não gate) |
| `trace.py` | Matriz de rastreabilidade e lacunas (relatório) |
| `selftest.py` | Suíte dos scripts — roda antes de qualquer mudança neles ser commitada |

`validate_plan.py` e `validate_review.py` rodam por hook do plugin (`hooks/hooks.json`): toda gravação em `docs/plans/` ou `docs/reviews/` dispara o validador, e a reprovação volta ao modelo para correção — o gate não depende de o agente lembrar dele. `validate_ids.py` é chamado por `/leanwork-execute` antes de implementar, porque não depende de edição.

**Degradação silenciosa.** Sem hook e sem ferramenta de execução no ambiente, a regra é conferir à mão **e dizer no chat que o gate automático não rodou**. Degradação silenciosa é pior que gate nenhum, porque parece gate: quem lê o resultado confia numa verificação que não aconteceu. Toda skill e comando com gate aplica esta regra e aponta para cá.

## Rastreabilidade cruzada

```
ADR-002 (arquitetura: lock pessimista para estoque)
   ↓ justifica
RN-05 (PRD: estoque decrementado atomicamente)
   ↓ valida em
CA-06 (PRD: cenário de estoque esgotando durante compras concorrentes)
   ↓ acontece em
UI-02.esgotado (SPEC-UI: estado da tela de confirmação)   ← opcional
   ↓ implementado em
T-07 (plano: fatia que fecha CA-06)  →  commit com "Refs: T-07, CA-06"
   ↓ validado por
R-XX (review: findings da implementação de T-07)
   ↓ verificado por
Teste CA_06_estoque_esgota_durante_compra (código)
```

Cada artefato declara seus elos: ADRs numerados sem reúso na proposta; `Cenário [CA-01]:` com passos citando `(RN-XX)` e `(ADR-XX)` no PRD; `UI-XX` mapeando `RN`/`CA` na SPEC-UI; `**Implementa:**`, `**Valida:**`, `**Decisões base:**` e `**Telas:**` em cada tarefa do plano; eixo e referências cruzadas em cada `R-XX`. O `trace.py` percorre os elos — incluindo o `git log` — e monta a matriz com estado de execução e de review por tarefa.

## O review

- **Autor ≠ verificador.** `/leanwork-review` despacha um sub-agente de contexto limpo, com payload autossuficiente. O raciocínio da implementação fica de fora de propósito: quem recebe a justificativa julga se ela convence, não se o código cumpre o spec.
- **Seis eixos.** Aderência ao plano, rastreabilidade, aderência ao spec, cobertura de teste, qualidade do código calibrada pelo `CLAUDE.md` do projeto e, quando há SPEC-UI, conformidade de interface — estrutura, estados e comportamento, nunca estética.
- **Evidência ou zero.** `CA-XX` só conta como coberto com `arquivo:linha` e a asserção reproduzida; nome de método de teste não é evidência.
- **Sensor de discriminação.** O eixo 4 injeta um defeito no código novo, em scratch fora da árvore do usuário, e observa se a suíte quebra. Mutante sobrevivente é `Bloqueante`.
- **Não faz:** review de formatação, threat modeling completo, otimização de performance fora dos atributos prioritários, preferência pessoal não declarada no projeto.

## Interface como especificação

Protótipo tem dois papéis: descoberta (descartável) e especificação (o contrato que o dev implementa). A `prototype-leanwork` trata do segundo. Ela indexa o que existe — HTML/React no repositório, imagens, Figma via MCP, export de Lovable/v0 — e só gera protótipo quando não há, delegando o craft visual para skills de frontend do ambiente.

O valor está nos estados. Todo `CA-XX` cujo `Então` descreve rejeição ou erro corresponde a um estado de tela; cada estado ganha ID (`UI-02.esgotado`), o plano declara quais implementa e o review verifica um a um. Projeto sem interface pula a fase inteira, e a SPEC-UI é por PRD, não por projeto.

## Contexto para o agente

As cinco skills do pipeline produzem documentos **para humanos**. A `context-leanwork` gera a ponte para o agente: `CLAUDE.md` da raiz e de módulos escolhidos, e `.claude/settings.json` com `allow`/`ask`/`deny` calibrados pela stack detectada.

- **Nunca destrutiva.** Só atualiza blocos entre `<!-- leanwork-context:start -->` e `<!-- leanwork-context:end -->`; arquivo escrito à mão nunca é sobrescrito, e o diff vem antes da gravação.
- **Comandos de inspeção real.** `package.json`, `Makefile`, `.csproj`, `pyproject.toml` — sem comando de teste no repo, o resultado é um TODO, não um comando chutado.
- **Raiz e módulo não se repetem.** Módulo só traz responsabilidade, domínio, boundaries e convenções que divergem da raiz.

### Sempre opt-in

Nenhuma skill gera `CLAUDE.md` nem SPEC-UI por conta própria. As outras partes do pipeline apenas **sugerem**:

| Momento | Quem sugere |
|---------|-------------|
| Proposta arquitetural concluída | `architect-leanwork` (checklist final) |
| Review rodou degradado por falta de `CLAUDE.md` | `reviewer-leanwork` |
| Review detectou padrão emergente não documentado | `reviewer-leanwork` (Notas ao processo) |
| Projeto tem artefatos do pipeline mas nenhum `CLAUDE.md` | `/leanwork-pipeline` |
| Módulo novo apareceu no repositório | `/leanwork-pipeline` |
| Projeto tem código mas nenhum `.claude/settings.json` | `/leanwork-pipeline` |
| Primeiro scaffolding concluído (comandos de build passam a existir) | `/leanwork-pipeline` |

A `prototype-leanwork` segue a mesma regra — também opcional, também só por sugestão ou pedido direto:

| Momento | Quem sugere |
|---------|-------------|
| PRD com interface aprovado, sem SPEC-UI | `prd-leanwork` ao concluir; `/leanwork-pipeline` |
| Plano prestes a ser gerado para PRD com UI | `planner-leanwork` |
| Review encontrou tela sem especificação | `reviewer-leanwork` |

Em todos os casos a sugestão é convite: se o usuário ignorar, o pipeline segue normalmente. Nenhuma skill usa `disable-model-invocation` — o opt-in é a promessa de não rodar sem pedido ou aceite, não uma trava de invocação.

## Fluxo típico

```
/leanwork-pipeline "Sistema de gestão de tickets multi-tenant"
  → architect → ADR-001..ADR-005
  → prd → RN-01..RN-08, CA-01..CA-15
  → prototype-leanwork → UI-01..UI-06 + estados   (opcional — tem interface)
  → planner → T-01..T-09 (fatias por CA)          (hook valida o plano a cada gravação)

/leanwork-execute T-04
  → validate_ids.py; carrega RN-03, CA-01, CA-03, ADR-002, UI-02 (default, esgotado)
  → teste na costura, implementação, suíte verde
  → sugere o commit "Refs: T-04, CA-01, CA-03" (check_commit.py); T-04: Status Concluído

/leanwork-review T-04
  → sub-agente → REVIEW-T-04-2026-06-15.md (R-01..R-03, 1 Bloqueante)
  → T-04 volta para Status: Bloqueado, com Bloqueio: R-01 (REVIEW-T-04-2026-06-15)

/leanwork-pipeline            (retomar)
  → status.py: T-04 Bloqueado; próxima elegível T-05
```

Mudança pequena entra por `/leanwork-pipeline` → trilha rápida → `/leanwork-execute T-01` → `/leanwork-review T-01`. O exemplo completo, com os cinco artefatos preenchidos e IDs cruzados, está em `stacks/dotnet/pipeline-example.md`.

## Filosofia

- **SDD pragmático, não ortodoxo.** Princípios do Spec Kit e do Kiro adaptados ao contexto Leanwork: Gherkin em PT-BR, agentes de IA como executores naturais, Azure DevOps como opção, não como pressuposto.
- **Sai a coreografia, fica a verificação.** Os modelos seguem instrução concisa e inferem contexto do repositório; continuam declarando conclusão sem prova e escrevendo teste raso. O pipeline aposta onde eles erram.
- **Português é padrão.** Termos técnicos consagrados podem ficar em inglês.
- **Sem cronograma, sem estimativa.** O pipeline produz "o quê", "por quê" e "em que ordem". "Quando" e "quanto" são do planejamento de sprint.
- **Stack-agnóstico no núcleo.** Código real de uma stack fica isolado em `stacks/` (ver [`stacks/README.md`](stacks/README.md)).
- **Lacuna declarada vale mais que lacuna preenchida.** Matriz honestamente incompleta é informação; matriz fechada com suposição é armadilha.

## Instalação

O plugin é distribuído internamente: o próprio repositório é o marketplace, adicionado por caminho local.

```bash
git clone https://github.com/leanwork/leanwork-sdd.git
claude plugin marketplace add ./leanwork-sdd
claude plugin install leanwork-sdd@leanwork
```

`leanwork-sdd` é o plugin e `leanwork` é o marketplace. Para atualizar depois de um `git pull`: `claude plugin marketplace update leanwork`. Os hooks e scripts chamam `python`, que precisa estar no `PATH`.

Para desenvolver o próprio plugin, `claude --plugin-dir /caminho/para/leanwork-sdd` carrega o diretório sem instalar, só na sessão atual. Depois de instalar, `/plugin` confirma que as skills foram carregadas.

## Crédito e inspiração

Pipeline desenhado por Mick Banagouro (Leanwork). Princípios SDD inspirados em [GitHub Spec Kit](https://github.com/github/spec-kit) e [AWS Kiro](https://kiro.dev); filosofia arquitetural no *Manual do Arquiteto de Software* de Elemar Júnior; trilha rápida e enxugamento da 2.0.0 adaptados de `tlc-spec-lean` (Tech Leads Club).

**[REFERENCES.md](REFERENCES.md)** documenta a base de engenharia por trás de cada fase, marcando o que é reprodução, adaptação ou contribuição própria, onde o pipeline **diverge** da literatura de propósito e onde ainda tem **lacunas**. O histórico de versões está em **[CHANGELOG.md](CHANGELOG.md)**.
