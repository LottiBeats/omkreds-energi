"""Laver eksempelplots med opdigtede data: python eksempler/plots_eksempel.py <udmappe>"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from omkreds_energi import overtemperatur as ot, dagslys as dl, plots

ud = sys.argv[1] if len(sys.argv) > 1 else "plots_eksempel"
os.makedirs(ud, exist_ok=True)
rnd = random.Random(1)


def aar(sommer, sol):
    """Opdigtet operativ temperatur for et år: årstid, døgn, solbidrag og støj."""
    t = []
    for time in range(8760):
        d, h = divmod(time, 24)
        aarstid = -math.cos(2 * math.pi * (d - 15) / 365)
        doegn = max(0.0, math.sin(math.pi * (h - 7) / 12)) if 7 <= h <= 19 else 0.0
        t.append(21.5 + 2.2 * aarstid + sommer * max(0, aarstid) + sol * doegn * (0.6 + 0.4 * max(0, aarstid))
                 + rnd.gauss(0, 0.35))
    return t


rum = {"Stue og køkken": aar(0.6, 2.0), "Soverum 1. sal": aar(1.3, 2.9), "Værelse": aar(0.5, 1.8),
       "Bad": aar(0.2, 1.0), "Kontor": aar(0.8, 2.4)}
data = ot.som_data(ot.vurder(rum))
plots.gem(plots.overtemperatur_soejler(data), os.path.join(ud, "overtemperatur_soejler.png"))
plots.gem(plots.varighedskurve(rum), os.path.join(ud, "varighedskurve.png"))
plots.gem(plots.temperaturtapet(rum["Soverum 1. sal"], "Soverum 1. sal"), os.path.join(ud, "temperaturtapet.png"))

# dagslys: to rum med vinduer mod syd (y = 0)
masker, da, omrids = [], [], []
for (x0, x1, y0, y1, vinduer) in [(0, 6.0, 0, 4.4, [1.5, 4.0]), (6.2, 9.6, 0, 3.6, [7.9])]:
    omrids.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    s = 0.5
    y = y0 + 0.5
    while y + s <= y1 - 0.5 + 1e-9:
        x = x0 + 0.5
        while x + s <= x1 - 0.5 + 1e-9:
            cx, cy = x + s / 2, y + s / 2
            v = sum(95 * math.exp(-((cx - vx) ** 2) / 3.5) for vx in vinduer) * math.exp(-(cy - y0) / 2.2)
            masker.append([(x, y), (x + s, y), (x + s, y + s), (x, y + s)])
            da.append(max(0, min(100, v + rnd.gauss(0, 3))))
            x += s
        y += s
andel = dl.andel_opfyldt(da)
plots.gem(plots.dagslyskort(masker, da, omrids, andel=andel), os.path.join(ud, "dagslyskort.png"))
print("gemt i", ud)
