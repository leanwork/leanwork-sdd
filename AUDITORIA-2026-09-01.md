# Auditoria adversarial — `leanwork-sdd` v1.5.0

> **Data:** 2026-09-01
> **Escopo lido:** 38 arquivos, integralmente (README, REFERENCES, LICENSE, plugin.json, 6 commands, 6 SKILL.md, 15 references, 3 templates)
> **Verificação externa:** `code.claude.com/docs/en/{plugins-reference, plugin-marketplaces, skills, plugins}`
> **Natureza:** auditoria somente-leitura. Nenhum arquivo do plugin foi editado.

**Veredito de abertura:** o plugin tem uma cadeia de rastreabilidade bem desenhada e um `REFERENCES.md` que efetivamente invalidou várias das acusações candidatas desta auditoria. Mas ele **não é instalável pelo caminho que o próprio README documenta**, **dois dos seis comandos falham deterministicamente** por divergência de vocabulário interno, e **a fase mais longa do ciclo de vida de software — a execução — está entre colchetes e sem dono**. O que existe está bem-feito; o problema é o que foi documentado como existente e não está.

**Contagem:** 17 findings — 4 Bloqueantes, 10 Importantes, 3 Sugestões. Os dois defeitos que quebram comandos hoje (vocabulário de status, `adr-leanwork`) somam menos de 20 linhas de correção.

---

## Índice

- [Bloqueantes](#bloqueantes)
  - [B1 — Não existe `marketplace.json`](#bloqueante-não-existe-marketplacejson--o-readme-documenta-uma-instalação-que-não-funciona)
  - [B2 — Vocabulário de status divergente](#bloqueante-vocabulário-de-status-divergente-entre-o-template-do-plano-e-os-comandos-que-o-leem)
  - [B3 — `adr-leanwork` é skill fantasma](#bloqueante-adr-leanwork--skill-fantasma-referenciada-duas-vezes)
  - [B4 — `[execução]` sem dono](#bloqueante-o-passo-execução-não-tem-dono--o-plugin-abandona-o-usuário-na-fase-mais-longa)
- [Importantes](#importantes)
  - [I1 — `deny` de `--force` bloqueia `--force-with-lease`](#importante-o-deny-de-git-push---force-também-bloqueia---force-with-lease-e-o-catálogo-recomenda-exatamente-o-que-não-funciona)
  - [I2 — `npx tsc` no allow é código morto](#importante-bashnpx-tsc-no-allow-é-código-morto-sob-bashnpx-no-ask)
  - [I3 — `docker compose down` destrói volumes](#importante-docker-compose-down-no-allow-autoriza-destruição-de-volumes)
  - [I4 — Nenhum `allowed-tools`](#importante-nenhuma-skill-ou-comando-declara-allowed-tools)
  - [I5 — `templates/` travado na v1.0](#importante-templates-está-travado-na-v10--a-documentação-mais-antiga-é-a-mais-errada)
  - [I6 — "Nunca se auto-invoca" não é implementado](#importante-nunca-se-auto-invoca-é-declarado-no-corpo-enquanto-o-frontmatter-otimiza-a-auto-invocação--e-existe-campo-oficial-para-o-efeito-desejado)
  - [I7 — Granularidade de tarefa com três definições](#importante-granularidade-de-tarefa-tem-três-definições-incompatíveis)
  - [I8 — Template pede custo e prazo](#importante-o-template-de-arquitetura-pede-custo-e-prazo-que-a-skill-promete-não-entregar)
  - [I9 — `id-conventions.md` se autocontradiz](#importante-id-conventionsmd-se-autocontradiz-sobre-reúso-de-id)
  - [I10 — Fences aninhadas nos templates](#importante-fences-aninhadas-nos-templates--o-agente-copia-a-cerca-de-fechamento-errada)
- [Sugestões](#sugestões)
- [Top 5 ações por retorno sobre esforço](#top-5-ações-por-retorno-sobre-esforço)
- [O que NÃO mudar](#o-que-não-mudar)
- [Perguntas ao autor](#perguntas-ao-autor)

---

# Bloqueantes

## [Bloqueante] Não existe `marketplace.json` — o README documenta uma instalação que não funciona

**Onde:** `README.md:327-334`; ausência de `.claude-plugin/marketplace.json` (o diretório contém apenas `plugin.json`).

**Problema:** o README oferece dois caminhos de instalação. O segundo não tem infraestrutura no repositório. A documentação oficial exige que o repositório distribuidor tenha `.claude-plugin/marketplace.json` com `name`, `owner` e `plugins[]`; sem ele não há o que `claude plugin install` resolva.

**Evidência:**

```bash
# Marketplace (se você publicar):
claude plugin install leanwork-sdd
```

Contra a doc oficial: *"Create `.claude-plugin/marketplace.json` in your repository root"* — https://code.claude.com/docs/en/plugin-marketplaces.md. Campos obrigatórios: `name`, `owner` (objeto com `name`), `plugins` (array; cada entrada exige `name` e `source`).

**Impacto:** quem clona o repositório e segue o README no segundo bloco recebe erro. O parêntese *"se você publicar"* não salva: ele sugere que publicar é um ato futuro do leitor, quando na verdade o arquivo que habilita a publicação está ausente do repositório do autor. Um plugin de SDD que não instala pelo caminho documentado tem um problema de credibilidade proporcional ao seu tema.

**Correção proposta:** criar `.claude-plugin/marketplace.json`:

```json
{
  "name": "leanwork",
  "owner": {
    "name": "Leanwork Group",
    "url": "https://leanwork.com.br"
  },
  "plugins": [
    {
      "name": "leanwork-sdd",
      "source": "./",
      "description": "Pipeline Spec-Driven Development: architect → PRD → protótipo → planner → review, com rastreabilidade ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R.",
      "version": "1.5.0",
      "license": "MIT",
      "category": "workflow"
    }
  ]
}
```

E corrigir o README para o comando real de marketplace:

```bash
# Marketplace:
claude plugin marketplace add leanwork/leanwork-sdd
claude plugin install leanwork-sdd@leanwork
```

**Confiança:** alta quanto à exigência do arquivo e ao schema (verificado na doc oficial). Média quanto à sintaxe exata dos dois comandos `plugin marketplace add` / `install <plugin>@<marketplace>` — confirmar contra `claude plugin --help` antes de publicar.

---

## [Bloqueante] Vocabulário de status divergente entre o template do plano e os comandos que o leem

**Onde:** `skills/planner-leanwork/references/plan-template.md:79` e `:167-171`; `commands/leanwork-next.md:43,46,72`; `commands/leanwork-trace.md:84-87,113,115`.

**Problema:** o plano tem duas representações de status para a mesma tarefa, em lugares diferentes do mesmo documento, e os comandos consumidores procuram uma terceira combinação. Nada define a transição.

**Evidência:** o bloco da tarefa usa texto simples —

```markdown
- [ ] **Status:** Pendente
```

A tabela de histórico do mesmo template usa emoji —

```markdown
| T-01   | ✅ Done | 2026-05-16   | `abc1234` | — |
| T-02   | 🔄 Doing | —          | —      | Aguardando review |
```

E os comandos procuram o vocabulário emoji dentro do bloco da tarefa:

- `leanwork-next.md:46` — *"Se há tarefas marcadas como `✅ Done` no plano mas sem review correspondente"*
- `leanwork-trace.md:113` — *"tarefas com `Status: Done` no plano"*

Repare que `next` e `trace` divergem **entre si**: um procura `✅ Done`, o outro procura `Status: Done`.

**Impacto:** um plano preenchido literalmente conforme o template nunca sai de `Status: Pendente` no bloco da tarefa — porque o template não diz para o quê mudar. `/leanwork-next` não encontrará nenhuma tarefa concluída e sugerirá eternamente a T-01. `/leanwork-trace` produzirá a Tabela 3 vazia ou inventada. Estes são os dois comandos que dependem de estado de execução, e ambos quebram. É a falha mais barata de corrigir e a mais cara de deixar: ela sabota exatamente o elo `T-XX → R-XX` que a v1.1 foi criada para fechar.

**Correção proposta:** fixar um vocabulário único e declará-lo em `templates/id-conventions.md`. Substituir `plan-template.md:79` por:

```markdown
- **Status:** Pendente
```

e adicionar imediatamente abaixo do bloco da T-01, no template:

```markdown
> **Vocabulário de status (fixo — comandos dependem dele):** `Pendente` | `Doing` | `Done` | `Blocked`.
> Escrever exatamente essas palavras no campo `Status:` da tarefa, sem emoji. Os emojis
> (✅ 🔄 ⛔) são decoração da tabela de Histórico e não devem ser usados como marcador de estado.
```

Depois trocar em `leanwork-next.md:43,46,72` as ocorrências de `⛔ Blocked` / `✅ Done` por `Status: Blocked` / `Status: Done`, alinhando com `leanwork-trace.md:113`.

**Confiança:** alta.

---

## [Bloqueante] `adr-leanwork` — skill fantasma referenciada duas vezes

**Onde:** `skills/planner-leanwork/SKILL.md:48` e `:87`.

**Problema:** o planner instrui o agente a delegar para uma skill que não existe no plugin (as seis são architect, prd, prototype, planner, reviewer, context).

**Evidência:**

> `:48` — "*se sim, sugerir resolver antes via skill `architect-leanwork` ou `adr-leanwork`*"
>
> `:87` — "*pausar e sugerir uso da skill `architect-leanwork` ou criação de ADR via `adr-leanwork`*"

**Impacto:** o momento em que essa instrução dispara é precisamente o pior — o planner detectou uma decisão arquitetural em aberto e vai propor ao usuário rodar um comando que não existe. O usuário perde confiança no pipeline no ponto em que ele estava certo sobre o processo. Duas ocorrências indicam que não foi lapso de digitação, e sim uma skill planejada que não veio.

**Correção proposta:** o `adr-template.md` já existe em `architect-leanwork/references/` e cobre o caso de ADR avulso. Substituir as duas ocorrências por:

`:48` → "*(se sim, sugerir resolver antes via `architect-leanwork` — ou, se for decisão isolada, registrar um ADR avulso com o template em `architect-leanwork/references/adr-template.md`)*"

`:87` → "*pausar e sugerir uso da skill `architect-leanwork`. Se a decisão for isolada e não exigir revisitar a proposta inteira, gerar um ADR avulso em `docs/architecture/adrs/` usando o template da skill de arquitetura. O plano consome decisões; não cria.*"

**Confiança:** alta.

---

## [Bloqueante] O passo `[execução]` não tem dono — o plugin abandona o usuário na fase mais longa

**Onde:** transversal. Origem em `README.md:6`.

**Problema:** o pipeline tem seis skills e seis comandos, e nenhum deles atua no intervalo entre "plano pronto" e "review". O plugin especifica exaustivamente e depois entrega um markdown com checkboxes.

**Evidência:**

```
1. Architect  →  2. PRD  →  3. Protótipo*  →  4. Planner  →  [execução]  →  5. Review
```

Os colchetes são honestos e é o único ponto do fluxo sem numeração. Mas as consequências se espalham por cinco frentes:

1. **Não há `/leanwork-execute`.** O `CLAUDE.md` gerado (`folder-conventions.md:84-99`) descreve em cinco passos como um agente deve encontrar e ler a próxima tarefa. Isso é a especificação de um comando que ninguém escreveu — está codificada como prosa em um arquivo de projeto em vez de virar `commands/leanwork-execute.md`.

2. **O estado de execução vive só em checkbox de markdown.** `plan-template.md:79` e `:163-171`. O plugin não escreve em nenhum sistema de tarefas; depende do agente reeditar o markdown corretamente a cada tarefa, sem verificação.

3. **O loop de round 2 do review não tem motor.** `review-template.md:15` tem o campo `Round: [1/2/3]` e `:191-199` tem a seção "Round anterior" com tabela de itens resolvidos. Mas `commands/leanwork-review.md` não tem parâmetro de round, não procura relatório anterior da mesma `T-XX`, e `folder-conventions.md:71` define o nome do arquivo `-round2.md` sem que nada o gere. A estrutura de re-review existe inteira, desabitada.

4. **Não há caminho de reconciliação quando um requisito muda depois do plano pronto.** `/leanwork-next` só olha para frente (`leanwork-next.md:48-53`); `planner-leanwork/SKILL.md:98` cobre "revisar plano existente" mas dispara por pedido do usuário, não por detecção de que o PRD mudou depois do plano. Em SDD, mudança de requisito pós-plano é o caso normal, não a exceção.

5. **`R-XX` bloqueante não volta para o plano.** O reviewer produz findings bloqueantes; nada os transforma em tarefa, em mudança de `Status`, ou em entrada no histórico. `leanwork-next.md:72` sabe *detectar* a inconsistência ("tarefa `Done` com review `Bloqueado` em aberto") mas só reporta.

**Impacto:** o pipeline investe quatro fases de rigor para produzir um artefato cuja execução é entregue ao improviso. O acoplamento inteiro `T-XX ↔ R-XX` — a razão de existir da v1.1 — depende de um humano editando markdown com disciplina. Na prática o plano diverge do código na segunda semana, e a partir daí `/leanwork-trace` produz uma matriz que descreve um projeto que não existe. Isso é pior que não ter matriz: `leanwork-trace.md:131` instrui corretamente a não inventar links, mas não tem como saber que os links escritos ficaram obsoletos.

**Correção proposta:** três intervenções, em ordem de retorno.

### (a) Criar `commands/leanwork-execute.md`

Promovendo a prosa de `folder-conventions.md:84-99` a comando de primeira classe:

````markdown
---
description: Executa a próxima tarefa pendente do plano SDD, carregando RN/CA/ADR/UI referenciados e atualizando o status ao concluir.
argument-hint: [T-XX — opcional; se omitido, pega a próxima pendente sem bloqueio]
---

# Executar tarefa do plano SDD

Tarefa alvo: $ARGUMENTS

## O que fazer

1. Localizar o plano em `docs/plans/PLAN-*.md`. Se houver mais de um, perguntar qual.
2. Se `$ARGUMENTS` traz uma `T-XX`, usar essa. Senão, encontrar a primeira tarefa com
   `Status: Pendente` cujas dependências em `Depende de:` estejam todas com `Status: Done`.
   Se não houver nenhuma elegível, reportar o bloqueio e parar.
3. Carregar o contexto declarado pela tarefa — não adivinhar:
   - `Implementa:` → abrir o PRD e ler cada `RN-XX` listado, na íntegra
   - `Valida:` → abrir o PRD e ler cada `Cenário [CA-XX]:` listado, na íntegra
   - `Decisões base:` → abrir a proposta arquitetural e ler cada `ADR-XX`
   - `Telas:` → abrir a SPEC-UI e ler a tela e **cada estado** listado
   Se algum ID referenciado não existir no artefato correspondente, PARAR e reportar —
   é gap de rastreabilidade, não erro de execução.
4. Verificar se a tarefa está listada na seção "Pontos de validação humana" do plano.
   Se estiver, pedir confirmação explícita antes de escrever qualquer código.
5. Implementar apenas o escopo de `Camadas/arquivos afetados`. Arquivo fora da lista exige
   justificativa explícita ao usuário antes de tocar.
6. Escrever os testes de `Testes a escrever:`, nomeando cada um `CA_XX_descricao` conforme
   `templates/id-conventions.md`.
7. Rodar os testes. Não marcar nada como concluído com teste vermelho.
8. Atualizar o plano: `Status: Done` na tarefa, marcar os checkboxes de
   `Critério de aceite (testável)`, e acrescentar linha na tabela de Histórico de execução
   com data e hash do commit.
9. Sugerir `/leanwork-review T-XX` como próximo passo. Não rodar automaticamente.

## O que NÃO fazer

- Executar mais de uma tarefa por invocação. Uma tarefa, um ciclo, uma revisão.
- Implementar regra de negócio que não está em nenhuma `RN-XX` da tarefa. Se a
  implementação exigir uma decisão que o PRD não cobre, parar e apontar a lacuna.
- Marcar `Done` uma tarefa com critério de aceite parcialmente atendido. Usar `Blocked`
  com a observação no histórico.
````

### (b) Dar motor ao round 2

Em `commands/leanwork-review.md`, acrescentar como primeiro passo:

> Procurar `docs/reviews/REVIEW-{T-XX}-*.md` existentes. Se houver, este é o round N+1: ler o relatório mais recente, preencher a seção "Round anterior" do template comparando item a item, e salvar como `REVIEW-{T-XX}-{data}-round{N+1}.md`.

### (c) Fechar o loop de findings

Acrescentar ao final de `commands/leanwork-review.md`:

> Se houver finding Bloqueante, mudar `Status:` da `T-XX` no plano para `Blocked` e registrar no Histórico de execução a referência ao `R-XX` que bloqueou. O plano é a fonte de verdade do estado; um review bloqueante que não aparece no plano é invisível para `/leanwork-next`.

**Confiança:** alta quanto à existência das cinco lacunas (verificáveis por leitura). Uma quarta intervenção possível — trocar checkbox de markdown por integração com o sistema de tarefas nativo do Claude Code — fica marcada como **[não verificado]**: não foi localizada documentação pública que estabilize essa API para uso por plugins, então não se recomenda depender dela sem confirmação.

---

# Importantes

## [Importante] O `deny` de `git push --force` também bloqueia `--force-with-lease`, e o catálogo recomenda exatamente o que não funciona

**Onde:** `skills/context-leanwork/references/permission-catalog.md:269` e `:277`.

**Problema:** o catálogo declara corretamente a semântica de precedência e prefixo na abertura, e depois emite uma recomendação que ela invalida.

**Evidência:**

`:8` — *"**Precedência:** `deny` → `ask` → `allow`. A primeira regra que casar decide, independente de quão específica ela seja."*

`:269` — `"Bash(git push --force:*)"` no `deny`.

`:277` — *"Se o time usa `--force-with-lease` legitimamente, adicionar `Bash(git push --force-with-lease:*)` ao `ask` em vez de afrouxar o `deny`."*

O comando `git push --force-with-lease origin main` casa com o prefixo `git push --force`. O `deny` decide primeiro. A regra sugerida no `ask` nunca é alcançada.

**Impacto:** o time segue a recomendação, o comando continua negado, e a conclusão natural do usuário é remover o `deny` inteiro — que é precisamente o desfecho que a recomendação queria evitar. Uma orientação de segurança que empurra o usuário a afrouxar a proteção é pior que a ausência de orientação. Agrava que `:320` afirma *"`deny` é a única camada que não pode ser afrouxada"*, o que aumenta a probabilidade de o usuário resolver o impasse editando o `deny` em vez de suspeitar da recomendação.

**Correção proposta:** substituir o `deny` por uma regra que não capture o `--force-with-lease`:

```jsonc
"deny": [
  "Bash(git push --force origin:*)",
  "Bash(git push -f:*)",
  "Bash(git reset --hard:*)",
  "Bash(git clean -fdx:*)"
]
```

E `:277` vira:

> **Sobre `git push --force` no `deny`:** proteção contra reescrita de histórico compartilhado. Atenção à semântica de prefixo: `Bash(git push --force:*)` **também casa com `--force-with-lease`**, porque `--force` é prefixo dele. Se o time usa `--force-with-lease` legitimamente, negar a forma explícita (`git push --force origin`, `git push -f`) e adicionar `Bash(git push --force-with-lease:*)` ao `ask`. Regra de `deny` mais larga que a intenção treina o time a removê-la.

**Confiança:** alta quanto à precedência `deny → ask → allow` (documentada). Alta quanto ao casamento por prefixo em regras `Bash(...:*)` — é a semântica declarada pelo próprio catálogo em `:8` e coerente com a documentação de permissões.

---

## [Importante] `Bash(npx tsc:*)` no allow é código morto sob `Bash(npx:*)` no ask

**Onde:** `skills/context-leanwork/references/permission-catalog.md:110` e `:115`.

**Problema:** a receita de Node coloca `npx tsc` no `allow` e `npx` genérico no `ask`. Pela precedência declarada no próprio arquivo, o `ask` vence e o `allow` nunca é alcançado.

**Evidência:**

```jsonc
"allow": [ ..., "Bash(npx tsc:*)" ],
"ask":   [ "Bash(npm install:*)", "Bash(npm i:*)", "Bash(npx:*)" ]
```

**Impacto:** menor que o finding anterior — o desfecho é um prompt a mais, não uma proteção derrubada. Mas é a mesma classe de erro no mesmo arquivo, e o arquivo é a única parte do plugin que produz configuração com efeito fora do markdown. Duas ocorrências do mesmo raciocínio invertido sugerem que as receitas não foram testadas contra a regra de precedência que o próprio documento abre declarando.

**Correção proposta:** remover `"Bash(npx tsc:*)"` do `allow` (é inalcançável) e acrescentar nota na receita:

> `npx` genérico fica no `ask` porque executa pacote arbitrário baixado na hora. Não adiantar exceções específicas (`npx tsc`, `npx prisma`) no `allow` — o `ask` mais largo vence pela precedência. Se um comando `npx` específico é frequente, o caminho correto é adicioná-lo como script no `package.json` e liberar `Bash(npm run <script>:*)`.

Essa nota tem valor além do conserto: ensina o padrão certo em vez de só corrigir o sintoma. **Auditar as demais receitas do arquivo com o mesmo critério** — não foi verificada uma a uma a existência de outras sombras de prefixo.

**Confiança:** alta.

---

## [Importante] `docker compose down` no allow autoriza destruição de volumes

**Onde:** `skills/context-leanwork/references/permission-catalog.md:286`.

**Problema:** `Bash(docker compose down:*)` no `allow` casa com `docker compose down -v`, que remove os volumes nomeados — bancos de desenvolvimento local com dados de seed, fixtures, estado acumulado.

**Evidência:**

```jsonc
"allow": [
  "Bash(docker compose up:*)",
  "Bash(docker compose down:*)",
  "Bash(docker compose logs:*)",
  "Bash(docker ps:*)"
]
```

**Impacto:** perda de dados locais sem prompt. O catálogo trata `rm -rf` e `git reset --hard` como merecedores de `deny` (`:57-59`) — o critério é destrutividade irreversível, e `down -v` se qualifica pelo mesmo critério. O agente que decide "vou limpar o ambiente e subir do zero" tem autorização prévia para isso. Pior que a perda em si é o efeito pedagógico: o catálogo é o artefato que o plugin usa para ensinar calibragem de permissão, e ele contém um allow largo demais no mesmo arquivo onde argumenta contra allows largos.

**Correção proposta:**

```jsonc
"allow": [
  "Bash(docker compose up:*)",
  "Bash(docker compose stop:*)",
  "Bash(docker compose logs:*)",
  "Bash(docker ps:*)"
],
"ask": [
  "Bash(docker compose down:*)",
  "Bash(docker build:*)",
  "Bash(docker push:*)"
]
```

Com a nota: *"`docker compose down` fica no `ask` porque `down -v` remove volumes nomeados — banco local, seed, fixtures. `stop` cobre o caso cotidiano de parar os containers sem risco."*

**Confiança:** alta quanto ao comportamento do `-v`. Alta quanto ao casamento por prefixo, pelo mesmo raciocínio do finding anterior.

---

## [Importante] Nenhuma skill ou comando declara `allowed-tools`

**Onde:** transversal — nenhum dos 12 arquivos de skill/comando tem o campo.

**Problema:** o plugin executa operações previsíveis e homogêneas — ler artefatos em `docs/`, escrever um markdown em `docs/`. Nada disso está pré-autorizado, então cada fase gera prompts de permissão repetidos.

**Evidência:** frontmatter integral de `commands/leanwork-trace.md`:

```yaml
---
description: Gera a matriz de rastreabilidade ADR ↔ RN ↔ CA ↔ UI ↔ T ↔ R a partir dos artefatos do pipeline SDD.
argument-hint: [arquivo do PRD, opcional — se omitido, tenta descobrir]
---
```

Contra a doc oficial: *"`allowed-tools` — Tools that don't require a permission prompt during skill execution"* — https://code.claude.com/docs/en/skills.md.

**Impacto:** ergonômico, mas com consequência de segurança invertida. Um comando como `/leanwork-trace` abre dezenas de arquivos; o usuário aprende a aprovar sem ler. Isso é treinamento de auto-aprovação por atrito, que é justamente o vício contra o qual `permission-catalog.md` foi escrito. O plugin recomenda calibrar permissões nos projetos dos outros e não calibra as próprias.

**Correção proposta:** declarar o mínimo por comando. Para `leanwork-trace.md` (estritamente leitura):

```yaml
allowed-tools: Read, Glob, Grep
```

Para os comandos que produzem artefato (`leanwork-start`, `leanwork-prototype`, `leanwork-review`), acrescentar `Write` **sem** pré-autorizar `Bash`. E deixar `/leanwork-context` sem `allowed-tools` de escrita deliberadamente — é o comando que grava `.claude/settings.json`, e prompt ali é a proteção correta.

**Confiança:** alta quanto à existência e semântica do campo (verificado). A escolha de quais tools liberar é julgamento, não regra da doc.

---

## [Importante] `templates/` está travado na v1.0 — a documentação mais antiga é a mais errada

**Onde:** `templates/id-conventions.md:3,18`; `templates/pipeline-example.md:3` e todo o corpo; `templates/folder-conventions.md:126`.

**Problema:** os três arquivos de `templates/` descrevem um pipeline de três fases. O pipeline tem seis skills desde a v1.4. E `id-conventions.md` é declarado pelo próprio arquivo como a referência única de que todas as skills dependem.

**Evidência:**

- `id-conventions.md:3` — *"Todas as **três** skills (`architect-leanwork`, `prd-leanwork`, `planner-leanwork`) e o comando `/leanwork-trace` dependem deste padrão."* — omite prototype, reviewer e context, e omite `/leanwork-review`, `/leanwork-prototype`, `/leanwork-next`, `/leanwork-context`.
- `id-conventions.md:18` — heading `### Comuns aos quatro` numa seção que governa **seis** tipos de ID (a própria tabela de `:7-14` lista seis).
- `pipeline-example.md:3` — *"Este documento mostra os **três** artefatos do pipeline (arquitetura → PRD → plano)"*. O exemplo end-to-end não tem SPEC-UI nem relatório de review; a matriz de `:159-166` não tem coluna `UI` nem `R`, e o Mermaid de `:170-180` para em `T-04`/`T-05`.
- `folder-conventions.md:126` — *"O que **não** colocar em `docs/`: Especificações de UI/UX (fluxos de design, mockups Figma) → pasta própria (`design/` ou link externo)"* — contradizendo a árvore do próprio arquivo em `:18-20`, que cria `docs/prototype/` com `SPEC-UI-001` e `assets/`.

**Impacto:** três efeitos distintos, o terceiro sendo o pior.

1. O `pipeline-example.md` é explicitamente *"exemplo de calibração para as skills"* (`:3`). Um exemplo de calibração desatualizado calibra para o comportamento antigo — um agente que o consulta produz matriz sem `UI` e sem `R`.
2. `folder-conventions.md:126` instrui ativamente a tirar a SPEC-UI de `docs/`, contra a especificação da própria skill de protótipo (`prototype-leanwork/SKILL.md:134`).
3. **O plugin cuja tese é "documentação viva rastreável" tem drift na sua própria documentação, nos arquivos declarados como fonte única.** Isso não é ironia gratuita — é o argumento mais forte que um cético pode usar contra adotar o método, e está no repositório.

**Correção proposta:**

- `id-conventions.md:3` → *"Todas as seis skills do pipeline e os comandos `/leanwork-trace`, `/leanwork-next` e `/leanwork-review` dependem deste padrão."*
- `id-conventions.md:18` → `### Comuns aos seis`
- `pipeline-example.md`: estender a demanda de Ofertas Relâmpago com um Fragmento 3 (SPEC-UI com `UI-01`/`UI-02` e os estados `.limiteExcedido`/`.esgotado` derivados de CA-02/CA-03) e um Fragmento 5 (relatório de review com um `R-01`), e acrescentar colunas `UI` e `R` na matriz de `:161`. É o arquivo de maior esforço da lista e o de maior retorno pedagógico.
- `folder-conventions.md:126` → *"Mockups e arquivos-fonte de design (Figma, Sketch) → pasta própria (`design/`) ou link externo. A **SPEC-UI** é exceção: é especificação rastreável, não artefato de design, e fica em `docs/prototype/`."*

**Adicionalmente:** instituir a regra de que toda skill nova obriga a varredura de `templates/`. O drift aqui não foi acidente isolado — foram três versões consecutivas sem revisitar a pasta.

**Confiança:** alta.

---

## [Importante] "Nunca se auto-invoca" é declarado no corpo, enquanto o frontmatter otimiza a auto-invocação — e existe campo oficial para o efeito desejado

**Onde:** `skills/prototype-leanwork/SKILL.md:3` vs `:167`; `skills/context-leanwork/SKILL.md:209`.

**Problema:** duas skills declaram no corpo que nunca se auto-invocam, e ambas trazem no frontmatter uma `description` densa de gatilhos de auto-invocação. O corpo só é lido depois que a skill foi carregada; a declaração chega tarde demais para impedir o que já aconteceu.

**Evidência:** `prototype-leanwork/SKILL.md:167` — *"Nunca se auto-invoca."* Contra a própria `description` (`:3`): *"Use quando o usuário pedir 'especificar as telas', 'documentar o protótipo', 'criar protótipo', 'mapear telas contra o PRD', 'gerar SPEC-UI', 'indexar o Figma'..."*. Sete frases-gatilho é o padrão recomendado para **maximizar** auto-invocação.

**Impacto:** a intenção é boa e está documentada em três lugares (`README:320`+, tabela de `prototype/SKILL.md:169-174`, `context/SKILL.md:209`) — a fase de protótipo deve ser convite, não imposição. Mas o mecanismo escolhido não produz o efeito. Um usuário que digitar "quero documentar o protótipo" vai disparar a skill que jurou não se auto-invocar. A promessa de opt-in do `context-leanwork` é mais delicada ainda: é a skill que grava `.claude/settings.json`.

**Correção proposta:** usar o campo oficial. Em ambas as skills, acrescentar ao frontmatter:

```yaml
disable-model-invocation: true
```

Doc: *"`disable-model-invocation` — `true` = só invocação manual (`/name`). Default: `false`"* — https://code.claude.com/docs/en/skills.md.

Feito isso, `prototype-leanwork/SKILL.md:167` pode manter a frase, porque ela passa a ser verdade, e a `description` continua útil para a listagem e para o `/leanwork-next` sugerir a skill por nome.

**Se a intenção não for essa** — se o autor quer que a skill seja auto-invocável e o "nunca se auto-invoca" significava apenas "as outras skills não a chamam automaticamente" — então a frase está mal redigida e deve virar: *"Nenhuma outra skill do pipeline a invoca automaticamente; as demais apenas sugerem."*

**Confiança:** alta quanto à existência do campo (verificado). Média quanto a qual das duas intenções é a do autor — daí a pergunta na seção final.

---

## [Importante] Granularidade de tarefa tem três definições incompatíveis

**Onde:** `skills/planner-leanwork/references/task-examples.md:9` e `:16`; `skills/planner-leanwork/SKILL.md:73-75`.

**Problema:** o parâmetro mais consequente do planner — o tamanho da tarefa — tem três números diferentes, dois deles no mesmo arquivo, em contradição direta.

**Evidência:**

- `task-examples.md:9` — *"executável em **30 minutos a 4 horas**"*
- `task-examples.md:16` — *"Mais de 2 horas estimadas mentalmente | Quebrar"*
- `planner-leanwork/SKILL.md:73-75` — *"Tarefa pequena (1 commit, ~30min-2h)... Tarefa média (1 PR, meio dia)... **Nunca** tarefa grande (>1 dia)."*

Uma tarefa de 3 horas é simultaneamente válida (`:9`), obrigatoriamente quebrável (`:16`) e "média, aceitável" (`SKILL.md:74`).

**Impacto:** o teto de tarefa define o tamanho do plano inteiro. Com 4h de teto, uma feature vira 8 tarefas; com 2h, vira 16. Dois planos gerados para o mesmo PRD saem estruturalmente diferentes conforme qual regra o modelo pegar primeiro — e `task-examples.md` é lido sob demanda, então a probabilidade varia por sessão. Isso ataca a reprodutibilidade, que é o argumento de venda do SDD.

**Correção proposta:** eleger `30min–4h` como teto único (é o mais permissivo e o único que aparece como afirmação positiva) e corrigir os outros dois:

- `task-examples.md:16` → `| Mais de 4 horas estimadas mentalmente | Quebrar |`
- `planner-leanwork/SKILL.md:73-75` → *"Tarefa pequena (1 commit, 30min–2h) — padrão. Tarefa média (1 PR, 2h–4h) — aceitável quando a coesão justifica. **Acima de 4h: quebrar.** Nunca tarefa de mais de 1 dia."*

Adicionar em `id-conventions.md`, junto da regra de `T-XX` (`:33`), a referência cruzada ao teto, para haver um lugar canônico.

**Confiança:** alta.

---

## [Importante] O template de arquitetura pede custo e prazo que a skill promete não entregar

**Onde:** `skills/architect-leanwork/references/proposal-template.md:18` vs `skills/architect-leanwork/SKILL.md:3` e `README.md:320`.

**Problema:** três documentos afirmam que o pipeline não produz estimativa. O template que o arquiteto preenche tem um campo de custo e prazo na seção 1.

**Evidência:**

- `proposal-template.md:18` — *"Custo e prazo de cara (em ordem de grandeza, não detalhado)"*
- `architect-leanwork/SKILL.md:3` (description) — *"NÃO entrega estimativa de esforço, cronograma ou código pronto"*
- `README.md:320` — *"**Sem cronograma, sem estimativa.** O pipeline produz 'o quê', 'por quê' e 'em que ordem'. 'Quando' e 'quanto' são responsabilidade do planejamento de sprint."*

**Impacto:** o campo do template vence, porque é o que o agente preenche na hora de gerar. O resultado é uma proposta arquitetural com ordem de grandeza de custo, que é exatamente o artefato que `README:320` afirma que o pipeline não produz — e é o tipo de número que, uma vez escrito num documento com timbre de proposta, circula como compromisso comercial. Um plugin de spec não deveria produzir número financeiro por acidente de template.

**Correção proposta:** decidir de que lado fica e alinhar os três.

**Se a posição de `README:320` é a verdadeira** (é a mais defensável): remover a linha `:18` do template e substituir o item por *"Ordem de grandeza de esforço em complexidade relativa (baixa/média/alta por componente), nunca em horas ou reais."*

**Se o campo é intencional** — arquiteto sênior sinalizando ordem de grandeza é prática legítima em proposta comercial — então corrigir os outros dois. `README:320` viraria: *"**Sem cronograma, sem estimativa detalhada.** A proposta arquitetural sinaliza ordem de grandeza para calibrar a decisão de viabilidade; horas e datas são responsabilidade do planejamento de sprint."*

Não deixar como está. É a única inconsistência do plugin com consequência potencialmente contratual.

**Confiança:** alta.

---

## [Importante] `id-conventions.md` se autocontradiz sobre reúso de ID

**Onde:** `templates/id-conventions.md:22` vs `:37`.

**Problema:** a regra geral proíbe reúso de ID; a regra específica de `R-XX` o institucionaliza.

**Evidência:**

`:22` — *"**Sem reúso**: uma vez que um ID foi atribuído, ele nunca é reciclado, mesmo que o item original seja revogado."*

`:37` — *"**R-XX**: numeração sequencial por relatório (cada `REVIEW-T-XX-*.md` começa do R-01). **Não** numeração global ao projeto."*

Com dois rounds de review na T-04, existem dois `R-01` distintos.

**Impacto:** menor que os anteriores, porque `:37` explicita o mecanismo de desambiguação (referência cruzada na seção "Round anterior"). Mas a regra `:22` está sob o heading `### Comuns aos quatro` e é lida como universal, então o leitor encontra a exceção só se chegar até `:37`. Pior: `R-01` é ambíguo em qualquer conversa fora do arquivo — "resolvi o R-01" não identifica nada sem o nome do relatório.

**Correção proposta:** tornar a exceção explícita no ponto da regra geral. `:22` vira:

> - **Sem reúso**: uma vez que um ID foi atribuído, ele nunca é reciclado, mesmo que o item original seja revogado. Use marcação de revogação (ver abaixo). **Exceção: `R-XX`**, cuja numeração é local ao relatório — ver a regra específica adiante.

E acrescentar em `:37`: *"Fora do arquivo do relatório, sempre citar `R-XX` qualificado: `R-01 (REVIEW-T-04-2026-06-15)`. `R-01` sozinho é ambíguo assim que existe mais de um relatório."*

**Confiança:** alta.

---

## [Importante] Fences aninhadas nos templates — o agente copia a cerca de fechamento errada

**Onde:** `skills/planner-leanwork/references/plan-template.md:7-172`; `skills/prd-leanwork/references/prd-template.md:7-189`; `skills/architect-leanwork/references/proposal-template.md`; `skills/prototype-leanwork/references/spec-ui-template.md:9-190`; `skills/reviewer-leanwork/references/review-template.md:7-212`; `skills/context-leanwork/references/claude-md-root-template.md` e `claude-md-module-template.md`.

**Problema:** todos os templates envolvem o documento inteiro numa cerca de três crases com linguagem `markdown`, e o conteúdo interno contém cercas de três crases (`gherkin`, `mermaid`, `bash`, `jsonc`). A primeira cerca interna fechada encerra o bloco externo.

**Evidência:** `prd-template.md` abre a cerca externa em `:7`; contém cerca `mermaid` em `:73`, `gherkin` em `:100`, `mermaid` em `:146` e `:159`; fecha em `:189`. `spec-ui-template.md` tem o mesmo padrão com o Mermaid de `:133-141`.

**Impacto:** duplo.

**(a)** Renderização quebrada no GitHub e em qualquer visualizador CommonMark, o que degrada o template como documentação humana.

**(b)** Mais sério: o agente que lê o template para gerar o artefato precisa inferir onde o documento-modelo termina. Com cercas desbalanceadas, a inferência erra — o sintoma típico é o PRD gerado carregando uma cerca órfã, ou truncando a partir do primeiro bloco Gherkin. Como o Gherkin é a seção 9 do PRD e é onde nascem os `CA-XX`, o truncamento atinge exatamente o elo mais crítico da cadeia.

**Correção proposta:** usar cerca externa de **quatro crases** em todos os sete templates. Trocar a linha de abertura de três crases + `markdown` por quatro crases + `markdown`, e a linha de fechamento correspondente por quatro crases. CommonMark permite fechamento apenas por cerca de comprimento igual ou maior, então as cercas internas de três crases passam a ser conteúdo literal, a renderização fica correta e o limite do modelo fica inequívoco.

**Confiança:** alta quanto à regra de CommonMark (é o dialeto de renderização declarado pelo ambiente). Alta quanto ao defeito de renderização; média quanto à frequência do erro de geração — é uma inferência sobre comportamento do modelo, não uma observação.

---

# Sugestões

## [Sugestão] `plugin.json` omite três campos aceitos e úteis

**Onde:** `.claude-plugin/plugin.json`.

**Problema:** o manifesto tem `name`, `version`, `description`, `author`, `homepage`, `keywords`. Faltam `license`, `repository` e `$schema` — os três aceitos pelo schema oficial.

**Evidência:** existe `LICENSE` na raiz (MIT, Leanwork Group, 2026) que o manifesto não declara. Doc oficial confirma os três campos: *"`license` | string | ... `repository` | string | ... `$schema` | string | JSON Schema URL for editor autocomplete"* — https://code.claude.com/docs/en/plugins-reference.md.

**Impacto:** `license` ausente no manifesto significa que ferramentas de catálogo não sabem que o plugin é MIT — relevante para adoção corporativa. `$schema` custa uma linha e dá autocomplete e validação no editor, o que teria capturado a omissão dos outros dois.

**Correção proposta:**

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "leanwork-sdd",
  "version": "1.5.0",
  "license": "MIT",
  "repository": "https://github.com/leanwork/leanwork-sdd",
  "...": "demais campos existentes"
}
```

(ajustar a URL do `repository` para a real).

**Confiança:** alta quanto aos campos serem aceitos. `name` é o único campo obrigatório, então nada disso quebra hoje.

---

## [Sugestão] `ADR-XX` ou `ADR-XXX` — dois padrões, três arquivos

**Onde:** `templates/id-conventions.md:9,21,27`; `templates/folder-conventions.md:42`; `skills/architect-leanwork/references/adr-template.md:94`.

**Problema:** a referência única de IDs diz dois dígitos; dois outros arquivos dizem três.

**Evidência:**

- `id-conventions.md:21` — *"**Largura mínima de 2 dígitos** com zero à esquerda"*, e a tabela de `:9` usa `ADR-XX`
- `folder-conventions.md:42` — *"**Nome de ADR como arquivo**: `ADR-XXX-titulo-em-kebab-case.md` — número com 3 dígitos"*
- `adr-template.md:94` — *"**Numeração ADR-XXX**: 3 dígitos com zero à esquerda"*
- `pipeline-example.md` usa `ADR-002` (3 dígitos), enquanto `plan-template.md:84` documenta o campo como `Decisões base: [ADR-XX]`

**Impacto:** baixo enquanto ADRs forem inline, porque o texto é livre. Vira real quando viram arquivos: um `Decisões base: ADR-02` no plano não localiza `ADR-002-lock-pessimista.md` por busca literal, e `/leanwork-trace` é instruído a fazer análise estática dos artefatos (`leanwork-trace.md:131`).

**Correção proposta:** padronizar em 3 dígitos para ADR — é o único ID com vida útil plurianual e o único que vira nome de arquivo. Corrigir `id-conventions.md:9` para `ADR-XXX`, ajustar a regra de largura em `:21` para *"Largura mínima de 2 dígitos, **exceto `ADR`, que usa 3**"*, e atualizar `plan-template.md:84`.

**Confiança:** alta.

---

## [Sugestão] Repositório sem `.gitignore`, com `.claude/settings.local.json` presente

**Onde:** raiz do repositório.

**Problema:** existe `.claude/settings.local.json` (não rastreado pelo git) e não existe `.gitignore`. Nada impede um `git add .` de commitá-lo.

**Evidência:** `git ls-files .claude` retorna vazio (não rastreado); não há arquivo `.gitignore` na raiz.

**Impacto:** `settings.local.json` é, por convenção, o arquivo de permissões pessoais do desenvolvedor — pode conter allows calibrados para a máquina do autor. Publicá-lo num plugin que outras pessoas instalam é distribuir configuração de permissão não intencional. A probabilidade é baixa; o custo da prevenção é uma linha. E há uma assimetria desconfortável: este é o repositório do plugin que ensina higiene de permissões.

**Correção proposta:** criar `.gitignore` na raiz:

```gitignore
.claude/settings.local.json
.DS_Store
Thumbs.db
```

**Confiança:** alta.

---

# Top 5 ações por retorno sobre esforço

1. **Unificar o vocabulário de status do plano** (`plan-template.md`, `leanwork-next.md`, `leanwork-trace.md`). ~15 linhas em 3 arquivos; desbloqueia dois dos seis comandos, que hoje falham deterministicamente. Maior retorno por linha editada do repositório inteiro.

2. **Remover `adr-leanwork`** (`planner-leanwork/SKILL.md:48,87`). Duas linhas; elimina o único ponto onde o plugin oferece ao usuário um comando inexistente, e no pior momento possível.

3. **Criar `marketplace.json` e corrigir o bloco de instalação do README.** Um arquivo de 15 linhas; transforma a instalação documentada em instalação real. É o pré-requisito de qualquer adoção fora da máquina do autor.

4. **Corrigir os três defeitos de `permission-catalog.md`** (`--force-with-lease`, `npx tsc` morto, `compose down -v`). ~10 linhas; é o único arquivo do plugin que produz configuração com efeito fora do markdown, e os três erros são da mesma classe — recomendação que a própria regra de precedência invalida.

5. **Criar `commands/leanwork-execute.md`.** Maior esforço da lista, e o único item que muda o que o plugin *é*: hoje ele especifica e depois solta a mão. O texto do comando já existe disperso em `folder-conventions.md:84-99`; o trabalho é promovê-lo e fechar o loop de status.

---

# O que NÃO mudar

Cinco decisões atacadas nesta auditoria e concluídas corretas.

**1. A fase de protótipo ser opcional com critério de saída explícito.** A acusação candidata era "fase opcional é fase que nunca roda". Não procede: `prototype-leanwork/SKILL.md:23-27` dá três sinais concretos e verificáveis de não-aplicabilidade (arquitetura sem container de frontend, PRD sem personas nem fluxos, Gherkin sem ator humano), `:31` traz o texto de saída pronto, e `:34` fecha com *"**Não insistir.** Especificar UI onde não há UI é ruído."* Isso é melhor engenharia de processo do que a maioria das ferramentas de spec: a decisão de pular tem critério, não é preferência do usuário no momento. E o `README.md` ecoa a mesma postura, então não é ruído local.

**2. O reviewer não trazer padrões de stack embutidos.** A acusação candidata era "review sem critério de stack é review vazio". O argumento de `stack-detection.md:96-104` derruba: *"Padrões evoluem rápido... Skill hard-coded com padrões de 2025 estaria desatualizada em 2027"*. E o fallback é honesto em vez de conveniente — `:104` proíbe explicitamente inventar (*"**Não inventar** que 'em .NET deveria ter MediatR' — isso é opinião, não regra do projeto"*) e `:108` obriga a declarar a limitação no relatório. Uma skill que se recusa a fingir competência é mais valiosa que uma que a simula.

**3. `screen-states.md` existir como catálogo separado.** A acusação candidata era redundância com `spec-ui-template.md`. Errado: é o arquivo de conteúdo mais original do plugin. O par vazio-inicial × vazio-por-filtro (`:33-35`), o `.conflito` de edição concorrente (`:76`) e o `.erroEnvio` que preserva os dados digitados (`:78`, ecoado como Bloqueante em `review-checklist.md:183`) são exatamente os bugs que atravessam sprint e sobrevivem ao QA. E `:123` fecha o mecanismo: *"cada `Cenário [CA-XX]` cujo `Então` descreve rejeição, bloqueio ou mensagem de erro corresponde a um estado de tela"* — isso converte Gherkin em inventário de estados por procedimento, não por intuição. Se o plugin fosse reduzido a um arquivo, seria este.

**4. `REFERENCES.md` declarar divergências deliberadas.** A acusação candidata era blindagem retórica — documento que antecipa críticas para desarmá-las. Não é o que faz. Fez trabalho real nesta auditoria: `:381-417` já registra a fatiagem horizontal, a numeração global de `T-XX`, o ID no nome do cenário em vez de tag Cucumber, e — o mais relevante — que o `grep` do trace verifica menção e não execução. As quatro estavam na lista de candidatas desta auditoria. Um documento que custa findings ao autor por antecipação não é blindagem; é honestidade com preço.

**5. A recusa em gerar tela para fechar a matriz.** A acusação candidata era conservadorismo que deixa trabalho na mesa. Está certo e é o comportamento mais difícil de manter: `prototype-leanwork/SKILL.md:130` — *"**Nunca gerar a tela faltante silenciosamente para 'fechar' a matriz.**"* — reforçado em `spec-ui-template.md:224`: *"Fechar matriz com invenção é pior que matriz honestamente incompleta."* A pressão de produto sempre empurra para o oposto, porque matriz verde demonstra melhor. Manter a lacuna visível é a decisão certa e a que mais custa disciplina.

---

# Perguntas ao autor

Cinco pontos onde não foi possível distinguir omissão de escolha, e a resposta muda a severidade do que está acima.

**1. A execução está fora do escopo por decisão?** Se sim, os colchetes em `README:6` deveriam virar declaração explícita — *"A execução é do seu agente e do seu processo; o pipeline entrega o plano e recebe o código de volta no review"* — e o Bloqueante sobre `[execução]` vira Sugestão. Se não é decisão, é a maior lacuna do plugin. Hoje o README não permite ao leitor saber qual dos dois é.

**2. O plugin é para distribuição pública ou uso interno da Leanwork via `--plugin-dir`?** Se for interno, o `marketplace.json` desce de Bloqueante para Sugestão e a correção vira remover o segundo bloco do README. Se for público, é pré-requisito de lançamento.

**3. `templates/` é para o humano ou para o agente?** `pipeline-example.md:3` diz *"exemplo de calibração para as skills"*, o que sugere agente — e aí o drift é funcional, não cosmético. Mas nenhuma `SKILL.md` instrui a ler `pipeline-example.md`. Se ninguém o lê, ele é documentação de apresentação e a prioridade cai; se as skills deveriam lê-lo, falta a instrução que aponta para ele.

**4. `allowed-tools` foi omitido por política ou por desconhecimento?** Há um argumento defensável para não pré-autorizar nada num plugin que outras empresas instalam. Se foi essa a razão, ela merece uma linha no README — vira postura, não lacuna. Se foi desconhecimento, o campo resolve o atrito de `/leanwork-trace` sem custo de segurança.

**5. Azure DevOps: integração planejada ou vocabulário emprestado?** `prd-template.md:56-67` produz a hierarquia Epic → Feature → PBI *"para o Azure DevOps"*, e `README:317` cita o ADO como parte do contexto de adaptação. Mas nada cria work item — o humano redigita. Se a integração está no roadmap, a seção 6 do PRD é a base certa e vale marcá-la como tal. Se não está, o *"para o Azure DevOps"* promete mais do que entrega e deveria virar *"para cadastro no seu board"*.

---

## Anexo — verificações contra a documentação oficial

Fatos confirmados em `code.claude.com/docs/en/` e usados como base dos findings:

| Item | Resultado | Fonte |
|---|---|---|
| `plugin.json` — único campo obrigatório | `name` | `plugins-reference.md` |
| `plugin.json` — `license`, `repository`, `$schema` aceitos | Sim | `plugins-reference.md` |
| `plugin.json` — `author` como objeto | Correto (formato atual do plugin está certo) | `plugins-reference.md` |
| `marketplace.json` obrigatório para distribuição | Sim, em `.claude-plugin/marketplace.json` | `plugin-marketplaces.md` |
| `marketplace.json` — campos obrigatórios | `name`, `owner`, `plugins[]` (cada plugin: `name`, `source`) | `plugin-marketplaces.md` |
| Limite de `description` no SKILL.md | 1.536 caracteres (com `when_to_use`) | `skills.md` |
| Tamanho recomendado do corpo do SKILL.md | < 500 linhas | `skills.md` |
| `allowed-tools` existe e evita prompt | Sim | `skills.md` |
| `disable-model-invocation` existe | Sim (`true` = só invocação manual) | `skills.md` |
| `${CLAUDE_PLUGIN_ROOT}` existe | Sim, substituído apenas em plugin skills | `skills.md` |
| Auto-descoberta de `skills/`, `commands/`, `agents/`, `hooks/` | Sim, por convenção de diretório | `plugins.md` |

**Conformidade verificada e aprovada:** as 6 descriptions estão entre 995 e 1.241 caracteres (limite 1.536); os 6 SKILL.md estão entre 106 e 245 linhas (recomendado < 500); `author` está no formato de objeto correto; `name` do plugin respeita o regex kebab-case. Nenhuma violação de limite oficial foi encontrada.
