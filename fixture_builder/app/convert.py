from __future__ import annotations

import base64

from openai import OpenAI

from .validate import strip_code_fence, validate_dmxlan

SYSTEM_PROMPT = """You convert lighting fixture DMX control tables into dmXLAN fixture library syntax.

Output ONLY dmXLAN text. No markdown, no commentary, no manufacturer line unless asked.

File syntax:
manufacturer = Brand

fixture = FixtureName, "Mode name"
color = 150,150,150

parameter = Intensity
default = 255
highlight = 255
parameter = Red, fine
option = skip
highlight = 255
range = 0, 5, Open
range = 6, 10, Close
macro = Zoom Reset
step = set, Control, 236
step = delay, 6
step = release, all

Hard rules:
- One DMX channel = one `parameter =` line, in channel order.
- 16-bit fine channels are `parameter = Name, fine` plus `option = skip`.
- Use Intensity, not Dimmer, for the master dimmer.
- Control and Dimmer Curve get `option = skip`.
- A range is NOT a range unless it has TWO DMX numbers: `range = start, end, label`.
  Good: range = 136, 143, No function
  Good: range = 0, 255, Narrow to Wide
  Bad:  range = 0, Narrow
  Bad:  range = 0, 7200K
- If a label starts with a digit, quote it: range = 0, 255, "7200K - 3200K"
- Slow->fast effects are one range with two numbers, not two single-value lines.
- RGB/W defaults and highlights are 255. Shutter default/highlight 0.
- Name modes clearly, include channel count when known: "11CH Full Access 8bit".
- Match the style of any existing manufacturer sample you are given.
- If the PDF table is missing a last channel that the mode count requires, add the obvious remaining channel (often Device Settings / Control) and keep channel count correct.

Example:

fixture = Zenit Z180 G2, "3CH CTC"
color = 150,150,150

parameter = Intensity
default = 255
highlight = 255
parameter = CTC
range = 0, 255, "7200K - 3200K"
parameter = Zoom
range = 0, 255, Narrow to Wide
"""


def _image_part(png_bytes: bytes, content_type: str = "image/png") -> dict:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{content_type};base64,{b64}", "detail": "high"},
    }


def build_user_prompt(
    *,
    manufacturer: str,
    fixture_name: str,
    extracted_text: str,
    style_sample: str,
    extra: str = "",
) -> str:
    parts = [
        f"Manufacturer: {manufacturer or '(detect from document)'}",
        f"Fixture name hint: {fixture_name or '(detect from document)'}",
        "Create every DMX mode from the tables. Keep each mode as its own fixture block.",
    ]
    if extracted_text.strip():
        parts.append("Extracted text from the document:\n" + extracted_text.strip())
    if style_sample.strip():
        parts.append("Existing manufacturer file sample to match:\n" + style_sample.strip())
    if extra.strip():
        parts.append(extra.strip())
    return "\n\n".join(parts)


def generate_fixture_text(
    *,
    api_key: str,
    model: str,
    manufacturer: str,
    fixture_name: str,
    extracted_text: str,
    images: list[tuple[bytes, str]],
    style_sample: str,
) -> tuple[str, list[str]]:
    if not api_key:
        raise ValueError("OpenAI API key is missing. Set it in the add-on options or OPENAI_API_KEY.")

    client = OpenAI(api_key=api_key)
    notes: list[str] = []
    user_text = build_user_prompt(
        manufacturer=manufacturer,
        fixture_name=fixture_name,
        extracted_text=extracted_text,
        style_sample=style_sample,
    )
    content: list[dict] = [{"type": "text", "text": user_text}]
    for blob, mime in images:
        content.append(_image_part(blob, mime))

    text = _complete(client, model, content)
    result = validate_dmxlan(text)
    if result.ok:
        return text, notes

    notes.append("First draft failed validation, retrying with parser errors.")
    retry_text = build_user_prompt(
        manufacturer=manufacturer,
        fixture_name=fixture_name,
        extracted_text=extracted_text,
        style_sample=style_sample,
        extra=(
            "Your previous output failed the dmXLAN parser. Fix every issue. "
            "Every range MUST have two numbers.\n\nParser errors:\n"
            + result.as_text()
            + "\n\nPrevious output:\n"
            + text
        ),
    )
    retry_content: list[dict] = [{"type": "text", "text": retry_text}]
    for blob, mime in images:
        retry_content.append(_image_part(blob, mime))
    text = _complete(client, model, retry_content)
    return text, notes


def _complete(client: OpenAI, model: str, content: list[dict]) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )
    choice = response.choices[0].message.content or ""
    return strip_code_fence(choice)
