from pathlib import Path

from app.library import append_fixtures, existing_fixture_keys, list_manufacturers


def test_append_creates_and_refuses_duplicates(tmp_path: Path):
    generated = """
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
    written = append_fixtures(str(tmp_path), "Cameo", generated)
    assert written["action"] == "created"
    names = list_manufacturers(str(tmp_path))
    assert names == ["Cameo"]
    keys = existing_fixture_keys((tmp_path / "Cameo.txt").read_text())
    assert ("Zenit Z180 G2", "3CH CTC") in keys
    try:
        append_fixtures(str(tmp_path), "Cameo", generated)
        raise AssertionError("duplicate write should fail")
    except ValueError as exc:
        assert "Already in library" in str(exc)
