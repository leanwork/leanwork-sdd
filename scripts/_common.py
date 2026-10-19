#!/usr/bin/env python3
"""Harness compartilhado dos validadores do pipeline SDD Leanwork.

Contrato de saida, identico nos tres validadores:

    exit 0 - artefato aprovado
    exit 1 - erro de conteudo no artefato
    exit 2 - erro de uso (alvo nao localizado, alvo ambiguo, argumento invalido)

Diagnosticos saem como "  ERROR <mensagem>" / "  WARN <mensagem>", em ordem de
descoberta, fechando com "<script>: N error(s), M warning(s) in <path>".

Alem do contrato de saida e do markdown generico, este modulo guarda o parsing
de plano e de review que mais de um script le: tarefas `#### T-XX`, cabecalho de
trilha rapida, recomendacao final e nome do relatorio. As regras - o que e erro,
o que e aviso - ficam em cada validador; aqui so se le.

Python 3.8+, stdlib apenas.
"""

import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_CONTENT = 1
EXIT_USAGE = 2


class UsageError(Exception):
    """Erro de uso: vira exit 2 sem passar pelo coletor de diagnosticos."""


class Diagnostics:
    """Coletor de diagnosticos, preservando a ordem de descoberta."""

    def __init__(self):
        self.items = []

    def error(self, message):
        self.items.append(("ERROR", message))

    def warn(self, message):
        self.items.append(("WARN", message))

    def counts(self, strict=False):
        errors = sum(1 for level, _ in self.items if level == "ERROR")
        warnings = sum(1 for level, _ in self.items if level == "WARN")
        if strict:
            return errors + warnings, 0
        return errors, warnings


def finish(script, target, diagnostics, strict=False, stream=None):
    """Renderiza os diagnosticos e devolve o exit code do contrato."""
    stream = stream or sys.stdout
    for level, message in diagnostics.items:
        effective = "ERROR" if (strict and level == "WARN") else level
        stream.write("  {} {}\n".format(effective, message))
    errors, warnings = diagnostics.counts(strict=strict)
    stream.write(
        "{}: {} error(s), {} warning(s) in {}\n".format(script, errors, warnings, target)
    )
    return EXIT_CONTENT if errors else EXIT_OK


def fail_usage(script, message, stream=None):
    """Renderiza um erro de uso no mesmo formato e devolve exit 2."""
    stream = stream or sys.stderr
    stream.write("  ERROR {}\n".format(message))
    stream.write("{}: usage error\n".format(script))
    return EXIT_USAGE


def resolve_target(explicit, root, search_dirs, patterns, kind):
    """Resolve o artefato alvo, cobrindo as quatro rotas previstas.

    1. caminho de arquivo explicito
    2. diretorio explicito, varrido pelos padroes
    3. sem argumento: auto-deteccao sob `root`, quando ha exatamente um candidato
    4. varios candidatos: UsageError listando as opcoes

    `patterns` e ordenado por precedencia: o primeiro padrao que casar dentro de
    um diretorio define o conjunto de candidatos daquele diretorio.
    """
    root = Path(root)

    if explicit is not None:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            direct = candidate if candidate.exists() else root / candidate
        else:
            direct = candidate
        if direct.is_file():
            return direct
        if direct.is_dir():
            found = _scan(direct, patterns)
            return _pick(found, kind, str(direct))
        raise UsageError("{} nao encontrado: {}".format(kind, explicit))

    found = []
    for relative in search_dirs:
        directory = root / relative
        if directory.is_dir():
            found = _scan(directory, patterns)
            if found:
                break
    return _pick(found, kind, str(root))


def _scan(directory, patterns):
    for pattern in patterns:
        matches = sorted(p for p in directory.glob(pattern) if p.is_file())
        if matches:
            return matches
    return []


def _pick(found, kind, where):
    if not found:
        raise UsageError("nenhum {} encontrado em {}".format(kind, where))
    if len(found) > 1:
        options = ", ".join(p.name for p in found)
        raise UsageError(
            "mais de um {} encontrado em {}: {} - informe qual validar".format(
                kind, where, options
            )
        )
    return found[0]


def read_lines(path):
    """Le o arquivo como UTF-8 e devolve a lista de linhas sem o terminador."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise UsageError("nao foi possivel ler {}: {}".format(path, exc))
    return text.replace("\r\n", "\n").split("\n")


ENVELOPE_OPEN = re.compile(r"^`{4,}\s*\w*\s*$")


def unwrap_envelope(lines):
    """Descasca o envelope de quatro crases usado pelos arquivos de template.

    Arquivo sem envelope volta inalterado. O envelope e andaime do template e
    nao faz parte do documento que o agente produz.
    """
    open_at = None
    for index, line in enumerate(lines):
        if ENVELOPE_OPEN.match(line):
            open_at = index
            break
    if open_at is None:
        return lines
    ticks = len(re.match(r"^`+", lines[open_at]).group(0))
    closer = re.compile(r"^`{" + str(ticks) + r",}\s*$")
    for index in range(len(lines) - 1, open_at, -1):
        if closer.match(lines[index]):
            return lines[open_at + 1 : index]
    return lines


def fence_mask(lines):
    """Marca as linhas que estao dentro de uma cerca de codigo.

    Conteudo dentro de cerca e ilustrativo: diagrama Mermaid, exemplo de
    template, fragmento de codigo. Nenhuma regra estrutural se aplica a ele.
    """
    mask = [False] * len(lines)
    open_ticks = None
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(`{3,})", line)
        if open_ticks is None:
            if match:
                open_ticks = len(match.group(1))
                mask[index] = True
            continue
        mask[index] = True
        if match and len(match.group(1)) >= open_ticks and not line.strip().strip("`"):
            open_ticks = None
    return mask


INLINE_CODE = re.compile(r"`[^`]*`")
PLACEHOLDER_DATE = re.compile(r"AAAA-MM-DD")
PLACEHOLDER_ELLIPSIS = re.compile(r"\[\.\.\.\]")
PLACEHOLDER_OPTIONS = re.compile(r"(?<![\w`])\[[^\[\]]*[/|][^\[\]]*\](?!\()")
PLACEHOLDER_PROSE = re.compile(r"(?<![\w`])\[[a-z][^\[\]]{11,}\](?!\()")


def find_placeholders(lines, mask=None):
    """Devolve (numero_da_linha, trecho) dos placeholders de template restantes.

    Reconhece quatro formas, todas deixadas pelos templates do pipeline: a data
    `AAAA-MM-DD`, o literal `[...]`, a lista de opcoes `[a / b / c]` e a prosa
    instrutiva `[descricao do que preencher]`. Link markdown, checkbox, no de
    Mermaid e ID entre colchetes (`[CA-01]`) ficam de fora de proposito.
    """
    mask = mask or [False] * len(lines)
    hits = []
    for index, raw in enumerate(lines):
        if index < len(mask) and mask[index]:
            continue
        line = INLINE_CODE.sub(" ", raw)
        for pattern in (
            PLACEHOLDER_DATE,
            PLACEHOLDER_ELLIPSIS,
            PLACEHOLDER_OPTIONS,
            PLACEHOLDER_PROSE,
        ):
            match = pattern.search(line)
            if match:
                hits.append((index + 1, match.group(0)))
                break
    return hits


FIELD = re.compile(r"^\s*[-*]\s*\*\*(?P<name>[^*]+?):\*\*\s*(?P<value>.*?)\s*$")


def parse_field(line):
    """Le uma linha no formato `- **Campo:** valor`. Devolve (nome, valor) ou None."""
    match = FIELD.match(line)
    if not match:
        return None
    return match.group("name").strip(), match.group("value").strip()


def strip_decoration(value):
    """Remove emoji decorativo e enfase markdown de um valor de campo."""
    cleaned = value.replace("**", "").replace("`", "")
    for emoji in ("✅", "⚠️", "⚠", "⛔", "❌", "\U0001f534", "\U0001f7e1", "\U0001f7e2"):
        cleaned = cleaned.replace(emoji, "")
    return cleaned.strip()


FILE_LINE = re.compile(r"[\w./\\-]+\.[A-Za-z0-9]+:\d+")


def has_file_line(text):
    """Confere se o texto cita uma evidencia no formato arquivo:linha."""
    return bool(FILE_LINE.search(text))


def enable_utf8_output():
    """Garante que emoji nos diagnosticos nao quebre o console do Windows."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


# --------------------------------------------------------------------------
# Plano
# --------------------------------------------------------------------------

STATUS_VOCAB = ("Pendente", "Em andamento", "Concluído", "Bloqueado")

HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*$")
TASK_HEADING = re.compile(r"^####\s+(?P<id>\S+)\s*(?:[—–-]\s*(?P<title>.*))?$")
BLOCK_MARKER = re.compile(r"^\*\*(?P<name>[^*]+?):\*\*\s*$")
THEMATIC_BREAK = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
TASK_ID = re.compile(r"^T-\d{2,}$")
TASK_REFERENCE = re.compile(r"T-\d+")
QUICK_TRACK_HEADER = re.compile(
    r"^\*\*PRD de refer[êe]ncia:\*\*.*trilha r[áa]pida", re.IGNORECASE
)


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

    def block_reason(self):
        """Valor de `**Bloqueio:**`, mesmo quando o campo veio depois de um bloco."""
        reason = self.field("Bloqueio")
        if reason is not None:
            return reason
        for _, text in self.body:
            field = parse_field(text)
            if field and field[0] == "Bloqueio":
                return field[1]
        return None

    def dependencies(self):
        """IDs citados em `Depende de:`; vazio para `nenhuma` ou campo ausente."""
        raw = self.field("Depende de") or ""
        if raw.strip().lower().startswith("nenhuma"):
            return []
        return TASK_REFERENCE.findall(raw)


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


def is_quick_track(lines, mask):
    """O plano e de trilha rapida quando o cabecalho declara isso.

    So o cabecalho conta - antes da primeira secao `## ` -, para que uma mencao
    a trilha rapida no corpo de um plano completo nao mude as regras dele.
    """
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        heading = HEADING.match(line)
        if heading and len(heading.group("hashes")) == 2:
            return False
        if QUICK_TRACK_HEADER.match(line.strip()):
            return True
    return False


# --------------------------------------------------------------------------
# Review
# --------------------------------------------------------------------------

RECOMMENDATION_VOCAB = ("Aprovado", "Aprovado com ressalvas", "Bloqueado")
RECOMMENDATION_LINE = re.compile(r"\*\*Recomendação final:\*\*\s*(?P<value>.*?)\s*$")
REVIEW_NAME = re.compile(
    r"^REVIEW-(?P<task>T-\d{2,})-(?P<date>\d{4}-\d{2}-\d{2})(?:-round(?P<round>\d+))?\.md$",
    re.IGNORECASE,
)


def find_recommendation(lines, mask):
    """Devolve (valor sem decoracao, indice da linha), ou (None, None)."""
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        match = RECOMMENDATION_LINE.search(line)
        if match:
            return strip_decoration(match.group("value")), index
    return None, None


def parse_review_name(path):
    """Le `REVIEW-T-XX-AAAA-MM-DD[-roundN].md`. Devolve (tarefa, data, round)
    ou None quando o nome foge da convencao. Sem sufixo, o round e 1."""
    match = REVIEW_NAME.match(Path(path).name)
    if not match:
        return None
    return match.group("task").upper(), match.group("date"), int(match.group("round") or 1)
