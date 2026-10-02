# omkreds energi

Værktøj til indeklima- og energidokumentation efter BR18. Bygningen modelleres i
Rhino/Grasshopper med Ladybug Tools, og beregningerne ligger her som almindelig Python 3,
så de kan testes uden Rhino.

```
omkreds_energi/   beregninger (ren Python, ingen Rhino)
  overtemperatur.py   timer over 27/28 °C pr. rum, BR18 § 386
grasshopper/      tynde Script-komponenter til Rhino 8, der kalder omkreds_energi
tests/            pytest
projekter/        én mappe pr. sag – ligger ikke i git (kun projekter/eksempel/)
```

## Grasshopper

Komponenterne er Rhino 8 Script-komponenter i Python 3. Hver fil beskriver selv sine
inputs og outputs øverst. Giv `_repo` stien til denne mappe.

## Test

```bash
pip install pytest
python -m pytest
```

## Plan

1. Overtemperatur (§ 386) ✔
2. Dagslys (§ 379): andel af gulvet med 300 lux i halvdelen af dagslystimerne
3. Notatgenerator (PDF) i omkreds-stil
4. Varmetabsramme og dimensionerende varmetab (DS 418)
5. Energiramme

## Forbehold

Beregningerne er et værktøj. Den ansvarlige rådgiver kontrollerer og underskriver.
