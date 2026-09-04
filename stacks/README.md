# stacks/ — Exemplos calibrados por stack

O núcleo do plugin (skills, templates, comandos) é stack-agnóstico: pseudocódigo, nomes de padrão genéricos (handler, repositório, validador) e placeholders entre colchetes. Nenhuma skill exige uma stack específica para funcionar — a resolução de stack acontece via proposta arquitetural, `CLAUDE.md` do projeto ou inspeção do repositório (ver `references/stack-detection.md` de cada skill).

Esta pasta guarda **exemplos aplicados**: o mesmo conteúdo didático do núcleo agnóstico, mas com código real de uma stack específica, para quem quer ver a convenção funcionando de ponta a ponta em vez de só em pseudocódigo.

## Convenção

Cada subpasta `stacks/<nome-da-stack>/` espelha, por nome de arquivo, o material agnóstico correspondente em `templates/` ou `skills/*/references/`. Por exemplo:

| Arquivo agnóstico | Versão calibrada |
|---|---|
| `skills/planner-leanwork/references/task-examples.md` | `stacks/dotnet/task-examples.md` |
| `skills/architect-leanwork/references/c4-mermaid-templates.md` (Nível 3) | `stacks/dotnet/c4-component-example.md` |
| pipeline completo (5 fases) | `stacks/dotnet/pipeline-example.md` |

Um arquivo agnóstico que tem versão calibrada inclui um ponteiro explícito para ela (`${CLAUDE_PLUGIN_ROOT}/stacks/<nome>/...`). O inverso também vale: todo arquivo em `stacks/` referencia de volta o material agnóstico que ele exemplifica.

## Stacks disponíveis

- **`dotnet/`** — .NET 8, EF Core, MediatR, FluentValidation, xUnit, Serilog. É a stack usada nos exemplos históricos do plugin (por isso é a mais completa), não uma recomendação.

## Adicionando uma nova stack

Para calibrar o plugin em outra stack (Node.js, Python, Java, etc.), criar `stacks/<nome>/` com os mesmos arquivos que fizerem sentido, seguindo a mesma estrutura didática do agnóstico correspondente — só o código muda, os IDs (`RN-XX`, `CA-XX`, `T-XX`, `ADR-XX`) e a lógica narrativa do exemplo (domínio fictício, cenário de negócio) permanecem os mesmos para facilitar comparação.
