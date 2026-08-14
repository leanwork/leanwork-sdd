---
description: Revisa implementação contra plano + PRD + arquitetura. Gera relatório REVIEW-{T-XX} com findings R-XX categorizados.
argument-hint: [T-XX e/ou path do diff/PR, opcional]
---

# Review de Implementação SDD

Você acaba de invocar o reviewer do pipeline SDD Leanwork. O objetivo é validar que a implementação entrega o que `T-XX` prometeu, cruzando código com plano, PRD e arquitetura.

Input do usuário: $ARGUMENTS

## O que fazer

### Passo 1 — Identificar a tarefa e o diff

Se o usuário forneceu `T-XX`, branch ou PR, use. Caso contrário, descobrir em ordem:

1. **Branch atual** (`git branch --show-current`) — procurar padrão `T-\d+`
2. **Último commit** (`git log -1 --pretty=%B`) — procurar padrão `T-\d+`
3. **Pergunta direta**: "Qual tarefa do plano essa implementação entrega? (ex.: T-04). E como acesso o código? (paste do diff, branch para comparar, ou caminho dos arquivos)"

### Passo 2 — Carregar contexto do projeto

Procure nos locais convencionais:

- Plano: `docs/plans/PLAN-*.md` que contém a tarefa T-XX
- PRD: referenciado no cabeçalho do plano (campo `**PRD de referência:**`)
- Arquitetura: `docs/architecture/proposta-arquitetural.md`
- CLAUDE.md: raiz do repositório

Se algum não existir, **registre como lacuna no relatório** e continue com review degradado. Não invente.

### Passo 3 — Descobrir a stack

Use a cascata em `references/stack-detection.md` da skill `reviewer-leanwork`:

1. Proposta arquitetural (seção 6.2 Containers + Restrições)
2. CLAUDE.md do projeto
3. Inspeção do repositório (`*.csproj`, `package.json`, etc.)
4. Pergunta ao usuário

Documente a stack descoberta e a fonte no preâmbulo do relatório.

### Passo 4 — Invocar a skill `reviewer-leanwork`

A partir daqui, a skill assume. Ela vai:

1. Aplicar os 5 eixos de review (aderência ao plano, rastreabilidade, aderência ao spec, cobertura de teste, qualidade do código)
2. Gerar findings numerados `R-XX` com severidade
3. Produzir o documento `REVIEW-T-XX-YYYY-MM-DD.md` seguindo o template

### Passo 5 — Salvar o relatório

Sugira salvar em `docs/reviews/REVIEW-{T-XX}-{data-iso}.md`. Se o projeto usa outra convenção (ex.: comentário direto no PR sem versionar), perguntar ao usuário.

Após gerar o relatório, mostrar ao usuário:

- Recomendação final (`✅ Aprovado / ⚠️ Aprovado com ressalvas / ⛔ Bloqueado`)
- Contagem por severidade
- Link/caminho do arquivo gerado
- Os 1-3 findings mais críticos em destaque (para o usuário decidir se vale ler o relatório completo)

## Casos especiais

### Review de PR com múltiplas tarefas

Se o PR entrega mais de uma tarefa (ex.: T-04, T-05, T-06 num único commit), gerar **um relatório por tarefa** e mostrar resumo agregado. Não misturar tudo num relatório só.

### Review de segundo round (re-review)

Se já existe um `REVIEW-T-XX-*.md` para a mesma tarefa, ler o anterior e marcar quais R-XX foram resolvidos e quais persistem. Novo relatório com sufixo `-round2` no nome.

### Projeto sem artefatos SDD

Se não há plano nem PRD, oferecer code review genérico mas **avisar que não há rastreabilidade** e sugerir rodar `/leanwork-start` para projetos futuros.

### Stack não detectada

Se nenhuma das 3 primeiras tentativas de detecção funcionou e o usuário não responde a pergunta de stack, parar e pedir esclarecimento — não fazer review chutando convenções.

## Regra de ouro

Não substitua a leitura humana do PR — complemente. O review estruturado serve para **não esquecer de checar coisas óbvias** e para **manter rastreabilidade**. Decisões finais ficam com pessoas.
