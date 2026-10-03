"""Tegner notatets figurer ud fra de JSON-filer, Grasshopper-komponenterne gemmer.

    python -m omkreds_energi.tegn <sagsmappe>/resultater [--format pdf png]

Læser overtemperatur.json og dagslys.json, hvis de findes, og gemmer figurerne i
<mappe>/figurer. Komponenterne kalder også `tegn_overtemperatur` og `tegn_dagslys` direkte.
"""
import argparse
import json
import os

from . import overtemperatur as ot, plots

FORMATER = ("pdf", "png")


def _gem(fig, mappe, navn, formater):
    os.makedirs(mappe, exist_ok=True)
    stier = []
    for f in formater:
        sti = os.path.join(mappe, f"{navn}.{f}")
        fig.savefig(sti, dpi=300, bbox_inches="tight", pad_inches=0.05)
        stier.append(sti)
    plots.plt.close(fig)
    return stier


def tegn_overtemperatur(rum, mappe, formater=FORMATER):
    """`rum` er {navn: [8760 operative temperaturer]}. Returnerer de gemte stier."""
    data = ot.som_data(ot.vurder(rum))
    stier = _gem(plots.overtemperatur_soejler(data), mappe, "overtemperatur_soejler", formater)
    stier += _gem(plots.varighedskurve(rum), mappe, "overtemperatur_varighed", formater)
    vaerst = max(data["rum"], key=lambda r: r["timer"][next(iter(r["timer"]))])
    stier += _gem(plots.temperaturtapet(rum[vaerst["navn"]], vaerst["navn"]), mappe,
                  "overtemperatur_tapet", formater)
    return stier


def tegn_dagslys(plotdata, mappe, formater=FORMATER):
    """`plotdata` har 'masker', 'da', 'omrids' og 'andel' (som dagslys-komponenten gemmer)."""
    fig = plots.dagslyskort(plotdata["masker"], plotdata["da"], plotdata.get("omrids", ()),
                            andel=plotdata.get("andel"))
    return _gem(fig, mappe, "dagslys_kort", formater)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mappe", help="mappen med overtemperatur.json og/eller dagslys.json")
    ap.add_argument("--format", nargs="+", default=list(FORMATER))
    a = ap.parse_args()
    ud = os.path.join(a.mappe, "figurer")
    stier = []
    p = os.path.join(a.mappe, "overtemperatur.json")
    if os.path.exists(p):
        stier += tegn_overtemperatur(json.load(open(p, encoding="utf-8"))["rum"], ud, a.format)
    p = os.path.join(a.mappe, "dagslys.json")
    if os.path.exists(p):
        stier += tegn_dagslys(json.load(open(p, encoding="utf-8")), ud, a.format)
    print("\n".join(stier) if stier else "Fandt hverken overtemperatur.json eller dagslys.json.")


if __name__ == "__main__":
    main()
