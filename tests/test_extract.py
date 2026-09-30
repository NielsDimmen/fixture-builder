from pathlib import Path

from app.extract import extract_upload

PDF = Path("/Users/niels/Downloads/CLZZ180G2-dmx_control_table--D004281-en.pdf")
FALLBACK = Path("/Users/niels/.cursor/projects/Users-niels-fixture-file/attachments/empty-state-draft/CLZZ180G2-dmx_control_table--D004281-en.pdf")


def _pdf_path() -> Path:
    if PDF.exists():
        return PDF
    return FALLBACK


def test_extracts_z180_dmx_pages():
    path = _pdf_path()
    assert path.exists(), "Z180 G2 DMX PDF is missing"
    extraction = extract_upload(path.read_bytes(), path.name, "application/pdf", max_pages=8)
    assert extraction.pages
    blob = extraction.combined_text.lower()
    assert "17ch" in blob.replace(" ", "")
    assert "dimmer" in blob
    assert extraction.pages[0].png_bytes.startswith(b"\x89PNG")
