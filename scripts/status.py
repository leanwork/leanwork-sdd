#!/usr/bin/env python3
"""Estado do pipeline SDD Leanwork, lido dos artefatos em `docs/`.

Substitui por leitura deterministica o que `/leanwork-next` reconstruia lendo
cada arquivo: artefatos presentes, tarefas por status, tarefa `Em andamento`,
tarefa `Bloqueado` e o motivo, `Concluído` sem review, review `Bloqueado` sem
round seguinte, status fora do vocabulario e a proxima tarefa elegivel. O modelo
so interpreta a saida e escolhe a sugestao.

E relatorio, nao gate: sai com 0 sempre que consegue ler, mesmo com pendencias.

Limite conhecido: o nome do relatorio (`REVIEW-T-XX-...`) nao diz de qual plano
ele e. Com mais de um plano no projeto, o review de `T-04` vale para toda `T-04`
- o mesmo limite que a leitura manual tinha.

Uso:
    python scripts/status.py [--root DIR] [--json]

Exit: 0 leu os artefatos, 2 erro de uso.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from _common import (
    STATUS_VOCAB,
    UsageError,
    enable_utf8_output,
    fail_usage,
    fence_mask,
    find_recommendation,
    is_quick_track,
    load_document,
    parse_review_name,
    parse_tasks,
    read_lines,
    unwrap_envelope,
)

SCRIPT = "status"

ADR_DEFINITION = re.compile(r"^\s*#{1,6}\s*\**(ADR-\d{2,})\**", re.MULTILINE)


def files(root, relative, pattern):
    directory = root / relative
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob(pattern) if p.is_file())


def read_text(path):
    return "\n".join(unwrap_envelope(read_lines(path)))


def collect_artifacts(root):
    architecture = files(root, "docs/architecture", "proposta-arquitetural.md")
    adr_files = files(root, "docs/architecture/adrs", "*.md")
    adrs = set()
    for path in architecture + adr_files:
        adrs.update(ADR_DEFINITION.findall(read_text(path)))
    return {
        "arquitetura": bool(architecture),
        "adrs": sorted(adrs),
        "prds": [p.name for p in files(root, "docs/prds", "PRD-*.md")],
        "spec_ui": [p.name for p in files(root, "docs/prototype", "SPEC-UI-*.md")],
        "planos": [p.name for p in files(root, "docs/plans", "PLAN-*.md")],
        "reviews": [p.name for p in files(root, "docs/reviews", "REVIEW-*.md")],
        "claude_md": (root / "CLAUDE.md").is_file(),
    }


def collect_reviews(root):
    """Ultimo relatorio de cada tarefa, por round e depois por data."""
    latest = {}
    unnamed = []
    for path in files(root, "docs/reviews", "REVIEW-*.md"):
        parsed = parse_review_name(path)
        if parsed is None:
            unnamed.append(path.name)
            continue
        task_id, date, round_number = parsed
        lines = unwrap_envelope(read_lines(path))
        recommendation, _ = find_recommendation(lines, fence_mask(lines))
        entry = {
            "arquivo": path.name,
            "data": date,
            "round": round_number,
            "recomendacao": recommendation,
        }
        current = latest.get(task_id)
        if current is None or (round_number, date) > (current["round"], current["data"]):
            latest[task_id] = entry
    return latest, unnamed


def summarize_plan(path, reviews):
    lines, mask = load_document(path)
    tasks = parse_tasks(lines, mask)
    status = {task.id: (task.field("Status") or "").strip() for task in tasks}

    counts = {value: 0 for value in STATUS_VOCAB}
    in_progress, blocked, invalid = [], [], []
    done_without_review, open_blocking_reviews = [], []
    next_task = None

    for task in tasks:
        value = status[task.id]
        if value in counts:
            counts[value] += 1
        else:
            invalid.append({"id": task.id, "status": value})

        review = reviews.get(task.id)
        if value == "Em andamento":
            in_progress.append(task.id)
        elif value == "Bloqueado":
            blocked.append({"id": task.id, "bloqueio": task.block_reason()})
        elif value == "Concluído" and review is None:
            done_without_review.append(task.id)

        if review is not None and review["recomendacao"] == "Bloqueado":
            open_blocking_reviews.append(
                {"id": task.id, "review": review["arquivo"], "status": value}
            )

        if (
            next_task is None
            and value == "Pendente"
            and all(status.get(dep) == "Concluído" for dep in task.dependencies())
        ):
            next_task = {"id": task.id, "titulo": task.title.strip()}

    return {
        "arquivo": path.name,
        "trilha_rapida": is_quick_track(lines, mask),
        "tarefas": len(tasks),
        "por_status": counts,
        "em_andamento": in_progress,
        "bloqueadas": blocked,
        "concluidas_sem_review": done_without_review,
        "reviews_bloqueados_abertos": open_blocking_reviews,
        "status_fora_do_vocabulario": invalid,
        "proxima": next_task,
    }


def build_report(root):
    reviews, unnamed = collect_reviews(root)
    return {
        "raiz": str(root),
        "artefatos": collect_artifacts(root),
        "planos": [summarize_plan(p, reviews) for p in files(root, "docs/plans", "PLAN-*.md")],
        "reviews_fora_da_convencao": unnamed,
    }


def yes(flag):
    return "sim" if flag else "não"


def render_markdown(report):
    art = report["artefatos"]
    out = [
        "# Estado do pipeline",
        "",
        "| Artefato | Estado |",
        "|---|---|",
        "| Arquitetura | {}{} |".format(
            yes(art["arquitetura"]),
            " — {}".format(", ".join(art["adrs"])) if art["adrs"] else "",
        ),
        "| PRDs | {} |".format(", ".join(art["prds"]) or "nenhum"),
        "| SPEC-UI | {} |".format(", ".join(art["spec_ui"]) or "nenhuma"),
        "| Planos | {} |".format(", ".join(art["planos"]) or "nenhum"),
        "| Reviews | {} |".format(len(art["reviews"])),
        "| CLAUDE.md | {} |".format(yes(art["claude_md"])),
    ]

    for plan in report["planos"]:
        counts = plan["por_status"]
        out += [
            "",
            "## {}{}".format(plan["arquivo"], " (trilha rápida)" if plan["trilha_rapida"] else ""),
            "",
            "Tarefas: {} — {}".format(
                plan["tarefas"],
                " · ".join("{} {}".format(counts[v], v) for v in STATUS_VOCAB),
            ),
            "",
        ]
        items = []
        if plan["reviews_bloqueados_abertos"]:
            items.append("- Review bloqueado sem round seguinte: " + ", ".join(
                "{} ({}, status {})".format(r["id"], r["review"], r["status"])
                for r in plan["reviews_bloqueados_abertos"]
            ))
        if plan["bloqueadas"]:
            items.append("- Bloqueado: " + "; ".join(
                "{} — {}".format(b["id"], b["bloqueio"] or "SEM MOTIVO REGISTRADO")
                for b in plan["bloqueadas"]
            ))
        if plan["concluidas_sem_review"]:
            items.append("- Concluído sem review: " + ", ".join(plan["concluidas_sem_review"]))
        if plan["em_andamento"]:
            items.append("- Em andamento: " + ", ".join(plan["em_andamento"]))
        if plan["status_fora_do_vocabulario"]:
            items.append("- Status fora do vocabulário: " + ", ".join(
                "{} ('{}')".format(i["id"], i["status"]) for i in plan["status_fora_do_vocabulario"]
            ))
        nxt = plan["proxima"]
        items.append(
            "- Próxima elegível: {}".format(
                "{} — {}".format(nxt["id"], nxt["titulo"]) if nxt else "nenhuma"
            )
        )
        out += items

    if report["reviews_fora_da_convencao"]:
        out += [
            "",
            "Reviews com nome fora da convenção `REVIEW-T-XX-AAAA-MM-DD[-roundN].md`: "
            + ", ".join(report["reviews_fora_da_convencao"]),
        ]
    return "\n".join(out) + "\n"


def main(argv=None):
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        prog=SCRIPT, description="Relata o estado do pipeline SDD a partir de docs/."
    )
    parser.add_argument("--root", default=".", help="raiz do projeto consumidor")
    parser.add_argument("--json", action="store_true", help="saida estruturada")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        return fail_usage(SCRIPT, "raiz nao encontrada: {}".format(args.root))

    try:
        report = build_report(root)
    except UsageError as exc:
        return fail_usage(SCRIPT, str(exc))

    if args.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
