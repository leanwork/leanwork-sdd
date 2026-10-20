# Template — Relatório de Review

Template completo a ser preenchido pelo `reviewer-leanwork`. Manter ordem das seções. Salvar como `docs/reviews/REVIEW-{T-XX}-{data-iso}.md`.

As cercas de quatro crases que delimitam o bloco abaixo são o envelope deste arquivo — não fazem parte do documento gerado. As cercas de três crases dentro dele fazem.

---

````markdown
# Review: T-XX — [Título da tarefa, idêntico ao do plano]

> **Plano de referência:** [path do plano, ex.: `docs/plans/PLAN-001-flash-sales.md`]
> **PRD de referência:** [path do PRD, ex.: `docs/prds/PRD-001-flash-sales.md`]
> **Arquitetura de referência:** [path, se existente]
> **Reviewer:** Claude (skill `reviewer-leanwork` v1.0)
> **Data:** [AAAA-MM-DD]
> **Round:** [1 / 2 / 3]
> **Recomendação final:** [✅ Aprovado / ⚠️ Aprovado com ressalvas / ⛔ Bloqueado]

---

## Sumário executivo

[1 parágrafo: o que foi entregue, o que está bem, o que precisa ser endereçado antes do merge.]

**Findings por severidade:**

| Severidade | Quantidade |
|------------|------------|
| Bloqueante | X |
| Importante | Y |
| Sugestão   | Z |
| **Total**  | **N** |

**Cobertura da tarefa:**

| Item | Esperado | Entregue | Status |
|------|----------|----------|--------|
| Regras implementadas (RN) | RN-XX, RN-YY | RN-XX, RN-YY | ✅ |
| Cenários validados (CA) | CA-XX, CA-YY, CA-ZZ | CA-XX, CA-YY | ⚠️ CA-ZZ sem teste |
| Decisões base (ADR) | ADR-XX | ADR-XX respeitada | ✅ |
| Critérios de aceite da tarefa | 3 | 2 atendidos, 1 parcial | ⚠️ |
| Telas e estados (UI) | UI-02 (default, limite, esgotado) | default, limite | ⚠️ falta `.esgotado` |
| Testes prometidos | 4 | 3 | ⚠️ falta CA_ZZ_* |

---

## Contexto da implementação

### Stack detectada

- [Backend: ...]
- [Banco: ...]
- [Frontend: ...]
- **Fonte:** [proposta arquitetural / CLAUDE.md / inspeção de repositório / informação do usuário]

### Padrões específicos aplicados (lidos do projeto)

- [padrão 1, ex.: "MediatR para comandos" (CLAUDE.md)]
- [padrão 2, ex.: "BusinessException para erros de negócio" (CLAUDE.md)]
- [padrão 3, ex.: "Naming `XxxCommand`/`XxxHandler`" (CLAUDE.md)]

*Se o projeto não tem padrões declarados em CLAUDE.md, indicar:*

> ⚠️ Padrões específicos da stack não estão documentados em `CLAUDE.md`. Foi aplicado apenas o piso de segurança (PII em log, segredo hardcoded). Recomenda-se documentar convenções do time para futuros reviews.

### Escopo do diff

- **Arquivos modificados:** N
- **Linhas adicionadas/removidas:** +AAA / -RRR
- **Commits:** N

---

## Findings detalhados

Os itens abaixo são numerados sequencialmente como `R-XX`. Cada um traz: eixo, severidade, evidência (arquivo:linha), sugestão.

### 🔴 Bloqueantes

Precisam ser resolvidos antes do merge.

#### R-01 — [Título curto descrevendo o problema]

- **Eixo:** [1. Aderência ao plano / 2. Rastreabilidade / 3. Aderência ao spec / 4. Cobertura de teste / 5. Qualidade do código / 6. Conformidade de interface]
- **Referência cruzada:** [RN-XX, CA-XX, ADR-XX, UI-XX se aplicável]
- **Evidência:** `src/Projeto/Foo/FooHandler.cs:45-52`
- **Descrição:** [O que está errado, com fragmento de código se ajudar]

  ```csharp
  // Exemplo do código problemático
  ```

- **Por quê é Bloqueante:** [Justificativa: viola RN-XX / não passa teste / introduz risco real em produção]
- **Sugestão de correção:** [Direção concreta — não é a única solução possível, mas é uma defensável]

#### R-02 — [...]

[Mesma estrutura]

### 🟡 Importantes

Devem ser endereçados nesta tarefa ou explicitamente adiados.

#### R-03 — [...]

[Mesma estrutura]

### 🟢 Sugestões

Melhorias opcionais, ficam a critério do autor.

#### R-04 — [...]

[Mesma estrutura, geralmente mais curta]

---

## Cobertura por RN (Implementa)

Verificação detalhada das regras de negócio que a tarefa prometeu concretizar.

### RN-05 — [Texto da regra, copiado do PRD]

- **Como foi implementada:** [Resumo objetivo de onde no código vive a regra]
- **Evidência:** `src/Projeto/Foo/FooHandler.cs:60-75`
- **Asserção:** `Assert.Equal(9, estoque.Quantidade)` — *(a expressão que prova a regra, reproduzida do teste)*
- **Status:** ✅ Implementada corretamente

### RN-07 — [Texto da regra]

- **Como foi implementada:** [Não foi! ou Implementação divergente]
- **Busca realizada:** `grep -r "RN-07\|LimiteCredito" tests/` — nenhum resultado
- **Status:** ❌ Ver R-01

---

## Cobertura por CA (Valida)

Verificação dos cenários Gherkin que a tarefa prometeu validar.

### CA-04 — [Nome do cenário, copiado do PRD]

- **Teste:** `tests/FooHandlerTests.cs:112`
- **Asserção:** `Assert.Equal(9, estoque.Quantidade)`
- **Cobre o cenário Gherkin completo?** Sim — Dado (estoque=10) / Quando (compra de 1) / Então (estoque=9) mapeados
- **Status:** ✅

### CA-06 — [Nome do cenário]

- **Teste:** Não encontrado
- **Busca realizada:** `grep -ri "CA-06\|cupom.*expirado\|AplicarCupom" tests/` — nenhum resultado
- **Status:** ❌ Ver R-02

---

## Sensor de discriminação

**Profundidade:** [padrão (1-3) | completo (risco: dinheiro / auth / integridade de dados)]
**Isolamento:** [git worktree | cópia em diretório temporário]
**Resultado:** [N/N mortos]

| # | Arquivo:linha | Mutação aplicada | Morto? |
|---|---|---|---|
| 1 | `src/servico.ext:42` | Condição `x > 0` invertida para `x >= 0` | ✅ Morto |
| 2 | `src/handler.ext:15` | Chamada obrigatória a `notificar()` removida | ❌ Sobreviveu → R-01 |

*Cada sobrevivente aponta o `R-XX` que gerou — mutante sobrevivente é `Bloqueante`, e o finding acusa a asserção fraca, não a mutação.*

*Quando o sensor não rodou (sem suíte executável, suíte vermelha, repositório em rebase, ambiente sem execução de código), manter a seção e escrever a razão no lugar da tabela. Ausência declarada é informação; seção omitida é silêncio que passa por aprovação.*

---

## Cobertura por UI (Telas) *(omitir quando o projeto não tem SPEC-UI)*

Verificação dos estados de tela que a tarefa prometeu implementar.

### UI-02 — [Nome da tela, copiado da SPEC-UI]

| Estado | Especificado | Implementado | Evidência |
|---|---|---|---|
| `.default` | Sim | ✅ | `src/Web/Checkout.tsx:20-60` |
| `.limiteExcedido` | Sim | ✅ | `src/Web/Checkout.tsx:62-78` |
| `.esgotado` | Sim | ❌ | Ver R-02 |

*Repetir para cada tela listada em `Telas:` da tarefa.*

---

## Verificação da Decisão Arquitetural

### ADR-002 — [Título da decisão]

- **Decisão original:** [Resumo do que o ADR determinou]
- **Implementação:** [Como o código materializou — citar arquivo:linha]
- **Conformidade:** ✅ A implementação usa `WITH (UPDLOCK, ROWLOCK)` conforme determinado

*Repetir para cada ADR listado em `Decisões base:` da tarefa.*

---

## Notas ao processo (não-findings)

Pontos que não viraram R-XX mas merecem registro para evoluir o pipeline.

- **Plano precisa de atualização:** [se aplicável — ex.: T-04 cobriu mais do que listado, sugerir extrair tarefa nova]
- **PRD ambíguo:** [se aplicável — ex.: RN-08 permitiu interpretação dupla]
- **ADR ausente:** [se aplicável — implementação tomou decisão arquitetural não documentada]
- **Padrão emergente:** [se aplicável — o time estabeleceu um padrão que ainda não está no `CLAUDE.md`. Descrever o padrão observado e sugerir `/leanwork-sdd:context-leanwork raiz` para documentá-lo]
- **Contexto do agente desatualizado:** [se aplicável — ex.: `CLAUDE.md` declara stack ou convenção que o código já não segue. Sugerir `/leanwork-sdd:context-leanwork auditar`]

---

## Round anterior (se Round 2+)

Comparação com `[REVIEW-T-XX-AAAA-MM-DD.md]` — quais itens foram resolvidos, quais persistem. A numeração recomeçou neste relatório: os `R-XX` da coluna abaixo são do round anterior e não têm relação com os de mesmo número deste round.

| Item anterior | Status | Comentário |
|---------------|--------|------------|
| R-01 (round 1) — Faltava teste CA-06 | ✅ Resolvido | Teste criado em `CA_06_*` |
| R-02 (round 1) — PII em log | ⚠️ Persiste | Ver R-02 deste round |
| R-03 (round 1) — Magic number | ✅ Resolvido | Constante extraída |

---

## Conclusão

[1-2 parágrafos de fechamento. Reconhecer o que está bem e ser claro sobre o que falta.]

**Próximos passos sugeridos:**

- [Item 1, ex.: "Endereçar R-01 e R-02 antes do merge"]
- [Item 2, ex.: "Considerar R-04 e R-05 nesta tarefa ou abrir tarefa nova de melhoria"]
- [Item 3, ex.: "Atualizar CLAUDE.md com padrão emergente identificado em Notas ao processo"]
````
