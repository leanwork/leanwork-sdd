# Exemplos de Tarefas — Calibrados em .NET

Esta é a versão com código real em .NET (MediatR, EF Core, FluentValidation, xUnit) dos seis exemplos de `skills/planner-leanwork/references/task-examples.md`. Estrutura, campos de rastreabilidade e princípio de granularidade são os mesmos — só o código muda. Para o "Princípio de granularidade" e a tabela "Quando uma tarefa NÃO preenche todos os campos", ver o arquivo agnóstico.

Está em `stacks/dotnet/` porque é um exemplo aplicado a uma stack, não parte do núcleo agnóstico do planner. Outras stacks podem ganhar seu próprio `stacks/<nome>/task-examples.md` seguindo a mesma estrutura.

---

## Exemplo 1 — Tarefa estrutural (Fase 1, fundação)

Tarefas estruturais geralmente **não preenchem `Implementa:` nem `Valida:`** porque não materializam regras de negócio diretamente — preparam terreno.

```markdown
#### T-01 — Criar entity FlashSale e configuration EF Core

- **Status:** Pendente
- **Complexidade:** Baixa
- **Depende de:** nenhuma
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-001 *(estrutura modular monolith)*
- **Camadas/arquivos afetados:**
  - `src/Contoso.Domain/Entities/FlashSale.cs` *(novo)*
  - `src/Contoso.Domain/Entities/FlashSaleItem.cs` *(novo)*
  - `src/Contoso.Infrastructure/Persistence/Configurations/FlashSaleConfiguration.cs` *(novo)*

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

- **Status:** Pendente
- **Complexidade:** Alta
- **Depende de:** T-01, T-02 (migration), T-03 (interface IFlashSaleRepository)
- **Implementa:** RN-03, RN-05
- **Valida:** CA-04, CA-06
- **Decisões base:** ADR-002 *(lock pessimista para evitar overselling)*
- **Camadas/arquivos afetados:**
  - `src/Contoso.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaCommand.cs` *(novo)*
  - `src/Contoso.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaHandler.cs` *(novo)*
  - `src/Contoso.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaResult.cs` *(novo)*
  - `src/Contoso.Infrastructure/Persistence/Repositories/FlashSaleRepository.cs` *(editado)*

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

- **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-04 (handler), T-08 (validator)
- **Implementa:** —
- **Valida:** CA-04, CA-05, CA-06, CA-07 *(todos os cenários do funcional principal)*
- **Decisões base:** ADR-003 *(REST + MediatR como padrão de entrada)*
- **Camadas/arquivos afetados:**
  - `src/Contoso.Api/Controllers/FlashSalesController.cs` *(editado)*
  - `src/Contoso.Api/DTOs/ComprarOfertaRequest.cs` *(novo)*

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

- **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-09 (endpoint pronto)
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-008 *(observabilidade via Application Insights)*
- **Camadas/arquivos afetados:**
  - `src/Contoso.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaHandler.cs` *(editado)*
  - `src/Contoso.Infrastructure/Telemetry/FlashSaleMetrics.cs` *(novo)*

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

- **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-09 (endpoint pronto)
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-006 *(roll-out controlado via feature flag)*
- **Camadas/arquivos afetados:**
  - `src/Contoso.Api/Controllers/FlashSalesController.cs` *(editado)*
  - `src/Contoso.Web/Pages/Home.razor` *(editado)*
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

## Exemplo 6 — Fatia vertical deliberada (entrega incremental ou risco de integração)

Exceção ao padrão horizontal dos Exemplos 1-4. Só se aplica quando a entrevista (Bloco 2 ou Bloco 4 de `SKILL.md`) sinalizou entrega incremental real ou risco de integração concreto — ver `SKILL.md`, seção "Orientação da fatia". Fora desses gatilhos, a quebra continua por camada.

A fatia atravessa as camadas de propósito, mas o comportamento coberto fica estreito o bastante (só o caminho feliz de um `CA-XX`) para caber no mesmo teto de 4h que os Exemplos 1-4 — o corte estreito aqui é por cenário, não por camada.

```markdown
#### T-01 — Fatia: comprar oferta relâmpago, caminho feliz

- **Status:** Pendente
- **Complexidade:** Alta
- **Depende de:** nenhuma
- **Implementa:** RN-03
- **Valida:** CA-04
- **Decisões base:** ADR-002 *(lock pessimista — adiado para a próxima fatia)*, ADR-003 *(REST + MediatR)*
- **Camadas/arquivos afetados:**
  - `src/Contoso.Domain/Entities/FlashSale.cs` *(novo)*
  - `src/Contoso.Application/Features/FlashSale/Commands/ComprarOferta/ComprarOfertaHandler.cs` *(novo)*
  - `src/Contoso.Infrastructure/Persistence/Configurations/FlashSaleConfiguration.cs` *(novo)*
  - `src/Contoso.Api/Controllers/FlashSalesController.cs` *(novo)*

**Descrição:**
Fatia mínima que atravessa as quatro camadas só para o caminho feliz: entity
+ configuration, handler que decrementa estoque sem lock pessimista ainda
(lock e concorrência são CA-06, ficam para a próxima fatia), e endpoint que
expõe o handler. Sem tratamento de erro além do óbvio (estoque zero). O
objetivo é ter algo demonstrável e verificável ponta a ponta o quanto antes —
não cobrir a funcionalidade inteira nesta tarefa.

**Critério de aceite (testável):**
- [ ] CA-04 verde: `POST /api/flash-sales/{id}/comprar` com estoque disponível
      retorna 200 e decrementa estoque em 1

**Testes a escrever:**
- *Integration (com WebApplicationFactory):* `CA_04_Compra_com_sucesso_decrementa_estoque`

**Riscos / pontos de atenção:**
- Concorrência (CA-06) e limite por cliente (RN-05) ficam para a fatia
  seguinte — não implementar lock pessimista aqui, é escopo de outra tarefa
- Fatia estreita gera **mais tarefas no total** que a quebra horizontal
  equivalente (compare com T-01/T-04/T-09 dos Exemplos 1 e 3, que cobrem a
  mesma feature): o ganho é demonstrabilidade cedo, não menos tarefas
```

---

## Convenção de nomenclatura de testes (xUnit)

Versão em .NET/xUnit da convenção descrita em `templates/id-conventions.md`, seção "Convenções de nomenclatura de testes".

```csharp
// xUnit
[Fact]
public void CA_01_Cliente_compra_produto_em_flash_sale_com_sucesso()
{
    // arrange / act / assert
}

[Theory]
[InlineData("CA-02", 0)]
[InlineData("CA-02", -1)]
public void CA_02_Compra_falha_quando_estoque_insuficiente(string ca, int estoque)
{
    // ...
}
```
