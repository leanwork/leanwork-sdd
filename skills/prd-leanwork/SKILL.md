---
name: prd-leanwork
description: Levanta requisitos e gera PRD em PT-BR com regras RN-XX, cenários Gherkin CA-XX e diagramas Mermaid. Use quando pedirem para criar PRD, levantar requisito, documentar demanda, detalhar feature ou escrever especificação, ou quando uma demanda nova precisar virar documento para os devs. Não inclui estimativa, complexidade nem cronograma.
allowed-tools: Read, Glob, Grep, Edit(docs/prds/**)
---

# PRD Leanwork — Levantamento de Requisitos

Esta skill ajuda a transformar uma demanda (ideia, conversa com cliente, feature solicitada) em um Product Requirement Document detalhado o suficiente para que um desenvolvedor execute sem precisar adivinhar nada.

O público-alvo do PRD são os devs do time. O documento precisa ser preciso o bastante para eliminar ambiguidade, mas não tão burocrático que ninguém leia. Estimativa, esforço e complexidade ficam **fora** deste documento — são tratados em outro momento (planning, refinamento). O PRD responde "o quê" e "por quê", não "quanto custa".

## Regras pinadas

O que não se negocia nesta skill. O restante do texto é orientação; isto é regra.

1. Não inventar nem preencher com `[A DEFINIR]`: sem insumo, perguntar; com "gera assim mesmo", marcar `> ⚠️ **Premissa:**`.
2. Regras `RN-XX` e cenários `CA-XX` sempre presentes, mesmo em PRD curto — são o que o plano e o review consomem.
3. Gherkin em PT-BR (`Funcionalidade`, `Cenário`, `Dado`, `Quando`, `Então`), sem mistura com inglês.
4. Sem estimativa, complexidade ou cronograma.

## Fluxo geral

A skill opera em duas fases:

1. **Entrevista estruturada** — fazer perguntas até ter material suficiente para um PRD útil. Não inventar nada, não preencher com `[A DEFINIR]`. Se não houver insumo, perguntar.
2. **Geração do PRD** — produzir markdown completo seguindo o template abaixo, com Mermaid e Gherkin onde fizer sentido.

## Fase 1 — Entrevista estruturada

**Busca antes de pergunta.** Fato se busca — no repositório, no `CLAUDE.md`, nos artefatos do pipeline e no que o usuário já colou. Decisão se pergunta: no máximo duas por vez, cada uma com opções concretas e a recomendação marcada.

Cada dimensão abaixo termina **respondida** (pela busca ou pelo usuário) ou marcada `n/a — motivo`. Dimensão sem um dos dois é lacuna, e lacuna impede a geração. Começar pelo "porquê" e descer para o "como".

### Dimensões a cobrir

**Contexto e problema**
- Problema e quem sente a dor hoje
- Cliente, produto ou módulo afetado
- Processo ou sistema atual que faz isso de outro jeito
- Impacto de não fazer

**Objetivo e escopo**
- Resultado esperado, em uma frase
- Usuários impactados (perfis, papéis, personas)
- Dentro do escopo
- Fora do escopo — tão importante quanto o que entra
- Demandas relacionadas que não fazem parte desta e podem confundir

**Comportamento e regras**
- Regras de negócio: validações, limites, condições, exceções
- Fluxos principais, alternativos e de erro
- Permissionamento: quem vê e faz o quê
- Restrições legais, regulatórias ou de compliance

**Integrações e dados**
- Sistemas externos ou módulos internos envolvidos
- Dados consumidos e dados produzidos ou persistidos
- Eventos disparados ou consumidos

**Aceitação e riscos**
- Como saberemos que está pronto (alto nível — vira Gherkin depois)
- Riscos técnicos, de negócio, de prazo, de dependência
- Dependências de outros times, fornecedores ou decisões pendentes

### Quando parar

Dá para escrever cada seção do template sem inventar: nenhuma seção ficaria vazia ou genérica por falta de insumo. Dimensão que não se aplica (ex.: integrações) fica `n/a — motivo`, não pergunta.

## Fase 2 — Geração do PRD

Use o template completo em `references/prd-template.md`. Leia o arquivo antes de gerar o PRD; ele contém a estrutura exata com todas as seções obrigatórias (visão, problema, objetivo, escopo, hierarquia Epic→Feature→PBI, fluxos, regras de negócio com IDs `RN-XX`, critérios de aceite Gherkin com IDs `[CA-XX]`, riscos) e opcionais (personas, permissionamento, integrações, diagrama de estados, arquitetura técnica).

Recursos auxiliares:

- `references/gherkin-examples.md` — exemplos calibrados de cenários Gherkin com IDs cruzados, cobrindo caminho feliz, validação, erro de regra, concorrência, integração externa, esquemas com tabela e cenários condicionais por permissão. Inclui anti-padrões a evitar.
- `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/pipeline-example.md` — exemplo end-to-end (calibrado em .NET) da mesma demanda nas cinco fases; consultar para ver como as `RN-XX` e os `CA-XX` deste PRD viram estado de tela, tarefa de execução e finding de review.

Manter a hierarquia de headings e a ordem das seções. Seções que não se aplicam podem ser omitidas, **menos** as marcadas como obrigatórias.

## Ao entregar o PRD

Se o PRD descreve interface de usuário (tem personas, fluxos de interação, cenários com ator em tela), **sugerir** — sem executar — a fase de especificação de interface:

> Este PRD tem interface. Antes do plano de execução, a skill `prototype-leanwork` pode indexar o protótipo (se você já tiver) ou gerar um, mapeando cada tela contra as regras e cenários daqui. Isso faz o plano dimensionar melhor as tarefas de UI e permite ao review verificar se todos os estados de tela foram implementados. Rode com `/leanwork-sdd:prototype-leanwork` se fizer sentido.

Se o PRD **não** tem interface (integração, job, processamento, API pura), não sugerir nada — seguir direto para o plano.

A sugestão é convite, não etapa obrigatória. Ignorá-la não bloqueia o pipeline.

---

## Convenções Leanwork

- **Idioma:** todo o PRD em português (Brasil), incluindo títulos das seções, regras de negócio e Gherkin. Termos técnicos consagrados (API, endpoint, queue, webhook) podem permanecer em inglês.
- **Mermaid:** usar sempre que houver fluxo, máquina de estados ou arquitetura. Diagramas devem caber em uma tela — se ficar grande demais, quebrar em sub-fluxos.
- **Gherkin em PT-BR:** `Funcionalidade`, `Cenário`, `Dado`, `Quando`, `Então`, `E`, `Mas`. Não misturar com inglês.
- **Hierarquia:** Epic → Feature → PBI, sempre. Mesmo que a demanda inteira caiba em uma única Feature, deixar a hierarquia explícita para facilitar o cadastro no Azure DevOps.
- **Numeração de regras e cenários:** `RN-01`, `RN-02` para regras de negócio; `CA-01`, `CA-02` para cenários Gherkin (critérios de aceite). Essa numeração é o ponto de costura com o plano de execução: o planner referencia esses IDs nas tarefas (`Implementa: RN-03`, `Valida: CA-01`), permitindo rastrear do código até a regra de negócio original.
- **Referência cruzada com arquitetura:** quando uma regra ou cenário existe por causa de uma decisão arquitetural já tomada, citar o ADR correspondente entre parênteses (ex.: "RN-05: estoque decrementado atomicamente (ADR-002)").

## O que não incluir

- Estimativas (story points, horas, t-shirt sizing P/M/G).
- Complexidade técnica subjetiva.
- Detalhes de implementação que travem o dev (escolha de biblioteca específica, nome de classe, padrão de código). O PRD é "o quê" e "por quê" — o "como" fica com quem implementa.
- Cronograma ou prazo. Isso é planejamento, não requisito.

## Padrões de comportamento

**Quando o usuário cola uma conversa/transcrição como entrada:** extrair o que dá da conversa, identificar lacunas e fazer apenas as perguntas necessárias para completar. A conversa é fonte da busca: o que está nela não vira pergunta.

**Quando o usuário pede um PRD curto / leve:** ainda assim manter as seções obrigatórias, mas reduzir os opcionais. Nunca pular regras de negócio ou critérios de aceite — esses são o coração do PRD.

**Quando o usuário pede para revisar/melhorar um PRD existente:** apontar o que está faltando comparado ao template antes de reescrever. Pedir confirmação se for fazer mudanças estruturais grandes.

**Quando a demanda é grande demais para um único PRD:** sugerir quebra em múltiplos PRDs (um por Feature ou por Epic), e explicar a razão da quebra.
