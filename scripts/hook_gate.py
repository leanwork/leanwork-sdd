#!/usr/bin/env python3
"""Hook PostToolUse que roda o gate do artefato editado.

Disparado por `hooks/hooks.json` depois de `Write` ou `Edit`. Le do stdin o JSON
do evento, pega `tool_input.file_path` e decide pelo caminho:

- `docs/plans/*.md`   -> `validate_plan.py`
- `docs/reviews/*.md` -> `validate_review.py`
- qualquer outro      -> nada a fazer, exit 0

O filtro por caminho fica aqui, e nao no campo `if` do hook, porque a
documentacao do Claude Code nao fecha a base do caminho relativo quando o hook
vem de plugin (PLAN-002, T-13). `validate_ids.py` nao entra: depende de PRD,
arquitetura e SPEC-UI, nao da edicao, e continua chamado por `/leanwork-execute`.

Uso:
    python scripts/hook_gate.py < evento.json

Exit: 0 artefato aprovado ou fora do escopo; 2 gate reprovado - em PostToolUse
a edicao ja aconteceu, e o stderr volta ao modelo para ele corrigir. Entrada
ilegivel ou erro de uso do validador nao bloqueia: o hook nao pode virar ruido
em edicao que nao e dele.
"""

import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

SCRIPT = "hook_gate"
SCRIPTS_DIR = Path(__file__).resolve().parent

GATES = (
    (("docs", "plans"), "validate_plan.py"),
    (("docs", "reviews"), "validate_review.py"),
)


def pick_gate(file_path, cwd):
    """Validador do artefato, ou None quando o caminho nao e de artefato."""
    path = Path(file_path)
    if not path.is_absolute() and cwd:
        path = Path(cwd) / path
    try:
        relative = path.resolve().relative_to(Path(cwd).resolve()) if cwd else path
        parts = PurePosixPath(relative.as_posix()).parts
    except ValueError:
        parts = PurePosixPath(path.as_posix()).parts

    if not parts or not parts[-1].lower().endswith(".md"):
        return None
    folders = tuple(part.lower() for part in parts[:-1])
    for prefix, script in GATES:
        # O par de pastas em qualquer ponto do caminho: cobre arquivo fora do
        # cwd e monorepo com `docs/` por modulo.
        for start in range(len(folders) - len(prefix) + 1):
            if folders[start : start + len(prefix)] == prefix:
                return script
    return None


def main():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass

    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(event, dict):
        return 0

    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not file_path:
        return 0

    cwd = event.get("cwd") or ""
    script = pick_gate(file_path, cwd)
    if script is None:
        return 0

    target = Path(file_path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target
    if not target.is_file():
        return 0

    command = [sys.executable, str(SCRIPTS_DIR / script), str(target)]
    if cwd:
        command += ["--root", cwd]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
    )

    if completed.returncode == 1:
        sys.stderr.write(
            "{}: {} reprovou {} - corrigir o artefato e salvar de novo.\n".format(
                SCRIPT, script, target.name
            )
        )
        sys.stderr.write(completed.stdout or "")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
