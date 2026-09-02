# Catálogo de Permissões — `.claude/settings.json`

Receitas de `allow` / `ask` / `deny` por ecossistema, usadas pela skill `context-leanwork` ao gerar o `.claude/settings.json`.

## Como as regras funcionam

- **Formato:** `Tool` ou `Tool(especificador)`
- **Precedência:** `deny` → `ask` → `allow`. A primeira regra que casar decide, independente de quão específica ela seja.
- **Escopos se somam:** as listas de `.claude/settings.json` (projeto), `.claude/settings.local.json` (pessoal) e `~/.claude/settings.json` (usuário) são combinadas. Um `deny` em qualquer escopo não pode ser afrouxado por um `allow` em outro.
- **`deny` não aceita exceção.** Não existe "negar tudo menos X" — para isso, use `allow` específico com `defaultMode` restritivo.
- **Sintaxe por tool:** `Bash` casa o texto inteiro do comando com `*` no lugar de qualquer trecho; `Read` e `Edit` usam caminhos estilo gitignore; `WebFetch` usa `domain:`.

### A fronteira de espaço nas regras de `Bash`

Errar isto é a fonte número um de regra que não protege o que se pensa proteger.

- `:*` no fim equivale a ` *`: `Bash(ls:*)` é a mesma regra que `Bash(ls *)`.
- **O espaço antes do `*` faz parte da regra.** `Bash(ls *)` exige espaço depois de `ls` — casa com `ls` e `ls -la`, **não** casa com `lsof`. Já `Bash(ls*)`, sem espaço, casa com `lsof` também.
- Pela mesma regra, `Bash(git push --force:*)` **não** casa com `git push --force-with-lease`: depois de `--force` vem `-`, não espaço.
- O `*` pode ir em qualquer posição, não só no fim: `Bash(git push * --force)` casa com `git push origin main --force`.
- Um `*` no fim precedido de espaço também casa o comando puro — mas só quando é o único wildcard da regra. `Bash(git push --force *)` casa com `git push --force`; `Bash(* --help *)` casa com `npm --help x` e não com `npm --help`.

**Consequência prática:** uma regra de `deny` escrita como prefixo só cobre a ordem de argumentos que você escreveu. Flag no fim, forma curta e alias escapam. Ao negar algo destrutivo, cobrir as variantes explicitamente — ver o bloco de Git adiante.

### Sombra de prefixo entre baldes

A precedência é `deny` → `ask` → `allow` e a especificidade **não** desempata. Uma regra larga no `ask` torna inalcançável qualquer regra mais estreita do `allow` — a [doc oficial](https://code.claude.com/docs/en/permissions) é literal: *"a matching ask rule prompts even when a more specific allow rule also matches the same call"*.

Logo, `Bash(npx tsc:*)` no `allow` convivendo com `Bash(npx:*)` no `ask` é código morto: o comando pergunta do mesmo jeito. Quando um comando coberto por regra larga é frequente demais para tolerar a confirmação, a saída **não** é abrir exceção no `allow` — é dar a ele um nome que a regra larga não alcance: um script no `package.json` chamado por `npm run`, um alvo de Makefile, um script em `scripts/`.

**Como conferir uma receita:** para cada entrada do `allow`, procurar no `ask` e no `deny` alguma regra que case com o mesmo comando. Se houver, a entrada do `allow` é inútil e deve sair, ou a regra larga precisa ser reescrita.

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
  "Bash(git reset --hard:*)",

  // Force push — as 6 variantes cobrem forma longa, curta,
  // e a flag depois do remote. Ver a seção de Git.
  "Bash(git push --force:*)",
  "Bash(git push -f:*)",
  "Bash(git push * --force)",
  "Bash(git push * --force *)",
  "Bash(git push * -f)",
  "Bash(git push * -f *)"
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
  "Bash(npm ci:*)"
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

**Sobre `npx` no `ask`:** `npx` executa pacote arbitrário baixado na hora — sempre passa por confirmação. Não adiantar exceções nomeadas (`npx tsc`, `npx prisma`) no `allow`: o `ask` mais largo vence pela precedência e a regra específica vira código morto. Para um `npx` frequente, declarar o comando como script no `package.json` e liberar `Bash(npm run <script>:*)`.

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
  "Bash(git push -f:*)",
  "Bash(git push * --force)",
  "Bash(git push * --force *)",
  "Bash(git push * -f)",
  "Bash(git push * -f *)",
  "Bash(git reset --hard:*)",
  "Bash(git clean -fdx:*)"
]
```

**Sobre `git commit` no `ask`:** decisão de estilo. Time que usa o agente para commits frequentes pode mover para `allow` — o commit é local e reversível. Perguntar ao usuário antes de gravar.

**Por que seis regras para negar force push.** Proteção contra reescrita de histórico compartilhado. Uma regra só não basta, por causa da fronteira de espaço:

| Comando | Regra que pega |
|---|---|
| `git push --force`, `git push --force origin main` | `Bash(git push --force:*)` |
| `git push -f origin main` | `Bash(git push -f:*)` |
| `git push origin main --force` | `Bash(git push * --force)` |
| `git push origin --force main` | `Bash(git push * --force *)` |
| `git push origin main -f` | `Bash(git push * -f)` |

**`--force-with-lease` continua liberado, e isso é intencional.** `Bash(git push --force:*)` exige espaço depois de `--force`, então não casa com `--force-with-lease` — o comando cai no `ask` pela regra `Bash(git push:*)`. Não é preciso adicionar nada ao `ask` para habilitá-lo. Time que queira negar também a forma com lease acrescenta `Bash(git push --force-with-lease:*)` ao `deny`.

**Buraco que permanece:** `git push origin +main` faz force push via refspec e não casa com nenhuma das seis. Negar `Bash(git push * +*)` cobre o caso, ao custo de falsos positivos em refspecs legítimos com `+`. Decisão do time; o padrão da skill é não incluir.

---

## Docker e infraestrutura local

```jsonc
"allow": [
  "Bash(docker compose up:*)",
  "Bash(docker compose stop:*)",
  "Bash(docker compose start:*)",
  "Bash(docker compose logs:*)",
  "Bash(docker ps:*)"
],
"ask": [
  "Bash(docker compose down:*)",
  "Bash(docker build:*)",
  "Bash(docker push:*)"
],
"deny": [
  "Bash(docker system prune:*)",
  "Bash(docker volume rm:*)",
  "Bash(docker volume prune:*)",
  "Bash(kubectl delete:*)",
  "Bash(terraform apply:*)",
  "Bash(terraform destroy:*)"
]
```

**Sobre `docker compose down` no `ask`:** `down -v` remove os volumes nomeados declarados na seção `volumes` **e** os anônimos ligados aos containers — banco de desenvolvimento, seed, fixtures. Sem a flag, `down` só remove containers e redes, que o `up` recria: o risco está inteiramente no `-v`. `stop` cobre o caso cotidiano de parar o ambiente sem tocar em nada persistente, e `start` traz de volta.

**Por que não negar apenas o `-v`.** Seria a regra mais precisa, e não é escrevível com segurança: o `deny` não aceita exceção, e a flag aparece em qualquer posição — `down --remove-orphans -v`, `-f compose.yml down -v`, `--volumes` por extenso. Cobrir as variantes exigiria uma dezena de regras de prefixo, e a primeira que faltasse seria a que passa. Estreitar o `allow` resolve em uma linha. Ver "Sombra de prefixo entre baldes".

**Sobre `docker volume rm` e `docker volume prune` no `deny`:** rota mais curta para a mesma perda que o `down -v`. `prune` sem flag remove os volumes anônimos não usados; com `-a`, também os nomeados. `docker system prune` já cobre a forma `--volumes` pelo casamento de prefixo.

**Buraco que permanece:** `docker compose up -V` (`--renew-anon-volumes`) descarta o conteúdo dos volumes anônimos ao recriar os containers. Volume nomeado não é afetado — por isso o `up` continua no `allow`. Projeto que guarde estado em volume anônimo deve mover `up` para o `ask`.

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
