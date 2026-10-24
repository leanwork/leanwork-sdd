# Boas práticas .NET — segurança e desempenho

Catálogo de critérios verificáveis em diff para projetos .NET / ASP.NET Core. Complementa o **piso de segurança** do reviewer (`skills/reviewer-leanwork/references/review-checklist.md`, eixo 5), que é stack-agnóstico e cobre só segredo hardcoded e PII em log.

## Como entra no pipeline

O reviewer não cobra preferência, cobra o que o projeto declarou (eixo 5). Por isso este catálogo **não vale sozinho**: um item só vira critério de review quando o projeto o adota no `CLAUDE.md`.

A adoção é a linha `Catálogo:` na seção `Segurança e desempenho` do `CLAUDE.md`, com formato fixo:

```markdown
## Segurança e desempenho

- Catálogo: `stacks/dotnet/boas-praticas` (Leanwork SDD) — exceto EF-12, WEB-06
```

Sem exclusões, escrever `exceto nenhum`. A skill `context-leanwork` oferece o catálogo quando detecta um projeto .NET e grava a linha se o time aceitar; dá para escrever à mão no mesmo formato.

Com a linha presente:

- o `/leanwork-execute` lê o README e os arquivos das áreas que a tarefa toca antes de implementar;
- a review cobra os itens não excluídos no eixo 5, citando o código no finding (`R-03 — viola EF-01: N+1 em ...`).

Item cuja área o projeto não usa (EF-XX num projeto com Dapper) não precisa de exceção, porque só se aplica quando o diff toca a área.

## Arquivos

| Arquivo | Prefixo | Escopo |
|---|---|---|
| [`seguranca-owasp.md`](seguranca-owasp.md) | `SEC-` | ASP.NET Core organizado pelo OWASP Top 10:2025 |
| [`httpclient.md`](httpclient.md) | `HTTP-` | Chamadas HTTP de saída: ciclo de vida, timeout, resiliência, SSRF, TLS |
| [`efcore.md`](efcore.md) | `EF-` | Acesso a dados com EF Core: N+1, rastreamento, paginação, bulk, ciclo de vida do contexto |
| [`async.md`](async.md) | `ASY-` | async/await, cancelamento, trabalho em background, concorrência |
| [`aspnetcore-desempenho.md`](aspnetcore-desempenho.md) | `WEB-` | Pipeline HTTP: paginação, corpo da requisição, cache, logging, serialização |

Os códigos (`SEC-01`, `EF-04`...) são estáveis: um item removido deixa o número vago, não renumera. Eles **não** são IDs do pipeline (`RN`, `CA`, `ADR`, `UI`, `T`, `R`) e não entram nos campos do plano.

## Formato de cada item

- **Regra** — uma frase, no imperativo, que dá para conferir lendo o diff
- **Sinal no diff** — o que procurar (API, padrão de código)
- **Severidade sugerida** — na escala do reviewer (`Bloqueante`, `Importante`, `Sugestão`); o projeto pode recalibrar ao adotar
- **Não é finding** — o falso positivo conhecido daquele item, quando há
- **Fonte** — documentação oficial de onde a regra vem

Itens de desempenho marcados com **(com medição)** só valem com evidência de gargalo: um profiler, um teste de carga ou um atributo de qualidade priorizado no PRD ou na arquitetura. Sem isso são otimização prematura, e a regra "não otimizar prematuramente" do reviewer continua valendo.

## Versão de referência

A base é **.NET 8** (a stack de `stacks/dotnet/`). Itens que exigem versão maior trazem a marca `[.NET 9+]` ou `[EF Core 7+]`. O .NET 8 e o .NET 9 perdem suporte em **2026-11-10**; o .NET 10 (LTS) vai até 2028-11. Conferir em <https://dotnet.microsoft.com/platform/support/policy> antes de citar datas.

## Critério de inclusão

O catálogo **não** tenta reunir toda boa prática publicada para .NET. Entra o que atende três condições:

1. Tem fonte oficial (Microsoft Learn, OWASP, guias da equipe do ASP.NET Core).
2. É **verificável no diff** de uma tarefa. "Faça threat modeling" não é; "não use `FromSqlRaw` com string interpolada" é.
3. O erro é objetivo, não preferência de estilo.

## Fontes

- OWASP Top 10:2025 — <https://top10.owasp.org/2025>
- ASP.NET Core Best Practices — <https://learn.microsoft.com/aspnet/core/fundamentals/best-practices>
- Segurança no ASP.NET Core — <https://learn.microsoft.com/aspnet/core/security/>
- IHttpClientFactory — <https://learn.microsoft.com/aspnet/core/fundamentals/http-requests> e <https://learn.microsoft.com/dotnet/fundamentals/networking/http/httpclient-guidelines>
- Resiliência HTTP — <https://learn.microsoft.com/dotnet/core/resilience/http-resilience>
- EF Core Performance — <https://learn.microsoft.com/ef/core/performance/>
- Cache (HybridCache, output cache) — <https://learn.microsoft.com/aspnet/core/performance/caching/overview>
- Rate limiting — <https://learn.microsoft.com/aspnet/core/performance/rate-limit>
- Async Guidance e ASP.NET Core Guidance, de David Fowler — <https://github.com/davidfowl/AspNetCoreDiagnosticScenarios>

**Reprodução, adaptação, autoral.** As regras e os exemplos de código são **adaptação** das fontes acima: traduzidos, condensados e reescritos no formato de critério de review. As notas de "Não é finding" de `seguranca-owasp.md` são **adaptação** do catálogo de falsos positivos da skill local `aspnet-owasp-audit`, conferido contra a documentação oficial. São **autorais** do Leanwork SDD: a seleção dos itens, a severidade sugerida, a marca "(com medição)" e a amarração com os eixos do reviewer.

## Divergências e lacunas

**Divergências deliberadas:**

- O OWASP Top 10 é um documento de conscientização sobre riscos, não um checklist. O mapeamento por categoria aqui serve para organizar, não para afirmar cobertura do Top 10. Para verificação de requisitos, a referência do OWASP é o ASVS, que este catálogo não reproduz.
- A severidade é calibrada para **review de tarefa**, não para laudo de auditoria. Um header de segurança ausente é `Sugestão` aqui e seria "Low/Medium" num pentest.
- `stacks/README.md` diz que cada arquivo de `stacks/` espelha um material agnóstico. Este catálogo espelha só o piso de segurança do eixo 5, e a maior parte dele não tem contraparte agnóstica: é conteúdo próprio da stack.

**Lacunas conhecidas:**

- Não cobre Blazor WebAssembly, gRPC, SignalR, Orleans, MAUI nem workers fora do ASP.NET Core.
- Não cobre infraestrutura (Kubernetes, gateway, WAF), observabilidade nem configuração de nuvem.
- Não substitui SAST, DAST, varredura de dependências no CI nem auditoria de segurança dedicada. Review de diff não enxerga o que a tarefa não tocou.
- Os itens "(com medição)" dependem de o projeto ter como medir; o catálogo não ensina profiling nem teste de carga.
