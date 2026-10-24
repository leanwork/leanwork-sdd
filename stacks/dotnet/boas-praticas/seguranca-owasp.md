# Segurança em ASP.NET Core — por categoria do OWASP Top 10:2025

Critérios `SEC-XX` verificáveis em diff. Formato, adoção e fontes estão no [`README.md`](README.md).

Muitos defaults do ASP.NET Core moderno já são seguros: Razor escapa HTML, o EF Core parametriza LINQ, cookies nascem `HttpOnly`. Por isso o finding quase sempre é **um desvio explícito do caminho seguro**, não a ausência de uma configuração. Antes de registrar, ler o "Não é finding" do item e conferir o `<TargetFramework>`.

## Sumário

| Categoria OWASP 2025 | Itens |
|---|---|
| A01 Broken Access Control | SEC-01 a SEC-04 |
| A02 Security Misconfiguration | SEC-05 a SEC-11 |
| A03 Software Supply Chain Failures | SEC-12 |
| A04 Cryptographic Failures | SEC-13 |
| A05 Injection | SEC-14 a SEC-18 |
| A06 Insecure Design | SEC-19 |
| A07 Authentication Failures | SEC-20, SEC-21 |
| A08 Software or Data Integrity Failures | SEC-22 |
| A09 Security Logging and Alerting Failures | SEC-23 |
| A10 Mishandling of Exceptional Conditions | SEC-24 |

Itens de segurança de outros arquivos: SSRF e TLS em [`httpclient.md`](httpclient.md) (HTTP-09, HTTP-10); chave de cache por usuário em [`aspnetcore-desempenho.md`](aspnetcore-desempenho.md) (WEB-05).

---

## A01 — Broken Access Control

### SEC-01 — A aplicação é fechada por padrão, e cada exceção anônima é explícita

- **Sinal no diff:** endpoint novo (`Map*`, action de controller) num projeto sem `FallbackPolicy`, sem `RequireAuthorization()` no grupo e sem filtro global; `[AllowAnonymous]` ou `.AllowAnonymous()` novo.
- **Severidade sugerida:** `Bloqueante` (endpoint de dados aberto); `Importante` (`[AllowAnonymous]` novo sem justificativa no PR).
- **Não é finding:** controller sem `[Authorize]` quando há `FallbackPolicy`, `MapGroup(...).RequireAuthorization()`, `AuthorizeFilter` global ou controller base com `[Authorize]`. `DefaultPolicy` (o que `[Authorize]` sem parâmetro resolve) é diferente de `FallbackPolicy` (o que vale quando não há metadado nenhum).
- **Atenção:** `UseStaticFiles()` responde antes do roteamento e fica fora do `FallbackPolicy`. `MapStaticAssets()` `[.NET 9+]` cria endpoints e é coberto.

```csharp
builder.Services.AddAuthorization(o =>
    o.FallbackPolicy = new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build());
```

- **Fonte:** [Require authenticated users](https://learn.microsoft.com/aspnet/core/security/authorization/secure-data#require-authenticated-users)

### SEC-02 — Recurso buscado por id é filtrado pelo dono ou pelo tenant

- **Sinal no diff:** `FindAsync(id)`, `FirstOrDefaultAsync(x => x.Id == id)` com `id` vindo da rota, sem filtro de `UserId`/`TenantId` e sem `IAuthorizationService.AuthorizeAsync(User, recurso, ...)` depois.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** filtro global de tenant (`HasQueryFilter`) já aplicado à entidade. Conferir se a query não usa `IgnoreQueryFilters()`.
- **Nota:** para recurso de outro dono, responder `404` em vez de `403` evita enumeração.

```csharp
// errado: qualquer usuário autenticado lê o pedido de qualquer outro
var pedido = await db.Pedidos.FirstOrDefaultAsync(p => p.Id == id, ct);
// certo
var pedido = await db.Pedidos.FirstOrDefaultAsync(p => p.Id == id && p.ClienteId == clienteAtual, ct);
```

- **Fonte:** [Resource-based authorization](https://learn.microsoft.com/aspnet/core/security/authorization/resourcebased)

### SEC-03 — Entidade do EF não é alvo de model binding

- **Sinal no diff:** parâmetro de action, `[FromBody]` ou `[BindProperty]` tipado com uma entidade que tem `DbSet<T>`; `_context.Update(entidadeVindaDoRequest)`; `[Bind(Exclude = ...)]`.
- **Severidade sugerida:** `Bloqueante` se a entidade tem campo sensível (`Role`, `IsAdmin`, `OwnerId`, `TenantId`, `Preco`, `Saldo`, `Status`); `Importante` nos demais casos.
- **Não é finding:** DTO como tipo distinto (`record CriarPedidoRequest(...)`). DTO que **herda** da entidade não protege. `[Bind("a,b")]` (lista de inclusão) protege; `Exclude` não, porque campo novo passa a ser vinculável.
- **Fonte:** [Overposting](https://learn.microsoft.com/aspnet/core/data/ef-rp/crud#overposting)

### SEC-04 — Redirect com destino vindo do usuário só para URL local

- **Sinal no diff:** `Redirect(returnUrl)`, `Results.Redirect(x)` com valor de query, form ou rota.
- **Severidade sugerida:** `Importante`.
- **Não é finding:** `LocalRedirect`, `Results.LocalRedirect`, `Url.IsLocalUrl` antes do redirect, `RedirectToAction`/`RedirectToPage`.
- **Fonte:** [Prevent open redirect attacks](https://learn.microsoft.com/aspnet/core/security/preventing-open-redirects)

## A02 — Security Misconfiguration

### SEC-05 — CORS com lista exata de origens

- **Sinal no diff:** `SetIsOriginAllowed(_ => true)`, `SetIsOriginAllowed(o => o.EndsWith(...))` ou `Contains`, sobretudo com `AllowCredentials()`; `AllowAnyOrigin()` em API que usa cookie.
- **Severidade sugerida:** `Bloqueante` (origem refletida com credencial); `Importante` (`AllowAnyOrigin` sem credencial em API não pública).
- **Não é finding:** `AllowAnyOrigin().AllowCredentials()` não é falha silenciosa: o ASP.NET Core lança exceção ao aplicar a política. É bug, não vulnerabilidade.
- **Atenção:** `WithOrigins("https://app.x.com/")` com barra final nunca casa, porque o header `Origin` não traz barra.
- **Fonte:** [Enable CORS](https://learn.microsoft.com/aspnet/core/security/cors)

### SEC-06 — Ordem do middleware preserva autenticação, autorização e CORS

- **Sinal no diff:** mudança em `Program.cs` com `UseAuthorization()` antes de `UseAuthentication()`, `UseCors()` fora do intervalo entre `UseRouting()` e `UseAuthorization()`, `UseExceptionHandler` depois de middlewares que lançam, `UseAntiforgery()` antes de autenticação e autorização.
- **Severidade sugerida:** `Bloqueante`.
- **Fonte:** [Middleware order](https://learn.microsoft.com/aspnet/core/fundamentals/middleware/#middleware-order)

### SEC-07 — Página de exceção detalhada, Swagger e endpoints de diagnóstico só em Development

- **Sinal no diff:** `UseDeveloperExceptionPage()`, `UseSwagger()`/`UseSwaggerUI()`, `MapOpenApi()`, endpoint que devolve `IConfiguration` ou variáveis de ambiente, sem guarda de `app.Environment.IsDevelopment()`; `ASPNETCORE_ENVIRONMENT=Development` em Dockerfile ou manifesto de produção.
- **Severidade sugerida:** `Importante`; `Bloqueante` se expõe configuração ou segredo.
- **Fonte:** [Handle errors in ASP.NET Core](https://learn.microsoft.com/aspnet/core/fundamentals/error-handling)

### SEC-08 — Cookie de autenticação sem downgrade dos defaults

- **Sinal no diff:** `Cookie.HttpOnly = false`, `Cookie.SecurePolicy = CookieSecurePolicy.None`, `Cookie.SameSite = SameSiteMode.None` sem motivo cross-site documentado.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** ausência de configuração explícita. Os defaults (`HttpOnly`, `SameSite=Lax`) já são seguros. O `ExpireTimeSpan` default de 14 dias é longo para aplicação sensível, mas é recomendação, não defeito.
- **Fonte:** [Cookie authentication](https://learn.microsoft.com/aspnet/core/security/authentication/cookie)

### SEC-09 — Antiforgery em toda ação que muda estado quando a autenticação é por cookie

- **Sinal no diff:** `POST`/`PUT`/`PATCH`/`DELETE` novo em app com autenticação por cookie, sem `AutoValidateAntiforgeryTokenAttribute` global nem `[ValidateAntiForgeryToken]`; `[IgnoreAntiforgeryToken]` novo; ação que muda estado exposta via `GET`.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** API autenticada só por Bearer token. O navegador não anexa o header `Authorization` sozinho, então não há CSRF. Razor Pages valida POST automaticamente.
- **Fonte:** [Prevent CSRF attacks](https://learn.microsoft.com/aspnet/core/security/anti-request-forgery)

### SEC-10 — Chaves de Data Protection persistidas, compartilhadas e protegidas em repouso

- **Sinal no diff:** app em container ou com mais de uma instância sem `AddDataProtection().PersistKeysTo*`; `PersistKeysTo*` sem `ProtectKeysWith*`; storage compartilhado entre apps sem `SetApplicationName`.
- **Severidade sugerida:** `Importante`; `Bloqueante` se as chaves ficam em texto claro num volume compartilhado.
- **Por quê:** chave efêmera derruba sessões a cada restart, e o time costuma "resolver" desligando o antiforgery. Chave em claro permite forjar cookie de qualquer usuário.
- **Fonte:** [Configure Data Protection](https://learn.microsoft.com/aspnet/core/security/data-protection/configuration/overview)

### SEC-11 — HTTPS, HSTS e headers de segurança em app que renderiza HTML

- **Sinal no diff:** app exposta sem `UseHttpsRedirection()` e `UseHsts()`; app com Razor, MVC ou Blazor Server sem `Content-Security-Policy`, `X-Content-Type-Options: nosniff` e `frame-ancestors`/`X-Frame-Options`.
- **Severidade sugerida:** `Sugestão` em API pura; `Importante` em app que renderiza HTML.
- **Não é finding:** TLS e HSTS terminados no proxy ou no ingress, quando o manifesto de deploy mostra isso.
- **Fonte:** [Enforce HTTPS](https://learn.microsoft.com/aspnet/core/security/enforcing-ssl); [OWASP HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html)

## A03 — Software Supply Chain Failures

### SEC-12 — Dependência nova sem vulnerabilidade conhecida, e auditoria do NuGet ligada

- **Sinal no diff:** `PackageReference` novo ou atualizado com aviso de auditoria (`NU1901` a `NU1904`) no build; `<NuGetAudit>false</NuGetAudit>` ou `NoWarn` de `NU190x` sem justificativa; `<NuGetAuditSuppress>` sem comentário de motivo; `<TargetFramework>` fora de suporte.
- **Severidade sugerida:** `Bloqueante` para advisory alto ou crítico em pacote alcançável; `Importante` para os demais e para auditoria desligada.
- **Nota:** desde o SDK do .NET 8 (8.0.100) a auditoria roda no `restore`. Até `net9.0` o default audita só dependências diretas (`NuGetAuditMode=direct`); projeto que mira `net10.0` audita também as transitivas (`all`). Em `net8.0`/`net9.0`, declarar `<NuGetAuditMode>all</NuGetAuditMode>` para ter o mesmo alcance.
- **Fonte:** [Auditing package dependencies](https://learn.microsoft.com/nuget/concepts/auditing-packages)

## A04 — Cryptographic Failures

### SEC-13 — Senha, token e cifra só com primitivas atuais

- **Sinal no diff:** `MD5`, `SHA1` para senha ou integridade; hash de senha caseiro; `new Random()` para gerar token, código ou senha; `CipherMode.ECB`; IV fixo ou zerado; chave de cifra no código; `Rfc2898DeriveBytes` com o construtor legado (SHA-1, poucas iterações).
- **Severidade sugerida:** `Bloqueante`.
- **Certo:** `PasswordHasher<T>` do Identity, ou Argon2id; `RandomNumberGenerator.GetBytes(32)` para token; `AesGcm` com nonce aleatório.
- **Não é finding:** `MD5`/`SHA1` em uso que não é de segurança (ETag, chave de cache, deduplicação), quando o contexto deixa isso claro.
- **Fonte:** [.NET cryptography model](https://learn.microsoft.com/dotnet/standard/security/cryptography-model); [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

Segredo hardcoded e PII em log já estão no piso de segurança do reviewer e não se repetem aqui.

## A05 — Injection

### SEC-14 — SQL nunca é montado com valor concatenado ou interpolado antes do método

- **Sinal no diff:** `FromSqlRaw`, `ExecuteSqlRaw`, `SqlQueryRaw` recebendo `$"..."` ou `+`; `SqlCommand`/`DbCommand.CommandText` concatenado; Dapper com `+` ou `$""` montando a string; `ORDER BY {coluna}` com coluna vinda do request.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** `FromSql($"... {valor}")`, `ExecuteSql($"...")` e `SqlQuery<T>($"...")` `[EF Core 7+]` viram `DbParameter`. `FromSqlRaw("... {0}", valor)` também. `@nome` do Dapper é parâmetro. Identificador dinâmico (coluna, tabela) é aceitável se vier de allowlist, `nameof` ou constante.
- **Atenção:** em EF6 (pacote `EntityFramework`), `Database.SqlQuery<T>(string, params object[])` é a forma crua. O nome colide com a forma segura do EF Core.
- **Fonte:** [SQL queries — EF Core](https://learn.microsoft.com/ef/core/querying/sql-queries)

### SEC-15 — Processo externo sem shell e com argumentos separados

- **Sinal no diff:** `Process.Start` com `cmd.exe`, `/bin/sh`, `bash`, `powershell` e dado do usuário em `Arguments`; `UseShellExecute = true`; `FileName` vindo de input; `Arguments` concatenado.
- **Severidade sugerida:** `Bloqueante`.
- **Certo:** `ProcessStartInfo.ArgumentList.Add(...)`, um argumento por chamada, sem shell.
- **Não é finding:** `Process.Start` com binário e argumentos constantes. `UseShellExecute` já é `false` por padrão no .NET Core e no .NET 5+.
- **Fonte:** [ProcessStartInfo.ArgumentList](https://learn.microsoft.com/dotnet/api/system.diagnostics.processstartinfo.argumentlist)

### SEC-16 — Caminho de arquivo nunca deriva de nome enviado pelo usuário

- **Sinal no diff:** `Path.Combine(raiz, file.FileName)`, `PhysicalFile(Path.Combine(raiz, entrada))`, `ZipArchiveEntry.ExtractToFile` sem validar contenção; upload sem limite de tamanho (`[RequestSizeLimit]`) e sem allowlist de extensão.
- **Severidade sugerida:** `Bloqueante` (traversal); `Importante` (falta de limite ou de allowlist).
- **Certo:** nome gerado pelo servidor (`Path.GetRandomFileName()`); `IFormFile.FileName` só para exibição, com HTML-encode; quando o nome precisa ser preservado, `Path.GetFullPath` + `StartsWith` da base com separador no fim.
- **Não é finding:** `Path.Combine(dir, Path.GetFileName(entrada))`, que remove os componentes de diretório.
- **Fonte:** [Upload files in ASP.NET Core — security considerations](https://learn.microsoft.com/aspnet/core/mvc/models/file-uploads#security-considerations)

### SEC-17 — HTML vindo de dado não é renderizado cru

- **Sinal no diff:** `@Html.Raw(...)`, `new HtmlString(...)`, `(MarkupString)` ou `AddMarkupContent` com dado do usuário; `JavaScriptEncoder.UnsafeRelaxedJsonEscaping`; `var x = '@Model.Valor';` dentro de `<script>`; `innerHTML` em JS do `wwwroot`.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** `@Model.Valor` (escapado automaticamente); `MarkupString` sobre conteúdo passado por sanitizador (`HtmlSanitizer`); `@Html.Raw(JsonSerializer.Serialize(x))` com opções default do System.Text.Json (frágil, mas o encoder default escapa `<`).
- **Fonte:** [Prevent XSS in ASP.NET Core](https://learn.microsoft.com/aspnet/core/security/cross-site-scripting)

### SEC-18 — Parser XML não reabilita DTD nem resolução externa

- **Sinal no diff:** `DtdProcessing = DtdProcessing.Parse`, `XmlResolver = new XmlUrlResolver()`, `new XmlTextReader(...)`, `XmlSerializer.Deserialize(stream)` direto sobre input externo.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** `XmlDocument.LoadXml` e `XmlReader.Create` com defaults no .NET Core e no .NET 5+, que já proíbem DTD e não resolvem entidade externa.
- **Fonte:** [OWASP XXE Prevention Cheat Sheet — .NET](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html#net)

## A06 — Insecure Design

### SEC-19 — Endpoint sensível a abuso tem limite de taxa

- **Sinal no diff:** endpoint novo de login, recuperação de senha, envio de OTP, cadastro público ou busca cara sem `RequireRateLimiting(...)`/`[EnableRateLimiting]`, em projeto que usa `AddRateLimiter`.
- **Severidade sugerida:** `Importante`.
- **Atenção:** a partição precisa identificar o cliente (usuário autenticado ou IP real atrás do proxy, com `UseForwardedHeaders` configurado). Partição única para todo mundo vira negação de serviço autoinfligida. `UseRateLimiter()` vem depois de `UseRouting()` quando a política é por endpoint.
- **Não é finding:** limite aplicado no gateway ou no WAF, quando o projeto declara isso.
- **Fonte:** [Rate limiting middleware](https://learn.microsoft.com/aspnet/core/performance/rate-limit)

## A07 — Authentication Failures

### SEC-20 — Validação de JWT não é afrouxada

- **Sinal no diff:** `ValidateIssuer = false`, `ValidateAudience = false`, `ValidateLifetime = false`, `RequireSignedTokens = false`, `SignatureValidator` que devolve o token sem validar, `RequireHttpsMetadata = false` fora de Development, token emitido com expiração longa (dias) num fluxo de login web.
- **Severidade sugerida:** `Bloqueante` (`RequireSignedTokens = false`, `SignatureValidator`, `ValidateLifetime = false`); `Importante` (issuer, audience, expiração longa).
- **Não é finding:** `ValidateIssuerSigningKey = false`. O default já é `false`, e a propriedade não controla a verificação de assinatura; quem controla é `RequireSignedTokens` (default `true`) com a resolução da chave. `ClockSkew` default de 5 minutos.
- **Fonte:** [Configure JWT bearer authentication](https://learn.microsoft.com/aspnet/core/security/authentication/configure-jwt-bearer-authentication)

### SEC-21 — Falha de login não revela se a conta existe

- **Sinal no diff:** mensagens distintas para "usuário não encontrado" e "senha incorreta"; caminho de código que retorna antes de verificar a senha quando o usuário não existe (diferença de tempo); recuperação de senha que responde diferente para e-mail cadastrado e não cadastrado.
- **Severidade sugerida:** `Importante`.
- **Fonte:** [OWASP Authentication Cheat Sheet — authentication responses](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#authentication-and-error-messages)

## A08 — Software or Data Integrity Failures

### SEC-22 — Desserialização não aceita tipo vindo do payload

- **Sinal no diff:** `BinaryFormatter`, `SoapFormatter`, `NetDataContractSerializer`, `LosFormatter`; `TypeNameHandling` diferente de `None` no Newtonsoft (inclusive via `[JsonProperty(TypeNameHandling = ...)]`); pacote `System.Runtime.Serialization.Formatters` adicionado; `EnableUnsafeBinaryFormatterSerialization`.
- **Severidade sugerida:** `Bloqueante`.
- **Não é finding:** System.Text.Json com `[JsonDerivedType]` `[.NET 7+]`, que é allowlist fechada; `DataContractSerializer` (sem o "Net"). No .NET 9+, `BinaryFormatter` sem o pacote de compatibilidade lança exceção em runtime: é código morto, não RCE.
- **Fonte:** [BinaryFormatter security guide](https://learn.microsoft.com/dotnet/standard/serialization/binaryformatter-security-guide)

## A09 — Security Logging and Alerting Failures

### SEC-23 — Eventos de segurança são registrados, e valor do usuário não forja linha de log

- **Sinal no diff:** fluxo novo de autenticação, autorização, troca de privilégio ou alteração de dado sensível sem log estruturado de quem, quando e o quê; mensagem de log montada por concatenação ou interpolação com valor do request.
- **Severidade sugerida:** `Sugestão`; `Importante` se o projeto declara requisito de auditoria (LGPD, regulação).
- **Nota:** template estruturado (`_logger.LogWarning("Falha de login para {UserId}", id)`) resolve a interpolação e também o desempenho (ver WEB-07). PII e segredo em log já estão no piso do reviewer.
- **Fonte:** [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

## A10 — Mishandling of Exceptional Conditions

### SEC-24 — Erro falha fechado e não vaza detalhe para o cliente

- **Sinal no diff:** `catch { return true; }` ou equivalente numa checagem de permissão, assinatura ou limite; `catch (Exception) { }` vazio; `ex.ToString()`, `ex.Message` ou `ex.StackTrace` no corpo da resposta.
- **Severidade sugerida:** `Bloqueante` (fail-open em controle de segurança, vazamento de detalhe interno); `Importante` (exceção engolida).
- **Certo:** `UseExceptionHandler` com `AddProblemDetails()`, detalhe só no log, id de correlação na resposta.
- **Fonte:** [Handle errors in ASP.NET Core APIs](https://learn.microsoft.com/aspnet/core/web-api/handle-errors)
