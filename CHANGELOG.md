# Changelog

Histórico de versões do plugin `leanwork-sdd`. Formato: versão, data quando registrada, e o que mudou com o motivo.

## [Não publicado] — rumo à 2.0.0

Execução do `docs/plans/PLAN-002-enxugamento-pipeline.md`.

### Gates disparados por hook (T-14)

- `hooks/hooks.json` registra um hook `PostToolUse` (`Write|Edit`) que roda `scripts/hook_gate.py`. Edição em `docs/plans/*.md` dispara `validate_plan.py`; em `docs/reviews/*.md`, `validate_review.py`. Reprovação sai com exit 2 e o stderr volta ao modelo, que corrige o artefato. `validate_ids.py` continua chamado por `/leanwork-execute`, porque não depende de edição.
- Planner, `/leanwork-execute` e `/leanwork-review` descrevem o gate em três linhas: hook, fallback por linha de comando, fallback manual declarado.
- **Teste manual (2026-10-19, Claude Code 2.1.292, Windows 11):** `claude -p --plugin-dir .` num projeto descartável com um plano válido.
  - Edição que troca `Status: Pendente` por `Status: Feito` → o modelo recebeu `hook_gate: validate_plan.py reprovou PLAN-001-fixture.md` com o `ERROR T-01 (linha 17): Status 'Feito' fora do vocabulario fixo`.
  - Edição seguinte para `Status: Em andamento` → nenhum retorno do hook.
- `selftest.py` ganha cinco casos do hook: plano válido, plano inválido, review inválido, arquivo fora do escopo e entrada ilegível.

### Justificativas escritas uma vez (T-15)

- "Degradação silenciosa é pior que gate nenhum" fica por extenso no README (seção dos gates). Planner, `/leanwork-execute` e `/leanwork-review` mantêm a regra em uma linha, com remissão.
- "Sombra de prefixo entre baldes" fica só no `permission-catalog.md`. Os três arquivos com gate guardam a regra operacional em uma linha: confirmar ou ajustar as settings, nunca pular a validação.
- A tabela "Quem sugere" fica no README, unificada para `context-leanwork` e `prototype-leanwork`. As duas skills apontam para ela e mantêm a regra de nunca rodar como efeito colateral.

### Descriptions curtas e regras pinadas (T-16)

- A `description` de cada skill fica só com gatilhos e exclusões. A soma das seis caiu de 6.437 para 2.006 caracteres; a linha de base de 2026-10-16 era 6.683.
- Cada SKILL ganha uma seção **Regras pinadas**, com 4 ou 5 itens: o que não se negocia na skill. O restante do texto perde caixa alta e negrito de alarme: `NUNCA`/`PARE`/`NÃO` em caixa alta caem de 18 ocorrências para 0 fora das regras pinadas.

### Entrevistas: busca antes de pergunta (T-17)

- Architect, PRD, planner e prototype declaram a mesma regra. Fato se busca no repositório, no `CLAUDE.md`, nos artefatos e na conversa. Decisão se pergunta, no máximo duas por vez, com opções concretas e a recomendação marcada.
- Os blocos de perguntas viraram **dimensões a cobrir**. Cada dimensão termina respondida ou marcada `n/a — motivo`; sem isso, é lacuna e impede a geração. Todas as dimensões anteriores foram mantidas.
- Na prototype, a pergunta de modo (ingestão, geração, híbrido) vem com a recomendação tirada do que a busca encontrou.

### Architect e PRD sem conteúdo de livro-texto (T-18)

- `skills/architect-leanwork/SKILL.md`: 248 → 147 linhas. Saíram a explicação de Cynefin (fica a consequência prática), a lista genérica de trade-offs, a lista de isomorfismos (está em `architectural-styles.md`), a explicação dos níveis do C4 e os princípios de escrita genéricos. Ficaram as posições Leanwork: restrição como restrição, sem modismo, sem estimativa, regra de escolha do nível C4 e o checklist final. Os catálogos em `references/` não mudaram.
- PRD: a hierarquia Epic → Feature → PBI passa a opcional, para quem cadastra no Azure DevOps, na SKILL e no template. O template perde a seção 7.2 (fluxos alternativos e de erro), que redescrevia os cenários `CA-XX`. A numeração das seções foi mantida porque `id-conventions.md` cita as seções 8 e 9.
- `REFERENCES.md`: a entrada de Cynefin passa de reprodução a adaptação.
