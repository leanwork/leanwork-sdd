---
description: Gera ou atualiza os arquivos CLAUDE.md (raiz e módulos) com contexto do projeto para agentes de IA.
argument-hint: [raiz | modulo <nome> | auditar — opcional]
---

# Contexto do projeto para agentes de IA

Gerar ou atualizar os arquivos `CLAUDE.md` que dão contexto de projeto ao agente: Resumo, Stack, Comandos, Convenções, Restrições e índice da documentação.

Escopo solicitado: $ARGUMENTS

## O que fazer

Invoque a skill `context-leanwork`, que conduz o fluxo completo. Se o usuário passou argumento, use-o para pular a pergunta de escopo:

- `raiz` → gerar/atualizar apenas o `CLAUDE.md` da raiz
- `modulo <nome>` → gerar/atualizar apenas o módulo indicado
- `auditar` → modo somente-leitura: reportar drift e lacunas sem gravar nada
- *(vazio)* → a skill pergunta o escopo

## Regras que valem sempre

**Nunca sobrescrever conteúdo humano.** A skill faz merge apenas dentro dos blocos delimitados por `<!-- leanwork-context:start -->` e `<!-- leanwork-context:end -->`. Arquivo sem esses marcadores foi escrito à mão: propor alternativas ao usuário, nunca decidir por ele.

**Sempre mostrar o diff antes de gravar.** Mesmo quando a mudança parecer trivial.

**Módulos são opt-in.** Detectar e listar os módulos, deixar o usuário escolher. Nunca gerar para todos de uma vez sem escolha explícita — projeto com 8 módulos vira 8 arquivos, e vários deles só ruído.

**Não inventar comandos.** A seção Comandos vem de inspeção real do repositório (`package.json`, `Makefile`, `.csproj`, etc.). Quando não houver comando para uma categoria, deixar TODO explícito.

## Ao final

Reportar:

- Arquivos criados, atualizados e inalterados
- Drift detectado (stack divergente, comando quebrado, link morto, padrão emergente não documentado)
- Lacunas que ficaram como TODO e o motivo
- Módulos detectados que não receberam `CLAUDE.md`, com o motivo

## Quando este comando é útil

- Logo após a proposta arquitetural ficar pronta (semear o contexto do projeto)
- Depois do primeiro scaffolding, quando os comandos de build/test passam a existir
- Quando um review apontou padrão emergente ainda não documentado
- Quando o `reviewer-leanwork` rodou em modo degradado por falta de `CLAUDE.md`
- Periodicamente, em modo `auditar`, para detectar drift antes que ele confunda o agente
