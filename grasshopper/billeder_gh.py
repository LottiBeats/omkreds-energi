"""Grasshopper: billeder til rapporten, ét pr. gruppe, uden at plots fylder hinandens billeder.

Rhino 8 Script-komponent, Python 3. Læg hvert plot (model, plan, dagslyskort, solbane, komfortkort …)
i sin egen Grasshopper-gruppe og giv gruppen et navn. Komponenten tager så for hver linje i _billeder:

  1. skjuler preview af alle andre komponenter og alle Rhino-objekter,
  2. sætter den aktive viewport til den ønskede retning og zoomer ind på gruppens geometri,
  3. gemmer billedet med gennemsigtig baggrund,
  4. sætter alt tilbage, som det var.

Inputs   _mappe     (str)          mappen, billederne gemmes i (fx sagens billeder/)
         _billeder  (List Access)  linjer "filnavn = Gruppenavn | retning", fx
                                     model_iso = Model | iso
                                     temperatur_plan = Temperaturplot | top
                                     solbane = Solbane | iso
                                   retning: iso (fra sydvest), iso_no, top, syd, nord, øst, vest
         _bredde_   (int)          standard 3200
         _hoejde_   (int)          standard 2000
         _koer      (bool)         knap: tag billederne
Outputs  rapport

Komponenten skal beregnes efter plottene: sæt den sidst på lærredet, og tryk på knappen,
når alt er beregnet.
"""
import os

import System
import Rhino
import Grasshopper as gh

RETNINGER = {
    "iso": Rhino.Geometry.Vector3d(1, 1, -0.8),       # set fra sydvest
    "iso_no": Rhino.Geometry.Vector3d(-1, -1, -0.8),  # set fra nordøst
    "iso_so": Rhino.Geometry.Vector3d(-1, 1, -0.8),
    "iso_nv": Rhino.Geometry.Vector3d(1, -1, -0.8),
    "top": None,
    "syd": Rhino.Geometry.Vector3d(0, 1, 0),
    "nord": Rhino.Geometry.Vector3d(0, -1, 0),
    "øst": Rhino.Geometry.Vector3d(-1, 0, 0),
    "vest": Rhino.Geometry.Vector3d(1, 0, 0),
}


def tolk(linje):
    if "=" not in linje:
        return None
    fil, rest = [x.strip() for x in linje.split("=", 1)]
    gruppe, retning = (rest.split("|", 1) + ["iso"])[:2]
    fil = fil if fil.lower().endswith(".png") else fil + ".png"
    return fil, gruppe.strip(), retning.strip().lower() or "iso"


def gruppens_objekter(ghdoc, navn):
    for o in ghdoc.Objects:
        if isinstance(o, gh.Kernel.Special.GH_Group) and o.NickName.strip().lower() == navn.lower():
            ids = set(o.ObjectIDs)
            return [x for x in ghdoc.Objects if x.InstanceGuid in ids]
    return None


def preview_objekter(ghdoc):
    """Alle komponenter og parametre, der kan vise geometri i Rhino."""
    return [o for o in ghdoc.Objects if isinstance(o, gh.Kernel.IGH_PreviewObject)]


def boks(objekter):
    b = Rhino.Geometry.BoundingBox.Empty
    for o in objekter:
        if isinstance(o, gh.Kernel.IGH_PreviewObject) and not o.Hidden:
            cb = o.ClippingBox
            if cb.IsValid:
                b.Union(cb)
    return b


def tag(view, ghdoc, rdoc, objekter, retning, sti, bredde, hoejde):
    vp = view.ActiveViewport
    gemt_kamera = Rhino.DocObjects.ViewportInfo(vp)
    gemt_skjult = {o.InstanceGuid: o.Hidden for o in preview_objekter(ghdoc)}
    egne = {o.InstanceGuid for o in objekter}
    skjulte_rhino = []
    try:
        # vis kun gruppens geometri
        for o in preview_objekter(ghdoc):
            if o.InstanceGuid not in egne:
                o.Hidden = True
        for ro in rdoc.Objects.GetObjectList(Rhino.DocObjects.ObjectEnumeratorSettings()):
            if ro.Visible and not ro.IsLocked:
                rdoc.Objects.Hide(ro.Id, True)
                skjulte_rhino.append(ro.Id)

        b = boks(objekter)
        if not b.IsValid:
            return "tom gruppe (ingen synlig geometri - er preview slået til?)"

        if retning == "top":
            vp.SetProjection(Rhino.Display.DefinedViewportProjection.Top, None, False)
        else:
            vp.ChangeToParallelProjection(True)
            d = RETNINGER.get(retning, RETNINGER["iso"])
            d.Unitize()
            midt = b.Center
            vp.SetCameraLocations(midt, midt - d * b.Diagonal.Length * 3)
            vp.CameraUp = Rhino.Geometry.Vector3d.ZAxis
        # luft rundt om: 6 % af diagonalen
        luft = b.Diagonal.Length * 0.06
        b.Inflate(luft)
        vp.ZoomBoundingBox(b)
        view.Redraw()

        cap = Rhino.Display.ViewCapture()
        cap.Width, cap.Height = bredde, hoejde
        cap.ScaleScreenItems = False
        cap.DrawAxes = False
        cap.DrawGrid = False
        cap.DrawGridAxes = False
        cap.TransparentBackground = True
        bmp = cap.CaptureToBitmap(view)
        if bmp is None:
            bmp = view.CaptureToBitmap(System.Drawing.Size(bredde, hoejde), False, False, False)
        bmp.Save(sti, System.Drawing.Imaging.ImageFormat.Png)
        return None
    finally:
        vp.SetViewProjection(gemt_kamera, True)
        for o in preview_objekter(ghdoc):
            if o.InstanceGuid in gemt_skjult:
                o.Hidden = gemt_skjult[o.InstanceGuid]
        for i in skjulte_rhino:
            rdoc.Objects.Show(i, True)
        rdoc.Views.Redraw()


linjer = []
if _koer and _mappe:
    os.makedirs(_mappe, exist_ok=True)
    ghdoc = ghenv.Component.OnPingDocument()
    rdoc = Rhino.RhinoDoc.ActiveDoc
    view = rdoc.Views.ActiveView
    bredde = int(_bredde_ or 3200)
    hoejde = int(_hoejde_ or 2000)
    for linje in _billeder or []:
        t = tolk(str(linje))
        if not t:
            continue
        fil, navn, retning = t
        objekter = gruppens_objekter(ghdoc, navn)
        if objekter is None:
            linjer.append("FEJL  %s: ingen gruppe med navnet '%s'" % (fil, navn))
            continue
        fejl = tag(view, ghdoc, rdoc, objekter, retning, os.path.join(_mappe, fil), bredde, hoejde)
        linjer.append(("FEJL  %s: %s" % (fil, fejl)) if fejl else ("%s  <- gruppe '%s', %s" % (fil, navn, retning)))
    linjer.append("Færdig: %s" % _mappe)
rapport = "\n".join(linjer) if linjer else "Sæt _mappe og tryk på _koer."
