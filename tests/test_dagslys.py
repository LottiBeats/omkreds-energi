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


def test_bolig_vurderes_som_helhed():
    # Stuen opfylder på hele gulvet, soverummet slet ikke: boligen samlet 50 % -> OK
    res = dl.vurder({"Stue": [80.0] * 20, "Soverum": [10.0] * 20})
    assert dl.samlet(res) == 50.0
    data = dl.som_data(res)
    json.dumps(data)
    assert data["ok"] is True
    assert data["maalehoejde_m"] == 0.50
    assert "Boligen samlet" in dl.som_tabel(res)


def test_bolig_samlet_vaegtes_med_areal():
    # lille rum der opfylder, stort rum der ikke gør
    res = dl.vurder({"Bad": [80.0] * 10, "Stue": [10.0] * 30})
    assert dl.samlet(res) == 25.0
    assert dl.som_data(res)["ok"] is False


def test_arbejdsrum_vurderes_rum_for_rum():
    res = dl.vurder({"Kontor 1": [80.0] * 20, "Kontor 2": [10.0] * 20})
    data = dl.som_data(res, bolig=False)
    assert data["ok"] is False
    assert data["maalehoejde_m"] == 0.85
    assert "IKKE OK" in dl.som_tabel(res, bolig=False)


def test_dagslystimer_er_den_lyse_halvdel():
    lys = [0, 0, 5, 10, 20, 0, 3, 8]
    maske = dl.dagslystimer(lys)
    assert sum(maske) == 4
    assert [i for i, m in enumerate(maske) if m] == [2, 3, 4, 7]


def test_tjek_net():
    assert dl.tjek_net([(0.5, 0.5)] * 4) == []
    adv = dl.tjek_net([(1.2, 0.6), (0.5, 0.5)])
    assert any("1.20 m" in a for a in adv)
    assert any("sideforhold" in a for a in adv)
    assert any("lige store" in a for a in adv)
