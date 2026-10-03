"""Plottene skal kunne tegnes og gemmes; udseendet tjekkes ved at se på dem."""
import json
import math

from omkreds_energi import tegn


def _aar(top):
    return [22 + top * max(0.0, math.sin(math.pi * (t % 24 - 7) / 12)) * max(0.0, -math.cos(2 * math.pi * t / 8760))
            for t in range(8760)]


def test_overtemperatur_figurer(tmp_path):
    stier = tegn.tegn_overtemperatur({"Stue": _aar(4), "Soverum": _aar(8)}, str(tmp_path), ("png",))
    assert len(stier) == 3
    assert all((tmp_path / p.split("\\")[-1].split("/")[-1]).stat().st_size > 5000 for p in stier)


def test_dagslyskort_og_cli(tmp_path, monkeypatch, capsys):
    masker = [[(x, y), (x + 0.5, y), (x + 0.5, y + 0.5), (x, y + 0.5)] for x in (0.5, 1.0, 1.5) for y in (0.5, 1.0)]
    plotdata = {"masker": masker, "da": [80, 70, 60, 40, 30, 20], "omrids": [[(0, 0), (2.5, 0), (2.5, 2), (0, 2)]], "andel": 50.0}
    (tmp_path / "dagslys.json").write_text(json.dumps(plotdata), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["tegn", str(tmp_path), "--format", "png"])
    tegn.main()
    assert (tmp_path / "figurer" / "dagslys_kort.png").stat().st_size > 5000
    assert "dagslys_kort.png" in capsys.readouterr().out
