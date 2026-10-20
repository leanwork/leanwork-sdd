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
import json
import os
import shutil
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
            "- **Portas de mão única:** nenhuma",
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
        "## 8. Pontos de validação humana",
        "",
        "- [ ] Após a Fase 1 — revisar com o time",
        "",
    ]

    return "\n".join(header + body + footer)


def build_quick_plan(task_count=1):
    """Plano de trilha rapida: sem PRD, sem secoes do plano completo, com o
    cenario CA-01 definido dentro da propria tarefa."""
    lines = [
        "# Plano de Execução: Fixture de trilha rápida",
        "",
        "**PRD de referência:** nenhum — trilha rápida",
        "**Cliente/Produto:** Fixture",
        "**Status:** Rascunho",
        "",
        "## Motivo",
        "",
        "Ajuste pequeno e reversível no saque.",
        "",
    ]
    for number in range(1, task_count + 1):
        lines += [
            "#### T-{:02d} — Ajusta o saque {}".format(number, number),
            "",
            "- **Status:** Pendente",
            "- **Complexidade:** Baixa",
            "- **Depende de:** nenhuma",
            "- **Valida:** CA-01",
            "- **Portas de mão única:** nenhuma",
            "",
            "**Cenários:**",
            "",
            "```gherkin",
            "  Cenário [CA-01]: saque dentro do saldo",
            "    Dado que o cliente tem saldo",
            "    Quando ele saca um valor menor",
            "    Então o saque é aceito",
            "```",
            "",
            "**Critério de aceite (testável):**",
            "- Cenário CA-01 passa",
            "",
            "**Testes a escrever:**",
            "- *Unit:* CA_01_saque_dentro_do_saldo",
            "",
        ]
    return "\n".join(lines)


STATUS_FIXTURE = {
    # tarefa: (status, depende de, extra)
    1: ("Concluído", "nenhuma", ""),  # review bloqueado no round 1, aprovado no round 2
    2: ("Concluído", "nenhuma", ""),  # sem review
    3: ("Concluído", "nenhuma", ""),  # review bloqueado, sem round seguinte
    4: ("Em andamento", "nenhuma", ""),
    5: ("Bloqueado", "nenhuma", "- **Bloqueio:** R-01 (REVIEW-T-05-2026-09-20)\n"),
    6: ("Pendente", "T-04", ""),  # dependencia nao concluida: nao elegivel
    7: ("Pendente", "T-02", ""),  # elegivel
    8: ("Done", "nenhuma", ""),  # fora do vocabulario
}


def build_status_project(workspace):
    plan = build_plan(task_count=len(STATUS_FIXTURE), with_map=True)
    for number, (status, depends, extra) in STATUS_FIXTURE.items():
        previous = "nenhuma" if number == 1 else "T-{:02d}".format(number - 1)
        plan = plan.replace(
            "#### T-{0:02d} — Tarefa número {0}\n\n- **Status:** Pendente\n"
            "- **Complexidade:** Baixa\n- **Depende de:** {1}\n".format(number, previous),
            "#### T-{0:02d} — Tarefa número {0}\n\n- **Status:** {1}\n{3}"
            "- **Complexidade:** Baixa\n- **Depende de:** {2}\n".format(
                number, status, depends, extra
            ),
        )
    write(workspace / "docs" / "plans" / "PLAN-001-fixture.md", plan)
    write(workspace / "docs" / "prds" / "PRD-001-fixture.md", PRD)
    write(workspace / "docs" / "architecture" / "proposta-arquitetural.md", ARCHITECTURE)
    write(workspace / "CLAUDE.md", "# Fixture\n")

    def review(recommendation):
        return REVIEW.replace("⚠️ Aprovado com ressalvas", recommendation)

    reviews = workspace / "docs" / "reviews"
    write(reviews / "REVIEW-T-01-2026-09-20.md", review("⛔ Bloqueado"))
    write(reviews / "REVIEW-T-01-2026-09-21-round2.md", review("✅ Aprovado"))
    write(reviews / "REVIEW-T-03-2026-09-21.md", review("⛔ Bloqueado"))
    write(reviews / "notas-soltas-do-review.md", "fora da convenção\n")
    write(reviews / "REVIEW-sem-tarefa.md", "fora da convenção\n")


def check_status_json(report):
    plan = report["planos"][0]
    expected = {
        "concluidas_sem_review": ["T-02"],
        "em_andamento": ["T-04"],
        "bloqueadas": [{"id": "T-05", "bloqueio": "R-01 (REVIEW-T-05-2026-09-20)"}],
        "reviews_bloqueados_abertos": [
            {"id": "T-03", "review": "REVIEW-T-03-2026-09-21.md", "status": "Concluído"}
        ],
        "status_fora_do_vocabulario": [{"id": "T-08", "status": "Done"}],
        "proxima": {"id": "T-07", "titulo": "Tarefa número 7"},
        "trilha_rapida": False,
    }
    problems = []
    for key, value in expected.items():
        if plan[key] != value:
            problems.append("{}: {!r} (esperado {!r})".format(key, plan[key], value))
    art = report["artefatos"]
    if not (art["arquitetura"] and art["adrs"] == ["ADR-01"] and art["claude_md"]):
        problems.append("artefatos: {!r}".format(art))
    if report["reviews_fora_da_convencao"] != ["REVIEW-sem-tarefa.md"]:
        problems.append("reviews_fora_da_convencao: {!r}".format(report["reviews_fora_da_convencao"]))
    return problems


TRACE_PRD = """# PRD-001 — Fixture de trace

## 8. Regras de negócio

- **RN-01:** o saldo nunca fica negativo (ADR-01)
- **RN-02:** saque noturno tem limite

## 9. Critérios de aceite

```gherkin
Funcionalidade: Saque

  Cenário [CA-01]: saque dentro do saldo
    Dado que o cliente tem saldo (RN-01)
    Então o saque é aceito

  Cenário [CA-02]: extrato após o saque
    Dado que houve saque
    Então o extrato mostra o lançamento
```
"""

TRACE_ARCHITECTURE = """# Proposta Arquitetural — Fixture

## 5. Decisões arquiteturais

### ADR-01: Separar domínio de infraestrutura

### ADR-02: Cache distribuído
"""

TRACE_SPEC_UI = """# SPEC-UI-001 — Fixture

## 3. Telas

### UI-01 — Tela de saque

| Estado | ID |
|---|---|
| Padrão | `UI-01.default` |
| Vazio | `UI-01.vazio` |

### UI-02 — Extrato

| Estado | ID |
|---|---|
| Padrão | `UI-02.default` |
"""


def build_trace_project(workspace, with_gaps=True):
    """Com `with_gaps`, uma lacuna de cada categoria mecanica; sem, nenhuma."""
    plan = build_plan(task_count=3)
    if with_gaps:
        fields = {
            1: "- **Status:** Concluído\n- **Implementa:** RN-01\n- **Valida:** CA-01\n"
               "- **Decisões base:** ADR-01\n- **Telas:** UI-01 (default)\n",
            2: "- **Status:** Bloqueado\n- **Decisões base:** ADR-09\n",
            3: "- **Status:** Feito\n- **Implementa:** RN-01\n",
        }
    else:
        fields = {
            1: "- **Status:** Concluído\n- **Implementa:** RN-01\n- **Valida:** CA-01\n"
               "- **Decisões base:** ADR-01\n",
            2: "- **Status:** Pendente\n- **Valida:** CA-02\n",
            3: "- **Status:** Pendente\n- **Implementa:** RN-01\n",
        }
    for number, block in fields.items():
        plan = plan.replace(
            "#### T-0{0} — Tarefa número {0}\n\n- **Status:** Pendente\n".format(number),
            "#### T-0{0} — Tarefa número {0}\n\n{1}".format(number, block),
        )
    write(workspace / "docs" / "plans" / "PLAN-001-fixture.md", plan)
    prd = TRACE_PRD if with_gaps else TRACE_PRD.replace(
        "- **RN-02:** saque noturno tem limite\n", ""
    )
    write(workspace / "docs" / "prds" / "PRD-001-fixture.md", prd)
    architecture = TRACE_ARCHITECTURE if with_gaps else TRACE_ARCHITECTURE.replace(
        "\n### ADR-02: Cache distribuído\n", ""
    )
    write(workspace / "docs" / "architecture" / "proposta-arquitetural.md", architecture)
    reviews = workspace / "docs" / "reviews"
    if with_gaps:
        write(workspace / "docs" / "prototype" / "SPEC-UI-001-fixture.md", TRACE_SPEC_UI)
        write(reviews / "REVIEW-T-03-2026-09-21.md",
              REVIEW.replace("⚠️ Aprovado com ressalvas", "⛔ Bloqueado"))
    else:
        write(reviews / "REVIEW-T-01-2026-09-21.md", REVIEW)


TRACE_EXPECTED_GAPS = {
    "rn_sem_cenario": ["RN-02"],
    "ca_sem_tarefa": ["CA-02"],
    "tarefa_sem_rastro": ["T-02"],
    "adr_citado_inexistente": ["ADR-09"],
    "adr_nunca_citado": ["ADR-02"],
    "concluida_sem_review": ["T-01"],
    "review_bloqueado_aberto": ["T-03 (REVIEW-T-03-2026-09-21.md)"],
    "status_fora_do_vocabulario": ["T-03 ('Feito')"],
    "bloqueio_sem_motivo": ["T-02"],
    "tela_sem_tarefa": ["UI-02"],
    "estado_sem_tarefa": ["UI-01.vazio"],
}


def check_trace_gaps(report):
    problems = []
    for key in sorted(set(TRACE_EXPECTED_GAPS) | set(report["lacunas"])):
        got = report["lacunas"].get(key)
        if got != TRACE_EXPECTED_GAPS.get(key):
            problems.append("{}: {!r} (esperado {!r})".format(key, got, TRACE_EXPECTED_GAPS.get(key)))
    row = report["matriz"][0]
    if row != {"ca": "CA-01", "rn": ["RN-01"], "adr": ["ADR-01"], "ui": ["UI-01"],
               "t": ["T-01"], "r": []}:
        problems.append("linha CA-01: {!r}".format(row))
    return problems


def check_trace_clean(report):
    problems = []
    if report["lacunas"]:
        problems.append("lacunas inesperadas: {!r}".format(report["lacunas"]))
    if report["spec_ui"] or any("ui" in row for row in report["matriz"]):
        problems.append("colunas de UI presentes sem SPEC-UI")
    if report["git"] or any("commits" in row for row in report["matriz"]):
        problems.append("coluna de commits presente sem git")
    if not any("sem git" in warning for warning in report["avisos"]):
        problems.append("sem aviso de git ausente: {!r}".format(report["avisos"]))
    return problems


def build_trace_git_project(workspace):
    build_trace_project(workspace, with_gaps=False)
    git = ["git", "-C", str(workspace), "-c", "user.name=selftest",
           "-c", "user.email=selftest@example.invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(git[:3] + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "."], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "Saque dentro do saldo\n\nRefs: T-01, CA-01"],
                   check=True)


def check_trace_git(report):
    commits = report["matriz"][0].get("commits")
    if not report["git"] or not commits or len(commits) != 1:
        return ["commits de CA-01: {!r}".format(commits)]
    return []


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


def write_crlf(path, content):
    """Grava com CRLF explicito, independente da plataforma que roda o selftest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = content.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(body.encode("utf-8"))


def envelope(content, language="markdown"):
    """Embrulha o conteudo no envelope de quatro crases dos arquivos de template.

    A prosa antes do envelope e instrucao para o agente e nao faz parte do
    documento: se `unwrap_envelope` nao a descartasse, todo template seria
    acusado de secao obrigatoria ausente.
    """
    return "\n".join(
        [
            "# Template de fixture",
            "",
            "Instrução para o agente, fora do envelope — não é o documento.",
            "",
            "````" + language,
            content,
            "````",
            "",
        ]
    )


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


def commit_case(name, rule, message, exit_code, expect, as_file=False,
                with_plan=False, strict=False):
    """Caso do check_commit. O fixture invalido e a propria mensagem, entao a
    regra violada vai no campo `rule` em vez de na primeira linha."""

    def setup(workspace):
        if as_file:
            write(workspace / "COMMIT_EDITMSG", message)
        if with_plan:
            write(workspace / "docs" / "plans" / "PLAN-001-fixture.md", build_plan())

    def argv(workspace):
        args = (
            [str(workspace / "COMMIT_EDITMSG")] if as_file else ["--message", message]
        )
        if with_plan:
            args += ["--plan", str(workspace / "docs" / "plans" / "PLAN-001-fixture.md")]
        if strict:
            args.append("--strict")
        return args

    return {
        "name": name,
        "rule": rule,
        "script": "check_commit.py",
        "setup": setup,
        "argv": argv,
        "exit": exit_code,
        "expect": expect,
    }


EXAMPLE = SCRIPTS_DIR.parent / "stacks" / "dotnet" / "pipeline-example.md"
EXAMPLE_TARGETS = {
    "1": "docs/architecture/proposta-arquitetural.md",
    "2": "docs/prds/PRD-001-ofertas-relampago.md",
    "3": "docs/prototype/SPEC-UI-001-ofertas-relampago.md",
    "4": "docs/plans/PLAN-001-ofertas-relampago.md",
    "5": "docs/reviews/REVIEW-T-03-2026-06-15.md",
}
MATRIX_START = "<!-- trace:start -->"
MATRIX_END = "<!-- trace:end -->"


def example_fragments():
    """{numero: conteudo} de cada `## Fragmento N`, sem o envelope de quatro crases."""
    fragments = {}
    current = None
    body = None
    for line in EXAMPLE.read_text(encoding="utf-8").split("\n"):
        if line.startswith("## Fragmento "):
            current = line.split()[2]
            continue
        if current is not None and body is None and line.startswith("````markdown"):
            body = []
            continue
        if body is not None:
            if line.startswith("````"):
                fragments[current] = "\n".join(body) + "\n"
                current, body = None, None
            else:
                body.append(line)
    return fragments


def example_matrix():
    """A matriz publicada no exemplo, entre os marcadores de trace."""
    text = EXAMPLE.read_text(encoding="utf-8")
    start = text.index(MATRIX_START) + len(MATRIX_START)
    return text[start : text.index(MATRIX_END)].strip("\n") + "\n"


def example_setup(workspace):
    for number, content in example_fragments().items():
        write(workspace / EXAMPLE_TARGETS[number], content)


def hook_case(name, rule, setup, file_path, exit_code, expect, raw=None):
    """Caso do hook_gate. O evento do harness chega por stdin; `file_path` e
    relativo ao workspace, que faz o papel do `cwd` da sessao."""

    def stdin(workspace):
        if raw is not None:
            return raw
        return json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Edit",
                "cwd": str(workspace),
                "tool_input": {"file_path": file_path},
            }
        )

    return {
        "name": name,
        "rule": rule,
        "script": "hook_gate.py",
        "setup": setup,
        "argv": lambda w: [],
        "stdin": stdin,
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

    # -- validate_plan: forma de arquivo (envelope e fim de linha) --------
    cases.append(
        plan_case(
            "plan_com_envelope",
            "—",
            None,
            0,
            "0 error(s), 0 warning(s)",
            base=envelope(build_plan()),
        )
    )
    # Nenhum mutante de `read_lines` morre neste caso: toda regex dos
    # validadores termina em `\s*$`, que ja absorve o `\r`. O caso fica como
    # guarda de regressao da propriedade que importa ao usuario Windows - um
    # arquivo CRLF valida limpo - e nao como prova de que a normalizacao pesa.
    cases.append(
        {
            "name": "plan_crlf",
            "rule": "—",
            "script": "validate_plan.py",
            "setup": lambda w: write_crlf(
                w / "docs" / "plans" / "PLAN-001-fixture.md", build_plan()
            ),
            "argv": PLAN_ARGV,
            "exit": 0,
            "expect": "0 error(s), 0 warning(s)",
        }
    )

    # -- validate_plan: um caso por ERROR declarado em T-02 ---------------
    cases.append(
        plan_case(
            "plan_secao_ausente",
            "seção obrigatória ausente",
            drop("## 8. Pontos de validação humana"),
            1,
            "secao obrigatoria ausente: 'Pontos de validação humana'",
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
            "tarefa sem campo Portas de mão única",
            drop("- **Portas de mão única:** nenhuma"),
            1,
            "campo obrigatorio ausente: '**Portas de mão única:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_warn_campo_antigo_de_arquivos",
            "—",
            swap(
                "- **Portas de mão única:** nenhuma",
                "- **Camadas/arquivos afetados:**\n  - `src/modulo1` *(novo)*",
            ),
            0,
            "campo '**Camadas/arquivos afetados:**' e do formato anterior a 2.0.0",
        )
    )
    cases.append(
        plan_case(
            "plan_portas_com_lista",
            "—",
            swap(
                "- **Portas de mão única:** nenhuma",
                "- **Portas de mão única:**\n  - migration — coluna `saldo` nova",
            ),
            0,
            "0 error(s), 0 warning(s)",
        )
    )
    cases.append(
        plan_case(
            "quick_plan_com_porta_de_mao_unica",
            "trilha rápida declarando porta de mão única",
            swap(
                "- **Portas de mão única:** nenhuma",
                "- **Portas de mão única:** migration — coluna `saldo` nova",
            ),
            1,
            "trilha rapida com porta de mao unica declarada",
            base=build_quick_plan(),
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
            "sem nenhum item de lista",
        )
    )
    cases.append(
        plan_case(
            "plan_criterio_vazio",
            "Critério de aceite sem conteúdo",
            swap("- [ ] O módulo 1 responde ao caso principal\n", ""),
            1,
            "sem nenhum item de lista",
        )
    )
    cases.append(
        plan_case(
            "plan_criterio_lista_simples",
            "—",
            lambda plan: plan.replace("- [ ] O módulo", "- O módulo"),
            0,
            "0 error(s), 0 warning(s)",
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
    blocked_heading = "#### T-02 — Tarefa número 2\n\n- **Status:** "
    cases.append(
        plan_case(
            "plan_bloqueado_sem_motivo",
            "Status Bloqueado sem campo Bloqueio",
            swap(blocked_heading + "Pendente", blocked_heading + "Bloqueado"),
            1,
            "Status 'Bloqueado' sem campo '**Bloqueio:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_bloqueado_motivo_vazio",
            "campo Bloqueio sem motivo",
            swap(
                blocked_heading + "Pendente",
                blocked_heading + "Bloqueado\n- **Bloqueio:**",
            ),
            1,
            "sem campo '**Bloqueio:**'",
        )
    )
    cases.append(
        plan_case(
            "plan_bloqueado_com_motivo",
            "—",
            swap(
                blocked_heading + "Pendente",
                blocked_heading + "Bloqueado\n"
                "- **Bloqueio:** R-01 (REVIEW-T-02-2026-09-22)",
            ),
            0,
            "0 error(s), 0 warning(s)",
        )
    )
    cases.append(
        plan_case(
            "plan_historico_legado_ignorado",
            "—",
            lambda plan: plan
            + "\n## 11. Histórico de execução\n\n"
            "| Tarefa | Status | Concluída em | Commit | Observação |\n"
            "|--------|--------|--------------|--------|------------|\n"
            "| T-02 | Concluído | — | — | — |\n",
            0,
            "0 error(s), 0 warning(s)",
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
                "- [ ] Critério quatro\n- [ ] Critério cinco\n- [ ] Critério seis",
            ),
            0,
            "6 criterios de aceite (limiar 5)",
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
            "plan_link_com_barra_nao_e_placeholder",
            "—",
            swap(
                "**Status:** Rascunho",
                "**Status:** Rascunho\n**Fonte:** [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)",
            ),
            0,
            "0 error(s), 0 warning(s)",
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
            "review_com_envelope",
            "—",
            lambda _: envelope(REVIEW),
            0,
            "0 error(s), 0 warning(s)",
        )
    )
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
            "review_ca_sem_assercao",
            "CA com arquivo:linha mas sem a asserção reproduzida",
            drop("- **Asserção:** `assert resposta.status == 200`"),
            1,
            "CA-01 (Cobertura por CA, linha 46): marcado como coberto sem campo "
            "'**Asserção:**'",
        )
    )
    cases.append(
        review_case(
            "review_rn_sem_assercao",
            "RN com arquivo:linha mas sem a asserção reproduzida",
            drop("- **Asserção:** `assert saldo - valor >= 0`"),
            1,
            "RN-01 (Cobertura por RN",
        )
    )
    # A excecao do ADR - conformidade arquitetural nao exige assercao - ja e
    # guardada por `review_valido`, cuja entrada de ADR nao tem o campo.
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

    # -- trilha rapida: validate_plan e validate_ids -----------------------
    no_sources = {"prd": None, "architecture": None, "spec_ui": None}
    cases.append(
        plan_case("quick_plan_valido", "—", None, 0, "0 error(s), 0 warning(s)",
                  base=build_quick_plan())
    )
    cases.append(
        plan_case(
            "quick_plan_duas_tarefas",
            "trilha rápida com mais de uma tarefa",
            None,
            1,
            "plano de trilha rapida com 2 tarefas",
            base=build_quick_plan(task_count=2),
        )
    )
    cases.append(
        plan_case(
            "quick_plan_mantem_rigor_da_tarefa",
            "tarefa da trilha rápida sem Testes a escrever",
            drop("**Testes a escrever:**"),
            1,
            "bloco obrigatorio ausente: '**Testes a escrever:**'",
            base=build_quick_plan(),
        )
    )
    cases.append(
        plan_case(
            "plan_trilha_rapida_so_no_cabecalho",
            "plano completo sem seção obrigatória, com trilha rápida citada no corpo",
            lambda plan: drop("## 8. Pontos de validação humana")(plan).replace(
                "## 1. Resumo executivo\n",
                "## 1. Resumo executivo\n\n"
                "**PRD de referência:** nenhum — trilha rápida\n",
            ),
            1,
            "secao obrigatoria ausente: 'Pontos de validação humana'",
        )
    )
    cases.append(
        ids_case("quick_ids_valido", "—", build_quick_plan(), 0,
                 "0 error(s), 0 warning(s)", **no_sources)
    )
    cases.append(
        ids_case(
            "quick_ids_ca_indefinido",
            "CA citado em Valida e não definido no plano de trilha rápida",
            build_quick_plan().replace("**Valida:** CA-01", "**Valida:** CA-01, CA-02"),
            1,
            "CA-02 nao existe em PLAN-001-fixture.md",
            **no_sources
        )
    )
    cases.append(
        ids_case(
            "quick_ids_ca_definido_nao_citado",
            "—",
            build_quick_plan().replace(
                "    Então o saque é aceito\n",
                "    Então o saque é aceito\n\n"
                "  Cenário [CA-02]: saque acima do saldo\n"
                "    Dado que o cliente tem saldo\n"
                "    Quando ele saca um valor maior\n"
                "    Então o saque é recusado\n",
            ),
            0,
            "CA definido(s) no plano que nenhuma tarefa do plano cita: CA-02",
            **no_sources
        )
    )

    # -- exemplo end-to-end: fragmentos nao podem apodrecer -------------------
    example_root = lambda w: ["--root", str(w)]
    cases.append(
        {
            "name": "exemplo_plano_passa_no_gate",
            "rule": "—",
            "script": "validate_plan.py",
            "setup": example_setup,
            "argv": lambda w: [str(w / EXAMPLE_TARGETS["4"])],
            "exit": 0,
            "expect": "validate_plan: 0 error(s)",
        }
    )
    cases.append(
        {
            "name": "exemplo_ids_existem_na_origem",
            "rule": "—",
            "script": "validate_ids.py",
            "setup": example_setup,
            "argv": lambda w: [str(w / EXAMPLE_TARGETS["4"])] + example_root(w),
            "exit": 0,
            "expect": "validate_ids: 0 error(s)",
        }
    )
    cases.append(
        {
            "name": "exemplo_review_passa_no_gate",
            "rule": "—",
            "script": "validate_review.py",
            "setup": example_setup,
            "argv": lambda w: [str(w / EXAMPLE_TARGETS["5"])],
            "exit": 0,
            "expect": "validate_review: 0 error(s)",
        }
    )
    cases.append(
        {
            "name": "exemplo_matriz_e_saida_do_trace",
            "rule": "—",
            "script": "trace.py",
            "setup": example_setup,
            "argv": example_root,
            "env": lambda w: {"GIT_CEILING_DIRECTORIES": str(w.parent)},
            "exit": 0,
            "expect": example_matrix(),
        }
    )

    # -- hook_gate: gate disparado pelo harness ------------------------------
    plan_path = "docs/plans/PLAN-001-fixture.md"
    cases.append(
        hook_case(
            "hook_plano_valido",
            "—",
            plan_setup(build_plan()),
            plan_path,
            0,
            "",
        )
    )
    cases.append(
        hook_case(
            "hook_plano_invalido_bloqueia",
            "Status fora do vocabulario fixo",
            plan_setup(marker("vocabulario de Status") + swap("Pendente", "Feito")(build_plan())),
            plan_path,
            2,
            "hook_gate: validate_plan.py reprovou PLAN-001-fixture.md",
        )
    )
    cases.append(
        hook_case(
            "hook_review_invalido_bloqueia",
            "Recomendacao fora do vocabulario",
            review_setup(
                marker("vocabulario de recomendacao")
                + REVIEW.replace("Aprovado com ressalvas", "Talvez", 1)
            ),
            "docs/reviews/REVIEW-T-01-2026-09-22.md",
            2,
            "hook_gate: validate_review.py reprovou",
        )
    )
    cases.append(
        hook_case(
            "hook_fora_do_escopo",
            "—",
            plan_setup(marker("vocabulario de Status") + swap("Pendente", "Feito")(build_plan())),
            "README.md",
            0,
            "",
        )
    )
    cases.append(
        hook_case(
            "hook_entrada_ilegivel",
            "—",
            lambda w: None,
            plan_path,
            0,
            "",
            raw="isto nao e json",
        )
    )

    # -- status: relatorio, nao gate -----------------------------------------
    cases.append(
        {
            "name": "status_json_categorias",
            "rule": "—",
            "script": "status.py",
            "setup": build_status_project,
            "argv": lambda w: ["--root", str(w), "--json"],
            "exit": 0,
            "expect": '"planos"',
            "check_json": check_status_json,
        }
    )
    cases.append(
        {
            "name": "status_markdown",
            "rule": "—",
            "script": "status.py",
            "setup": build_status_project,
            "argv": lambda w: ["--root", str(w)],
            "exit": 0,
            "expect": "- Próxima elegível: T-07 — Tarefa número 7",
        }
    )
    cases.append(
        {
            "name": "status_projeto_vazio",
            "rule": "—",
            "script": "status.py",
            "setup": lambda w: None,
            "argv": lambda w: ["--root", str(w)],
            "exit": 0,
            "expect": "| Planos | nenhum |",
        }
    )
    cases.append(
        {
            "name": "status_raiz_inexistente",
            "rule": "—",
            "script": "status.py",
            "setup": lambda w: None,
            "argv": lambda w: ["--root", str(w / "nao-existe")],
            "exit": 2,
            "expect": "raiz nao encontrada",
        }
    )

    # -- trace: matriz e lacunas ---------------------------------------------
    no_git = lambda w: {"GIT_CEILING_DIRECTORIES": str(w.parent)}
    cases.append(
        {
            "name": "trace_uma_lacuna_de_cada",
            "rule": "—",
            "script": "trace.py",
            "setup": build_trace_project,
            "argv": lambda w: ["--root", str(w), "--json"],
            "env": no_git,
            "exit": 0,
            "expect": '"lacunas"',
            "check_json": check_trace_gaps,
        }
    )
    cases.append(
        {
            "name": "trace_sem_lacunas_sem_ui_sem_git",
            "rule": "—",
            "script": "trace.py",
            "setup": lambda w: build_trace_project(w, with_gaps=False),
            "argv": lambda w: ["--root", str(w), "--json"],
            "env": no_git,
            "exit": 0,
            "expect": '"lacunas"',
            "check_json": check_trace_clean,
        }
    )
    cases.append(
        {
            "name": "trace_markdown_mermaid",
            "rule": "—",
            "script": "trace.py",
            "setup": build_trace_project,
            "argv": lambda w: ["--root", str(w), "--mermaid"],
            "env": no_git,
            "exit": 0,
            "expect": "    RN01 --> CA01",
        }
    )
    if shutil.which("git"):
        cases.append(
            {
                "name": "trace_commits_pelo_trailer",
                "rule": "—",
                "script": "trace.py",
                "setup": build_trace_git_project,
                "argv": lambda w: ["--root", str(w), "--json"],
                "env": no_git,
                "exit": 0,
                "expect": '"commits"',
                "check_json": check_trace_git,
            }
        )

    # -- check_commit -----------------------------------------------------
    subject = "Implementa o saque dentro do saldo\n\n"
    cases.append(
        commit_case("commit_valido", "—", subject + "Refs: T-01, CA-01", 0, "0 error(s)")
    )
    cases.append(
        commit_case(
            "commit_por_arquivo",
            "—",
            subject + "# comentario do git\nRefs: T-02, UI-01.vazio",
            0,
            "0 error(s)",
            as_file=True,
        )
    )
    cases.append(
        commit_case(
            "commit_sem_trailer",
            "mensagem sem trailer Refs",
            subject + "Corpo sem referência.",
            1,
            "mensagem sem trailer 'Refs:'",
        )
    )
    cases.append(
        commit_case(
            "commit_id_malformado",
            "ID malformado no trailer",
            subject + "Refs: T-01, CA-1",
            1,
            "ID malformado ou nao referenciavel no trailer: 'CA-1'",
        )
    )
    cases.append(
        commit_case(
            "commit_id_de_review",
            "R-XX não é referenciável no trailer",
            subject + "Refs: T-01, R-01",
            1,
            "nao referenciavel no trailer: 'R-01'",
        )
    )
    cases.append(
        commit_case(
            "commit_sem_tarefa",
            "trailer sem nenhuma T-XX",
            subject + "Refs: CA-01",
            1,
            "sem nenhuma T-XX",
        )
    )
    cases.append(
        commit_case(
            "commit_tarefa_inexistente_no_plano",
            "T-XX citada que não existe no plano",
            subject + "Refs: T-09, CA-01",
            1,
            "T-09 citada no trailer nao existe no plano",
            with_plan=True,
        )
    )
    cases.append(
        commit_case(
            "commit_tarefa_existente_no_plano",
            "—",
            subject + "Refs: T-03",
            0,
            "0 error(s)",
            with_plan=True,
        )
    )
    cases.append(
        commit_case(
            "commit_strict_promove_repetido",
            "—",
            subject + "Refs: T-01, T-01",
            1,
            "1 error(s), 0 warning(s)",
            strict=True,
        )
    )
    cases.append(
        {
            "name": "commit_sem_mensagem",
            "rule": "—",
            "script": "check_commit.py",
            "setup": lambda w: None,
            "argv": lambda w: ["--message", "   "],
            "exit": 2,
            "expect": "nenhuma mensagem informada",
        }
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
    env = None
    if "env" in case:
        env = dict(os.environ)
        env.update(case["env"](workspace))
    stdin = case["stdin"](workspace) if "stdin" in case else None
    completed = subprocess.run(
        command,
        env=env,
        input=stdin,
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
    if "check_json" in case and completed.returncode == 0:
        try:
            problems += case["check_json"](json.loads(output))
        except ValueError as exc:
            problems.append("saida nao e JSON: {}".format(exc))

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
