#!/usr/bin/env python3
"""Gate do relatorio de review do pipeline SDD Leanwork.

Fecha os modos pelos quais um relatorio aprova sem ter verificado nada:
placeholder nao preenchido, recomendacao incoerente com a severidade dos
findings, e cobertura marcada com visto sem evidencia.

Estrutura de referencia:
`skills/reviewer-leanwork/references/review-template.md`.

Evidence-or-zero: em `Cobertura por RN`, `Cobertura por CA` e `Verificação da
Decisão Arquitetural`, uma entrada marcada como coberta precisa citar
`arquivo:linha`. Nome de metodo de teste sozinho descreve intencao, nao
comportamento verificado - e nao conta como evidencia.

Excecao de ausencia objetiva
----------------------------
Um finding pode nao ter `arquivo:linha` quando aponta a ausencia de algo: nao
existe onde citar. A excecao e reconhecida de forma estreita, de proposito - ela
e a brecha por onde um relatorio preguicoso passaria. Para valer, a evidencia
precisa reunir as duas coisas:

  1. uma marca de ausencia do vocabulario fechado em ABSENCE_MARKERS
  2. o alvo ausente, nomeado - um ID do pipeline ou um caminho de arquivo

"Nao verificado", "nao deu tempo" ou "ausente" sozinho nao passam.

Uso:
    python scripts/validate_review.py [alvo] [--root DIR] [--strict]

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
    has_file_line,
    parse_field,
    read_lines,
    resolve_target,
    strip_decoration,
    unwrap_envelope,
)

SCRIPT = "validate_review"

RECOMMENDATION_VOCAB = ("Aprovado", "Aprovado com ressalvas", "Bloqueado")

SEVERITY_SECTIONS = (
    ("Bloqueante", ("bloqueante",)),
    ("Importante", ("importante",)),
    ("Sugestão", ("sugestão", "sugestao")),
)

COVERAGE_SECTIONS = (
    ("Cobertura por RN", ("cobertura por rn",)),
    ("Cobertura por CA", ("cobertura por ca",)),
    (
        "Verificação da Decisão Arquitetural",
        ("verificação da decisão arquitetural", "verificacao da decisao arquitetural"),
    ),
)

ABSENCE_MARKERS = (
    "não existe",
    "nao existe",
    "não há",
    "nao ha",
    "não encontrado",
    "nao encontrado",
    "não encontrada",
    "nao encontrada",
    "inexistente",
    "nenhum teste",
    "nenhuma cobertura",
)

NAMED_TARGET = re.compile(
    r"(?:(?:RN|CA|ADR|UI|T)-\d{2,})|(?:[\w./\\-]+\.[A-Za-z0-9]{1,6}\b)"
)

HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*$")
FINDING_HEADING = re.compile(r"^#{3,6}\s+\**(?P<id>R-[\w-]*)\**")
FINDING_ID = re.compile(r"^R-\d{2,}$")
ENTRY_HEADING = re.compile(r"^#{3,6}\s+\**(?P<id>(?:RN|CA|ADR|UI)-\d{2,})\**")
ASSERTION_FIELD = re.compile(r"\*\*Asser[çc][ãa]o:\*\*\s*\S")
ASSERTION_REQUIRED = ("Cobertura por RN", "Cobertura por CA")
COVERED = ("✅",)
NOT_COVERED = ("❌", "⚠")
RECOMMENDATION_LINE = re.compile(r"\*\*Recomendação final:\*\*\s*(?P<value>.*?)\s*$")
SURVIVOR_ROW = re.compile(r"^\s*\|.*Sobreviveu", re.IGNORECASE)
REFERENCED_FINDING = re.compile(r"R-\d{2,}")


class Block:
    """Um trecho do relatorio delimitado por um heading."""

    def __init__(self, identifier, line_number, level):
        self.id = identifier
        self.line = line_number
        self.level = level
        self.lines = []

    @property
    def text(self):
        return "\n".join(self.lines)


def is_absence_claim(text):
    lowered = text.lower()
    if not any(marker in lowered for marker in ABSENCE_MARKERS):
        return False
    return bool(NAMED_TARGET.search(text))


def section_of(lines, mask, keywords, levels=(2,)):
    """Recorta a secao de nivel `levels` cujo titulo casa com `keywords`."""
    start = None
    level = None
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        heading = HEADING.match(line)
        if not heading:
            continue
        depth = len(heading.group("hashes"))
        title = strip_decoration(heading.group("text")).lower()
        if start is None:
            if depth in levels and any(word in title for word in keywords):
                start = index
                level = depth
            continue
        if depth <= level:
            return lines[start:index], start
    if start is None:
        return None, None
    return lines[start:], start


def collect_findings(lines, mask, diagnostics):
    """Le os findings R-XX e a severidade da secao que os contem."""
    findings = []
    current_severity = None
    current = None

    for index, line in enumerate(lines):
        if mask[index]:
            if current is not None:
                current.lines.append(line)
            continue

        heading = HEADING.match(line)
        if heading:
            finding = FINDING_HEADING.match(line)
            if finding:
                raw_id = finding.group("id")
                if not FINDING_ID.match(raw_id):
                    diagnostics.error(
                        "linha {}: ID de finding malformado '{}' - o padrao e "
                        "R-NN".format(index + 1, raw_id)
                    )
                    current = None
                    continue
                current = Block(raw_id, index + 1, len(heading.group("hashes")))
                current.severity = current_severity
                findings.append(current)
                continue

            title = strip_decoration(heading.group("text")).lower()
            for severity, keywords in SEVERITY_SECTIONS:
                if any(word in title for word in keywords):
                    current_severity = severity
                    break
            current = None
            continue

        if current is not None:
            current.lines.append(line)

    return findings


def check_finding_ids(findings, diagnostics):
    if not findings:
        diagnostics.warn(
            "relatorio sem nenhum finding R-XX - possivel, mas raro: confira se a "
            "verificacao realmente aconteceu"
        )
        return

    seen = {}
    for finding in findings:
        if finding.id in seen:
            diagnostics.error(
                "{} duplicado: linhas {} e {}".format(
                    finding.id, seen[finding.id], finding.line
                )
            )
            continue
        seen[finding.id] = finding.line

    numbers = sorted(int(identifier.split("-")[1]) for identifier in seen)
    if numbers and numbers[0] != 1:
        diagnostics.error(
            "numeracao de findings comeca em R-{:02d} - cada relatorio recomeca em "
            "R-01".format(numbers[0])
        )
    for position, number in enumerate(numbers, start=1):
        if number != position:
            diagnostics.error(
                "sequencia de findings com buraco: esperado R-{:02d}, encontrado "
                "R-{:02d}".format(position, number)
            )
            break


def check_finding_evidence(findings, diagnostics):
    for finding in findings:
        evidence = None
        for line in finding.lines:
            field = parse_field(line)
            if field and field[0].lower().startswith("evid"):
                evidence = field[1]
                break

        if evidence is None:
            diagnostics.error(
                "{} (linha {}): sem campo '**Evidência:**'".format(
                    finding.id, finding.line
                )
            )
            continue

        if has_file_line(evidence):
            continue

        if is_absence_claim(evidence) or is_absence_claim(finding.text):
            continue

        diagnostics.error(
            "{} (linha {}): evidencia sem citacao arquivo:linha - '{}'".format(
                finding.id, finding.line, evidence.strip() or "(vazia)"
            )
        )


def read_recommendation(lines, mask, diagnostics):
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        match = RECOMMENDATION_LINE.search(line)
        if not match:
            continue
        value = strip_decoration(match.group("value"))
        if "/" in value or not value:
            diagnostics.error(
                "linha {}: recomendacao final ainda no placeholder - escolha um "
                "valor de {}".format(index + 1, " / ".join(RECOMMENDATION_VOCAB))
            )
            return None
        if value not in RECOMMENDATION_VOCAB:
            diagnostics.error(
                "linha {}: recomendacao final '{}' fora do vocabulario {}".format(
                    index + 1, value, " / ".join(RECOMMENDATION_VOCAB)
                )
            )
            return None
        return value

    diagnostics.error("recomendacao final ausente: campo '**Recomendação final:**'")
    return None


def check_coherence(recommendation, findings, diagnostics):
    if recommendation is None:
        return

    blockers = [f for f in findings if getattr(f, "severity", None) == "Bloqueante"]

    if blockers and recommendation != "Bloqueado":
        diagnostics.error(
            "incoerencia de severidade: {} finding(s) Bloqueante(s) ({}) e "
            "recomendacao '{}' - Bloqueante aberto exige 'Bloqueado'".format(
                len(blockers),
                ", ".join(f.id for f in blockers),
                recommendation,
            )
        )

    if recommendation == "Aprovado" and findings:
        diagnostics.error(
            "incoerencia de severidade: recomendacao 'Aprovado' com {} finding(s) "
            "aberto(s) ({}) - use 'Aprovado com ressalvas'".format(
                len(findings), ", ".join(f.id for f in findings)
            )
        )


def check_coverage(lines, mask, diagnostics):
    """Evidence-or-zero: entrada coberta cita arquivo:linha e reproduz a assercao.

    Os dois campos respondem perguntas diferentes: `arquivo:linha` diz onde
    olhar, a assercao diz o que foi verificado. Nome de teste declara intencao e
    diverge da assercao com frequencia - e assim que um teste que so confere
    `status == 200` passa por cobertura de um cenario sobre estoque.

    A assercao e exigida so em RN e CA. Conformidade de ADR e estrutural - a
    evidencia e o arquivo onde a decisao esta materializada, nao uma expressao
    de teste.
    """
    for label, keywords in COVERAGE_SECTIONS:
        section, offset = section_of(lines, mask, keywords)
        if section is None:
            continue

        entries = []
        current = None
        for position, line in enumerate(section):
            heading = HEADING.match(line)
            if heading:
                entry = ENTRY_HEADING.match(line)
                if entry:
                    current = Block(
                        entry.group("id"),
                        offset + position + 1,
                        len(heading.group("hashes")),
                    )
                    entries.append(current)
                else:
                    current = None
                continue
            if current is not None:
                current.lines.append(line)

        for entry in entries:
            body = entry.text
            if not any(mark in body for mark in COVERED):
                continue
            if any(mark in body for mark in NOT_COVERED):
                continue
            if not has_file_line(body):
                diagnostics.error(
                    "{} ({}, linha {}): marcado como coberto sem citacao arquivo:linha "
                    "- nome de teste nao e evidencia".format(entry.id, label, entry.line)
                )
                continue
            if label in ASSERTION_REQUIRED and not ASSERTION_FIELD.search(body):
                diagnostics.error(
                    "{} ({}, linha {}): marcado como coberto sem campo "
                    "'**Asserção:**' - arquivo:linha diz onde olhar, a assercao diz "
                    "o que foi verificado".format(entry.id, label, entry.line)
                )


def check_sensor(lines, mask, findings, diagnostics):
    """Sensor de discriminacao: mutante sobrevivente exige finding Bloqueante.

    Secao ausente e WARN, nao ERROR: ha projeto legitimo sem suite executavel, e
    o gate nao inventa bloqueio onde nao ha o que medir.
    """
    section, offset = section_of(lines, mask, ("sensor de discriminação", "sensor de discriminacao"))
    if section is None:
        diagnostics.warn(
            "secao 'Sensor de discriminação' ausente - sem ela nao da para saber se "
            "os testes discriminam comportamento"
        )
        return

    blockers = {
        finding.id
        for finding in findings
        if getattr(finding, "severity", None) == "Bloqueante"
    }

    for position, line in enumerate(section):
        if not SURVIVOR_ROW.match(line):
            continue
        referenced = REFERENCED_FINDING.findall(line)
        if not referenced:
            diagnostics.error(
                "Sensor de discriminação (linha {}): mutante sobrevivente sem R-XX "
                "correspondente - sobrevivente e Bloqueante".format(
                    offset + position + 1
                )
            )
            continue
        if not any(identifier in blockers for identifier in referenced):
            diagnostics.error(
                "Sensor de discriminação (linha {}): mutante sobrevivente aponta "
                "para {}, que nao e Bloqueante".format(
                    offset + position + 1, ", ".join(referenced)
                )
            )


def check_round(path, lines, mask, diagnostics):
    if not re.search(r"-round\d+", path.name, re.IGNORECASE):
        return
    section, _ = section_of(lines, mask, ("round anterior",))
    if section is None:
        diagnostics.warn(
            "arquivo com sufixo de round sem secao 'Round anterior' - sem ela nao da "
            "para saber o que foi resolvido"
        )


def check_placeholders(lines, mask, diagnostics):
    for number, snippet in find_placeholders(lines, mask):
        diagnostics.error(
            "linha {}: placeholder de template nao preenchido: {}".format(
                number, snippet
            )
        )


def validate(path, diagnostics):
    lines = unwrap_envelope(read_lines(path))
    mask = fence_mask(lines)

    findings = collect_findings(lines, mask, diagnostics)
    check_finding_ids(findings, diagnostics)
    check_finding_evidence(findings, diagnostics)

    recommendation = read_recommendation(lines, mask, diagnostics)
    check_coherence(recommendation, findings, diagnostics)

    check_coverage(lines, mask, diagnostics)
    check_sensor(lines, mask, findings, diagnostics)
    check_round(path, lines, mask, diagnostics)
    check_placeholders(lines, mask, diagnostics)


def main(argv=None):
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        prog=SCRIPT, description="Valida um relatorio de review do pipeline SDD."
    )
    parser.add_argument("target", nargs="?", help="arquivo ou diretorio do relatorio")
    parser.add_argument("--root", default=".", help="raiz do projeto consumidor")
    parser.add_argument("--strict", action="store_true", help="promove warning a erro")
    args = parser.parse_args(argv)

    try:
        path = resolve_target(
            args.target,
            args.root,
            ["docs/reviews", "."],
            ["REVIEW-*.md", "*.md"],
            "relatorio de review",
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
