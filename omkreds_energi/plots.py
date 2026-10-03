"""Plots til notaterne: overtemperatur (§ 386) og dagslys (§ 379).

Grasshopper eksporterer tallene; plottene laves her med matplotlib, så de ser ens ud
fra sag til sag og kan gemmes som PDF/SVG til tryk og PNG til skærm.

Stilen: data i gråtoner, det der ikke overholder kravet i én accentfarve. Mål er i cm,
så figurerne passer ind i en A4-side uden skalering (16 cm = tekstbredden).
"""
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, ListedColormap

CM = 1 / 2.54
BREDDE = 16 * CM

SORT = "#1A1A1A"
GRAA = "#9A9A9A"
LYSGRAA = "#D9D9D9"
ACCENT = "#E74825"

STIL = {
    # Schibsted Grotesk bruges, hvis den er installeret (Google Fonts); ellers Arial.
    "font.family": ["Schibsted Grotesk", "Arial", "sans-serif"],
    "font.size": 8.5,
    "axes.edgecolor": SORT,
    "axes.labelcolor": SORT,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 10,
    "xtick.color": SORT,
    "ytick.color": SORT,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.frameon": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
}

MAANEDER = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
MAANED_START = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


def _tal(x):
    """Dansk talformat: 1.234,5"""
    s = f"{x:,.0f}" if float(x).is_integer() else f"{x:,.1f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def gem(fig, sti):
    """Gemmer som den filtype, stien slutter på (.pdf, .svg, .png)."""
    fig.savefig(sti, dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


# --- Overtemperatur ------------------------------------------------------------------

def overtemperatur_soejler(data):
    """Vandrette søjler pr. rum med grænserne. `data` er som_data() fra overtemperatur."""
    rum = sorted(data["rum"], key=lambda r: -r["timer"][next(iter(r["timer"]))])
    graenser = list(rum[0]["timer"].keys())
    with plt.rc_context(STIL):
        n = len(rum)
        fig, akser = plt.subplots(1, len(graenser), figsize=(BREDDE, (1.4 + 0.55 * n) * CM * 1.6),
                                  sharey=True, gridspec_kw={"wspace": 0.12})
        for ax, g in zip(akser, graenser):
            tilladt = rum[0]["tilladt"][g]
            vaerdier = [r["timer"][g] for r in rum]
            farver = [ACCENT if v > tilladt else GRAA for v in vaerdier]
            y = range(n)
            ax.barh(y, vaerdier, color=farver, height=0.62, zorder=2)
            ax.axvline(tilladt, color=SORT, lw=0.9, ls=(0, (3, 2)), zorder=3)
            maks = max(max(vaerdier), tilladt) * 1.22
            ax.set_xlim(0, maks)
            for yi, v in zip(y, vaerdier):
                ax.text(v + maks * 0.015, yi, _tal(v), va="center", fontsize=8,
                        color=ACCENT if v > tilladt else SORT, fontweight="bold" if v > tilladt else "normal")
            ax.set_title(f"Timer over {_tal(float(g))} °C  ·  grænse {_tal(tilladt)} h")
            ax.spines["left"].set_visible(False)
            ax.tick_params(axis="y", length=0)
            ax.set_xlabel("timer pr. år")
        akser[0].set_yticks(range(n), [r["navn"] for r in rum])
        akser[0].invert_yaxis()
        return fig


def varighedskurve(rum, graenser=(27, 28), titel="Operativ temperatur, sorteret – varmeste timer"):
    """Varighedskurver: årets timer sorteret efter temperatur, de 400 varmeste vist.
    `rum` er {navn: [8760 temperaturer]}. Rum der overskrider 100 h over 27 °C får accentfarven."""
    with plt.rc_context(STIL):
        fig, ax = plt.subplots(figsize=(BREDDE, 7 * CM))
        vis = 400
        for navn, t in rum.items():
            s = sorted(t, reverse=True)[:vis]
            daarlig = sum(1 for v in t if v > graenser[0]) > 100
            ax.plot(range(1, vis + 1), s, color=ACCENT if daarlig else GRAA, lw=1.6 if daarlig else 1.0,
                    zorder=3 if daarlig else 2)
            ax.text(vis + 6, s[-1], navn, va="center", fontsize=7.5, color=ACCENT if daarlig else SORT)
        for g, h in zip(graenser, (100, 25)):
            ax.axhline(g, color=SORT, lw=0.6, ls=(0, (3, 2)))
            ax.axvline(h, color=LYSGRAA, lw=0.8, zorder=1)
            ax.text(h + 3, ax.get_ylim()[1], f"{h} h", va="top", fontsize=7.5, color=GRAA)
        ax.set_xlim(0, vis)
        ax.set_xlabel("antal timer pr. år med mindst denne temperatur")
        ax.set_ylabel("°C")
        ax.set_title(titel)
        ax.yaxis.set_major_formatter(lambda v, _: _tal(v))
        return fig


def temperaturtapet(temp, navn, graense=27.0):
    """Hele året som et tæppe: dag på x-aksen, time på y-aksen, operativ temperatur som farve.
    Timer over grænsen står i accentfarven, så man ser hvornår på døgnet og året de ligger."""
    dage = len(temp) // 24
    grid = [[temp[d * 24 + h] for d in range(dage)] for h in range(24)]
    lo = math.floor(min(temp))
    with plt.rc_context(STIL):
        fig, ax = plt.subplots(figsize=(BREDDE, 6.2 * CM))
        graa = LinearSegmentedColormap.from_list("graa", ["#F4F4F4", "#2A2A2A"])
        trin = [lo + i * (graense - lo) / 10 for i in range(11)] + [graense + 1, graense + 50]
        farver = [graa(i / 9) for i in range(10)] + ["#F2A08A", ACCENT]
        cmap = ListedColormap(farver)
        norm = BoundaryNorm(trin, cmap.N)
        im = ax.imshow(grid, aspect="auto", cmap=cmap, norm=norm, origin="lower",
                       extent=(0, dage, 0, 24), interpolation="nearest")
        ax.set_yticks([0, 6, 12, 18, 24], ["0", "6", "12", "18", "24"])
        ax.set_xticks([m + 15 for m in MAANED_START], MAANEDER)
        ax.tick_params(axis="x", length=0)
        ax.set_ylabel("kl.")
        timer = sum(1 for v in temp if v > graense)
        ax.set_title(f"{navn}: {_tal(timer)} timer over {_tal(graense)} °C")
        for s in ax.spines.values():
            s.set_visible(False)
        cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.03, ticks=[lo, graense, graense + 1])
        cb.ax.set_yticklabels([_tal(lo), _tal(graense), _tal(graense + 1)])
        cb.outline.set_visible(False)
        cb.set_label("°C", rotation=0, labelpad=6)
        return fig


# --- Dagslys -------------------------------------------------------------------------

def dagslyskort(masker, da, rum_omrids=(), titel="Dagslys: andel af dagslystimerne med 300 lux",
                krav_tid=50.0, andel=None):
    """Plan med beregningsnettet farvet efter DA (%).

    `masker` er en liste af polygoner [(x, y), ...] i m, én pr. målepunkt (fra målenettets mesh).
    `rum_omrids` er rummenes polygoner. Masker under krav_tid er grå, masker over er sorte
    toner, og grænsen ved krav_tid tegnes som en tydelig kontur."""
    with plt.rc_context(STIL):
        xs = [p[0] for m in masker for p in m] + [p[0] for r in rum_omrids for p in r]
        ys = [p[1] for m in masker for p in m] + [p[1] for r in rum_omrids for p in r]
        bx, by = max(xs) - min(xs), max(ys) - min(ys)
        h = min(13 * CM, BREDDE * by / bx * 0.86 + 1.6 * CM)
        fig, ax = plt.subplots(figsize=(BREDDE, h))
        trin = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        farver = ["#F7F7F7", "#EDEDED", "#E0E0E0", "#D0D0D0", "#BDBDBD",
                  "#FBD3C6", "#F7AE96", "#F28A67", "#EC6A44", ACCENT]
        cmap = ListedColormap(farver)
        norm = BoundaryNorm(trin, cmap.N)
        pc = PolyCollection(masker, array=da, cmap=cmap, norm=norm, edgecolors="#FFFFFF", linewidths=0.3)
        ax.add_collection(pc)
        for r in rum_omrids:
            xs_r, ys_r = zip(*(list(r) + [r[0]]))
            ax.plot(xs_r, ys_r, color=SORT, lw=1.6, solid_joinstyle="miter")
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.axis("off")
        if andel is not None:
            titel += f" · {_tal(round(andel))} % af gulvet opfylder kravet"
        ax.set_title(titel)
        cb = fig.colorbar(pc, ax=ax, orientation="horizontal", fraction=0.05, pad=0.04, aspect=40,
                          ticks=trin)
        cb.ax.set_xticklabels([f"{t}" for t in trin])
        cb.outline.set_visible(False)
        cb.ax.axvline(krav_tid, color=SORT, lw=1.2)
        cb.set_label(f"% af dagslystimerne med mindst 300 lux · krav: {_tal(krav_tid)} % af tiden på halvdelen af gulvet",
                     fontsize=7.5)
        return fig
