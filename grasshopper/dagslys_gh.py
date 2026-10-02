"""Grasshopper: dagslys efter BR18 § 379 (300 lux i halvdelen af dagslystimerne).

Rhino 8 Script-komponent, Python 3. Indsæt filen og lav:
  inputs   _repo    (str)          stien til omkreds-energi
           _da      (Tree Access)  DA pr. målepunkt fra HB Annual Daylight med tærsklen
                                   300 lux og skemaet sat til dagslystimerne, én gren pr. rum
           _mesh_   (List Access)  målenettets mesh pr. rum: vægter punkterne med areal og
                                   tjekker maskerne (valgfri, men anbefalet)
           _navne_  (List Access)  rumnavne (valgfri)
           _bolig_  (bool)         True: boligen som helhed, net i 0,50 m (standard)
                                   False: arbejdsrum, hvert rum for sig, net i 0,85 m
  outputs  tabel, ok, data

Beregningsnettet: 0,50 m over gulv i boliger (0,85 m i arbejdsrum), 0,5 m randzone
fra væggene, lige store masker med længste side højst 1,0 m.

Selve beregningen ligger i omkreds_energi/dagslys.py.
"""
import json
import sys

if _repo and _repo not in sys.path:
    sys.path.insert(0, _repo)

import importlib
from omkreds_energi import dagslys as dl
importlib.reload(dl)


def _afstand(a, b):
    return ((a.X - b.X) ** 2 + (a.Y - b.Y) ** 2 + (a.Z - b.Z) ** 2) ** 0.5


def _trekant(a, b, c):
    ux, uy, uz = b.X - a.X, b.Y - a.Y, b.Z - a.Z
    vx, vy, vz = c.X - a.X, c.Y - a.Y, c.Z - a.Z
    return 0.5 * ((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2) ** 0.5


def _masker(mesh):
    """(areal, (side_a, side_b)) pr. flade, i samme rækkefølge som Honeybee's målepunkter."""
    v = mesh.Vertices
    ud = []
    for i in range(mesh.Faces.Count):
        f = mesh.Faces[i]
        a = _trekant(v[f.A], v[f.B], v[f.C])
        if f.IsQuad:
            a += _trekant(v[f.A], v[f.C], v[f.D])
        ud.append((a, (_afstand(v[f.A], v[f.B]), _afstand(v[f.B], v[f.C]))))
    return ud


bolig = True if _bolig_ is None else bool(_bolig_)
rum, arealer, net = {}, {}, []
for i, gren in enumerate(_da.Branches if _da else []):
    navn = str(_navne_[i]) if _navne_ and i < len(_navne_) else "Rum %d" % (i + 1)
    rum[navn] = [float(v) for v in gren]
    if _mesh_ and i < len(_mesh_) and _mesh_[i] is not None:
        masker = _masker(_mesh_[i])
        arealer[navn] = [m[0] for m in masker]
        net += ["%s: %s" % (navn, a) for a in dl.tjek_net([m[1] for m in masker])]

if rum:
    resultater = dl.vurder(rum, arealer)
    data_dict = dl.som_data(resultater, bolig=bolig, net_advarsler=net)
    tabel = dl.som_tabel(resultater, bolig=bolig)
    if net:
        tabel += "\n" + "\n".join("! net – " + a for a in net)
    if not arealer:
        tabel += "\n! uden _mesh_ tælles alle punkter lige – kun rigtigt ved lige store masker"
    ok = data_dict["ok"]
    data = json.dumps(data_dict, ensure_ascii=False)
else:
    tabel, ok, data = "Ingen DA-værdier på _da.", None, None
