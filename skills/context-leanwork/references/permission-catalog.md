# Catálogo de Permissões — `.claude/settings.json`

Receitas de `allow` / `ask` / `deny` por ecossistema, usadas pela skill `context-leanwork` ao gerar o `.claude/settings.json`.

## Como as regras funcionam

- **Formato:** `Tool` ou `Tool(especificador)`
- **Precedência:** `deny` → `ask` → `allow`. A primeira regra que casar decide, independente de quão específica ela seja.
- **Escopos se somam:** as listas de `.claude/settings.json` (projeto), `.claude/settings.local.json` (pessoal) e `~/.claude/settings.json` (usuário) são combinadas. Um `deny` em qualquer escopo não pode ser afrouxado por um `allow` em outro.
- **`deny` não aceita exceção.** Não existe "negar tudo menos X" — para isso, use `allow` específico com `defaultMode` restritivo.
- **Sintaxe por tool:** `Bash` usa wildcard com `:` para prefixo de comando; `Read` e `Edit` usam caminhos estilo gitignore; `WebFetch` usa `domain:`.

## Onde cada coisa mora

| Arquivo | Escopo | Versionado | Uso |
|---|---|---|---|
| `.claude/settings.json` | Projeto | **Sim** — viaja com o repo | Política do time |
| `.claude/settings.local.json` | Projeto, pessoal | Não (gitignore) | Overrides da máquina do dev |
| `~/.claude/settings.json` | Usuário | Não | Preferências pessoais em todos os projetos |

A skill escreve **apenas** o `.claude/settings.json`. Preferências individuais são do dev, não do projeto.

---

## Deny universal — vale para qualquer stack

Esta lista é o núcleo de segurança e entra em **todo** projeto, independente de tecnologia. São arquivos que carregam segredo em texto puro.

```jsonc
"deny": [
  // Variáveis de ambiente
  "Read(**/.env)",
  "Read(**/.env.*)",

  // Chaves e certificados
  "Read(**/*.pem)",
  "Read(**/*.key)",
  "Read(**/*.pfx)",
  "Read(**/*.p12)",
  "Read(**/id_rsa*)",
  "Read(**/id_ed25519*)",

  // Credenciais de cloud e infra
  "Read(**/.aws/credentials)",
  "Read(**/.kube/config)",
  "Read(**/*.kubeconfig)",
  "Read(**/terraform.tfstate)",
  "Read(**/terraform.tfstate.*)",
  "Read(**/*.tfvars)",

  // Tokens de registry
  "Read(**/.npmrc)",
  "Read(**/.pypirc)",
  "Read(**/.docker/config.json)",

  // Comandos destrutivos
  "Bash(rm -rf:*)",
  "Bash(git push --force:*)",
  "Bash(git reset --hard:*)"
]
```

**Sobre `terraform.tfstate`:** costuma ser esquecido e é dos piores — guarda senha de banco, chave de API e token em texto puro. Sempre incluir quando o projeto tem Terraform.

**Sobre `.npmrc` e `.pypirc`:** carregam token de publicação em registry. Ler é o primeiro passo para vazar.

---

## .NET

```jsonc
"allow": [
  "Bash(dotnet build:*)",
  "Bash(dotnet test:*)",
  "Bash(dotnet run:*)",
  "Bash(dotnet restore:*)",
  "Bash(dotnet format:*)",
  "Bash(dotnet ef migrations list:*)",
  "Bash(dotnet ef migrations script:*)"
],
"ask": [
  "Bash(dotnet add package:*)",
  "Bash(dotnet ef migrations add:*)",
  "Bash(dotnet ef database update:*)",
  "Bash(dotnet nuget push:*)"
],
"deny": [
  "Read(**/appsettings.Production.json)",
  "Read(**/appsettings.*.Production.json)",
  "Read(**/secrets.json)",
  "Bash(dotnet ef database drop:*)"
]
```

**Notas de calibragem:**
- `dotnet ef migrations script` e `list` são leitura — seguros no `allow`. `add` e `database update` alteram estado — vão para `ask`.
- `dotnet ef database drop` é destrutivo e irreversível: `deny`, não `ask`.
- `secrets.json` é o User Secrets do .NET, que vive fora do repo mas é lido pela aplicação.
- `dotnet add package` no `ask` protege contra supply chain — instalação silenciosa de pacote é vetor real.

## Node.js / TypeScript

```jsonc
"allow": [
  "Bash(npm run build:*)",
  "Bash(npm run test:*)",
  "Bash(npm run lint:*)",
  "Bash(npm run dev:*)",
  "Bash(npm ci:*)",
  "Bash(npx tsc:*)"
],
"ask": [
  "Bash(npm install:*)",
  "Bash(npm i:*)",
  "Bash(npx:*)"
],
"deny": [
  "Bash(npm publish:*)",
  "Read(**/.npmrc)"
]
```

**Adaptar ao gerenciador detectado pelo lockfile:** `pnpm-lock.yaml` → trocar `npm` por `pnpm`; `yarn.lock` → `yarn`; `bun.lockb` → `bun`. Usar o gerenciador errado gera regra que nunca casa.

**Sobre `npx` no `ask`:** `npx` executa pacote arbitrário da internet. Deveria sempre passar por confirmação, com exceção de binários específicos já conhecidos do projeto (que podem ir no `allow` nomeados).

## Python

```jsonc
"allow": [
  "Bash(pytest:*)",
  "Bash(ruff:*)",
  "Bash(black:*)",
  "Bash(mypy:*)",
  "Bash(python -m pytest:*)"
],
"ask": [
  "Bash(pip install:*)",
  "Bash(poetry add:*)",
  "Bash(uv add:*)",
  "Bash(alembic upgrade:*)",
  "Bash(python manage.py migrate:*)"
],
"deny": [
  "Bash(twine upload:*)",
  "Read(**/.pypirc)",
  "Bash(python manage.py flush:*)"
]
```

Adaptar ao gerenciador detectado: `poetry.lock` → poetry; `uv.lock` → uv; `Pipfile.lock` → pipenv.

## Go

```jsonc
"allow": [
  "Bash(go build:*)",
  "Bash(go test:*)",
  "Bash(go run:*)",
  "Bash(go vet:*)",
  "Bash(go fmt:*)",
  "Bash(golangci-lint run:*)"
],
"ask": [
  "Bash(go get:*)",
  "Bash(go install:*)"
]
```

## Java / Kotlin

```jsonc
"allow": [
  "Bash(./gradlew build:*)",
  "Bash(./gradlew test:*)",
  "Bash(mvn compile:*)",
  "Bash(mvn test:*)"
],
"ask": [
  "Bash(./gradlew publish:*)",
  "Bash(mvn deploy:*)",
  "Bash(./gradlew flywayMigrate:*)"
],
"deny": [
  "Read(**/*.jks)",
  "Read(**/*.keystore)"
]
```

## Rust

```jsonc
"allow": [
  "Bash(cargo build:*)",
  "Bash(cargo test:*)",
  "Bash(cargo run:*)",
  "Bash(cargo clippy:*)",
  "Bash(cargo fmt:*)"
],
"ask": [
  "Bash(cargo add:*)",
  "Bash(cargo install:*)"
],
"deny": [
  "Bash(cargo publish:*)"
]
```

## PHP

```jsonc
"allow": [
  "Bash(php artisan test:*)",
  "Bash(./vendor/bin/phpunit:*)",
  "Bash(./vendor/bin/pint:*)"
],
"ask": [
  "Bash(composer require:*)",
  "Bash(composer update:*)",
  "Bash(php artisan migrate:*)"
],
"deny": [
  "Bash(php artisan migrate:fresh:*)",
  "Bash(php artisan db:wipe:*)"
]
```

## Ruby

```jsonc
"allow": [
  "Bash(bundle exec rspec:*)",
  "Bash(bundle exec rubocop:*)",
  "Bash(bin/rails test:*)"
],
"ask": [
  "Bash(bundle add:*)",
  "Bash(bin/rails db:migrate:*)"
],
"deny": [
  "Bash(bin/rails db:drop:*)",
  "Bash(gem push:*)"
]
```

---

## Git — transversal a qualquer stack

```jsonc
"allow": [
  "Bash(git status:*)",
  "Bash(git diff:*)",
  "Bash(git log:*)",
  "Bash(git show:*)",
  "Bash(git branch:*)",
  "Bash(git add:*)",
  "Bash(git stash:*)"
],
"ask": [
  "Bash(git commit:*)",
  "Bash(git push:*)",
  "Bash(git merge:*)",
  "Bash(git rebase:*)",
  "Bash(gh pr create:*)",
  "Bash(gh pr merge:*)"
],
"deny": [
  "Bash(git push --force:*)",
  "Bash(git reset --hard:*)",
  "Bash(git clean -fdx:*)"
]
```

**Sobre `git commit` no `ask`:** decisão de estilo. Time que usa o agente para commits frequentes pode mover para `allow` — o commit é local e reversível. Perguntar ao usuário antes de gravar.

**Sobre `git push --force` no `deny`:** proteção contra reescrita de histórico compartilhado. Se o time usa `--force-with-lease` legitimamente, adicionar `Bash(git push --force-with-lease:*)` ao `ask` em vez de afrouxar o `deny`.

---

## Docker e infraestrutura local

```jsonc
"allow": [
  "Bash(docker compose up:*)",
  "Bash(docker compose down:*)",
  "Bash(docker compose logs:*)",
  "Bash(docker ps:*)"
],
"ask": [
  "Bash(docker build:*)",
  "Bash(docker push:*)"
],
"deny": [
  "Bash(docker system prune:*)",
  "Bash(kubectl delete:*)",
  "Bash(terraform apply:*)",
  "Bash(terraform destroy:*)"
]
```

**Sobre Terraform no `deny`:** `apply` mexe em infraestrutura real e custa dinheiro. Mesmo `ask` é arriscado — a confirmação vira reflexo. Time que faz IaC com agente deveria mover para `ask` conscientemente, nunca deixar em `allow`.

---

## Princípios de calibragem

**Menor privilégio por padrão.** Preferir prefixo específico a tool inteira. `Bash(dotnet build:*)` em vez de `Bash(dotnet:*)`, e nunca `Bash` ou `Bash(*)`.

**A pergunta que decide o balde:**

| Pergunta | Balde |
|---|---|
| É leitura ou operação local reversível? | `allow` |
| Altera estado externo, mas é recuperável? | `ask` |
| É irreversível, destrutivo, ou expõe segredo? | `deny` |

**Fadiga de confirmação é risco de segurança.** Lista `ask` grande demais treina o dev a aprovar no automático, o que anula a proteção. Melhor um `allow` generoso no que é seguro e um `deny` firme no que é perigoso, com `ask` reservado ao que realmente merece pausa.

**`deny` é a única camada que não pode ser afrouxada.** Como as listas de todos os escopos se somam e `deny` vence sempre, é onde vale investir rigor: um `deny` no projeto protege todo mundo do time, independente das configurações pessoais de cada dev.

**Não bloquear o que o pipeline SDD precisa.** O agente lê `docs/**` o tempo todo (PRDs, planos, ADRs). Nunca colocar `docs/` em `deny`.
