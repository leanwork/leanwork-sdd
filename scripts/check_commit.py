#!/usr/bin/env python3
"""Gate do trailer de rastreabilidade na mensagem de commit.

A trilha codigo -> requisito vem do `git log`: todo commit de tarefa carrega o
trailer `Refs: T-04, CA-01, CA-03`. Este script verifica o trailer em vez de
confiar que o agente lembrou dele. A convencao canonica esta em
`templates/id-conventions.md`, secao "Trailer de commit".

Adaptado de `check_commit.py` da skill `tlc-spec-lean` (Tech Leads Club,
CC-BY-4.0): reaproveita a leitura da mensagem por arquivo, `--message` ou stdin,
e o uso opcional como hook `commit-msg` do git. Nao valida Conventional Commits -
o que se verifica aqui e o trailer de IDs, que o tlc nao tem.

Uso:
    python scripts/check_commit.py [msgfile] [--message MSG] [--plan PLANO] [--strict]

Como hook do git, sem depender de agente:
    ln -s <plugin>/scripts/check_commit.py .git/hooks/commit-msg

Regras:
    ERROR  mensagem sem linha `Refs:`
    ERROR  ID malformado ou de tipo nao referenciavel (`R-XX` e local ao review)
    ERROR  trailer sem nenhuma `T-XX`
    ERROR  com `--plan`: `T-XX` citada que nao existe no plano
    WARN   ID repetido no trailer

Exit: 0 aprovado, 1 erro de conteudo, 2 erro de uso.
"""

import argparse
import os
import re
import sys

from _common import (
    Diagnostics,
    UsageError,
    enable_utf8_output,
    fail_usage,
    finish,
    load_document,
    parse_tasks,
    resolve_target,
)

SCRIPT = "check_commit"

TRAILER = re.compile(r"^Refs:\s*(?P<value>.*?)\s*$")
REFERENCEABLE_ID = re.compile(r"^(T|RN|CA|ADR|UI)-\d{2,}(\.[a-zA-Z][a-zA-Z0-9]*)?$")


def read_message(args):
    if args.message is not None:
        return args.message, "mensagem"
    if args.msgfile:
        # O git passa um caminho que existe. Qualquer outra coisa e a propria
        # mensagem, que e como se chama o script a mao.
        if os.path.isfile(args.msgfile):
            with open(args.msgfile, "r", encoding="utf-8") as handle:
                return handle.read(), args.msgfile
        return args.msgfile, "mensagem"
    if not sys.stdin.isatty():
        return sys.stdin.read(), "stdin"
    return "", "mensagem"


def extract_refs(message):
    """Devolve a lista de IDs de todas as linhas `Refs:`, ou None se nao houver."""
    found = None
    for line in message.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("#"):
            continue
        match = TRAILER.match(line.strip())
        if not match:
            continue
        found = found or []
        found += [token.strip() for token in match.group("value").split(",")]
    return found


def plan_task_ids(plan_path):
    """IDs `T-XX` declarados no plano, pelo mesmo parser dos validadores."""
    lines, mask = load_document(plan_path)
    return {task.id for task in parse_tasks(lines, mask)}


def check(message, diagnostics, known_tasks=None):
    refs = extract_refs(message)
    if refs is None:
        diagnostics.error(
            "mensagem sem trailer 'Refs:' - todo commit de tarefa cita a T-XX e "
            "os CA-XX que fecha, ex.: 'Refs: T-04, CA-01'"
        )
        return

    seen = set()
    tasks = []
    for token in refs:
        if not token:
            diagnostics.error("trailer 'Refs:' com item vazio")
            continue
        if not REFERENCEABLE_ID.match(token):
            diagnostics.error(
                "ID malformado ou nao referenciavel no trailer: '{}' - aceitos "
                "T-NN, RN-NN, CA-NN, ADR-NN e UI-NN".format(token)
            )
            continue
        if token in seen:
            diagnostics.warn("ID repetido no trailer: {}".format(token))
            continue
        seen.add(token)
        if token.startswith("T-"):
            tasks.append(token)

    if not tasks:
        diagnostics.error("trailer 'Refs:' sem nenhuma T-XX - o commit precisa nomear a tarefa")

    if known_tasks is not None:
        for task in tasks:
            if task not in known_tasks:
                diagnostics.error("{} citada no trailer nao existe no plano".format(task))


def main(argv=None):
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        prog=SCRIPT, description="Valida o trailer Refs: de uma mensagem de commit."
    )
    parser.add_argument(
        "msgfile", nargs="?", default=None,
        help="arquivo de mensagem (como o git passa ao commit-msg) ou a propria mensagem",
    )
    parser.add_argument("--message", default=None, help="a mensagem de commit como texto")
    parser.add_argument("--plan", default=None, help="plano para conferir as T-XX citadas")
    parser.add_argument("--root", default=".", help="raiz do projeto consumidor")
    parser.add_argument("--strict", action="store_true", help="promove warning a erro")
    args = parser.parse_args(argv)

    message, target = read_message(args)
    if not message.strip():
        return fail_usage(
            SCRIPT, "nenhuma mensagem informada (arquivo, --message ou stdin)"
        )

    known_tasks = None
    if args.plan is not None:
        try:
            plan_path = resolve_target(
                args.plan, args.root, ["docs/plans", "."], ["PLAN-*.md", "*.md"], "plano"
            )
            known_tasks = plan_task_ids(plan_path)
        except UsageError as exc:
            return fail_usage(SCRIPT, str(exc))

    diagnostics = Diagnostics()
    check(message, diagnostics, known_tasks)
    return finish(SCRIPT, target, diagnostics, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
