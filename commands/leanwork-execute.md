---
description: Executa uma tarefa do plano SDD carregando o contexto declarado (RN/CA/ADR/UI), implementando só o escopo da tarefa e atualizando o Status ao final.
argument-hint: [T-XX — opcional; se omitido, pega a próxima tarefa elegível]
allowed-tools: Read, Glob, Grep, Bash(python:*)
---

# Executar tarefa do plano SDD

Tarefa alvo: $ARGUMENTS

Este comando executa **uma** tarefa do plano. Ele existe para que a implementação carregue o mesmo contexto que o planejamento produziu — em vez de o agente reconstruir a intenção a partir do título da tarefa.

## O que fazer

### Passo 1 — Localizar o plano e a tarefa

1. Procurar o plano em `docs/plans/PLAN-*.md`. Se houver mais de um, perguntar qual — não escolher pelo mais recente.
2. Se `$ARGUMENTS` traz uma `T-XX`, usar essa tarefa. Se ela não estiver `Pendente`, avisar o estado atual e confirmar antes de seguir.
3. Se `$ARGUMENTS` está vazio, encontrar a primeira tarefa com `Status: Pendente` cujas dependências em `Depende de:` estejam **todas** com `Status: Concluído`. Se nenhuma for elegível, reportar o que está bloqueando e parar.

O vocabulário de status é fixo (`Pendente` / `Em andamento` / `Concluído` / `Bloqueado`) e está em `templates/id-conventions.md`. Ler o campo `**Status:**` de dentro do bloco `#### T-XX` — o `Status:` do cabeçalho do plano é status de documento, não de tarefa.

### Passo 2 — Carregar o contexto declarado pela tarefa

Abrir e ler na íntegra o que a tarefa referencia. **Não deduzir pelo título:**

- `Implementa:` → o PRD, cada `RN-XX` listado
- `Valida:` → o PRD, cada `Cenário [CA-XX]:` listado. No plano de trilha rápida (`PRD de referência: nenhum — trilha rápida`) não há PRD: os cenários estão no bloco `**Cenários:**` da própria tarefa
- `Decisões base:` → a proposta arquitetural, cada `ADR-XX`
- `Telas:` → a SPEC-UI, a tela e **cada estado** listado (campo ausente em projeto sem interface — não é lacuna)

Antes de ler, rodar o gate de rastreabilidade na raiz do projeto. Ele confere de uma vez, para todas as tarefas do plano, que cada `RN-XX`, `CA-XX`, `ADR-XX` e `UI-XX` citado existe no artefato onde aquele ID nasce:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_ids.py" docs/plans/PLAN-XXX-nome.md
```

**Exit diferente de zero é PARE.** Cada `ERROR` é um gap de rastreabilidade, não erro de execução: implementar assim mesmo produz código que ninguém consegue amarrar a um requisito. Reportar o gap e aguardar — não inventar o ID que falta, não seguir "assumindo que era o RN-03".

Linha `WARN` não interrompe. Duas formas aparecem: artefato de origem ausente, e aí a verificação daquela classe de ID foi **pulada**, não aprovada; e regra do PRD que nenhuma tarefa cita, que é gap de cobertura — análise de `/leanwork-trace`, não bloqueio aqui.

**Fallback — modo degradado.** Sem ferramenta de execução de código disponível, conferir à mão cada ID dos campos acima contra o artefato de origem e **avisar no chat que a rastreabilidade não passou pelo gate automático**. Degradação silenciosa é pior que gate nenhum, porque parece gate.

Se o `Bash` pedir confirmação apesar de `Bash(python:*)` no `allowed-tools` deste comando, a causa é regra mais larga no `ask`/`deny` das settings do usuário — a precedência ignora especificidade (ver `permission-catalog.md`, seção "Sombra de prefixo entre baldes"). Confirmar ou ajustar as settings; nunca pular a validação.

Ler também o `CLAUDE.md` da raiz e o do módulo afetado, se existirem — é onde estão as convenções que o review vai cobrar.

### Passo 3 — Verificar pontos de validação humana

Conferir se a tarefa aparece na seção "Pontos de validação humana" do plano. Se aparecer, pedir confirmação explícita **antes de escrever qualquer código** e aguardar resposta.

### Passo 4 — Marcar início

Atualizar o campo `**Status:**` da tarefa para `Em andamento` antes de começar. Isso torna a sessão recuperável: se o trabalho for interrompido, o próximo `/leanwork-pipeline` mostra onde parou em vez de sugerir a tarefa como se nada tivesse acontecido.

### Passo 5 — Implementar

Implementar o comportamento que a tarefa promete — os `CA-XX` de `Valida:` e os critérios de aceite. Onde o código mora segue as convenções do repositório e não precisa de justificativa. O que precisa é `**Portas de mão única:**`: tocar migration, contrato público, schema ou configuração de permissão que a tarefa não declara exige parar e confirmar com o usuário antes — porta de mão única não declarada é finding no review, e o reviewer vai encontrar.

Respeitar as decisões de `Decisões base:` mesmo quando houver abordagem que pareça melhor. Se a decisão parecer errada, é caso de ADR novo via `architect-leanwork`, não de divergir na implementação.

### Passo 6 — Escrever e rodar os testes

Escrever os testes de `Testes a escrever:` **antes** do código de produção da costura correspondente, quando praticável — ver o teste falhar primeiro é o que confirma que ele testa a coisa certa, não um teste que passaria mesmo vazio. Nomear cada um conforme `templates/id-conventions.md` — `CA_XX_descricao` para os que provam um cenário. É esse nome que fecha o elo `CA-XX → teste` para o `/leanwork-trace`.

Rodar o typecheck/build do projeto antes de rodar a suíte — erro de tipo não é falha de teste, é implementação incompleta, e roda mais rápido. Rodar os testes. **Não marcar nada como concluído com teste vermelho ou typecheck quebrado.**

### Passo 7 — Fechar o estado

Se os critérios de aceite estão todos atendidos e os testes passam:

1. Conferir cada item de `Critério de aceite (testável)` contra a implementação e a Definition of Done do `CLAUDE.md`, quando houver
2. Atualizar o campo `**Status:**` para `Concluído`

Não commitar por conta própria. Sugerir a mensagem de commit já com o trailer `Refs:` — a `T-XX` e os `CA-XX` de `Valida:` (convenção em `templates/id-conventions.md`, seção "Trailer de commit") — e deixar a decisão com o usuário. Conferir a mensagem sugerida antes de apresentá-la:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/check_commit.py" --message "<mensagem>" --plan docs/plans/PLAN-XXX-nome.md
```

O plano não guarda data nem hash: a trilha de quando e onde a tarefa mudou é o `git log`.

Se **não** for possível concluir, usar `Status: Bloqueado`, registrar o motivo no campo `**Bloqueio:**` da tarefa e parar. Tarefa parcialmente feita marcada como `Concluído` é a inconsistência que o `/leanwork-trace` foi feito para achar — não criar uma de propósito.

### Passo 8 — Sugerir o próximo passo

Sugerir `/leanwork-review T-XX`. **Não rodar automaticamente** — quem implementou não decide se a implementação passou.

## O que NÃO fazer

- **Executar mais de uma tarefa por invocação.** Uma tarefa, um ciclo, uma revisão. Se a próxima parecer trivial, ela ainda assim tem critério de aceite próprio e review próprio.
- **Implementar regra de negócio que não está em nenhuma `RN-XX` da tarefa.** Se a implementação exigir uma decisão que o PRD não cobre, parar e apontar a lacuna — o PRD é que precisa mudar, não o código que precisa adivinhar.
- **Marcar `Concluído` com critério de aceite parcialmente atendido.** Usar `Bloqueado` com o motivo em `**Bloqueio:**`.
- **Reescrever o plano durante a execução.** Se a tarefa está mal dimensionada, apontar e sugerir revisar o plano via `planner-leanwork`. Executar uma tarefa diferente da planejada quebra a rastreabilidade silenciosamente.
- **Pular os testes porque "a mudança é pequena".** O critério de conclusão é o que está escrito na tarefa.

## Regra de ouro

O plano é a fonte de verdade do estado, e este comando é o único que o atualiza durante a execução. Um estado que o plano não declara não existe para o pipeline: `/leanwork-pipeline` e `/leanwork-trace` leem esse arquivo e nada mais. Deixar o plano desatualizado é mais custoso que não ter plano, porque os dois comandos passam a descrever um projeto que não existe.
