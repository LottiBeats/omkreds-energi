"""Testene genregner eksemplerne i TBST's vejledning om korrektioner til 10 pct.-reglen.

Vejledningen aflæser faktorerne på kurver og runder; derfor tolerancerne.
"""
from pytest import approx

from omkreds_energi import glasareal as g


def test_eksempel_rudetype_side_8():
    # 14 m² rum, 1,64 m² glas med LT 0,58 -> ikke OK.
    # Vejledningen skriver F_LT = 0,73, men 0,58/0,75 = 0,773 (trykfejl; dens egen
    # 12,9 %-linje bruger 0,773). Konklusionen holder: 1,27 m² < 1,4 m².
    assert g.f_lt(0.58) == approx(0.773, abs=0.001)
    rum = g.Rum("Rum", 14.0, [g.Vindue("V1", 1.64, lt=0.58)])
    r = g.vurder_rum(rum)
    assert r.krav == approx(1.4)
    assert r.korrigeret == approx(1.27, abs=0.01)
    assert not r.ok


def test_hoej_lt_giver_ekstra_areal_side_9():
    assert g.f_lt(0.84) == approx(1.12)


def test_eksempel_vaegtykkelse_side_9():
    # 0,96 m² glas i 50 cm væg; vejledningen aflæser 1 m²-kurven: 0,91
    assert g.f_vaeg(0.5, 1.0) == approx(0.91)
    assert g.f_vaeg(0.5, 0.96) == approx(0.91, abs=0.01)
    assert g.f_vaeg(0.35, 0.5) == 1.0          # ingen korrektion under 40 cm
    assert g.f_vaeg(0.9, 0.3) == 0.50           # yderværdi


def test_eksempel_omgivelser_side_11():
    # middelprofilvinkel 33° -> ca. 0,69; A_kor = (0,72/0,75) · 0,69 · 2,2 = 1,46 m² >= 1,4
    assert g.f_omg(33) == approx(0.69, abs=0.015)
    v = g.Vindue("Parti", 2.2, lt=0.72, faktorer={"omg": g.f_omg(33)})
    r = g.vurder_rum(g.Rum("Rum", 14.0, [v]))
    assert r.korrigeret == approx(1.46, abs=0.03)
    assert r.ok


def test_tabelvaerdier():
    assert g.f_omg(45) == 0.50
    assert g.f_oh(25) == 1.00 and g.f_oh(45) == 0.70 and g.f_oh(70) == 0.50
    assert g.f_sf(90) == 0.53 and g.f_sf(90, 40) == 0.74
    assert g.f_afs(30, "moerk") == 0.26
    assert g.f_rum(7.0, bolig=False) == 0.77
    assert g.f_rum(7.0) == 0.9 and g.f_rum(5.5) == 1.0


def test_eksempel_overlappende_skygger_side_19():
    # udhæng 18° -> ~0,99 (vejledningen ekstrapolerer); sidefremspring 42° uendelig høj -> 0,82;
    # 23°/h 53° -> 0,92 i vejledningen (aflæst i tabel 5), tabel 6 giver 0,93
    assert g.f_oh(18) == approx(0.99, abs=0.011)
    assert g.f_sf(42) == approx(0.82, abs=0.005)
    assert g.f_sf(23, 53) == approx(0.92, abs=0.015)
    f = 0.99 * g.f_sf(42) * g.f_sf(23, 53)
    assert f * 0.92 == approx(0.69, abs=0.01)


def test_ovenlys_og_flere_flader():
    assert g.er_ovenlys(60) and not g.er_ovenlys(61)
    rum = g.Rum("Stue", 30.0, [
        g.Vindue("Facade", 2.0, flade="SV"),
        g.Vindue("Ovenlys", 0.8, flade="tag", ovenlys=True),
    ])
    r = g.vurder_rum(rum)
    # ovenlys 0,8 · 1,4 = 1,12; forhold 1,12/2,0 = 0,56 >= 0,3 -> F_FL = 1,2
    assert r.f_fl == 1.2
    assert r.korrigeret == approx((2.0 + 1.12) * 1.2)


def test_flere_flader_kraever_forhold_03():
    rum = g.Rum("Stue", 30.0, [g.Vindue("A", 3.0, flade="S"), g.Vindue("B", 0.5, flade="V")])
    assert g.vurder_rum(rum).f_fl == 1.0


def test_soverum_lempelse_i_bolig():
    skygge = {"omg": 0.5}
    stue = g.Rum("Stue", 30.0, [g.Vindue("S", 5.0)])
    sove = g.Rum("Soverum", 10.0, [g.Vindue("V", 1.2, faktorer=skygge)], soverum=True)
    res, ok, noter = g.vurder_bolig([stue, sove])
    assert not res[1].ok              # 0,6 m² < 1,0 m²
    assert res[1].uden_skygge == approx(1.2)
    assert ok                         # 5,6 m² >= 4,0 m² samlet, og soverum OK uden skygge
    assert "Soverum" in noter[0]


def test_lempelse_gaelder_ikke_stuen():
    stue = g.Rum("Stue", 30.0, [g.Vindue("S", 3.5, faktorer={"omg": 0.5})])
    sove = g.Rum("Soverum", 10.0, [g.Vindue("V", 3.0)], soverum=True)
    _, ok, _ = g.vurder_bolig([stue, sove])
    assert not ok
