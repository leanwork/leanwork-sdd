#!/usr/bin/env python3
"""Matriz de rastreabilidade ADR <-> RN <-> CA <-> UI <-> T <-> R do pipeline SDD.

Monta por leitura deterministica a matriz e as lacunas que `/leanwork-trace`
montava a mao. O modelo so interpreta: decide o que a lacuna significa e o que
fazer com ela.

Uma linha por `CA-XX` definido (no PRD, ou no proprio plano na trilha rapida):
as `RN-XX` citadas nos passos do cenario, os `ADR-XX` da regra e das tarefas,
as telas, as tarefas que o validam, o ultimo review de cada tarefa e - com git -
os commits cujo trailer `Refs:` cita a tarefa.

Lacunas mecanicas reportadas:
    rn_sem_cenario, ca_sem_tarefa, tarefa_sem_rastro, adr_citado_inexistente,
    adr_nunca_citado, concluida_sem_review, review_bloqueado_aberto,
    status_fora_do_vocabulario, bloqueio_sem_motivo e, com SPEC-UI,
    tela_sem_tarefa e estado_sem_tarefa.

Ficam para o modelo, porque pedem julgamento: CA de interface sem tela, tela sem
respaldo no PRD e lacunas abertas da secao 8 da SPEC-UI.

Sem SPEC-UI, as colunas de UI somem e nao geram lacuna. Sem git, a coluna de
commits some com aviso.

Uso:
    python scripts/trace.py [--root DIR] [--prd ARQUIVO] [--json] [--mermaid]

Exit: 0 leu os artefatos, 2 erro de uso. E relatorio, nao gate.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from _common import (
    STATUS_VOCAB,
    enable_utf8_output,
    fail_usage,
    is_quick_track,
    load_document,
    parse_tasks,
    read_lines,
    unwrap_envelope,
)
from check_commit import extract_refs
from status import collect_reviews, files
from validate_ids import (
    ADR_DEFINITION,
    CA_DEFINITION,
    RN_DEFINITION,
    SCREEN_WITH_STATES,
    UI_DEFINITION,
)

SCRIPT = "trace"

RN_TOKEN = re.compile(r"RN-\d{2,}")
CA_TOKEN = re.compile(r"CA-\d{2,}")
ADR_TOKEN = re.compile(r"ADR-\d{2,}")
UI_STATE_TOKEN = re.compile(r"(UI-\d{2,})\.([a-zA-Z][a-zA-Z0-9]*)")
PLAN_NUMBER = re.compile(r"^(?:PRD|PLAN)-(\d+)")


def text_of(paths):
    return "\n".join("\n".join(unwrap_envelope(read_lines(p))) for p in paths)


def scenarios(text):
    """{CA-XX: [RN-XX citadas nos passos do cenario]}."""
    result = {}
    matches = list(CA_DEFINITION.finditer(text))
    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        block = text[match.end():end]
        fence = block.find("```")
        if fence != -1:
            block = block[:fence]
        result[match.group(1)] = sorted(set(RN_TOKEN.findall(block)))
    return result


def rules(text):
    """{RN-XX: [ADR-XX citados na linha da regra]}."""
    result = {}
    for line in text.split("\n"):
        match = RN_DEFINITION.match(line)
        if match:
            result.setdefault(match.group(1), set()).update(ADR_TOKEN.findall(line))
    return {rn: sorted(adrs) for rn, adrs in result.items()}


def screens(text):
    """{UI-XX: [estados]} a partir da SPEC-UI."""
    result = {screen: set() for screen in UI_DEFINITION.findall(text)}
    for screen, state in UI_STATE_TOKEN.findall(text):
        result.setdefault(screen, set()).add(state)
    return {screen: sorted(states) for screen, states in result.items()}


def ids_in(task, field, pattern):
    raw = task.field(field) or ""
    return sorted(set(pattern.findall(raw)))


def screens_in(task):
    raw = task.field("Telas") or ""
    result = {}
    for match in SCREEN_WITH_STATES.finditer(raw):
        states = [s.strip() for s in (match.group("states") or "").split(",") if s.strip()]
        result.setdefault(match.group("screen"), set()).update(states)
    return result


def git_commits(root):
    """{T-XX: [hash curto]} pelo trailer `Refs:`, ou None sem git."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "log", "--format=%h%x1f%B%x1e"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    result = {}
    for record in completed.stdout.split("\x1e"):
        if "\x1f" not in record:
            continue
        sha, body = record.split("\x1f", 1)
        for ref in extract_refs(body) or []:
            if ref.startswith("T-"):
                result.setdefault(ref, []).append(sha.strip())
    return result


def select(root, prd_arg):
    prds = files(root, "docs/prds", "PRD-*.md")
    plans = files(root, "docs/plans", "PLAN-*.md")
    if prd_arg is None:
        return prds, plans
    chosen = [p for p in prds if p.name == Path(prd_arg).name]
    if not chosen:
        raise ValueError("PRD nao encontrado em docs/prds: {}".format(prd_arg))
    number = PLAN_NUMBER.match(chosen[0].name)
    paired = [p for p in plans if number and PLAN_NUMBER.match(p.name)
              and PLAN_NUMBER.match(p.name).group(1) == number.group(1)]
    return chosen, paired


def build(root, prd_arg=None):
    prds, plans = select(root, prd_arg)
    architecture = files(root, "docs/architecture", "proposta-arquitetural.md")
    architecture += files(root, "docs/architecture/adrs", "*.md")
    spec_paths = files(root, "docs/prototype", "SPEC-UI-*.md")

    prd_text = text_of(prds)
    defined_ca = scenarios(prd_text)
    defined_rn = rules(prd_text)
    defined_adr = sorted(set(ADR_DEFINITION.findall(text_of(architecture))))
    defined_ui = screens(text_of(spec_paths)) if spec_paths else None
    has_ui = defined_ui is not None

    tasks = []
    for plan in plans:
        lines, mask = load_document(plan)
        if is_quick_track(lines, mask):
            defined_ca.update(scenarios("\n".join(lines)))
        for task in parse_tasks(lines, mask):
            label = task.id if len(plans) == 1 else "{}:{}".format(plan.stem.split("-")[1], task.id)
            tasks.append((label, task))

    reviews, _ = collect_reviews(root)
    commits = git_commits(root)

    rows = []
    for ca in sorted(defined_ca):
        validating = [(label, task) for label, task in tasks if ca in ids_in(task, "Valida", CA_TOKEN)]
        rns = defined_ca[ca]
        adrs = set()
        for rn in rns:
            adrs.update(defined_rn.get(rn, []))
        ui = set()
        for _, task in validating:
            adrs.update(ids_in(task, "Decisões base", ADR_TOKEN))
            ui.update(screens_in(task))
        row = {
            "ca": ca,
            "rn": rns,
            "adr": sorted(adrs),
            "t": [label for label, _ in validating],
            "r": [
                "{} ({})".format(reviews[t.id]["arquivo"], reviews[t.id]["recomendacao"])
                for _, t in validating if t.id in reviews
            ],
        }
        if has_ui:
            row["ui"] = sorted(ui)
        if commits is not None:
            row["commits"] = sorted({sha for _, t in validating for sha in commits.get(t.id, [])})
        rows.append(row)

    gaps = {}

    def gap(kind, item):
        gaps.setdefault(kind, []).append(item)

    for rn in sorted(defined_rn):
        if not any(rn in cited for cited in defined_ca.values()):
            gap("rn_sem_cenario", rn)
    for row in rows:
        if not row["t"]:
            gap("ca_sem_tarefa", row["ca"])

    cited_adr = set(ADR_TOKEN.findall(prd_text))
    for label, task in tasks:
        cited_adr.update(ids_in(task, "Decisões base", ADR_TOKEN))
        if not ids_in(task, "Implementa", RN_TOKEN) and not ids_in(task, "Valida", CA_TOKEN):
            gap("tarefa_sem_rastro", label)
    if architecture:
        for adr in sorted(cited_adr - set(defined_adr)):
            gap("adr_citado_inexistente", adr)
        for adr in defined_adr:
            if adr not in cited_adr:
                gap("adr_nunca_citado", adr)

    for label, task in tasks:
        status = (task.field("Status") or "").strip()
        review = reviews.get(task.id)
        if status not in STATUS_VOCAB:
            gap("status_fora_do_vocabulario", "{} ('{}')".format(label, status))
        if status == "Bloqueado" and not task.block_reason():
            gap("bloqueio_sem_motivo", label)
        if status == "Concluído" and review is None:
            gap("concluida_sem_review", label)
        if review is not None and review["recomendacao"] == "Bloqueado":
            gap("review_bloqueado_aberto", "{} ({}{})".format(
                label, review["arquivo"], ", tarefa marcada Concluído" if status == "Concluído" else ""
            ))

    if has_ui:
        covered = {}
        for _, task in tasks:
            for screen, states in screens_in(task).items():
                covered.setdefault(screen, set()).update(states)
        for screen, states in sorted(defined_ui.items()):
            if screen not in covered:
                gap("tela_sem_tarefa", screen)
                continue
            for state in states:
                if state not in covered[screen]:
                    gap("estado_sem_tarefa", "{}.{}".format(screen, state))

    warnings = []
    if commits is None:
        warnings.append("sem git no projeto: coluna de commits omitida")
    if not prds and not any(is_quick_track(*load_document(p)) for p in plans):
        warnings.append("nenhum PRD em docs/prds: RN e CA vem so de planos de trilha rapida")

    return {
        "prds": [p.name for p in prds],
        "planos": [p.name for p in plans],
        "spec_ui": has_ui,
        "git": commits is not None,
        "matriz": rows,
        "lacunas": gaps,
        "avisos": warnings,
        "_rules": defined_rn,
    }


GAP_LABELS = (
    ("rn_sem_cenario", "RN sem cenário"),
    ("ca_sem_tarefa", "CA sem tarefa"),
    ("tarefa_sem_rastro", "Tarefa sem Implementa nem Valida (legítimo se estrutural)"),
    ("adr_citado_inexistente", "ADR citado e inexistente na arquitetura"),
    ("adr_nunca_citado", "ADR nunca citado"),
    ("concluida_sem_review", "Concluído sem review"),
    ("review_bloqueado_aberto", "Review bloqueado sem round seguinte"),
    ("status_fora_do_vocabulario", "Status fora do vocabulário"),
    ("bloqueio_sem_motivo", "Bloqueado sem motivo"),
    ("tela_sem_tarefa", "Tela sem tarefa"),
    ("estado_sem_tarefa", "Estado de tela sem tarefa"),
)


def render_markdown(report, mermaid=False):
    columns = [("CA", "ca"), ("RN", "rn"), ("ADR", "adr")]
    if report["spec_ui"]:
        columns.append(("UI", "ui"))
    columns += [("T", "t"), ("Review", "r")]
    if report["git"]:
        columns.append(("Commits", "commits"))

    def cell(value):
        if isinstance(value, list):
            return ", ".join(value) or "—"
        return value or "—"

    out = ["# Matriz de rastreabilidade", ""]
    out.append("| " + " | ".join(title for title, _ in columns) + " |")
    out.append("|" + "---|" * len(columns))
    for row in report["matriz"]:
        out.append("| " + " | ".join(cell(row[key]) for _, key in columns) + " |")
    if not report["matriz"]:
        out.append("| " + " | ".join("—" for _ in columns) + " |")

    out += ["", "## Lacunas", ""]
    listed = False
    for key, label in GAP_LABELS:
        if key in report["lacunas"]:
            out.append("- **{}:** {}".format(label, ", ".join(report["lacunas"][key])))
            listed = True
    if not listed:
        out.append("Nenhuma lacuna mecânica.")

    for warning in report["avisos"]:
        out += ["", "> Aviso: {}".format(warning)]

    if mermaid:
        out += ["", "```mermaid", "graph LR"]
        edges = set()
        for rn, adrs in report["_rules"].items():
            for adr in adrs:
                edges.add("    {} --> {}".format(adr.replace("-", ""), rn.replace("-", "")))
        for row in report["matriz"]:
            for rn in row["rn"]:
                edges.add("    {} --> {}".format(rn.replace("-", ""), row["ca"].replace("-", "")))
            for t in row["t"]:
                edges.add("    {} --> {}".format(row["ca"].replace("-", ""), t.replace("-", "").replace(":", "_")))
        out += sorted(edges) + ["```"]
    return "\n".join(out) + "\n"


def main(argv=None):
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        prog=SCRIPT, description="Gera a matriz de rastreabilidade do pipeline SDD."
    )
    parser.add_argument("--root", default=".", help="raiz do projeto consumidor")
    parser.add_argument("--prd", default=None, help="restringe a um PRD e ao plano de mesmo numero")
    parser.add_argument("--json", action="store_true", help="saida estruturada")
    parser.add_argument("--mermaid", action="store_true", help="inclui o diagrama Mermaid")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        return fail_usage(SCRIPT, "raiz nao encontrada: {}".format(args.root))
    try:
        report = build(root, args.prd)
    except ValueError as exc:
        return fail_usage(SCRIPT, str(exc))

    if args.json:
        public = {k: v for k, v in report.items() if not k.startswith("_")}
        sys.stdout.write(json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_markdown(report, mermaid=args.mermaid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
