"""Termisk indeklima efter BR18 § 386: timer over 27 og 28 °C pr. rum.

Kriterierne for boliger står i vejledningen til § 386: højst 100 timer om året over 27 °C
og højst 25 timer over 28 °C. Timerne tælles på den operative temperatur fra en
timesimulering af et helt år (8760 eller 8784 værdier pr. rum).

Modulet er ren Python 3 uden afhængigheder, så det kan testes uden Rhino og bruges
fra en Grasshopper-komponent i Rhino 8.
"""

from dataclasses import dataclass, field

# (grænse i °C, tilladte timer pr. år)
KRITERIER_BOLIG = ((27.0, 100), (28.0, 25))

TIMER_PR_AAR = (8760, 8784)


@dataclass
class Rumresultat:
    navn: str
    timer: dict = field(default_factory=dict)       # grænse -> timer over
    tilladt: dict = field(default_factory=dict)     # grænse -> tilladte timer
    maks_temp: float = 0.0
    advarsler: list = field(default_factory=list)

    @property
    def ok(self):
        return all(self.timer[g] <= self.tilladt[g] for g in self.timer)


def timer_over(temperaturer, graense, brugstid=None):
    """Antal timer hvor temperaturen er strengt over grænsen.

    `brugstid` er en valgfri liste af sandt/falsk pr. time; kun timer i brugstiden tælles.
    """
    if brugstid is None:
        return sum(1 for t in temperaturer if t > graense)
    if len(brugstid) != len(temperaturer):
        raise ValueError("brugstid og temperaturer har ikke samme længde")
    return sum(1 for t, b in zip(temperaturer, brugstid) if b and t > graense)


def vurder_rum(navn, temperaturer, kriterier=KRITERIER_BOLIG, brugstid=None):
    temperaturer = [float(t) for t in temperaturer]
    if not temperaturer:
        raise ValueError("ingen temperaturer for rummet '%s'" % navn)

    res = Rumresultat(navn=navn, maks_temp=max(temperaturer))
    if len(temperaturer) not in TIMER_PR_AAR:
        res.advarsler.append(
            "%d værdier – forventede et helt år i timer (8760)" % len(temperaturer))

    for graense, tilladt in kriterier:
        res.timer[graense] = timer_over(temperaturer, graense, brugstid)
        res.tilladt[graense] = tilladt
    return res


def vurder(rum, kriterier=KRITERIER_BOLIG, brugstid=None):
    """`rum` er {rumnavn: [temperaturer]}. Returnerer en liste af Rumresultat."""
    return [vurder_rum(n, t, kriterier, brugstid) for n, t in rum.items()]


def som_tabel(resultater):
    """Tekst-tabel til et Grasshopper-panel eller terminalen."""
    if not resultater:
        return "Ingen rum."
    graenser = list(resultater[0].timer)
    hoved = ["Rum"] + ["h > %g °C" % g for g in graenser] + ["Maks °C", ""]
    linjer = [hoved]
    for r in resultater:
        linjer.append(
            [r.navn]
            + ["%d / %d" % (r.timer[g], r.tilladt[g]) for g in graenser]
            + ["%.1f" % r.maks_temp, "OK" if r.ok else "IKKE OK"])
    bredder = [max(len(l[i]) for l in linjer) for i in range(len(hoved))]
    tekst = ["  ".join(c.ljust(b) for c, b in zip(l, bredder)).rstrip() for l in linjer]
    for r in resultater:
        tekst += ["! %s: %s" % (r.navn, a) for a in r.advarsler]
    return "\n".join(tekst)


def som_data(resultater):
    """Resultaterne som almindelige dicts, klar til JSON og notatet."""
    return {
        "kriterier": [[g, t] for g, t in resultater[0].tilladt.items()] if resultater else [],
        "rum": [
            {
                "navn": r.navn,
                "timer": {str(g): h for g, h in r.timer.items()},
                "tilladt": {str(g): h for g, h in r.tilladt.items()},
                "maks_temp": round(r.maks_temp, 2),
                "ok": r.ok,
                "advarsler": r.advarsler,
            }
            for r in resultater
        ],
        "ok": all(r.ok for r in resultater),
    }
