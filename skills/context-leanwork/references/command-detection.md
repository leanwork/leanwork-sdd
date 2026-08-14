# Detecção de Comandos por Ecossistema

A seção **Comandos** do `CLAUDE.md` é a única que não tem fonte nos artefatos do pipeline SDD — precisa vir de inspeção do repositório.

**Regra central: extrair, nunca inventar.** Um comando inventado (`npm test` num projeto que não tem esse script) faz o agente falhar de forma confusa e mina a confiança no arquivo inteiro. Quando não houver comando, registrar a lacuna explicitamente.

## Ordem de precedência

Quando o projeto tem múltiplas fontes possíveis, seguir esta ordem — a primeira que existir vence:

1. **Task runner dedicado** — `Makefile`, `justfile`, `Taskfile.yml`, `Rakefile`. Se o time criou um, é porque é a interface pretendida.
2. **Scripts do gerenciador de pacotes** — `package.json` (`scripts`), `pyproject.toml` (`[tool.poetry.scripts]`), `Cargo.toml` (aliases em `.cargo/config.toml`)
3. **Comandos nativos do ecossistema** — só quando há evidência de projeto (`.csproj`, `go.mod`), e ainda assim conferindo se a estrutura é padrão
4. **Documentação existente** — `README.md`, `CONTRIBUTING.md`, `docs/`. Menos confiável (envelhece), mas melhor que chutar.

## Tabela por ecossistema

### Node.js / TypeScript

**Fonte:** `package.json` → objeto `scripts`

Extrair as chaves existentes e mapear para as categorias do CLAUDE.md. Nomes comuns, mas **sempre conferir o que existe de fato**:

| Categoria | Chaves típicas |
|-----------|----------------|
| Build | `build`, `compile` |
| Testes | `test`, `test:unit`, `test:e2e`, `test:watch` |
| Rodar local | `dev`, `start`, `serve` |
| Lint / format | `lint`, `format`, `check` |

Detectar o gerenciador pelo lockfile: `package-lock.json` → `npm`, `yarn.lock` → `yarn`, `pnpm-lock.yaml` → `pnpm`, `bun.lockb` → `bun`. **Usar o gerenciador correto no comando** — `npm run dev` num projeto pnpm pode funcionar mas quebra a convenção do time.

### .NET

**Fonte:** `*.sln`, `*.csproj`, `global.json`, `Directory.Build.props`

Comandos nativos são previsíveis, mas conferir a estrutura antes:

- Build: `dotnet build` (ou apontando para o `.sln` quando há vários projetos)
- Testes: `dotnet test` — verificar se existem projetos de teste (`*.Tests.csproj`, `*.IntegrationTests.csproj`); se houver separação, dar os dois comandos
- Rodar: `dotnet run --project src/[Projeto.Api]` — **precisa do caminho real**, extrair da estrutura
- Migrations: `dotnet ef migrations add [Nome] --project [...] --startup-project [...]` — só incluir se houver pacote `Microsoft.EntityFrameworkCore.Design`; os caminhos de `--project`/`--startup-project` são o erro mais comum, extrair da estrutura real
- Watch: `dotnet watch --project [...]`

Conferir `global.json` para a versão do SDK e mencioná-la na seção Stack.

### Python

**Fonte:** `pyproject.toml`, `requirements.txt`, `Makefile`, `tox.ini`, `noxfile.py`

Ecossistema fragmentado — detectar a ferramenta antes:

- `pyproject.toml` com `[tool.poetry]` → `poetry install`, `poetry run pytest`
- `pyproject.toml` com `[tool.uv]` ou `uv.lock` → `uv sync`, `uv run pytest`
- `Pipfile` → `pipenv install`, `pipenv run pytest`
- `requirements.txt` puro → `pip install -r requirements.txt`, `pytest`

Framework web pelo import ou dependência: Django → `python manage.py runserver` / `python manage.py migrate`; FastAPI → `uvicorn app.main:app --reload`; Flask → `flask run`.

### Go

**Fonte:** `go.mod`, `Makefile`

- Build: `go build ./...`
- Testes: `go test ./...` (adicionar `-race` se o projeto usa concorrência de forma central)
- Rodar: `go run ./cmd/[nome]` — extrair o caminho real de `cmd/`
- Lint: `golangci-lint run` — só se houver `.golangci.yml`

### Java / Kotlin

**Fonte:** `pom.xml` (Maven) ou `build.gradle` / `build.gradle.kts` (Gradle)

- Maven: `mvn clean install`, `mvn test`, `mvn spring-boot:run`
- Gradle: `./gradlew build`, `./gradlew test`, `./gradlew bootRun` — preferir o wrapper (`./gradlew`) quando existir

### Rust

**Fonte:** `Cargo.toml`

- Build: `cargo build` / `cargo build --release`
- Testes: `cargo test`
- Rodar: `cargo run`
- Lint: `cargo clippy`

### PHP

**Fonte:** `composer.json` → `scripts`

- Laravel: `php artisan serve`, `php artisan migrate`, `php artisan test`
- Genérico: `composer install`, `./vendor/bin/phpunit`

### Ruby

**Fonte:** `Gemfile`, `Rakefile`

- Rails: `bin/rails server`, `bin/rails db:migrate`, `bin/rails test` ou `bundle exec rspec`
- Genérico: `bundle install`, `bundle exec rake`

## Infraestrutura local

Verificar separadamente — costuma ser pré-requisito para rodar testes de integração:

| Arquivo | Comando |
|---------|---------|
| `docker-compose.yml` / `compose.yaml` | `docker compose up -d` |
| `.devcontainer/` | Mencionar que o projeto tem devcontainer configurado |
| `Tiltfile`, `skaffold.yaml` | `tilt up` / `skaffold dev` |

Quando existir `docker-compose.yml` com banco, incluir o comando na seção Comandos — o agente precisa saber como subir a dependência antes de rodar teste de integração.

## Projetos multi-stack (monorepo)

Quando o repositório tem front e back em stacks diferentes, agrupar por contexto com comentário, não misturar:

```bash
# Backend (.NET) — a partir de src/Api
dotnet build
dotnet test

# Frontend (React) — a partir de src/Web
pnpm install
pnpm dev
```

Incluir o diretório de trabalho quando o comando não roda da raiz. É a causa mais comum de comando "que não funciona".

## Quando não houver comando

Registrar a lacuna com placeholder explícito:

```markdown
# Testes
<!-- TODO: nenhum comando de teste detectado. Não há projeto de teste no repositório
     nem script definido. Confirmar com o time se existe estratégia de teste. -->
```

Isso é informação útil por si só — um projeto sem comando de teste é um achado que vale reportar ao usuário, não algo a esconder atrás de um `dotnet test` chutado.

## Validação opcional

Quando o ambiente permitir execução, a skill **pode** validar os comandos detectados antes de gravar (rodar o de build ou o de lint, que são rápidos e não destrutivos).

Regras:

- Nunca rodar comandos destrutivos ou de longa duração para validar (migrations, deploy, testes E2E completos)
- Sempre pedir confirmação antes de executar qualquer coisa
- Falha na validação vira nota no relatório, não motivo para omitir o comando — o comando pode falhar por ambiente não configurado, não por estar errado
