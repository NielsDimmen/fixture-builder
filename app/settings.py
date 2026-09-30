from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    library_path: str = "/share/dmxlan"
    port: int = 8099
    max_pages: int = 8
    max_upload_mb: int = 20


def _from_options_file() -> dict:
    path = Path("/data/options.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return {
        "openai_api_key": data.get("openai_api_key") or "",
        "openai_model": data.get("openai_model") or "gpt-4o",
        "library_path": data.get("library_path") or "/share/dmxlan",
    }


def load_settings() -> AppSettings:
    file_opts = _from_options_file()
    return AppSettings(
        openai_api_key=os.environ.get("OPENAI_API_KEY") or file_opts.get("openai_api_key", ""),
        openai_model=os.environ.get("OPENAI_MODEL") or file_opts.get("openai_model", "gpt-4o"),
        library_path=os.environ.get("LIBRARY_PATH") or file_opts.get("library_path", "/share/dmxlan"),
        port=int(os.environ.get("PORT", "8099")),
        max_pages=int(os.environ.get("MAX_PAGES", "8")),
        max_upload_mb=int(os.environ.get("MAX_UPLOAD_MB", "20")),
    )


settings = load_settings()
