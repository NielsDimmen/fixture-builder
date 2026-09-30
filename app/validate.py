from __future__ import annotations

import re
from dataclasses import dataclass, field

RANGE_TWO_NUMBERS = re.compile(
    r"^range\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(.+?)\s*$"
)
RANGE_LINE = re.compile(r"^range\s*=")
PARAM_LINE = re.compile(r"^parameter\s*=")
FIXTURE_LINE = re.compile(r'^fixture\s*=\s*(.+)$')
COLOR_LINE = re.compile(r"^color\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")
DEFAULT_LINE = re.compile(r"^default\s*=\s*(\d+)\s*$")
HIGHLIGHT_LINE = re.compile(r"^highlight\s*=\s*(\d+)\s*$")
OPTION_LINE = re.compile(r"^option\s*=\s*skip\s*$")
MACRO_LINE = re.compile(r"^macro\s*=")
STEP_LINE = re.compile(r"^step\s*=")
MANUFACTURER_LINE = re.compile(r"^manufacturer\s*=")
ALLOWED_PREFIXES = (
    "manufacturer",
    "fixture",
    "color",
    "parameter",
    "default",
    "highlight",
    "option",
    "range",
    "macro",
    "step",
)
CHANNEL_IN_NAME = re.compile(r"(\d+)\s*(?:CH|ch)\b")


@dataclass
class ValidationIssue:
    line: int
    message: str


@dataclass
class FixtureInfo:
    name: str
    mode: str
    start_line: int
    parameters: int


@dataclass
class ValidationResult:
    ok: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    fixtures: list[FixtureInfo] = field(default_factory=list)

    def as_text(self) -> str:
        if self.ok:
            return "OK"
        return "\n".join(f"Line {item.line}: {item.message}" for item in self.issues)


def _unquoted_label_starts_with_digit(label: str) -> bool:
    text = label.strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        return False
    return bool(re.match(r"^\d", text))


def _parse_fixture_header(raw: str) -> tuple[str, str]:
    value = raw.strip()
    match = re.match(r'^([^,]+),\s*"([^"]*)"\s*$', value)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    match = re.match(r"^([^,]+),\s*(.+)$", value)
    if match:
        return match.group(1).strip(), match.group(2).strip().strip('"')
    return value, ""


def validate_dmxlan(text: str) -> ValidationResult:
    issues: list[ValidationIssue] = []
    fixtures: list[FixtureInfo] = []
    current: FixtureInfo | None = None

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for index, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue

        key = line.split("=", 1)[0].strip().lower()
        if key not in ALLOWED_PREFIXES:
            issues.append(ValidationIssue(index, f"Unknown keyword '{key}'."))
            continue

        if MANUFACTURER_LINE.match(line):
            continue

        fixture_match = FIXTURE_LINE.match(line)
        if fixture_match:
            if current:
                fixtures.append(current)
            name, mode = _parse_fixture_header(fixture_match.group(1))
            current = FixtureInfo(name=name, mode=mode, start_line=index, parameters=0)
            continue

        if COLOR_LINE.match(line):
            continue
        if line.lower().startswith("color"):
            issues.append(ValidationIssue(index, "color must be 'color = R, G, B' with three numbers 0-255."))
            continue

        if PARAM_LINE.match(line):
            if current is None:
                issues.append(ValidationIssue(index, "parameter before fixture header."))
            else:
                current.parameters += 1
            continue

        if DEFAULT_LINE.match(line) or HIGHLIGHT_LINE.match(line) or OPTION_LINE.match(line):
            continue
        if line.lower().startswith("default") or line.lower().startswith("highlight"):
            issues.append(ValidationIssue(index, "default/highlight must be a whole number 0-255."))
            continue
        if line.lower().startswith("option"):
            issues.append(ValidationIssue(index, "option must be 'option = skip'."))
            continue

        if RANGE_LINE.match(line):
            match = RANGE_TWO_NUMBERS.match(line)
            if not match:
                issues.append(
                    ValidationIssue(
                        index,
                        "range is not a range without two DMX numbers. Use 'range = start, end, label' "
                        "(example: range = 136, 143, No function).",
                    )
                )
                continue
            start, end = int(match.group(1)), int(match.group(2))
            label = match.group(3)
            if not (0 <= start <= 255 and 0 <= end <= 255):
                issues.append(ValidationIssue(index, "range values must be 0-255."))
            if start > end:
                issues.append(ValidationIssue(index, "range start is higher than end."))
            if _unquoted_label_starts_with_digit(label):
                issues.append(
                    ValidationIssue(
                        index,
                        'labels that start with a digit must be quoted, e.g. range = 0, 255, "7200K - 3200K".',
                    )
                )
            continue

        if MACRO_LINE.match(line) or STEP_LINE.match(line):
            continue

        issues.append(ValidationIssue(index, f"Could not parse line: {line}"))

    if current:
        fixtures.append(current)

    if not fixtures:
        issues.append(ValidationIssue(1, "No fixture = ... header found."))

    for fixture in fixtures:
        if fixture.parameters == 0:
            issues.append(ValidationIssue(fixture.start_line, f"{fixture.name} has no parameters."))
        expected = _expected_channels(fixture.mode) or _expected_channels(fixture.name)
        if expected and fixture.parameters != expected:
            issues.append(
                ValidationIssue(
                    fixture.start_line,
                    f"{fixture.name} {fixture.mode!r} has {fixture.parameters} parameters, expected {expected}.",
                )
            )

    return ValidationResult(ok=not issues, issues=issues, fixtures=fixtures)


def _expected_channels(label: str) -> int | None:
    match = CHANNEL_IN_NAME.search(label or "")
    if not match:
        return None
    return int(match.group(1))


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)
    return stripped.strip() + "\n"
