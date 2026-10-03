"""Tegninger til rapporten ud fra en Honeybee-model (HBJSON) i stedet for skærmbilleder fra Rhino.

Gem modellen i Grasshopper med *HB Dump Objects* (model.hbjson). Så tegnes:

- `aksonometri`: huset set skråt ovenfra, med vinduer, som stregtegning med lyse flader
- `plan`: rummenes gulve set ovenfra med navne, farvet efter en værdi pr. rum
- `solbane`: solens bane på himlen for en placering, månedsvis, med klokkeslæt

Kræver honeybee-core og ladybug-core (pip install honeybee-core ladybug-core).
"""
import math

from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize

from .plots import plt, STIL, CM, BREDDE, SORT, GRAA, LYSGRAA, ACCENT, _tal

VAEG = "#ECECE8"
TAG = "#D6D6D1"
GLAS = "#A9C0CB"
SKYGGE = "#C9C9C4"


def indlaes(sti):
    from honeybee.model import Model
    return Model.from_hbjson(sti)


def rumnavn(rum):
    return rum.display_name or rum.identifier


def find_rum(model, noegle):
    """Rum ud fra et navn eller id, som det står i resultaterne (EnergyPlus skriver id'er med store bogstaver)."""
    n = str(noegle).casefold()
    for r in model.rooms:
        if r.identifier.casefold() == n or (r.display_name or "").casefold() == n:
            return r
    return None


# --- aksonometri ---------------------------------------------------------------------

def _projektion(azimut, hoejde):
    a, h = math.radians(azimut), math.radians(hoejde)
    ca, sa, ch, sh = math.cos(a), math.sin(a), math.cos(h), math.sin(h)

    def p(pt):
        x, y, z = pt.x, pt.y, pt.z
        xr = x * ca - y * sa
        yr = x * sa + y * ca
        return (xr, yr * sh + z * ch), yr * ch - z * sh   # (2D-punkt, dybde: større er længere væk)

    def mod_kamera(n):
        nyr = n.x * sa + n.y * ca
        return nyr * ch - n.z * sh < 0   # fladen vender mod beskueren

    return p, mod_kamera


def aksonometri(model, azimut=35, hoejde=32, titel=None):
    """Stregtegning af klimaskærmen. Indvendige flader mellem rum tegnes ikke."""
    p, mod_kamera = _projektion(azimut, hoejde)
    flader = []
    for rum in model.rooms:
        for f in rum.faces:
            if f.boundary_condition.__class__.__name__ == "Surface" or not mod_kamera(f.normal):
                continue
            pts = [p(v) for v in f.geometry.vertices]
            dybde = sum(d for _, d in pts) / len(pts)
            farve = TAG if f.type.name in ("RoofCeiling",) else VAEG
            if f.type.name == "Floor":
                continue
            flader.append((dybde, [q for q, _ in pts], farve, 0.6))
            for ap in f.apertures + f.doors:
                ap_pts = [p(v) for v in ap.geometry.vertices]
                flader.append((dybde - 1e-3, [q for q, _ in ap_pts], GLAS if ap in f.apertures else VAEG, 0.45))
    for s in model.shades:
        if not mod_kamera(s.geometry.normal):
            continue
        pts = [p(v) for v in s.geometry.vertices]
        flader.append((sum(d for _, d in pts) / len(pts), [q for q, _ in pts], SKYGGE, 0.4))
    flader.sort(key=lambda f: -f[0])  # fjerneste først

    with plt.rc_context(STIL):
        fig, ax = plt.subplots(figsize=(BREDDE, 9 * CM))
        for _, poly, farve, lw in flader:
            ax.add_collection(PolyCollection([poly], facecolors=farve, edgecolors=SORT, linewidths=lw,
                                             joinstyle="round"))
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.axis("off")
        if titel:
            ax.set_title(titel)
        return fig


# --- plan ----------------------------------------------------------------------------

def _gulve(rum):
    return [f for f in rum.faces if f.type.name == "Floor"] or [min(rum.faces, key=lambda f: f.center.z)]


def plan(model, vaerdier=None, enhed="", titel=None, graense=None, hoej_er_daarlig=True, etage=None):
    """Gulvene set ovenfra. `vaerdier` er {rum-id eller navn: tal}; rum uden værdi står hvide.

    Med `graense` får rum på den forkerte side af grænsen accentfarven, de øvrige gråtoner.
    `etage` vælger gulvhøjden (m); som standard laveste etage.
    """
    vaerdier = {str(k).casefold(): v for k, v in (vaerdier or {}).items()}
    rum_paa_etage = []
    hoejder = sorted({round(min(f.center.z for f in _gulve(r)), 1) for r in model.rooms})
    z0 = hoejder[0] if etage is None else min(hoejder, key=lambda h: abs(h - etage))
    for r in model.rooms:
        if round(min(f.center.z for f in _gulve(r)), 1) == z0:
            rum_paa_etage.append(r)

    def vaerdi(r):
        for k in (r.identifier, r.display_name or ""):
            if k.casefold() in vaerdier:
                return vaerdier[k.casefold()]
        return None

    tal = [v for v in (vaerdi(r) for r in rum_paa_etage) if v is not None]
    norm = Normalize(min(tal + [0]), max(tal + [1]))
    graa = LinearSegmentedColormap.from_list("graa", ["#F2F2F0", "#9C9C97"])

    with plt.rc_context(STIL):
        fig, ax = plt.subplots(figsize=(BREDDE, 8.5 * CM))
        for r in rum_paa_etage:
            v = vaerdi(r)
            if v is None:
                farve = "#FFFFFF"
            elif graense is not None and ((v > graense) if hoej_er_daarlig else (v < graense)):
                farve = "#F4B3A0"
            else:
                farve = graa(norm(v))
            for f in _gulve(r):
                poly = [(pt.x, pt.y) for pt in f.geometry.boundary]
                ax.add_collection(PolyCollection([poly], facecolors=farve, edgecolors=SORT, linewidths=1.4,
                                                 joinstyle="miter"))
            c = r.geometry.center if hasattr(r, "geometry") else _gulve(r)[0].center
            tekst = rumnavn(r) + (f"\n{_tal(round(v, 1))} {enhed}".rstrip() if v is not None else "")
            ax.text(c.x, c.y, tekst, ha="center", va="center", fontsize=7.5, color=SORT, linespacing=1.3)
            # vinduer som tykke streger på gulvets kant
            for f in r.faces:
                for ap in f.apertures:
                    pts = ap.geometry.vertices
                    lav = [pt for pt in pts if abs(pt.z - min(q.z for q in pts)) < 1e-6] or pts[:2]
                    if f.type.name == "Wall" and len(lav) >= 2:
                        ax.plot([lav[0].x, lav[-1].x], [lav[0].y, lav[-1].y], color=GLAS, lw=3.2,
                                solid_capstyle="butt", zorder=3)
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.margins(0.04)
        ax.axis("off")
        if titel:
            ax.set_title(titel)
        return fig


# --- solbane -------------------------------------------------------------------------

MAANED_NAVN = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


def solbane(bredde, laengde, tidszone=1, titel=None):
    """Solbanediagram (polært): azimut rundt, højde ind mod midten. 21. i hver måned og hel time."""
    from ladybug.sunpath import Sunpath
    sp = Sunpath(bredde, laengde, tidszone)

    def r(alt):
        return 90 - alt

    with plt.rc_context(STIL):
        fig = plt.figure(figsize=(BREDDE * 0.62, BREDDE * 0.62))
        ax = fig.add_subplot(projection="polar")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        for m in (12, 1, 2, 3, 4, 5, 6):
            pts = [sp.calculate_sun(m, 21, h / 4) for h in range(0, 24 * 4)]
            pts = [s for s in pts if s.altitude > 0]
            if not pts:
                continue
            ax.plot([math.radians(s.azimuth) for s in pts], [r(s.altitude) for s in pts],
                    color=ACCENT if m == 6 else (SORT if m == 12 else GRAA), lw=1.2 if m in (6, 12) else 0.7)
            top = max(pts, key=lambda s: s.altitude)
            navn = {6: "21. jun", 12: "21. dec", 3: "21. mar/sep"}.get(m)
            if navn:
                ax.text(math.radians(top.azimuth), r(top.altitude) - 3, navn, ha="center", va="top", fontsize=7,
                        color=ACCENT if m == 6 else SORT)
        for h in range(4, 22):
            pts = [sp.calculate_sun(m, 21, h) for m in (6, 7, 5, 8, 4, 9, 3, 10, 2, 11, 1, 12)]
            pts = sorted([s for s in pts if s.altitude > 0], key=lambda s: s.altitude)
            if len(pts) > 1:
                ax.plot([math.radians(s.azimuth) for s in pts], [r(s.altitude) for s in pts], color=LYSGRAA, lw=0.6,
                        zorder=1)
                s = pts[-1]
                ax.text(math.radians(s.azimuth), r(s.altitude) - 4, f"{h}", fontsize=6.5, color=GRAA, ha="center")
        ax.set_rlim(0, 90)
        ax.set_rticks([0, 30, 60, 90], ["90°", "60°", "30°", ""])
        ax.set_xticks([math.radians(a) for a in (0, 90, 180, 270)], ["N", "Ø", "S", "V"])
        ax.grid(color=LYSGRAA, lw=0.5)
        ax.spines["polar"].set_color(SORT)
        ax.spines["polar"].set_linewidth(0.6)
        ax.tick_params(labelsize=7.5)
        ax.set_title(titel or f"Solbane, {_tal(round(bredde, 2))}° N · {_tal(round(laengde, 2))}° Ø", pad=16)
        return fig
