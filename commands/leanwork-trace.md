---
description: Gera a matriz de rastreabilidade ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R a partir dos artefatos do pipeline SDD.
argument-hint: [arquivo do PRD, opcional — se omitido, analisa todos]
allowed-tools: Read, Glob, Grep, Bash(python:*), Edit(docs/traceability/**)
---

# Matriz de rastreabilidade SDD

Conectar arquitetura (ADRs) → regras (RNs) → cenários (CAs) → telas (UIs, quando houver) → tarefas (Ts) → reviews (Rs) → commits, e apontar onde a cadeia quebra.

Artefato alvo: $ARGUMENTS

## Passo 1 — Rodar o script

Na raiz do projeto, com `--prd docs/prds/PRD-XXX-nome.md` quando o usuário indicar um PRD (restringe ao PRD e ao plano de mesmo número):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/trace.py" --mermaid
```

A saída traz a matriz (uma linha por `CA-XX`, com RN, ADR, UI, T, último review e — com git — os commits cujo trailer `Refs:` cita a tarefa) e as **lacunas mecânicas**: RN sem cenário, CA sem tarefa, tarefa sem `Implementa` nem `Valida`, ADR citado e inexistente, ADR nunca citado, `Concluído` sem review, review `Bloqueado` sem round seguinte, status fora do vocabulário, `Bloqueado` sem motivo e, com SPEC-UI, tela e estado sem tarefa. Sem SPEC-UI, as colunas de UI somem e isso não é lacuna. Sem git, a coluna de commits some com aviso. `--json` dá a mesma coisa estruturada.

Não refazer a matriz à mão nem reler os artefatos para recontar: o script é a fonte. O trabalho deste comando é interpretar.

**Fallback — modo degradado.** Sem ferramenta de execução, montar a matriz lendo PRD, plano, SPEC-UI e reviews com as mesmas categorias, e **dizer no chat que a matriz não saiu do script**.

## Passo 2 — Interpretar as lacunas

Para cada lacuna, dizer o risco e uma ação, sem inventar o elo que falta:

- **`Concluído` com review `Bloqueado` em aberto** é a mais grave — estado declarado e estado validado divergem. Vem primeiro
- **Tarefa sem rastro** é legítima quando estrutural (fundação, migration); investigar antes de reportar como problema
- **ADR nunca citado** pode ser decisão sem impacto ou over-engineering — perguntar, não concluir

O script não julga o que pede leitura de conteúdo. Com SPEC-UI, verificar à parte:

- **CA de interface sem tela** — cenário com ator em tela que nenhuma `UI-XX` cobre
- **Tela sem respaldo no PRD** — `UI-XX` que não mapeia para `RN-XX` nem `CA-XX`: escopo extra ou lacuna do PRD
- **Lacunas abertas da SPEC-UI** — itens da seção 8 do documento sem decisão registrada

`R-XX` é sempre citado com o nome do relatório (`R-01 (REVIEW-T-04-2026-06-15)`): a numeração recomeça a cada arquivo.

## Passo 3 — Salvar (opcional)

Perguntar se o usuário quer salvar a matriz como `docs/traceability/MATRIX-{nome_do_prd}.md`, para versionar junto dos outros artefatos.

## Regra de ouro

Análise estática dos artefatos: não inventar link que não está escrito. Elo ausente é lacuna, não adivinhação.
