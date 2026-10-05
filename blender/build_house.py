"""
build_house.py -- headless Blender build of the Space house.

Builds the four floors from the site's glTF exports, adds slabs, roof,
parapets, finishes, ground, dawn lighting, fog and a street camera, saves
blender/space-house.blend and (unless --no-render) renders
blender/renders/01-dawn.png.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py
  ... --python build_house.py -- --no-render

Target: Blender 5.2 LTS. Scene units are metres. Everything that belongs to a
floor is parented to an Empty "Floor.<name>" whose scale is UNIT_M, so the
children are authored in model units (1 unit = 8 ft) and the floors can be
moved later for a cutaway animation.

Axis convention: Three.js (x, y, z) -> Blender (x, -z, y). +X = east,
+Y = north, so the street (Three.js +Z) is on the Blender -Y (south) side.
"""

import math
import os
import re
import sys

import bpy
from mathutils import Matrix, Vector

# =============================================================================
# CONSTANTS
# =============================================================================

REPO_FALLBACK = "/Users/rejoesudarsan/Dev/networker-space"

UNIT_M = 2.4384              # 1 model unit = 8 ft = 2.4384 m
SLAB_T = 0.14583             # slab thickness, units (0.3556 m)
STOREY = 1.45                # storey height, units (3.535 m)
WALL_H_GLB = 0.5625          # cutaway wall height baked into the GLB, units
COL_H_GLB = 0.5625 + 6 / 96  # column height in the GLB, units (0.625)
# Spec says 1.30; storey - slab (1.30417) closes the 1 cm sliver under the
# slab above. Set to 1.30 for the literal value.
WALL_H = STOREY - SLAB_T

# floor key -> width, depth (units), Three.js offset (x, z), LEVEL (up, units)
FLOORS = {
    "basement": dict(width=4.584, depth=7.229, offset=(0.416, 1.387), level=-0.72),
    "ground":   dict(width=6.25,  depth=10.0,  offset=(0.0, 0.0),     level=0.73),
    "first":    dict(width=5.833, depth=8.313, offset=(-0.208, -0.842), level=2.18),
    "second":   dict(width=4.583, depth=7.063, offset=(0.417, -0.217), level=3.63),
}
FLOOR_ORDER = ["basement", "ground", "first", "second"]
COLLECTION_FOR = {"basement": "Basement", "ground": "Ground",
                  "first": "First", "second": "Second"}

# Slab voids, floor-local Three.js (x0, z0, x1, z1), units.
SLAB_VOIDS = {
    "basement": [],
    "ground": [(0.56, -0.65, 1.99, 0.8),
               (1.25, 3.27, 3.12, 5.01),     # notch from front edge
               (-1.85, 3.2, -0.2, 5.01)],    # notch from front edge
    "first": [],
    "second": [(0.18, -0.49, 1.88, 1.06)],   # courtyard void
}

# Roof / terrace (second-floor-local, units)
TERRACE_X1 = -0.95           # terrace spans x -width/2 .. -0.95, rooms -0.95 .. +width/2
PARAPET_H = 0.30
PARAPET_T = 0.08
# Height of the roof slab's underside above the second-floor slab top.
# Spec literal: STOREY (leaves a ~37 cm gap above the 1.30-unit walls).
# Default treats the roof like the next floor slab: top at +STOREY, hanging
# below, so the house reads closed.
ROOF_UNDERSIDE = STOREY - SLAB_T
ROOF_VOIDS = []              # Three.js (x0, z0, x1, z1); e.g. SLAB_VOIDS["second"] to open the courtyard

# Finish planes (floor-local Three.js x0, z0, x1, z1), thickness in metres
FINISH_T_M = 0.02
FINISHES = [
    # floor,   name,            rect (x0, z0, x1, z1),       material
    ("ground", "Living1.Teak",  (0.56, 0.2, 2.4, 3.2),       "Teak"),
    ("ground", "FrontLawn",     (-0.2, 3.3, 1.2, 4.95),      "Foliage"),
    ("ground", "EntranceCourt", (-2.3, -0.3, -1.55, 1.3),    "Red Oxide"),
    # terrace floor is added from the terrace extents (Terracotta)
]

# Openings (floor-local units). The GLB walls have every window span and door
# gap cut full height; these close them above the opening.
SILL_H = 22 / 96             # sill top (the GLB "sills" mesh is 0..SILL_H)
WINDOW_H = 0.86              # window height above the sill (site/src/world/windows.js)
WINDOW_HEAD = SILL_H + WINDOW_H
SILL_MATERIAL = "Lime White"  # spec said Teak; the photos / board show plastered wall under the windows
DOOR_HEAD = 84 / 96          # 7 ft
WIN_MIN_LEN = 0.18           # windows.js island filter: skip shorter ...
WIN_MAX_WIDTH = 0.20         # ... or broader (curved / area) islands
WIN_FRAME = 0.035            # head / sill rail section
WIN_RAIL_H = 0.036
WIN_MULLION = 0.025
WIN_MULLION_STEP = 0.42
WIN_PANE_T = 0.012
OPENINGS_JSON = "data/openings.json"   # relative to this script; from extract_openings.mjs
GAP_HEADS = "all"            # lintels at DOOR_HEAD over non-door wall gaps: "all" | "perimeter" | "none"
FILL_SLIVERS = True          # fill <1 ft gaps between wall strips full height

# Plinth skirt: ground-floor-local Three.js (w, d, x, z) from site/src/world/world.js;
# boxes from the street (y = -LEVEL.ground) up to the slab underside.
SKIRTS = [
    (1.275, 0.06, -2.4875, 4.97),
    (1.45, 0.06, 0.525, 4.97),
    (6.25, 0.06, 0.0, -4.97),
    (0.06, 10.0, -3.1, 0.0),
    (0.06, 9.45, 3.1, -0.275),
]
# Gate steps (world.js): for s < 4: box(0.8, 0.73 - s*0.18, 0.22) at (-2.75, street, 5.05 + s*0.2)
STEP_X, STEP_W, STEP_D, STEP_Z0, STEP_DZ, STEP_RISE, STEP_COUNT = -2.75, 0.8, 0.22, 5.05, 0.2, 0.18, 4
# Street gate + front wall (details.js groundFloor), ground-floor-local
GATE_PIER_X1 = -2.38         # second pier; the first is at -width/2 + 0.05
GATE_Z_INSET = 0.1           # zf = depth/2 - 0.1
GATE_PIER = (0.1, 0.44, 0.12)            # w, h, d
GATE_PIER_CAP = (0.13, 0.025, 0.15)
GATE_H, GATE_SLATS = 0.4, 7
FRONT_WALL_H, FRONT_WALL_T = 0.22, 0.08
FRONT_COPING_H, FRONT_COPING_T = 0.025, 0.11
OFFICE_GATE_SLATS = 6        # details.js street(): at the plot's front-right, street level

# Site
GROUND_RADIUS_M = 60.0
GROUND_SEGMENTS = 128

# Palette: name -> (hex, roughness, metallic)
PALETTE = {
    "Lime White":     ("#E8E4DA", 0.90, 0.0),
    "Lime White Shade": ("#DEDAD1", 0.90, 0.0),   # plinth skirt, copings (site plasterShade)
    "Teak":           ("#805238", 0.45, 0.0),
    "Terrazzo":       ("#CBC4B5", 0.35, 0.0),
    "Sandstone":      ("#B3A68B", 0.80, 0.0),
    "Terracotta":     ("#B66E51", 0.85, 0.0),
    "Red Oxide":      ("#884B45", 0.30, 0.0),
    "Charcoal Steel": ("#383B3A", 0.40, 0.8),
    "Foliage":        ("#59634D", 0.70, 0.0),
    "Asphalt":        ("#4A4846", 0.90, 0.0),
}
TERRAZZO_CHIPS = ("#A89E8E", "#DCD6C9")
TERRACOTTA_GROUT = "#8F5A42"
LIME_BUMP_SCALE = 80.0       # per metre
LIME_BUMP_STRENGTH = 0.05
BRICK_TILE_M = 0.30

# Dawn
SKY_HORIZON = "#E9C9C0"
SKY_ZENITH = "#CFC6D3"
SKY_GRADIENT_TOP = 0.6       # sin(elevation) at which the sky reaches the zenith colour
WORLD_STRENGTH = 1.0
FOG_COLOR = "#D1BFC2"
FOG_DENSITY = 0.005          # per metre (spec 0.012 read muddy at ~56 m)
FOG_ANISOTROPY = 0.3
# 'domain': finite fog box around the scene (default; keeps the sun and sky
# from being fully absorbed by an infinite medium). 'world': world Volume.
FOG_MODE = "domain"
FOG_BOX_SIZE_M = (160.0, 160.0, 60.0)
FOG_BOX_Z0_M = -5.0
SUN_COLOR = "#FFC394"
SUN_STRENGTH = 4.0           # spec ~2; raised so the facade reads bright through the haze
SUN_ANGLE_DEG = 3.0
SUN_ELEVATION_DEG = 8.0
SUN_AZIMUTH_DEG = 112.5      # clockwise from north (+Y): east-south-east
MIST_START_M = 5.0
MIST_DEPTH_M = 150.0

# Camera
CAM_LENS_MM = 50.0
CAM_SENSOR_MM = 36.0
CAM_HEIGHT_M = 1.7
# The spec's "about 22 m from the house centre" puts a 50 mm lens ~10 m from
# a 15 m wide, 13 m tall house, which cannot frame it. The distance is derived
# instead so the house fills CAM_FILL of the frame (width or height, whichever
# binds). Set CAM_DISTANCE_M to a number to force a distance from the house
# centre.
CAM_FILL = 0.62
CAM_DISTANCE_M = None
CAM_AIM_Z_M = None           # None -> mid-height of the visible house (spec: ~4 m)
CAM_MIN_EDGE_MARGIN_M = 2.0  # keep camera inside the ground disc

# Extra views
ANGLE_LENS_MM = 35.0
ANGLE_CAM_M = (-15.95, -27.85, 1.6)     # street, off the front-left corner (like photo p03)
ANGLE_TARGET_M = (-1.0, -6.0, 6.0)       # ~9.4 deg up; frame spans ~-9.5..+28.4 deg (steps ~-5.4, parapet ~25)
TOP_CAM_Z_M = 45.0
TOP_MARGIN = 1.12                        # ortho frame = plot extent x margin
TOP_ROTATE_DEG = -90.0                   # long axis across the frame; street on the right

# Render
RES_X, RES_Y = 1536, 1024
QUICK_SAMPLES = 32
QUICK_PERCENT = 50
SAMPLES = 256
VIEW_TRANSFORM = "AgX"
EXPOSURE = 0.0

# =============================================================================
# Paths and args
# =============================================================================

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.join(REPO_FALLBACK, "blender")
REPO = os.path.dirname(SCRIPT_DIR)
if not os.path.isdir(os.path.join(REPO, "site", "public", "models")):
    REPO = REPO_FALLBACK
    SCRIPT_DIR = os.path.join(REPO, "blender")
MODELS_DIR = os.path.join(REPO, "site", "public", "models")
BLEND_PATH = os.path.join(SCRIPT_DIR, "space-house.blend")
RENDER_DIR = os.path.join(SCRIPT_DIR, "renders")
RENDER_PATH = os.path.join(RENDER_DIR, "01-dawn.png")
RENDER_ANGLE_PATH = os.path.join(RENDER_DIR, "02-angle.png")
RENDER_TOP_PATH = os.path.join(RENDER_DIR, "03-top.png")
OPENINGS_PATH = os.path.join(SCRIPT_DIR, OPENINGS_JSON)

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NO_RENDER = "--no-render" in ARGS
QUICK = "--quick" in ARGS


def warn(msg):
    print("[build_house] WARNING: " + msg)


def info(msg):
    print("[build_house] " + msg)


# =============================================================================
# Helpers
# =============================================================================

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h, alpha=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), alpha)


def scaled(rgba, k):
    return (rgba[0] * k, rgba[1] * k, rgba[2] * k, rgba[3])


def three_rect_to_blender(r):
    """Three.js (x0, z0, x1, z1) -> Blender (x0, x1, y0, y1)."""
    x0, z0, x1, z1 = r
    return (min(x0, x1), max(x0, x1), -max(z0, z1), -min(z0, z1))


def link_only(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def set_parent(obj, parent):
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)


def slab_mesh(name, rect, voids, z_top, thickness):
    """Closed prism over rect (x0, x1, y0, y1) minus rectangular voids.

    Built on a grid of every rect/void edge so there are no T-junctions:
    top/bottom quads per kept cell, side quads on boundary edges.
    """
    x0, x1, y0, y1 = rect
    clipped = []
    for (vx0, vx1, vy0, vy1) in voids:
        cx0, cx1 = max(vx0, x0), min(vx1, x1)
        cy0, cy1 = max(vy0, y0), min(vy1, y1)
        if cx1 > cx0 and cy1 > cy0:
            clipped.append((cx0, cx1, cy0, cy1))
    xs = sorted({x0, x1} | {v for c in clipped for v in c[0:2]})
    ys = sorted({y0, y1} | {v for c in clipped for v in c[2:4]})

    def in_void(px, py):
        return any(c[0] < px < c[1] and c[2] < py < c[3] for c in clipped)

    zt, zb = z_top, z_top - thickness
    verts, index = [], {}

    def vid(i, j, top):
        key = (i, j, top)
        if key not in index:
            index[key] = len(verts)
            verts.append((xs[i], ys[j], zt if top else zb))
        return index[key]

    faces, edge_count, directed, mat_idx = [], {}, [], []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if in_void((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2):
                continue
            ring = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]  # CCW from +Z
            faces.append([vid(a, b, True) for a, b in ring])
            faces.append([vid(a, b, False) for a, b in reversed(ring)])
            mat_idx += [0, 1]
            for k in range(4):
                a, b = ring[k], ring[(k + 1) % 4]
                key = frozenset((a, b))
                edge_count[key] = edge_count.get(key, 0) + 1
                directed.append((a, b))
    for a, b in directed:
        if edge_count[frozenset((a, b))] == 1:
            faces.append([vid(a[0], a[1], True), vid(a[0], a[1], False),
                          vid(b[0], b[1], False), vid(b[0], b[1], True)])
            mat_idx.append(1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me["_mat_idx"] = mat_idx  # top = 0, bottom / sides = 1 (consumed by add_slab)
    return me


def add_slab(name, rect, voids, z_top, thickness, coll, parent, mat, side_mat=None):
    """side_mat: material for the underside and edges (top keeps `mat`)."""
    me = slab_mesh(name, rect, voids, z_top, thickness)
    idx = list(me["_mat_idx"])
    del me["_mat_idx"]
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    if parent is not None:
        set_parent(obj, parent)
    if mat is not None:
        me.materials.append(mat)
        if side_mat is not None and len(idx) == len(me.polygons):
            me.materials.append(side_mat)
            try:
                me.polygons.foreach_set("material_index", idx)
                me.update()
            except Exception as e:
                warn("slab side material on %s: %s" % (name, e))
    return obj


class BoxMesh:
    """Accumulates axis-aligned boxes into one mesh (floor-local units)."""

    def __init__(self):
        self.verts, self.faces = [], []

    def add(self, x0, x1, y0, y1, z0, z1):
        if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
            return
        b = len(self.verts)
        self.verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                       (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.faces.append([b + i for i in f])

    def add_centred(self, cx, cy, cz, sx, sy, sz):
        self.add(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2)

    def add_three(self, x0, x1, z0, z1, y0, y1):
        """Three.js extents (x, z plan; y up) -> Blender (x, -z, y)."""
        self.add(min(x0, x1), max(x0, x1), -max(z0, z1), -min(z0, z1), y0, y1)

    def to_object(self, name, coll, parent, mat):
        if not self.faces:
            return None
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        obj = bpy.data.objects.new(name, me)
        coll.objects.link(obj)
        if parent is not None:
            set_parent(obj, parent)
        if mat is not None:
            me.materials.append(mat)
        return obj


def mesh_islands(verts, polys, weld=1e-4):
    """Bounding boxes (x0, x1, y0, y1) of the connected parts of a mesh.

    Vertices are welded on a grid first (glTF export splits them), like
    islands() in site/src/world/windows.js.
    """
    key_to_id, ids, pts = {}, [], []
    for v in verts:
        k = (round(v[0] / weld), round(v[1] / weld), round(v[2] / weld))
        if k not in key_to_id:
            key_to_id[k] = len(pts)
            pts.append(v)
        ids.append(key_to_id[k])
    parent = list(range(len(pts)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for poly in polys:
        r0 = root(ids[poly[0]])
        for vi in poly[1:]:
            r = root(ids[vi])
            if r != r0:
                parent[r] = r0
    boxes = {}
    for i, p in enumerate(pts):
        r = root(i)
        b = boxes.get(r)
        if b is None:
            boxes[r] = [p[0], p[0], p[1], p[1]]
        else:
            b[0], b[1] = min(b[0], p[0]), max(b[1], p[0])
            b[2], b[3] = min(b[2], p[1]), max(b[3], p[1])
    return [tuple(b) for b in boxes.values()]


def spans(a0, a1, cuts):
    """What is left of [a0, a1] once the cuts are removed (details.js spans())."""
    out = [(a0, a1)]
    for c0, c1 in cuts:
        nxt = []
        for s0, s1 in out:
            if c1 <= s0 or c0 >= s1:
                nxt.append((s0, s1))
            else:
                nxt += [(u, v) for u, v in ((s0, c0), (c1, s1)) if v - u > 0.04]
        out = nxt
    return out


def cuts_at_z(rects, z, pad=0.0):
    """Three.js rects (x0, z0, x1, z1) crossing the line at fixed z -> x cuts."""
    return [(r[0] - pad, r[2] + pad) for r in rects if r[1] - pad < z < r[3] + pad]


def add_box(name, x0, x1, y0, y1, z0, z1, coll, parent, mat):
    return add_slab(name, (x0, x1, y0, y1), [], z1, z1 - z0, coll, parent, mat)


def get_collection(name, parent_coll):
    c = bpy.data.collections.new(name)
    parent_coll.children.link(c)
    return c


# =============================================================================
# Materials
# =============================================================================

def new_material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True  # deprecated / implicit in 5.x
    except Exception:
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat, nt, bsdf


def metric_coords(nt):
    """Object coords scaled to metres (children of floor Empties are in units)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-900, 0)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (-700, 0)
    mp.inputs["Scale"].default_value = (UNIT_M, UNIT_M, UNIT_M)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def ramp(nt, stops, interp="LINEAR"):
    node = nt.nodes.new("ShaderNodeValToRGB")
    node.location = (-250, 0)
    cr = node.color_ramp
    try:
        cr.interpolation = interp
    except Exception as e:
        warn("color ramp interpolation: %s" % e)
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = stops[0][1]
    cr.elements[1].position = stops[-1][0]
    cr.elements[1].color = stops[-1][1]
    for pos, col in stops[1:-1]:
        el = cr.elements.new(pos)
        el.color = col
    return node


def build_materials():
    mats = {}
    for name, (hx, rough, metal) in PALETTE.items():
        mat, nt, bsdf = new_material(name)
        base = hex_to_linear(hx)
        bsdf.inputs["Base Color"].default_value = base
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        try:
            mat.diffuse_color = base  # viewport solid colour
        except Exception:
            pass
        try:
            if name.startswith("Lime White"):
                vec = metric_coords(nt)
                noise = nt.nodes.new("ShaderNodeTexNoise")
                noise.location = (-450, -250)
                noise.inputs["Scale"].default_value = LIME_BUMP_SCALE
                noise.inputs["Detail"].default_value = 4.0
                nt.links.new(vec, noise.inputs["Vector"])
                bump = nt.nodes.new("ShaderNodeBump")
                bump.location = (-150, -250)
                bump.inputs["Strength"].default_value = LIME_BUMP_STRENGTH
                bump.inputs["Distance"].default_value = 0.02
                nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
                nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
            elif name == "Teak":
                vec = metric_coords(nt)
                wave = nt.nodes.new("ShaderNodeTexWave")
                wave.location = (-450, 0)
                try:
                    wave.wave_type = "BANDS"
                    wave.bands_direction = "X"
                    wave.wave_profile = "SIN"
                except Exception as e:
                    warn("wave texture props: %s" % e)
                wave.inputs["Scale"].default_value = 6.0
                wave.inputs["Distortion"].default_value = 8.0
                wave.inputs["Detail"].default_value = 3.0
                wave.inputs["Detail Scale"].default_value = 1.5
                noise = nt.nodes.new("ShaderNodeTexNoise")
                noise.location = (-700, -250)
                noise.inputs["Scale"].default_value = 3.0
                # noise distortion of the grain: add noise colour to coordinates
                add = nt.nodes.new("ShaderNodeVectorMath")
                add.location = (-600, 0)
                add.operation = "ADD"
                nt.links.new(vec, add.inputs[0])
                nt.links.new(noise.outputs["Color"], add.inputs[1])
                nt.links.new(vec, noise.inputs["Vector"])
                nt.links.new(add.outputs["Vector"], wave.inputs["Vector"])
                r = ramp(nt, [(0.0, scaled(base, 0.62)), (1.0, scaled(base, 1.1))])
                nt.links.new(wave.outputs["Fac"], r.inputs["Fac"])
                nt.links.new(r.outputs["Color"], bsdf.inputs["Base Color"])
            elif name == "Terrazzo":
                vec = metric_coords(nt)
                vor = nt.nodes.new("ShaderNodeTexVoronoi")
                vor.location = (-450, 0)
                vor.inputs["Scale"].default_value = 40.0
                c1, c2 = (hex_to_linear(h) for h in TERRAZZO_CHIPS)
                nt.links.new(vec, vor.inputs["Vector"])
                r = ramp(nt, [(0.0, base), (0.55, c1), (0.8, c2)], "CONSTANT")
                nt.links.new(vor.outputs["Color"], r.inputs["Fac"])
                nt.links.new(r.outputs["Color"], bsdf.inputs["Base Color"])
            elif name in ("Sandstone", "Red Oxide"):
                vec = metric_coords(nt)
                noise = nt.nodes.new("ShaderNodeTexNoise")
                noise.location = (-450, 0)
                noise.inputs["Scale"].default_value = 6.0 if name == "Sandstone" else 12.0
                noise.inputs["Detail"].default_value = 6.0
                nt.links.new(vec, noise.inputs["Vector"])
                k = 0.12 if name == "Sandstone" else 0.05
                r = ramp(nt, [(0.3, scaled(base, 1 - k)), (0.7, scaled(base, 1 + k))])
                nt.links.new(noise.outputs["Fac"], r.inputs["Fac"])
                nt.links.new(r.outputs["Color"], bsdf.inputs["Base Color"])
            elif name == "Terracotta":
                vec = metric_coords(nt)
                brick = nt.nodes.new("ShaderNodeTexBrick")
                brick.location = (-450, 0)
                try:
                    brick.offset = 0.0           # stack-bond tiles
                    brick.offset_frequency = 1
                except Exception as e:
                    warn("brick props: %s" % e)
                brick.inputs["Scale"].default_value = 1.0
                brick.inputs["Brick Width"].default_value = BRICK_TILE_M
                brick.inputs["Row Height"].default_value = BRICK_TILE_M
                brick.inputs["Mortar Size"].default_value = 0.006
                brick.inputs["Color1"].default_value = base
                brick.inputs["Color2"].default_value = scaled(base, 0.9)
                brick.inputs["Mortar"].default_value = hex_to_linear(TERRACOTTA_GROUT)
                nt.links.new(vec, brick.inputs["Vector"])
                nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
        except Exception as e:
            warn("procedural nodes for %s failed (%s); using flat colour" % (name, e))
        mats[name] = mat
    mats["Glass"] = build_glass()
    return mats


def build_glass():
    mat, nt, bsdf = new_material("Glass")
    bsdf.inputs["Base Color"].default_value = hex_to_linear("#F2F5F4")
    bsdf.inputs["Roughness"].default_value = 0.05
    for key in ("Transmission Weight", "Transmission"):  # 4.x+ / 3.x name
        try:
            bsdf.inputs[key].default_value = 1.0
            break
        except Exception:
            continue
    else:
        warn("Glass: no Transmission input found")
    try:
        bsdf.inputs["IOR"].default_value = 1.45
    except Exception as e:
        warn("Glass IOR: %s" % e)
    try:
        mat.diffuse_color = (0.8, 0.85, 0.85, 0.3)
    except Exception:
        pass
    return mat


# =============================================================================
# Import floors
# =============================================================================

def enable_gltf_addon():
    try:
        import addon_utils
        addon_utils.enable("io_scene_gltf2", default_set=True)
    except Exception as e:
        warn("could not enable io_scene_gltf2: %s" % e)


def import_gltf(path):
    """Import a GLB; enable the glTF add-on and retry once if the op is missing."""
    if not os.path.isfile(path):
        raise RuntimeError("GLB not found: %s" % path)
    try:
        bpy.ops.import_scene.gltf(filepath=path)
    except (AttributeError, RuntimeError) as e:
        warn("glTF import failed (%s); enabling io_scene_gltf2 and retrying" % e)
        enable_gltf_addon()
        try:
            bpy.ops.import_scene.gltf(filepath=path)
        except Exception as e2:
            raise RuntimeError("could not import %s: %s" % (path, e2))


def base_name(name):
    return re.sub(r"\.\d+$", "", name)


def import_floor(key, coll, detail_coll, mats):
    spec = FLOORS[key]
    ox, oz = spec["offset"]
    empty = bpy.data.objects.new("Floor." + key, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.location = (ox * UNIT_M, -oz * UNIT_M, spec["level"] * UNIT_M)
    empty.scale = (UNIT_M, UNIT_M, UNIT_M)
    coll.objects.link(empty)

    path = os.path.join(MODELS_DIR, key + ".glb")
    before_obj = set(bpy.data.objects)
    before_mat = set(bpy.data.materials)
    vl = bpy.context.view_layer
    vl.active_layer_collection = vl.layer_collection
    import_gltf(path)
    vl.update()
    new_objs = [o for o in bpy.data.objects if o not in before_obj]
    new_mats = [m for m in bpy.data.materials if m not in before_mat]

    # Bake each imported transform into its data, then reparent to our Empty.
    world = {o: o.matrix_world.copy() for o in new_objs}
    counts = {}
    for o in new_objs:
        if o.type == "EMPTY":
            continue
        b = base_name(o.name)
        if o.type == "MESH" and o.data is not None:
            o.data.transform(world[o])
        o.parent = None
        o.matrix_basis = Matrix.Identity(4)
        if b == "slab":
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
            continue
        set_parent(o, empty)
        if o.type == "MESH":
            o.data.materials.clear()
        if b == "walls":
            o.data.transform(Matrix.Diagonal((1.0, 1.0, WALL_H / WALL_H_GLB, 1.0)))
            o.data.materials.append(mats["Lime White"])
            link_only(o, coll)
        elif b == "columns":
            o.data.transform(Matrix.Diagonal((1.0, 1.0, WALL_H / COL_H_GLB, 1.0)))
            o.data.materials.append(mats["Lime White"])
            link_only(o, coll)
        elif b == "sills":
            o.data.materials.append(mats[SILL_MATERIAL])
            link_only(o, coll)
        else:  # details / LineSegments
            link_only(o, detail_coll)
        o.name = "%s.%s" % (key, b)
        if o.type == "MESH":
            o.data.name = o.name
        counts[b] = counts.get(b, 0) + 1
    for o in new_objs:
        try:
            if o.type == "EMPTY" and o.name in bpy.data.objects:
                bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError:
            pass
    for m in new_mats:
        if m.users == 0:
            bpy.data.materials.remove(m)
    info("imported %s: %s" % (key, counts))
    return empty


# =============================================================================
# Openings: window heads, frames, glass; door heads
# =============================================================================

def load_openings():
    try:
        import json
        with open(OPENINGS_PATH) as f:
            return json.load(f)
    except Exception as e:
        warn("no door openings (%s): run extract_openings.mjs; doors stay full height" % e)
        return None


def build_windows(key, empty, coll, mats):
    """Head block over every sill + teak frames, mullions and a glass pane per window island."""
    sills = bpy.data.objects.get("%s.sills" % key)
    if sills is None or sills.type != "MESH":
        warn("%s: no sills mesh; windows skipped" % key)
        return 0
    # Head: the sill footprint again, from the window head to the wall top.
    head_me = sills.data.copy()
    head_me.name = "%s.windowHeads" % key
    k = (WALL_H - WINDOW_HEAD) / SILL_H
    head_me.transform(Matrix.Translation((0.0, 0.0, WINDOW_HEAD)) @ Matrix.Diagonal((1.0, 1.0, k, 1.0)))
    head_me.materials.clear()
    head_me.materials.append(mats["Lime White"])
    head = bpy.data.objects.new(head_me.name, head_me)
    coll.objects.link(head)
    set_parent(head, empty)

    verts = [v.co[:] for v in sills.data.vertices]
    polys = [p.vertices[:] for p in sills.data.polygons]
    frames, panes = BoxMesh(), BoxMesh()
    n = 0
    H, z0 = WINDOW_H, SILL_H
    for (x0, x1, y0, y1) in mesh_islands(verts, polys):
        sx, sy = x1 - x0, y1 - y0
        along_x = sx > sy
        length = max(sx, sy)
        if length < WIN_MIN_LEN or min(sx, sy) > WIN_MAX_WIDTH:
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for zc in (WIN_RAIL_H / 2, H - WIN_RAIL_H / 2):
            if along_x:
                frames.add_centred(cx, cy, z0 + zc, length, WIN_FRAME, WIN_RAIL_H)
            else:
                frames.add_centred(cx, cy, z0 + zc, WIN_FRAME, length, WIN_RAIL_H)
        div = max(1, int(math.ceil(length / WIN_MULLION_STEP)))
        for j in range(div + 1):
            off = -length / 2 + j * length / div
            frames.add_centred(cx + (off if along_x else 0.0), cy + (0.0 if along_x else off),
                               z0 + H / 2, WIN_MULLION, WIN_MULLION, H)
        if along_x:
            panes.add_centred(cx, cy, z0 + H / 2, length, WIN_PANE_T, H - 0.05)
        else:
            panes.add_centred(cx, cy, z0 + H / 2, WIN_PANE_T, length, H - 0.05)
        n += 1
    frames.to_object("%s.windowFrames" % key, coll, empty, mats["Teak"])
    panes.to_object("%s.windowGlass" % key, coll, empty, mats["Glass"])
    return n


def build_door_heads(key, empty, coll, mats, openings):
    """Heads over doors and (per GAP_HEADS) other wall gaps; slivers filled full height."""
    if not openings:
        return 0, 0, 0
    fl = openings.get("floors", {}).get(key, {})
    doors = fl.get("doors", [])
    bm = BoxMesh()
    for d in doors:
        bm.add_three(d["x0"], d["x1"], d["z0"], d["z1"], DOOR_HEAD, WALL_H)
    bm.to_object("%s.doorHeads" % key, coll, empty, mats["Lime White"])

    gaps = [g for g in fl.get("gaps", [])
            if GAP_HEADS == "all" or (GAP_HEADS == "perimeter" and g.get("perimeter"))]
    gm = BoxMesh()
    for g in gaps:
        gm.add_three(g["x0"], g["x1"], g["z0"], g["z1"], DOOR_HEAD, WALL_H)
    gm.to_object("%s.gapHeads" % key, coll, empty, mats["Lime White"])

    slivers = fl.get("slivers", []) if FILL_SLIVERS else []
    sm = BoxMesh()
    for g in slivers:
        sm.add_three(g["x0"], g["x1"], g["z0"], g["z1"], 0.0, WALL_H)
    sm.to_object("%s.sliverFill" % key, coll, empty, mats["Lime White"])
    return len(doors), len(gaps), len(slivers)


# =============================================================================
# Plinth, compound wall, gates, steps
# =============================================================================

def slat_gate(steel, ax, az, bx, bz, y, h, slats):
    """details.js slatGate() for an axis-aligned leaf, Three.js plan coords."""
    along_z = abs(bx - ax) < 1e-6
    length = abs(bz - az) if along_z else abs(bx - ax)
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    sx, sz = (0.015, length) if along_z else (length, 0.015)
    for i in range(slats):
        yb = y + 0.04 + i * (h - 0.06) / slats
        steel.add_three(mx - sx / 2, mx + sx / 2, mz - sz / 2, mz + sz / 2, yb, yb + 0.032)
    for (px, pz) in ((ax, az), (bx, bz)):
        steel.add_three(px - 0.012, px + 0.012, pz - 0.012, pz + 0.012, y + 0.02, y + h)


def build_site_works(empties, colls, site, mats):
    g = FLOORS["ground"]
    hw, hd = g["width"] / 2, g["depth"] / 2
    street = -g["level"]                      # street level in ground-floor-local units
    G, Gc = empties["ground"], colls["ground"]

    skirt = BoxMesh()
    for (w, d, x, z) in SKIRTS:
        skirt.add_three(x - w / 2, x + w / 2, z - d / 2, z + d / 2, street, -SLAB_T)
    skirt.to_object("ground.plinthSkirt", Gc, G, mats["Lime White Shade"])

    steps = BoxMesh()
    for i in range(STEP_COUNT):
        z = STEP_Z0 + i * STEP_DZ
        steps.add_three(STEP_X - STEP_W / 2, STEP_X + STEP_W / 2, z - STEP_D / 2, z + STEP_D / 2,
                        street, street + (g["level"] - i * STEP_RISE))
    steps.to_object("ground.gateSteps", Gc, G, mats["Sandstone"])

    plaster, trim, steel = BoxMesh(), BoxMesh(), BoxMesh()
    zf = hd - GATE_Z_INSET
    gx0, gx1 = -hw + 0.05, GATE_PIER_X1
    pw, ph, pd = GATE_PIER
    cw, ch, cd = GATE_PIER_CAP
    for x in (gx0, gx1):
        plaster.add_three(x - pw / 2, x + pw / 2, zf - pd / 2, zf + pd / 2, 0.0, ph)
        trim.add_three(x - cw / 2, x + cw / 2, zf - cd / 2, zf + cd / 2, ph, ph + ch)
    slat_gate(steel, gx1 - 0.08, zf - 0.03, gx1 - 0.08, zf - 0.6, 0.0, GATE_H, GATE_SLATS)
    for (x0, x1) in spans(gx1 + 0.06, hw - 0.02, cuts_at_z(SLAB_VOIDS["ground"], zf, 0.06)):
        if x1 - x0 < 0.1:
            continue
        t, ct = FRONT_WALL_T / 2, FRONT_COPING_T / 2
        plaster.add_three(x0, x1, zf - t, zf + t, 0.0, FRONT_WALL_H)
        trim.add_three(x0 - 0.01, x1 + 0.01, zf - ct, zf + ct, FRONT_WALL_H, FRONT_WALL_H + FRONT_COPING_H)
    plaster.to_object("ground.frontWall", Gc, G, mats["Lime White"])
    trim.to_object("ground.copings", Gc, G, mats["Lime White Shade"])
    steel.to_object("ground.streetGate", Gc, G, mats["Charcoal Steel"])

    # Office gate at the plot's front-right, on the street (not on the ground floor).
    units = bpy.data.objects.new("Site.Units", None)   # model-unit frame at street level
    units.empty_display_type = "PLAIN_AXES"
    units.scale = (UNIT_M, UNIT_M, UNIT_M)
    site.objects.link(units)
    ox, oz = g["offset"]
    px1, pz1 = ox + hw, oz + hd
    office = BoxMesh()
    slat_gate(office, px1 - 0.12, pz1 - 0.03, px1 - 0.12, pz1 - 0.45, 0.0, GATE_H, OFFICE_GATE_SLATS)
    office.to_object("Site.OfficeGate", site, units, mats["Charcoal Steel"])


# =============================================================================
# Build
# =============================================================================

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    try:
        scene.unit_settings.system = "METRIC"
        scene.unit_settings.scale_length = 1.0
    except Exception as e:
        warn("unit settings: %s" % e)

    root = scene.collection
    house = get_collection("House", root)
    colls = {k: get_collection(COLLECTION_FOR[k], house) for k in FLOOR_ORDER}
    roof_coll = get_collection("Roof", house)
    site = get_collection("Site", root)
    detail = get_collection("Detail", root)
    detail.hide_viewport = True
    detail.hide_render = True

    mats = build_materials()

    empties = {}
    for key in FLOOR_ORDER:
        empties[key] = import_floor(key, colls[key], detail, mats)

    # Floor slabs (top at the Empty origin, hanging below)
    for key in FLOOR_ORDER:
        s = FLOORS[key]
        hw, hd = s["width"] / 2, s["depth"] / 2
        voids = [three_rect_to_blender(v) for v in SLAB_VOIDS[key]]
        add_slab("%s.slab" % key, (-hw, hw, -hd, hd), voids, 0.0, SLAB_T,
                 colls[key], empties[key], mats["Terrazzo"], side_mat=mats["Lime White"])

    # Close the full-height window and door slots above each opening
    openings = load_openings()
    for key in FLOOR_ORDER:
        nw = build_windows(key, empties[key], colls[key], mats)
        nd, ng, ns = build_door_heads(key, empties[key], colls[key], mats, openings)
        info("%s: %d windows framed, %d door heads, %d gap heads, %d slivers filled"
             % (key, nw, nd, ng, ns))
    build_site_works(empties, colls, site, mats)

    # Details from blender/details/ (see DETAILS.md). Each is its own module.
    detail_views = []
    detail_ctx = None
    try:
        if SCRIPT_DIR not in sys.path:
            sys.path.insert(0, SCRIPT_DIR)
        import details as detail_modules
        detail_ctx = dict(
            scene=scene, mats=mats, empties=empties, colls=colls, site=site, house=house,
            roof_coll=roof_coll,
            helpers=dict(add_box=add_box, add_slab=add_slab, get_collection=get_collection,
                         set_parent=set_parent, three_rect_to_blender=three_rect_to_blender,
                         new_material=new_material, link_only=link_only, info=info, warn=warn),
            constants=dict(UNIT_M=UNIT_M, SLAB_T=SLAB_T, STOREY=STOREY, WALL_H=WALL_H,
                           FLOORS=FLOORS, PARAPET_H=PARAPET_H, PARAPET_T=PARAPET_T,
                           TERRACE_X1=TERRACE_X1, SLAB_VOIDS=SLAB_VOIDS),
        )
        detail_views = detail_modules.build_all(detail_ctx) or []
    except Exception as e:
        warn("details package failed: %s" % e)

    # Finish planes
    fin_t = FINISH_T_M / UNIT_M
    for key, name, rect, mname in FINISHES:
        voids = [three_rect_to_blender(v) for v in SLAB_VOIDS[key]]
        add_slab("%s.%s" % (key, name), three_rect_to_blender(rect), voids,
                 fin_t, fin_t, colls[key], empties[key], mats[mname])

    # Second floor: terrace floor + terrace parapet
    sec = FLOORS["second"]
    shw, shd = sec["width"] / 2, sec["depth"] / 2
    tx0, tx1 = -shw, TERRACE_X1
    t = PARAPET_T
    sec_voids = [three_rect_to_blender(v) for v in SLAB_VOIDS["second"]]
    add_slab("second.Terrace.Terracotta", (tx0, tx1, -shd, shd), sec_voids,
             fin_t, fin_t, colls["second"], empties["second"], mats["Terracotta"])
    lw = mats["Lime White"]
    add_box("second.TerraceParapet.W", tx0, tx0 + t, -shd, shd, 0.0, PARAPET_H,
            colls["second"], empties["second"], lw)
    add_box("second.TerraceParapet.S", tx0 + t, tx1, -shd, -shd + t, 0.0, PARAPET_H,
            colls["second"], empties["second"], lw)
    add_box("second.TerraceParapet.N", tx0 + t, tx1, shd - t, shd, 0.0, PARAPET_H,
            colls["second"], empties["second"], lw)

    # Roof: Empty at the roof slab underside, child of Floor.second (in units)
    roof = bpy.data.objects.new("Floor.roof", None)
    roof.empty_display_type = "PLAIN_AXES"
    roof_coll.objects.link(roof)
    set_parent(roof, empties["second"])
    roof.location = (0.0, 0.0, ROOF_UNDERSIDE)
    rx0, rx1 = TERRACE_X1, shw
    roof_voids = [three_rect_to_blender(v) for v in ROOF_VOIDS]
    add_slab("roof.slab", (rx0, rx1, -shd, shd), roof_voids, SLAB_T, SLAB_T,
             roof_coll, roof, lw)
    z0, z1 = SLAB_T, SLAB_T + PARAPET_H
    add_box("roof.Parapet.S", rx0, rx1, -shd, -shd + t, z0, z1, roof_coll, roof, lw)
    add_box("roof.Parapet.N", rx0, rx1, shd - t, shd, z0, z1, roof_coll, roof, lw)
    add_box("roof.Parapet.W", rx0, rx0 + t, -shd + t, shd - t, z0, z1, roof_coll, roof, lw)
    add_box("roof.Parapet.E", rx1 - t, rx1, -shd + t, shd - t, z0, z1, roof_coll, roof, lw)

    # Ground disc at street level
    n = GROUND_SEGMENTS
    verts = [(GROUND_RADIUS_M * math.cos(2 * math.pi * i / n),
              GROUND_RADIUS_M * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    me = bpy.data.meshes.new("Site.Street")
    me.from_pydata(verts, [], [list(range(n))])
    me.update()
    street = bpy.data.objects.new("Site.Street", me)
    site.objects.link(street)
    me.materials.append(mats["Asphalt"])

    if detail_ctx is not None:
        detail_modules.finish_all(detail_ctx)

    house_bbox = compute_house_bbox()
    world = build_world(scene)
    fog = build_fog(scene, site, world)
    sun = build_sun(site)
    cam = build_camera(scene, site, house_bbox)
    cam_angle = build_angle_camera(site)
    cam_top = build_top_camera(site, house_bbox)
    scene.camera = cam
    setup_render(scene, world)
    views = [
        ("01-dawn", cam, RENDER_PATH, []),
        ("02-angle", cam_angle, RENDER_ANGLE_PATH, []),
        # Plan view: no roof, haze or low sun, and no heads, so openings read.
        ("03-top", cam_top, RENDER_TOP_PATH,
         [roof_coll, sun] + ([fog] if fog is not None else [])
         + [o for o in bpy.data.objects
            if o.name.endswith((".doorHeads", ".windowHeads", ".gapHeads"))]),
    ]
    views.extend(detail_views)
    return scene, cam, sun, house_bbox, views


def compute_house_bbox():
    xs, ys = [], []
    for key, s in FLOORS.items():
        ox, oz = s["offset"]
        xs += [(ox - s["width"] / 2) * UNIT_M, (ox + s["width"] / 2) * UNIT_M]
        ys += [-(oz + s["depth"] / 2) * UNIT_M, -(oz - s["depth"] / 2) * UNIT_M]
    top = (FLOORS["second"]["level"] + ROOF_UNDERSIDE + SLAB_T + PARAPET_H) * UNIT_M
    return dict(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys), z0=0.0, z1=top)


def build_world(scene):
    world = bpy.data.worlds.new("Dawn")
    scene.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (500, 0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (250, 0)
    bg.inputs["Strength"].default_value = WORLD_STRENGTH
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-600, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-400, 0)
    r = ramp(nt, [(0.0, hex_to_linear(SKY_HORIZON)),
                  (SKY_GRADIENT_TOP, hex_to_linear(SKY_ZENITH))])
    # Generated coords on the world are the view direction; Z = sin(elevation).
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    try:
        ms = world.mist_settings
        ms.start = MIST_START_M
        ms.depth = MIST_DEPTH_M
        ms.falloff = "QUADRATIC"
    except Exception as e:
        warn("mist settings: %s" % e)
    return world


def scatter_node(nt):
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Color"].default_value = hex_to_linear(FOG_COLOR)
    vs.inputs["Density"].default_value = FOG_DENSITY
    vs.inputs["Anisotropy"].default_value = FOG_ANISOTROPY
    return vs


def build_fog(scene, site, world):
    try:
        if FOG_MODE == "world":
            nt = world.node_tree
            out = [n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputWorld"][0]
            vs = scatter_node(nt)
            vs.location = (250, -250)
            nt.links.new(vs.outputs["Volume"], out.inputs["Volume"])
            return None
        mat = bpy.data.materials.new("Fog")
        try:
            mat.use_nodes = True
        except Exception:
            pass
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (300, 0)
        vs = scatter_node(nt)
        nt.links.new(vs.outputs["Volume"], out.inputs["Volume"])
        sx, sy, sz = FOG_BOX_SIZE_M
        box = add_box("Site.FogVolume", -sx / 2, sx / 2, -sy / 2, sy / 2,
                      FOG_BOX_Z0_M, FOG_BOX_Z0_M + sz, site, None, mat)
        box.display_type = "WIRE"
        box.hide_select = True
        return box
    except Exception as e:
        warn("fog setup failed: %s" % e)
        return None


def build_sun(site):
    ld = bpy.data.lights.new("Sun.Dawn", type="SUN")
    ld.color = hex_to_linear(SUN_COLOR)[:3]
    ld.energy = SUN_STRENGTH
    try:
        ld.angle = math.radians(SUN_ANGLE_DEG)
    except Exception as e:
        warn("sun angle: %s" % e)
    sun = bpy.data.objects.new("Sun.Dawn", ld)
    site.objects.link(sun)
    el, az = math.radians(SUN_ELEVATION_DEG), math.radians(SUN_AZIMUTH_DEG)
    to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    sun.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
    sun.location = to_sun * 30.0
    return sun


def build_camera(scene, site, bb):
    cd = bpy.data.cameras.new("Camera.Street")
    cd.lens = CAM_LENS_MM
    cd.sensor_width = CAM_SENSOR_MM
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.1
    cd.clip_end = 1000.0
    cam = bpy.data.objects.new("Camera.Street", cd)
    site.objects.link(cam)
    scene.camera = cam

    cx, cy = (bb["x0"] + bb["x1"]) / 2, (bb["y0"] + bb["y1"]) / 2
    w, h = bb["x1"] - bb["x0"], bb["z1"] - bb["z0"]
    aspect = RES_X / RES_Y
    per_m_w = CAM_SENSOR_MM / CAM_LENS_MM      # frame width per metre of distance
    per_m_h = per_m_w / aspect
    if CAM_DISTANCE_M is not None:
        cam_y = cy - CAM_DISTANCE_M
    else:
        d_front = max(w / (CAM_FILL * per_m_w), h / (CAM_FILL * per_m_h))
        cam_y = bb["y0"] - d_front
    limit = GROUND_RADIUS_M - CAM_MIN_EDGE_MARGIN_M
    if math.hypot(cx, cam_y) > limit:
        warn("camera clamped to stay %.1f m inside the ground disc" % CAM_MIN_EDGE_MARGIN_M)
        cam_y = -math.sqrt(max(limit ** 2 - cx ** 2, 0.0))
    cam.location = (cx, cam_y, CAM_HEIGHT_M)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)  # level, looking +Y

    aim_z = CAM_AIM_Z_M if CAM_AIM_Z_M is not None else (bb["z0"] + bb["z1"]) / 2
    horiz = cy - cam_y
    cd.shift_y = (aim_z - CAM_HEIGHT_M) / horiz * CAM_LENS_MM / CAM_SENSOR_MM
    cam["aim_z_m"] = aim_z
    cam["distance_to_house_centre_m"] = horiz
    return cam


def build_angle_camera(site):
    cd = bpy.data.cameras.new("Camera.Angle")
    cd.lens = ANGLE_LENS_MM
    cd.sensor_width = CAM_SENSOR_MM
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.1
    cd.clip_end = 1000.0
    cam = bpy.data.objects.new("Camera.Angle", cd)
    site.objects.link(cam)
    cam.location = ANGLE_CAM_M
    d = Vector(ANGLE_TARGET_M) - Vector(ANGLE_CAM_M)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def build_top_camera(site, bb):
    cd = bpy.data.cameras.new("Camera.Top")
    cd.type = "ORTHO"
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.1
    cd.clip_end = 500.0
    cam = bpy.data.objects.new("Camera.Top", cd)
    site.objects.link(cam)
    # include the gate steps beyond the front edge
    y0 = bb["y0"] - (STEP_Z0 + STEP_COUNT * STEP_DZ - FLOORS["ground"]["depth"] / 2) * UNIT_M
    cx, cy = (bb["x0"] + bb["x1"]) / 2, (y0 + bb["y1"]) / 2
    ex, ey = bb["x1"] - bb["x0"], bb["y1"] - y0
    rotated = abs(round(TOP_ROTATE_DEG / 90.0)) % 2 == 1
    fw, fh = (ey, ex) if rotated else (ex, ey)        # extents across frame width / height
    cd.ortho_scale = max(fw, fh * RES_X / RES_Y) * TOP_MARGIN
    cam.location = (cx, cy, TOP_CAM_Z_M)
    cam.rotation_euler = (0.0, 0.0, math.radians(TOP_ROTATE_DEG))
    return cam


def setup_render(scene, world):
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    cy = scene.cycles
    cy.samples = SAMPLES
    try:
        cy.use_denoising = True
    except Exception as e:
        warn("denoising: %s" % e)
    try:
        cy.volume_bounces = 1
    except Exception as e:
        warn("volume bounces: %s" % e)

    # GPU (Metal) with CPU fallback
    device = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        try:
            prefs.refresh_devices()
        except Exception:
            prefs.get_devices()
        gpus = sum(1 for d in prefs.devices if d.type != "CPU")
        for d in prefs.devices:
            d.use = (d.type != "CPU") if gpus else True  # GPU only when available
        if gpus:
            device = "GPU"
    except Exception as e:
        warn("Metal GPU setup failed, using CPU (%s)" % e)
    try:
        cy.device = device
    except Exception as e:
        warn("cycles device: %s" % e)
        device = "CPU"
    info("Cycles device: %s" % device)

    vs = scene.view_settings
    try:
        vs.view_transform = VIEW_TRANSFORM
    except Exception as e:
        warn("view transform %s: %s" % (VIEW_TRANSFORM, e))
    vs.exposure = EXPOSURE
    vs.gamma = 1.0

    try:
        bpy.context.view_layer.use_pass_mist = True
    except Exception as e:
        warn("mist pass: %s" % e)

    im = scene.render.image_settings
    try:
        im.media_type = "IMAGE"  # 5.x
    except Exception:
        pass
    try:
        im.file_format = "PNG"
        im.color_mode = "RGB"
        im.color_depth = "8"
    except Exception as e:
        warn("image settings: %s" % e)
    scene.render.filepath = RENDER_PATH


def render_views(scene, views):
    if QUICK:
        scene.cycles.samples = QUICK_SAMPLES
        scene.render.resolution_percentage = QUICK_PERCENT
    info("rendering %d samples at %d%% of %dx%d ..."
         % (scene.cycles.samples, scene.render.resolution_percentage, RES_X, RES_Y))
    for name, cam, path, hidden in views:
        saved = [(h, h.hide_render) for h in hidden]
        try:
            for h in hidden:
                h.hide_render = True
            scene.camera = cam
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            info("wrote %s" % path)
        except Exception as e:
            warn("render %s failed: %s" % (name, e))
        finally:
            for h, v in saved:
                h.hide_render = v
    scene.camera = views[0][1]


def summary(scene, cam, sun, bb):
    info("---- summary ----")
    for c in bpy.data.collections:
        info("collection %-10s %3d objects" % (c.name, len(c.all_objects)))
    info("house bbox (m): x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f"
         % (bb["x0"], bb["x1"], bb["y0"], bb["y1"], bb["z0"], bb["z1"]))
    loc = cam.location
    info("camera at (%.2f, %.2f, %.2f), %.1f m from house centre, aim z %.2f m, shift_y %.3f"
         % (loc.x, loc.y, loc.z, cam["distance_to_house_centre_m"], cam["aim_z_m"],
            cam.data.shift_y))
    info("fog mode: %s" % FOG_MODE)
    info("blend:  %s" % BLEND_PATH)
    info("renders: %s" % ("skipped (--no-render)" if NO_RENDER else
                          ", ".join((RENDER_PATH, RENDER_ANGLE_PATH, RENDER_TOP_PATH))
                          + (" (quick)" if QUICK else "")))


def main():
    scene, cam, sun, bb, views = build()
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, relative_remap=True)
    info("saved %s" % BLEND_PATH)
    summary(scene, cam, sun, bb)
    if not NO_RENDER:
        render_views(scene, views)


main()
