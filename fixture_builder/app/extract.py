from __future__ import annotations

import re
from dataclasses import dataclass

PAGE_HINTS = (
    "dmx",
    "ch mode",
    "channel",
    "control table",
    "function",
    "values",
)


@dataclass
class ExtractedPage:
    index: int
    text: str
    png_bytes: bytes


@dataclass
class Extraction:
    filename: str
    content_type: str
    pages: list[ExtractedPage]
    combined_text: str


def _looks_like_dmx_page(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in PAGE_HINTS)


def extract_pdf(data: bytes, filename: str, max_pages: int = 8) -> Extraction:
    import fitz

    doc = fitz.open(stream=data, filetype="pdf")
    scored: list[tuple[int, str]] = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        scored.append((i, text))

    dmx_indexes = [i for i, text in scored if _looks_like_dmx_page(text)]
    if not dmx_indexes:
        dmx_indexes = [i for i, _ in scored]

    chosen = dmx_indexes[:max_pages]
    pages: list[ExtractedPage] = []
    for i in chosen:
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.1, 1.1), alpha=False)
        pages.append(
            ExtractedPage(
                index=i + 1,
                text=scored[i][1].strip(),
                png_bytes=pix.tobytes("png"),
            )
        )

    combined = "\n\n".join(
        f"--- page {page.index} ---\n{page.text}" for page in pages if page.text
    )
    return Extraction(filename=filename, content_type="application/pdf", pages=pages, combined_text=combined)


def extract_image(data: bytes, filename: str, content_type: str) -> Extraction:
    page = ExtractedPage(index=1, text="", png_bytes=data)
    return Extraction(
        filename=filename,
        content_type=content_type or "image/png",
        pages=[page],
        combined_text="",
    )


def extract_upload(data: bytes, filename: str, content_type: str, max_pages: int = 8) -> Extraction:
    name = (filename or "").lower()
    kind = (content_type or "").lower()
    if name.endswith(".pdf") or "pdf" in kind:
        return extract_pdf(data, filename, max_pages=max_pages)
    if name.endswith((".png", ".jpg", ".jpeg", ".webp")) or kind.startswith("image/"):
        return extract_image(data, filename, kind)
    raise ValueError("Upload a PDF or an image (PNG, JPG, WEBP).")


def summarize_extraction(extraction: Extraction) -> str:
    if not extraction.pages:
        return "No pages extracted."
    bits = [f"{extraction.filename}: {len(extraction.pages)} page(s)"]
    for page in extraction.pages:
        preview = re.sub(r"\s+", " ", page.text)[:240]
        bits.append(f"page {page.index}: {preview or '(image only)'}")
    return "\n".join(bits)
