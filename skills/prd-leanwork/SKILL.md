---
name: prd-leanwork
description: Levantamento estruturado de requisitos e geração de PRDs (Product Requirement Documents) detalhados em português, no padrão Leanwork. Use sempre que o usuário pedir explicitamente para "criar PRD", "levantar requisito", "documentar demanda", "detalhar feature", "escrever especificação" ou qualquer variação dessas expressões. Também use quando o usuário descrever uma demanda nova e indicar que precisa virar documento para os devs executarem. A skill conduz uma entrevista estruturada quando o contexto está incompleto, e produz markdown com hierarquia Epic→Feature→PBI, regras de negócio numeradas (RN-XX), critérios de aceite em Gherkin (PT-BR) com IDs (CA-XX) e diagramas Mermaid. Os IDs RN/CA são o ponto de costura com o plano de execução (planner-leanwork) e a arquitetura (architect-leanwork) — formam a matriz de rastreabilidade ADR ↔ RN ↔ CA ↔ UI ↔ T. NÃO inclui estimativa de esforço, t-shirt sizing ou complexidade — o foco é "o quê" e "por quê", não "quanto custa".
allowed-tools: Read, Glob, Grep, Edit(docs/prds/**)
---

# PRD Leanwork — Levantamento de Requisitos

Esta skill ajuda a transformar uma demanda (ideia, conversa com cliente, feature solicitada) em um Product Requirement Document detalhado o suficiente para que um desenvolvedor execute sem precisar adivinhar nada.

O público-alvo do PRD são os devs do time. O documento precisa ser preciso o bastante para eliminar ambiguidade, mas não tão burocrático que ninguém leia. Estimativa, esforço e complexidade ficam **fora** deste documento — são tratados em outro momento (planning, refinamento). O PRD responde "o quê" e "por quê", não "quanto custa".

## Fluxo geral

A skill opera em duas fases:

1. **Entrevista estruturada** — fazer perguntas até ter material suficiente para um PRD útil. Não inventar nada, não preencher com `[A DEFINIR]`. Se não houver insumo, perguntar.
2. **Geração do PRD** — produzir markdown completo seguindo o template abaixo, com Mermaid e Gherkin onde fizer sentido.

## Fase 1 — Entrevista estruturada

Antes de escrever uma linha do PRD, garantir que as informações abaixo estão claras. Se faltar algo, perguntar antes de gerar. As perguntas devem ser feitas em blocos lógicos, não todas de uma vez — começar pelo "porquê" e ir descendo para o "como".

### Bloco 1 — Contexto e problema

- Qual problema essa demanda resolve? Quem está sentindo essa dor hoje?
- Qual cliente / produto / módulo é afetado? (Ultrafarma, LeanOps, Projeto X, outro?)
- Existe algum processo ou sistema atual que faz isso de outro jeito? Como funciona hoje?
- Qual o impacto de **não** fazer essa demanda?

### Bloco 2 — Objetivo e escopo

- Qual o resultado esperado quando essa demanda estiver pronta? (uma frase)
- Quais usuários serão impactados? (perfis, papéis, personas)
- O que está **dentro** do escopo desta entrega?
- O que está **fora** do escopo? (tão importante quanto o que está dentro — evita scope creep)
- Existe alguma demanda relacionada que NÃO faz parte desta, mas pode confundir? Listar para excluir explicitamente.

### Bloco 3 — Comportamento e regras

- Quais são as regras de negócio que regem essa funcionalidade? (validações, limites, condições, exceções)
- Quais são os fluxos principais? E os fluxos alternativos / de erro?
- Há regras de permissionamento? (quem pode ver/fazer o quê)
- Há restrições legais, regulatórias ou de compliance? (LGPD, ANVISA, etc.)

### Bloco 4 — Integrações e dados

- A demanda envolve integração com sistemas externos ou outros módulos internos?
- Quais dados são consumidos? Quais são produzidos/persistidos?
- Há eventos a serem disparados ou consumidos?

### Bloco 5 — Aceitação e riscos

- Como saberemos que está pronto? (critérios de aceite, em alto nível — depois transformamos em Gherkin)
- Há riscos conhecidos? (técnicos, de negócio, de prazo, de dependência)
- Existem dependências de outros times, fornecedores, decisões pendentes?

### Quando parar de perguntar

Material suficiente significa: dá para escrever cada seção do template sem inventar. Não é necessário ter resposta para 100% das perguntas — algumas (ex.: integrações) podem legitimamente não se aplicar. O sinal de "pode gerar" é: **não há nenhuma seção do template que ficaria vazia ou genérica por falta de insumo**.

Se o usuário disser "gera assim mesmo, depois ajusto", respeitar — gerar com o que tem e marcar explicitamente as seções que ficaram com premissa, no formato `> ⚠️ **Premissa:** [descrição]`.

## Fase 2 — Geração do PRD

Use o template completo em `references/prd-template.md`. Leia o arquivo antes de gerar o PRD; ele contém a estrutura exata com todas as seções obrigatórias (visão, problema, objetivo, escopo, hierarquia Epic→Feature→PBI, fluxos, regras de negócio com IDs `RN-XX`, critérios de aceite Gherkin com IDs `[CA-XX]`, riscos) e opcionais (personas, permissionamento, integrações, diagrama de estados, arquitetura técnica).

Recursos auxiliares:

- `references/gherkin-examples.md` — exemplos calibrados de cenários Gherkin com IDs cruzados, cobrindo caminho feliz, validação, erro de regra, concorrência, integração externa, esquemas com tabela e cenários condicionais por permissão. Inclui anti-padrões a evitar.
- `${CLAUDE_PLUGIN_ROOT}/templates/pipeline-example.md` — exemplo end-to-end da mesma demanda nas cinco fases; consultar para ver como as `RN-XX` e os `CA-XX` deste PRD viram estado de tela, tarefa de execução e finding de review.

Manter a hierarquia de headings e a ordem das seções. Seções que não se aplicam podem ser omitidas, **menos** as marcadas como obrigatórias.

## Ao entregar o PRD

Se o PRD descreve interface de usuário (tem personas, fluxos de interação, cenários com ator em tela), **sugerir** — sem executar — a fase de especificação de interface:

> Este PRD tem interface. Antes do plano de execução, a skill `prototype-leanwork` pode indexar o protótipo (se você já tiver) ou gerar um, mapeando cada tela contra as regras e cenários daqui. Isso faz o plano dimensionar melhor as tarefas de UI e permite ao review verificar se todos os estados de tela foram implementados. Rode com `/leanwork-prototype` se fizer sentido.

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

## O que NÃO incluir

- Estimativas (story points, horas, t-shirt sizing P/M/G).
- Complexidade técnica subjetiva.
- Detalhes de implementação que travem o dev (escolha de biblioteca específica, nome de classe, padrão de código). O PRD é "o quê" e "por quê" — o "como" fica com quem implementa.
- Cronograma ou prazo. Isso é planejamento, não requisito.

## Padrões de comportamento

**Quando o usuário cola uma conversa/transcrição como entrada:** extrair o que dá da conversa, identificar lacunas e fazer apenas as perguntas necessárias para completar. Não repetir perguntas cuja resposta já está na conversa.

**Quando o usuário pede um PRD curto / leve:** ainda assim manter as seções obrigatórias, mas reduzir os opcionais. Nunca pular regras de negócio ou critérios de aceite — esses são o coração do PRD.

**Quando o usuário pede para revisar/melhorar um PRD existente:** apontar o que está faltando comparado ao template antes de reescrever. Pedir confirmação se for fazer mudanças estruturais grandes.

**Quando a demanda é grande demais para um único PRD:** sugerir quebra em múltiplos PRDs (um por Feature ou por Epic), e explicar a razão da quebra.
