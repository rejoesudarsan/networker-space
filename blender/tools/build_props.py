"""Loose props for the homepage beats: the objects that fall at dawn, the
three membership compositions, and the final empty chair.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python blender/tools/build_props.py

Writes site/public/models/props/props.gltf (+ .bin and textures/). Every
prop is one root node named after it (chair, armchair, table, book, petal,
slab) with its origin at the floor contact, sized in the site's units
(1 unit = 8 ft = 2.4384 m). Built in metres here and scaled on export.
The textures are the same CC0 teak and sandstone the house uses
(blender/assets, fetched by fetch_assets.py); without them the props fall
back to flat palette colours.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "assets", "textures")
OUT = os.path.join(os.path.dirname(ROOT), "site", "public", "models", "props")
UNIT_M = 2.4384

# Board 08 palette.
TEAK = "#805238"
SANDSTONE = "#B3A68B"
LINEN = "#D9D2C3"
PAGES = "#EEE9DD"
FABRIC = "#9C8E7E"
GULMOHAR = "#C96A3D"
CERAMIC = "#3A3632"
STEM = "#59634D"


def srgb(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


# ---------------------------------------------------------------- materials

def material(name, color, rough=0.6, tex=None, scale=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(color)
    bsdf.inputs["Roughness"].default_value = rough
    folder = os.path.join(TEX, tex) if tex else None
    if folder and os.path.exists(os.path.join(folder, "color.jpg")):
        uv = nt.nodes.new("ShaderNodeUVMap")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])

        def img(file, non_color=False):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = bpy.data.images.load(os.path.join(folder, file))
            if n.image.size[0] > 1024:
                n.image.scale(1024, 1024)       # web size, as export_site.py
            if non_color:
                n.image.colorspace_settings.name = "Non-Color"
            nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
            return n

        col = img("color.jpg")
        nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
        if os.path.exists(os.path.join(folder, "roughness.jpg")):
            nt.links.new(img("roughness.jpg", True).outputs["Color"], bsdf.inputs["Roughness"])
        if os.path.exists(os.path.join(folder, "normal.jpg")):
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(img("normal.jpg", True).outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT = {}


def mats():
    MAT["teak"] = material("Teak", TEAK, 0.55, "teak", 1.6)
    MAT["stone"] = material("Sandstone", SANDSTONE, 0.95, "sandstone", 0.8)
    MAT["linen"] = material("Linen", LINEN, 0.85)
    MAT["pages"] = material("Pages", PAGES, 0.9)
    MAT["fabric"] = material("Fabric", FABRIC, 0.95)
    MAT["petal"] = material("Petal", GULMOHAR, 0.7)
    MAT["ceramic"] = material("Ceramic", CERAMIC, 0.4)
    MAT["stem"] = material("Stem", STEM, 0.8)


# ---------------------------------------------------------------- building

def box_uv(bm, size=1.0):
    """Per-face planar UVs from the dominant normal, in metres / size."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = (co[a] / size, co[b] / size)


class Part:
    """Collects boxes and tubes into one bmesh per material."""

    def __init__(self):
        self.bms = {}

    def bm(self, key):
        if key not in self.bms:
            self.bms[key] = bmesh.new()
        return self.bms[key]

    def box(self, key, size, at, rot=(0, 0, 0)):
        b = bmesh.new()
        bmesh.ops.create_cube(b, size=1.0)
        m = Matrix.Translation(at) @ (Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")) @ Matrix.Diagonal((*size, 1))
        bmesh.ops.transform(b, matrix=m, verts=b.verts)
        self._add(key, b)

    def leg(self, key, a, c, r0, r1, seg=10):
        """A tapered round leg from a to c."""
        a, c = Vector(a), Vector(c)
        d = c - a
        b = bmesh.new()
        bmesh.ops.create_cone(b, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=d.length)
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        m = Matrix.Translation((a + c) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.transform(b, matrix=m, verts=b.verts)
        self._add(key, b)

    def _add(self, key, b):
        me = bpy.data.meshes.new("tmp")
        b.to_mesh(me)
        b.free()
        self.bm(key).from_mesh(me)
        bpy.data.meshes.remove(me)

    def add_bm(self, key, b):
        self._add(key, b)

    def object(self, name, bevel=0.0):
        me = bpy.data.meshes.new(name)
        big = bmesh.new()
        slots = []
        for key, b in self.bms.items():
            box_uv(b, 1.0)
            tmp = bpy.data.meshes.new("t")
            b.to_mesh(tmp)
            n0 = len(big.faces)
            big.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
            big.faces.ensure_lookup_table()
            for f in big.faces[n0:]:
                f.material_index = len(slots)
            slots.append(MAT[key])
            b.free()
        big.to_mesh(me)
        big.free()
        for m in slots:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        if bevel:
            mod = ob.modifiers.new("bevel", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = "ANGLE"
        for p in ob.data.polygons:
            p.use_smooth = False
        return ob


def bent_panel(p, key, w, h, t, bend, at, tilt):
    """A curved backrest: a row of slices bowed backwards by `bend` at the ends."""
    b = bmesh.new()
    n = 10
    rows = []
    for i in range(n + 1):
        u = i / n - 0.5
        x = u * w
        y = bend * (2 * u) ** 2
        rows.append([b.verts.new((x, y + dy, z)) for dy, z in ((0, 0), (t, 0), (t, h), (0, h))])
    for i in range(n):
        A, B = rows[i], rows[i + 1]
        for k in range(4):
            b.faces.new((A[k], B[k], B[(k + 1) % 4], A[(k + 1) % 4]))
    b.faces.new(list(reversed(rows[0])))
    b.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    m = Matrix.Translation(at) @ Matrix.Rotation(tilt, 4, "X")
    bmesh.ops.transform(b, matrix=m, verts=b.verts)
    p.add_bm(key, b)


def chair():
    """Teak dining chair with a bowed back, as in the CTA comp."""
    p = Part()
    sh = 0.45
    w, d = 0.44, 0.42
    p.box("teak", (w, d, 0.03), (0, 0, sh))
    for sx in (-1, 1):
        p.leg("teak", (sx * 0.19, -0.17, 0), (sx * 0.185, -0.165, sh - 0.01), 0.016, 0.019)
        # Back legs rise past the seat to carry the backrest, raked back.
        p.leg("teak", (sx * 0.19, 0.2, 0), (sx * 0.18, 0.17, sh), 0.016, 0.019)
        p.leg("teak", (sx * 0.18, 0.17, sh), (sx * 0.185, 0.24, 0.8), 0.019, 0.016)
        p.box("teak", (0.02, d - 0.06, 0.03), (sx * 0.19, 0.0, 0.16))
    p.box("teak", (w - 0.06, 0.02, 0.03), (0, -0.17, sh - 0.06))
    bent_panel(p, "teak", 0.42, 0.17, 0.022, 0.035, (0, 0.215, 0.6), -0.18)
    return p.object("chair", 0.004)


def armchair():
    """Low teak lounge chair with a fabric seat and back cushion."""
    p = Part()
    for sx in (-1, 1):
        p.leg("teak", (sx * 0.31, -0.3, 0), (sx * 0.31, -0.3, 0.58), 0.02, 0.022)
        p.leg("teak", (sx * 0.31, 0.3, 0), (sx * 0.31, 0.36, 0.42), 0.02, 0.022)
        p.box("teak", (0.05, 0.72, 0.035), (sx * 0.31, -0.02, 0.58))   # arm
        p.box("teak", (0.03, 0.62, 0.04), (sx * 0.31, 0.0, 0.25))      # side rail
        p.leg("teak", (sx * 0.31, 0.36, 0.42), (sx * 0.29, 0.46, 0.8), 0.022, 0.018)
    p.box("teak", (0.6, 0.03, 0.04), (0, -0.3, 0.25))
    p.box("teak", (0.6, 0.03, 0.04), (0, 0.3, 0.25))
    p.box("fabric", (0.56, 0.6, 0.12), (0, -0.02, 0.33))
    back = bmesh.new()
    bmesh.ops.create_cube(back, size=1.0)
    bmesh.ops.transform(back, matrix=Matrix.Translation((0, 0.38, 0.6)) @ Matrix.Rotation(-0.28, 4, "X") @ Matrix.Diagonal((0.54, 0.12, 0.42, 1)), verts=back.verts)
    p.add_bm("fabric", back)
    ob = p.object("armchair", 0.012)
    return ob


def table():
    """Round pedestal side table with a cup and a vase of twigs."""
    p = Part()
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=True, segments=40, radius1=0.3, radius2=0.3, depth=0.04)
    bmesh.ops.translate(b, vec=(0, 0, 0.52), verts=b.verts)
    p.add_bm("teak", b)
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=True, segments=28, radius1=0.12, radius2=0.1, depth=0.5)
    bmesh.ops.translate(b, vec=(0, 0, 0.25), verts=b.verts)
    p.add_bm("teak", b)
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=True, segments=20, radius1=0.035, radius2=0.03, depth=0.07)
    bmesh.ops.translate(b, vec=(-0.13, -0.05, 0.575), verts=b.verts)
    p.add_bm("ceramic", b)
    b = bmesh.new()
    bmesh.ops.create_uvsphere(b, u_segments=16, v_segments=10, radius=0.05)
    bmesh.ops.scale(b, vec=(1, 1, 1.3), verts=b.verts)
    bmesh.ops.translate(b, vec=(0.05, 0.03, 0.6), verts=b.verts)
    p.add_bm("ceramic", b)
    rnd = random.Random(4)
    for i in range(7):
        a = i / 7 * math.tau + rnd.uniform(-0.3, 0.3)
        top = (0.05 + math.cos(a) * rnd.uniform(0.05, 0.12), 0.03 + math.sin(a) * rnd.uniform(0.05, 0.12), 0.6 + rnd.uniform(0.18, 0.28))
        p.leg("stem", (0.05, 0.03, 0.64), top, 0.004, 0.002, 5)
        for k in range(4):
            u = 0.45 + k * 0.15
            c = Vector((0.05, 0.03, 0.64)).lerp(Vector(top), u)
            p.box("stem", (0.03, 0.012, 0.004), c, (0, rnd.uniform(-0.5, 0.5), a + rnd.uniform(-1, 1)))
    return p.object("table", 0.003)


def book():
    p = Part()
    w, d, h = 0.16, 0.235, 0.032
    p.box("linen", (w, d, 0.004), (0, 0, 0.002))
    p.box("linen", (w, d, 0.004), (0, 0, h - 0.002))
    p.box("linen", (0.006, d, h), (-w / 2 + 0.003, 0, h / 2))
    p.box("pages", (w - 0.012, d - 0.01, h - 0.008), (0.003, 0, h / 2))
    return p.object("book", 0.0015)


def petal():
    """A gulmohar petal: a cupped, frilled spoon of a shape."""
    b = bmesh.new()
    n, m = 14, 5
    grid = []
    for j in range(m + 1):
        v = j / m
        row = []
        for i in range(n + 1):
            u = i / n
            a = (u - 0.5) * math.pi * 1.4
            r = 0.022 * v * (1.0 + 0.12 * math.sin(u * 22))
            x = math.sin(a) * r
            y = 0.012 + math.cos(a) * r - 0.006
            z = 0.006 * (x / 0.022) ** 2 + 0.004 * v * v
            row.append(b.verts.new((x, y * 1.25, z)))
        grid.append(row)
    for j in range(m):
        for i in range(n):
            b.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.remove_doubles(b, verts=b.verts, dist=1e-5)
    p = Part()
    p.add_bm("petal", b)
    ob = p.object("petal")
    ob.modifiers.new("solid", "SOLIDIFY").thickness = 0.0012
    return ob


def slab(name, w, d, h, seed):
    """A rough-topped sandstone fragment, as on the membership comps."""
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.transform(b, matrix=Matrix.Translation((0, 0, -h / 2)) @ Matrix.Diagonal((w, d, h, 1)), verts=b.verts)
    bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=14, use_grid_fill=True)
    off = Vector((seed * 7.1, seed * 3.3, seed * 1.7))
    for v in b.verts:
        co = v.co
        top = co.z > -0.002
        side = max(abs(co.x) / (w / 2), abs(co.y) / (d / 2))
        n = noise.fractal(co * 6.0 + off, 0.6, 2.0, 4)
        if top:
            co.z += 0.012 * n - 0.02 * max(0.0, side - 0.85) / 0.15
        if side > 0.98:
            # Chipped edges, deeper toward the top.
            k = 0.02 * (1 + n) * (0.4 + 0.6 * (1 + co.z / h))
            co.x -= math.copysign(k, co.x) * (abs(co.x) / (w / 2) > 0.98)
            co.y -= math.copysign(k, co.y) * (abs(co.y) / (d / 2) > 0.98)
    p = Part()
    p.add_bm("stone", b)
    return p.object(name)


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    mats()
    props = [chair(), armchair(), table(), book(), petal(),
             slab("slab", 1.1, 0.9, 0.42, 1), slab("slab_wide", 1.35, 0.95, 0.42, 2)]
    for i, ob in enumerate(props):
        ob.location = (i * 2.0, 0, 0)
        # To site units, then y-up on export.
        ob.scale = (1 / UNIT_M,) * 3
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "props.gltf")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_yup=True, export_apply=True,
                              export_extras=True, export_texture_dir="textures", export_image_format="JPEG",
                              export_jpeg_quality=82, export_cameras=False, export_lights=False)
    print("[props] wrote %s (%d props)" % (path, len(props)))


main()
