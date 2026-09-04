---
name: prototype-leanwork
description: Especificação de interface a partir de protótipo — ingestão de protótipo existente (HTML exportado, imagens, Figma via MCP, Lovable/v0 exportado) ou geração de protótipo navegável quando não houver. Produz o documento SPEC-UI com inventário de telas (UI-XX), estados por tela e mapeamento cruzado com regras de negócio (RN-XX) e cenários Gherkin (CA-XX) do PRD. Use quando o usuário pedir "especificar as telas", "documentar o protótipo", "criar protótipo", "mapear telas contra o PRD", "gerar SPEC-UI", "indexar o Figma", ou quando aceitar sugestão de especificar interface antes do plano de execução. Roda entre o PRD e o plano de execução, e é opcional — projetos sem interface (API, worker, CLI, biblioteca) pulam esta fase inteiramente. NÃO faz design visual próprio — delega o craft de tipografia, paleta e composição para skills de frontend disponíveis no ambiente. NÃO inventa telas ou estados não observados no protótipo — declara a lacuna e pergunta.
allowed-tools: Read, Glob, Grep, Edit(docs/prototype/**)
---

# Prototype Leanwork — Especificação de Interface

Esta skill produz a **SPEC-UI**: o documento que transforma protótipo em especificação rastreável. É a ponte entre o PRD (que diz *o quê* e *por quê*) e o plano de execução (que diz *o que fazer*), respondendo *como isso aparece na tela*.

O valor não está em desenhar bonito — está em **amarrar cada tela às regras de negócio que ela materializa**, para que o plano dimensione corretamente e o review consiga verificar conformidade.

## Princípios

- **Ingestão primeiro, geração como fallback.** Se existe protótipo, ele é a fonte de verdade. Gerar só quando não houver.
- **Nunca inventar tela ou estado.** O que não foi observado no protótipo vira lacuna declarada, não suposição preenchida.
- **Rastreabilidade é o produto.** O mapeamento `UI-XX ↔ RN-XX ↔ CA-XX` é o que justifica a fase existir.
- **Design-agnóstica.** O craft visual é delegado a skills de frontend do ambiente. Esta skill cuida de estrutura, estados e rastreabilidade.
- **Opcional por natureza.** Projeto sem interface pula. PRD sem interface pula. Nunca bloquear o pipeline por ausência de SPEC-UI.
- **Origem sempre declarada.** Cada informação no documento marca se foi extraída do protótipo ou informada pelo usuário.

## Fase 0 — Verificar se a fase se aplica

Antes de qualquer coisa, confirmar que o PRD tem interface. Sinais de que **não** tem:

- Arquitetura sem container de frontend (só API, worker, job, CLI, biblioteca)
- PRD sem seção de Personas e sem fluxos de interação
- Cenários Gherkin descrevem apenas comportamento de sistema (jobs, integrações, eventos), sem ator humano em tela

Se não se aplica, informar ao usuário e encerrar:

> Este PRD não descreve interface de usuário — os cenários são de integração e processamento. A fase de protótipo não se aplica aqui. Pode seguir direto para o plano de execução com `planner-leanwork`.

**Não insistir.** Especificar UI onde não há UI é ruído.

Quando o PRD tem interface **parcial** (algumas features com tela, outras não), especificar apenas as que têm e registrar explicitamente as que ficaram de fora e por quê.

## Fase 1 — Determinar o modo

Perguntar uma vez, com opções claras:

> Como vamos trabalhar a interface?
>
> **A.** Já tenho protótipo — quero indexar e mapear contra o PRD *(modo ingestão)*
> **B.** Não tenho protótipo — quero gerar um *(modo geração)*
> **C.** Tenho protótipo parcial — indexar o que existe e gerar o que falta *(modo híbrido)*

O modo **C** é comum: cliente entregou 4 telas principais, mas os estados de erro e as telas administrativas não foram desenhadas.

## Fase 2 (modo ingestão) — Extrair do protótipo

Ver `references/ingestion-guide.md` para o procedimento detalhado por formato.

**Ordem de tentativa recomendada:** HTML exportado → imagens → Figma via MCP → Lovable/v0 exportado para repositório.

Resumo do que cada formato entrega:

| Formato | Extração automática | Precisa perguntar |
|---|---|---|
| HTML/React no repositório | Alta — rotas, componentes, campos, classes, estados no código | Estados não implementados; intenção de negócio |
| Imagens (PNG/JPG) | Média — layout, campos, hierarquia, cores aproximadas | Navegação entre telas; estados não capturados; tokens exatos |
| Figma via MCP | Alta — frames, camadas, tokens, componentes | Fluxo de navegação; comportamento dinâmico |
| Lovable/v0 exportado | Alta — igual ao caso HTML/React | Igual ao caso HTML/React |

**Regra crítica:** ao final da extração, listar explicitamente **o que não foi possível extrair** antes de perguntar. O usuário precisa saber onde a skill está cega.

Exemplo:

> Extraí 6 telas das imagens. Não consigo determinar por elas:
> - Qual tela leva a qual (navegação)
> - Estados de carregamento e erro (não aparecem nos prints)
> - Valores exatos de cor — identifiquei "azul escuro" mas não o hex
>
> Posso perguntar sobre esses pontos, ou você prefere anexar mais material?

## Fase 3 (modo geração) — Gerar o protótipo

Ver `references/generation-guide.md` para arquétipos, condução e delegação.

Fontes, em ordem de precedência:

1. **PRD** — personas, fluxos, regras, cenários e permissionamento definem quais telas existem e quais estados cada uma tem
2. **Arquitetura** — stack do frontend, SPA vs SSR, biblioteca de componentes obrigatória, restrições de acessibilidade e i18n
3. **Repositório** — design tokens, tema, componentes e telas já existentes. O protótipo **herda**, não reinventa
4. **Entrevista** — apenas as lacunas que as três fontes anteriores não cobrem

### Delegação do craft visual

Esta skill **não** decide tipografia, escala, paleta ou composição. Ela monta o briefing estruturado (arquétipo, telas, estados, tokens conhecidos, restrições) e delega para uma skill de frontend disponível no ambiente.

Se não houver skill de frontend disponível, gerar HTML simples e funcional, focado em **estrutura e estados** — e declarar no documento que a fidelidade é de wireframe, não visual final.

### Entrevista

Seis blocos, **pulando o que já foi respondido** pelas fontes anteriores. Com PRD e arquitetura bem-feitos, normalmente sobram 2-3 perguntas.

| Bloco | Pergunta | Pula quando |
|---|---|---|
| Arquétipo | Admin/dashboard, site institucional, app de operação, e-commerce, portal, ferramenta interna? | PRD deixa óbvio |
| Dispositivo | Desktop-first, mobile-first, mobile-only, responsivo pleno? | Arquitetura declara |
| Fidelidade | Wireframe (estrutura e estados) ou alta fidelidade? | — sempre perguntar |
| Identidade | Existe marca ou design system? | Repositório tem tokens, ou arquitetura declara biblioteca |
| Densidade e tom | Denso tipo ERP ou espaçoso tipo consumer? Formal ou descontraído? | Arquétipo já implica fortemente |
| Restrições | Acessibilidade, tema escuro, i18n, biblioteca obrigatória? | Arquitetura já lista |

**Sobre identidade visual:** nunca fazer pergunta aberta do tipo "que cores você quer". Pergunta aberta gera resposta ruim e protótipo genérico. Em vez disso:

- **Cliente tem marca** → pedir referência (site, manual, assets) e extrair
- **Repositório tem design system** → detectar e seguir, sem perguntar
- **Greenfield sem identidade** → propor 2-3 direções concretas e nomeadas para o usuário escolher

## Fase 4 — Mapear contra o PRD

O coração da skill. Para cada tela `UI-XX`, determinar:

- **Quais `RN-XX` se manifestam nela** — e como (validação de campo, estado desabilitado, mensagem, regra de exibição)
- **Quais `CA-XX` acontecem nela** — cada cenário Gherkin tem que acontecer em algum lugar
- **Quais estados a tela precisa ter** para cobrir esses cenários

### Cruzamento reverso — onde está o valor real

Percorrer o PRD e verificar cobertura na direção inversa:

| Lacuna | Significado | Ação |
|---|---|---|
| `CA-XX` sem tela | Cenário do PRD não tem onde acontecer | Apontar. Pode ser cenário de backend (ok) ou tela faltando (problema) |
| `RN-XX` de interface sem manifestação | Regra que deveria aparecer na tela não aparece | Apontar — provável tela incompleta |
| Tela sem `RN-XX` nem `CA-XX` | Tela que o PRD não pediu | Apontar — pode ser escopo extra ou lacuna do PRD |
| Estado ausente | Cenário de erro do PRD sem tela correspondente | Apontar — a causa mais comum de bug de UI |

**Nunca gerar a tela faltante silenciosamente para "fechar" a matriz.** Declarar a lacuna e deixar a decisão com o usuário: gerar a tela, ajustar o PRD, ou aceitar como fora de escopo.

## Fase 5 — Produzir o documento

Usar `references/spec-ui-template.md`. Salvar como `docs/prototype/SPEC-UI-XXX-nome-kebab.md`, usando **o mesmo número do PRD** correspondente.

O documento contém: inventário de telas com `UI-XX`, estados por tela, mapeamento cruzado, componentes reutilizáveis, tokens de design, lacunas identificadas e link para o artefato visual.

Ver `references/screen-states.md` para o catálogo de estados — a seção mais valiosa do documento, porque é onde a maioria dos bugs de interface nasce.

## Convenções de ID

`UI-XX` segue as regras gerais do pipeline (ver `${CLAUDE_PLUGIN_ROOT}/templates/id-conventions.md`):

- Numeração sequencial global ao documento SPEC-UI (`UI-01`, `UI-02`, ..., `UI-NN`)
- Largura mínima de 2 dígitos
- Sem reúso — tela removida mantém o ID marcado como removido
- **Estados usam sufixo com ponto**: `UI-02.erro`, `UI-02.vazio`, `UI-02.carregando`. Permite ao plano e ao review referenciarem estado específico

## Integração com o resto do pipeline

**Para o planner:** as tarefas de interface ganham o campo `Telas:` listando `UI-XX` e os estados envolvidos. O inventário de componentes reutilizáveis evita que o plano crie tarefas duplicadas para o mesmo componente.

**Para o reviewer:** a SPEC-UI vira critério de conformidade — a tela implementada tem todos os estados especificados? Os campos batem? A skill de review avalia **estrutura, estados e comportamento**, não estética.

**Para o trace:** `UI-XX` entra na cadeia `ADR → RN → CA → UI → T → R`.

## O que NÃO incluir na SPEC-UI

- **Código de componente.** Isso é implementação, pertence às tarefas do plano.
- **Regras de negócio redigidas de novo.** Referenciar `RN-XX`; não reescrever.
- **Especificação de pixel.** Medidas exatas, espaçamentos e escalas vivem no protótipo e no design system, não em markdown.
- **Copy final de textos longos.** Mensagens curtas de erro e rótulos de botão são úteis; parágrafos inteiros não.
- **Telas especulativas.** "Talvez precisemos de uma tela de relatório" não entra. Se não está no PRD nem no protótipo, não existe.

## Quando sugerir esta skill

Nenhuma skill ou comando do pipeline a invoca sem aceite explícito do usuário — as demais apenas sugerem:

| Momento | Quem sugere |
|---|---|
| PRD com interface aprovado, sem SPEC-UI | `prd-leanwork` ao concluir; `/leanwork-next` |
| Plano prestes a ser gerado para PRD com UI | `planner-leanwork` |
| Review encontrou tela sem especificação | `reviewer-leanwork` |

A sugestão é convite. Se o usuário pular, o pipeline segue sem fase de interface e o plano simplesmente não terá campo `Telas:`.

Pedido direto ("especificar as telas", "documentar o protótipo") carrega a skill normalmente, e é para isso que a `description` lista as frases-gatilho. O que a skill não faz é rodar como efeito colateral de outra tarefa.

## Recursos auxiliares

- `references/spec-ui-template.md` — template do documento SPEC-UI
- `references/ingestion-guide.md` — extração por formato (HTML, imagens, Figma MCP, Lovable/v0)
- `references/generation-guide.md` — arquétipos de interface, condução da entrevista e delegação do craft visual
- `references/screen-states.md` — catálogo de estados de tela e quando cada um é obrigatório
- `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/pipeline-example.md` — exemplo end-to-end (calibrado em .NET) da mesma demanda nas cinco fases; consultar para ver como um `CA-XX` do PRD vira estado `UI-XX.sufixo` e como o plano e o review consomem esse estado
