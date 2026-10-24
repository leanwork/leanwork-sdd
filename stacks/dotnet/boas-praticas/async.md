# async/await e concorrência

Critérios `ASY-XX` verificáveis em diff. Formato, adoção e fontes estão no [`README.md`](README.md).

O ASP.NET Core atende muitas requisições com poucas threads, desde que nenhuma fique bloqueada esperando I/O. Quase todo defeito deste arquivo leva ao mesmo sintoma em produção: **thread pool starvation**. A latência sobe para todos os endpoints de uma vez, sem CPU alta, e o problema some quando a carga cai. Não aparece em teste unitário.

---

### ASY-01 — Sem bloqueio sobre `Task` (sync over async)

- **Sinal no diff:** `.Result`, `.Wait()`, `.GetAwaiter().GetResult()`, `Task.WaitAll` em código alcançável por requisição, handler ou hosted service.
- **Severidade sugerida:** `Bloqueante`.
- **Certo:** `await` em toda a cadeia até o endpoint.
- **Não é finding:** `Main` síncrono de ferramenta de console; `.Result` sobre `Task` que já foi aguardada (depois de `await Task.WhenAll(...)`).
- **Fonte:** [ASP.NET Core Best Practices — avoid blocking calls](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#avoid-blocking-calls)

### ASY-02 — Sem `async void`

- **Sinal no diff:** método `async void` que não é event handler de UI; lambda `async` passada para parâmetro do tipo `Action` (vira `async void` sem aparecer na assinatura), como `list.ForEach(async x => ...)`.
- **Severidade sugerida:** `Bloqueante`.
- **Por quê:** exceção em `async void` não tem `Task` para ser observada e derruba o processo. Em action de controller, o método retorna antes do trabalho terminar.
- **Fonte:** [Async Guidance — async void](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md#async-void)

### ASY-03 — `CancellationToken` aceito e repassado até o I/O

- **Sinal no diff:** método assíncrono público novo sem parâmetro `CancellationToken`; método que recebe o token e não o repassa para EF Core, `HttpClient`, `Stream`, `Task.Delay` ou fila.
- **Severidade sugerida:** `Importante`.
- **Nota:** em endpoint, o binding injeta `HttpContext.RequestAborted` num parâmetro `CancellationToken`. Em hosted service, o token é o `stoppingToken`.
- **Fonte:** [Async Guidance — cancellation](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md#cancelling-uncancellable-operations)

### ASY-04 — Sem `Task.Run` para "tornar assíncrono" nem para disparar e esquecer

- **Sinal no diff:** `await Task.Run(() => metodoSincrono())` em código de requisição; `_ = Task.Run(...)` ou `Task` sem `await` dentro de endpoint para trabalho que deve sobreviver à resposta.
- **Severidade sugerida:** `Importante`; `Bloqueante` se a closure captura serviço scoped (`DbContext`, `HttpContext`), ver EF-10 e WEB-04.
- **Por quê:** o ASP.NET Core já roda o código na thread pool. `Task.Run` só agenda outra thread da mesma pool. Fire-and-forget não sobrevive a restart, perde exceções e usa serviços já descartados.
- **Certo:** trabalho que não cabe na requisição vai para `BackgroundService` alimentado por `Channel<T>` ou para uma fila (Service Bus, RabbitMQ), cada item com o próprio escopo de DI.
- **Fonte:** [ASP.NET Core Best Practices](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#avoid-blocking-calls); [ASP.NET Core Guidance — fire and forget](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AspNetCoreGuidance.md)

### ASY-05 — Exclusão mútua em código assíncrono usa `SemaphoreSlim`, fora do caminho comum

- **Sinal no diff:** `lock` em caminho chamado por toda requisição; `Monitor`/`Mutex` em volta de I/O; tentativa de `await` dentro de `lock` contornada com `.Result` (ver ASY-01).
- **Severidade sugerida:** `Importante`.
- **Certo:** `await semaphore.WaitAsync(ct)` com `try/finally` para `Release()`. Melhor ainda é eliminar o estado compartilhado (`ConcurrentDictionary`, cache com proteção contra stampede, ver WEB-06).
- **Não é finding:** `lock` curto em seção sem I/O fora do caminho quente.
- **Fonte:** [ASP.NET Core Best Practices — "do not acquire locks in common code paths"](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#avoid-blocking-calls)

### ASY-06 — Paralelismo sobre coleção tem limite

- **Sinal no diff:** `await Task.WhenAll(itens.Select(i => ChamarAsync(i)))` sobre coleção sem tamanho limitado (vinda do banco, de arquivo, do request).
- **Severidade sugerida:** `Importante`.
- **Por quê:** mil itens viram mil chamadas simultâneas à dependência, que cai ou começa a responder 429.
- **Certo:** `Parallel.ForEachAsync(itens, new ParallelOptions { MaxDegreeOfParallelism = n, CancellationToken = ct }, ...)` `[.NET 6+]`, ou lotes.
- **Fonte:** [Parallel.ForEachAsync](https://learn.microsoft.com/dotnet/api/system.threading.tasks.parallel.foreachasync)

### ASY-07 — `TaskCompletionSource` com continuações assíncronas

- **Sinal no diff:** `new TaskCompletionSource<T>()` sem `TaskCreationOptions.RunContinuationsAsynchronously`.
- **Severidade sugerida:** `Importante`.
- **Por quê:** sem a opção, quem chama `SetResult` executa a continuação do `await` na própria thread. Isso causa deadlock e estado corrompido difíceis de reproduzir. Atenção para não confundir com `TaskContinuationOptions.RunContinuationsAsynchronously`, de nome igual e efeito nenhum aqui.
- **Fonte:** [Async Guidance — TaskCompletionSource](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md)

### ASY-08 — Construtor e factory de DI não fazem I/O

- **Sinal no diff:** construtor ou lambda de registro (`AddSingleton(sp => ...)`) que lê banco, chama HTTP ou abre arquivo, com ou sem `.Result`.
- **Severidade sugerida:** `Importante`.
- **Certo:** inicialização assíncrona em `IHostedService.StartAsync`, ou carga preguiçosa com `Lazy<Task<T>>`/cache.
- **Fonte:** [Async Guidance — constructors](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md#constructors)

---

## Não é finding

- **`ConfigureAwait(false)` ausente em código de aplicação ASP.NET Core.** Não existe `SynchronizationContext` no ASP.NET Core, então a ausência não causa deadlock nem custo relevante. Em **biblioteca** reutilizável (pacote NuGet interno), aí sim é convenção recomendada.
- **`return Task` direto em vez de `return await`.** É escolha de estilo com trade-off (stack trace, `using`). Só vira finding se o projeto declarar a convenção.
- **`ValueTask` vs `Task`.** Otimização de alocação para APIs muito quentes. Sem medição, não é finding.
