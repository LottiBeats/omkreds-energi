"""Grasshopper: dagslys efter BR18 § 379 (300 lux i halvdelen af dagslystimerne).

Rhino 8 Script-komponent, Python 3. Indsæt filen og lav:
  inputs   _repo         (str)          stien til omkreds-energi
           _da           (Tree Access)  DA pr. målepunkt fra HB Annual Daylight med
                                        tærsklen 300 lux, én gren pr. rum
           _mesh_        (List Access)  målenettets mesh pr. rum, så punkterne vægtes
                                        med fladeareal (valgfri)
           _navne_       (List Access)  rumnavne (valgfri)
           _maalehoejde_ (float)        målehøjde i m, kommer med i notatet (valgfri)
           _randzone_    (float)        randzone i m, kommer med i notatet (valgfri)
  outputs  tabel, ok, data

Selve beregningen ligger i omkreds_energi/dagslys.py.
"""
import json
import sys

if _repo and _repo not in sys.path:
    sys.path.insert(0, _repo)

import importlib
from omkreds_energi import dagslys as dl
importlib.reload(dl)


def _trekant(a, b, c):
    ux, uy, uz = b.X - a.X, b.Y - a.Y, b.Z - a.Z
    vx, vy, vz = c.X - a.X, c.Y - a.Y, c.Z - a.Z
    return 0.5 * ((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2) ** 0.5


def _fladearealer(mesh):
    # Rhino.Geometry.Mesh: areal pr. flade, samme rækkefølge som Honeybee's målepunkter
    v = mesh.Vertices
    arealer = []
    for i in range(mesh.Faces.Count):
        f = mesh.Faces[i]
        a = _trekant(v[f.A], v[f.B], v[f.C])
        if f.IsQuad:
            a += _trekant(v[f.A], v[f.C], v[f.D])
        arealer.append(a)
    return arealer


rum, arealer = {}, {}
for i, gren in enumerate(_da.Branches if _da else []):
    navn = str(_navne_[i]) if _navne_ and i < len(_navne_) else "Rum %d" % (i + 1)
    rum[navn] = [float(v) for v in gren]
    if _mesh_ and i < len(_mesh_) and _mesh_[i] is not None:
        arealer[navn] = _fladearealer(_mesh_[i])

if rum:
    resultater = dl.vurder(rum, arealer)
    tabel = dl.som_tabel(resultater)
    ok = all(r.ok for r in resultater)
    data = json.dumps(dl.som_data(resultater, _maalehoejde_, _randzone_), ensure_ascii=False)
else:
    tabel, ok, data = "Ingen DA-værdier på _da.", None, None
