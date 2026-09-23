---
description: Revisa implementação contra plano + PRD + arquitetura. Gera relatório REVIEW-{T-XX} com findings R-XX categorizados.
argument-hint: [T-XX e/ou path do diff/PR, opcional]
allowed-tools: Read, Glob, Grep, Edit(docs/reviews/**), Bash(python:*), Agent
---

# Review de Implementação SDD

Você acaba de invocar o reviewer do pipeline SDD Leanwork. O objetivo é validar que a implementação entrega o que `T-XX` prometeu, cruzando código com plano, PRD e arquitetura.

Input do usuário: $ARGUMENTS

## O que fazer

### Passo 1 — Identificar a tarefa e o diff

Se o usuário forneceu `T-XX`, branch ou PR, use. Caso contrário, descobrir em ordem:

1. **Branch atual** (`git branch --show-current`) — procurar padrão `T-\d+`
2. **Último commit** (`git log -1 --pretty=%B`) — procurar padrão `T-\d+`
3. **Pergunta direta**: "Qual tarefa do plano essa implementação entrega? (ex.: T-04). E como acesso o código? (paste do diff, branch para comparar, ou caminho dos arquivos)"

Identificada a tarefa, **procurar reviews anteriores dela**: `docs/reviews/REVIEW-{T-XX}-*.md`. Se existir algum, esta review é o round N+1 — ver "Review de segundo round" nos casos especiais e conduzir por lá. Essa verificação é parte do fluxo normal, não exceção: revisar de novo sem comparar com o round anterior perde exatamente a informação que justifica o re-review.

### Passo 2 — Carregar contexto do projeto

Procure nos locais convencionais:

- Plano: `docs/plans/PLAN-*.md` que contém a tarefa T-XX
- PRD: referenciado no cabeçalho do plano (campo `**PRD de referência:**`)
- Arquitetura: `docs/architecture/proposta-arquitetural.md`
- CLAUDE.md: raiz do repositório

Se algum não existir, **registre como lacuna no relatório** e continue com review degradado. Não invente.

### Passo 3 — Descobrir a stack

Use a cascata em `references/stack-detection.md` da skill `reviewer-leanwork`:

1. Proposta arquitetural (seção 6.2 Containers + Restrições)
2. CLAUDE.md do projeto
3. Inspeção do repositório (`*.csproj`, `package.json`, etc.)
4. Pergunta ao usuário

Documente a stack descoberta e a fonte no preâmbulo do relatório.

### Passo 4 — Despachar o verificador num contexto limpo

A review roda num **sub-agente fresco**, não neste contexto. A razão é direta: se `/leanwork-execute` acabou de implementar a tarefa nesta mesma conversa, quem revisa tem o raciocínio da implementação inteiro em memória e tende a confirmar a própria intenção em vez de ler o que o código faz. Autor e verificador precisam ser contextos diferentes.

Despachar um sub-agente **read-only sobre a árvore**, instruído a aplicar a skill `reviewer-leanwork` e a devolver os findings — não a escrever arquivo nenhum.

**Payload do verificador.** O sub-agente não herda esta conversa, então o payload precisa ser autossuficiente: nada nele pode dizer "a tarefa que acabamos de discutir". Enumerar, item a item:

1. A tarefa `T-XX` **copiada na íntegra** do plano — campos, critérios de aceite e testes a escrever, não o resumo dela
2. O **texto integral** de cada `RN-XX`, `CA-XX`, `ADR-XX` e `UI-XX` que a tarefa declara, copiado do artefato de origem. Referência por código não serve: o sub-agente não tem o PRD em contexto
3. O diff ou os arquivos sob review
4. A stack detectada **e a fonte dela** (Passo 3)
5. Os padrões lidos do `CLAUDE.md` da raiz e do módulo afetado
6. Quando for round N+1, o relatório do round anterior

**O que NÃO entra no payload, e por quê:**

- **O raciocínio da implementação** — como a solução foi pensada, que alternativas foram descartadas
- **As justificativas de quem executou** — "fiz assim porque o handler já fazia X"
- **Qualquer narrativa sobre por que uma escolha foi feita**

Esses três itens transformam a review em avaliação da explicação, não do código. Um verificador que recebe a justificativa julga se ela é convincente; um verificador que recebe só o spec e o código julga se o código cumpre o spec — que é a pergunta do review. Incluir o raciocínio reintroduz exatamente o viés que o sub-agente existe para eliminar, e de quebra reintroduz o vazamento de contexto: payload largo demais é o mesmo contexto com outro nome.

O sub-agente devolve os findings `R-XX` com severidade. **Quem escreve o relatório, salva o arquivo e edita o plano é o orquestrador** — Passos 5 e 6 seguem aqui, não lá.

**Fallback — modo degradado.** Se não houver capacidade de sub-agente disponível no ambiente, rodar a review inline **e avisar no chat que autor e verificador são o mesmo contexto nesta execução**. O aviso não é opcional: é a única coisa que impede uma review degradada de passar por verificação independente.

A skill `reviewer-leanwork` continua sendo a fonte do método — os 5 eixos (aderência ao plano, rastreabilidade, aderência ao spec, cobertura de teste, qualidade do código), mais o 6º de conformidade de interface quando o projeto tem SPEC-UI — e o relatório segue o template dela.

### Passo 5 — Salvar o relatório

Sugira salvar em `docs/reviews/REVIEW-{T-XX}-{data-iso}.md`. Se o projeto usa outra convenção (ex.: comentário direto no PR sem versionar), perguntar ao usuário.

**Gate — validar o relatório antes de salvar.** Escrever o arquivo e, antes de apresentá-lo, rodar:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_review.py" docs/reviews/REVIEW-T-XX-AAAA-MM-DD.md
```

**Exit diferente de zero é PARE — relatório reprovado não é entregue.** Os `ERROR` cobram o que o review promete e é fácil de não cumprir: finding sem `arquivo:linha`, item de cobertura marcado como coberto sem citar onde, `RN-XX`/`CA-XX` coberto sem a asserção reproduzida, recomendação fora do vocabulário (`Aprovado` / `Aprovado com ressalvas` / `Bloqueado`), e a incoerência mais cara — `Bloqueante` no corpo com recomendação diferente de `Bloqueado`. Corrigir o relatório e rodar de novo até sair 0.

Linha `WARN` não reprova: relatório sem nenhum finding e relatório de round sem a seção do round anterior são sinais para conferir, não para bloquear.

**Fallback — modo degradado.** Sem ferramenta de execução de código disponível, conferir à mão as regras acima e **dizer no chat que o relatório não passou pelo gate automático**. Degradação silenciosa é pior que gate nenhum, porque parece gate.

Se o `Bash` pedir confirmação apesar de `Bash(python:*)` no `allowed-tools` deste comando, a causa é regra mais larga no `ask`/`deny` das settings do usuário — a precedência ignora especificidade (ver `permission-catalog.md`, seção "Sombra de prefixo entre baldes"). Confirmar ou ajustar as settings; nunca pular a validação.

Após gerar o relatório, mostrar ao usuário:

- Recomendação final (`✅ Aprovado / ⚠️ Aprovado com ressalvas / ⛔ Bloqueado`)
- Contagem por severidade
- Link/caminho do arquivo gerado
- Os 1-3 findings mais críticos em destaque (para o usuário decidir se vale ler o relatório completo)

### Passo 6 — Devolver o resultado ao plano

O review só existe para o resto do pipeline se o plano souber dele. Se houver **pelo menos um finding `Bloqueante`**:

1. Mudar o campo `**Status:**` da `T-XX` no plano para `Bloqueado`
2. Registrar na tabela de Histórico de execução (seção 11) a referência ao relatório e aos findings que bloquearam — ex.: `Bloqueado por R-01, R-03 (REVIEW-T-04-2026-06-15)`

Confirmar com o usuário antes de editar o plano, e avisar se a tarefa estava marcada como `Concluído`: essa é a inconsistência entre estado declarado e estado validado que o `/leanwork-trace` reporta como grave.

Sem findings bloqueantes, **não** mexer no plano — `Aprovado com ressalvas` não muda o estado da tarefa, e findings Importantes viram tarefa nova via `planner-leanwork` quando justificarem.

O plano é a fonte de verdade do estado: um review bloqueante que não aparece nele é invisível para `/leanwork-next`, e a tarefa segue sendo sugerida como pronta.

## Casos especiais

### Review de PR com múltiplas tarefas

Se o PR entrega mais de uma tarefa (ex.: T-04, T-05, T-06 num único commit), gerar **um relatório por tarefa** e mostrar resumo agregado. Não misturar tudo num relatório só.

### Review de segundo round (re-review)

Se já existe `REVIEW-{T-XX}-*.md` para a mesma tarefa:

1. Determinar o round: contar os relatórios existentes da tarefa. O novo é o round N+1 (sem sufixo = round 1, `-round2`, `-round3`, ...)
2. Ler o **relatório mais recente** e preencher a seção "Round anterior" do template, item a item: cada `R-XX` do round anterior marcado como resolvido, persistente ou não verificável
3. Salvar como `REVIEW-{T-XX}-{data-iso}-round{N+1}.md`. Não editar o relatório anterior — o histórico de qualidade da tarefa é a sequência deles
4. Numerar os findings novos a partir de `R-01` **deste** relatório. A numeração de `R-XX` é local ao relatório: ao citar um finding fora dele, qualificar com o nome do arquivo (`R-01 (REVIEW-T-04-2026-06-15)`)

### Projeto sem artefatos SDD

Se não há plano nem PRD, oferecer code review genérico mas **avisar que não há rastreabilidade** e sugerir rodar `/leanwork-start` para projetos futuros.

### Stack não detectada

Se nenhuma das 3 primeiras tentativas de detecção funcionou e o usuário não responde a pergunta de stack, parar e pedir esclarecimento — não fazer review chutando convenções.

## Regra de ouro

Não substitua a leitura humana do PR — complemente. O review estruturado serve para **não esquecer de checar coisas óbvias** e para **manter rastreabilidade**. Decisões finais ficam com pessoas.
