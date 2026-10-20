---
description: Executa uma tarefa do plano SDD numa branch própria, carregando o contexto declarado (RN/CA/ADR/UI), e encadeia a review num sub-agente; sem Bloqueante, integra a branch na base.
argument-hint: [T-XX — opcional; se omitido, pega a próxima tarefa elegível]
allowed-tools: Read, Glob, Grep, Bash(python:*), Bash(git status:*), Bash(git branch:*), Bash(git switch:*), Bash(git diff:*), Bash(git log:*), Bash(git symbolic-ref:*), Bash(git add:*), Edit(docs/reviews/**), Agent
---

# Executar tarefa do plano SDD

Tarefa alvo: $ARGUMENTS

Este comando executa **uma** tarefa do plano, de ponta a ponta: abre a branch da tarefa, implementa neste contexto, entrega a review a um sub-agente de contexto limpo e, sem `Bloqueante`, integra a branch na base. Ele existe para que a implementação carregue o mesmo contexto que o planejamento produziu — em vez de o agente reconstruir a intenção a partir do título da tarefa.

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

Antes de ler, rodar o gate de rastreabilidade — sem hook, porque não depende de edição: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_ids.py" docs/plans/PLAN-XXX-nome.md`. Se o `Bash` pedir confirmação apesar do `allowed-tools`, é regra mais larga nas settings do usuário (`permission-catalog.md`, "Sombra de prefixo entre baldes"): confirmar ou ajustar, nunca pular a validação.
Exit diferente de zero é PARE: cada `ERROR` é um ID citado que não existe na origem — reportar o gap e aguardar, sem inventar o ID. `WARN` não interrompe (origem ausente = verificação pulada, não aprovada).
Sem execução de código, conferir os IDs à mão e avisar no chat que a rastreabilidade não passou pelo gate automático (ver README, "Degradação silenciosa").

Ler também o `CLAUDE.md` da raiz e o do módulo afetado, se existirem — é onde estão as convenções que o review vai cobrar.

### Passo 3 — Verificar pontos de validação humana

Conferir se a tarefa aparece na seção "Pontos de validação humana" do plano. Se aparecer, pedir confirmação explícita **antes de escrever qualquer código** e aguardar resposta.

### Passo 4 — Abrir a branch e marcar início

A tarefa vive em `task/PLAN-XXX-T-XX`, aberta a partir da branch base — nome, base e diff em `templates/id-conventions.md`, seção "Branch de tarefa".

1. **Árvore limpa.** `git status --porcelain` sem arquivo rastreado modificado ou em stage. Se houver, parar e perguntar ao usuário se commita ou guarda as mudanças — não fazer `stash` nem descartar por conta própria: mudança alheia levada para a branch da tarefa entra no diff que o verificador lê. Arquivo não rastreado não bloqueia, mas não entra nos commits da tarefa
2. **Branch já existe** (`git branch --list task/PLAN-XXX-T-XX`): é retomada — trabalho interrompido ou review bloqueada. `git switch` para ela e seguir de onde o `Status:` e o último relatório em `docs/reviews/` indicam, sem recriar
3. **Branch nova:** `git switch -c task/PLAN-XXX-T-XX <base>`. Com a base atrás do remoto, avisar — atualizar a base é decisão do usuário

Já na branch, atualizar o campo `**Status:**` da tarefa para `Em andamento`. Isso torna a sessão recuperável: se o trabalho for interrompido, o próximo `/leanwork-pipeline` mostra onde parou em vez de sugerir a tarefa como se nada tivesse acontecido.

**Fallback — sem git.** Fora de um repositório git, seguir sem branch e avisar no chat que o diff da review não está isolado: o verificador vai ler a árvore inteira.

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
3. Commitar na branch da tarefa o código, os testes e o plano. `git add` arquivo por arquivo, só o que a tarefa tocou — nunca `git add -A` ou `git add .`, que levam para o diff qualquer não rastreado que estava na árvore. A mensagem termina com o trailer `Refs:` — a `T-XX` e os `CA-XX` de `Valida:` (convenção em `templates/id-conventions.md`, seção "Trailer de commit") — e passa pelo gate antes do commit:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/check_commit.py" --message "<mensagem>" --plan docs/plans/PLAN-XXX-nome.md
```

O comando não pergunta antes de commitar, porque o commit é local e fica numa branch que só esta tarefa usa. Mas `git commit` fica de fora do `allowed-tools` de propósito: a confirmação de permissão do Claude Code é o ponto em que o usuário vê a mensagem. O plano não guarda data nem hash: a trilha de quando e onde a tarefa mudou é o `git log`.

Se **não** for possível concluir, usar `Status: Bloqueado`, registrar o motivo no campo `**Bloqueio:**` da tarefa, commitar o estado na branch e parar — sem review. Tarefa parcialmente feita marcada como `Concluído` é a inconsistência que o `/leanwork-trace` foi feito para achar — não criar uma de propósito.

### Passo 8 — Encadear a review

Com a tarefa `Concluído` e commitada, seguir direto para a review: Passos 1 a 7 de `${CLAUDE_PLUGIN_ROOT}/commands/leanwork-review.md`, com a `T-XX` e a branch já conhecidas. Lá estão o sub-agente verificador, o payload, o relatório, o veredicto e a integração na base — este comando não repete nada disso.

Quem implementou não decide se a implementação passou: o verificador é um contexto que não viu esta conversa. Duas regras seguram essa separação daqui:

- **O payload não leva o raciocínio da implementação.** Este contexto tem tudo em memória e vai querer explicar as escolhas; a lista do que não entra está no Passo 4 da review
- **O veredicto é o do verificador.** Transcrever os `R-XX` com a severidade que ele devolveu. Rebaixar um `Bloqueante` porque "o código está certo" é o autor revisando a si mesmo pela porta dos fundos — discordância vai para o chat, ao lado do relatório, e a decisão é do usuário

Não encadear a review quando a tarefa terminou `Bloqueado` ou quando a execução parou esperando confirmação do usuário.

## O que NÃO fazer

- **Executar mais de uma tarefa por invocação.** Uma tarefa, uma branch, uma revisão. Se a próxima parecer trivial, ela ainda assim tem critério de aceite próprio e review próprio.
- **Implementar fora da branch da tarefa**, ou levar para ela mudança que a tarefa não fez. O diff da branch é o que o verificador lê.
- **Fazer push.** A integração é local; publicar é decisão do usuário.
- **Implementar regra de negócio que não está em nenhuma `RN-XX` da tarefa.** Se a implementação exigir uma decisão que o PRD não cobre, parar e apontar a lacuna — o PRD é que precisa mudar, não o código que precisa adivinhar.
- **Marcar `Concluído` com critério de aceite parcialmente atendido.** Usar `Bloqueado` com o motivo em `**Bloqueio:**`.
- **Reescrever o plano durante a execução.** Se a tarefa está mal dimensionada, apontar e sugerir revisar o plano via `planner-leanwork`. Executar uma tarefa diferente da planejada quebra a rastreabilidade silenciosamente.
- **Pular os testes porque "a mudança é pequena".** O critério de conclusão é o que está escrito na tarefa.

## Regra de ouro

O plano é a fonte de verdade do estado, e este comando é o único que o atualiza durante a execução. Um estado que o plano não declara não existe para o pipeline: `/leanwork-pipeline` e `/leanwork-trace` leem esse arquivo e nada mais. Deixar o plano desatualizado é mais custoso que não ter plano, porque os dois comandos passam a descrever um projeto que não existe.
