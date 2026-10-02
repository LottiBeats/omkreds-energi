"""Dagslys efter BR18 § 379, beregningsmetoden.

Et rum har tilstrækkeligt dagslys, når mindst halvdelen af referenceplanet har 300 lux
i mindst halvdelen af dagslystimerne (metoden fra DS/EN 17037, som BR18 henviser til).

Input pr. rum er DA-værdien for hvert målepunkt: hvor stor en procentdel af
dagslystimerne punktet har mindst 300 lux. Det er det, Honeybee's Annual Daylight
giver med tærsklen 300 lux. Målepunkterne kan vægtes med deres areal, hvis målenettet
ikke er ensartet.

Målehøjde og randzone bestemmes, når målenettet laves i Grasshopper; de skrives med i
resultatet, så de kommer med i notatet.
"""

from dataclasses import dataclass, field

LUX = 300               # krævet belysningsstyrke
ANDEL_TID = 50.0        # % af dagslystimerne
ANDEL_GULV = 50.0       # % af referenceplanet


@dataclass
class Rumresultat:
    navn: str
    andel_gulv: float            # % af referenceplanet, der opfylder tidskravet
    punkter: int
    krav_gulv: float = ANDEL_GULV
    advarsler: list = field(default_factory=list)

    @property
    def ok(self):
        return self.andel_gulv >= self.krav_gulv


def andel_opfyldt(da, arealer=None, krav_tid=ANDEL_TID):
    """Andel (%) af planet, hvor DA >= krav_tid. Vægtes med `arealer`, hvis givet."""
    if not da:
        raise ValueError("ingen målepunkter")
    if arealer is None:
        arealer = [1.0] * len(da)
    elif len(arealer) != len(da):
        raise ValueError("arealer og målepunkter har ikke samme længde")
    total = sum(arealer)
    if total <= 0:
        raise ValueError("samlet areal er nul")
    opfyldt = sum(a for d, a in zip(da, arealer) if d >= krav_tid)
    return 100.0 * opfyldt / total


def vurder_rum(navn, da, arealer=None, krav_tid=ANDEL_TID, krav_gulv=ANDEL_GULV):
    da = [float(d) for d in da]
    res = Rumresultat(
        navn=navn,
        andel_gulv=andel_opfyldt(da, arealer, krav_tid),
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


def som_tabel(resultater):
    if not resultater:
        return "Ingen rum."
    linjer = [["Rum", "Andel af gulv", "Krav", "Punkter", ""]]
    for r in resultater:
        linjer.append([r.navn, "%.0f %%" % r.andel_gulv, "%.0f %%" % r.krav_gulv,
                       str(r.punkter), "OK" if r.ok else "IKKE OK"])
    bredder = [max(len(l[i]) for l in linjer) for i in range(len(linjer[0]))]
    tekst = ["  ".join(c.ljust(b) for c, b in zip(l, bredder)).rstrip() for l in linjer]
    for r in resultater:
        tekst += ["! %s: %s" % (r.navn, a) for a in r.advarsler]
    return "\n".join(tekst)


def som_data(resultater, maalehoejde=None, randzone=None):
    return {
        "metode": "%d lux i %g %% af dagslystimerne på %g %% af referenceplanet"
                  % (LUX, ANDEL_TID, ANDEL_GULV),
        "maalehoejde_m": maalehoejde,
        "randzone_m": randzone,
        "rum": [
            {"navn": r.navn, "andel_gulv": round(r.andel_gulv, 1), "krav": r.krav_gulv,
             "punkter": r.punkter, "ok": r.ok, "advarsler": r.advarsler}
            for r in resultater
        ],
        "ok": all(r.ok for r in resultater),
    }
