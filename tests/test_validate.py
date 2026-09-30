from pathlib import Path

from app.validate import validate_dmxlan

CAMEO = Path("/Users/niels/Documents/dmXLAN Files/Fixture Library/Cameo.txt")


def test_range_requires_two_numbers():
    text = """
fixture = Zenit Z180 G2, "3CH CTC"
color = 150,150,150
parameter = CTC
range = 0, Narrow
"""
    result = validate_dmxlan(text)
    assert not result.ok
    assert any("two DMX numbers" in item.message for item in result.issues)


def test_kelvin_label_must_be_quoted():
    text = """
fixture = Zenit Z180 G2, "3CH CTC"
color = 150,150,150
parameter = Intensity
default = 255
parameter = CTC
range = 0, 7200K
parameter = Zoom
range = 0, 255, Narrow to Wide
"""
    result = validate_dmxlan(text)
    assert not result.ok
    assert any("two DMX numbers" in item.message or "quoted" in item.message for item in result.issues)


def test_quoted_kelvin_range_is_ok():
    text = """
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
    result = validate_dmxlan(text)
    assert result.ok, result.as_text()
    assert result.fixtures[0].parameters == 3


def test_existing_z180_block_validates():
    source = CAMEO.read_text(encoding="utf-8")
    start = source.index('fixture = Zenit Z180 G2, "3CH CTC"')
    end = source.index('fixture = Zenith W600 SMD')
    result = validate_dmxlan(source[start:end])
    assert result.ok, result.as_text()
    modes = {item.mode: item.parameters for item in result.fixtures}
    assert modes["3CH CTC"] == 3
    assert modes["17CH Full Access 16bit"] == 17
