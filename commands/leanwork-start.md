---
description: Inicia o pipeline SDD da Leanwork (architect → PRD → planner) para uma nova demanda.
argument-hint: [descrição curta da demanda, opcional]
---

# Iniciar pipeline SDD Leanwork

Você acaba de invocar o pipeline Spec-Driven Development da Leanwork. O pipeline tem 5 fases, sendo a de protótipo opcional:

1. **Architect** — proposta arquitetural (skill `architect-leanwork`)
2. **PRD** — levantamento de requisitos (skill `prd-leanwork`)
3. **Protótipo** *(opcional — só para PRDs com interface)* — especificação de telas e estados (skill `prototype-leanwork`, via `/leanwork-prototype`)
4. **Planner** — quebra em tarefas executáveis (skill `planner-leanwork`)
5. **Review** — validação da implementação contra plano + PRD + arquitetura (skill `reviewer-leanwork`, invocada via `/leanwork-review` após cada tarefa entregue)

A demanda atual: $ARGUMENTS

## O que fazer

Antes de invocar qualquer skill, descobrir em que ponto a demanda está. Pergunte ao usuário **uma única vez**, com opções claras:

> Essa demanda é:
>
> **A.** Projeto/sistema novo — começar pela arquitetura (architect → PRD → planner)
> **B.** Feature nova num sistema existente cuja arquitetura já está definida — pular para o PRD (PRD → planner)
> **C.** Feature já documentada em PRD, falta só o plano de execução — ir direto ao planner
> **D.** Não sei ainda, me ajuda a decidir

Conforme a resposta:

- **A**: leia a skill `architect-leanwork` e siga o fluxo dela. Ao concluir a proposta arquitetural, pergunte se o usuário quer encadear para o PRD. Se sim, leia `prd-leanwork` e continue.
- **B**: pergunte rapidamente se há uma proposta arquitetural existente para você ler (caminho do arquivo). Se sim, leia. Em seguida invoque `prd-leanwork`.
- **C**: pergunte o caminho do PRD, leia-o, e invoque `planner-leanwork`.
- **D**: faça 2-3 perguntas curtas para classificar (existe código? existe ADR? existe PRD?) e proponha o ponto de entrada.

## Convenções de pasta

Recomenda-se a seguinte estrutura para os artefatos do pipeline no repositório do projeto:

```
docs/
├── architecture/
│   └── proposta-arquitetural.md     # output do architect-leanwork
├── prds/
│   ├── PRD-001-flash-sales.md       # outputs do prd-leanwork
│   └── PRD-002-checkout-pix.md
├── prototype/
│   └── SPEC-UI-001-flash-sales.md    # output do prototype-leanwork (só PRDs com UI)
├── plans/
│   ├── PLAN-001-flash-sales.md       # outputs do planner-leanwork
│   └── PLAN-002-checkout-pix.md
└── reviews/
    ├── REVIEW-T-04-2026-06-15.md      # outputs do reviewer-leanwork
    └── REVIEW-T-05-2026-06-16.md
```

Não impor essa estrutura se o usuário já tiver outra — apenas sugerir quando o projeto for novo.

## Regra de ouro

Não tente fazer as 3 fases num único disparo sem checkpoint. O pipeline SDD funciona porque cada fase produz um artefato revisável antes da próxima começar. Ao concluir cada fase, pare, mostre o resultado e pergunte se pode seguir.
