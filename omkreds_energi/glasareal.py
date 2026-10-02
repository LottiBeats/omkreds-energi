"""Dagslys efter BR18 § 379, 10 pct.-reglen med korrektioner af glasarealet.

Kilder (læst 2026-10-02):
- Bygningsreglementets vejledning om lys og udsyn, afsnit 1.2.
- Bygningsreglementets vejledning om korrektioner til 10 pct.-reglen for dagslys,
  TBST januar 2019 (Johnsen og Lumbye, SBi). Tabelnumrene nedenfor henviser hertil.

Glasarealet er vinduets frie åbningsareal (vinduesareal minus ramme, karm og sprosser).
For hvert vindue ganges glasarealet med de relevante korrektionsfaktorer:

    A_Gkor,i = F_LT · F_VÆG · F_OMG · F_OH · F_SF · F_AFS · F_ATR · F_RUM · F_FL · F_OVLYS · A_Gvin,i

og rummet har tilstrækkeligt dagslys, når  Σ A_Gkor,i ≥ 0,1 · A_gulv  (netto gulvareal).

I boliger kan soveværelser og børneværelser accepteres med lidt mindre, hvis deres
glasareal *uden korrektion for skyggende forhold* er mindst 10 % af gulvarealet, og
summen af de korrigerede glasarealer for alle beboelsesrum er mindst 10 % af deres
samlede gulvareal (se `vurder_bolig`).

Mellemværdier i tabellerne interpoleres lineært, som vejledningen anviser. Uden for
tabellerne bruges yderværdien.
"""

from bisect import bisect_right
from dataclasses import dataclass, field

KRAV = 0.10
LT_REF = 0.75


def _interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect_right(xs, x) - 1
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[i] + t * (ys[i + 1] - ys[i])


# --- Rudetype -------------------------------------------------------------------------

def f_lt(lt):
    """F_LT = LT_akt / 0,75. Kan være over 1 for ruder med høj lystransmittans."""
    return lt / LT_REF


# --- Tabel 1: vægtykkelse -------------------------------------------------------------

_VAEG_TYKKELSE = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
_VAEG_GLAS = [0.5, 1.0, 1.5, 2.0, 3.0]
_VAEG = [
    [1.00, 1.00, 0.81, 0.65, 0.51, 0.50],   # glas ≤ 0,5 m²
    [1.00, 1.00, 0.91, 0.80, 0.67, 0.56],   # 1,0 m²
    [1.00, 1.00, 0.96, 0.88, 0.76, 0.65],   # 1,5 m²
    [1.00, 1.00, 1.00, 0.95, 0.83, 0.71],   # 2,0 m²
    [1.00, 1.00, 1.00, 1.00, 1.00, 0.91],   # ≥ 3,0 m²
]


def f_vaeg(tykkelse, glasareal):
    """Vægtykkelse i m, glasareal for vinduet/vinduespartiet i m². Ingen korrektion < 0,4 m."""
    if tykkelse <= 0.4:
        return 1.0
    raekker = [_interp(tykkelse, _VAEG_TYKKELSE, r) for r in _VAEG]
    return _interp(glasareal, _VAEG_GLAS, raekker)


# --- Tabel 2: skyggende omgivelser ----------------------------------------------------

_OMG_V = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
_OMG_F = [1.00, 1.00, 0.95, 0.91, 0.84, 0.77, 0.66, 0.55, 0.50, 0.50, 0.50, 0.50]


def f_omg(profilvinkel):
    """Middelprofilvinkel (°) fra vinduets midte til overkanten af skyggegivere inden for ±45°."""
    return _interp(profilvinkel, _OMG_V, _OMG_F)


# --- Tabel 3: udhæng over vinduet ('uendeligt' langt) ---------------------------------

_OH_V = [0, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
_OH_F = [1.00, 1.00, 1.00, 1.00, 0.95, 0.89, 0.80, 0.70, 0.60, 0.55, 0.50, 0.50]


def f_oh(vinkel):
    """Vinkel V_OH (°) fra vinduets midte til udhængets forkant, målt fra lodret facade.

    Gælder for udhæng, der er 'uendeligt' langt (vinklerne α og β til udhængets hjørner
    er mindst 60°). For kortere udhæng: aflæs tabel 4 og giv faktoren direkte.
    """
    return _interp(vinkel, _OH_V, _OH_F)


# --- Tabel 5 og 6: fremspring ved siden af vinduet -----------------------------------

_SF_V = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
_SF_H = [40, 60, 80]
_SF = [
    [1.00, 0.97, 0.94, 0.91, 0.88, 0.85, 0.82, 0.79, 0.76, 0.74],   # h = 40°
    [1.00, 0.97, 0.94, 0.90, 0.85, 0.80, 0.75, 0.70, 0.64, 0.59],   # h = 60°
    [1.00, 0.97, 0.93, 0.88, 0.83, 0.78, 0.72, 0.66, 0.59, 0.53],   # h ≥ 80° (= tabel 5)
]


def f_sf(vinkel, hoejdevinkel=90):
    """Vinkel V_SF (°) i vandret plan til fremspringets forkant; højdevinkel h (°) til dets
    overkant. Uendeligt højt fremspring: h = 90 (tabel 5). h under 40° regnes som 40°."""
    raekker = [_interp(vinkel, _SF_V, r) for r in _SF]
    return _interp(hoejdevinkel, _SF_H, raekker)


# --- Tabel 9: faste lameller foran vinduet --------------------------------------------

_AFS_V = [0, 15, 30, 45]
_AFS = {"lys": [0.60, 0.52, 0.42, 0.30], "moerk": [0.50, 0.38, 0.26, 0.12]}


def f_afs(lamelhaeldning, farve="lys"):
    """Vejledende. Lyse lameller RL = 0,8, mørke RL = 0,2. Drejelige: mest åbne vinkel.
    Vandrette udhæng af lameller regnes som massive udhæng (f_oh)."""
    return _interp(lamelhaeldning, _AFS_V, _AFS[farve])


# --- Atrium ---------------------------------------------------------------------------

F_TAG = {"let": 0.8, "middel": 0.6, "tung": 0.4}


def f_atr(f_g_kor, lt_tag, tagkonstruktion="middel"):
    """F_ATR = F_G,kor · F_LT-tag · F_TAG (tabel 10). Udokumenteret: F_TAG højst 0,6."""
    return f_g_kor * lt_tag * F_TAG[tagkonstruktion]


# --- Tabel 11: rumdybde ---------------------------------------------------------------

_RUM_D = [5.0, 6.0, 7.0, 8.0]
_RUM_F = [1.00, 0.90, 0.77, 0.64]
F_RUM_BOLIG = 0.9   # boligrum med gulv mere end 6 m fra vinduer


def f_rum(dybde, bolig=True):
    """Bolig: 0,9 hvis der er gulv mere end 6 m fra vinduerne, ellers 1.
    Arbejdsrum: dybde til fjerneste arbejdsplads (tabel 11); over 8 m bør der regnes."""
    if bolig:
        return F_RUM_BOLIG if dybde > 6.0 else 1.0
    return _interp(dybde, _RUM_D, _RUM_F)


# --- Tabel 12 og 13: ovenlys og vinduer i flere flader ------------------------------

F_OVLYS = 1.4      # hældning ≤ 60° fra vandret
F_FL = 1.2         # vinduer i flere flader, hvis forholdet mellem fladerne er ≥ 0,3
FL_MIN_FORHOLD = 0.3


def er_ovenlys(haeldning_fra_vandret):
    return haeldning_fra_vandret <= 60.0


# --- Beregning ------------------------------------------------------------------------

@dataclass
class Vindue:
    navn: str
    glasareal: float                 # frit glasareal, m²
    lt: float = LT_REF
    flade: str = ""                  # fx "SV-facade" eller "tag" – til F_FL
    ovenlys: bool = False
    faktorer: dict = field(default_factory=dict)   # skyggefaktorer: navn -> værdi

    @property
    def f_skygge(self):
        f = 1.0
        for v in self.faktorer.values():
            f *= v
        return f

    @property
    def f_uden_fl(self):
        return f_lt(self.lt) * self.f_skygge * (F_OVLYS if self.ovenlys else 1.0)


@dataclass
class Rum:
    navn: str
    gulvareal: float                 # netto, m²
    vinduer: list
    soverum: bool = False            # soveværelse/børneværelse – lempelse i boliger
    f_rum: float = 1.0


@dataclass
class Rumresultat:
    navn: str
    gulvareal: float
    krav: float
    korrigeret: float
    uden_skygge: float               # korrigeret for alt andet end skyggende forhold
    f_fl: float
    vinduer: list                    # [(navn, glasareal, samlet faktor, korrigeret)]
    soverum: bool = False

    @property
    def ok(self):
        return self.korrigeret >= self.krav - 1e-9


def _f_fl(vinduer):
    pr_flade = {}
    for v in vinduer:
        pr_flade[v.flade] = pr_flade.get(v.flade, 0.0) + v.glasareal * v.f_uden_fl
    arealer = [a for a in pr_flade.values() if a > 0]
    if len(arealer) >= 2 and min(arealer) / max(arealer) >= FL_MIN_FORHOLD:
        return F_FL
    return 1.0


def vurder_rum(rum, krav=KRAV):
    f_fl = _f_fl(rum.vinduer)
    linjer, korrigeret, uden_skygge = [], 0.0, 0.0
    for v in rum.vinduer:
        f = v.f_uden_fl * rum.f_rum * f_fl
        korrigeret += f * v.glasareal
        uden_skygge += f / v.f_skygge * v.glasareal
        linjer.append((v.navn, v.glasareal, f, f * v.glasareal))
    return Rumresultat(rum.navn, rum.gulvareal, krav * rum.gulvareal, korrigeret,
                       uden_skygge, f_fl, linjer, rum.soverum)


def vurder_bolig(rum, krav=KRAV):
    """Returnerer (resultater, samlet_ok, noter).

    Soverum, der ikke klarer kravet med skyggekorrektion, accepteres, hvis de klarer det
    uden, og beboelsesrummene samlet klarer kravet med korrektioner.
    """
    res = [vurder_rum(r, krav) for r in rum]
    samlet_korr = sum(r.korrigeret for r in res)
    samlet_krav = sum(r.krav for r in res)
    samlet_ok = samlet_korr >= samlet_krav - 1e-9
    noter, ok = [], samlet_ok
    for r in res:
        if r.ok:
            continue
        if r.soverum and r.uden_skygge >= r.krav - 1e-9 and samlet_ok:
            noter.append("%s: accepteret som sove-/børneværelse (%.2f m² uden skyggekorrektion "
                         "≥ %.2f m², og boligen samlet overholder kravet)"
                         % (r.navn, r.uden_skygge, r.krav))
        else:
            ok = False
            noter.append("%s: %.2f m² korrigeret glas < %.2f m²" % (r.navn, r.korrigeret, r.krav))
    return res, ok, noter


def som_tabel(resultater):
    linjer = [["Rum", "Gulv m²", "Krav m²", "Korr. glas m²", "Andel", ""]]
    for r in resultater:
        linjer.append([r.navn, "%.1f" % r.gulvareal, "%.2f" % r.krav, "%.2f" % r.korrigeret,
                       "%.1f %%" % (100 * r.korrigeret / r.gulvareal),
                       "OK" if r.ok else "IKKE OK"])
    bredder = [max(len(l[i]) for l in linjer) for i in range(len(linjer[0]))]
    return "\n".join("  ".join(c.ljust(b) for c, b in zip(l, bredder)).rstrip() for l in linjer)
