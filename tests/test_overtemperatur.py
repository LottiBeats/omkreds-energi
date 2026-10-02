import json

import pytest

from omkreds_energi import overtemperatur as ot


def aar(basis=22.0, varme_timer=0, varme_temp=29.0):
    """Et år i timer med `varme_timer` timer på `varme_temp`, resten på `basis`."""
    return [varme_temp] * varme_timer + [basis] * (8760 - varme_timer)


def test_taeller_kun_strengt_over_graensen():
    assert ot.timer_over([26.9, 27.0, 27.1, 28.5], 27.0) == 2


def test_brugstid_begraenser_optaellingen():
    temp = [30.0, 30.0, 30.0, 20.0]
    assert ot.timer_over(temp, 27.0, brugstid=[True, False, True, True]) == 2


def test_brugstid_skal_have_samme_laengde():
    with pytest.raises(ValueError):
        ot.timer_over([30.0, 30.0], 27.0, brugstid=[True])


def test_koeligt_rum_er_ok():
    r = ot.vurder_rum("Stue", aar())
    assert r.ok
    assert r.timer == {27.0: 0, 28.0: 0}
    assert r.advarsler == []


def test_paa_graensen_er_ok_en_time_mere_er_ikke():
    assert ot.vurder_rum("Soverum", aar(varme_timer=25)).ok
    r = ot.vurder_rum("Soverum", aar(varme_timer=26))
    assert not r.ok
    assert r.timer[28.0] == 26


def test_27_graensen_alene_kan_faelde_rummet():
    # 101 timer på 27,5 °C: over 27, men ikke over 28
    r = ot.vurder_rum("Kontor", aar(varme_timer=101, varme_temp=27.5))
    assert r.timer == {27.0: 101, 28.0: 0}
    assert not r.ok


def test_advarsel_ved_ufuldstaendigt_aar():
    r = ot.vurder_rum("Bad", [22.0] * 100)
    assert r.advarsler


def test_tomt_rum_giver_fejl():
    with pytest.raises(ValueError):
        ot.vurder_rum("Tomt", [])


def test_tabel_og_data():
    res = ot.vurder({"Stue": aar(), "Soverum": aar(varme_timer=40)})
    tabel = ot.som_tabel(res)
    assert "Soverum" in tabel and "IKKE OK" in tabel

    data = ot.som_data(res)
    json.dumps(data)  # skal kunne gemmes
    assert data["ok"] is False
    assert [r["ok"] for r in data["rum"]] == [True, False]
