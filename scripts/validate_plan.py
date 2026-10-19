#!/usr/bin/env python3
"""Gate estrutural do plano de execucao do pipeline SDD Leanwork.

Converte em verificacao deterministica o que hoje e prosa em
`skills/planner-leanwork/SKILL.md` e `references/plan-template.md`. A fonte
canonica das regras de ID e de vocabulario e `templates/id-conventions.md`.

Uso:
    python scripts/validate_plan.py [alvo] [--root DIR] [--strict]

`alvo` aceita arquivo, diretorio, ou nada - neste caso o plano e auto-detectado
em `docs/plans/` a partir de `--root` (padrao: diretorio corrente).

Decisao de calibragem: "tarefa com mais de 5 criterios de aceite" e WARN, nunca
ERROR. O limiar subiu de 3 para 5 com a fatia vertical por CA-XX (PLAN-002,
T-07). A heuristica vale como sinal de tarefa grande demais
(`templates/id-conventions.md`, T-XX), mas quebrar a tarefa e julgamento de quem
planeja - o gate aponta, nao decide.

O campo `**Status:**` da tarefa e a unica fonte de estado. Plano antigo com
tabela de Historico de execucao continua passando: a tabela e ignorada, nem
comparada nem proibida.

Plano de trilha rapida (cabecalho `**PRD de referencia:** nenhum - trilha
rapida`) dispensa as secoes do plano completo e mantem o rigor da tarefa. Mais
de uma tarefa e ERROR: e o sinal de que a mudanca nao cabe na trilha.

Exit: 0 aprovado, 1 erro de conteudo, 2 erro de uso.
"""

import argparse
import re
import sys

from _common import (
    HEADING,
    STATUS_VOCAB,
    Diagnostics,
    UsageError,
    enable_utf8_output,
    fail_usage,
    find_placeholders,
    finish,
    is_quick_track,
    load_document,
    parse_tasks,
    resolve_target,
)

SCRIPT = "validate_plan"

REQUIRED_SECTIONS = (
    "Resumo executivo",
    "Estratégia de entrega",
    "Fases",
    "Pontos de validação humana",
)

REQUIRED_FIELDS = (
    "Status",
    "Complexidade",
    "Depende de",
    "Portas de mão única",
)

CA_MARKER = "Critério de aceite"
TESTS_MARKER = "Testes a escrever"

MAX_ACCEPTANCE_CRITERIA = 5

LIST_ITEM = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S")
STATUS_AS_CHECKBOX = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*\*\*Status")
BLOCK_FIELD = "Bloqueio"
DOORS_FIELD = "Portas de mão única"
LEGACY_SCOPE_FIELD = "Camadas/arquivos afetados"



def collect_sections(lines, mask):
    sections = []
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        heading = HEADING.match(line)
        if heading and len(heading.group("hashes")) == 2:
            text = re.sub(r"^\d+\.\s*", "", heading.group("text"))
            text = re.sub(r"\*\(.*?\)\*", "", text).strip()
            sections.append((index + 1, text))
    return sections


def check_quick_track_size(tasks, diagnostics):
    if len(tasks) > 1:
        diagnostics.error(
            "plano de trilha rapida com {} tarefas - a trilha rapida tem uma tarefa "
            "so; mudanca maior vai pelo fluxo completo (PRD -> plano)".format(len(tasks))
        )
    for task in tasks:
        doors = task.field(DOORS_FIELD)
        if doors is not None and not doors.strip().lower().startswith("nenhuma"):
            diagnostics.error(
                "{} (linha {}): trilha rapida com porta de mao unica declarada - "
                "migration, contrato publico, schema ou permissao vai pelo fluxo "
                "completo".format(task.id, task.line)
            )


def check_sections(sections, diagnostics):
    titles = [title.lower() for _, title in sections]
    for required in REQUIRED_SECTIONS:
        if not any(required.lower() in title for title in titles):
            diagnostics.error("secao obrigatoria ausente: '{}'".format(required))


def check_task_fields(task, diagnostics):
    for required in REQUIRED_FIELDS:
        if required == DOORS_FIELD and task.field(required) is None:
            if task.field(LEGACY_SCOPE_FIELD) is not None:
                diagnostics.warn(
                    "{} (linha {}): campo '**{}:**' e do formato anterior a 2.0.0 - "
                    "substituir por '**{}:**' (nenhuma, ou o que e caro de "
                    "reverter)".format(task.id, task.line, LEGACY_SCOPE_FIELD, DOORS_FIELD)
                )
                continue
        if task.field(required) is None:
            diagnostics.error(
                "{} (linha {}): campo obrigatorio ausente: '**{}:**'".format(
                    task.id, task.line, required
                )
            )

    if not task.has_marker(CA_MARKER):
        diagnostics.error(
            "{} (linha {}): bloco obrigatorio ausente: '**{} (testável):**'".format(
                task.id, task.line, CA_MARKER
            )
        )
    if not task.has_marker(TESTS_MARKER):
        diagnostics.error(
            "{} (linha {}): bloco obrigatorio ausente: '**{}:**'".format(
                task.id, task.line, TESTS_MARKER
            )
        )


def check_status(task, diagnostics):
    for number, text in task.body:
        if STATUS_AS_CHECKBOX.match(text):
            diagnostics.error(
                "{} (linha {}): Status representado como checkbox - o estado da "
                "tarefa vive so no campo '**Status:**', por extenso".format(
                    task.id, number
                )
            )
            return

    value = task.field("Status")
    if value is None:
        return
    if value not in STATUS_VOCAB:
        diagnostics.error(
            "{} (linha {}): Status '{}' fora do vocabulario fixo {}".format(
                task.id, task.line, value, " / ".join(STATUS_VOCAB)
            )
        )


def check_acceptance_criteria(task, diagnostics):
    content = task.marker_lines(CA_MARKER)
    if content is None:
        return
    items = [line for line in content if LIST_ITEM.match(line)]
    if not items:
        diagnostics.error(
            "{} (linha {}): '{}' sem nenhum item de lista".format(
                task.id, task.line, CA_MARKER
            )
        )
        return
    if len(items) > MAX_ACCEPTANCE_CRITERIA:
        diagnostics.warn(
            "{} (linha {}): {} criterios de aceite (limiar {}) - sinal de tarefa "
            "grande demais".format(
                task.id, task.line, len(items), MAX_ACCEPTANCE_CRITERIA
            )
        )


def check_tests_section(task, diagnostics):
    content = task.marker_lines(TESTS_MARKER)
    if content is None:
        return
    body = "\n".join(content).strip()
    if not body:
        diagnostics.warn(
            "{} (linha {}): '{}' vazio - declare os cenarios ou marque "
            "'Não aplicável' com a razao".format(task.id, task.line, TESTS_MARKER)
        )


def check_ids_and_dependencies(tasks, diagnostics):
    seen = {}
    for task in tasks:
        if task.id in seen:
            diagnostics.error(
                "{} duplicado: linhas {} e {}".format(task.id, seen[task.id], task.line)
            )
            continue
        seen[task.id] = task.line

    numbers = sorted(task.number for task in tasks)
    for position, number in enumerate(numbers, start=1):
        if number != position:
            diagnostics.error(
                "sequencia de tarefas com buraco: esperado T-{:02d}, encontrado "
                "T-{:02d}".format(position, number)
            )
            break

    known = set(seen)
    for task in tasks:
        for reference in task.dependencies():
            if reference not in known:
                diagnostics.error(
                    "{} (linha {}): depende de {}, que nao existe no plano".format(
                        task.id, task.line, reference
                    )
                )
                continue
            if int(reference.split("-")[1]) > task.number:
                diagnostics.error(
                    "{} (linha {}): dependencia para frente - depende de {}, que "
                    "vem depois dela".format(task.id, task.line, reference)
                )


def check_block_reason(task, diagnostics):
    if task.field("Status") != "Bloqueado":
        return
    if not task.block_reason():
        diagnostics.error(
            "{} (linha {}): Status 'Bloqueado' sem campo '**{}:**' com o motivo".format(
                task.id, task.line, BLOCK_FIELD
            )
        )


def check_dependency_map(sections, tasks, diagnostics):
    if len(tasks) <= 5:
        return
    titles = [title.lower() for _, title in sections]
    if not any("mapa de dependências" in title for title in titles):
        diagnostics.warn(
            "plano com {} tarefas sem secao 'Mapa de dependências'".format(len(tasks))
        )


def check_placeholders(lines, mask, diagnostics):
    for number, snippet in find_placeholders(lines, mask):
        diagnostics.warn(
            "linha {}: placeholder de template nao preenchido: {}".format(
                number, snippet
            )
        )


def validate(path, diagnostics):
    lines, mask = load_document(path)
    sections = collect_sections(lines, mask)
    quick = is_quick_track(lines, mask)

    if not quick:
        check_sections(sections, diagnostics)
    tasks = parse_tasks(lines, mask, diagnostics)

    if not tasks:
        diagnostics.error("nenhuma tarefa '#### T-XX' encontrada no plano")
        return

    for task in tasks:
        check_task_fields(task, diagnostics)
        check_status(task, diagnostics)
        check_acceptance_criteria(task, diagnostics)
        check_tests_section(task, diagnostics)
        check_block_reason(task, diagnostics)

    check_ids_and_dependencies(tasks, diagnostics)
    if quick:
        check_quick_track_size(tasks, diagnostics)
    else:
        check_dependency_map(sections, tasks, diagnostics)
    check_placeholders(lines, mask, diagnostics)


def main(argv=None):
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        prog=SCRIPT, description="Valida a estrutura de um plano de execucao SDD."
    )
    parser.add_argument("target", nargs="?", help="arquivo ou diretorio do plano")
    parser.add_argument("--root", default=".", help="raiz do projeto consumidor")
    parser.add_argument(
        "--strict", action="store_true", help="promove warning a erro"
    )
    args = parser.parse_args(argv)

    try:
        path = resolve_target(
            args.target,
            args.root,
            ["docs/plans", "docs/plan", "."],
            ["PLAN-*.md", "*.md"],
            "plano",
        )
    except UsageError as exc:
        return fail_usage(SCRIPT, str(exc))

    diagnostics = Diagnostics()
    try:
        validate(path, diagnostics)
    except UsageError as exc:
        return fail_usage(SCRIPT, str(exc))

    return finish(SCRIPT, path, diagnostics, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
