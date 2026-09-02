---
description: Especifica a interface a partir de protótipo existente ou gera um novo. Produz SPEC-UI com telas (UI-XX) mapeadas contra o PRD.
argument-hint: [caminho do PRD e/ou do protótipo — opcional]
allowed-tools: Read, Glob, Grep, Edit(docs/prototype/**)
---

# Especificação de Interface

Transformar protótipo em especificação rastreável: inventário de telas com `UI-XX`, estados por tela e mapeamento cruzado com as regras (`RN-XX`) e cenários (`CA-XX`) do PRD.

Input: $ARGUMENTS

## O que fazer

### Passo 1 — Verificar se a fase se aplica

Antes de tudo, confirmar que há interface a especificar. Se a arquitetura não tem container de frontend, ou se o PRD não tem personas nem fluxos de interação, informar e encerrar:

> Este PRD não descreve interface — os cenários são de integração e processamento. A fase de protótipo não se aplica. Pode seguir direto para `planner-leanwork`.

Não insistir. Projeto de API, worker, job ou biblioteca pula esta fase inteiramente.

### Passo 2 — Localizar o PRD

Se o usuário não passou o caminho, procurar em `docs/prds/`. Havendo mais de um, perguntar qual. A SPEC-UI é **por PRD**, não por projeto — um projeto pode ter features com interface e features sem.

### Passo 3 — Determinar o modo

Perguntar uma vez:

> **A.** Já tenho protótipo — indexar e mapear contra o PRD *(ingestão)*
> **B.** Não tenho protótipo — quero gerar um *(geração)*
> **C.** Tenho protótipo parcial — indexar o que existe e gerar o que falta *(híbrido)*

### Passo 4 — Invocar a skill `prototype-leanwork`

A skill conduz a partir daqui:

- **Ingestão:** detecta o formato (HTML no repositório, imagens, Figma via MCP, Lovable/v0 exportado), extrai o máximo, e **declara explicitamente o que não conseguiu extrair** antes de perguntar
- **Geração:** deriva telas e estados do PRD, respeita a stack da arquitetura, herda tokens já existentes no repositório, e delega o craft visual para skill de frontend disponível no ambiente
- **Ambos:** cruzam com o PRD nas duas direções para revelar lacunas

### Passo 5 — Salvar

`docs/prototype/SPEC-UI-XXX-nome-kebab.md`, com o mesmo número do PRD correspondente.

## Regras que valem sempre

**Nunca inventar tela ou estado.** O que não foi observado no protótipo e não deriva do PRD vira lacuna declarada, não suposição preenchida.

**Nunca fechar a matriz com invenção.** Se um `CA-XX` não tem tela correspondente, registrar e pedir decisão — não gerar a tela silenciosamente para o relatório ficar verde.

**Sempre declarar a origem.** Cada tela e estado marca se veio do protótipo, foi derivado do PRD, ou foi gerado. Estado derivado não passou por validação de design — quem implementa precisa saber.

**O craft visual é delegado.** A skill decide quais telas e quais estados; tipografia, paleta e composição ficam com skills de frontend do ambiente. Sem skill de frontend disponível, gerar wireframe funcional e declarar a fidelidade honestamente.

## Ao final

Reportar:

- Telas especificadas (`UI-01`..`UI-NN`) e origem de cada uma
- Cobertura: quantos `RN-XX` e `CA-XX` do PRD têm manifestação em tela
- Lacunas que precisam de decisão antes do plano de execução
- Componentes reutilizáveis identificados
- Sugestão de seguir para `planner-leanwork`, agora com o campo `Telas:` disponível nas tarefas de interface
