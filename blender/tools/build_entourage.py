"""Build blender/entourage.blend: the people, cars and two-wheelers library.

  /snap/bin/blender -b --factory-startup --python blender/tools/build_entourage.py [-- --render]

Every source file is in blender/assets/ (credits in blender/ENTOURAGE.md).
Each source is imported, posed (rigged figures get a frame of their own Idle
or Walk clip baked in), joined into one mesh, turned so its front faces +X,
scaled to metres with its origin on the ground at the footprint centre, and
shaded flat. Its materials are then replaced by a small flat palette, so
assets from different authors read as one set beside the faceted house.

Variants (a white SUV, a silver one; a woman in a saree, one in a kurta...)
share the mesh and differ only in object-level materials. Each variant is
its own collection under People, Cars or Bikes, ready to be linked and
instanced by details/entourage.py. --render also writes a line-up of the
whole library to blender/renders/entourage-lineup.png.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
ASSETS = os.path.join(BL, "assets")
OUT = os.path.join(BL, "entourage.blend")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def log(msg):
    print("[entourage] " + msg)


# ---------------------------------------------------------------------------
# Palette: flat Principled materials, named by role and colour
# ---------------------------------------------------------------------------

def _lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


def mat(hex_colour, rough=0.75, metal=0.0, emit=0.0):
    name = "Ent %s" % hex_colour.upper()
    if rough < 0.3 or metal or emit:
        name += " r%.2f m%.1f e%.1f" % (rough, metal, emit)
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = _lin(hex_colour)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*rgb, 1)
    return m


# Shared vehicle roles
TYRE = ("#1C1C1C", 0.85)
BLACK = ("#262626", 0.6)
GLASS = ("#1F262B", 0.08)
CHROME = ("#A9ACAE", 0.3, 0.8)
HEAD = ("#F2E6C4", 0.3, 0.0, 0.6)
TAIL = ("#9E1E18", 0.4)
SEAT = ("#2A2522", 0.8)


def role_mat(spec):
    return mat(*spec) if isinstance(spec, tuple) else mat(spec)


# ---------------------------------------------------------------------------
# Import and normalise
# ---------------------------------------------------------------------------

def import_file(path):
    before = set(bpy.data.objects)
    if path.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def bake_pose(objs, action_name, frame):
    """Pose rigged figures on one frame of their own clip and bake it in."""
    arms = [o for o in objs if o.type == "ARMATURE"]
    for a in arms:
        act = next((x for x in bpy.data.actions if x.name == action_name), None)
        if act is None:
            raise RuntimeError("no action %s (have %s)" % (action_name, [x.name for x in bpy.data.actions]))
        a.animation_data_create()
        for t in list(a.animation_data.nla_tracks):
            a.animation_data.nla_tracks.remove(t)
        a.animation_data.action = act
        try:
            if act.slots:
                a.animation_data.action_slot = act.slots[0]
        except AttributeError:
            pass
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


# These rigs lie on their backs in the rest pose (their clips stand them up)
STAND_UP = Matrix.Rotation(math.radians(90), 4, "X")


def rest_pose(objs):
    for a in (o for o in objs if o.type == "ARMATURE"):
        if a.animation_data:
            a.animation_data.action = None
            for t in list(a.animation_data.nla_tracks):
                a.animation_data.nla_tracks.remove(t)
        for pb in a.pose.bones:
            pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def pose_bones(objs, ops):
    """ops: (bone name prefix, armature-space axis, degrees), applied in
    order, each a rotation about the bone's head. The rigs face -Y in
    armature space with +Z up; children follow their parents."""
    for a in (o for o in objs if o.type == "ARMATURE"):
        for prefix, axis, deg in ops:
            pb = next((b for b in a.pose.bones if b.name.startswith(prefix)), None)
            if pb is None:
                raise RuntimeError("no bone %s* in %s" % (prefix, [b.name for b in a.pose.bones]))
            m = pb.matrix.copy()
            h = m.translation.copy()
            pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ m
            bpy.context.view_layer.update()


def join(objs, name, drop, keep=False):
    """Evaluated meshes (pose baked) merged into one object in world space.
    drop(obj) -> True skips helper geometry (ground planes, backdrops)."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mats = []
    for o in objs:
        if o.type != "MESH" or drop(o):
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=False, depsgraph=dg)
        me.transform(o.matrix_world)
        remap = []
        for s in me.materials:
            if s not in mats:
                mats.append(s)
            remap.append(mats.index(s))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if not keep:
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    return me


def purge():
    """Drop everything the last import left behind (source meshes,
    materials, images, actions) so the next source's names stay clean."""
    for _ in range(4):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def normalise(me, yaw_deg, size, axis, k=None):
    """Turn (front to +X), scale so `axis` ('z' height or 'x' length)
    measures `size` metres, origin at the footprint centre on the ground."""
    vs = [v.co for v in me.vertices]
    if axis == "x" and (max(v.y for v in vs) - min(v.y for v in vs)) > (max(v.x for v in vs) - min(v.x for v in vs)):
        yaw_deg += 90                  # vehicles: length along X
    me.transform(Matrix.Rotation(math.radians(yaw_deg), 4, "Z"))
    vs = [v.co for v in me.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)])
    hi = Vector([max(v[i] for v in vs) for i in range(3)])
    if k is None:
        k = size / (hi - lo)["xyz".index(axis)]
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    me.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-c))
    for p in me.polygons:
        p.use_smooth = False
    try:
        me.free_normals_split()
    except AttributeError:
        pass
    if me.has_custom_normals:
        me.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(me.loops))
    return me


# ---------------------------------------------------------------------------
# Recolouring
# ---------------------------------------------------------------------------

def slot_roles(me, role_of):
    """Source material slot -> role name (string)."""
    return [role_of(m.name if m else "") for m in me.materials]


def assign(me, face_roles):
    """face_roles: list of role names per polygon. Rebuild slots as one per
    role, in a stable order, and return that order."""
    order = sorted(set(face_roles))
    me.materials.clear()
    for r in order:
        me.materials.append(None)
    for p, r in zip(me.polygons, face_roles):
        p.material_index = order.index(r)
    return order


def person_roles(me, src_roles, kurta=False):
    """Face roles for a figure standing on z=0 facing +X. Faces whose source
    role is 'band' are classified by height and position: shoes, bottom,
    top, hands, face, hair. Other source roles are kept."""
    h = max(v.co.z for v in me.vertices)
    out = []
    top_lo = 0.32 if kurta else 0.47
    for p in me.polygons:
        r = src_roles[p.material_index] if src_roles else "band"
        if r != "band":
            out.append(r)
            continue
        c = p.center
        z = c.z / h
        lat = abs(c.y) / h
        if z < 0.035:
            r = "shoes"
        elif z > 0.935 or (z > 0.86 and p.normal.x < -0.35):
            r = "hair"
        elif z > 0.835:
            r = "skin"
        elif lat > 0.085 and 0.33 < z < 0.53:
            r = "skin"                 # hands
        elif lat > 0.105 and 0.53 <= z < 0.70:
            r = "arm"                  # sleeves or bare forearms
        elif z >= top_lo:
            r = "top"
        else:
            r = "bottom"
        out.append(r)
    return out


def vehicle_roles(me, src_roles):
    return [src_roles[p.material_index] if src_roles else "body" for p in me.polygons]


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def is_helper(o):
    n = o.name.lower()
    return n.startswith(("plane", "icosphere")) or max(o.dimensions) > 40 * min(o.dimensions[:2] or [1]) and o.dimensions.z < 1e-3


def src(path):
    return os.path.join(ASSETS, path)


QCAR = {"Black": "black", "Grey": "tyre", "Headlights": "head", "TailLights": "tail",
        "Windows": "glass", "White": "body", "Blue": "body", "LightBlue": "body",
        "Material.007": "trim"}

SOURCES = {
    # Cars: Quaternius "Realistic Car Pack" (CC0). Length in metres.
    "SUV":    dict(file="quaternius-cars/SUV.obj", yaw=0, size=4.4, axis="x", roles=QCAR),
    "Hatch":  dict(file="quaternius-cars/NormalCar2.obj", yaw=0, size=3.85, axis="x", roles=QCAR),
    "Sedan":  dict(file="quaternius-cars/NormalCar1.obj", yaw=0, size=4.3, axis="x", roles=QCAR),
    # Two-wheelers and the auto (Sketchfab, CC-BY, via Objaverse)
    "Scooter": dict(file="sketchfab/scooter-gulli-bulli_noorulhasan.glb", yaw=180, size=1.8, axis="x",
                    roles={"Material.001": "body", "Material.002": "black", "Material.003": "trim",
                           "front_light": "head", "bake_light": "head"}),
    "Vespa":   dict(file="sketchfab/scooter-summer_steryo.glb", yaw=0, size=1.75, axis="x",
                    roles={"lambert3": "tyre", "lambert4": "body", "lambert5": "black", "lambert6": "trim",
                           "lambert7": "tail", "test1Default1": "head", "lambert1": "trim"}),
    "Motorbike": dict(file="sketchfab/motorcycle_matisosanimation.glb", yaw=0, size=2.0, axis="x",
                      roles={"MOTOCAP_azul": "body", "MOTOCAP_freno": "tail", "MOTOCAP_luz": "trim",
                             "MOTOCAP_metal": "trim", "MOTOCAP_negro": "black"}),
    "Auto":    dict(file="sketchfab/auto-rikshaw_sagarkalbande.glb", yaw=0, size=2.65, axis="x",
                    roles={"Yellow": "body", "Point.001": "canopy", "Black": "black", "Glass": "glass",
                           "material": "black", "Seat": "seat", "numberplate": "plate",
                           "Spot": "plate", "BlackVelvet.003": "tyre", "BlackVelvet.004": "tyre",
                           "Steel": "trim", "Steel.003": "trim", "Point": "trim"}, default="black"),
    # People (Sketchfab, CC-BY). Height in metres.
    "ManPhone":  dict(file="sketchfab/man-phone-walking_roh3d.glb", yaw=90, size=1.72, axis="z", person=True,
                      roles={"02_-_Default": "hair", "03_-_Default": "skin", "04_-_Default": "top",
                             "05_-_Default": "top2", "06_-_Default": "bottom", "07_-_Default": "bag"}),
    "WomanBags": dict(file="sketchfab/business-girl_roh3d.glb", yaw=90, size=1.6, axis="z", person=True,
                      roles={"wire_028089177": "band", "wire_225198087": "hair", "wire_008008136": "shoes",
                             "wire_061135006": "shoes"}, default="bag"),
    "ManWalk":   dict(file="sketchfab/man_razvansavescu.glb", yaw=90, size=1.72, axis="z", person=True,
                      pose=("Walk", 6), roles={}, default="band"),
    "ManIdle":   dict(file="sketchfab/man_razvansavescu.glb", yaw=90, size=1.70, axis="z", person=True,
                      pose=("Idle", 1), roles={}, default="band"),
    "WomanIdle": dict(file="sketchfab/woman_razvansavescu.glb", yaw=90, size=1.58, axis="z", person=True,
                      pose=("Armature|idle", 1), roles={"hair": "hair"}, default="band"),
    "WomanWalk": dict(file="sketchfab/girl_razvansavescu.glb", yaw=90, size=1.58, axis="z", person=True,
                      pose=("walk", 4), roles={"hair": "hair"}, default="band"),
}
# Seated and riding figures: the rest pose with legs and arms turned
# (armature space: -Y is forward, so -X degrees about X swings a limb forward)
ARMS_DOWN = [("L.upperArm", "Y", 32), ("R.upperArm", "Y", -32)]
SIT = [("L.upperLeg", "X", -88), ("R.upperLeg", "X", -88),
       ("L.lowerLeg", "X", 88), ("R.lowerLeg", "X", 88)] + ARMS_DOWN + [
       ("L.lowerArm", "X", -62), ("R.lowerArm", "X", -62)]
RIDE = [("L.upperLeg", "X", -78), ("R.upperLeg", "X", -78),
        ("L.lowerLeg", "X", 72), ("R.lowerLeg", "X", 72)] + ARMS_DOWN + [
        ("L.upperArm", "X", -50), ("R.upperArm", "X", -50),
        ("L.lowerArm", "X", -25), ("R.lowerArm", "X", -25),
        ("lowerBody", "X", -8)]
for key, f, size in (("Man", "man_razvansavescu.glb", 1.70), ("Woman", "woman_razvansavescu.glb", 1.58)):
    for pose, ops in (("Sit", SIT), ("Ride", RIDE)):
        SOURCES[key + pose] = dict(file="sketchfab/" + f, yaw=90, size=size, axis="z", person=True,
                                   bones=ops, roles={"hair": "hair"}, default="band")


def build_source(key, s, kurta=False):
    objs = import_file(src(s["file"]))
    only = s.get("only")
    drop = lambda o: is_helper(o) or o.type != "MESH" or (only is not None and o.name != only)
    roles = s["roles"]
    default = s.get("default", "trim")
    if "pose" in s:
        bake_pose(objs, *s["pose"])
    k = None
    rest_roles = None
    if "bones" in s:
        # Scale and dress the standing figure, then sit it down: the height
        # bands only make sense standing, and posing keeps the face order.
        rest_pose(objs)
        rest = join(objs, "rest", drop, keep=True)
        rest.transform(STAND_UP)
        k = s["size"] / mesh_dims(rest)[2]
        normalise(rest, s["yaw"], s["size"], s["axis"], k)
        rest_roles = person_roles(rest, slot_roles(rest, lambda n: roles.get(n, default)), kurta)
        bpy.data.meshes.remove(rest)
        pose_bones(objs, s["bones"])
    me = join(objs, "Ent." + key + (".Kurta" if kurta else ""), drop)
    if "bones" in s:
        me.transform(STAND_UP)
    for o in [o for o in bpy.data.objects if o.type in {"LIGHT", "CAMERA", "EMPTY", "ARMATURE"}]:
        bpy.data.objects.remove(o, do_unlink=True)
    me.use_fake_user = True            # survive the purge below
    purge()
    normalise(me, s["yaw"], s["size"], s["axis"], k)
    src_roles = slot_roles(me, lambda n: roles.get(n, default))
    if rest_roles is not None:
        face_roles = rest_roles
    elif s.get("person"):
        face_roles = person_roles(me, src_roles, kurta)
    else:
        face_roles = vehicle_roles(me, src_roles)
    order = assign(me, face_roles)
    log("%s: %d faces, roles %s, size %s" % (key, len(me.polygons), order,
                                            tuple(round(v, 2) for v in mesh_dims(me))))
    return me, order


def mesh_dims(me):
    vs = [v.co for v in me.vertices]
    return [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]


# ---------------------------------------------------------------------------
# Variants: (collection name, source key, {role: colour spec})
# ---------------------------------------------------------------------------

def car(body):
    return {"body": body, "trim": ("#3A3D40", 0.5), "black": BLACK, "tyre": TYRE,
            "glass": GLASS, "head": HEAD, "tail": TAIL}


def bike(body, trim="#3B3E41"):
    return {"body": body, "trim": trim, "black": BLACK, "tyre": TYRE, "head": HEAD,
            "tail": TAIL, "glass": GLASS, "seat": SEAT}


SKIN = ["#8D5A3B", "#A8704A", "#6E4630", "#7B4F35", "#5A3A28", "#C08A62"]
HAIR = "#16120F"


def dress(top, bottom, skin, shoes="#3A2E26", hair=HAIR, arm=None, **extra):
    d = {"top": top, "bottom": bottom, "skin": skin, "shoes": shoes, "hair": hair,
         "arm": arm or top, "top2": top, "bag": "#6B4A2E"}
    d.update(extra)
    return d


VARIANTS = {
    "Cars": [
        ("Car.SUV.White",    "SUV",   car(("#E9E8E3", 0.35))),
        ("Car.SUV.Silver",   "SUV",   car(("#A7AAAD", 0.3, 0.4))),
        ("Car.Hatch.White",  "Hatch", car(("#ECEBE6", 0.35))),
        ("Car.Hatch.Silver", "Hatch", car(("#B3B5B6", 0.3, 0.4))),
        ("Car.Hatch.Red",    "Hatch", car(("#8E1F1B", 0.35))),
        ("Car.Sedan.Grey",   "Sedan", car(("#5E6366", 0.3, 0.3))),
    ],
    "Bikes": [
        ("Bike.Scooter.Grey",  "Scooter", bike(("#8C9094", 0.35, 0.3))),
        ("Bike.Scooter.Blue",  "Scooter", bike(("#2E4B73", 0.35))),
        ("Bike.Scooter.White", "Scooter", bike(("#E6E4DE", 0.35))),
        ("Bike.Vespa.Mint",    "Vespa",   bike(("#9CC8B5", 0.35), trim="#C9CCCE")),
        ("Bike.Motorbike.Black", "Motorbike", bike(("#1E1F22", 0.35), trim="#8E9195")),
        ("Bike.Motorbike.Red",   "Motorbike", bike(("#8B1D1A", 0.35), trim="#8E9195")),
        ("Bike.Auto", "Auto", {"body": ("#1F6B3A", 0.45), "canopy": ("#E3B21E", 0.6), "black": BLACK,
                               "tyre": TYRE, "glass": GLASS, "seat": SEAT, "trim": ("#3A3D40", 0.5),
                               "plate": "#E8D33A"}),
    ],
    "People": [
        ("Person.ManPhone",        "ManPhone",  dress("#E7DCC8", "#2A2F38", SKIN[1], top2="#3D4F6B")),
        ("Person.WomanBags.Kurta", "WomanBags", dress("#B5562F", "#E9E3D6", SKIN[0], bag="#C9B48F")),
        ("Person.ManWalk.Shirt",   "ManWalk",   dress("#6B7F8E", "#3B4A63", SKIN[2], arm=SKIN[2])),
        ("Person.ManWalk.Kurta",   "ManWalk",   dress("#F1ECE2", "#F1ECE2", SKIN[3], shoes="#6B4A2E")),
        ("Person.ManIdle.Tee",     "ManIdle",   dress("#2F5B55", "#4F6280", SKIN[0], arm=SKIN[0], shoes="#F2EFE8")),
        ("Person.WomanIdle.Churidar", "WomanIdle", dress("#6D2F4A", "#ECE6DA", SKIN[1], arm=SKIN[1], shoes="#8A5232")),
        ("Person.WomanWalk.Kurta", "WomanWalk", dress("#C47B2B", "#D8CFBD", SKIN[4], arm=SKIN[4], shoes="#8A5232")),
        ("Person.ManPhone.Blue",   "ManPhone",  dress("#C9B48F", "#3B4A63", SKIN[3], top2="#6B7F8E")),
        ("Person.WomanWalk.Green", "WomanWalk", dress("#2F5B55", "#E7DCC8", SKIN[1], arm=SKIN[1], shoes="#3A2E26")),
        ("Person.ManIdle.Shirt",   "ManIdle",   dress("#D9D3C7", "#5B4636", SKIN[4])),
        ("Person.ManSit",          "ManSit",    dress("#7A3F1F", "#E9E3D6", SKIN[2], arm=SKIN[2])),
        ("Person.WomanSit",        "WomanSit",  dress("#3D4F6B", "#D8CFBD", SKIN[0], arm=SKIN[0])),
        ("Person.ManRide",         "ManRide",   dress("#8C6E55", "#2A2F38", SKIN[1])),
        ("Person.WomanRide",       "WomanRide", dress("#A34A3A", "#E9E3D6", SKIN[5], arm=SKIN[5])),
        ("Person.ManRide.Khaki",   "ManRide",   dress("#A88F5E", "#A88F5E", SKIN[2], arm=SKIN[2])),   # auto driver
    ],
}
KURTA = {"Person.WomanBags.Kurta", "Person.ManWalk.Kurta", "Person.WomanWalk.Kurta", "Person.WomanIdle.Churidar",
         "Person.WomanWalk.Green", "Person.WomanSit", "Person.WomanRide"}

# Ridden two-wheelers: (collection, bike variant, rider variant, (x, z)),
# the rider's offset in metres from the bike's origin, fitted by eye with
# tools/entourage_closeup.py.
RIDDEN = [
    ("Bike.Scooter.Blue.Ridden",    "Bike.Scooter.Blue",    "Person.WomanRide", (0.08, 0.16)),
    ("Bike.Scooter.Grey.Ridden",    "Bike.Scooter.Grey",    "Person.ManRide",   (0.02, 0.16)),
    ("Bike.Motorbike.Black.Ridden", "Bike.Motorbike.Black", "Person.ManRide",   (0.42, 0.27)),
    ("Bike.Auto.Driven",            "Bike.Auto",            "Person.ManRide.Khaki", (0.40, 0.04)),
]


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    root = scene.collection
    groups = {}
    for g in ("People", "Cars", "Bikes"):
        groups[g] = bpy.data.collections.new(g)
        root.children.link(groups[g])

    used = sorted({(k, c in KURTA) for vs in VARIANTS.values() for c, k, _ in vs})
    meshes = {}
    for key, kurta in used:
        meshes[key, kurta] = build_source(key, SOURCES[key], kurta)

    for g, vs in VARIANTS.items():
        for cname, key, colours in vs:
            me, order = meshes[key, cname in KURTA]
            coll = bpy.data.collections.new(cname)
            groups[g].children.link(coll)
            ob = bpy.data.objects.new(cname, me)
            coll.objects.link(ob)
            for i, r in enumerate(order):
                ob.material_slots[i].link = "OBJECT"
                spec = colours.get(r)
                if spec is None:
                    log("WARNING %s: no colour for role %s" % (cname, r))
                    spec = "#FF00FF"
                ob.material_slots[i].material = role_mat(spec)

    def copy_into(coll, name, loc):
        src_ob = bpy.data.collections[name].objects[0]
        ob = bpy.data.objects.new(name + ".Copy", src_ob.data)
        coll.objects.link(ob)
        for a, b in zip(ob.material_slots, src_ob.material_slots):
            a.link = "OBJECT"
            a.material = b.material
        ob.location = loc
        return ob

    for cname, bike_name, rider_name, (x, z) in RIDDEN:
        coll = bpy.data.collections.new(cname)
        groups["Bikes"].children.link(coll)
        copy_into(coll, bike_name, (0, 0, 0))
        copy_into(coll, rider_name, (x, 0, z))
    for me in bpy.data.meshes:
        me.use_fake_user = False
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log("saved %s (%d KB)" % (OUT, os.path.getsize(OUT) // 1024))
    return groups


def render_lineup(groups):
    """All variants in rows (people, bikes, cars), lit like the house."""
    scene = bpy.context.scene
    y = 0.0
    insts = {}
    for g, gap in (("People", 0.9), ("Bikes", 2.4), ("Cars", 4.0)):
        bpy.context.view_layer.layer_collection.children[g].exclude = True
        x = 0.0
        for coll in groups[g].children:
            ob = bpy.data.objects.new("I." + coll.name, None)
            ob.instance_type = "COLLECTION"
            ob.instance_collection = coll
            scene.collection.objects.link(ob)
            insts.setdefault(g, []).append(ob)
            ob.location = (x, y, 0)
            ob.rotation_euler = (0, 0, math.radians(-35))
            x += gap
        y += 3.0 if g == "People" else 4.5
    world = bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.6, 0.62, 0.66, 1)
    bg.inputs[1].default_value = 0.8
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.collection.objects.link(sun)
    me = bpy.data.meshes.new("ground")
    me.from_pydata([(-20, -20, 0), (60, -20, 0), (60, 40, 0), (-20, 40, 0)], [], [(0, 1, 2, 3)])
    gr = bpy.data.objects.new("ground", me)
    me.materials.append(mat("#8A8580", 0.9))
    scene.collection.objects.link(gr)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    cam.location = (8.0, -11.0, 9.5)
    cam.rotation_euler = (math.radians(57), 0, 0)
    cam.data.lens = 30
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    os.makedirs(os.path.join(BL, "renders"), exist_ok=True)
    scene.render.filepath = os.path.join(BL, "renders", "entourage-lineup.png")
    bpy.ops.render.render(write_still=True)
    log("lineup %s" % scene.render.filepath)
    # People close-up, from the front-left (they should all face +X, i.e. right)
    for ob in insts["People"]:
        ob.rotation_euler = (0, 0, 0)
    n = len(insts["People"])
    cam.location = ((n - 1) * 0.45, -12.5, 1.3)
    cam.rotation_euler = (math.radians(88), 0, 0)
    cam.data.lens = 32
    scene.render.resolution_x, scene.render.resolution_y = 1600, 700
    scene.render.filepath = os.path.join(BL, "renders", "entourage-people.png")
    bpy.ops.render.render(write_still=True)


groups = build()
if "--render" in ARGS:
    render_lineup(groups)
