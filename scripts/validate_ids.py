#!/usr/bin/env python3
"""Gate de integridade da matriz de rastreabilidade do pipeline SDD Leanwork.

Confere que todo `RN-XX`, `CA-XX`, `ADR-XX` e `UI-XX` citado pelas tarefas do
plano existe no artefato onde aquele ID nasce. Substitui por mecanismo a
conferencia manual que o Passo 2 de `/leanwork-execute` descreve em prosa.

    RN-XX / CA-XX  -> docs/prds/PRD-*.md
    ADR-XX         -> docs/architecture/proposta-arquitetural.md + adrs/
    UI-XX[.estado] -> docs/prototype/SPEC-UI-*.md

Artefato de origem ausente nao reprova: a verificacao daquela classe de ID e
pulada e declarada em WARN. Projeto sem SPEC-UI e sem campo `Telas:` e o estado
correto e nao gera diagnostico.

`R-XX` nao entra aqui de proposito: e o unico ID cujo namespace e o arquivo, e
reinicia a cada relatorio. Quem o valida e `validate_review.py`.

Uso:
    python scripts/validate_ids.py [plano] [--root DIR] [--strict]

Exit: 0 aprovado, 1 erro de conteudo, 2 erro de uso.
"""

import argparse
import re
import sys
from pathlib import Path

from _common import (
    Diagnostics,
    UsageError,
    enable_utf8_output,
    fail_usage,
    finish,
    read_lines,
    resolve_target,
    unwrap_envelope,
)
from validate_plan import load_document, parse_tasks

SCRIPT = "validate_ids"

ID_PATTERN = re.compile(r"^(RN|CA|ADR|UI)-\d{2,}(\.[a-zA-Z][a-zA-Z0-9]*)?$")
ID_TOKEN = re.compile(r"[A-Za-z]+-[A-Za-z0-9.]+")

TASK_FIELDS = (
    ("Implementa", "RN"),
    ("Valida", "CA"),
    ("Decisões base", "ADR"),
    ("Telas", "UI"),
)

SCREEN_WITH_STATES = re.compile(
    r"(?P<screen>UI-\d{2,})\s*(?:\((?P<states>[^)]*)\))?"
)

RN_DEFINITION = re.compile(r"^\s*[-*>|#\s]*\**(RN-\d{2,})\**\s*[:—–-]", re.MULTILINE)
CA_DEFINITION = re.compile(r"Cen[áa]rio\s*\[(CA-\d{2,})\]")
ADR_DEFINITION = re.compile(r"^\s*#{1,6}\s*\**(ADR-\d{2,})\**\s*[:—–-]", re.MULTILINE)
UI_DEFINITION = re.compile(r"^\s*#{1,6}\s*\**(UI-\d{2,})\**\s*[:—–-]", re.MULTILINE)


class Source:
    """Um artefato de origem: o texto concatenado e se ele existe."""

    def __init__(self, label, paths):
        self.label = label
        self.paths = paths
        self.text = ""
        for path in paths:
            self.text += "\n".join(unwrap_envelope(read_lines(path))) + "\n"

    @property
    def available(self):
        return bool(self.paths)

    @property
    def where(self):
        return ", ".join(p.name for p in self.paths)


def gather(root, relative_dir, patterns):
    directory = Path(root) / relative_dir
    if not directory.is_dir():
        return []
    found = []
    for pattern in patterns:
        found.extend(sorted(p for p in directory.glob(pattern) if p.is_file()))
    return found


def load_sources(root):
    prd = gather(root, "docs/prds", ["PRD-*.md"])
    architecture = gather(root, "docs/architecture", ["proposta-arquitetural.md"])
    architecture += gather(root, "docs/architecture/adrs", ["*.md"])
    spec_ui = gather(root, "docs/prototype", ["SPEC-UI-*.md"])
    return {
        "RN": Source("docs/prds/PRD-*.md", prd),
        "CA": Source("docs/prds/PRD-*.md", prd),
        "ADR": Source(
            "docs/architecture/proposta-arquitetural.md + adrs/", architecture
        ),
        "UI": Source("docs/prototype/SPEC-UI-*.md", spec_ui),
    }


def collect_references(tasks, diagnostics):
    """Extrai os IDs citados por cada tarefa, por classe.

    Devolve {classe: [(id, task_id, line)]} e, separadamente, os estados de tela
    declarados em `Telas:`.
    """
    references = {"RN": [], "CA": [], "ADR": [], "UI": []}
    states = []

    for task in tasks:
        for field_name, expected_class in TASK_FIELDS:
            raw = task.field(field_name)
            if raw is None:
                continue
            value = raw.strip()
            if not value or value.lower().startswith(("nenhum", "n/a", "—", "-")):
                continue

            if expected_class == "UI":
                for match in SCREEN_WITH_STATES.finditer(value):
                    screen = match.group("screen")
                    references["UI"].append((screen, task.id, task.line))
                    raw_states = match.group("states") or ""
                    for state in (s.strip() for s in raw_states.split(",")):
                        if state:
                            states.append((screen, state, task.id, task.line))
                continue

            for token in ID_TOKEN.findall(value):
                if not token.startswith(expected_class + "-"):
                    continue
                if not ID_PATTERN.match(token):
                    diagnostics.error(
                        "{} (linha {}): ID malformado em '{}:' -> '{}'".format(
                            task.id, task.line, field_name, token
                        )
                    )
                    continue
                references[expected_class].append((token, task.id, task.line))

    return references, states


def is_defined(identifier, source, kind):
    if kind == "CA":
        return identifier in CA_DEFINITION.findall(source.text)
    pattern = re.compile(
        r"(?<![\w-])" + re.escape(identifier) + r"(?![\w.-])"
    )
    return bool(pattern.search(source.text))


def screen_section(screen, text):
    """Recorta a secao da SPEC-UI que descreve uma tela."""
    lines = text.split("\n")
    start = None
    level = None
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+\**" + re.escape(screen) + r"\b", line)
        if heading:
            start = index
            level = len(heading.group(1))
            break
    if start is None:
        return None
    for index in range(start + 1, len(lines)):
        heading = re.match(r"^(#{1,6})\s", lines[index])
        if heading and len(heading.group(1)) <= level:
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:])


def check_references(references, states, sources, diagnostics):
    for kind in ("RN", "CA", "ADR", "UI"):
        cited = references[kind]
        source = sources[kind]

        if not cited:
            continue

        if not source.available:
            diagnostics.warn(
                "verificacao de {} pulada: artefato de origem nao encontrado ({}) "
                "- {} ID(s) citado(s) no plano seguem nao verificados".format(
                    kind, source.label, len(cited)
                )
            )
            continue

        for identifier, task_id, line in cited:
            if not is_defined(identifier, source, kind):
                diagnostics.error(
                    "{} (linha {}): {} nao existe em {}".format(
                        task_id, line, identifier, source.where
                    )
                )

    check_states(states, sources["UI"], diagnostics)


def check_states(states, source, diagnostics):
    if not states:
        return
    if not source.available:
        diagnostics.warn(
            "verificacao de estados de tela pulada: artefato de origem nao "
            "encontrado ({})".format(source.label)
        )
        return

    for screen, state, task_id, line in states:
        section = screen_section(screen, source.text)
        if section is None:
            continue
        token = re.compile(r"\." + re.escape(state) + r"(?![\w])")
        if not token.search(section):
            diagnostics.error(
                "{} (linha {}): estado '{}.{}' nao esta definido na SPEC-UI - a "
                "tela existe, o estado nao".format(task_id, line, screen, state)
            )


def check_coverage_gaps(references, sources, diagnostics):
    """Regra de negocio do PRD que nenhuma tarefa cita e gap de cobertura.

    E WARN, nao ERROR: quem reporta gap como analise e `/leanwork-trace`, e um
    plano que cobre so parte do PRD e legitimo.
    """
    for kind, pattern in (("RN", RN_DEFINITION), ("CA", CA_DEFINITION)):
        source = sources[kind]
        if not source.available:
            continue
        defined = sorted(set(pattern.findall(source.text)))
        cited = {identifier for identifier, _, _ in references[kind]}
        missing = [identifier for identifier in defined if identifier not in cited]
        if missing:
            diagnostics.warn(
                "{} definido(s) no PRD que nenhuma tarefa do plano cita: {}".format(
                    kind, ", ".join(missing)
                )
            )


def validate(plan_path, root, diagnostics):
    lines, mask = load_document(plan_path)
    tasks = parse_tasks(lines, mask)
    if not tasks:
        diagnostics.error("nenhuma tarefa '#### T-XX' encontrada no plano")
        return

    references, states = collect_references(tasks, diagnostics)
    sources = load_sources(root)
    check_references(references, states, sources, diagnostics)
    check_coverage_gaps(references, sources, diagnostics)


def main(argv=None):
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        prog=SCRIPT,
        description="Valida a integridade dos IDs citados pelo plano de execucao.",
    )
    parser.add_argument("target", nargs="?", help="arquivo ou diretorio do plano")
    parser.add_argument("--root", default=".", help="raiz do projeto consumidor")
    parser.add_argument("--strict", action="store_true", help="promove warning a erro")
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
        validate(path, args.root, diagnostics)
    except UsageError as exc:
        return fail_usage(SCRIPT, str(exc))

    return finish(SCRIPT, path, diagnostics, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
