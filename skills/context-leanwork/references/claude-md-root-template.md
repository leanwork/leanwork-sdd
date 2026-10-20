# Template — CLAUDE.md da raiz do projeto

Template do arquivo de contexto que fica na raiz do repositório. Alvo: **60-120 linhas**. Acima disso, mover detalhe para docs referenciados.

Os marcadores `<!-- leanwork-context:start -->` e `<!-- leanwork-context:end -->` delimitam o que a skill pode atualizar em execuções futuras. Conteúdo fora deles é preservado integralmente.

As cercas de quatro crases que delimitam o bloco abaixo são o envelope deste arquivo — não fazem parte do documento gerado. As cercas de três crases dentro dele fazem.

---

````markdown
# [Nome do Projeto]

<!-- leanwork-context:start -->

## Resumo

[2-4 linhas. O que este sistema faz e para quem. Extraído do sumário executivo da
proposta arquitetural, comprimido. Um dev novo deve entender o propósito em 15 segundos.]

## Stack

- **Backend:** [linguagem + framework + versão]
- **Frontend:** [framework + versão, ou "não aplicável"]
- **Banco:** [engine + versão]
- **Infra:** [cloud, orquestração, filas, cache — só o que existe de fato]
- **Testes:** [frameworks de teste em uso]

## Comandos

[Apenas comandos que existem de verdade no repositório. Se um comando esperado não
existe, deixar o TODO explícito em vez de inventar.]

```bash
# Build
[comando real]

# Testes
[comando real]

# Rodar local
[comando real]

# Migrations
[comando real, se aplicável]

# Lint / format
[comando real, se aplicável]
```

## Convenções

[Só o que é decisão do projeto e o agente não adivinharia. Cada item em uma linha.
Origem entre parênteses quando vier de ADR.]

- [ex.: Comandos e queries passam por um pipeline centralizado de handlers; controllers nunca chamam a lógica de negócio direto (ADR-004)]
- [ex.: Erros de negócio via exceção dedicada, mapeada para HTTP 422; erros técnicos sobem para o tratamento de erro global]
- [ex.: Nomeação: `XxxCommand`, `XxxHandler`, `XxxValidator`, `XxxResult`]
- [ex.: Repositórios isolam o ORM; query builder do ORM nunca cruza a fronteira da camada de aplicação (ADR-006)]
- [ex.: Testes de cenário do PRD nomeados `CA_XX_descricao_do_cenario`]
- [ex.: Logging estruturado obrigatório em handlers; PII nunca em log]

## Restrições

[Tudo que é dado, não escolha. Extraído da seção 4 da proposta arquitetural.]

- [ex.: Dados devem permanecer em território nacional (LGPD + contrato)]
- [ex.: Cloud obrigatoriamente Azure (padrão corporativo do cliente)]
- [ex.: Compatibilidade com o ERP legado via API REST — contrato não pode mudar]

## Documentação

[Índice dos artefatos do pipeline SDD. Caminhos relativos, sem duplicar conteúdo.]

- **Arquitetura:** `docs/architecture/proposta-arquitetural.md`
- **ADRs:** `docs/architecture/adrs/` — decisões arquiteturais numeradas
- **PRDs:** `docs/prds/` — requisitos por feature (RN-XX, CA-XX)
- **Planos:** `docs/plans/` — tarefas de execução (T-XX)
- **Reviews:** `docs/reviews/` — relatórios de review (R-XX)

## Definition of Done

[Vale para toda tarefa, e por isso não se repete em cada plano. Ajustar ao que o time de fato cobra; remover o que não se aplica.]

- Critérios de aceite da tarefa verificados e testes passando
- Cobertura de testes conforme padrão do projeto
- Review aprovado (`/leanwork-review T-XX` ou par humano)
- Migrations testadas em ambiente espelhado, quando houver
- Logging estruturado nos pontos críticos
- Documentação interna atualizada (README, CLAUDE.md, ADR se houver decisão nova)
- Validação em staging com PO/QA, quando o modelo de entrega pedir
- Rollback documentado quando houver migration destrutiva

## Como trabalhar neste projeto

Este projeto usa o pipeline SDD Leanwork. Antes de implementar qualquer feature:

1. Verifique se existe um plano em `docs/plans/PLAN-XXX-*.md`
2. Identifique a próxima tarefa pendente sem bloqueio: `Status: Pendente` e todas as tarefas de `Depende de:` com `Status: Concluído`
3. Leia a tarefa inteira, incluindo os campos `Implementa:`, `Valida:` e `Decisões base:`
4. Abra os artefatos referenciados:
   - Regras de negócio (`RN-XX`) → o PRD indicado no cabeçalho do plano
   - Critérios de aceite (`CA-XX`) → seção Gherkin do mesmo PRD
   - Decisões arquiteturais (`ADR-XX`) → `docs/architecture/`
5. Respeite os pontos de validação humana marcados no plano
6. Nomeie os testes conforme a convenção `CA_XX_*` para preservar rastreabilidade
7. Atualize o estado ao terminar: campo `Status:` da tarefa (`Pendente` → `Em andamento` → `Concluído`, ou `Bloqueado` com o motivo em `Bloqueio:`). O plano é a fonte de verdade do estado — tarefa concluída que continua `Pendente` fica invisível para quem retomar o trabalho
8. Execute **uma tarefa por vez**, cada uma na sua branch `task/PLAN-XXX-T-XX` aberta a partir da branch base do projeto, e só integre na base depois de review sem `Bloqueante`

> Com o plugin Leanwork SDD instalado, `/leanwork-execute` faz os passos 1 a 8: abre a branch, implementa, entrega a review a um sub-agente e integra. `/leanwork-review T-XX` revisa de novo depois de uma correção. Sem o plugin, seguir os passos manualmente — eles não dependem de ferramenta.

<!-- leanwork-context:end -->

<!-- Conteúdo abaixo desta linha é mantido manualmente e não é alterado pela skill context-leanwork. -->
````

---

## Notas de preenchimento

### Resumo

Comprimir o sumário executivo da proposta arquitetural, não copiar. O sumário tem ~1 página; aqui cabem 2-4 linhas. Foco em **o que o sistema faz**, não em como.

### Stack

Só o que existe. Se a proposta arquitetural previa Redis mas ele ainda não foi implementado, não listar — ou listar com marcação explícita (`Redis (previsto, ainda não implementado — ADR-007)`).

### Comandos

**A seção mais frágil do arquivo.** Comandos inventados fazem o agente falhar de forma confusa. Regras:

- Extrair de arquivos reais (`package.json`, `Makefile`, `.csproj`)
- Se o projeto tem múltiplos runners (ex.: `npm` no front, `dotnet` no back), agrupar por contexto com comentário
- Se não houver comando de teste, escrever `<!-- TODO: nenhum comando de teste detectado no repositório -->` em vez de chutar

### Convenções

O critério para incluir: **o agente erraria se não soubesse disso?** Se a resposta é não, não inclua.

Exemplos que **entram**: pipeline de handlers centralizado obrigatório, padrão de tratamento de erro, convenção de nomeação de teste, boundaries entre camadas.

Exemplos que **não entram**: "escreva testes", "use nomes descritivos", "siga SOLID". Genérico demais para agregar.

Citar ADR entre parênteses sempre que a convenção vier de uma decisão arquitetural. Isso permite ao agente (e ao reviewer) rastrear o porquê.

### Restrições

Diferença entre convenção e restrição: convenção é escolha do time (pode mudar por decisão interna); restrição é imposta de fora (cliente, regulação, contrato). Manter separado ajuda o agente a saber o que é negociável.

### Documentação

Apenas caminhos. **Não** descrever o conteúdo de cada PRD — isso muda toda semana e vira link morto. Se o projeto tem muitos PRDs, apontar para a pasta, não listar um a um.

### Definition of Done

Substitui o checklist de prontidão que os planos repetiam igual a cada feature. Item próprio de uma feature (migration destrutiva, flag) vai em `Estratégia de entrega` do plano, não aqui. Preencher a partir do que o time já cobra em review — lista aspiracional que ninguém confere é pior que lista curta.

### Seção "Como trabalhar neste projeto"

Esse bloco é praticamente igual entre projetos que usam o pipeline SDD. Manter — é o que faz o agente navegar os artefatos sozinho em vez de perguntar.
