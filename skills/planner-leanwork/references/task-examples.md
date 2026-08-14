# Exemplos de Tarefas — Calibragem de Granularidade

Referência para calibrar como tarefas devem ser escritas no plano de execução. Mostra a faixa correta de granularidade (nem grande demais, nem fragmentada demais), o uso correto dos campos de rastreabilidade (`Implementa`, `Valida`, `Decisões base`) e padrões para diferentes tipos de tarefa.

---

## Princípio de granularidade

Boa tarefa cabe em **1 commit ou 1 PR pequeno**, executável em **30 minutos a 4 horas**. Acima disso, quebrar. Abaixo disso (10 min), provavelmente é um detalhe que deveria estar embutido em outra tarefa.

| Sinal de "está grande demais" | Resposta |
|-------------------------------|----------|
| Mais de 3 critérios de aceite | Quebrar em 2 tarefas |
| `Implementa:` lista 4+ RNs | Provavelmente 2 tarefas disfarçadas |
| Descrição precisa de "e também", "além disso" | Sintoma claro de tarefa dupla |
| Mais de 2 horas estimadas mentalmente | Quebrar |
| Mexe em mais de 3 camadas diferentes | Verificar se não dá pra separar por camada |

| Sinal de "está pequena demais" | Resposta |
|--------------------------------|----------|
| Trivial sem critério de aceite real | Fundir com a tarefa anterior |
| "Criar pasta X" | Embutir na tarefa de criação do arquivo |
| "Renomear variável Y" | Não é tarefa de plano, é refactoring inline |

---

## Exemplo 1 — Tarefa estrutural (Fase 1, fundação)

Tarefas estruturais geralmente **não preenchem `Implementa:` nem `Valida:`** porque não materializam regras de negócio diretamente — preparam terreno.

```markdown
#### T-01 — Criar entity FlashSale e configuration EF Core

- [ ] **Status:** Pendente
- **Complexidade:** Baixa
- **Depende de:** nenhuma
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-001 *(estrutura modular monolith)*
- **Camadas/arquivos afetados:**
  - `src/Ultrafarma.Domain/Entities/FlashSale.cs` *(novo)*
  - `src/Ultrafarma.Domain/Entities/FlashSaleItem.cs` *(novo)*
  - `src/Ultrafarma.Infrastructure/Persistence/Configurations/FlashSaleConfiguration.cs` *(novo)*

**Descrição:**
Criar a entidade `FlashSale` com propriedades: `Id`, `ProductId`, `Price`, `Stock`,
`StartsAt`, `EndsAt`, `Status` (enum). Aggregate root com lista de `FlashSaleItem`
(itens vendidos). Configuration EF Core com índice composto em `(ProductId, StartsAt)`
e constraint `EndsAt > StartsAt`. Sem lógica de comportamento ainda — apenas estrutura.

**Critério de aceite (testável):**
- [ ] Entity compila e está mapeada corretamente (verificável via `dotnet ef migrations add`)
- [ ] Configuration aplica constraint e índice

**Testes a escrever:**
- *Não aplicável* — tarefa estrutural. Testes virão nas tarefas T-04 (handler) e T-08 (validation).

**Riscos / pontos de atenção:**
- Padrão de nomenclatura do projeto usa `Entity` como sufixo? Verificar antes em `CLAUDE.md`.
```

---

## Exemplo 2 — Tarefa de lógica de negócio (Fase 2)

Tarefas de lógica de negócio **sempre preenchem `Implementa:`** (regras do PRD) e geralmente **preenchem `Valida:`** (cenários que ficam verdes).

```markdown
#### T-04 — Implementar handler de compra com lock pessimista de estoque

- [ ] **Status:** Pendente
- **Complexidade:** Alta
- **Depende de:** T-01, T-02 (migration), T-03 (interface IFlashSaleRepository)
- **Implementa:** RN-03, RN-05
- **Valida:** CA-04, CA-06
- **Decisões base:** ADR-002 *(lock pessimista para evitar overselling)*
- **Camadas/arquivos afetados:**
  - `src/Ultrafarma.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaCommand.cs` *(novo)*
  - `src/Ultrafarma.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaHandler.cs` *(novo)*
  - `src/Ultrafarma.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaResult.cs` *(novo)*
  - `src/Ultrafarma.Infrastructure/Persistence/Repositories/FlashSaleRepository.cs` *(editado)*

**Descrição:**
Handler MediatR que: (1) abre transação `IsolationLevel.Serializable`,
(2) chama `IFlashSaleRepository.GetByIdWithLockAsync` que executa
`SELECT ... WITH (UPDLOCK, ROWLOCK)`, (3) valida `Stock > 0` e
`!HasCustomerPurchased(customerId)`, (4) decrementa `Stock`, (5) cria
`FlashSaleItem` registrando a compra, (6) commit. Lança `BusinessException`
em violação de regra (estoque esgotado, limite por cliente); deixa exceções
técnicas subirem para middleware global.

**Critério de aceite (testável):**
- [ ] CA-04 verde: compra atômica decrementa estoque e cria registro de venda
- [ ] CA-06 verde: 100 compras concorrentes em estoque=10 → exatamente 10 sucessos
- [ ] Exceções técnicas (SQL timeout, etc) não são convertidas em `BusinessException`

**Testes a escrever:**
- *Unit:* `CA_04_Compra_com_sucesso_decrementa_estoque`,
  `Handler_lanca_BusinessException_quando_estoque_zero`,
  `Handler_lanca_BusinessException_quando_cliente_ja_comprou`
- *Integration:* `Compra_em_oferta_ativa_persiste_em_banco_real`
- *Stress (xUnit + Task.WhenAll):* `CA_06_100_compras_concorrentes_respeitam_estoque_atomico`

**Riscos / pontos de atenção:**
- Lock pessimista em produção tem custo de bloqueio — monitorar `sys.dm_tran_locks`
  na primeira janela de Black Friday (entrar em T-12, observabilidade)
- Cuidado com timeout de transação — definir explicitamente
  `IsolationLevel.Serializable` e `CommandTimeout=10s` no DbContextOptions
- **Ponto de validação humana sugerido:** revisar implementação com tech lead
  antes de avançar para T-05 (controller). Lock pessimista é decisão de impacto
  operacional.
```

---

## Exemplo 3 — Tarefa de exposição (Fase 3)

Tarefas de controller/endpoint **preenchem `Valida:`** porque sua conclusão é o que faz o cenário Gherkin acontecer end-to-end.

```markdown
#### T-09 — Expor endpoint POST /api/flash-sales/{id}/comprar

- [ ] **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-04 (handler), T-08 (validator)
- **Implementa:** —
- **Valida:** CA-04, CA-05, CA-06, CA-07 *(todos os cenários do funcional principal)*
- **Decisões base:** ADR-003 *(REST + MediatR como padrão de entrada)*
- **Camadas/arquivos afetados:**
  - `src/Ultrafarma.Api/Controllers/FlashSalesController.cs` *(editado)*
  - `src/Ultrafarma.Api/DTOs/ComprarOfertaRequest.cs` *(novo)*

**Descrição:**
Endpoint REST que recebe `ComprarOfertaRequest`, monta `ComprarOfertaCommand`
com `customerId` extraído do JWT claim `sub`, despacha via MediatR e mapeia
resultado para HTTP: sucesso → 200 com `ComprarOfertaResponse`,
`BusinessException` → 422 com mensagem de negócio, demais exceções → 500
via middleware global.

**Critério de aceite (testável):**
- [ ] Compra autenticada bem-sucedida retorna 200 (CA-04)
- [ ] Compra com estoque zero retorna 422 com mensagem específica (CA-06)
- [ ] Compra fora da janela retorna 422 com mensagem específica (CA-07)
- [ ] Compra sem JWT retorna 401

**Testes a escrever:**
- *Integration (com WebApplicationFactory):*
  `POST_comprar_flash_sale_retorna_200_quando_valido`,
  `POST_comprar_flash_sale_retorna_422_quando_estoque_zero`,
  `POST_comprar_flash_sale_retorna_401_sem_autenticacao`

**Riscos / pontos de atenção:**
- Verificar se rate limiting do endpoint precisa ser mais restrito que o padrão
  (oferta relâmpago pode atrair bots)
- Conferir se o JWT claim `sub` é o ID do cliente ou se precisa de mapeamento
```

---

## Exemplo 4 — Tarefa de qualidade transversal (Fase 5)

Tarefas de observabilidade, métricas, logging tipicamente **não preenchem `Implementa:` nem `Valida:`** — não materializam regra de negócio nem fecham cenário, mas são obrigatórias para produção.

```markdown
#### T-12 — Adicionar instrumentação de métricas e logging estruturado

- [ ] **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-09 (endpoint pronto)
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-008 *(observabilidade via Application Insights)*
- **Camadas/arquivos afetados:**
  - `src/Ultrafarma.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaHandler.cs` *(editado)*
  - `src/Ultrafarma.Infrastructure/Telemetry/FlashSaleMetrics.cs` *(novo)*

**Descrição:**
Adicionar: (1) log estruturado com Serilog no handler com propriedades
`flashSaleId`, `customerId`, `outcome` (success/sold_out/limit_exceeded);
(2) métricas custom no Application Insights: `flash_sale_purchase_attempts`,
`flash_sale_purchase_outcomes` com tag `outcome`; (3) custom metric de
`stock_remaining_at_purchase` para análise post-mortem.

**Critério de aceite (testável):**
- [ ] Cada tentativa de compra gera log estruturado com correlation id
- [ ] Métricas custom aparecem no App Insights em ambiente local
- [ ] PII (CPF, email) NÃO aparece nos logs

**Testes a escrever:**
- *Unit (com fake logger):* `Handler_emite_log_com_outcome_correto_em_sucesso`,
  `Handler_nao_emite_PII_em_log`

**Riscos / pontos de atenção:**
- Cuidado com cardinalidade de tags em métricas custom — `customerId` como tag
  exploda cardinality. Manter como log property, não tag de métrica.
```

---

## Exemplo 5 — Tarefa que materializa decisão arquitetural

Quando uma tarefa **existe especificamente para implementar uma decisão arquitetural**, `Decisões base:` carrega o ADR e `Implementa:` pode ficar vazio se nenhuma regra de negócio do PRD a justifica diretamente.

```markdown
#### T-15 — Configurar feature flag para "Ofertas Relâmpago" via LaunchDarkly

- [ ] **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-09 (endpoint pronto)
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-006 *(roll-out controlado via feature flag)*
- **Camadas/arquivos afetados:**
  - `src/Ultrafarma.Api/Controllers/FlashSalesController.cs` *(editado)*
  - `src/Ultrafarma.Web/Pages/Home.razor` *(editado)*
  - `appsettings.json` *(editado)*

**Descrição:**
Adicionar gate `FeatureFlag.FlashSales` no endpoint POST e no componente de UI.
Configurar flag no LaunchDarkly com targeting: `false` por padrão, `true` para
clientes do canary group `flash-sales-canary`. Documentar no `CLAUDE.md` do
projeto como ativar/desativar.

**Critério de aceite (testável):**
- [ ] Com flag OFF: endpoint retorna 404 e UI esconde seção
- [ ] Com flag ON: comportamento normal
- [ ] Targeting funciona para canary group

**Testes a escrever:**
- *Integration:* `Endpoint_retorna_404_quando_feature_flag_off`,
  `Endpoint_funciona_quando_feature_flag_on`

**Riscos / pontos de atenção:**
- Ponto de validação humana antes de ativar em produção: confirmar que a flag
  está em OFF no environment de produção do LaunchDarkly antes do deploy
```

---

## Quando uma tarefa NÃO preenche todos os campos

Cenários legítimos onde algum campo fica vazio:

| Situação | `Implementa` | `Valida` | `Decisões base` |
|----------|--------------|----------|-----------------|
| Estrutural (entity, migration) | vazio | vazio | pode citar ADR de estrutura |
| Lógica de negócio | obrigatório (RN) | provável (CA) | provável (ADR) |
| Exposição (controller, endpoint) | vazio (já implementado em handler) | provável (CA) | pode citar |
| UI (componente) | vazio | possível (CA de UX) | possível |
| Observabilidade | vazio | vazio | provável |
| Testes transversais | vazio | múltiplos CAs | vazio |
| Migração de dados | vazio | vazio | possível |

**Regra de bolso:** se a tarefa não preenche nenhum dos três campos, perguntar: ela é realmente necessária? Tarefas sem rastreabilidade nenhuma são candidatas a serem cortadas ou fundidas a outras.
