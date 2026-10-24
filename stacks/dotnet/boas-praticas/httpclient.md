# HttpClient — chamadas HTTP de saída

Critérios `HTTP-XX` verificáveis em diff. Formato, adoção e fontes estão no [`README.md`](README.md).

O `HttpClient` concentra três tipos de defeito que aparecem juntos: desempenho (esgotamento de sockets, DNS desatualizado), resiliência (timeout, retry) e segurança (SSRF, TLS). Por isso os três ficam neste arquivo, e não espalhados por tema.

---

## Ciclo de vida

### HTTP-01 — `HttpClient` não é criado e descartado por requisição

- **Sinal no diff:** `new HttpClient()` (ou `using var client = new HttpClient()`) dentro de método chamado por requisição, handler, job ou loop.
- **Severidade sugerida:** `Importante`; `Bloqueante` em caminho quente.
- **Por quê:** cada instância descartada deixa sockets em `TIME_WAIT`. Sob carga, a aplicação esgota as portas disponíveis.
- **Certo:** `IHttpClientFactory` com cliente tipado ou nomeado (`AddHttpClient<T>`). Fora de DI, um `SocketsHttpHandler` de vida longa compartilhado (ver HTTP-02).

```csharp
builder.Services.AddHttpClient<CatalogoClient>(c =>
    c.BaseAddress = new Uri(builder.Configuration["Catalogo:Url"]!));

public sealed class CatalogoClient(HttpClient http) { /* ... */ }
```

- **Fonte:** [Pool HTTP connections with HttpClientFactory](https://learn.microsoft.com/aspnet/core/fundamentals/best-practices#pool-http-connections-with-httpclientfactory)

### HTTP-02 — `HttpClient` estático ou singleton rotaciona conexões

- **Sinal no diff:** `static readonly HttpClient` ou `HttpClient` registrado como singleton sem `SocketsHttpHandler.PooledConnectionLifetime` configurado.
- **Severidade sugerida:** `Importante`.
- **Por quê:** conexão mantida aberta para sempre não percebe mudança de DNS. A troca de IP de um serviço (failover, deploy blue-green) só chega à aplicação no restart.

```csharp
private static readonly HttpClient Http = new(new SocketsHttpHandler
{
    PooledConnectionLifetime = TimeSpan.FromMinutes(2)
});
```

- **Não é finding:** cliente obtido de `IHttpClientFactory`, que já rotaciona os handlers (default de 2 minutos).
- **Fonte:** [HttpClient guidelines for .NET](https://learn.microsoft.com/dotnet/fundamentals/networking/http/httpclient-guidelines)

### HTTP-03 — Cliente tipado não é capturado por serviço singleton

- **Sinal no diff:** classe registrada com `AddSingleton` recebendo um cliente tipado (ou um `HttpClient` da factory) no construtor e guardando em campo.
- **Severidade sugerida:** `Importante`.
- **Por quê:** o singleton prende o handler para sempre, e a rotação da factory deixa de valer. É o mesmo problema de DNS do HTTP-02, escondido atrás de DI.
- **Certo:** registrar o consumidor como transient ou scoped; ou injetar `IHttpClientFactory` e chamar `CreateClient` a cada uso; ou usar o padrão de HTTP-02.
- **Fonte:** [IHttpClientFactory with .NET — avoid typed clients in singleton services](https://learn.microsoft.com/dotnet/core/extensions/httpclient-factory#avoid-typed-clients-in-singleton-services)

## Timeout e resiliência

### HTTP-04 — Toda chamada externa tem timeout pensado para ela

- **Sinal no diff:** cliente novo sem `Timeout` configurado e sem resilience handler, chamando dependência externa num fluxo síncrono do usuário.
- **Severidade sugerida:** `Importante`.
- **Por quê:** o default do `HttpClient.Timeout` é **100 segundos**. Uma dependência lenta prende a requisição do usuário, as threads e as conexões por esse tempo todo.
- **Não é finding:** cliente com `AddStandardResilienceHandler`, cujo timeout total default é 30 s e o por tentativa é 10 s.
- **Fonte:** [HttpClient.Timeout](https://learn.microsoft.com/dotnet/api/system.net.http.httpclient.timeout)

### HTTP-05 — Um único resilience handler, sem retry em método não idempotente

- **Sinal no diff:** dois ou mais `Add*ResilienceHandler`/`AddPolicyHandler` empilhados no mesmo cliente; `AddStandardResilienceHandler()` num cliente que faz `POST`/`PUT`/`PATCH`/`DELETE` sem `Retry.DisableForUnsafeHttpMethods()` e sem chave de idempotência; retry caseiro em `for`/`while` em volta de `SendAsync`.
- **Severidade sugerida:** `Importante`; `Bloqueante` se o retry pode duplicar efeito financeiro ou de estoque.
- **Por quê:** o handler padrão faz retry em **todos** os métodos HTTP. Um `POST` que criou o registro e caiu por timeout é reenviado, e o registro duplica. Handlers empilhados multiplicam tentativas e timeouts.

```csharp
builder.Services.AddHttpClient<PagamentoClient>()
    .AddStandardResilienceHandler(o => o.Retry.DisableForUnsafeHttpMethods());
```

- **Fonte:** [Build resilient HTTP apps](https://learn.microsoft.com/dotnet/core/resilience/http-resilience)

### HTTP-06 — `CancellationToken` chega até a chamada HTTP

- **Sinal no diff:** `GetAsync(url)`, `SendAsync(req)`, `GetFromJsonAsync<T>(url)` sem o token, dentro de método que recebe `CancellationToken` ou de endpoint (que tem `HttpContext.RequestAborted`).
- **Severidade sugerida:** `Importante`.
- **Por quê:** o usuário desistiu ou o timeout de cima estourou, e a chamada externa segue consumindo conexão até terminar. Regra geral em ASY-03.
- **Fonte:** [Async Guidance — cancellation](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md#cancelling-uncancellable-operations)

## Resposta

### HTTP-07 — Resposta é descartada e tem o status verificado

- **Sinal no diff:** `var resp = await http.SendAsync(...)` sem `using`; leitura do corpo sem checar `IsSuccessStatusCode` nem chamar `EnsureSuccessStatusCode()`.
- **Severidade sugerida:** `Importante`.
- **Por quê:** resposta não descartada e não lida até o fim segura a conexão no pool. Corpo de erro desserializado como sucesso vira objeto vazio que se propaga sem ninguém perceber.
- **Não é finding:** `GetFromJsonAsync`, `GetStringAsync` e afins, que já lançam em status de erro e descartam a resposta.
- **Fonte:** [Make HTTP requests with the HttpClient class](https://learn.microsoft.com/dotnet/fundamentals/networking/http/httpclient)

### HTTP-08 — Payload grande é lido como stream (com medição)

- **Sinal no diff:** `ReadAsStringAsync()` seguido de `JsonSerializer.Deserialize` sobre resposta potencialmente grande (exportação, listagem sem paginação, arquivo).
- **Severidade sugerida:** `Sugestão`.
- **Certo:** `HttpCompletionOption.ResponseHeadersRead` + `ReadFromJsonAsync`/`ReadAsStreamAsync`, ou `GetFromJsonAsAsyncEnumerable<T>` para coleção.
- **Por quê:** string intermediária de vários MB vai para o Large Object Heap e dobra o pico de memória.
- **Fonte:** [HttpClient guidelines for .NET](https://learn.microsoft.com/dotnet/fundamentals/networking/http/httpclient-guidelines)

## Segurança

### HTTP-09 — URL de destino vinda do usuário passa por allowlist (SSRF)

- **Sinal no diff:** `GetAsync`/`SendAsync`/`new HttpRequestMessage` com URL ou host vindo de query, body, header ou registro editável pelo usuário (webhook, "importar de URL", avatar remoto).
- **Severidade sugerida:** `Bloqueante`.
- **Certo:** `Uri.TryCreate` + esquema `https` + host em allowlist exata; `AllowAutoRedirect = false` no handler. Quando a allowlist não basta, validar o IP **resolvido** no `SocketsHttpHandler.ConnectCallback`, rejeitando faixas privadas e `169.254.169.254`.
- **Não é finding:** URL montada só com valores de configuração.
- **Atenção:** `BaseAddress` não protege. Uma string absoluta passada como "caminho relativo" ignora o `BaseAddress` inteiro. `AllowAutoRedirect` é `true` por padrão, então um host permitido pode redirecionar para a rede interna depois da checagem.
- **Fonte:** [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

### HTTP-10 — Validação de certificado TLS nunca é desligada fora de Development

- **Sinal no diff:** `ServerCertificateCustomValidationCallback = (_, _, _, _) => true`, `HttpClientHandler.DangerousAcceptAnyServerCertificateValidator`, `SslProtocols.Tls`/`Tls11` explícitos.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** callback que valida pinning ou uma CA privada específica, ou desligamento sob guarda de `IsDevelopment()`.
- **Fonte:** [TLS best practices with .NET](https://learn.microsoft.com/dotnet/framework/network-programming/tls)
