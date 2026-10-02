"""Grasshopper: timer over 27/28 °C pr. rum (BR18 § 386).

Rhino 8 Script-komponent, Python 3. Indsæt filen og lav:
  inputs   _repo    (str)          stien til omkreds-energi
           _temp    (Tree Access)  oper_temp pr. rum, én gren pr. rum (8760 værdier)
           _navne_  (List Access)  rumnavne i samme rækkefølge som grenene (valgfri)
  outputs  tabel, ok, data

Selve beregningen ligger i omkreds_energi/overtemperatur.py, så den kan testes uden Rhino.
"""
import json
import sys

if _repo and _repo not in sys.path:
    sys.path.insert(0, _repo)

import importlib
from omkreds_energi import overtemperatur as ot
importlib.reload(ot)  # så rettelser i modulet slår igennem uden at genstarte Rhino


def _tal(v):
    # LB-datacollections har .values; ellers forventes tal
    return list(v.values) if hasattr(v, "values") else [float(v)]


rum = {}
for i, gren in enumerate(_temp.Branches if _temp else []):
    vaerdier = []
    for v in gren:
        vaerdier.extend(_tal(v))
    navn = _navne_[i] if _navne_ and i < len(_navne_) else "Rum %d" % (i + 1)
    rum[str(navn)] = vaerdier

if rum:
    resultater = ot.vurder(rum)
    tabel = ot.som_tabel(resultater)
    ok = all(r.ok for r in resultater)
    data = json.dumps(ot.som_data(resultater), ensure_ascii=False)
else:
    tabel, ok, data = "Ingen temperaturer på _temp.", None, None
