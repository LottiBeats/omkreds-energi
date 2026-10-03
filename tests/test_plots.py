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


def test_komfortkort(tmp_path):
    from omkreds_energi import plots
    v = [1 if 4000 < t < 5000 and 12 <= t % 24 <= 17 else (-1 if t < 800 else 0) for t in range(8760)]
    sti = tmp_path / "komfort.png"
    plots.gem(plots.komfortkort(v, "Stue", 8, 22), str(sti))
    assert sti.stat().st_size > 5000


def test_tegninger_paa_proevemodel(tmp_path):
    import importlib.util
    import subprocess
    import sys
    if importlib.util.find_spec("honeybee") is None:
        import pytest
        pytest.skip("honeybee-core er ikke installeret")
    subprocess.run([sys.executable, "eksempler/proevemodel.py", str(tmp_path)], check=True)
    from omkreds_energi import tegninger, plots
    m = tegninger.indlaes(str(tmp_path / "model.hbjson"))
    assert {tegninger.rumnavn(r) for r in m.rooms} == {"Stue og køkken", "Bad", "Værelse"}
    assert tegninger.find_rum(m, "RESIDENCE_2").display_name == "Bad"
    for navn, fig in [("a", tegninger.aksonometri(m)), ("p", tegninger.plan(m, {"Residence_1": 31}, graense=25)),
                      ("s", tegninger.solbane(55.68, 12.57))]:
        plots.gem(fig, str(tmp_path / f"{navn}.png"))
        assert (tmp_path / f"{navn}.png").stat().st_size > 5000
