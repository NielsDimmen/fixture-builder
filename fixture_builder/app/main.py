from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .convert import generate_fixture_text
from .extract import extract_upload, summarize_extraction
from .library import append_fixtures, list_manufacturers, read_style_sample
from .settings import load_settings
from .validate import validate_dmxlan

STATIC_DIR = Path(__file__).parent / "static"
app = FastAPI(title="Fixture Builder")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ValidateBody(BaseModel):
    text: str


class AppendBody(BaseModel):
    manufacturer: str
    text: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    settings = load_settings()
    return {
        "ok": True,
        "has_openai_key": bool(settings.openai_api_key),
        "model": settings.openai_model,
        "library_path": settings.library_path,
    }


@app.get("/api/manufacturers")
def manufacturers() -> dict:
    settings = load_settings()
    return {"manufacturers": list_manufacturers(settings.library_path), "library_path": settings.library_path}


@app.post("/api/validate")
def validate_text(body: ValidateBody) -> dict:
    result = validate_dmxlan(body.text)
    return {
        "ok": result.ok,
        "errors": [{"line": item.line, "message": item.message} for item in result.issues],
        "fixtures": [
            {"name": item.name, "mode": item.mode, "channels": item.parameters}
            for item in result.fixtures
        ],
    }


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    manufacturer: str = Form(""),
    fixture_name: str = Form(""),
) -> JSONResponse:
    settings = load_settings()
    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File is larger than {settings.max_upload_mb} MB.")

    try:
        extraction = extract_upload(
            data,
            file.filename or "upload",
            file.content_type or "",
            max_pages=settings.max_pages,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    brand = manufacturer.strip()
    style = read_style_sample(settings.library_path, brand) if brand else ""
    images: list[tuple[bytes, str]] = []
    for page in extraction.pages:
        mime = "image/png"
        if extraction.content_type.startswith("image/"):
            mime = extraction.content_type
        images.append((page.png_bytes, mime))

    try:
        text, notes = generate_fixture_text(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            manufacturer=brand,
            fixture_name=fixture_name.strip(),
            extracted_text=extraction.combined_text,
            images=images,
            style_sample=style,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI request failed: {exc}") from exc

    result = validate_dmxlan(text)
    return JSONResponse(
        {
            "text": text,
            "ok": result.ok,
            "errors": [{"line": item.line, "message": item.message} for item in result.issues],
            "fixtures": [
                {"name": item.name, "mode": item.mode, "channels": item.parameters}
                for item in result.fixtures
            ],
            "notes": notes,
            "extraction": summarize_extraction(extraction),
            "pages": [page.index for page in extraction.pages],
        }
    )


@app.post("/api/append")
def append(body: AppendBody) -> dict:
    settings = load_settings()
    result = validate_dmxlan(body.text)
    if not result.ok:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Fix validation errors before writing to the library.",
                "errors": [{"line": item.line, "message": item.message} for item in result.issues],
            },
        )
    try:
        written = append_fixtures(settings.library_path, body.manufacturer, body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return written
