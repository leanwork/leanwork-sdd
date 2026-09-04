# Exemplos de Tarefas — Calibragem de Granularidade

Referência para calibrar como tarefas devem ser escritas no plano de execução. Mostra a faixa correta de granularidade (nem grande demais, nem fragmentada demais), o uso correto dos campos de rastreabilidade (`Implementa`, `Valida`, `Decisões base`) e padrões para diferentes tipos de tarefa.

Os exemplos abaixo usam pseudocódigo e nomes de camada genéricos — nenhum framework ou biblioteca específica. Para ver os mesmos seis exemplos com código real (.NET, EF Core, MediatR, xUnit, Serilog, LaunchDarkly), ver `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/task-examples.md`.

---

## Princípio de granularidade

Boa tarefa cabe em **1 commit ou 1 PR pequeno**, executável em **30 minutos a 4 horas** — teto canônico declarado em `templates/id-conventions.md` (regra de `T-XX`). Acima disso, quebrar. Abaixo disso (10 min), provavelmente é um detalhe que deveria estar embutido em outra tarefa.

A faixa calibra a quebra na cabeça de quem planeja; ela não vira campo da tarefa. O plano registra `Complexidade` qualitativa, nunca horas.

| Sinal de "está grande demais" | Resposta |
|-------------------------------|----------|
| Mais de 3 critérios de aceite | Quebrar em 2 tarefas |
| `Implementa:` lista 4+ RNs | Provavelmente 2 tarefas disfarçadas |
| Descrição precisa de "e também", "além disso" | Sintoma claro de tarefa dupla |
| Mais de 4 horas estimadas mentalmente | Quebrar |
| Mexe em mais de 3 camadas diferentes | Verificar se não dá pra separar por camada — **exceto** em fatia vertical deliberada (Exemplo 6), onde atravessar camadas é o objetivo e o corte certo é por comportamento, não por camada |

| Sinal de "está pequena demais" | Resposta |
|--------------------------------|----------|
| Trivial sem critério de aceite real | Fundir com a tarefa anterior |
| "Criar pasta X" | Embutir na tarefa de criação do arquivo |
| "Renomear variável Y" | Não é tarefa de plano, é refactoring inline |

---

## Exemplo 1 — Tarefa estrutural (Fase 1, fundação)

Tarefas estruturais geralmente **não preenchem `Implementa:` nem `Valida:`** porque não materializam regras de negócio diretamente — preparam terreno.

```markdown
#### T-01 — Criar entidade FlashSale e mapeamento de persistência

- **Status:** Pendente
- **Complexidade:** Baixa
- **Depende de:** nenhuma
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-001 *(estrutura modular monolith)*
- **Camadas/arquivos afetados:**
  - `dominio/entidades/flash-sale` *(novo)*
  - `dominio/entidades/flash-sale-item` *(novo)*
  - `infraestrutura/persistencia/mapeamento-flash-sale` *(novo)*

**Descrição:**
Criar a entidade `FlashSale` com propriedades: `id`, `produtoId`, `preco`, `estoque`,
`iniciaEm`, `terminaEm`, `status` (enum). Aggregate root com lista de `FlashSaleItem`
(itens vendidos). Mapeamento de persistência com índice composto em
`(produtoId, iniciaEm)` e constraint `terminaEm > iniciaEm`. Sem lógica de
comportamento ainda — apenas estrutura.

**Critério de aceite (testável):**
- [ ] Entidade compila e está mapeada corretamente (verificável via geração/dry-run de migration)
- [ ] Mapeamento aplica constraint e índice

**Testes a escrever:**
- *Não aplicável* — tarefa estrutural. Testes virão nas tarefas T-04 (handler) e T-08 (validação).

**Riscos / pontos de atenção:**
- Padrão de nomenclatura do projeto usa algum sufixo específico para entidades? Verificar antes em `CLAUDE.md`.
```

---

## Exemplo 2 — Tarefa de lógica de negócio (Fase 2)

Tarefas de lógica de negócio **sempre preenchem `Implementa:`** (regras do PRD) e geralmente **preenchem `Valida:`** (cenários que ficam verdes).

```markdown
#### T-04 — Implementar handler de compra com lock pessimista de estoque

- **Status:** Pendente
- **Complexidade:** Alta
- **Depende de:** T-01, T-02 (migration), T-03 (interface do repositório)
- **Implementa:** RN-03, RN-05
- **Valida:** CA-04, CA-06
- **Decisões base:** ADR-002 *(lock pessimista para evitar overselling)*
- **Camadas/arquivos afetados:**
  - `aplicacao/flash-sale/comandos/comprar-oferta/comando` *(novo)*
  - `aplicacao/flash-sale/comandos/comprar-oferta/handler` *(novo)*
  - `aplicacao/flash-sale/comandos/comprar-oferta/resultado` *(novo)*
  - `infraestrutura/persistencia/repositorios/flash-sale-repositorio` *(editado)*

**Descrição:**
Handler que: (1) abre transação com isolamento serializável, (2) chama
`buscarPorIdComLock`, que lê a linha da oferta com lock pessimista de escrita
(bloqueio exclusivo até o commit), (3) valida `estoque > 0` e
`!clienteJaComprou(clienteId)`, (4) decrementa `estoque`, (5) cria
`FlashSaleItem` registrando a compra, (6) commit. Lança exceção de negócio
em violação de regra (estoque esgotado, limite por cliente); deixa exceções
técnicas subirem para o tratamento de erro global.

**Critério de aceite (testável):**
- [ ] CA-04 verde: compra atômica decrementa estoque e cria registro de venda
- [ ] CA-06 verde: 100 compras concorrentes em estoque=10 → exatamente 10 sucessos
- [ ] Exceções técnicas (timeout de banco, etc.) não são convertidas em exceção de negócio

**Testes a escrever:**
- *Unit:* `CA_04_compra_com_sucesso_decrementa_estoque`,
  `handler_lanca_excecao_de_negocio_quando_estoque_zero`,
  `handler_lanca_excecao_de_negocio_quando_cliente_ja_comprou`
- *Integration:* `compra_em_oferta_ativa_persiste_em_banco_real`
- *Stress (execução concorrente):* `CA_06_100_compras_concorrentes_respeitam_estoque_atomico`

**Riscos / pontos de atenção:**
- Lock pessimista em produção tem custo de bloqueio — monitorar contenção de locks
  na primeira janela de Black Friday (entrar em T-12, observabilidade)
- Cuidado com timeout de transação — definir explicitamente isolamento serializável
  e timeout de comando na configuração de acesso a dados
- **Ponto de validação humana sugerido:** revisar implementação com tech lead
  antes de avançar para T-05 (endpoint). Lock pessimista é decisão de impacto
  operacional.
```

---

## Exemplo 3 — Tarefa de exposição (Fase 3)

Tarefas de controller/endpoint **preenchem `Valida:`** porque sua conclusão é o que faz o cenário Gherkin acontecer end-to-end.

```markdown
#### T-09 — Expor endpoint POST /api/flash-sales/{id}/comprar

- **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-04 (handler), T-08 (validador)
- **Implementa:** —
- **Valida:** CA-04, CA-05, CA-06, CA-07 *(todos os cenários do funcional principal)*
- **Decisões base:** ADR-003 *(REST + pipeline de handlers como padrão de entrada)*
- **Camadas/arquivos afetados:**
  - `api/controllers/flash-sales-controller` *(editado)*
  - `api/dtos/comprar-oferta-request` *(novo)*

**Descrição:**
Endpoint REST que recebe `ComprarOfertaRequest`, monta o comando `ComprarOferta`
com `clienteId` extraído do token de autenticação, despacha para o handler e mapeia
resultado para HTTP: sucesso → 200 com `ComprarOfertaResponse`,
exceção de negócio → 422 com mensagem de negócio, demais exceções → 500
via tratamento de erro global.

**Critério de aceite (testável):**
- [ ] Compra autenticada bem-sucedida retorna 200 (CA-04)
- [ ] Compra com estoque zero retorna 422 com mensagem específica (CA-06)
- [ ] Compra fora da janela retorna 422 com mensagem específica (CA-07)
- [ ] Compra sem autenticação retorna 401

**Testes a escrever:**
- *Integration (com cliente HTTP de teste):*
  `POST_comprar_flash_sale_retorna_200_quando_valido`,
  `POST_comprar_flash_sale_retorna_422_quando_estoque_zero`,
  `POST_comprar_flash_sale_retorna_401_sem_autenticacao`

**Riscos / pontos de atenção:**
- Verificar se rate limiting do endpoint precisa ser mais restrito que o padrão
  (oferta relâmpago pode atrair bots)
- Conferir se o claim de identidade do token é o ID do cliente ou se precisa de mapeamento
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
- **Decisões base:** ADR-008 *(observabilidade via ferramenta de APM)*
- **Camadas/arquivos afetados:**
  - `aplicacao/flash-sale/comandos/comprar-oferta/handler` *(editado)*
  - `infraestrutura/telemetria/flash-sale-metricas` *(novo)*

**Descrição:**
Adicionar: (1) log estruturado no handler com propriedades `flashSaleId`,
`clienteId`, `outcome` (success/sold_out/limit_exceeded); (2) métricas custom
na ferramenta de APM: `flash_sale_purchase_attempts`,
`flash_sale_purchase_outcomes` com tag `outcome`; (3) métrica custom de
`stock_remaining_at_purchase` para análise post-mortem.

**Critério de aceite (testável):**
- [ ] Cada tentativa de compra gera log estruturado com correlation id
- [ ] Métricas custom aparecem na ferramenta de APM em ambiente local
- [ ] PII (CPF, email) NÃO aparece nos logs

**Testes a escrever:**
- *Unit (com logger fake):* `handler_emite_log_com_outcome_correto_em_sucesso`,
  `handler_nao_emite_pii_em_log`

**Riscos / pontos de atenção:**
- Cuidado com cardinalidade de tags em métricas custom — `clienteId` como tag
  explode cardinalidade. Manter como propriedade de log, não tag de métrica.
```

---

## Exemplo 5 — Tarefa que materializa decisão arquitetural

Quando uma tarefa **existe especificamente para implementar uma decisão arquitetural**, `Decisões base:` carrega o ADR e `Implementa:` pode ficar vazio se nenhuma regra de negócio do PRD a justifica diretamente.

```markdown
#### T-15 — Configurar feature flag para "Ofertas Relâmpago"

- **Status:** Pendente
- **Complexidade:** Média
- **Depende de:** T-09 (endpoint pronto)
- **Implementa:** —
- **Valida:** —
- **Decisões base:** ADR-006 *(roll-out controlado via feature flag)*
- **Camadas/arquivos afetados:**
  - `api/controllers/flash-sales-controller` *(editado)*
  - `web/paginas/home` *(editado)*
  - `configuracao/app` *(editado)*

**Descrição:**
Adicionar gate `FeatureFlag.FlashSales` no endpoint POST e no componente de UI.
Configurar flag no serviço de feature flag com targeting: `false` por padrão,
`true` para clientes do canary group `flash-sales-canary`. Documentar no
`CLAUDE.md` do projeto como ativar/desativar.

**Critério de aceite (testável):**
- [ ] Com flag OFF: endpoint retorna 404 e UI esconde seção
- [ ] Com flag ON: comportamento normal
- [ ] Targeting funciona para canary group

**Testes a escrever:**
- *Integration:* `endpoint_retorna_404_quando_feature_flag_off`,
  `endpoint_funciona_quando_feature_flag_on`

**Riscos / pontos de atenção:**
- Ponto de validação humana antes de ativar em produção: confirmar que a flag
  está em OFF no environment de produção antes do deploy
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
- **Decisões base:** ADR-002 *(lock pessimista — adiado para a próxima fatia)*, ADR-003 *(REST + pipeline de handlers)*
- **Camadas/arquivos afetados:**
  - `dominio/entidades/flash-sale` *(novo)*
  - `aplicacao/flash-sale/comandos/comprar-oferta/handler` *(novo)*
  - `infraestrutura/persistencia/mapeamento-flash-sale` *(novo)*
  - `api/controllers/flash-sales-controller` *(novo)*

**Descrição:**
Fatia mínima que atravessa as quatro camadas só para o caminho feliz: entidade
+ mapeamento, handler que decrementa estoque sem lock pessimista ainda
(lock e concorrência são CA-06, ficam para a próxima fatia), e endpoint que
expõe o handler. Sem tratamento de erro além do óbvio (estoque zero). O
objetivo é ter algo demonstrável e verificável ponta a ponta o quanto antes —
não cobrir a funcionalidade inteira nesta tarefa.

**Critério de aceite (testável):**
- [ ] CA-04 verde: `POST /api/flash-sales/{id}/comprar` com estoque disponível
      retorna 200 e decrementa estoque em 1

**Testes a escrever:**
- *Integration (com cliente HTTP de teste):* `CA_04_compra_com_sucesso_decrementa_estoque`

**Riscos / pontos de atenção:**
- Concorrência (CA-06) e limite por cliente (RN-05) ficam para a fatia
  seguinte — não implementar lock pessimista aqui, é escopo de outra tarefa
- Fatia estreita gera **mais tarefas no total** que a quebra horizontal
  equivalente (compare com T-01/T-04/T-09 dos Exemplos 1 e 3, que cobrem a
  mesma feature): o ganho é demonstrabilidade cedo, não menos tarefas
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
