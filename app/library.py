from __future__ import annotations

from pathlib import Path

SKIP_NAMES = {
    "parameter.txt",
    "fixture.txt",
    "libversion.txt",
    "test.txt",
    "fixture.lib",
}


def library_dir(path: str) -> Path:
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def manufacturer_filename(name: str) -> str:
    cleaned = " ".join((name or "").split()).strip()
    if not cleaned:
        raise ValueError("Manufacturer name is empty.")
    if cleaned.lower().endswith(".txt"):
        return cleaned
    return f"{cleaned}.txt"


def list_manufacturers(path: str) -> list[str]:
    folder = Path(path)
    if not folder.exists():
        return []
    names: list[str] = []
    for item in sorted(folder.glob("*.txt")):
        if item.name.lower() in SKIP_NAMES:
            continue
        names.append(item.stem)
    return names


def manufacturer_path(path: str, manufacturer: str) -> Path:
    return library_dir(path) / manufacturer_filename(manufacturer)


def read_style_sample(path: str, manufacturer: str, limit: int = 120) -> str:
    file_path = manufacturer_path(path, manufacturer)
    if not file_path.exists():
        return ""
    lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    head = lines[:40]
    tail = lines[-limit:]
    return "\n".join(head + ["", "# ... existing fixtures omitted ...", ""] + tail)


def existing_fixture_keys(text: str) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line.lower().startswith("fixture"):
            continue
        if "=" not in line:
            continue
        value = line.split("=", 1)[1].strip()
        if "," in value:
            name, mode = value.split(",", 1)
            keys.add((name.strip(), mode.strip().strip('"')))
        else:
            keys.add((value, ""))
    return keys


def append_fixtures(path: str, manufacturer: str, generated: str) -> dict:
    file_path = manufacturer_path(path, manufacturer)
    incoming = generated.strip() + "\n"
    if file_path.exists():
        current = file_path.read_text(encoding="utf-8", errors="replace")
        existing = existing_fixture_keys(current)
        created = existing_fixture_keys(incoming)
        overlap = sorted(existing & created)
        if overlap:
            pretty = ", ".join(f"{name} {mode}".strip() for name, mode in overlap)
            raise ValueError(f"Already in library, not overwritten: {pretty}")
        if not current.endswith("\n"):
            current += "\n"
        file_path.write_text(current + "\n\n" + incoming, encoding="utf-8")
        action = "appended"
    else:
        header = f"manufacturer = {manufacturer.strip()}\n\n\n"
        file_path.write_text(header + incoming, encoding="utf-8")
        action = "created"
    return {"path": str(file_path), "action": action, "filename": file_path.name}
