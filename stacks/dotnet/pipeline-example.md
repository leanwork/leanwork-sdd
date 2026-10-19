# Exemplo End-to-End — Pipeline SDD Leanwork (calibrado em .NET)

Este documento mostra os cinco artefatos do pipeline (arquitetura → PRD → SPEC-UI → plano → review) para uma demanda fictícia, com os IDs cruzados preenchidos. Serve como exemplo de calibração para as skills e como referência rápida do "como tudo se conecta".

**Este exemplo é calibrado em .NET/C#** (MediatR, EF Core, xUnit) só para ter código concreto em vez de pseudocódigo — as skills continuam stack-agnósticas, e o que se calibra aqui é o **cruzamento de IDs entre fases**, não a stack. Está em `stacks/dotnet/` (e não em `templates/`) exatamente por isso: é um exemplo aplicado a uma stack, não parte do núcleo agnóstico. Outras stacks podem ganhar seu próprio `stacks/<nome>/pipeline-example.md` seguindo a mesma estrutura de fragmentos.

As skills do pipeline apontam para este arquivo em "Recursos auxiliares". Quando ele diverge do que as skills produzem, é este arquivo que está errado — os templates em `references/` são a fonte de verdade da estrutura; aqui só se calibra o **cruzamento de IDs entre fases**.

## Demanda fictícia

> **Cliente:** Contoso
> **Demanda:** Implementar venda em "Ofertas Relâmpago" — produtos com estoque limitado a preço promocional, disponíveis por janela curta de tempo (15 minutos a 2 horas). Cliente pode comprar no máximo 1 unidade do produto em oferta. Estoque precisa ser decrementado de forma atômica para evitar overselling.

A demanda atravessa as cinco fases. Abaixo, fragmentos representativos de cada artefato — não são os documentos completos, e sim os trechos onde os IDs se cruzam.

---

## Fragmento 1 — Proposta Arquitetural (saída do `architect-leanwork`)

````markdown
# Proposta Arquitetural — Ofertas Relâmpago

## 5. Decisões arquiteturais (ADRs resumidos)

### ADR-002: Adotar lock pessimista no SQL Server para decremento de estoque em ofertas relâmpago

- **Contexto**: Cenário de Black Friday com até 500 req/s concorrentes no mesmo produto.
  Lock otimista (versionamento) resultaria em alta taxa de retentativas e UX ruim. Solução
  precisa garantir consistência forte porque overselling tem custo regulatório (ANVISA) e
  reputacional.
- **Decisão**: Usar `SELECT ... WITH (UPDLOCK, ROWLOCK)` ao ler o estoque dentro da
  transação de compra; commit libera o lock.
- **Justificativa**: Atende o atributo de qualidade "Consistência forte" priorizado para
  ofertas relâmpago. Trade-off aceito: throughput menor que solução com Redis + Lua,
  mas (a) o time já opera SQL Server, (b) volume previsto (50 produtos em oferta
  simultânea) cabe sem gargalo.
- **Alternativas consideradas**:
  - Redis com decremento atômico via Lua script — descartada porque adicionaria
    componente novo na stack para ganho marginal no volume previsto
  - Lock otimista com retry — descartada porque retentativas em alta concorrência
    degradam UX
- **Consequências**:
  - Positivas: garantia forte de não-overselling, sem novo componente de infra
  - Negativas / dívidas plantadas: throughput limitado pelo SQL Server (revisar se
    volume passar de 5x o atual)
````

---

## Fragmento 2 — PRD (saída do `prd-leanwork`)

````markdown
# PRD: Ofertas Relâmpago

## 8. Regras de negócio

- **RN-01**: Uma oferta relâmpago tem janela de validade definida por `inicio_em` e
  `fim_em` (UTC). Fora dessa janela, o produto volta ao preço regular.
- **RN-03**: Cada cliente pode comprar no máximo 1 unidade de um mesmo produto em oferta
  relâmpago. Tentativas adicionais retornam erro de negócio (não erro técnico).
- **RN-05**: O estoque da oferta é decrementado atomicamente no momento da confirmação
  da compra. Se o estoque chegar a zero antes do fim da janela, a oferta é encerrada
  automaticamente e mostrada como "esgotada". *(ADR-002)*
- **RN-07**: Compra em oferta relâmpago não pode ser cancelada pelo cliente após
  confirmada — apenas pelo SAC.

## 9. Critérios de aceite

```gherkin
Funcionalidade: Compra em Oferta Relâmpago

  Cenário [CA-01]: Cliente compra produto em oferta relâmpago com sucesso
    Dado que existe oferta ativa do produto X com 10 unidades (RN-01)
    E o cliente Y nunca comprou esse produto na oferta atual
    Quando o cliente Y confirma a compra de 1 unidade
    Então o estoque da oferta é decrementado para 9 unidades (RN-05)
    E o pedido é registrado com o preço promocional
    E o cliente recebe confirmação por e-mail

  Cenário [CA-02]: Cliente tenta comprar segunda unidade do mesmo produto em oferta
    Dado que o cliente Y já comprou 1 unidade do produto X na oferta atual (RN-03)
    Quando o cliente Y tenta comprar mais 1 unidade
    Então a compra é rejeitada com mensagem "Limite de 1 unidade por cliente nesta oferta"
    E o estoque da oferta não é alterado

  Cenário [CA-03]: Estoque da oferta esgota durante compras concorrentes
    Dado que existe oferta ativa do produto X com 1 unidade restante (RN-05)
    E dois clientes confirmam compra simultaneamente
    Quando o sistema processa as duas requisições
    Então apenas uma compra é confirmada com sucesso
    E a outra é rejeitada com mensagem "Produto esgotado nesta oferta"
    E o estoque final é 0
```
````

---

## Fragmento 3 — SPEC-UI (saída do `prototype-leanwork`)

Fase opcional: só existe porque esta demanda tem interface de cliente. Um PRD de integração
ou job não teria este fragmento, e a ausência não seria lacuna.

Repare que os dois estados de exceção não vieram do protótipo — foram **derivados dos
cenários Gherkin do Fragmento 2**. É o mecanismo central da fase: todo `Então` que descreve
rejeição, bloqueio ou mensagem de erro corresponde a um estado de tela.

````markdown
# SPEC-UI-001: Ofertas Relâmpago

> **PRD de referência:** `docs/prds/PRD-001-ofertas-relampago.md`
> **Modo:** Ingestão (protótipo HTML do Lovable)
> **Fidelidade:** Alta fidelidade
> **Status:** Aprovado

## 3. Inventário de telas

| ID | Tela | Rota | Persona | Implementa (RN) | Valida (CA) |
|---|---|---|---|---|---|
| UI-01 | Listagem de ofertas | `/ofertas` | Cliente | RN-01 | CA-01 |
| UI-02 | Checkout da oferta | `/ofertas/:id/checkout` | Cliente | RN-03, RN-05 | CA-01, CA-02, CA-03 |

## 4. Telas em detalhe

### UI-02 — Checkout da oferta

**Propósito:** confirmar a compra de 1 unidade do produto em oferta.

**Regras que se manifestam:**

| Regra | Como aparece na tela |
|---|---|
| RN-03 | Botão "Confirmar compra" desabilitado com aviso quando o cliente já comprou |
| RN-05 | Contador de unidades restantes; oferta esgotada bloqueia a confirmação |

**Estados:**

| Estado | ID | Quando ocorre | O que o usuário vê | Origem |
|---|---|---|---|---|
| Padrão | `UI-02.default` | Oferta ativa, cliente elegível | Resumo do item, preço promocional, botão ativo | Protótipo |
| Limite excedido | `UI-02.limiteExcedido` | Cliente já comprou (RN-03) | Alerta "Limite de 1 unidade por cliente nesta oferta" + link para a listagem | Derivado de CA-02 |
| Esgotado | `UI-02.esgotado` | Estoque zerou durante a sessão (RN-05) | Aviso "Produto esgotado nesta oferta" + botão desabilitado | Derivado de CA-03 |
| Carregando | `UI-02.carregando` | Confirmação em processamento | Botão em spinner, formulário travado | Derivado do PRD |

## 7. Cobertura do PRD

### Regras de negócio

| RN | Manifesta em | Status |
|---|---|---|
| RN-01 | UI-01 | ✅ Coberta |
| RN-03 | UI-02 (`.limiteExcedido`) | ✅ Coberta |
| RN-05 | UI-02 (`.esgotado`) | ✅ Coberta |
| RN-07 | — | ⚠️ Regra de backend (cancelamento pelo SAC) — sem interface neste PRD |

### Cenários Gherkin

| CA | Acontece em | Status |
|---|---|---|
| CA-01 | UI-01 → UI-02 (`.default`) | ✅ Coberto |
| CA-02 | UI-02 (`.limiteExcedido`) | ✅ Coberto |
| CA-03 | UI-02 (`.esgotado`) | ✅ Coberto |

## 8. Lacunas e pendências

| # | Lacuna | Impacto | Decisão necessária |
|---|---|---|---|
| 1 | `.limiteExcedido` e `.esgotado` não estavam no protótipo original | Derivados do PRD, não validados visualmente | Validar com design antes de implementar |
````

---

## Fragmento 4 — Plano de Execução (saída do `planner-leanwork`)

Fatia vertical por `CA-XX`: cada tarefa de comportamento fecha um cenário ponta a ponta, da tela ao banco. A única fatia horizontal é a fundação (`T-01`), porque migration é exceção prevista. O estado de cada tarefa vive só no `**Status:**`; quando e em que commit ele mudou é trilha do git.

````markdown
# Plano de Execução: Ofertas Relâmpago

**PRD de referência:** `docs/prds/PRD-001-ofertas-relampago.md`
**Cliente/Produto:** Contoso — e-commerce
**Status:** Em execução

## 1. Resumo executivo

Uma fundação horizontal (entidade e migration) e três fatias verticais, uma por cenário do PRD. A compra concorrente (`CA-03`) tem fatia própria porque é ela que prova a ADR-002.

## 2. Estratégia de entrega

**Modelo de entrega:** incremental, atrás da feature flag `ofertas-relampago`, desligada até `T-04` fechar.

## 5. Fases

### Fase 1 — Fundação

#### T-01 — Criar a entidade de oferta e a migration

- **Status:** Concluído
- **Complexidade:** Baixa
- **Depende de:** nenhuma
- **Portas de mão única:** migration — tabela `OfertaRelampago` com `EstoqueRestante`

**Descrição:**
Fatia horizontal por exceção: migration isolada, revisável e reversível por conta própria. Entidade `OfertaRelampago` com janela (`InicioEm`, `FimEm`, UTC) e estoque.

**Critério de aceite (testável):**
- A migration aplica e reverte num banco vazio
- Oferta fora da janela não aparece na consulta de ofertas ativas

**Testes a escrever:**
- *Integration:* `Migration_aplica_e_reverte`, `Oferta_fora_da_janela_nao_aparece_como_ativa`

### Fase 2 — Fatias por cenário

#### T-02 — Comprar produto em oferta com sucesso

- **Status:** Concluído
- **Complexidade:** Média
- **Depende de:** T-01
- **Implementa:** RN-01, RN-05
- **Valida:** CA-01
- **Telas:** UI-01, UI-02 (default, carregando)
- **Portas de mão única:** contrato público — rota `POST /api/ofertas/{id}/compras`

**Descrição:**
Caminho feliz ponta a ponta: listagem, checkout, handler MediatR de compra, decremento de estoque e pedido com preço promocional. A disputa por estoque fica para `T-03`.

**Critério de aceite (testável):**
- Compra de 1 unidade numa oferta com 10 deixa o estoque persistido em 9 e registra o pedido com preço promocional (CA-01)
- `UI-02.carregando` trava o formulário enquanto a confirmação processa

**Testes a escrever:**
- *Integration:* `CA_01_Compra_com_sucesso_decrementa_estoque` — `POST` contra banco real, asserção sobre o estoque persistido
- *Component:* estados `default` e `carregando` da `UI-02`

#### T-03 — Respeitar o estoque em compras concorrentes

- **Status:** Bloqueado
- **Bloqueio:** R-01 (REVIEW-T-03-2026-06-15) — o teste de CA-03 não exercita concorrência
- **Complexidade:** Alta
- **Depende de:** T-02
- **Implementa:** RN-05
- **Valida:** CA-03
- **Decisões base:** ADR-002
- **Telas:** UI-02 (esgotado)
- **Portas de mão única:** nenhuma

**Descrição:**
Transação `Serializable` com `SELECT ... WITH (UPDLOCK, ROWLOCK)` na leitura da oferta, conforme a ADR-002. Estoque zerado encerra a oferta e leva o checkout para `UI-02.esgotado`.

**Critério de aceite (testável):**
- Duas compras simultâneas com 1 unidade restante: exatamente 1 sucesso, 1 rejeição "Produto esgotado nesta oferta" e estoque final 0 (CA-03)
- Sem o `UPDLOCK`, o teste de concorrência falha

**Testes a escrever:**
- *Stress (xUnit + threads, banco real):* `CA_03_Compra_concorrente_respeita_estoque_atomico` — 100 compras concorrentes com estoque 10 → 10 sucessos, 90 rejeições, estoque final 0

**Riscos / pontos de atenção:**
- Lock pessimista tem custo de bloqueio — monitorar `sys.dm_tran_locks` na primeira janela de Black Friday

#### T-04 — Limitar a uma unidade por cliente

- **Status:** Pendente
- **Complexidade:** Baixa
- **Depende de:** T-02
- **Implementa:** RN-03
- **Valida:** CA-02
- **Telas:** UI-02 (limiteExcedido)
- **Portas de mão única:** nenhuma

**Descrição:**
Rejeição antes de tocar o estoque, com erro de negócio. O checkout mostra `UI-02.limiteExcedido` sem perder o resumo do item.

**Critério de aceite (testável):**
- Segunda compra do mesmo cliente na mesma oferta é rejeitada com "Limite de 1 unidade por cliente nesta oferta" e o estoque não muda (CA-02)

**Testes a escrever:**
- *Integration:* `CA_02_Segunda_compra_do_mesmo_cliente_e_rejeitada`
- *Component:* o estado `limiteExcedido` da `UI-02` mantém o resumo do item visível

## 9. Pontos de validação humana

- [ ] Antes de **T-03** — validar com design os estados `.limiteExcedido` e `.esgotado`, derivados do PRD e ausentes do protótipo (lacuna 1 da SPEC-UI)
````

O elo código → requisito sai do commit. A mensagem que o `/leanwork-execute` sugeriu ao fechar a `T-03`, conferida pelo `check_commit.py`:

```
Lock pessimista no decremento de estoque da oferta

Refs: T-03, CA-03, ADR-002, UI-02.esgotado
```

---

## Fragmento 5 — Relatório de Review (saída do `reviewer-leanwork`)

O review fecha o ciclo: lê o código contra a tarefa, a tarefa contra o PRD, e devolve `R-XX` rastreáveis. Aqui ele pega o defeito que a matriz **não pega** — o `trace.py` confirma que a `T-03` valida `CA-03`, não que o teste prove `CA-03`.

````markdown
# Review: T-03 — Respeitar o estoque em compras concorrentes

> **Plano de referência:** `docs/plans/PLAN-001-ofertas-relampago.md`
> **PRD de referência:** `docs/prds/PRD-001-ofertas-relampago.md`
> **Reviewer:** Claude (skill `reviewer-leanwork`, sub-agente de contexto limpo)
> **Data:** 2026-06-15
> **Round:** 1
> **Recomendação final:** ⛔ Bloqueado

## Sumário executivo

O handler está bem estruturado e a ADR-002 foi respeitada literalmente. O bloqueio é de cobertura: o teste que carrega o nome de `CA-03` não reproduz concorrência, então o cenário que justifica a decisão arquitetural inteira segue sem prova.

**Cobertura da tarefa:**

| Item | Esperado | Entregue | Status |
|------|----------|----------|--------|
| Regras implementadas (RN) | RN-05 | RN-05 — `ComprarOfertaHandler.cs:41` | ✅ |
| Cenários validados (CA) | CA-03 | teste existe pelo nome, não pelo comportamento | ⛔ Ver R-01 |
| Decisões base (ADR) | ADR-002 | `UPDLOCK, ROWLOCK` em `FlashSaleRepository.cs:27` | ✅ |
| Telas e estados (UI) | UI-02 (esgotado) | `checkout.tsx:63` | ✅ |
| Testes prometidos | 1 (stress) | 1, sem concorrência | ⛔ Ver R-01 |

## Findings detalhados

### 🔴 Bloqueantes

#### R-01 — O teste de CA-03 não exercita concorrência

- **Eixo:** 4. Cobertura de teste
- **Referência cruzada:** CA-03, RN-05, ADR-002
- **Evidência:** `tests/Contoso.Application.Tests/FlashSale/ComprarOfertaHandlerTests.cs:88`
- **Descrição:** `CA_03_Compra_concorrente_respeita_estoque_atomico` dispara as compras em sequência, contra repositório em memória. Não há duas transações vivas ao mesmo tempo, então o `UPDLOCK` nunca é disputado. O sensor de discriminação confirmou: com o `UPDLOCK` removido, a suíte continua verde — mutante sobrevivente.
- **Por quê é Bloqueante:** CA-03 é o único cenário que prova a ADR-002, e overselling tem custo regulatório declarado no contexto da decisão. Um teste que passa com o lock removido dá falsa segurança exatamente no ponto de maior risco.
- **Sugestão de correção:** promover para teste de integração com banco real e N threads, como prevê "Testes a escrever" da T-03 (*Stress*), e verificar que a versão sem `UPDLOCK` falha.

## Sensor de discriminação

**Profundidade:** completo (risco: integridade de dados — overselling)
**Isolamento:** git worktree
**Resultado:** 1/2 mortos

| # | Arquivo:linha | Mutação aplicada | Morto? |
|---|---|---|---|
| 1 | `src/Contoso.Infrastructure/Persistence/Repositories/FlashSaleRepository.cs:27` | `WITH (UPDLOCK, ROWLOCK)` removido da leitura da oferta | ❌ Sobreviveu → R-01 |
| 2 | `src/Contoso.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaHandler.cs:41` | Decremento `EstoqueRestante -= 1` removido | ✅ Morto |

## Cobertura por CA (Valida)

### CA-03 — Estoque da oferta esgota durante compras concorrentes

- **Teste correspondente:** `ComprarOfertaHandlerTests.cs:88` — existe pelo nome, não pelo comportamento
- **Status:** ⛔ Não coberto — ver R-01

## Notas ao processo (não-findings)

- **Plano precisa de atualização:** T-03 volta a `Status: Bloqueado`, com `Bloqueio: R-01 (REVIEW-T-03-2026-06-15)`. O round 2 vira `REVIEW-T-03-2026-06-17-round2.md`, com numeração de `R-XX` reiniciada e referência cruzada na seção "Round anterior".
````

---

## A matriz de rastreabilidade dessa demanda

Saída do `trace.py` com os cinco fragmentos acima gravados nas pastas de `templates/folder-conventions.md` — é o que o `/leanwork-trace` apresenta, antes da leitura do modelo. O `selftest.py` regenera esta matriz a partir dos fragmentos e falha se ela divergir do texto abaixo.

<!-- trace:start -->
| CA | RN | ADR | UI | T | Review |
|---|---|---|---|---|---|
| CA-01 | RN-01, RN-05 | ADR-002 | UI-01, UI-02 | T-02 | — |
| CA-02 | RN-03 | — | UI-02 | T-04 | — |
| CA-03 | RN-05 | ADR-002 | UI-02 | T-03 | REVIEW-T-03-2026-06-15.md (Bloqueado) |

## Lacunas

- **RN sem cenário:** RN-07
- **Tarefa sem Implementa nem Valida (legítimo se estrutural):** T-01
- **Concluído sem review:** T-01, T-02
- **Review bloqueado sem round seguinte:** T-03 (REVIEW-T-03-2026-06-15.md)

> Aviso: sem git no projeto: coluna de commits omitida
<!-- trace:end -->

## Leitura da matriz

As lacunas acima são as mecânicas, que o script acha sozinho. O que pede julgamento fica para o modelo:

- **RN-07 sem cenário:** "cancelamento só pelo SAC" está declarada, mas sem `CA` → regra não testada. Provavelmente o cancelamento vai virar feature separada (PRD-002). Decidir: mover a RN-07 para o outro PRD ou acrescentar um `CA-04` aqui.
- **T-01 sem `Implementa` nem `Valida`:** legítimo — é a fundação horizontal, sem comportamento a fechar.
- **T-01 e T-02 concluídas sem review:** gap real. O `/leanwork-pipeline` sugere `/leanwork-review` para as duas antes de abrir a `T-04`.
- **T-03 com review bloqueado:** a `T-03` *valida* `CA-03` na matriz, e foi o review que descobriu que o teste não prova o cenário. **O trace verifica menção, não execução** — os dois são complementares, não substitutos.
- **Commits:** num repositório real, a matriz ganha a coluna `Commits` lida do `git log` pelo trailer `Refs:`. Aqui os fragmentos estão fora de um repositório git, e o script avisa que omitiu a coluna em vez de deixá-la vazia.

---

## O que esse exemplo mostra

- **IDs cruzados preenchidos** em todos os artefatos
- **Anotação de ADR no PRD** (`(ADR-002)` ao lado de RN-05)
- **Anotação de RN no Gherkin** (`Dado que existe oferta ativa (RN-01)`)
- **Estado de tela derivado de cenário** (`UI-02.esgotado` nasce de CA-03, não do protótipo)
- **Fatia vertical por `CA-XX`** (T-02, T-03 e T-04 fecham um cenário cada; T-01 é a fundação horizontal)
- **Portas de mão única declaradas** (a migration da T-01, a rota pública da T-02)
- **Tarefa que materializa decisão arquitetural** (T-03 cita ADR-002)
- **Finding que reabre a tarefa** (R-01 devolve T-03 para `Bloqueado`, com o motivo em `**Bloqueio:**`)
- **Elo código → requisito pelo trailer** (`Refs: T-03, CA-03, ADR-002, UI-02.esgotado`)
- **Matriz gerada por script** (a mesma saída que o `trace.py` produz, conferida pelo selftest)
- **Limite do trace exposto** (CA-03 parecia coberto; só o review viu que não)
- **Nomes de teste seguindo a convenção** `CA_XX_descricao`
