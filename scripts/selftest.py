#!/usr/bin/env python3
"""Selftest dos validadores do pipeline SDD Leanwork.

Gera artefatos-fixture em diretorio temporario, roda cada validador como
subprocesso e confere o exit code e a mensagem esperada. Cobre, para cada
validador, um fixture valido e um fixture por modo de falha declarado, mais as
quatro rotas de resolucao de alvo do harness.

Todo fixture invalido carrega, na primeira linha, a regra que ele viola -
fixture sem explicacao vira fixture que ninguem sabe se ainda testa algo.

Uso:
    python scripts/selftest.py [--verbose]

Exit: 0 se todos os casos passaram, 1 se algum falhou.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = "selftest"
SCRIPTS_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def marker(rule):
    return "<!-- FIXTURE INVÁLIDO: viola {} -->\n\n".format(rule)


def build_plan(task_count=3, with_map=False):
    """Plano minimo e valido, com `task_count` tarefas sequenciais."""
    header = [
        "# Plano de Execução: Fixture de selftest",
        "",
        "**Cliente/Produto:** Fixture",
        "**Status:** Rascunho",
        "",
        "## 1. Resumo executivo",
        "",
        "Plano sintetico usado pelo selftest dos validadores.",
        "",
        "## 2. Estratégia de entrega",
        "",
        "**Modelo de entrega:** incremental por fase.",
        "",
    ]

    if with_map:
        header += [
            "## 4. Mapa de dependências",
            "",
            "```mermaid",
            "graph TD",
            "    T01[T-01 base] --> T02[T-02 consumo]",
            "```",
            "",
        ]

    body = ["## 5. Fases", "", "### Fase 1 — Fundação", "", "**Objetivo da fase:** uma frase.", ""]

    for number in range(1, task_count + 1):
        depends = "nenhuma" if number == 1 else "T-{:02d}".format(number - 1)
        body += [
            "---",
            "",
            "#### T-{:02d} — Tarefa número {}".format(number, number),
            "",
            "- **Status:** Pendente",
            "- **Complexidade:** Baixa",
            "- **Depende de:** {}".format(depends),
            "- **Camadas/arquivos afetados:**",
            "  - `src/modulo{}` *(novo)*".format(number),
            "",
            "**Descrição:**",
            "Faz a parte {} do trabalho.".format(number),
            "",
            "**Critério de aceite (testável):**",
            "- [ ] O módulo {} responde ao caso principal".format(number),
            "",
            "**Testes a escrever:**",
            "- *Unit:* módulo {} rejeita entrada vazia".format(number),
            "",
        ]

    footer = [
        "## 7. Checklist de prontidão para produção",
        "",
        "- [ ] Testes passando",
        "",
        "## 9. Pontos de validação humana",
        "",
        "- [ ] Após a Fase 1 — revisar com o time",
        "",
        "## 11. Histórico de execução",
        "",
        "| Tarefa | Status | Concluída em | Commit | Observação |",
        "|--------|--------|--------------|--------|------------|",
    ]
    for number in range(1, task_count + 1):
        footer.append("| T-{:02d} | Pendente | — | — | — |".format(number))
    footer.append("")

    return "\n".join(header + body + footer)


def build_traceable_plan():
    """Plano que cita IDs das quatro classes, para exercitar validate_ids."""
    plan = build_plan(task_count=2)
    return plan.replace(
        "- **Depende de:** nenhuma\n",
        "- **Depende de:** nenhuma\n"
        "- **Implementa:** RN-01\n"
        "- **Valida:** CA-01\n"
        "- **Decisões base:** ADR-01\n"
        "- **Telas:** UI-01 (default, vazio)\n",
        1,
    )


PRD = """# PRD-001 — Fixture

## 8. Regras de negócio

- **RN-01:** o saldo nunca fica negativo

## 9. Critérios de aceite

```gherkin
Funcionalidade: Saque

  Cenário [CA-01]: saque dentro do saldo
    Dado que o cliente tem saldo (RN-01)
    Quando ele saca um valor menor
    Então o saque é aceito
```
"""

ARCHITECTURE = """# Proposta Arquitetural — Fixture

## 5. Decisões arquiteturais

### ADR-01: Separar domínio de infraestrutura

Contexto, decisão e consequências.
"""

SPEC_UI = """# SPEC-UI-001 — Fixture

## 3. Telas

### UI-01 — Tela de saque

| Estado | ID | Condição | Comportamento | Origem |
|---|---|---|---|---|
| Padrão | `UI-01.default` | Saldo disponível | Formulário de saque | Protótipo |
| Vazio | `UI-01.vazio` | Sem conta ativa | Mensagem orientando abertura | Protótipo |
"""


REVIEW = """# Review: T-01 — Tarefa número 1

> **Plano de referência:** docs/plans/PLAN-001-fixture.md
> **PRD de referência:** docs/prds/PRD-001-fixture.md
> **Reviewer:** Claude (skill `reviewer-leanwork`)
> **Data:** 2026-09-22
> **Round:** 1
> **Recomendação final:** ⚠️ Aprovado com ressalvas

---

## Sumário executivo

A tarefa entrega o escopo prometido, com uma ressalva de legibilidade.

---

## Findings detalhados

### 🟡 Importantes

#### R-01 — Nome de variável não descreve o que guarda

- **Eixo:** 5. Qualidade do código
- **Evidência:** `src/modulo1.py:42`
- **Descrição:** a variável `x` guarda o saldo disponível.
- **Sugestão de correção:** renomear para `saldoDisponivel`.

---

## Cobertura por RN (Implementa)

### RN-01 — o saldo nunca fica negativo

- **Como foi implementada:** guarda no serviço de saque.
- **Evidência:** `src/modulo1.py:30`
- **Asserção:** `assert saldo - valor >= 0`
- **Status:** ✅ Implementada corretamente

---

## Cobertura por CA (Valida)

### CA-01 — saque dentro do saldo

- **Teste:** `tests/test_modulo1.py:12`
- **Asserção:** `assert resposta.status == 200`
- **Cobre o cenário completo?** Sim — Dado/Quando/Então mapeados
- **Status:** ✅

---

## Verificação da Decisão Arquitetural

### ADR-01 — Separar domínio de infraestrutura

- **Decisão original:** domínio não conhece infraestrutura.
- **Implementação:** `src/modulo1.py:1`
- **Conformidade:** ✅ respeitada

---

## Sensor de discriminação

**Profundidade:** padrão (1-3)
**Isolamento:** git worktree
**Resultado:** 2/2 mortos

| # | Arquivo:linha | Mutação aplicada | Morto? |
|---|---|---|---|
| 1 | `src/modulo1.py:42` | Condição `saldo > 0` invertida para `saldo >= 0` | ✅ Morto |
| 2 | `src/modulo1.py:30` | Retorno trocado de 200 para 204 | ✅ Morto |

---

## Conclusão

Endereçar R-01 antes do merge.
"""


# --------------------------------------------------------------------------
# Montagem dos casos
# --------------------------------------------------------------------------


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def plan_setup(content):
    def setup(workspace):
        write(workspace / "docs" / "plans" / "PLAN-001-fixture.md", content)

    return setup


def traceable_setup(plan_content, prd=PRD, architecture=ARCHITECTURE, spec_ui=SPEC_UI):
    def setup(workspace):
        write(workspace / "docs" / "plans" / "PLAN-001-fixture.md", plan_content)
        if prd is not None:
            write(workspace / "docs" / "prds" / "PRD-001-fixture.md", prd)
        if architecture is not None:
            write(
                workspace / "docs" / "architecture" / "proposta-arquitetural.md",
                architecture,
            )
        if spec_ui is not None:
            write(workspace / "docs" / "prototype" / "SPEC-UI-001-fixture.md", spec_ui)

    return setup


def review_setup(content, name="REVIEW-T-01-2026-09-22.md"):
    def setup(workspace):
        write(workspace / "docs" / "reviews" / name, content)

    return setup


PLAN_ARGV = lambda w: [str(w / "docs" / "plans" / "PLAN-001-fixture.md")]
IDS_ARGV = lambda w: [
    str(w / "docs" / "plans" / "PLAN-001-fixture.md"),
    "--root",
    str(w),
]
REVIEW_ARGV = lambda w: [str(w / "docs" / "reviews" / "REVIEW-T-01-2026-09-22.md")]


def plan_case(name, rule, mutate, exit_code, expect, argv=PLAN_ARGV, base=None):
    content = base if base is not None else build_plan()
    content = mutate(content) if mutate else content
    if exit_code == 1:
        content = marker(rule) + content
    return {
        "name": name,
        "rule": rule,
        "script": "validate_plan.py",
        "setup": plan_setup(content),
        "argv": argv,
        "exit": exit_code,
        "expect": expect,
    }


def ids_case(name, rule, plan_content, exit_code, expect, **sources):
    if exit_code == 1:
        plan_content = marker(rule) + plan_content
    return {
        "name": name,
        "rule": rule,
        "script": "validate_ids.py",
        "setup": traceable_setup(plan_content, **sources),
        "argv": IDS_ARGV,
        "exit": exit_code,
        "expect": expect,
    }


def review_case(name, rule, mutate, exit_code, expect, filename=None):
    content = mutate(REVIEW) if mutate else REVIEW
    if exit_code == 1:
        content = marker(rule) + content
    file_name = filename or "REVIEW-T-01-2026-09-22.md"
    return {
        "name": name,
        "rule": rule,
        "script": "validate_review.py",
        "setup": review_setup(content, file_name),
        "argv": lambda w: [str(w / "docs" / "reviews" / file_name)],
        "exit": exit_code,
        "expect": expect,
    }


def drop(needle):
    return lambda text: "\n".join(
        line for line in text.split("\n") if needle not in line
    )


def swap(old, new, count=1):
    return lambda text: text.replace(old, new, count)


def build_cases():
    cases = []

    # -- validate_plan: caso valido ---------------------------------------
    cases.append(
        plan_case("plan_valido", "—", None, 0, "0 error(s), 0 warning(s)")
    )

    # -- validate_plan: um caso por ERROR declarado em T-02 ---------------
    cases.append(
        plan_case(
            "plan_secao_ausente",
            "seção obrigatória ausente",
            drop("## 7. Checklist de prontidão para produção"),
            1,
            "secao obrigatoria ausente: 'Checklist de prontidão'",
        )
    )
    cases.append(
        plan_case(
            "plan_status_ausente",
            "tarefa sem campo Status",
            drop("- **Status:** Pendente"),
            1,
            "campo obrigatorio ausente: '**Status:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_status_fora_do_vocabulario",
            "Status fora do vocabulário fixo",
            swap("- **Status:** Pendente", "- **Status:** Feito"),
            1,
            "Status 'Feito' fora do vocabulario fixo",
        )
    )
    cases.append(
        plan_case(
            "plan_status_como_checkbox",
            "Status representado como checkbox",
            swap("- **Status:** Pendente", "- [ ] **Status:** Pendente"),
            1,
            "Status representado como checkbox",
        )
    )
    cases.append(
        plan_case(
            "plan_complexidade_ausente",
            "tarefa sem campo Complexidade",
            drop("- **Complexidade:** Baixa"),
            1,
            "campo obrigatorio ausente: '**Complexidade:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_depende_de_ausente",
            "tarefa sem campo Depende de",
            drop("- **Depende de:**"),
            1,
            "campo obrigatorio ausente: '**Depende de:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_camadas_ausente",
            "tarefa sem campo Camadas/arquivos afetados",
            drop("- **Camadas/arquivos afetados:**"),
            1,
            "campo obrigatorio ausente: '**Camadas/arquivos afetados:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_bloco_criterio_ausente",
            "tarefa sem bloco Critério de aceite",
            drop("**Critério de aceite (testável):**"),
            1,
            "bloco obrigatorio ausente: '**Critério de aceite (testável):**'",
        )
    )
    cases.append(
        plan_case(
            "plan_bloco_testes_ausente",
            "tarefa sem bloco Testes a escrever",
            drop("**Testes a escrever:**"),
            1,
            "bloco obrigatorio ausente: '**Testes a escrever:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_criterio_sem_itens",
            "Critério de aceite sem nenhum item de checkbox",
            swap(
                "- [ ] O módulo 1 responde ao caso principal",
                "O módulo 1 precisa funcionar.",
            ),
            1,
            "sem nenhum item '- [ ]'",
        )
    )
    cases.append(
        plan_case(
            "plan_id_malformado",
            "ID de tarefa fora do padrão T-NN",
            swap("#### T-03 — Tarefa número 3", "#### T-3 — Tarefa número 3"),
            1,
            "ID de tarefa malformado 'T-3'",
        )
    )
    cases.append(
        plan_case(
            "plan_id_duplicado",
            "ID de tarefa repetido",
            swap("#### T-03 — Tarefa número 3", "#### T-02 — Tarefa número 3"),
            1,
            "T-02 duplicado",
        )
    )
    cases.append(
        plan_case(
            "plan_sequencia_com_buraco",
            "sequência de tarefas com buraco",
            swap("#### T-03 — Tarefa número 3", "#### T-05 — Tarefa número 3"),
            1,
            "sequencia de tarefas com buraco",
        )
    )
    cases.append(
        plan_case(
            "plan_dependencia_inexistente",
            "Depende de aponta para tarefa inexistente",
            swap("- **Depende de:** T-02", "- **Depende de:** T-09"),
            1,
            "depende de T-09, que nao existe no plano",
        )
    )
    cases.append(
        plan_case(
            "plan_dependencia_para_frente",
            "dependência para frente",
            swap("- **Depende de:** nenhuma", "- **Depende de:** T-03"),
            1,
            "dependencia para frente",
        )
    )
    cases.append(
        plan_case(
            "plan_historico_divergente",
            "coluna Status do histórico diverge do campo Status",
            swap("| T-02 | Pendente |", "| T-02 | Concluído |"),
            1,
            "consta como 'Concluído' na tabela",
        )
    )

    # -- validate_plan: WARNs nao mudam o exit code -----------------------
    cases.append(
        plan_case(
            "plan_warn_muitos_criterios",
            "—",
            swap(
                "- [ ] O módulo 1 responde ao caso principal",
                "- [ ] Critério um\n- [ ] Critério dois\n- [ ] Critério três\n"
                "- [ ] Critério quatro",
            ),
            0,
            "4 criterios de aceite (limiar 3)",
        )
    )
    cases.append(
        plan_case(
            "plan_warn_sem_mapa_de_dependencias",
            "—",
            None,
            0,
            "sem secao 'Mapa de dependências'",
            base=build_plan(task_count=6),
        )
    )
    cases.append(
        plan_case(
            "plan_warn_placeholder",
            "—",
            swap("**Status:** Rascunho", "**Status:** Rascunho\n**Data:** AAAA-MM-DD"),
            0,
            "placeholder de template nao preenchido: AAAA-MM-DD",
        )
    )
    cases.append(
        plan_case(
            "plan_warn_testes_vazio",
            "—",
            swap("- *Unit:* módulo 1 rejeita entrada vazia", ""),
            0,
            "'Testes a escrever' vazio",
        )
    )
    cases.append(
        plan_case(
            "plan_strict_promove_warn",
            "—",
            swap("**Status:** Rascunho", "**Status:** Rascunho\n**Data:** AAAA-MM-DD"),
            1,
            "1 error(s), 0 warning(s)",
            argv=lambda w: PLAN_ARGV(w) + ["--strict"],
        )
    )
    cases.append(
        plan_case(
            "plan_com_mapa_nao_avisa",
            "—",
            None,
            0,
            "0 error(s), 0 warning(s)",
            base=build_plan(task_count=6, with_map=True),
        )
    )

    # -- rotas de resolucao de alvo (harness de T-01) ---------------------
    cases.append(
        plan_case(
            "rota_diretorio",
            "—",
            None,
            0,
            "0 error(s), 0 warning(s)",
            argv=lambda w: [str(w / "docs" / "plans")],
        )
    )
    cases.append(
        plan_case(
            "rota_auto_deteccao",
            "—",
            None,
            0,
            "0 error(s), 0 warning(s)",
            argv=lambda w: ["--root", str(w)],
        )
    )
    cases.append(
        {
            "name": "rota_ambiguidade",
            "rule": "dois planos candidatos no mesmo diretório",
            "script": "validate_plan.py",
            "setup": lambda w: (
                write(w / "docs" / "plans" / "PLAN-001-fixture.md", build_plan()),
                write(w / "docs" / "plans" / "PLAN-002-outro.md", build_plan()),
            ),
            "argv": lambda w: ["--root", str(w)],
            "exit": 2,
            "expect": "mais de um plano encontrado",
        }
    )
    cases.append(
        {
            "name": "rota_alvo_inexistente",
            "rule": "alvo informado não existe",
            "script": "validate_plan.py",
            "setup": lambda w: None,
            "argv": lambda w: [str(w / "docs" / "plans" / "NAO-EXISTE.md")],
            "exit": 2,
            "expect": "plano nao encontrado",
        }
    )

    # -- validate_ids -----------------------------------------------------
    cases.append(
        ids_case(
            "ids_valido",
            "—",
            build_traceable_plan(),
            0,
            "0 error(s), 0 warning(s)",
        )
    )
    cases.append(
        ids_case(
            "ids_sem_spec_ui_e_sem_telas",
            "—",
            build_plan(task_count=2),
            0,
            "0 error(s), 0 warning(s)",
            prd=None,
            architecture=None,
            spec_ui=None,
        )
    )
    cases.append(
        ids_case(
            "ids_rn_inexistente",
            "RN citado no plano não existe no PRD",
            build_traceable_plan().replace("- **Implementa:** RN-01", "- **Implementa:** RN-09"),
            1,
            "RN-09 nao existe em PRD-001-fixture.md",
        )
    )
    cases.append(
        ids_case(
            "ids_ca_inexistente",
            "CA citado no plano não existe no PRD",
            build_traceable_plan().replace("- **Valida:** CA-01", "- **Valida:** CA-09"),
            1,
            "CA-09 nao existe em PRD-001-fixture.md",
        )
    )
    cases.append(
        ids_case(
            "ids_adr_inexistente",
            "ADR citado no plano não existe na arquitetura",
            build_traceable_plan().replace(
                "- **Decisões base:** ADR-01", "- **Decisões base:** ADR-09"
            ),
            1,
            "ADR-09 nao existe em proposta-arquitetural.md",
        )
    )
    cases.append(
        ids_case(
            "ids_tela_inexistente",
            "tela citada no plano não existe na SPEC-UI",
            build_traceable_plan().replace(
                "- **Telas:** UI-01 (default, vazio)", "- **Telas:** UI-09 (default)"
            ),
            1,
            "UI-09 nao existe em SPEC-UI-001-fixture.md",
        )
    )
    cases.append(
        ids_case(
            "ids_estado_de_tela_inexistente",
            "estado de tela citado não é definido pela SPEC-UI",
            build_traceable_plan().replace(
                "- **Telas:** UI-01 (default, vazio)",
                "- **Telas:** UI-01 (default, esgotado)",
            ),
            1,
            "estado 'UI-01.esgotado' nao esta definido na SPEC-UI",
        )
    )
    cases.append(
        ids_case(
            "ids_malformado",
            "ID fora do padrão de numeração",
            build_traceable_plan().replace("- **Implementa:** RN-01", "- **Implementa:** RN-1"),
            1,
            "ID malformado em 'Implementa:' -> 'RN-1'",
        )
    )
    cases.append(
        ids_case(
            "ids_warn_artefato_ausente",
            "—",
            build_traceable_plan(),
            0,
            "verificacao de RN pulada",
            prd=None,
        )
    )
    cases.append(
        ids_case(
            "ids_warn_gap_de_cobertura",
            "—",
            build_traceable_plan(),
            0,
            "RN definido(s) no PRD que nenhuma tarefa do plano cita: RN-02",
            prd=PRD.replace(
                "- **RN-01:** o saldo nunca fica negativo",
                "- **RN-01:** o saldo nunca fica negativo\n"
                "- **RN-02:** o extrato registra todo saque",
            ),
        )
    )

    # -- validate_review --------------------------------------------------
    cases.append(review_case("review_valido", "—", None, 0, "0 error(s), 0 warning(s)"))
    cases.append(
        review_case(
            "review_recomendacao_placeholder",
            "recomendação final ainda no placeholder",
            swap(
                "**Recomendação final:** ⚠️ Aprovado com ressalvas",
                "**Recomendação final:** [✅ Aprovado / ⚠️ Aprovado com ressalvas / ⛔ Bloqueado]",
            ),
            1,
            "recomendacao final ainda no placeholder",
        )
    )
    cases.append(
        review_case(
            "review_recomendacao_fora_do_vocabulario",
            "recomendação final fora do vocabulário",
            swap(
                "**Recomendação final:** ⚠️ Aprovado com ressalvas",
                "**Recomendação final:** Aprovadíssimo",
            ),
            1,
            "fora do vocabulario",
        )
    )
    cases.append(
        review_case(
            "review_recomendacao_ausente",
            "recomendação final ausente",
            drop("**Recomendação final:**"),
            1,
            "recomendacao final ausente",
        )
    )
    cases.append(
        review_case(
            "review_bloqueante_sem_bloqueado",
            "finding Bloqueante com recomendação diferente de Bloqueado",
            swap("### 🟡 Importantes", "### 🔴 Bloqueantes"),
            1,
            "incoerencia de severidade: 1 finding(s) Bloqueante(s)",
        )
    )
    cases.append(
        review_case(
            "review_aprovado_com_finding",
            "recomendação Aprovado com finding aberto",
            swap(
                "**Recomendação final:** ⚠️ Aprovado com ressalvas",
                "**Recomendação final:** ✅ Aprovado",
            ),
            1,
            "recomendacao 'Aprovado' com 1 finding(s)",
        )
    )
    cases.append(
        review_case(
            "review_finding_sem_evidencia",
            "finding sem campo de evidência",
            drop("- **Evidência:** `src/modulo1.py:42`"),
            1,
            "R-01 (linha 24): sem campo '**Evidência:**'",
        )
    )
    cases.append(
        review_case(
            "review_evidencia_sem_arquivo_linha",
            "evidência de finding sem citação arquivo:linha",
            swap(
                "- **Evidência:** `src/modulo1.py:42`",
                "- **Evidência:** o handler de saque",
            ),
            1,
            "evidencia sem citacao arquivo:linha",
        )
    )
    cases.append(
        review_case(
            "review_ausencia_objetiva_aceita",
            "—",
            swap(
                "- **Evidência:** `src/modulo1.py:42`",
                "- **Evidência:** não existe teste cobrindo CA-01",
            ),
            0,
            "0 error(s), 0 warning(s)",
        )
    )
    cases.append(
        review_case(
            "review_ausencia_generica_recusada",
            "ausência declarada sem nomear o alvo",
            lambda text: text.replace(
                "- **Evidência:** `src/modulo1.py:42`", "- **Evidência:** ausente"
            ).replace("a variável `x` guarda o saldo disponível.", "não deu tempo."),
            1,
            "evidencia sem citacao arquivo:linha",
        )
    )
    cases.append(
        review_case(
            "review_ca_sem_evidencia",
            "CA marcado como coberto citando só o nome do teste",
            lambda text: text.replace(
                "- **Teste:** `tests/test_modulo1.py:12`",
                "- **Teste correspondente:** `tests/test_modulo1.py::CA_01_saque_ok`",
            ).replace("- **Asserção:** `assert resposta.status == 200`\n", ""),
            1,
            "CA-01 (Cobertura por CA",
        )
    )
    cases.append(
        review_case(
            "review_rn_sem_evidencia",
            "RN marcado como coberto sem citação arquivo:linha",
            lambda text: text.replace(
                "- **Evidência:** `src/modulo1.py:30`",
                "- **Evidência:** serviço de saque",
            ).replace("- **Asserção:** `assert saldo - valor >= 0`\n", ""),
            1,
            "RN-01 (Cobertura por RN",
        )
    )
    cases.append(
        review_case(
            "review_adr_sem_evidencia",
            "ADR marcado como conforme sem citação arquivo:linha",
            swap(
                "- **Implementação:** `src/modulo1.py:1`",
                "- **Implementação:** respeitada no serviço",
            ),
            1,
            "ADR-01 (Verificação da Decisão Arquitetural",
        )
    )
    cases.append(
        review_case(
            "review_finding_malformado",
            "ID de finding fora do padrão R-NN",
            swap("#### R-01 —", "#### R-1 —"),
            1,
            "ID de finding malformado 'R-1'",
        )
    )
    cases.append(
        review_case(
            "review_finding_duplicado",
            "ID de finding repetido",
            swap(
                "#### R-01 — Nome de variável não descreve o que guarda",
                "#### R-01 — Primeiro finding\n\n"
                "- **Eixo:** 5. Qualidade do código\n"
                "- **Evidência:** `src/modulo1.py:50`\n\n"
                "#### R-01 — Nome de variável não descreve o que guarda",
            ),
            1,
            "R-01 duplicado",
        )
    )
    cases.append(
        review_case(
            "review_finding_nao_comeca_em_r01",
            "numeração de findings não começa em R-01",
            swap("#### R-01 —", "#### R-02 —"),
            1,
            "numeracao de findings comeca em R-02",
        )
    )
    cases.append(
        review_case(
            "review_placeholder",
            "placeholder de template remanescente",
            swap(
                "A tarefa entrega o escopo prometido, com uma ressalva de legibilidade.",
                "[resumo do que foi entregue nesta tarefa]",
            ),
            1,
            "placeholder de template nao preenchido",
        )
    )
    cases.append(
        review_case(
            "review_sensor_sobrevivente_sem_bloqueante",
            "mutante sobrevivente apontando para finding que não é Bloqueante",
            swap(
                "| 2 | `src/modulo1.py:30` | Retorno trocado de 200 para 204 | ✅ Morto |",
                "| 2 | `src/modulo1.py:30` | Retorno trocado de 200 para 204 | ❌ Sobreviveu → R-01 |",
            ),
            1,
            "aponta para R-01, que nao e Bloqueante",
        )
    )
    cases.append(
        review_case(
            "review_sensor_sobrevivente_sem_finding",
            "mutante sobrevivente sem finding correspondente",
            swap(
                "| 2 | `src/modulo1.py:30` | Retorno trocado de 200 para 204 | ✅ Morto |",
                "| 2 | `src/modulo1.py:30` | Retorno trocado de 200 para 204 | ❌ Sobreviveu |",
            ),
            1,
            "mutante sobrevivente sem R-XX correspondente",
        )
    )
    cases.append(
        review_case(
            "review_sensor_ausente_apenas_avisa",
            "—",
            lambda text: text.split("## Sensor de discriminação")[0]
            + "## Conclusão\n\nEndereçar R-01 antes do merge.\n",
            0,
            "secao 'Sensor de discriminação' ausente",
        )
    )
    cases.append(
        review_case(
            "review_sem_findings_avisa",
            "—",
            lambda text: text.replace(
                text[text.index("### 🟡 Importantes") : text.index("---\n\n## Cobertura por RN")],
                "",
            ).replace("**Recomendação final:** ⚠️ Aprovado com ressalvas", "**Recomendação final:** ✅ Aprovado"),
            0,
            "relatorio sem nenhum finding R-XX",
        )
    )
    cases.append(
        review_case(
            "review_round_sem_secao_anterior",
            "—",
            None,
            0,
            "sem secao 'Round anterior'",
            filename="REVIEW-T-01-2026-09-22-round2.md",
        )
    )

    return cases


# --------------------------------------------------------------------------
# Execução
# --------------------------------------------------------------------------


def run_case(case, root, verbose):
    workspace = root / case["name"]
    workspace.mkdir(parents=True, exist_ok=True)
    case["setup"](workspace)

    command = [sys.executable, str(SCRIPTS_DIR / case["script"])] + case["argv"](
        workspace
    )
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout or ""

    problems = []
    if completed.returncode != case["exit"]:
        problems.append(
            "exit {} (esperado {})".format(completed.returncode, case["exit"])
        )
    if case["expect"] not in output:
        problems.append("saida nao contem '{}'".format(case["expect"]))

    if verbose and not problems:
        sys.stdout.write("  ok   {}\n".format(case["name"]))

    if problems:
        sys.stdout.write("  FAIL {} — {}\n".format(case["name"], "; ".join(problems)))
        sys.stdout.write("       regra violada pelo fixture: {}\n".format(case["rule"]))
        for line in output.strip().split("\n"):
            sys.stdout.write("       | {}\n".format(line))
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=SCRIPT, description="Selftest dos validadores do pipeline SDD."
    )
    parser.add_argument("--verbose", action="store_true", help="lista cada caso")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass

    cases = build_cases()
    failures = 0

    with tempfile.TemporaryDirectory(prefix="leanwork-selftest-") as temporary:
        root = Path(temporary)
        for case in cases:
            if not run_case(case, root, args.verbose):
                failures += 1

    sys.stdout.write(
        "{}: {} error(s), 0 warning(s) in {} caso(s)\n".format(
            SCRIPT, failures, len(cases)
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
