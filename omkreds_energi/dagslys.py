"""Dagslys efter BR18 § 379, beregningsmetoden (300 lux).

Kilde: Bygningsreglementets vejledning om lys og udsyn, afsnit 1.2 (læst 2026-10-02).

- Kravet: 300 lux eller mere på mindst halvdelen af det relevante gulvareal i mindst
  halvdelen af dagslystimerne. For boliger gælder det **boligen som helhed**.
- Dagslystimerne er den halvdel af årets timer, hvor der er mest dagslys.
- Beregningsnet: vandret plan 0,50 m over gulvet i boliger og 0,85 m i arbejdsrum.
  Randzone på 0,5 m fra væggene er undtaget. Maskerne bør være lige store, forholdet
  mellem korteste og længste side over 0,7, og længste side normalt højst 1,0 m.
- Under skråvægge tæller kun gulv, hvor loftet er over beregningsplanet.
- Vejrdata: DRY 2001-2010 med DMI Report 18-20. Metoden bygger på DS/EN 17037.
- Standardreflektanser: se REFLEKTANSER.

Input pr. rum er DA-værdien for hvert målepunkt: hvor stor en procentdel af
dagslystimerne punktet har mindst 300 lux. Det giver Honeybee's Annual Daylight med
tærsklen 300 lux, når skemaet er sat til dagslystimerne (se `dagslystimer`).
"""

from dataclasses import dataclass, field

LUX = 300
ANDEL_TID = 50.0        # % af dagslystimerne
ANDEL_GULV = 50.0       # % af det relevante gulvareal

MAALEHOEJDE = {"bolig": 0.50, "arbejdsrum": 0.85}    # m over gulv
RANDZONE = 0.5                                       # m fra væggene
MASKE_MAKS_SIDE = 1.0                                # m
MASKE_MIN_FORHOLD = 0.7                              # korteste / længste side

VEJRDATA = "DRY 2001-2010 (Wang et al., 2013) og DMI Report 18-20"

REFLEKTANSER = {
    "lofter": 0.70,
    "indvendige vægge": 0.50,
    "gulve": 0.20,
    "glas": 0.15,
    "vinduesramme/-karm": 0.70,
    "terræn, træer mv.": 0.10,
    "omkringliggende bygninger": 0.20,
}


@dataclass
class Rumresultat:
    navn: str
    andel_gulv: float            # % af planet, der opfylder tidskravet
    areal: float                 # samlet areal af målepunkterne (eller antal punkter)
    punkter: int
    krav_gulv: float = ANDEL_GULV
    advarsler: list = field(default_factory=list)

    @property
    def ok(self):
        return self.andel_gulv >= self.krav_gulv


def dagslystimer(dagslys):
    """Sand/falsk pr. time: den halvdel af årets timer med mest dagslys.

    `dagslys` er en timeværdi pr. time for året, fx global vandret belysningsstyrke
    eller globalstråling fra vejrfilen. Ved lige værdier vælges de tidligste timer.
    """
    n = len(dagslys) // 2
    valgte = set(sorted(range(len(dagslys)), key=lambda i: (-dagslys[i], i))[:n])
    return [i in valgte for i in range(len(dagslys))]


def tjek_net(masker, maks_side=MASKE_MAKS_SIDE, min_forhold=MASKE_MIN_FORHOLD):
    """Advarsler for beregningsnettet. `masker` er [(side_a, side_b), ...] i m."""
    if not masker:
        return []
    advarsler = []
    laengste = max(max(a, b) for a, b in masker)
    if laengste > maks_side + 1e-6:
        advarsler.append("maskeside på %.2f m – vejledningen anbefaler højst %.1f m"
                         % (laengste, maks_side))
    forhold = min(min(a, b) / max(a, b) for a, b in masker if max(a, b) > 0)
    if forhold < min_forhold:
        advarsler.append("maskernes sideforhold ned til %.2f – bør være over %.1f"
                         % (forhold, min_forhold))
    arealer = [a * b for a, b in masker]
    if max(arealer) > 1.05 * min(arealer):
        advarsler.append("maskerne er ikke lige store – vægt punkterne med areal")
    return advarsler


def _vaegte(da, arealer):
    if arealer is None:
        return [1.0] * len(da)
    if len(arealer) != len(da):
        raise ValueError("arealer og målepunkter har ikke samme længde")
    return [float(a) for a in arealer]


def andel_opfyldt(da, arealer=None, krav_tid=ANDEL_TID):
    """Andel (%) af planet, hvor DA >= krav_tid. Vægtes med `arealer`, hvis givet."""
    if not da:
        raise ValueError("ingen målepunkter")
    vaegte = _vaegte(da, arealer)
    total = sum(vaegte)
    if total <= 0:
        raise ValueError("samlet areal er nul")
    return 100.0 * sum(a for d, a in zip(da, vaegte) if d >= krav_tid) / total


def vurder_rum(navn, da, arealer=None, krav_tid=ANDEL_TID, krav_gulv=ANDEL_GULV):
    da = [float(d) for d in da]
    vaegte = _vaegte(da, arealer) if da else []
    res = Rumresultat(
        navn=navn,
        andel_gulv=andel_opfyldt(da, arealer, krav_tid),
        areal=sum(vaegte),
        punkter=len(da),
        krav_gulv=krav_gulv,
    )
    if any(d < 0 or d > 100 for d in da):
        res.advarsler.append("DA-værdier uden for 0–100 % – er det lux i stedet for procent?")
    if len(da) < 10:
        res.advarsler.append("kun %d målepunkter – målenettet er for groft" % len(da))
    return res


def vurder(rum, arealer=None, krav_tid=ANDEL_TID, krav_gulv=ANDEL_GULV):
    """`rum` er {rumnavn: [DA pr. punkt]}; `arealer` er {rumnavn: [areal pr. punkt]}."""
    arealer = arealer or {}
    return [vurder_rum(n, d, arealer.get(n), krav_tid, krav_gulv) for n, d in rum.items()]


def samlet(resultater):
    """Boligen som helhed: arealvægtet andel over alle rum (%)."""
    total = sum(r.areal for r in resultater)
    if total <= 0:
        raise ValueError("ingen rum")
    return sum(r.andel_gulv * r.areal for r in resultater) / total


def som_tabel(resultater, bolig=True):
    if not resultater:
        return "Ingen rum."
    linjer = [["Rum", "Andel af gulv", "Krav", "Punkter", ""]]
    for r in resultater:
        linjer.append([r.navn, "%.0f %%" % r.andel_gulv, "%.0f %%" % r.krav_gulv,
                       str(r.punkter), "OK" if r.ok else "(under)" if bolig else "IKKE OK"])
    if bolig:
        s = samlet(resultater)
        linjer.append(["Boligen samlet", "%.0f %%" % s, "%.0f %%" % ANDEL_GULV,
                       str(sum(r.punkter for r in resultater)),
                       "OK" if s >= ANDEL_GULV else "IKKE OK"])
    bredder = [max(len(l[i]) for l in linjer) for i in range(len(linjer[0]))]
    tekst = ["  ".join(c.ljust(b) for c, b in zip(l, bredder)).rstrip() for l in linjer]
    for r in resultater:
        tekst += ["! %s: %s" % (r.navn, a) for a in r.advarsler]
    return "\n".join(tekst)


def som_data(resultater, bolig=True, maalehoejde=None, randzone=RANDZONE, net_advarsler=()):
    if maalehoejde is None:
        maalehoejde = MAALEHOEJDE["bolig" if bolig else "arbejdsrum"]
    data = {
        "metode": "%d lux på mindst %g %% af det relevante gulvareal i mindst %g %% af "
                  "dagslystimerne" % (LUX, ANDEL_GULV, ANDEL_TID),
        "vurderes_for": "boligen som helhed" if bolig else "hvert rum",
        "maalehoejde_m": maalehoejde,
        "randzone_m": randzone,
        "vejrdata": VEJRDATA,
        "reflektanser": REFLEKTANSER,
        "net_advarsler": list(net_advarsler),
        "rum": [
            {"navn": r.navn, "andel_gulv": round(r.andel_gulv, 1), "krav": r.krav_gulv,
             "punkter": r.punkter, "ok": r.ok, "advarsler": r.advarsler}
            for r in resultater
        ],
    }
    if bolig:
        data["samlet_andel"] = round(samlet(resultater), 1)
        data["ok"] = data["samlet_andel"] >= ANDEL_GULV
    else:
        data["ok"] = all(r.ok for r in resultater)
    return data
