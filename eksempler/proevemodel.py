"""Laver en opdigtet Honeybee-model til at afprøve tegningerne: en trekantbygning med en lav tilbygning.

    python eksempler/proevemodel.py <udmappe>
"""
import os
import sys

from ladybug_geometry.geometry3d import Point3D, Face3D, Polyface3D
from honeybee.model import Model
from honeybee.room import Room
from honeybee.boundarycondition import boundary_conditions as bcs

ud = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(ud, exist_ok=True)

# trekantbygning: 12 m lang, 8,7 m bred, 7 m høj, langs x
L, B, H = 12.0, 8.7, 7.0
v = [Point3D(0, 0, 0), Point3D(L, 0, 0), Point3D(L, B, 0), Point3D(0, B, 0),
     Point3D(0, B / 2, H), Point3D(L, B / 2, H)]
flader = [
    Face3D([v[0], v[3], v[2], v[1]]),          # gulv
    Face3D([v[0], v[1], v[5], v[4]]),          # skråtag syd
    Face3D([v[2], v[3], v[4], v[5]]),          # skråtag nord
    Face3D([v[1], v[2], v[5]]),                # gavl øst
    Face3D([v[3], v[0], v[4]]),                # gavl vest
]
hus = Room.from_polyface3d("Residence_1", Polyface3D.from_faces(flader, 0.01))
hus.display_name = "Stue og køkken"
for f in hus.faces:
    n = f.normal
    if abs(n.x) > 0.9:                       # gavle: stort glasparti
        f.apertures_by_ratio(0.45, 0.01)
    elif n.z > 0 and n.y < 0:                # skråtaget mod syd: ovenlys
        f.apertures_by_ratio(0.12, 0.01)

# tilbygning: to små rum mod øst
bad = Room.from_box("Residence_2", 2.4, 2.5, 2.8, origin=Point3D(L, 0.6, 0))
bad.display_name = "Bad"
vaer = Room.from_box("Residence_3", 3.4, 2.8, 2.8, origin=Point3D(L, 3.1, 0))
vaer.display_name = "Værelse"
for r in (bad, vaer):
    for f in r.faces:
        if f.type.name == "Wall" and f.normal.x > 0.9:
            f.apertures_by_ratio(0.3 if r is vaer else 0.12, 0.01)

model = Model("Proevemodel", rooms=[hus, bad, vaer], units="Meters", tolerance=0.01, angle_tolerance=1)
model.solve_adjacency() if hasattr(model, "solve_adjacency") else Room.solve_adjacency(model.rooms, 0.01)
sti = model.to_hbjson("model", ud)
print(sti)
