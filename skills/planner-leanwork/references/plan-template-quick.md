# Template — Plano de Trilha Rápida

Variante curta de `plan-template.md` para mudança pequena e reversível. O critério de entrada e a regra de saída estão em `SKILL.md`, seção "Trilha rápida" — ler antes de usar este template.

É um plano de **uma tarefa**, sem PRD: os cenários `CA-XX` nascem dentro da própria tarefa. Fases, mapa de dependências, rollback e pontos de validação humana não existem aqui. `**Portas de mão única:**` é sempre `nenhuma` — havendo uma, a mudança não cabe na trilha. O rigor da tarefa é o mesmo do plano completo — critério de aceite, testes a escrever e status —, e por isso `/leanwork-execute`, `/leanwork-review` e os gates funcionam sem fluxo paralelo.

As cercas de quatro crases que delimitam o bloco abaixo são o envelope deste arquivo — não fazem parte do documento gerado. As cercas de três crases dentro dele fazem.

---

````markdown
# Plano de Execução: [Título curto da mudança]

**PRD de referência:** nenhum — trilha rápida
**Cliente/Produto:** [produto ou projeto]
**Stack:** [linguagem e framework do trecho tocado]
**Autor:** [nome]
**Data:** [AAAA-MM-DD]
**Status:** Rascunho

## Motivo

[1 a 3 linhas: o que muda e por quê. Confirmar o critério de entrada — poucos arquivos tocados e nenhuma porta de mão única (migration, contrato público, schema, permissão).]

#### T-01 — [Título curto e imperativo]

- **Status:** Pendente
- **Complexidade:** Baixa
- **Depende de:** nenhuma
- **Valida:** CA-01
- **Portas de mão única:** nenhuma

**Cenários:**

```gherkin
Cenário [CA-01]: [comportamento esperado]
  Dado [contexto]
  Quando [ação]
  Então [resultado observável]
```

**Descrição:**
[O que muda, em 1 a 3 linhas.]

**Critério de aceite (testável):**
- [Cenário CA-01 passa]

**Testes a escrever:**
- *Unit:* [teste nomeado `CA_01_descricao` que prova o cenário]
````
