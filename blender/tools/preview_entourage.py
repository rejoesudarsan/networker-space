"""Fast Workbench check of details/entourage.py on the last saved scene.

  /snap/bin/blender -b blender/space-house.blend --python blender/tools/preview_entourage.py [-- <view> ...]

Runs the entourage module (and swaps the garage car) on the saved
space-house.blend without saving, then renders Workbench frames to
blender/renders/preview-entourage-<view>.png. Views: top (the street and
plot from above), garage (the basement parking from above), plan:<floor>,<cx>,<cz>,<half>
(any floor from above, in its Three.js units), and the scene's cameras
street, angle, court2, entrance, terrace. Default: all but plan."""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
views = args or ["top", "garage", "street", "angle", "court2", "entrance", "terrace"]

src = open(os.path.join(BL, "build_house.py")).read().replace("\nmain()\n", "\n")
ns = {"__file__": os.path.join(BL, "build_house.py"), "__name__": "build_house_lib"}
exec(compile(src, "build_house.py", "exec"), ns)
sys.path.insert(0, BL)
scene = bpy.context.scene
ctx = dict(
    scene=scene, mats={m.name: m for m in bpy.data.materials},
    empties={k: bpy.data.objects["Floor.%s" % k] for k in ns["FLOOR_ORDER"]},
    colls={k: bpy.data.collections[ns["COLLECTION_FOR"][k]] for k in ns["FLOOR_ORDER"]},
    site=bpy.data.collections["Site"], house=bpy.data.collections["House"],
    helpers={k: ns[k] for k in ("add_box", "add_slab", "get_collection", "set_parent",
                                "three_rect_to_blender", "new_material", "link_only", "info", "warn")},
    constants={k: ns[k] for k in ("UNIT_M", "SLAB_T", "STOREY", "WALL_H", "FLOORS", "PARAPET_H",
                                  "PARAPET_T", "TERRACE_X1", "SLAB_VOIDS")},
)

import importlib
from details import _entourage, entourage, garage_fitout
if not bpy.data.objects.get("Entourage.basement.Car"):
    for o in bpy.data.objects:
        if o.name.startswith("basement.Car."):
            o.hide_render = True
    c = garage_fitout.CAR
    _entourage.place(ctx, "Car.SUV.White", "basement", c["x"], c["z"], rot=-90,
                     coll=ctx["colls"]["basement"], label="basement.Car")
if not any(o.name.startswith("Entourage.Person") for o in bpy.data.objects):
    entourage.build(ctx)

sc = scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "MATERIAL"
sh.show_shadows = True
for o in bpy.data.objects:
    if "fog" in o.name.lower():
        o.hide_render = True


def render(name, cam, res=(1200, 800), hide=()):
    hidden = []
    for c in hide:
        coll = bpy.data.collections.get(c)
        if coll and not coll.hide_render:
            coll.hide_render = True
            hidden.append(coll)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.filepath = os.path.join(BL, "renders", "preview-entourage-%s.png" % name)
    bpy.ops.render.render(write_still=True)
    for coll in hidden:
        coll.hide_render = False
    print("[preview_entourage] wrote", sc.render.filepath)


def top_cam(frame, cx, cz, half):
    e = bpy.data.objects["Floor.%s" % frame] if frame != "street" else bpy.data.objects["Site.Units"]
    p = e.matrix_world @ Vector((cx, -cz, 0))
    cam = bpy.data.objects.new("T." + frame, bpy.data.cameras.new("T"))
    sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = half * 2 * ns["UNIT_M"]
    cam.data.clip_end = 200
    cam.location = (p.x, p.y, p.z + 40)
    return cam


CAMS = {"street": "Camera.Street", "angle": "Camera.Angle", "court2": "Camera.Court2",
        "entrance": "Camera.Entrance", "terrace": "Camera.Terrace"}
for v in views:
    if v == "top":
        render("top", top_cam("street", 0.0, 4.5, 12.0), (1400, 1400), hide=("Roof",))
    elif v == "garage":
        render("garage", top_cam("basement", -1.1, -1.3, 2.6), (900, 900),
               hide=("Ground", "First", "Second", "Roof"))
    elif v.startswith("plan:"):
        # plan:<floor>,<cx>,<cz>,<half>: that floor from above, floors over it hidden
        f, cx, cz, half = v[5:].split(",")
        above = ns["FLOOR_ORDER"][ns["FLOOR_ORDER"].index(f) + 1:]
        render("plan-" + f, top_cam(f, float(cx), float(cz), float(half)), (900, 900),
               hide=[ns["COLLECTION_FOR"][k] for k in above] + ["Roof"])
    elif v in CAMS:
        render(v, bpy.data.objects[CAMS[v]])
