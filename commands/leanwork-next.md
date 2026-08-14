---
description: Inspeciona artefatos existentes (architecture/PRD/plan/review) e sugere a próxima fase do pipeline SDD.
---

# Próxima fase do pipeline SDD

Você está no meio de um pipeline SDD Leanwork. Sua tarefa é descobrir em que ponto o projeto está e sugerir o próximo passo.

## O que fazer

1. **Procure os artefatos do pipeline** no diretório atual. Locais convencionais (mas verifique também pasta raiz e `docs/` se não achar):
   - Arquitetura: `docs/architecture/*.md`, `ARQUITETURA.md`, `architecture.md`
   - PRDs: `docs/prds/*.md`, `PRD-*.md`, `prds/`
   - Planos: `docs/plans/*.md`, `PLAN-*.md`, `plans/`
   - Reviews: `docs/reviews/*.md`, `REVIEW-*.md`, `reviews/`
   - Contexto do agente: `CLAUDE.md` na raiz e nas pastas de módulo

2. **Para cada artefato encontrado, identifique o estado:**
   - **Arquitetura**: tem ADRs preenchidos? Tem diagramas C4? Marcações `[A DEFINIR]` ou `⚠️ Premissa`?
   - **PRD**: tem RN-XX preenchidos? Tem cenários CA-XX em Gherkin? Status no cabeçalho (`Rascunho / Em revisão / Aprovado`)?
   - **Plano**: quantas tarefas T-XX existem? Quantas marcadas como concluídas? Há tarefas `⛔ Blocked`?
   - **Reviews**: quantos relatórios existem? Quantos `⛔ Bloqueado`? Tarefas Done sem review correspondente?
   - **Contexto do agente**: existe `CLAUDE.md` na raiz? Tem as seções essenciais (Stack, Comandos, Convenções)? Há `<!-- TODO -->` pendentes? Módulos sem `CLAUDE.md`?

3. **Sintetize o estado** em uma tabela curta para o usuário ver:

   ```
   | Artefato | Status | Próximo passo natural |
   |----------|--------|----------------------|
   | Arquitetura (ADRs 1-5)  | Completa  | — |
   | PRD-001 Flash Sales     | Aprovado  | Gerar plano |
   | PLAN-001 Flash Sales    | 5/12 ✅   | Continuar execução (T-06) |
   | Reviews                  | 3 OK, 1 bloqueado | Resolver R-02 de T-04 |
   | CLAUDE.md (raiz)         | Comandos com TODO | Rodar `/leanwork-context raiz` |
   ```

4. **Sugira UMA próxima ação concreta**, em ordem de prioridade. Não listar opções:

   **Prioridade 1 — Resolver bloqueios:**
   - Se há review com recomendação `⛔ Bloqueado` e sem round subsequente: "Há review bloqueante em T-XX (findings R-01, R-03). Quer revisar os pontos para correção?"
   - Se há tarefa `⛔ Blocked` no plano: identificar a dependência e sugerir como destravar

   **Prioridade 2 — Validar entregas:**
   - Se há tarefas marcadas como `✅ Done` no plano mas sem review correspondente: "T-04 e T-05 foram marcadas como concluídas mas não têm review. Quer rodar `/leanwork-review T-04` antes de avançar?"

   **Prioridade 3 — Avançar execução:**
   - Se há plano com próxima tarefa pendente sem bloqueio: "PLAN-001 tem T-06 como próxima tarefa pendente sem bloqueio. Quer que eu prepare o contexto dela para execução?"

   **Prioridade 4 — Avançar pipeline:**
   - Se há PRD aprovado sem plano: "Vamos gerar o plano de execução para PRD-001. Posso invocar a skill `planner-leanwork` agora?"
   - Se há arquitetura mas nenhum PRD: "Arquitetura está pronta. Qual é a primeira feature a virar PRD? Posso invocar a skill `prd-leanwork`."
   - Se nada foi feito: "Não encontrei artefatos do pipeline. Quer rodar `/leanwork-start` para começar?"

   **Sugestão paralela — contexto do agente (nunca prioridade principal):**

   Quando aplicável, mencionar **junto** com a sugestão principal, em uma linha, sem tomar o lugar dela:
   - Projeto tem artefatos do pipeline mas nenhum `CLAUDE.md` na raiz: "(Aproveitando: não há `CLAUDE.md` na raiz — `/leanwork-context raiz` deixaria os próximos reviews mais completos.)"
   - `CLAUDE.md` existe mas tem `<!-- TODO -->` pendentes: "(A seção Comandos do `CLAUDE.md` está com TODO — agora que há scaffolding, `/leanwork-context raiz` consegue preencher.)"
   - Módulo novo detectado sem `CLAUDE.md`: "(Módulo `X` apareceu desde a última vez — `/leanwork-context modulo X` se achar que vale.)"
   - Reviews recentes citam padrão emergente: "(Os últimos reviews apontaram padrão ainda não documentado — `/leanwork-context raiz` capturaria isso.)"

   Essas sugestões são **convites de uma linha**. Nunca transformá-las na ação principal, nunca repetir se o usuário ignorou, e nunca gerar o arquivo por conta própria.

5. **Se houver inconsistência**, apontar antes de sugerir:
   - PRD cita ADR-007 que não existe na arquitetura
   - Plano cita CA-12 que não está no PRD
   - Tarefas marcadas como concluídas sem commit hash
   - **Tarefa marcada como `✅ Done` mas com review `⛔ Bloqueado` em aberto** (inconsistência grave entre estado declarado e estado validado)

## Não fazer

- Não invocar nenhuma skill sem confirmação. Este comando **sugere**, não executa.
- Não listar todos os artefatos do projeto — só os do pipeline SDD.
- Não inventar status. Se não há informação clara, dizer "estado indeterminado".
- Não pular review quando uma tarefa foi concluída — review é parte do pipeline, não opcional.
- Não gerar nem editar `CLAUDE.md` por conta própria. O arquivo é território do dev: apenas sugerir `/leanwork-context` e seguir em frente se ele ignorar.
