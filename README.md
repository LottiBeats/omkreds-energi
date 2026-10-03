# omkreds energi

Værktøj til indeklima- og energidokumentation efter BR18. Bygningen modelleres i
Rhino/Grasshopper med Ladybug Tools, og beregningerne ligger her som almindelig Python 3,
så de kan testes uden Rhino.

```
omkreds_energi/   beregninger (ren Python, ingen Rhino)
  overtemperatur.py   timer over 27/28 °C pr. rum, BR18 § 386
  dagslys.py          300 lux-metoden, § 379 (boligen som helhed, dagslystimer, net-tjek)
  glasareal.py        10 pct.-reglen med alle korrektionsfaktorer fra TBST's vejledning
  plots.py            figurer til notatet: søjler, varighedskurver, temperaturtapet, dagslyskort
  tegn.py             tegner figurerne fra komponenternes JSON: python -m omkreds_energi.tegn <mappe>
grasshopper/      tynde Script-komponenter til Rhino 8, der kalder omkreds_energi
tests/            pytest
eksempler/        plots_eksempel.py tegner alle figurer med opdigtede data
projekter/        én mappe pr. sag – ligger ikke i git (kun projekter/eksempel/)
```

## Grasshopper

Komponenterne er Rhino 8 Script-komponenter i Python 3. Hver fil beskriver selv sine
inputs og outputs øverst. Giv `_repo` stien til denne mappe.

## Test

```bash
pip install pytest matplotlib
python -m pytest
```

## Kilder

Reglerne er tjekket mod bygningsreglementet.dk den 2. oktober 2026 og står i toppen af
hvert modul:

- § 386 og vejledningen om termisk indeklima (overtemperatur)
- § 379 og vejledningen om lys og udsyn, afsnit 1.2 (dagslys, 300 lux)
- TBST: Vejledning om korrektioner til 10 pct.-reglen for dagslys, januar 2019

Tjek igen, når der kommer en ny version af BR18.

## Plan

1. Overtemperatur (§ 386) ✔
2. Dagslys (§ 379): 300 lux-metoden og 10 pct.-reglen ✔
3. Figurer til notatet ✔
4. Notatgenerator (PDF)
5. Varmetabsramme og dimensionerende varmetab (DS 418)
6. Energiramme

## Forbehold

Beregningerne er et værktøj. Den ansvarlige rådgiver kontrollerer og underskriver.
