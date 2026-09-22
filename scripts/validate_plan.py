#!/usr/bin/env python3
"""Gate estrutural do plano de execucao do pipeline SDD Leanwork.

Converte em verificacao deterministica o que hoje e prosa em
`skills/planner-leanwork/SKILL.md` e `references/plan-template.md`. A fonte
canonica das regras de ID e de vocabulario e `templates/id-conventions.md`.

Uso:
    python scripts/validate_plan.py [alvo] [--root DIR] [--strict]

`alvo` aceita arquivo, diretorio, ou nada - neste caso o plano e auto-detectado
em `docs/plans/` a partir de `--root` (padrao: diretorio corrente).

Decisao de calibragem: "tarefa com mais de 3 criterios de aceite" e WARN, nunca
ERROR. A heuristica vale como sinal de tarefa grande demais
(`templates/id-conventions.md`, T-XX), mas quebrar a tarefa e julgamento de quem
planeja - o gate aponta, nao decide.

Exit: 0 aprovado, 1 erro de conteudo, 2 erro de uso.
"""

import argparse
import re
import sys

from _common import (
    Diagnostics,
    UsageError,
    enable_utf8_output,
    fail_usage,
    fence_mask,
    find_placeholders,
    finish,
    parse_field,
    read_lines,
    resolve_target,
    unwrap_envelope,
)

SCRIPT = "validate_plan"

STATUS_VOCAB = ("Pendente", "Em andamento", "Concluído", "Bloqueado")

REQUIRED_SECTIONS = (
    "Resumo executivo",
    "Estratégia de entrega",
    "Fases",
    "Checklist de prontidão",
    "Pontos de validação humana",
)

REQUIRED_FIELDS = (
    "Status",
    "Complexidade",
    "Depende de",
    "Camadas/arquivos afetados",
)

CA_MARKER = "Critério de aceite"
TESTS_MARKER = "Testes a escrever"

MAX_ACCEPTANCE_CRITERIA = 3

HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*$")
TASK_HEADING = re.compile(r"^####\s+(?P<id>\S+)\s*(?:[—–-]\s*(?P<title>.*))?$")
BLOCK_MARKER = re.compile(r"^\*\*(?P<name>[^*]+?):\*\*\s*$")
THEMATIC_BREAK = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
CHECKBOX = re.compile(r"^\s*[-*]\s*\[[ xX]\]")
STATUS_AS_CHECKBOX = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*\*\*Status")
TASK_ID = re.compile(r"^T-\d{2,}$")
TASK_REFERENCE = re.compile(r"T-\d+")
HISTORY_ROW = re.compile(r"^\|\s*(?P<id>T-\d+)\s*\|\s*(?P<status>[^|]*?)\s*\|")


class Task:
    def __init__(self, task_id, line_number, title):
        self.id = task_id
        self.line = line_number
        self.title = title or ""
        self.fields = {}
        self.markers = {}
        self.body = []

    @property
    def number(self):
        return int(self.id.split("-")[1])

    def field(self, name):
        return self.fields.get(name)

    def marker_lines(self, prefix):
        for name, content in self.markers.items():
            if name.startswith(prefix):
                return content
        return None

    def has_marker(self, prefix):
        return self.marker_lines(prefix) is not None


def load_document(path):
    """Le o artefato, descasca o envelope de template e marca as cercas."""
    lines = unwrap_envelope(read_lines(path))
    return lines, fence_mask(lines)


def parse_tasks(lines, mask, diagnostics=None):
    """Extrai as tarefas do plano.

    So um cabecalho `#### T-XX` fora de cerca abre tarefa. Mencao a `T-XX` numa
    linha `Depende de:` ou num no de diagrama Mermaid nao abre - confundir os
    dois produz falso positivo de tarefa duplicada.
    """
    tasks = []
    current = None
    current_marker = None

    for index, line in enumerate(lines):
        if mask[index]:
            if current is not None:
                current.body.append((index + 1, line))
                if current_marker is not None:
                    current.markers[current_marker].append(line)
            continue

        heading = HEADING.match(line)
        if heading:
            task_match = TASK_HEADING.match(line)
            if task_match and task_match.group("id").startswith("T-"):
                raw_id = task_match.group("id")
                if not TASK_ID.match(raw_id):
                    if diagnostics is not None:
                        diagnostics.error(
                            "linha {}: ID de tarefa malformado '{}' - o padrao e "
                            "T-NN com no minimo dois digitos".format(index + 1, raw_id)
                        )
                    current = None
                    current_marker = None
                    continue
                current = Task(raw_id, index + 1, task_match.group("title"))
                tasks.append(current)
                current_marker = None
                continue
            current = None
            current_marker = None
            continue

        if current is None:
            continue

        current.body.append((index + 1, line))

        if THEMATIC_BREAK.match(line):
            current_marker = None
            continue

        marker = BLOCK_MARKER.match(line)
        if marker:
            current_marker = marker.group("name").strip()
            current.markers.setdefault(current_marker, [])
            continue

        field = parse_field(line)
        if field and current_marker is None:
            current.fields[field[0]] = field[1]
            continue

        if current_marker is not None:
            current.markers[current_marker].append(line)

    return tasks


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


def check_sections(sections, diagnostics):
    titles = [title.lower() for _, title in sections]
    for required in REQUIRED_SECTIONS:
        if not any(required.lower() in title for title in titles):
            diagnostics.error("secao obrigatoria ausente: '{}'".format(required))


def check_task_fields(task, diagnostics):
    for required in REQUIRED_FIELDS:
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
    items = [line for line in content if CHECKBOX.match(line)]
    if not items:
        diagnostics.error(
            "{} (linha {}): '{}' sem nenhum item '- [ ]'".format(
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
        raw = task.field("Depende de")
        if raw is None:
            continue
        if raw.strip().lower().startswith("nenhuma"):
            continue
        for reference in TASK_REFERENCE.findall(raw):
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


def check_history(lines, mask, tasks, diagnostics):
    statuses = {task.id: task.field("Status") for task in tasks}
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        row = HISTORY_ROW.match(line)
        if not row:
            continue
        task_id = row.group("id")
        declared = row.group("status").replace("*", "").strip()
        expected = statuses.get(task_id)
        if expected is None or not declared:
            continue
        if declared != expected:
            diagnostics.error(
                "Histórico de execução (linha {}): {} consta como '{}' na tabela e "
                "'{}' no campo '**Status:**'".format(
                    index + 1, task_id, declared, expected
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

    check_ids_and_dependencies(tasks, diagnostics)
    check_history(lines, mask, tasks, diagnostics)
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
