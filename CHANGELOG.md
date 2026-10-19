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
