# Desempenho no pipeline HTTP do ASP.NET Core

Critérios `WEB-XX` verificáveis em diff. Formato, adoção e fontes estão no [`README.md`](README.md).

Acesso a dados está em [`efcore.md`](efcore.md), chamadas de saída em [`httpclient.md`](httpclient.md) e async em [`async.md`](async.md). Aqui fica o que é próprio da borda HTTP: contrato de listagem, leitura do corpo, cache, logging e serialização.

---

## Contrato e corpo da requisição

### WEB-01 — Endpoint de listagem tem paginação com teto no servidor

- **Sinal no diff:** endpoint que devolve coleção sem parâmetros de página; `pageSize` aceito do cliente sem teto (`?pageSize=1000000`).
- **Severidade sugerida:** `Importante`.
- **Certo:** teto aplicado no servidor (`Math.Clamp(pageSize, 1, 100)`), e a query obedece (EF-04).
- **Fonte:** [ASP.NET Core Best Practices — return large collections across multiple smaller pages](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#return-large-collections-across-multiple-smaller-pages)

### WEB-02 — Coleção não é devolvida como `IEnumerable` preguiçoso

- **Sinal no diff:** action que retorna `IEnumerable<T>` vindo direto de `IQueryable`/LINQ sem materializar.
- **Severidade sugerida:** `Importante`.
- **Por quê:** o serializador enumera de forma síncrona, o que bloqueia a thread (ASY-01) e pode executar a query depois de o contexto ter sido descartado.
- **Certo:** `await ...ToListAsync(ct)`, ou `IAsyncEnumerable<T>` para streaming.
- **Fonte:** [Return IEnumerable\<T\> or IAsyncEnumerable\<T\>](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#return-ienumerablet-or-iasyncenumerablet)

### WEB-03 — Corpo da requisição não é lido de forma síncrona nem inteiro em memória

- **Sinal no diff:** `new StreamReader(Request.Body).ReadToEnd()`; `Request.Form` (síncrono) em vez de `await Request.ReadFormAsync()`; `AllowSynchronousIO = true`; upload grande copiado inteiro para `MemoryStream`.
- **Severidade sugerida:** `Importante`.
- **Certo:** `ReadToEndAsync`, `ReadFormAsync`, binding de `IFormFile` com limite (`[RequestSizeLimit]`, ver SEC-16) e cópia por stream para o destino. Arquivo grande: streaming com `MultipartReader`.
- **Fonte:** [Avoid synchronous read or write on HttpRequest/HttpResponse body](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#avoid-synchronous-read-or-write-on-httprequesthttpresponse-body)

### WEB-04 — `HttpContext` não é usado fora da requisição

- **Sinal no diff:** `HttpContext` ou `IHttpContextAccessor.HttpContext` lido em thread de background, depois de `Task.Run`, ou guardado em campo de serviço singleton.
- **Severidade sugerida:** `Bloqueante`.
- **Por quê:** `HttpContext` não é thread-safe e é reciclado ao fim da requisição. Fora dela, devolve `null` ou, pior, dados de **outra** requisição.
- **Certo:** copiar os valores necessários (id do usuário, tenant, correlation id) para variáveis antes de sair do escopo da requisição.
- **Fonte:** [Do not access HttpContext from multiple threads](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#do-not-access-httpcontext-from-multiple-threads)

## Cache

### WEB-05 — Chave de cache inclui tudo o que varia a resposta, inclusive usuário e tenant

- **Sinal no diff:** `IMemoryCache`, `IDistributedCache`, `HybridCache` ou output cache com chave que omite usuário, tenant, idioma ou filtro, sobre dado que depende deles; output cache aplicado a endpoint autenticado com política customizada.
- **Severidade sugerida:** `Bloqueante` se a omissão serve dado de um usuário ou tenant para outro; `Importante` nos demais casos.
- **Não é finding:** política default de output cache, que já não guarda respostas a requisições autenticadas nem respostas com `Set-Cookie`.
- **Fonte:** [Output caching middleware](https://learn.microsoft.com/aspnet/core/performance/caching/output)

### WEB-06 — Cache de dado caro usa proteção contra stampede e expiração (com medição)

- **Sinal no diff:** padrão `TryGetValue` → buscar → `Set` sobre dado caro e muito acessado; entrada de `IMemoryCache` sem expiração; `IMemoryCache` com `SizeLimit` configurado e entrada sem `Size`.
- **Severidade sugerida:** `Sugestão`; `Importante` para entrada sem expiração que cresce com o input.
- **Certo:** `HybridCache.GetOrCreateAsync` `[.NET 9+]`, que garante uma única execução da factory por chave enquanto as demais chamadas aguardam; expiração explícita.
- **Fonte:** [HybridCache library](https://learn.microsoft.com/aspnet/core/performance/caching/hybrid); [Cache in-memory](https://learn.microsoft.com/aspnet/core/performance/caching/memory)

## Logging e serialização

### WEB-07 — Log com template estruturado, não interpolação

- **Sinal no diff:** `_logger.LogInformation($"Pedido {id} criado")` ou concatenação na mensagem (analisador `CA2254`); log em laço de alto volume sem `IsEnabled`.
- **Severidade sugerida:** `Importante`.
- **Por quê:** a string interpolada é montada mesmo com o nível desligado, e o log perde os campos estruturados (`{PedidoId}` deixa de ser consultável no Seq, Elastic ou Application Insights).
- **Certo:** `_logger.LogInformation("Pedido {PedidoId} criado", id)`; em caminho quente, `[LoggerMessage]` (source generator).
- **Fonte:** [High-performance logging in .NET](https://learn.microsoft.com/dotnet/core/extensions/high-performance-logging); [CA2254](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca2254)

### WEB-08 — `JsonSerializerOptions` é criado uma vez e reutilizado

- **Sinal no diff:** `new JsonSerializerOptions { ... }` dentro de método chamado por requisição e passado a `Serialize`/`Deserialize` (analisador `CA1869`).
- **Severidade sugerida:** `Importante`.
- **Por quê:** cada instância nova refaz o cache de metadados de serialização, um custo alto de CPU e memória por chamada.
- **Certo:** instância `static readonly`, ou as opções configuradas no DI (`ConfigureHttpJsonOptions`, `AddJsonOptions`).
- **Fonte:** [CA1869](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1869)

### WEB-09 — Caminho quente evita alocação grande e repetida (com medição)

- **Sinal no diff:** `new byte[n]` grande por requisição; `string` montada por concatenação em laço; resposta grande montada em `MemoryStream` antes de escrever.
- **Severidade sugerida:** `Sugestão`.
- **Certo:** `ArrayPool<byte>.Shared`, `StringBuilder`, escrita direta no `Response.Body`/`PipeWriter`.
- **Por quê:** objeto acima de 85 KB vai para o Large Object Heap, que só é coletado na geração 2.
- **Fonte:** [ASP.NET Core Best Practices — minimize large object allocations](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#minimize-large-object-allocations)
