import json

import pytest

from omkreds_energi import dagslys as dl


def test_halvdelen_af_punkterne_er_lige_nok():
    da = [80.0] * 10 + [20.0] * 10
    assert dl.andel_opfyldt(da) == 50.0
    assert dl.vurder_rum("Stue", da).ok


def test_lige_under_er_ikke_ok():
    da = [80.0] * 9 + [20.0] * 11
    assert not dl.vurder_rum("Stue", da).ok


def test_da_paa_50_taeller_med():
    assert dl.andel_opfyldt([50.0, 49.9]) == 50.0


def test_arealvaegtning():
    # ét stort punkt ved vinduet opfylder, tre små inde i rummet gør ikke
    assert dl.andel_opfyldt([90, 10, 10, 10], arealer=[3, 1, 1, 1]) == 50.0


def test_arealer_skal_passe():
    with pytest.raises(ValueError):
        dl.andel_opfyldt([90, 10], arealer=[1])


def test_ingen_punkter_giver_fejl():
    with pytest.raises(ValueError):
        dl.andel_opfyldt([])


def test_advarsel_ved_lux_i_stedet_for_procent():
    r = dl.vurder_rum("Køkken", [450.0] * 20)
    assert any("lux" in a for a in r.advarsler)


def test_advarsel_ved_groft_net():
    assert dl.vurder_rum("Bad", [80.0] * 4).advarsler


def test_tabel_og_data():
    res = dl.vurder({"Stue": [80.0] * 20, "Soverum": [10.0] * 20})
    assert "IKKE OK" in dl.som_tabel(res)
    data = dl.som_data(res, maalehoejde=0.85, randzone=0.5)
    json.dumps(data)
    assert data["ok"] is False
    assert data["maalehoejde_m"] == 0.85
