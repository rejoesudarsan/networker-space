"""Shared furniture builder for the club fit-out modules (café, event space,
game and quiet rooms) and the site's loose props.

Pieces are modelled in metres around their own floor-contact origin, then
placed with plan coordinates in the floor's Three.js frame (x east, z toward
the street, units of 8 ft), so a module reads like the plan:

    kit = Kit(ctx, "ground", "ground.Cafe")
    chair(kit, 1.2, 2.4, rot=math.pi)        # at plan x 1.2, z 2.4, facing north
    kit.done()                               # one mesh object per material

All geometry for one Kit lands in a handful of objects (one per material),
parented to the Floor.<name> empty so they ride with the cutaway and bake
as part of that floor. Materials come from build_materials() where one fits
(Teak, Lime White, Sandstone, Terracotta, Charcoal Steel, Terrazzo, Foliage);
the rest are flat palette materials made once here.

Facing: rot 0 means the piece faces +z in plan (toward the street); a chair
with rot 0 has its back to the north and its sitter looking at the street.
To face east use rot pi/2, west -pi/2, north pi.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

M = 1 / 2.4384            # metres -> plan units

# Flat palette materials for soft goods and fittings (board 08 family).
FLAT = {
    "Cushion": ("#B5653F", 0.95),        # muted gulmohar
    "Olive Velvet": ("#6A6A3C", 0.9),
    "Linen": ("#D8D0C0", 0.95),
    "Rattan": ("#B48A57", 0.8),
    "Brass": ("#9C7A3C", 0.35),
    "Ceramic White": ("#ECE8DF", 0.35),
    "Ceramic Dark": ("#3A3632", 0.4),
    "Chalkboard": ("#2F3331", 0.85),
    "Chalk": ("#E6E2D6", 0.9),
    "Screen": ("#F1EFEA", 0.6),
    "Felt Green": ("#3F5A3E", 0.95),
    "Book Spines": ("#8C6A4E", 0.8),
    "Leaf": ("#4E6B35", 0.75),
    "Pot": ("#A9643F", 0.85),
    "Lamp Glow": ("#FFD9A8", 0.5),
    "Black Steel": ("#232524", 0.45),
    "Gulmohar Paint": ("#C96A3D", 0.9),
    "Bark": ("#5A4636", 0.9),
}


def _hex(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(ctx, name):
    if name in ctx["mats"]:
        return ctx["mats"][name]
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    hx, rough = FLAT[name]
    mat, nt, bsdf = ctx["helpers"]["new_material"](name)
    lin = _hex(hx)
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if name == "Lamp Glow":
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = (*lin, 1.0)
                break
        bsdf.inputs["Emission Strength"].default_value = 4.0
    mat.diffuse_color = (*lin, 1.0)
    return mat


_DIRS = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}   # blender xy


def wall(ctx, floor, x, z, side, h=1.2, gap=0.003):
    """Plan coordinate of the nearest wall face from (x, z) toward `side`
    (z for north/south, x for east/west), found by a ray at height h metres,
    pulled `gap` units back into the room. Use it to hang things on walls
    instead of trusting measured numbers."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = ctx["empties"][floor]
    U = ctx["constants"]["UNIT_M"]
    o = e.matrix_world @ Vector((x, -z, h / U))
    dx, dy = _DIRS[side]
    hit, loc, *_ = ctx["scene"].ray_cast(dg, o, Vector((dx, dy, 0)), distance=20.0)
    if not hit:
        ctx["helpers"]["warn"]("wall(): no %s wall from (%.2f, %.2f) on %s" % (side, x, z, floor))
        return (x + dx * 0.5) if dx else (z - dy * 0.5)
    p = e.matrix_world.inverted() @ loc
    if dx:
        return p.x - dx * gap
    return -p.y + dy * gap


class Kit:
    """Geometry for one fit-out group, bucketed by material."""

    def __init__(self, ctx, floor, name):
        self.ctx = ctx
        self.floor = floor
        self.name = name
        self.parts = {}
        self.place = Matrix.Identity(4)
        self.base = 0.0085           # top of the 2 cm floor finish

    # -- placement: plan (x, z, rot) -> blender floor-local, metres -> units
    def at(self, x, z, rot=0.0, y=0.0):
        self.place = Matrix.Translation((x, -z, self.base + y)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((M, M, M, 1))
        return self

    def _bm(self, mat):
        if mat not in self.parts:
            self.parts[mat] = bmesh.new()
        return self.parts[mat]

    def _put(self, mat, geom_verts, local):
        bm = self._bm(mat)
        bmesh.ops.transform(bm, matrix=self.place @ local, verts=geom_verts)

    # -- primitives, in metres, piece-local: x right, y back (away from the
    #    sitter, i.e. plan -z), z up.
    def box(self, mat, cx, cy, cz, sx, sy, sz, rz=0.0, rx=0.0):
        bm = self._bm(mat)
        g = bmesh.ops.create_cube(bm, size=1.0)
        local = (Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X")
                 @ Matrix.Diagonal((sx, sy, sz, 1)))
        self._put(mat, g["verts"], local)

    def cyl(self, mat, cx, cy, z0, z1, r0, r1=None, seg=12, a=None, b=None):
        """A (tapered) cylinder from z0 to z1, or along the segment a -> b."""
        bm = self._bm(mat)
        r1 = r0 if r1 is None else r1
        if a is not None:
            a, b = Vector(a), Vector(b)
            d = b - a
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=d.length)
            q = Vector((0, 0, 1)).rotation_difference(d.normalized())
            local = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
        else:
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=z1 - z0)
            local = Matrix.Translation((cx, cy, (z0 + z1) / 2))
        self._put(mat, g["verts"], local)

    def ball(self, mat, cx, cy, cz, r, sz=1.0, sub=1):
        bm = self._bm(mat)
        g = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        self._put(mat, g["verts"], Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((1, 1, sz, 1)))

    def arc_box(self, mat, cx, cy, r_in, r_out, a0, a1, z0, z1, seg=16):
        """A curved slab: the ring sector between radii r_in and r_out."""
        bm = self._bm(mat)
        ring = []
        for i in range(seg + 1):
            a = a0 + (a1 - a0) * i / seg
            ca, sa = math.cos(a), math.sin(a)
            ring.append([bm.verts.new((cx + ca * r, cy + sa * r, z)) for r, z in
                         ((r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1))])
        new = [v for row in ring for v in row]
        for i in range(seg):
            A, B = ring[i], ring[i + 1]
            for k in range(4):
                bm.faces.new((A[k], A[(k + 1) % 4], B[(k + 1) % 4], B[k]))
        bm.faces.new(list(reversed(ring[0])))
        bm.faces.new(ring[-1])
        self._put(mat, new, Matrix.Identity(4))

    def done(self):
        ctx = self.ctx
        coll = ctx["colls"][self.floor]
        empty = ctx["empties"][self.floor]
        out = []
        for mat_name, bm in self.parts.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            nm = "%s.%s" % (self.name, mat_name.replace(" ", ""))
            me = bpy.data.meshes.new(nm)
            bm.to_mesh(me)
            bm.free()
            for p in me.polygons:
                p.use_smooth = False
            me.materials.append(material(ctx, mat_name))
            ob = bpy.data.objects.new(nm, me)
            coll.objects.link(ob)
            ob.parent = empty
            ob.matrix_parent_inverse = Matrix.Identity(4)
            out.append(ob)
        self.parts = {}
        return out


# ---------------------------------------------------------------- seating

def chair(kit, x, z, rot=0.0, mat="Teak"):
    """Teak dining chair with a bowed back rail (the site's CTA chair)."""
    kit.at(x, z, rot)
    sh = 0.45
    kit.box(mat, 0, 0, sh, 0.44, 0.42, 0.03)
    for sx in (-1, 1):
        kit.cyl(mat, 0, 0, 0, 0, 0.016, 0.019, 8, a=(sx * 0.19, -0.17, 0), b=(sx * 0.185, -0.165, sh - 0.01))
        kit.cyl(mat, 0, 0, 0, 0, 0.016, 0.019, 8, a=(sx * 0.19, 0.2, 0), b=(sx * 0.18, 0.17, sh))
        kit.cyl(mat, 0, 0, 0, 0, 0.019, 0.016, 8, a=(sx * 0.18, 0.17, sh), b=(sx * 0.185, 0.24, 0.8))
        kit.box(mat, sx * 0.19, 0, 0.16, 0.02, 0.36, 0.03)
    kit.arc_box(mat, 0, -0.1, 0.33, 0.352, math.pi / 2 - 0.62, math.pi / 2 + 0.62, 0.62, 0.79, 10)


def stool(kit, x, z, h=0.46, mat="Teak"):
    kit.at(x, z)
    kit.cyl(mat, 0, 0, h - 0.04, h, 0.17, 0.17, 20)
    for k in range(3):
        a = k * math.tau / 3 + 0.3
        kit.cyl(mat, 0, 0, 0, 0, 0.016, 0.02, 8, a=(math.cos(a) * 0.16, math.sin(a) * 0.16, 0),
                b=(math.cos(a) * 0.1, math.sin(a) * 0.1, h - 0.04))
    kit.cyl(mat, 0, 0, 0.22, 0.24, 0.13, 0.13, 16)


def armchair(kit, x, z, rot=0.0, fabric="Olive Velvet"):
    """Low teak lounge chair with a velvet seat and back."""
    kit.at(x, z, rot)
    for sx in (-1, 1):
        kit.cyl("Teak", 0, 0, 0, 0, 0.02, 0.022, 8, a=(sx * 0.31, -0.3, 0), b=(sx * 0.31, -0.3, 0.58))
        kit.cyl("Teak", 0, 0, 0, 0, 0.02, 0.022, 8, a=(sx * 0.31, 0.3, 0), b=(sx * 0.31, 0.36, 0.42))
        kit.box("Teak", sx * 0.31, 0.02, 0.58, 0.05, 0.72, 0.035)
        kit.box("Teak", sx * 0.31, 0, 0.25, 0.03, 0.62, 0.04)
        kit.cyl("Teak", 0, 0, 0, 0, 0.022, 0.018, 8, a=(sx * 0.31, 0.36, 0.42), b=(sx * 0.29, 0.46, 0.8))
    kit.box("Teak", 0, -0.3, 0.25, 0.6, 0.03, 0.04)
    kit.box("Teak", 0, 0.3, 0.25, 0.6, 0.03, 0.04)
    kit.box(fabric, 0, 0.02, 0.33, 0.56, 0.6, 0.12)
    kit.box(fabric, 0, 0.38, 0.6, 0.54, 0.12, 0.42, rx=0.28)


def banquette(kit, x0, z0, x1, z1, back="north", seat_h=0.45, depth=0.55):
    """Built-in lime-plaster bench against a wall with loose seat and back
    cushions. (x0, z0)-(x1, z1) is the plan rectangle of the bench."""
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    rot = {"north": 0.0, "south": math.pi, "east": -math.pi / 2, "west": math.pi / 2}[back]
    length = (x1 - x0 if back in ("north", "south") else z1 - z0) / M
    kit.at(cx, cz, rot)
    d = depth
    kit.box("Lime White", 0, 0, (seat_h - 0.08) / 2, length, d, seat_h - 0.08)
    n = max(1, int(length / 0.62))
    w = length / n
    for i in range(n):
        u = -length / 2 + w * (i + 0.5)
        kit.box("Cushion", u, -0.02, seat_h - 0.04, w - 0.025, d - 0.05, 0.08)
        kit.box("Linen", u, d / 2 - 0.08, seat_h + 0.2, w - 0.06, 0.12, 0.34, rx=-0.12)


def sofa(kit, x, z, rot=0.0, length=1.9, fabric="Linen"):
    kit.at(x, z, rot)
    kit.box("Teak", 0, 0, 0.1, length, 0.82, 0.12)
    kit.box(fabric, 0, -0.02, 0.27, length - 0.24, 0.74, 0.2)
    kit.box(fabric, 0, 0.34, 0.5, length - 0.04, 0.18, 0.62)
    for sx in (-1, 1):
        kit.box(fabric, sx * (length / 2 - 0.1), 0, 0.42, 0.2, 0.82, 0.38)
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.cyl("Teak", sx * (length / 2 - 0.08), sy * 0.33, 0, 0.06, 0.02, 0.02, 8)


# ---------------------------------------------------------------- tables

def bistro(kit, x, z, r=0.32, h=0.74, top="Lime White", things=True, seed=0):
    """Round café table on a black steel pedestal, a cup and a sprig."""
    kit.at(x, z)
    kit.cyl(top, 0, 0, h - 0.03, h, r, r, 28)
    kit.cyl("Black Steel", 0, 0, 0.0, h - 0.03, 0.03, 0.03, 10)
    kit.cyl("Black Steel", 0, 0, 0.0, 0.025, 0.22, 0.2, 18)
    if things:
        rnd = random.Random(seed)
        a = rnd.uniform(0, math.tau)
        kit.cyl("Ceramic White", math.cos(a) * r * 0.45, math.sin(a) * r * 0.45, h, h + 0.08, 0.04, 0.045, 14)
        kit.cyl("Ceramic Dark", -math.cos(a) * r * 0.3, -math.sin(a) * r * 0.3, h, h + 0.12, 0.03, 0.022, 10)
        for k in range(4):
            b = k * 1.6 + a
            kit.cyl("Leaf", 0, 0, 0, 0, 0.003, 0.002, 4,
                    a=(-math.cos(a) * r * 0.3, -math.sin(a) * r * 0.3, h + 0.1),
                    b=(-math.cos(a) * r * 0.3 + math.cos(b) * 0.05, -math.sin(a) * r * 0.3 + math.sin(b) * 0.05, h + 0.24))


def long_table(kit, x, z, rot=0.0, length=2.4, width=0.9, h=0.75, top="Teak"):
    kit.at(x, z, rot)
    kit.box(top, 0, 0, h - 0.025, length, width, 0.05)
    for sx in (-1, 1):
        # Trestle legs in black steel.
        kit.box("Black Steel", sx * (length / 2 - 0.25), 0, (h - 0.05) / 2, 0.05, width - 0.14, h - 0.05)
    kit.box("Black Steel", 0, 0, 0.12, length - 0.5, 0.04, 0.04)


def side_table(kit, x, z, h=0.52, r=0.24):
    kit.at(x, z)
    kit.cyl("Teak", 0, 0, h - 0.035, h, r, r, 24)
    kit.cyl("Teak", 0, 0, 0, h - 0.035, r * 0.42, r * 0.36, 18)


def desk(kit, x, z, rot=0.0, length=1.4, depth=0.7, lamp=True):
    kit.at(x, z, rot)
    kit.box("Teak", 0, 0, 0.73, length, depth, 0.035)
    for sx in (-1, 1):
        kit.box("Black Steel", sx * (length / 2 - 0.04), 0, 0.36, 0.03, depth - 0.06, 0.72)
    if lamp:
        lx = length / 2 - 0.18
        kit.cyl("Black Steel", lx, 0.2, 0.75, 0.77, 0.07, 0.07, 12)
        kit.cyl("Black Steel", 0, 0, 0, 0, 0.008, 0.008, 6, a=(lx, 0.2, 0.77), b=(lx - 0.05, 0.12, 1.15))
        kit.cyl("Brass", 0, 0, 0, 0, 0.06, 0.03, 12, a=(lx - 0.05, 0.12, 1.1), b=(lx - 0.1, 0.02, 1.08))


# ---------------------------------------------------------------- café

def coffee_counter(kit, x, z, rot=0.0, length=2.6, ret=0.9):
    """L-shaped bar: lime-plaster body with a teak slatted front, terrazzo top,
    a brass espresso machine, grinder and a cake dome. `ret` adds a rounded
    end at the right-hand end. Customers stand on the -y (front) side."""
    kit.at(x, z, rot)
    h, d = 1.02, 0.62
    kit.box("Lime White", 0, 0, h / 2 - 0.02, length, d, h - 0.04)
    kit.box("Terrazzo", 0, 0.02, h - 0.02, length + 0.04, d + 0.08, 0.04)
    # Slatted teak front, facing the room (-y side here is the customer side).
    n = int(length / 0.06)
    for i in range(n):
        u = -length / 2 + 0.03 + i * (length - 0.06) / max(1, n - 1)
        kit.box("Teak", u, -d / 2 - 0.012, h / 2 - 0.06, 0.035, 0.025, h - 0.2)
    kit.box("Teak", 0, -d / 2 - 0.01, 0.04, length, 0.04, 0.08)
    if ret:
        kit.arc_box("Lime White", length / 2, d / 2 + 0.0, 0.02, d + 0.02, -math.pi / 2, 0, 0.0, h - 0.04, 12)
        kit.arc_box("Terrazzo", length / 2, d / 2 + 0.0, 0.0, d + 0.06, -math.pi / 2, 0, h - 0.04, h, 12)
    # Machine on the back half of the top.
    mx = -length * 0.18
    kit.box("Brass", mx, 0.12, h + 0.2, 0.62, 0.42, 0.4)
    kit.box("Black Steel", mx, -0.06, h + 0.06, 0.58, 0.12, 0.08)
    for k in (-1, 1):
        kit.cyl("Black Steel", mx + k * 0.16, -0.14, h + 0.1, h + 0.16, 0.035, 0.035, 10)
    kit.cyl("Ceramic White", mx - 0.12, 0.2, h + 0.4, h + 0.46, 0.04, 0.045, 10)
    kit.cyl("Ceramic White", mx + 0.06, 0.2, h + 0.4, h + 0.46, 0.04, 0.045, 10)
    gx = mx + 0.5
    kit.box("Black Steel", gx, 0.12, h + 0.12, 0.18, 0.22, 0.24)
    kit.cyl("Ceramic Dark", gx, 0.12, h + 0.24, h + 0.42, 0.06, 0.1, 12)
    # Cake stand with a glass-ish dome (ceramic white, kept opaque for baking).
    cx = length * 0.28
    kit.cyl("Teak", cx, -0.05, h, h + 0.03, 0.18, 0.18, 20)
    kit.ball("Ceramic White", cx, -0.05, h + 0.03, 0.16, 0.8, 2)
    # Stack of cups and a tip jar.
    for i in range(4):
        kit.cyl("Ceramic White", length * 0.42, 0.15, h + i * 0.05, h + i * 0.05 + 0.048, 0.045, 0.05, 12)


def back_shelf(kit, x, z, rot=0.0, length=2.2, rows=3):
    """Open teak shelves on black brackets against a wall, with jars and cups."""
    kit.at(x, z, rot)
    rnd = random.Random(int(x * 100 + z * 10))
    for r in range(rows):
        y = 1.25 + r * 0.38
        kit.box("Teak", 0, 0, y, length, 0.26, 0.035)
        for sx in (-1, 1):
            kit.box("Black Steel", sx * (length / 2 - 0.15), 0.06, y - 0.06, 0.02, 0.14, 0.1)
        u = -length / 2 + 0.1
        while u < length / 2 - 0.12:
            kind = rnd.random()
            if kind < 0.45:
                kit.cyl("Ceramic White", u, 0, y + 0.02, y + 0.12, 0.045, 0.05, 10)
                u += 0.12
            elif kind < 0.75:
                kit.cyl("Ceramic Dark", u, 0, y + 0.02, y + 0.22, 0.055, 0.055, 10)
                u += 0.14
            else:
                kit.cyl("Leaf", u, 0, y + 0.02, y + 0.1, 0.05, 0.05, 8)
                kit.ball("Leaf", u, 0, y + 0.16, 0.08, 0.8)
                u += 0.18
            u += rnd.uniform(0.02, 0.12)


def pendant(kit, x, z, ceiling, drop=0.7, r=0.2, mat="Rattan"):
    """Woven shade on a cord, `ceiling` in metres above the floor."""
    kit.at(x, z)
    bottom = ceiling - drop
    kit.cyl("Black Steel", 0, 0, bottom + r * 0.9, ceiling, 0.004, 0.004, 4)
    kit.cyl(mat, 0, 0, bottom, bottom + r * 0.9, r, r * 0.25, 16)
    kit.cyl("Lamp Glow", 0, 0, bottom + 0.02, bottom + 0.08, r * 0.3, r * 0.3, 10)


def plant(kit, x, z, h=1.1, pot_r=0.2, seed=1):
    """A potted plant: terracotta pot and a crown of leaf blobs."""
    kit.at(x, z)
    rnd = random.Random(seed)
    ph = pot_r * 1.6
    kit.cyl("Pot", 0, 0, 0, ph, pot_r * 0.8, pot_r, 14)
    for k in range(5):
        a = rnd.uniform(0, math.tau)
        rr = rnd.uniform(0.0, pot_r * 1.2)
        top = (math.cos(a) * rr, math.sin(a) * rr, ph + h * rnd.uniform(0.45, 0.95))
        kit.cyl("Bark", 0, 0, 0, 0, 0.012, 0.008, 5, a=(0, 0, ph), b=top)
        kit.ball("Leaf", top[0], top[1], top[2], h * rnd.uniform(0.14, 0.22), 0.75)


def rug(kit, x0, z0, x1, z1, mat="Linen"):
    kit.at((x0 + x1) / 2, (z0 + z1) / 2)
    kit.box(mat, 0, 0, 0.006, (x1 - x0) / M, (z1 - z0) / M, 0.012)


# ---------------------------------------------------------------- walls

def wall_panel(kit, x, z, rot, w, h, y0, mat, t=0.02):
    """A flat panel on a wall face (rot 0 = facing the street)."""
    kit.at(x, z, rot)
    kit.box(mat, 0, 0, y0 + h / 2, w, t, h)


def faces_wall(kit, x, z, rot, w, h, y0=0.4, seed=7):
    """The guestbook wall (pin 3): rows of small round face outlines drawn by
    guests, here as low-relief discs in two plaster tones and a few in teak."""
    kit.at(x, z, rot)
    rnd = random.Random(seed)
    cols, rows = int(w / 0.2), int(h / 0.24)
    for i in range(cols):
        for j in range(rows):
            if rnd.random() < 0.18:
                continue
            u = -w / 2 + 0.08 + i * (w - 0.16) / max(1, cols - 1) + rnd.uniform(-0.02, 0.02)
            v = y0 + 0.1 + j * (h - 0.2) / max(1, rows - 1) + rnd.uniform(-0.02, 0.02)
            m = "Book Spines" if rnd.random() < 0.55 else "Ceramic Dark"
            # A face: a ring of short strokes (an oval), two eyes, a smile.
            s = rnd.uniform(0.85, 1.1)
            for q in range(14):
                a = q * math.tau / 14
                kit.box(m, u + math.cos(a) * 0.055 * s, -0.01, v + 0.075 + math.sin(a) * 0.072 * s,
                        0.006, 0.005, 0.006)
            kit.box(m, u - 0.02 * s, -0.01, v + 0.09 * s, 0.01, 0.005, 0.01)
            kit.box(m, u + 0.02 * s, -0.01, v + 0.09 * s, 0.01, 0.005, 0.01)
            kit.box(m, u, -0.01, v + 0.045 * s, 0.035 * s, 0.005, 0.005)


def am_pm_panel(kit, x, z, rot, w=1.4, h=1.1, y0=0.9):
    """Sandstone panel with line-art: a cup over AM, a wine glass over PM
    (pin 12) -- the café by day, the club by night."""
    kit.at(x, z, rot)
    kit.box("Sandstone", 0, 0, y0 + h / 2, w, 0.04, h)
    f = -0.025
    line = "Charcoal Steel"
    # Cup (left).
    cx, base = -w * 0.22, y0 + h * 0.42
    kit.box(line, cx, f, base, 0.2, 0.008, 0.008)
    kit.box(line, cx - 0.1, f, base + 0.14, 0.008, 0.008, 0.28, rz=0, rx=0)
    kit.box(line, cx + 0.1, f, base + 0.14, 0.008, 0.008, 0.28)
    kit.box(line, cx, f, base + 0.28, 0.22, 0.008, 0.008)
    kit.box(line, cx, f, base + 0.15, 0.12, 0.008, 0.06)
    # Glass (right).
    gx = w * 0.22
    kit.box(line, gx, f, base, 0.12, 0.008, 0.008)
    kit.box(line, gx, f, base + 0.08, 0.008, 0.008, 0.16)
    for k in range(9):
        a = math.pi + k * math.pi / 8
        kit.box(line, gx + math.cos(a) * 0.09, f, base + 0.26 + math.sin(a) * 0.09, 0.012, 0.008, 0.012)
    kit.box(line, gx, f, base + 0.26, 0.19, 0.008, 0.008)
    # AM / PM as blocky low-relief letters.
    ty = y0 + h * 0.16
    _letters(kit, line, cx, f, ty, "AM")
    _letters(kit, line, gx, f, ty, "PM")


_GLYPH = {   # 3x5 pixel glyphs
    "A": ["010", "101", "111", "101", "101"],
    "M": ["101", "111", "111", "101", "101"],
    "P": ["110", "101", "110", "100", "100"],
    "S": ["111", "100", "111", "001", "111"],
    "C": ["111", "100", "100", "100", "111"],
    "E": ["111", "100", "110", "100", "111"],
    "T": ["111", "010", "010", "010", "010"],
    "G": ["111", "100", "101", "101", "111"],
    "I": ["111", "010", "010", "010", "111"],
    "O": ["111", "101", "101", "101", "111"],
    "N": ["101", "111", "111", "111", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "R": ["110", "101", "110", "101", "101"],
    "H": ["101", "101", "111", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "W": ["101", "101", "111", "111", "101"],
    "K": ["101", "101", "110", "101", "101"],
    "D": ["110", "101", "101", "101", "110"],
    "F": ["111", "100", "110", "100", "100"],
    "B": ["110", "101", "110", "101", "110"],
    "'": ["010", "010", "000", "000", "000"],
    ".": ["000", "000", "000", "000", "010"],
    " ": ["000", "000", "000", "000", "000"],
}


def _letters(kit, mat, cx, y, z, text, px=0.022):
    w = len(text) * 4 * px
    for i, ch in enumerate(text):
        g = _GLYPH.get(ch.upper(), _GLYPH[" "])
        for r, row in enumerate(g):
            for c, on in enumerate(row):
                if on == "1":
                    kit.box(mat, cx - w / 2 + (i * 4 + c) * px + px / 2, y, z + (4 - r) * px + px / 2, px * 0.92, 0.008, px * 0.92)


def lettering(kit, x, z, rot, text, y0, px=0.03, mat="Charcoal Steel"):
    """A line of blocky relief letters on a wall face (rot 0 = facing the street)."""
    kit.at(x, z, rot)
    _letters(kit, mat, 0, -0.012, y0, text, px)


def spotlight_cone(kit, x, z, rot, top_y, width, floor_depth=0.9, mat="Gulmohar Paint"):
    """Pin 2/17/23: a cone of light painted on the wall from a lamp down to the
    floor, spilling onto the floor as a trapezoid. A single chair stands in it."""
    kit.at(x, z, rot)
    bm_mat = mat
    # Wall triangle as thin strips (a fan of narrow boxes reads as a flat paint area).
    n = 24
    for i in range(n):
        v = i / n
        hgt = top_y * (1 - v)
        wv = width * v + 0.02
        kit.box(bm_mat, 0, -0.004, hgt - top_y / n / 2, wv, 0.004, top_y / n + 0.002)
    # Floor spill.
    for i in range(10):
        v = i / 10
        kit.box(bm_mat, 0, -0.004 - floor_depth * (v + 0.05), 0.002, width * (1 + 0.25 * v), floor_depth / 10 + 0.002, 0.003)
    # The lamp.
    kit.cyl("Black Steel", 0, -0.08, top_y + 0.02, top_y + 0.1, 0.06, 0.03, 12)
    kit.box("Black Steel", 0, -0.04, top_y + 0.1, 0.02, 0.08, 0.02)


# ---------------------------------------------------------------- event, games, quiet

def bleachers(kit, x, z, rot=0.0, width=3.0, steps=3, rise=0.4, tread=0.7):
    """Tiered teak seating (pin 21) with gulmohar cushions on each step."""
    kit.at(x, z, rot)
    for s in range(steps):
        y0 = s * tread
        kit.box("Teak", 0, y0 + tread / 2, (s + 1) * rise / 2, width, tread, (s + 1) * rise)
        n = max(1, int(width / 0.55))
        for i in range(n):
            u = -width / 2 + (i + 0.5) * width / n
            kit.box("Cushion", u, y0 + tread * 0.35, (s + 1) * rise + 0.03, width / n - 0.08, tread * 0.5, 0.05)


def stage(kit, x, z, rot=0.0, w=2.6, d=1.4, h=0.3):
    """Low teak platform, a mic stand, a stool and two floor speakers."""
    kit.at(x, z, rot)
    kit.box("Teak", 0, 0, h / 2, w, d, h)
    kit.box("Black Steel", 0, -d / 2 - 0.005, h / 2, w, 0.01, h)
    kit.cyl("Black Steel", 0.3, 0.1, h, h + 0.02, 0.12, 0.12, 12)
    kit.cyl("Black Steel", 0.3, 0.1, h, h + 1.45, 0.008, 0.008, 6)
    kit.cyl("Black Steel", 0.3, 0.06, h + 1.42, h + 1.5, 0.02, 0.02, 8)
    for sx in (-1, 1):
        kit.box("Black Steel", sx * (w / 2 - 0.25), 0.1, h + 0.25, 0.32, 0.3, 0.5, rx=0.0)


def screen(kit, x, z, rot, w=2.4, h=1.35, y0=0.9):
    """Projection screen on a wall, with a thin black frame."""
    kit.at(x, z, rot)
    kit.box("Black Steel", 0, -0.01, y0 + h / 2, w + 0.06, 0.02, h + 0.06)
    kit.box("Screen", 0, -0.022, y0 + h / 2, w, 0.006, h)


def carrom(kit, x, z, rot=0.0):
    """Carrom board on a teak stand, coins on the felt."""
    kit.at(x, z, rot)
    s = 0.88
    kit.box("Teak", 0, 0, 0.7, s + 0.1, s + 0.1, 0.06)
    kit.box("Ceramic White", 0, 0, 0.735, s, s, 0.012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.cyl("Teak", sx * s * 0.4, sy * s * 0.4, 0, 0.67, 0.025, 0.03, 8)
            kit.cyl("Ceramic Dark", sx * s * 0.45, sy * s * 0.45, 0.74, 0.745, 0.025, 0.025, 10)
    rnd = random.Random(3)
    for i in range(19):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0, 0.08)
        kit.cyl("Ceramic Dark" if i % 2 else "Teak", math.cos(a) * r, math.sin(a) * r, 0.742, 0.75, 0.016, 0.016, 8)


def game_table(kit, x, z, rot=0.0, seed=5):
    """Square teak table with a board game laid out, four chairs."""
    kit.at(x, z, rot)
    kit.box("Teak", 0, 0, 0.73, 0.9, 0.9, 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.box("Teak", sx * 0.4, sy * 0.4, 0.36, 0.05, 0.05, 0.72)
    kit.box("Linen", 0, 0, 0.755, 0.5, 0.5, 0.01)
    rnd = random.Random(seed)
    for i in range(8):
        kit.cyl("Cushion" if i % 2 else "Ceramic Dark", rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0.76, 0.8, 0.015, 0.012, 8)


def chalk_wall(kit, x, z, rot, w=2.2, h=1.6, y0=0.5):
    """Chalkboard game wall (pin 24): noughts and crosses, hangman, a score."""
    kit.at(x, z, rot)
    kit.box("Teak", 0, -0.01, y0 + h / 2, w + 0.08, 0.02, h + 0.08)
    kit.box("Chalkboard", 0, -0.022, y0 + h / 2, w, 0.006, h)
    f = -0.027
    _letters(kit, "Chalk", 0, f, y0 + h - 0.28, "GAME TIME", 0.03)
    gx, gy = w * 0.2, y0 + 0.55
    for k in (-1, 1):
        kit.box("Chalk", gx + k * 0.1, f, gy, 0.012, 0.004, 0.6)
        kit.box("Chalk", gx, f, gy + k * 0.1, 0.6, 0.004, 0.012)
    hx = -w * 0.25
    kit.box("Chalk", hx, f, gy - 0.25, 0.3, 0.004, 0.012)
    kit.box("Chalk", hx - 0.1, f, gy + 0.05, 0.012, 0.004, 0.6)
    kit.box("Chalk", hx - 0.02, f, gy + 0.34, 0.18, 0.004, 0.012)
    kit.ball("Chalk", hx + 0.07, f, gy + 0.22, 0.05, 1, 1)


def bookshelf(kit, x, z, rot=0.0, w=1.6, h=2.0, seed=2):
    """Teak bookcase full of books, the odd plant and object."""
    kit.at(x, z, rot)
    d = 0.32
    for sx in (-1, 1):
        kit.box("Teak", sx * (w / 2 - 0.015), 0, h / 2, 0.03, d, h)
    kit.box("Teak", 0, d / 2 - 0.01, h / 2, w, 0.02, h)
    rnd = random.Random(seed)
    shelves = 5
    for s in range(shelves + 1):
        y = 0.06 + s * (h - 0.1) / shelves
        kit.box("Teak", 0, 0, y, w - 0.03, d, 0.025)
        if s == shelves:
            break
        u = -w / 2 + 0.05
        top = (h - 0.1) / shelves - 0.05
        while u < w / 2 - 0.08:
            if rnd.random() < 0.08:
                kit.ball("Leaf", u + 0.08, 0, y + 0.12, 0.08, 0.9)
                u += 0.2
                continue
            bw = rnd.uniform(0.025, 0.05)
            bh = top * rnd.uniform(0.62, 0.95)
            m = rnd.choice(["Book Spines", "Linen", "Cushion", "Ceramic Dark", "Olive Velvet", "Book Spines"])
            kit.box(m, u + bw / 2, 0.01, y + 0.0125 + bh / 2, bw, d * 0.8, bh)
            u += bw + 0.003
