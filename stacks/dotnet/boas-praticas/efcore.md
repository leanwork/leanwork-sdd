# EF Core — acesso a dados

Critérios `EF-XX` verificáveis em diff. Formato, adoção e fontes estão no [`README.md`](README.md).

Banco de teste tem pouco dado, então a maior parte destes defeitos passa no CI e aparece em produção. O review é o último ponto barato para pegá-los. SQL cru e injeção estão em [`seguranca-owasp.md`](seguranca-owasp.md) (SEC-14).

**Ferramenta de verificação:** com `LogTo(Console.WriteLine, LogLevel.Information)` ou o logger `Microsoft.EntityFrameworkCore.Database.Command` em `Information`, o teste de integração mostra o SQL gerado e o número de idas ao banco. É a evidência mais direta para EF-01, EF-05 e EF-07.

---

## Quantidade de idas ao banco

### EF-01 — Sem N+1: navegação não é carregada dentro de laço

- **Sinal no diff:** `foreach` sobre resultado de query acessando coleção ou referência de navegação (com lazy loading ligado); query dentro de `foreach`/`Select` (`await db.X.Where(... item.Id ...)` por item); `UseLazyLoadingProxies()` novo.
- **Severidade sugerida:** `Importante`; `Bloqueante` em listagem ou endpoint de alto volume.
- **Certo:** projeção (`Select`) com os dados relacionados numa única query; `Include` quando a entidade completa é necessária; para N chaves, uma query com `Where(x => ids.Contains(x.Id))`.

```csharp
// errado: 1 query de pedidos + 1 por pedido
foreach (var p in await db.Pedidos.ToListAsync(ct))
    total += p.Itens.Sum(i => i.Valor);           // lazy load por iteração

// certo: uma ida ao banco
var totais = await db.Pedidos
    .Select(p => new { p.Id, Total = p.Itens.Sum(i => i.Valor) })
    .ToListAsync(ct);
```

- **Fonte:** [Efficient querying — beware of lazy loading](https://learn.microsoft.com/ef/core/performance/efficient-querying#beware-of-lazy-loading)

### EF-02 — Alteração em massa sem carregar entidades `[EF Core 7+]`

- **Sinal no diff:** carregar N entidades para alterar um campo ou excluir, seguido de `SaveChangesAsync`; `SaveChangesAsync` dentro de laço.
- **Severidade sugerida:** `Importante`.
- **Certo:** `ExecuteUpdateAsync`/`ExecuteDeleteAsync`, uma instrução só; `SaveChangesAsync` uma vez, fora do laço, quando a regra exige carregar as entidades.
- **Atenção:** `ExecuteUpdate`/`ExecuteDelete` não passam pelo change tracker: não disparam interceptors de `SaveChanges`, não atualizam entidades já carregadas no contexto e ignoram concorrência otimista. Se a regra de negócio depende disso (auditoria, evento de domínio), carregar e salvar é o correto.

```csharp
await db.Ofertas.Where(o => o.Fim < agora)
    .ExecuteUpdateAsync(s => s.SetProperty(o => o.Status, StatusOferta.Encerrada), ct);
```

- **Fonte:** [Efficient updating](https://learn.microsoft.com/ef/core/performance/efficient-updating)

### EF-03 — Várias coleções incluídas usam split query (com medição)

- **Sinal no diff:** query com dois ou mais `Include` de **coleção** no mesmo nível (`Include(p => p.Itens).Include(p => p.Pagamentos)`).
- **Severidade sugerida:** `Sugestão`.
- **Por quê:** o JOIN multiplica as linhas (explosão cartesiana). `AsSplitQuery()` faz uma query por coleção. O custo é mais idas ao banco e risco de inconsistência entre as queries sem transação.
- **Fonte:** [Single vs. split queries](https://learn.microsoft.com/ef/core/querying/single-split-queries)

## Volume de dados

### EF-04 — Query de listagem tem limite e ordenação determinística

- **Sinal no diff:** `ToListAsync()` sobre tabela que cresce (pedidos, logs, eventos) sem `Take`; `Skip`/`Take` sem `OrderBy`; `OrderBy` por coluna não única sem desempate.
- **Severidade sugerida:** `Importante`.
- **Certo:** `Take` sempre. Para tabela grande ou rolagem infinita, paginação por chave (keyset): `Where(x => x.Id > ultimoId).OrderBy(x => x.Id).Take(n)`, que usa índice e não degrada nas páginas finais como o `Skip`.
- **Fonte:** [Pagination](https://learn.microsoft.com/ef/core/querying/pagination); [Limit the resultset size](https://learn.microsoft.com/ef/core/performance/efficient-querying#limit-the-resultset-size)

### EF-05 — Filtro roda no banco, não na memória

- **Sinal no diff:** `ToList()`/`ToListAsync()`/`AsEnumerable()` **antes** de `Where`, `OrderBy`, `Count`, `Any` ou `Take`; método C# não traduzível dentro do `Where` forçando avaliação no cliente; `.ToList().Count` ou `Count() > 0` onde cabe `AnyAsync`.
- **Severidade sugerida:** `Importante`.
- **Por quê:** a tabela inteira trafega para filtrar meia dúzia de linhas.
- **Fonte:** [Client vs. server evaluation](https://learn.microsoft.com/ef/core/querying/client-eval)

### EF-06 — Listagem projeta só as colunas que usa

- **Sinal no diff:** query de leitura para tela ou API que materializa entidade completa (com colunas grandes: `byte[]`, `nvarchar(max)`, JSON) e usa poucos campos.
- **Severidade sugerida:** `Sugestão`; `Importante` se carrega coluna grande sem uso.
- **Certo:** `Select(x => new ItemDto(x.Id, x.Nome))`. Projeção também dispensa `AsNoTracking` (EF-07), porque DTO não é rastreado.
- **Fonte:** [Project only properties you need](https://learn.microsoft.com/ef/core/performance/efficient-querying#project-only-properties-you-need)

### EF-07 — Leitura sem alteração não rastreia entidades

- **Sinal no diff:** query de entidades para leitura (endpoint `GET`, relatório) sem `AsNoTracking()`, em projeto cujo contexto não define `QueryTrackingBehavior.NoTracking` por padrão.
- **Severidade sugerida:** `Sugestão`.
- **Não é finding:** query cujo resultado é alterado e salvo em seguida; projeção para DTO.
- **Fonte:** [Tracking vs. no-tracking queries](https://learn.microsoft.com/ef/core/querying/tracking)

### EF-08 — Filtro e ordenação novos têm índice

- **Sinal no diff:** `Where`/`OrderBy` novo por coluna sem índice, em tabela grande, sem `HasIndex` correspondente na configuração do modelo nem na migration da tarefa.
- **Severidade sugerida:** `Sugestão`; `Importante` se o PRD ou a arquitetura priorizam desempenho para aquele fluxo.
- **Fonte:** [Indexes](https://learn.microsoft.com/ef/core/modeling/indexes)

## Ciclo de vida do `DbContext`

### EF-09 — `DbContext` não é usado em paralelo

- **Sinal no diff:** `Task.WhenAll` sobre várias queries no **mesmo** contexto; `Parallel.ForEach` usando o contexto injetado; query disparada sem `await` antes de outra.
- **Severidade sugerida:** `Bloqueante`.
- **Por quê:** o `DbContext` não é thread-safe. O EF Core lança `InvalidOperationException` ("A second operation was started...") quando detecta; quando não detecta, corrompe estado.
- **Certo:** `await` sequencial; ou um contexto por tarefa paralela via `IDbContextFactory<T>`.
- **Fonte:** [Avoiding DbContext threading issues](https://learn.microsoft.com/ef/core/dbcontext-configuration/#avoiding-dbcontext-threading-issues)

### EF-10 — `DbContext` não sobrevive ao escopo que o criou

- **Sinal no diff:** `DbContext` injetado em serviço singleton, `BackgroundService` ou `IHostedService`; contexto capturado em closure de `Task.Run` ou fire-and-forget dentro de um endpoint.
- **Severidade sugerida:** `Bloqueante`.
- **Por quê:** o contexto é scoped à requisição. Usado depois dela, lança `ObjectDisposedException`. Num singleton, vira um contexto eterno que acumula entidades rastreadas e é compartilhado entre threads.
- **Certo:** `IServiceScopeFactory.CreateAsyncScope()` por unidade de trabalho no background, ou `IDbContextFactory<T>`.
- **Fonte:** [DbContext lifetime, configuration, and initialization](https://learn.microsoft.com/ef/core/dbcontext-configuration/); [ASP.NET Core Guidance — fire and forget](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AspNetCoreGuidance.md)

### EF-11 — Todo acesso ao banco em código de requisição é assíncrono

- **Sinal no diff:** `ToList()`, `First()`, `SaveChanges()`, `Find()` síncronos em controller, endpoint, handler ou serviço chamado por eles.
- **Severidade sugerida:** `Importante`.
- **Fonte:** [Asynchronous programming — EF Core](https://learn.microsoft.com/ef/core/miscellaneous/async)

### EF-12 — Pooling de contexto e query compilada só onde o ganho foi medido (com medição)

- **Sinal no diff:** proposta de `AddDbContextPool` ou `EF.CompileAsyncQuery`.
- **Severidade sugerida:** não gera finding por ausência. Se adotado, conferir: contexto com pooling não pode guardar estado próprio entre requisições (campos no `DbContext` derivado); query compilada aceita só parâmetros escalares.
- **Fonte:** [Advanced performance topics](https://learn.microsoft.com/ef/core/performance/advanced-performance-topics)
