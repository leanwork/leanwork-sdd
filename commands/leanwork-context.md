---
description: Gera ou atualiza o contexto do projeto para agentes — CLAUDE.md (raiz e módulos) e permissões em .claude/settings.json.
argument-hint: [raiz | modulo <nome> | permissoes | auditar — opcional]
---

# Contexto do projeto para agentes de IA

Gerar ou atualizar o contexto de projeto para agentes de IA: os arquivos `CLAUDE.md` (Resumo, Stack, Comandos, Convenções, Restrições, índice da documentação) e as permissões em `.claude/settings.json`.

Escopo solicitado: $ARGUMENTS

## O que fazer

Invoque a skill `context-leanwork`, que conduz o fluxo completo. Se o usuário passou argumento, use-o para pular a pergunta de escopo:

- `raiz` → gerar/atualizar apenas o `CLAUDE.md` da raiz
- `modulo <nome>` → gerar/atualizar apenas o módulo indicado
- `permissoes` → gerar/atualizar apenas o `.claude/settings.json`
- `auditar` → modo somente-leitura: reportar drift e lacunas sem gravar nada
- *(vazio)* → a skill pergunta o escopo

## Regras que valem sempre

**Nunca sobrescrever conteúdo humano.** A skill faz merge apenas dentro dos blocos delimitados por `<!-- leanwork-context:start -->` e `<!-- leanwork-context:end -->`. Arquivo sem esses marcadores foi escrito à mão: propor alternativas ao usuário, nunca decidir por ele.

**Sempre mostrar o diff antes de gravar.** Mesmo quando a mudança parecer trivial.

**Módulos são opt-in.** Detectar e listar os módulos, deixar o usuário escolher. Nunca gerar para todos de uma vez sem escolha explícita — projeto com 8 módulos vira 8 arquivos, e vários deles só ruído.

**Não inventar comandos.** A seção Comandos vem de inspeção real do repositório (`package.json`, `Makefile`, `.csproj`, etc.). Quando não houver comando para uma categoria, deixar TODO explícito.

**Permissões seguem menor privilégio.** Prefixo específico, nunca tool inteira — `Bash(dotnet build:*)` e jamais `Bash` ou `Bash(*)`. O deny universal de segredos entra sempre. E nunca colocar `docs/` em `deny`: o agente lê PRDs, planos e ADRs o tempo todo.

**Permissões só ficam boas depois que existe código.** Em repositório vazio não há stack para detectar — nesse caso, gerar apenas o deny universal e as regras de git, e avisar que vale rodar de novo após o scaffolding.

## Ao final

Reportar:

- Arquivos criados, atualizados e inalterados (`CLAUDE.md` e/ou `settings.json`)
- Drift detectado (stack divergente, comando quebrado, link morto, padrão emergente não documentado)
- Lacunas que ficaram como TODO e o motivo
- Módulos detectados que não receberam `CLAUDE.md`, com o motivo
- Regras de permissão adicionadas, por balde, e divergências encontradas sem alteração

## Quando este comando é útil

- Logo após a proposta arquitetural ficar pronta (semear o contexto do projeto)
- **Depois do primeiro scaffolding** — o momento mais importante: é quando a stack e os comandos de build/teste passam a existir, e as permissões podem ser calibradas de verdade
- Quando um review apontou padrão emergente ainda não documentado
- Quando o `reviewer-leanwork` rodou em modo degradado por falta de `CLAUDE.md`
- Periodicamente, em modo `auditar`, para detectar drift antes que ele confunda o agente
