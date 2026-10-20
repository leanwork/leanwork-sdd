---
description: Ponto de entrada do pipeline SDD Leanwork. Sem artefatos, conduz a entrada (fluxo completo, trilha rápida ou ponto de partida); com artefatos, lê o estado e sugere uma próxima ação.
argument-hint: [descrição curta da demanda, opcional]
allowed-tools: Read, Glob, Grep, Bash(python:*), Bash(git branch:*), Edit(docs/architecture/**), Edit(docs/prds/**), Edit(docs/prototype/**), Edit(docs/plans/**)
---

# Pipeline SDD Leanwork

O pipeline tem cinco fases — arquitetura (`architect-leanwork`), PRD (`prd-leanwork`), protótipo *(opcional, só com interface — `prototype-leanwork`)*, plano (`planner-leanwork`) e, a cada tarefa entregue, review (`/leanwork-review`). Mudança pequena e reversível tem a **trilha rápida**: um plano de uma tarefa, sem PRD, com os cenários na própria tarefa e o mesmo review.

Demanda informada: $ARGUMENTS

## Passo 1 — Ler o estado

Rodar na raiz do projeto:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" --json
```

A saída lista os artefatos presentes e, por plano, as tarefas por status, `Em andamento`, `Bloqueado` com o motivo, `Concluído` sem review, review `Bloqueado` sem round seguinte, status fora do vocabulário e a próxima tarefa elegível. É relatório, não gate: exit 0 com pendências é o normal. Interpretar a saída — não reler os artefatos para refazer a contagem.

O script lê a branch atual. Tarefa em andamento ou com review bloqueada vive na sua branch `task/PLAN-XXX-T-XX` (`templates/id-conventions.md`, seção "Branch de tarefa") e não aparece na base até ser integrada. Por isso, na base, listar também as branches de tarefa abertas: `git branch --list "task/*" --no-merged`. Cada uma é trabalho em curso, e entra na prioridade 1 ou 3 abaixo conforme o estado dela.

**Fallback — modo degradado.** Sem ferramenta de execução, ler `docs/plans/`, `docs/reviews/` e os demais artefatos à mão, aplicando as mesmas categorias, e **dizer no chat que o estado foi reconstruído sem o script**.

## Passo 2 — Entrada ou continuidade

**Sem artefatos do pipeline, ou com uma demanda nova em `$ARGUMENTS`:** conduzir a entrada. Perguntar **uma única vez**:

> Essa demanda é:
>
> **A.** Projeto/sistema novo — começar pela arquitetura (architect → PRD → planner)
> **B.** Feature nova num sistema cuja arquitetura já está definida — começar pelo PRD (PRD → planner)
> **C.** Feature já documentada em PRD, falta o plano — ir direto ao planner
> **D.** Mudança pequena e reversível (poucos arquivos, sem migration, contrato público, schema ou permissão) — trilha rápida, sem PRD
> **E.** Não sei ainda, me ajuda a decidir

- **A**: ler `architect-leanwork` e seguir o fluxo dela; ao concluir, perguntar se encadeia para o PRD
- **B**: perguntar se há proposta arquitetural para ler; em seguida, `prd-leanwork`
- **C**: perguntar o caminho do PRD, lê-lo e invocar `planner-leanwork`
- **D**: ler `planner-leanwork`, seção "Trilha rápida", confirmar o critério de entrada e gerar o plano a partir de `references/plan-template-quick.md`. Fora do critério, dizer por quê e propor B ou C
- **E**: 2-3 perguntas curtas (existe código? ADR? PRD? a mudança é pequena e reversível?) e propor o ponto de entrada

Estrutura de pastas para projeto novo: `templates/folder-conventions.md`. Sugerir, não impor, se o projeto já tem outra.

**Com artefatos:** sugerir **uma** próxima ação, na ordem de prioridade abaixo. Não listar opções.

1. **Resolver bloqueios** — review `Bloqueado` sem round seguinte (citar `R-XX` com o nome do relatório: a numeração recomeça a cada arquivo); tarefa `Bloqueado`, a partir do motivo em `Bloqueio:`. A correção é feita na branch da tarefa e fecha com `/leanwork-review T-XX`
2. **Validar entregas** — tarefa `Concluído` sem review: sugerir `/leanwork-review T-XX`
3. **Avançar execução** — tarefa `Em andamento` primeiro (é trabalho interrompido, e `/leanwork-execute T-XX` retoma a branch dela); depois a próxima elegível: `/leanwork-execute T-XX`, que implementa, revisa e integra
4. **Avançar o pipeline** — PRD com interface sem SPEC-UI e sem plano: oferecer `prototype-leanwork` ou ir direto ao `planner-leanwork`, sem bloquear; PRD sem plano: `planner-leanwork`; arquitetura sem PRD: `prd-leanwork`

Antes da sugestão, apontar o que o script marcou como inconsistência: tarefa `Concluído` com review `Bloqueado` em aberto (grave), `Bloqueado` sem motivo, status fora do vocabulário. Referência quebrada entre artefatos é do `validate_ids.py` e da matriz do `/leanwork-trace`.

**Sugestão paralela — contexto do agente**, em uma linha junto da principal, nunca no lugar dela, e sem repetir se o usuário ignorou: sem `CLAUDE.md` na raiz, `CLAUDE.md` com `<!-- TODO -->`, módulo novo sem `CLAUDE.md`, padrão emergente apontado em review, código sem `.claude/settings.json` → `/leanwork-sdd:context-leanwork` com o escopo (`raiz`, `modulo <nome>`, `permissoes`).

## Regras

- Na continuidade, este comando **sugere**: nenhuma skill é invocada sem confirmação
- Na entrada, cada fase produz um artefato revisável antes da próxima: ao concluir uma fase, parar, mostrar o resultado e perguntar se segue
- Não cobrar SPEC-UI de PRD sem interface, nem pular review de tarefa concluída
- Não gerar nem editar `CLAUDE.md` por conta própria
