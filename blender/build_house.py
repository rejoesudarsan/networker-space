"""
build_house.py -- headless Blender build of the Space house.

Builds the four floors from the site's glTF exports, closes the cutaway
openings, adds slabs, roof, facade depth (reveals, window boxes, cladding,
copings, terrace railing), the street compound wall and gates, CC0 image
textures, two gulmohar-style trees, HDRI dawn light with compositor fog, and
three cameras. Saves blender/space-house.blend, renders three views and writes
side-by-side / overlay comparisons of the street view against board 01.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py -- --quick
  options after "--":  --quick (32 samples, 50 %)   --no-render (build + save only)

Assets: python3 blender/fetch_assets.py downloads the CC0 HDRI, textures and
tree into blender/assets/ (see assets/LICENSES.md). Without them the script
falls back to procedural materials, a gradient sky and no trees.

Target: Blender 5.2 LTS. Scene units are metres. Everything that belongs to a
floor is parented to an Empty "Floor.<name>" whose scale is UNIT_M, so the
children are authored in model units (1 unit = 8 ft) and the floors can be
moved later for a cutaway animation.

Axis convention: Three.js (x, y, z) -> Blender (x, -z, y). +X = east,
+Y = north, so the street (Three.js +Z) is on the Blender -Y (south) side.
"""

import json
import math
import os
import re
import sys

import bpy
from mathutils import Matrix, Vector

try:
    import bmesh
except Exception:  # pragma: no cover - always present inside Blender
    bmesh = None
try:
    import numpy as np
except Exception:  # pragma: no cover - ships with Blender
    np = None

# =============================================================================
# CONSTANTS
# =============================================================================

REPO_FALLBACK = "/Users/rejoesudarsan/Dev/networker-space"

UNIT_M = 2.4384              # 1 model unit = 8 ft = 2.4384 m
SLAB_T = 0.14583             # slab thickness, units (0.3556 m)
STOREY = 1.45                # storey height, units (3.535 m)
WALL_H_GLB = 0.5625          # cutaway wall height baked into the GLB, units
COL_H_GLB = 0.5625 + 6 / 96  # column height in the GLB, units (0.625)
WALL_H = STOREY - SLAB_T     # walls meet the slab above (spec 1.30)
M = 1.0 / UNIT_M             # one metre in model units

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
               (1.25, 3.27, 3.12, 5.01),     # notch from front edge (office court)
               (-1.85, 3.2, -0.2, 5.01)],    # notch from front edge (parking ramp)
    "first": [],
    "second": [(0.18, -0.49, 1.88, 1.06)],   # courtyard void
}
# Slab overhang trims come from openings.json "slabTrim" (extract_openings.mjs):
# cut back to ~30 cm past the wall on front / side edges; deeper overhangs kept.
USE_SLAB_TRIM = True

# Roof / terrace (second-floor-local, units)
TERRACE_X1 = -0.95           # terrace spans x -width/2 .. -0.95, rooms -0.95 .. +width/2
PARAPET_H = 0.30
PARAPET_T = 0.08
ROOF_UNDERSIDE = STOREY - SLAB_T   # roof slab top at +STOREY like a floor slab
ROOF_VOIDS = []
COPING_T = 0.05 * M          # coping thickness
COPING_OVER = 0.03 * M       # coping overhang each side

# Finish planes (floor-local Three.js x0, z0, x1, z1), thickness in metres
FINISH_T_M = 0.02
FINISHES = [
    ("ground", "Living1.Teak",  (0.56, 0.2, 2.4, 3.2),       "Teak"),
    ("ground", "FrontLawn",     (-0.2, 3.3, 1.2, 4.95),      "Foliage"),
    ("ground", "EntranceCourt", (-2.3, -0.3, -1.55, 1.3),    "Red Oxide"),
]

# Openings (floor-local units)
SILL_H = 22 / 96             # sill top (the GLB "sills" mesh is 0..SILL_H)
WINDOW_H = 0.86              # window height above the sill (site/src/world/windows.js)
WINDOW_HEAD = SILL_H + WINDOW_H
SILL_MATERIAL = "Lime White"
DOOR_HEAD = 84 / 96          # 7 ft
WIN_MIN_LEN = 0.18           # windows.js island filter: skip shorter ...
WIN_MAX_WIDTH = 0.20         # ... or broader (curved / area) islands
WIN_FRAME = 0.035
WIN_RAIL_H = 0.036
WIN_MULLION = 0.025
WIN_MULLION_STEP = 0.42
WIN_PANE_T = 0.012
WIN_REVEAL = 0.15 * M        # frames + glass set back from the outer wall face
OPENINGS_JSON = "data/openings.json"
GAP_HEADS = "all"            # "all" | "perimeter" | "none"
FILL_SLIVERS = True

# ---- PROVISIONAL facade depth (board 01 / p03 / p19); correct positions here ----
# Front (street) face of every floor, ground-frame Three.js z (walls end here).
FRONT_FACE_Z = 3.314
# Window boxes: plaster frame projecting around each street window.
WINDOW_BOXES = True
WINDOW_BOX_FLOORS = ("ground", "first", "second")
WINDOW_BOX_FRONT_TOL = 0.8   # a window counts as "street" if its outer face is within this of the floor's front
WINDOW_BOX_MIN_LEN = 0.25    # skip narrow windows
WINDOW_BOX_DEPTH = 0.40 * M  # projection from the wall face
WINDOW_BOX_T = 0.10 * M      # frame thickness
SUNSHADE_T = 0.05 * M
SUNSHADE_EXTRA = 0.20 * M    # sunshade projects this much past the box
# Grey stone cladding: strips (floor, ground-frame x0, x1, bottom, top in floor-local units)
CLADDING_STRIPS = [
    ("first", 0.25, 1.25, -SLAB_T, STOREY),            # wall between the centre and right street windows
    ("second", 0.25, 0.50, -SLAB_T, STOREY + PARAPET_H),  # up to the roof parapet, left of the grey window box
]
# Deep grey box around a street window (floor, window centre x in ground frame): ring from
# the floor's front face back to the window, replaces that window's plaster box.
CLADDING_BOXES = [("second", 1.125)]
CLADDING_RING_T = 0.30 * M
CLADDING_T = 0.03 * M        # panel thickness proud of the wall
CLADDING_HEX = "#9C978F"
# Terrace railing (charcoal steel horizontal bars on the terrace parapet)
TERRACE_RAILING = True
RAIL_H = 0.90 * M            # above the parapet coping
RAIL_BARS = (0.30 * M, 0.60 * M, 0.90 * M)
RAIL_BAR = 0.03 * M
RAIL_POST = 0.04 * M
RAIL_POST_STEP = 1.2 * M
# Ground-floor plot boundary wall (west side passage) cut down to a kerb
BOUNDARY_CUT_X = -2.95       # ground-local x; walls west of this are the plot boundary
BOUNDARY_WALL_H = 0.08       # units above the ground-floor slab

# ---- PROVISIONAL street base (board 01, p05, p19); ground-frame Three.js units ----
COMPOUND_Z = 5.85            # centre line of the street compound wall (steps end at ~5.76)
COMPOUND_T = 0.23 * M
COMPOUND_H = 1.50 * M        # above the street
PIER_W = 0.35 * M
PIER_H = 1.65 * M
# Openings along the wall (x0, x1, kind)
COMPOUND_GATES = [
    (-3.10, -2.35, "pedestrian"),   # by the entrance steps (x -2.75)
    (-1.85, -0.20, "vehicle"),      # parking ramp notch
    (1.25, 3.05, "office"),         # office court notch
]
COMPOUND_X0, COMPOUND_X1 = -3.30, 3.25
SIDE_WALL_Z = (5.0, COMPOUND_Z)     # short side returns from the slab edge to the street wall
GATE_H = 1.40 * M
GATE_SLAT_H = 0.075 * M
GATE_SLAT_PITCH = 0.17 * M
GATE_SLAT_T = 0.02 * M
GATE_POST = 0.05 * M
PERGOLA = True                      # concrete canopy over the pedestrian gate (p05, board 01)
PERGOLA_X = (-3.32, -2.12)
PERGOLA_Z = (5.0, COMPOUND_Z + 0.10)
PERGOLA_TOP = 2.65 * M
PERGOLA_SLAB_T = 0.15 * M
PERGOLA_POST = 0.25 * M

# Plinth skirt: ground-floor-local Three.js (w, d, x, z) from site/src/world/world.js
SKIRTS = [
    (1.275, 0.06, -2.4875, 4.97),
    (1.45, 0.06, 0.525, 4.97),
    (6.25, 0.06, 0.0, -4.97),
    (0.06, 10.0, -3.1, 0.0),
    (0.06, 9.45, 3.1, -0.275),
]
STEP_X, STEP_W, STEP_D, STEP_Z0, STEP_DZ, STEP_RISE, STEP_COUNT = -2.75, 0.8, 0.22, 5.05, 0.2, 0.18, 4

# Bevels
BEVEL = True
BEVEL_M = 0.015
BEVEL_SEGMENTS = 2
BEVEL_ANGLE_DEG = 30.0

# Site
GROUND_RADIUS_M = 150.0
GROUND_SEGMENTS = 192
# Street dissolves into fog: fade from FADE_Y0 to FADE_Y1 (metres, toward the house)
# and beyond |x| FADE_X0..FADE_X1.
STREET_FADE_Y = (-19.0, -13.5)
STREET_FADE_X = (11.0, 22.0)

# Palette: name -> (hex, roughness, metallic) -- board 08
PALETTE = {
    "Lime White":       ("#E8E4DA", 0.90, 0.0),
    "Lime White Shade": ("#DEDAD1", 0.90, 0.0),
    "Teak":             ("#805238", 0.45, 0.0),
    "Terrazzo":         ("#CBC4B5", 0.35, 0.0),
    "Sandstone":        ("#B3A68B", 0.80, 0.0),
    "Terracotta":       ("#B66E51", 0.85, 0.0),
    "Red Oxide":        ("#884B45", 0.30, 0.0),
    "Charcoal Steel":   ("#383B3A", 0.40, 0.8),
    "Foliage":          ("#59634D", 0.70, 0.0),
    "Asphalt":          ("#4A4846", 0.90, 0.0),
    "Cladding":         (CLADDING_HEX, 0.80, 0.0),
}
# material -> (texture key in assets/manifest.json, normal strength, pull toward flat palette)
TEXTURED = {
    "Lime White":       ("plaster", 0.8, 0.10),
    "Lime White Shade": ("plaster", 0.8, 0.10),
    "Teak":             ("teak", 0.4, 0.10),
    "Cladding":         ("cladding", 0.8, 0.10),
    "Sandstone":        ("sandstone", 0.6, 0.15),
    "Terracotta":       ("terracotta", 0.6, 0.10),
    "Asphalt":          ("asphalt", 0.6, 0.10),
    "Charcoal Steel":   ("steel", 0.3, 0.20),
}
USE_TEXTURES = True
TERRAZZO_CHIPS = ("#A89E8E", "#DCD6C9")
TERRACOTTA_GROUT = "#8F5A42"
LIME_BUMP_SCALE = 80.0
LIME_BUMP_STRENGTH = 0.05
BRICK_TILE_M = 0.30

# Dawn light
SKY_HORIZON = "#E9C9C0"      # camera-ray sky (board 01)
SKY_ZENITH = "#CFC6D3"
SKY_GRADIENT_TOP = 0.32      # sin(elevation) where the zenith colour is reached (~frame top)
SKY_CAMERA_STRENGTH = 1.0
HDRI_STRENGTH = 1.2          # lighting-only world; bryanston gives ~1.4-2.6 W/m2 on vertical faces at 1.0
HDRI_TINT = "#E9C9C0"
HDRI_TINT_AMOUNT = 0.6
HDRI_ROTATION_DEG = 156.5    # turns the HDRI sun (NW in the file) to SUN_AZIMUTH_DEG
SUN_COLOR = "#FFC394"
SUN_STRENGTH = 1.5
SUN_ANGLE_DEG = 3.0
SUN_ELEVATION_DEG = 8.0
SUN_AZIMUTH_DEG = 112.5      # clockwise from north (+Y): east-south-east

# Fog: 'compositor' (Mist pass mixed toward FOG_COLOR; sky kept), 'domain' (volume box),
# 'world' (world volume)
FOG_MODE = "compositor"
FOG_COLOR = "#D1BFC2"
MIST_START_M = 12.0          # street camera is ~47 m from the street wall, ~54 m from the facade
MIST_DEPTH_M = 110.0
MIST_FALLOFF = "LINEAR"
FOG_AMOUNT = 0.70            # max mix toward the fog colour (facade gets ~0.27)
FOG_EMISSION_STRENGTH = 1.0  # faded street = emissive fog colour (match SKY_CAMERA_STRENGTH)
FOG_DENSITY = 0.005          # 'domain' / 'world' modes
FOG_ANISOTROPY = 0.3
FOG_BOX_SIZE_M = (200.0, 200.0, 60.0)
FOG_BOX_Z0_M = -5.0

# Trees (PROVISIONAL positions, ground-frame Three.js x, z; on the street outside the wall)
TREES = True
TREE_POSITIONS = [(-4.2, 6.6, 20.0), (4.6, 6.6, 200.0)]   # x, z, rotation deg
TREE_HEIGHT_M = 9.0
FLOWER_COUNT = 900
FLOWER_COLORS = ("#E2502B", "#C8381F", "#F06A32")
FLOWER_RADIUS = (0.16, 0.30)  # metres at final size

# Street camera: frontal elevation framed like board 01
CAM_LENS_MM = 50.0
CAM_SENSOR_MM = 36.0
CAM_HEIGHT_M = 1.7
BOARD_TOP_FRAC = 0.26        # roof top at 26 % from the top of the frame
BOARD_BASE_FRAC = 0.78       # compound-wall base at 78 %
CAM_DISTANCE_M = None        # force a distance from the house centre (disables the fit)

# Extra views
ANGLE_LENS_MM = 35.0
ANGLE_CAM_M = (-15.95, -27.85, 1.6)
ANGLE_TARGET_M = (-1.0, -6.0, 6.0)
TOP_CAM_Z_M = 45.0
TOP_MARGIN = 1.12
TOP_ROTATE_DEG = -90.0

# Render
RES_X, RES_Y = 1536, 1024
QUICK_SAMPLES = 32
QUICK_PERCENT = 50
SAMPLES = 256
# 'Khronos PBR Neutral' keeps palette colours close to their hex values (AgX greys them).
VIEW_TRANSFORM = "Khronos PBR Neutral"
VIEW_TRANSFORM_FALLBACK = "AgX"
EXPOSURE = 0.0
BOARD_IMAGE = "reference/art-direction/01-dawn-exterior.png"   # relative to the repo

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
COMPARE_PATH = os.path.join(RENDER_DIR, "01-compare.png")
OVERLAY_PATH = os.path.join(RENDER_DIR, "01-overlay.png")
OPENINGS_PATH = os.path.join(SCRIPT_DIR, OPENINGS_JSON)
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
MANIFEST_PATH = os.path.join(ASSETS_DIR, "manifest.json")
BOARD_PATH = os.path.join(REPO, BOARD_IMAGE)

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NO_RENDER = "--no-render" in ARGS
QUICK = "--quick" in ARGS

# Collected while building; reported in the summary.
PROVISIONAL = []
BEVEL_OBJECTS = []


def warn(msg):
    print("[build_house] WARNING: " + msg)


def info(msg):
    print("[build_house] " + msg)


def provisional(what, where):
    PROVISIONAL.append("%s -- %s" % (what, where))


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


def get_collection(name, parent_coll):
    c = bpy.data.collections.new(name)
    parent_coll.children.link(c)
    return c


def slab_mesh(name, rect, voids, z_top, thickness):
    """Closed prism over rect (x0, x1, y0, y1) minus rectangular voids.

    Built on a grid of every rect/void edge so there are no T-junctions:
    top/bottom quads per kept cell, side quads on boundary edges.
    Returns (mesh, per-face material index: top 0, bottom / sides 1).
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
    return me, mat_idx


def add_slab(name, rect, voids, z_top, thickness, coll, parent, mat, side_mat=None, bevel=False):
    """side_mat: material for the underside and edges (top keeps `mat`)."""
    me, idx = slab_mesh(name, rect, voids, z_top, thickness)
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
    if bevel:
        BEVEL_OBJECTS.append(obj)
    return obj


def add_box(name, x0, x1, y0, y1, z0, z1, coll, parent, mat, bevel=False):
    return add_slab(name, (x0, x1, y0, y1), [], z1, z1 - z0, coll, parent, mat, bevel=bevel)


class BoxMesh:
    """Accumulates axis-aligned boxes into one mesh (floor-local units)."""

    def __init__(self):
        self.verts, self.faces = [], []

    def add(self, x0, x1, y0, y1, z0, z1):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        if x1 - x0 <= 1e-9 or y1 - y0 <= 1e-9 or z1 - z0 <= 1e-9:
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

    def ring_xz(self, x0, x1, z0, z1, y_a, y_b, t):
        """A frame of thickness t around the opening x0..x1 / z0..z1 (Blender), between y_a and y_b."""
        self.add(x0 - t, x1 + t, y_a, y_b, z1, z1 + t)       # head
        self.add(x0 - t, x1 + t, y_a, y_b, z0 - t, z0)       # sill
        self.add(x0 - t, x0, y_a, y_b, z0, z1)               # left
        self.add(x1, x1 + t, y_a, y_b, z0, z1)               # right

    def to_object(self, name, coll, parent, mat, bevel=False):
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
        if bevel:
            BEVEL_OBJECTS.append(obj)
        return obj


def mesh_islands(verts, polys, weld=1e-4):
    """Bounding boxes (x0, x1, y0, y1) of the connected parts of a mesh (windows.js islands())."""
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


def mesh_bounds(me):
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def merge_doubles(me, dist=1e-5):
    """Weld the split glTF vertices so bevels and islands see connected geometry."""
    if bmesh is None:
        return
    try:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
        bm.to_mesh(me)
        bm.free()
        me.update()
    except Exception as e:
        warn("merge doubles on %s: %s" % (me.name, e))


def clip_west_walls(me, cut_x, height):
    """Lower every wall west of cut_x to `height` (plot boundary -> kerb), with a clean step."""
    if bmesh is None:
        return 0
    try:
        bm = bmesh.new()
        bm.from_mesh(me)
        for c in (cut_x, cut_x + 0.002):
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6,
                                   plane_co=(c, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0))
        moved = 0
        for v in bm.verts:
            if v.co.x <= cut_x + 1e-6 and v.co.z > height:
                v.co.z = height
                moved += 1
        bm.to_mesh(me)
        bm.free()
        me.update()
        return moved
    except Exception as e:
        warn("boundary wall clip failed: %s" % e)
        return 0


def box_uv(me, scale_m):
    """Box-projected UVs in metres (dominant normal axis per face) -> 'BoxUV'."""
    if np is None or not me.polygons:
        return
    try:
        nv, nl, npoly = len(me.vertices), len(me.loops), len(me.polygons)
        co = np.empty(nv * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) * scale_m
        lv = np.empty(nl, np.int32)
        me.loops.foreach_get("vertex_index", lv)
        nrm = np.empty(npoly * 3, np.float32)
        me.polygons.foreach_get("normal", nrm)
        nrm = np.abs(nrm.reshape(-1, 3))
        start = np.empty(npoly, np.int32)
        total = np.empty(npoly, np.int32)
        me.polygons.foreach_get("loop_start", start)
        me.polygons.foreach_get("loop_total", total)
        poly_of_loop = np.repeat(np.arange(npoly), total)
        order = np.argsort(np.repeat(start, total) + np.concatenate([np.arange(t) for t in total]))
        poly_of_loop = poly_of_loop[order]
        axis = np.argmax(nrm, axis=1)[poly_of_loop]
        p = co[lv]
        u = np.where(axis == 0, p[:, 1], p[:, 0])
        v = np.where(axis == 2, p[:, 1], p[:, 2])
        uv = me.uv_layers.new(name="BoxUV")
        uv.data.foreach_set("uv", np.stack([u, v], axis=1).ravel().astype(np.float32))
        me.uv_layers.active = uv
    except Exception as e:
        warn("box UV on %s: %s" % (me.name, e))


def add_bevel(obj, scale_m):
    try:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = BEVEL_M / scale_m
        mod.segments = BEVEL_SEGMENTS
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(BEVEL_ANGLE_DEG)
        try:
            mod.use_clamp_overlap = True
            mod.harden_normals = False   # faces stay flat-shaded
        except Exception:
            pass
    except Exception as e:
        warn("bevel on %s: %s" % (obj.name, e))


def sock(sockets, name, stype=None):
    """Socket by name (and type, for multi-type nodes like ShaderNodeMix)."""
    for s in sockets:
        if s.name == name and (stype is None or s.type == stype):
            return s
    raise KeyError(name)


def mix_rgba(nt, blend="MIX", fac=1.0):
    """ShaderNodeMix in colour mode -> (node, factor, a, b, result)."""
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    try:
        n.blend_type = blend
    except Exception as e:
        warn("mix blend %s: %s" % (blend, e))
    f = sock(n.inputs, "Factor", "VALUE")
    f.default_value = fac
    return n, f, sock(n.inputs, "A", "RGBA"), sock(n.inputs, "B", "RGBA"), sock(n.outputs, "Result", "RGBA")


def math_node(nt, op, a=None, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


# =============================================================================
# Materials
# =============================================================================

def load_manifest():
    try:
        with open(MANIFEST_PATH) as f:
            m = json.load(f)
        return m
    except Exception as e:
        warn("no asset manifest (%s): run fetch_assets.py; using procedural materials" % e)
        return {}


def asset_path(rel):
    return os.path.join(SCRIPT_DIR, rel) if rel else None


def new_material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True  # deprecated / implicit in 5.x
    except Exception:
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (150, 0)
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


def load_image(path, non_color=False):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        for name in ("Non-Color", "Generic Data", "Raw"):
            try:
                img.colorspace_settings.name = name
                break
            except Exception:
                continue
    return img


def image_mean(img, srgb):
    """Mean RGB of an image (linear). Byte images expose raw values / 255 via .pixels."""
    if np is None:
        return None
    try:
        n = len(img.pixels)
        buf = np.empty(n, np.float32)
        img.pixels.foreach_get(buf)
        px = buf.reshape(-1, 4)[::7, :3]
        m = px.mean(axis=0)
        if srgb and not img.is_float:
            m = np.array([srgb_to_linear(float(c)) for c in m])
        return [max(float(c), 1e-4) for c in m]
    except Exception as e:
        warn("image stats for %s: %s" % (img.name, e))
        return None


def textured_material(name, entry, hx, rough, metal, normal_strength, pull):
    """Image-texture PBR material on the BoxUV map (metres), tinted to the palette hex."""
    maps = entry.get("maps", {})
    paths = {k: asset_path(v) for k, v in maps.items()}
    if not paths.get("color") or not os.path.isfile(paths["color"]):
        return None
    size = float(entry.get("size_m") or 1.0)
    mat, nt, bsdf = new_material(name)
    target = hex_to_linear(hx)
    try:
        mat.diffuse_color = target
    except Exception:
        pass
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.location = (-1300, 0)
    try:
        uvn.uv_map = "BoxUV"
    except Exception:
        pass
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (-1100, 0)
    mp.inputs["Scale"].default_value = (1.0 / size, 1.0 / size, 1.0)
    nt.links.new(uvn.outputs["UV"], mp.inputs["Vector"])
    vec = mp.outputs["Vector"]

    # colour: tex * (palette / tex mean), then a little pull toward the flat palette colour
    img = load_image(paths["color"])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.location = (-850, 250)
    nt.links.new(vec, tex.inputs["Vector"])
    mean = image_mean(img, srgb=True) or [0.5, 0.5, 0.5]
    mult = [min(max(target[i] / mean[i], 0.2), 4.0) for i in range(3)] + [1.0]
    m1, _f1, a1, b1, r1 = mix_rgba(nt, "MULTIPLY", 1.0)
    m1.location = (-550, 250)
    nt.links.new(tex.outputs["Color"], a1)
    b1.default_value = mult
    m2, _f2, a2, b2, r2 = mix_rgba(nt, "MIX", pull)
    m2.location = (-300, 250)
    nt.links.new(r1, a2)
    b2.default_value = target
    nt.links.new(r2, bsdf.inputs["Base Color"])

    # roughness: map scaled so its mean lands on the palette roughness
    if paths.get("roughness") and os.path.isfile(paths["roughness"]):
        rimg = load_image(paths["roughness"], non_color=True)
        rt = nt.nodes.new("ShaderNodeTexImage")
        rt.image = rimg
        rt.location = (-850, -50)
        nt.links.new(vec, rt.inputs["Vector"])
        rmean = image_mean(rimg, srgb=False) or [rough] * 3
        k = min(max(rough / max(rmean[0], 1e-3), 0.2), 5.0)
        mul = math_node(nt, "MULTIPLY", b=k, clamp=True)
        mul.location = (-550, -50)
        nt.links.new(rt.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = rough

    # normal map (tangent space on the BoxUV map)
    if paths.get("normal") and os.path.isfile(paths["normal"]):
        nimg = load_image(paths["normal"], non_color=True)
        ntx = nt.nodes.new("ShaderNodeTexImage")
        ntx.image = nimg
        ntx.location = (-850, -350)
        nt.links.new(vec, ntx.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (-550, -350)
        try:
            nm.uv_map = "BoxUV"
        except Exception:
            pass
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(ntx.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    # metalness
    if metal > 0 and paths.get("metalness") and os.path.isfile(paths["metalness"]):
        mimg = load_image(paths["metalness"], non_color=True)
        mtx = nt.nodes.new("ShaderNodeTexImage")
        mtx.image = mimg
        mtx.location = (-850, -650)
        nt.links.new(vec, mtx.inputs["Vector"])
        mm = math_node(nt, "MULTIPLY", b=metal, clamp=True)
        nt.links.new(mtx.outputs["Color"], mm.inputs[0])
        nt.links.new(mm.outputs[0], bsdf.inputs["Metallic"])
    else:
        bsdf.inputs["Metallic"].default_value = metal
    return mat


def procedural_material(name, hx, rough, metal):
    mat, nt, bsdf = new_material(name)
    base = hex_to_linear(hx)
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    try:
        mat.diffuse_color = base
    except Exception:
        pass
    try:
        if name.startswith("Lime White") or name == "Cladding":
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
            nt.links.new(vec, wave.inputs["Vector"])
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
        elif name in ("Sandstone", "Red Oxide", "Asphalt"):
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
                brick.offset = 0.0
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
    return mat


def add_street_fade(mat):
    """Street dissolves into the fog: mix the surface toward an emissive fog colour
    beyond STREET_FADE_Y (toward the house) and STREET_FADE_X (sideways)."""
    try:
        nt = mat.node_tree
        out = [n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial"][0]
        surf_link = out.inputs["Surface"].links[0]
        surf = surf_link.from_socket
        tc = nt.nodes.new("ShaderNodeTexCoord")
        tc.location = (-600, -700)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        sep.location = (-400, -700)
        nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])  # disc at origin, metres
        fy = nt.nodes.new("ShaderNodeMapRange")
        fy.location = (-200, -650)
        fy.inputs["From Min"].default_value = STREET_FADE_Y[0]
        fy.inputs["From Max"].default_value = STREET_FADE_Y[1]
        fy.clamp = True
        nt.links.new(sep.outputs["Y"], fy.inputs["Value"])
        ax = math_node(nt, "ABSOLUTE")
        ax.location = (-200, -850)
        nt.links.new(sep.outputs["X"], ax.inputs[0])
        fx = nt.nodes.new("ShaderNodeMapRange")
        fx.location = (0, -850)
        fx.inputs["From Min"].default_value = STREET_FADE_X[0]
        fx.inputs["From Max"].default_value = STREET_FADE_X[1]
        fx.clamp = True
        nt.links.new(ax.outputs[0], fx.inputs["Value"])
        mx = math_node(nt, "MAXIMUM")
        mx.location = (150, -700)
        nt.links.new(fy.outputs["Result"], mx.inputs[0])
        nt.links.new(fx.outputs["Result"], mx.inputs[1])
        sm = math_node(nt, "POWER", b=1.5, clamp=True)   # ease in
        nt.links.new(mx.outputs[0], sm.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission")
        em.location = (150, -450)
        em.inputs["Color"].default_value = hex_to_linear(FOG_COLOR)
        em.inputs["Strength"].default_value = FOG_EMISSION_STRENGTH
        ms = nt.nodes.new("ShaderNodeMixShader")
        ms.location = (350, -200)
        nt.links.remove(surf_link)
        nt.links.new(sm.outputs[0], ms.inputs[0])
        nt.links.new(surf, ms.inputs[1])
        nt.links.new(em.outputs["Emission"], ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs["Surface"])
    except Exception as e:
        warn("street fade: %s" % e)


def build_materials(manifest):
    mats = {}
    textures = manifest.get("textures", {}) if USE_TEXTURES else {}
    for name, (hx, rough, metal) in PALETTE.items():
        mat = None
        if name in TEXTURED and TEXTURED[name][0] in textures:
            key, nstr, pull = TEXTURED[name]
            try:
                mat = textured_material(name, textures[key], hx, rough, metal, nstr, pull)
            except Exception as e:
                warn("textured %s failed (%s); procedural instead" % (name, e))
                mat = None
        if mat is None:
            mat = procedural_material(name, hx, rough, metal)
        mats[name] = mat
    add_street_fade(mats["Asphalt"])
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


def import_gltf(path, flat=False):
    """Import a glTF/GLB; enable the glTF add-on and retry once if the op is missing.
    flat=True asks for flat shading (no custom split normals), so bevels stay clean."""
    if not os.path.isfile(path):
        raise RuntimeError("glTF not found: %s" % path)

    def go():
        if flat:
            try:
                bpy.ops.import_scene.gltf(filepath=path, import_shading="FLAT")
                return
            except TypeError as e:  # option renamed / removed
                warn("glTF import_shading unavailable (%s)" % e)
        bpy.ops.import_scene.gltf(filepath=path)
    try:
        go()
    except (AttributeError, RuntimeError) as e:
        warn("glTF import failed (%s); enabling io_scene_gltf2 and retrying" % e)
        enable_gltf_addon()
        try:
            go()
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
    import_gltf(path, flat=True)
    vl.update()
    new_objs = [o for o in bpy.data.objects if o not in before_obj]
    new_mats = [m for m in bpy.data.materials if m not in before_mat]

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
        if b in ("walls", "columns", "sills") and o.type == "MESH":
            merge_doubles(o.data)
        if b == "walls":
            o.data.transform(Matrix.Diagonal((1.0, 1.0, WALL_H / WALL_H_GLB, 1.0)))
            if key == "ground" and BOUNDARY_WALL_H is not None:
                n = clip_west_walls(o.data, BOUNDARY_CUT_X, BOUNDARY_WALL_H)
                if n:
                    provisional("Ground-floor plot boundary wall cut to a %.2f m kerb" % (BOUNDARY_WALL_H * UNIT_M),
                                "walls west of ground-local x %.2f (the side-passage boundary)" % BOUNDARY_CUT_X)
            o.data.materials.append(mats["Lime White"])
            link_only(o, coll)
            BEVEL_OBJECTS.append(o)
        elif b == "columns":
            o.data.transform(Matrix.Diagonal((1.0, 1.0, WALL_H / COL_H_GLB, 1.0)))
            o.data.materials.append(mats["Lime White"])
            link_only(o, coll)
            BEVEL_OBJECTS.append(o)
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
# Openings: window heads, frames, glass, boxes; door heads
# =============================================================================

def load_openings():
    try:
        with open(OPENINGS_PATH) as f:
            return json.load(f)
    except Exception as e:
        warn("no openings data (%s): run extract_openings.mjs; doors stay full height" % e)
        return None


def front_y(key):
    """Blender floor-local y of the street face (Three.js z = FRONT_FACE_Z in the ground frame)."""
    return -(FRONT_FACE_Z - FLOORS[key]["offset"][1])


def is_cladding_box(key, cx_local):
    ox = FLOORS[key]["offset"][0]
    return any(f == key and abs(cx_local + ox - xg) < 0.15 for f, xg in CLADDING_BOXES)


def build_windows(key, empty, coll, mats, openings=None):
    """Head block over every sill; frames + glass set back WIN_REVEAL from the outer face;
    plaster window boxes (and grey cladding boxes) around street windows."""
    sills = bpy.data.objects.get("%s.sills" % key)
    walls = bpy.data.objects.get("%s.walls" % key)
    if sills is None or sills.type != "MESH":
        warn("%s: no sills mesh; windows skipped" % key)
        return 0, 0
    head_me = sills.data.copy()
    head_me.name = "%s.windowHeads" % key
    k = (WALL_H - WINDOW_HEAD) / SILL_H
    head_me.transform(Matrix.Translation((0.0, 0.0, WINDOW_HEAD)) @ Matrix.Diagonal((1.0, 1.0, k, 1.0)))
    head_me.materials.clear()
    head_me.materials.append(mats["Lime White"])
    head = bpy.data.objects.new(head_me.name, head_me)
    coll.objects.link(head)
    set_parent(head, empty)
    BEVEL_OBJECTS.append(head)

    wb = mesh_bounds(walls.data) if walls is not None else None
    cxw = (wb[0] + wb[1]) / 2 if wb else 0.0
    cyw = (wb[2] + wb[3]) / 2 if wb else 0.0
    yf = front_y(key)

    # Window strips: the extractor's sill polygons (corner windows stay separate there);
    # fall back to welded mesh islands like windows.js.
    jw = (openings or {}).get("floors", {}).get(key, {}).get("windows")
    if jw:
        islands = [three_rect_to_blender((w["x0"], w["z0"], w["x1"], w["z1"])) for w in jw]
    else:
        verts = [v.co[:] for v in sills.data.vertices]
        polys = [p.vertices[:] for p in sills.data.polygons]
        islands = mesh_islands(verts, polys)
    frames, panes, boxes, clad = BoxMesh(), BoxMesh(), BoxMesh(), BoxMesh()
    n = nb = 0
    H, z0 = WINDOW_H, SILL_H
    for (x0, x1, y0, y1) in islands:
        sx, sy = x1 - x0, y1 - y0
        along_x = sx > sy
        length = max(sx, sy)
        if length < WIN_MIN_LEN or min(sx, sy) > WIN_MAX_WIDTH:
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        # outward = away from the floor's wall centre; glass sits WIN_REVEAL in from that face
        if along_x:
            out = -1.0 if cy < cyw else 1.0
            face = y0 if out < 0 else y1
            pc = face - out * WIN_REVEAL
            pc = min(max(pc, y0 + WIN_FRAME / 2), y1 - WIN_FRAME / 2) if sy > WIN_FRAME else cy
            px, py = cx, pc
        else:
            out = -1.0 if cx < cxw else 1.0
            face = x0 if out < 0 else x1
            pc = face - out * WIN_REVEAL
            pc = min(max(pc, x0 + WIN_FRAME / 2), x1 - WIN_FRAME / 2) if sx > WIN_FRAME else cx
            px, py = pc, cy
        for zc in (WIN_RAIL_H / 2, H - WIN_RAIL_H / 2):
            if along_x:
                frames.add_centred(px, py, z0 + zc, length, WIN_FRAME, WIN_RAIL_H)
            else:
                frames.add_centred(px, py, z0 + zc, WIN_FRAME, length, WIN_RAIL_H)
        div = max(1, int(math.ceil(length / WIN_MULLION_STEP)))
        for j in range(div + 1):
            off = -length / 2 + j * length / div
            frames.add_centred(px + (off if along_x else 0.0), py + (0.0 if along_x else off),
                               z0 + H / 2, WIN_MULLION, WIN_MULLION, H)
        if along_x:
            panes.add_centred(px, py, z0 + H / 2, length, WIN_PANE_T, H - 0.05)
        else:
            panes.add_centred(px, py, z0 + H / 2, WIN_PANE_T, length, H - 0.05)
        n += 1

        # street windows: plaster box or grey cladding box
        street = along_x and out < 0 and (y0 - yf) < WINDOW_BOX_FRONT_TOL
        if not street:
            continue
        xg = cx + FLOORS[key]["offset"][0]
        if is_cladding_box(key, cx):
            t = CLADDING_RING_T
            ya = min(yf - CLADDING_T, y0 - WINDOW_BOX_DEPTH)
            clad.ring_xz(x0, x1, SILL_H, WINDOW_HEAD, ya, y0, t)
            provisional("Grey cladding box around %s-floor street window" % key,
                        "window x %.2f..%.2f (ground frame), from the front face (Three z %.2f) back to the window"
                        % (x0 + FLOORS[key]["offset"][0], x1 + FLOORS[key]["offset"][0], FRONT_FACE_Z))
            continue
        if WINDOW_BOXES and key in WINDOW_BOX_FLOORS and length >= WINDOW_BOX_MIN_LEN:
            t, d = WINDOW_BOX_T, WINDOW_BOX_DEPTH
            boxes.ring_xz(x0, x1, SILL_H, WINDOW_HEAD, y0 - d, y0, t)
            e = 0.05 * M
            boxes.add(x0 - t - e, x1 + t + e, y0 - d - SUNSHADE_EXTRA, y0,
                      WINDOW_HEAD + t, WINDOW_HEAD + t + SUNSHADE_T)
            nb += 1
            provisional("Window box + sunshade, %s floor" % key,
                        "street window x %.2f..%.2f (ground frame), outer face Three z %.2f (ground frame)"
                        % (xg - length / 2, xg + length / 2, -(y0) + FLOORS[key]["offset"][1]))
    frames.to_object("%s.windowFrames" % key, coll, empty, mats["Teak"])
    panes.to_object("%s.windowGlass" % key, coll, empty, mats["Glass"])
    boxes.to_object("%s.windowBoxes" % key, coll, empty, mats["Lime White"], bevel=True)
    clad.to_object("%s.claddingBox" % key, coll, empty, mats["Cladding"], bevel=True)
    return n, nb


def build_door_heads(key, empty, coll, mats, openings):
    """Heads over doors and (per GAP_HEADS) other wall gaps; slivers filled full height."""
    if not openings:
        return 0, 0, 0
    fl = openings.get("floors", {}).get(key, {})
    doors = fl.get("doors", [])
    bm = BoxMesh()
    for d in doors:
        bm.add_three(d["x0"], d["x1"], d["z0"], d["z1"], DOOR_HEAD, WALL_H)
    bm.to_object("%s.doorHeads" % key, coll, empty, mats["Lime White"], bevel=True)

    gaps = [g for g in fl.get("gaps", [])
            if GAP_HEADS == "all" or (GAP_HEADS == "perimeter" and g.get("perimeter"))]
    gm = BoxMesh()
    for g in gaps:
        gm.add_three(g["x0"], g["x1"], g["z0"], g["z1"], DOOR_HEAD, WALL_H)
    gm.to_object("%s.gapHeads" % key, coll, empty, mats["Lime White"], bevel=True)

    slivers = fl.get("slivers", []) if FILL_SLIVERS else []
    sm = BoxMesh()
    for g in slivers:
        sm.add_three(g["x0"], g["x1"], g["z0"], g["z1"], 0.0, WALL_H)
    sm.to_object("%s.sliverFill" % key, coll, empty, mats["Lime White"])
    return len(doors), len(gaps), len(slivers)


def build_cladding_strips(empties, colls, mats):
    for key, xg0, xg1, zb, zt in CLADDING_STRIPS:
        ox = FLOORS[key]["offset"][0]
        yf = front_y(key)
        bm = BoxMesh()
        bm.add(xg0 - ox, xg1 - ox, yf - CLADDING_T, yf, zb, zt)
        bm.to_object("%s.claddingStrip" % key, colls[key], empties[key], mats["Cladding"], bevel=True)
        provisional("Grey cladding strip, %s floor" % key,
                    "street face Three z %.2f (ground frame), x %.2f..%.2f, floor-local height %.2f..%.2f units"
                    % (FRONT_FACE_Z, xg0, xg1, zb, zt))


def parapet_with_coping(bm, cop, x0, x1, y0, y1, z0, z1):
    bm.add(x0, x1, y0, y1, z0, z1)
    o = COPING_OVER
    cop.add(x0 - o, x1 + o, y0 - o, y1 + o, z1, z1 + COPING_T)


def railing(bm, ax, ay, bx, by, z0):
    """Charcoal-steel horizontal-bar railing from (ax, ay) to (bx, by) (axis-aligned), base z0."""
    length = math.hypot(bx - ax, by - ay)
    if length <= 1e-6:
        return
    along_x = abs(bx - ax) >= abs(by - ay)
    nposts = max(1, int(math.ceil(length / RAIL_POST_STEP)))
    for i in range(nposts + 1):
        t = i / nposts
        px, py = ax + (bx - ax) * t, ay + (by - ay) * t
        bm.add_centred(px, py, z0 + RAIL_H / 2, RAIL_POST, RAIL_POST, RAIL_H)
    for h in RAIL_BARS:
        if along_x:
            bm.add(min(ax, bx), max(ax, bx), ay - RAIL_BAR / 2, ay + RAIL_BAR / 2, z0 + h - RAIL_BAR, z0 + h)
        else:
            bm.add(ax - RAIL_BAR / 2, ax + RAIL_BAR / 2, min(ay, by), max(ay, by), z0 + h - RAIL_BAR, z0 + h)


# =============================================================================
# Plinth, steps, street compound wall, gates, pergola
# =============================================================================

def gate_leaf(bm, x0, x1, zc, centre_post=False):
    """Horizontal-slat steel gate between x0 and x1 on the wall line zc (street frame, units)."""
    t = GATE_SLAT_T
    y = 0.10 * M
    while y + GATE_SLAT_H <= GATE_H + 1e-6:
        bm.add_three(x0 + 0.01 * M, x1 - 0.01 * M, zc - t / 2, zc + t / 2, y, y + GATE_SLAT_H)
        y += GATE_SLAT_PITCH
    p = GATE_POST
    posts = [x0 + p / 2, x1 - p / 2] + ([(x0 + x1) / 2] if centre_post else [])
    for px in posts:
        bm.add_three(px - p / 2, px + p / 2, zc - p / 2, zc + p / 2, 0.02 * M, GATE_H)
    bm.add_three(x0, x1, zc - p / 2, zc + p / 2, GATE_H - p, GATE_H)   # top rail


def build_site_works(empties, colls, site, mats):
    g = FLOORS["ground"]
    street = -g["level"]
    G, Gc = empties["ground"], colls["ground"]

    # Plinth skirts under the raised ground floor (front, back, sides; <= compound-wall height)
    skirt = BoxMesh()
    for (w, d, x, z) in SKIRTS:
        skirt.add_three(x - w / 2, x + w / 2, z - d / 2, z + d / 2, street, -SLAB_T)
    skirt.to_object("ground.plinthSkirt", Gc, G, mats["Lime White Shade"], bevel=True)

    steps = BoxMesh()
    for i in range(STEP_COUNT):
        z = STEP_Z0 + i * STEP_DZ
        steps.add_three(STEP_X - STEP_W / 2, STEP_X + STEP_W / 2, z - STEP_D / 2, z + STEP_D / 2,
                        street, street + (g["level"] - i * STEP_RISE))
    steps.to_object("ground.gateSteps", Gc, G, mats["Sandstone"], bevel=True)

    # Street frame: model units at street level (ground-floor plan frame, ground offset 0, 0)
    units = bpy.data.objects.new("Site.Units", None)
    units.empty_display_type = "PLAIN_AXES"
    units.scale = (UNIT_M, UNIT_M, UNIT_M)
    ox, oz = g["offset"]
    units.location = (ox * UNIT_M, -oz * UNIT_M, 0.0)
    site.objects.link(units)

    wall, cop, steel = BoxMesh(), BoxMesh(), BoxMesh()
    zc, t = COMPOUND_Z, COMPOUND_T
    cuts = [(a, b) for a, b, _k in COMPOUND_GATES]
    for (x0, x1) in spans(COMPOUND_X0, COMPOUND_X1, cuts):
        wall.add_three(x0, x1, zc - t / 2, zc + t / 2, 0.0, COMPOUND_H)
        cop.add_three(x0 - COPING_OVER, x1 + COPING_OVER, zc - t / 2 - COPING_OVER, zc + t / 2 + COPING_OVER,
                      COMPOUND_H, COMPOUND_H + COPING_T)
    for (a, b, kind) in COMPOUND_GATES:
        for (p0, p1) in ((a - PIER_W, a), (b, b + PIER_W)):
            wall.add_three(p0, p1, zc - t / 2 - 0.02 * M, zc + t / 2 + 0.02 * M, 0.0, PIER_H)
            cop.add_three(p0 - COPING_OVER, p1 + COPING_OVER, zc - t / 2 - 0.02 * M - COPING_OVER,
                          zc + t / 2 + 0.02 * M + COPING_OVER, PIER_H, PIER_H + COPING_T)
        gate_leaf(steel, a, b, zc, centre_post=(b - a) * UNIT_M > 2.5)
        provisional("Street %s gate (charcoal steel, horizontal slats, %.2f m high)" % (kind, GATE_H * UNIT_M),
                    "compound wall line Three z %.2f, x %.2f..%.2f (ground frame)" % (zc, a, b))
    # short side returns from the ground slab edge to the street wall
    for x in (COMPOUND_X0 + t / 2, COMPOUND_X1 - t / 2):
        wall.add_three(x - t / 2, x + t / 2, SIDE_WALL_Z[0], SIDE_WALL_Z[1], 0.0, COMPOUND_H)
        cop.add_three(x - t / 2 - COPING_OVER, x + t / 2 + COPING_OVER, SIDE_WALL_Z[0], SIDE_WALL_Z[1],
                      COMPOUND_H, COMPOUND_H + COPING_T)
    provisional("Street compound wall, %.2f m high, plastered, with coping and piers" % (COMPOUND_H * UNIT_M),
                "Three z %.2f (ground frame; in front of the gate steps), x %.2f..%.2f, side returns z %.2f..%.2f"
                % (zc, COMPOUND_X0, COMPOUND_X1, SIDE_WALL_Z[0], SIDE_WALL_Z[1]))

    if PERGOLA:
        px0, px1 = PERGOLA_X
        pz0, pz1 = PERGOLA_Z
        p = PERGOLA_POST
        top = PERGOLA_TOP
        for x in (px0 + p / 2, px1 - p / 2):
            wall.add_three(x - p / 2, x + p / 2, pz1 - p, pz1, 0.0, top - PERGOLA_SLAB_T)
        wall.add_three(px0, px1, pz0, pz1, top - PERGOLA_SLAB_T, top)
        provisional("Concrete pergola over the pedestrian gate (p05)",
                    "x %.2f..%.2f, Three z %.2f..%.2f (ground frame), top %.2f m" % (px0, px1, pz0, pz1, top * UNIT_M))

    wall.to_object("Site.CompoundWall", site, units, mats["Lime White"], bevel=True)
    cop.to_object("Site.CompoundCoping", site, units, mats["Lime White Shade"], bevel=True)
    steel.to_object("Site.Gates", site, units, mats["Charcoal Steel"])
    return units


# =============================================================================
# Trees (Poly Haven jacaranda as gulmohar stand-in + orange-red flower clusters)
# =============================================================================

ICO_V = None


def _ico():
    global ICO_V
    if ICO_V is None:
        p = (1 + 5 ** 0.5) / 2
        v = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p),
             (0, -1, -p), (0, 1, -p), (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
        n = (1 + p * p) ** 0.5
        v = [(a / n, b / n, c / n) for a, b, c in v]
        f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
             (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8),
             (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
        ICO_V = (v, f)
    return ICO_V


def fix_leaf_alpha(mat):
    """The 1k glTF leaves texture is a JPG (black background, no alpha): derive alpha from luminance."""
    try:
        nt = mat.node_tree
        out = [n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial"][0]
        link = out.inputs["Surface"].links[0]
        bsdf_out = link.from_socket
        bsdf = link.from_node
        tex = None
        if "Base Color" in bsdf.inputs and bsdf.inputs["Base Color"].links:
            tex = bsdf.inputs["Base Color"].links[0].from_node
            while tex is not None and tex.bl_idname != "ShaderNodeTexImage" and tex.inputs and tex.inputs[0].links:
                tex = tex.inputs[0].links[0].from_node
        if tex is None or tex.bl_idname != "ShaderNodeTexImage":
            tex = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage" and n.image
                        and "diff" in n.image.name.lower()), None)
        if tex is None:
            warn("leaf material %s: no diffuse texture found" % mat.name)
            return
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(tex.outputs["Color"], bw.inputs["Color"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.015
        mr.inputs["From Max"].default_value = 0.06
        mr.clamp = True
        nt.links.new(bw.outputs["Val"], mr.inputs["Value"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        ms = nt.nodes.new("ShaderNodeMixShader")
        nt.links.remove(link)
        nt.links.new(mr.outputs["Result"], ms.inputs[0])
        nt.links.new(tr.outputs[0], ms.inputs[1])
        nt.links.new(bsdf_out, ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs["Surface"])
        if "Alpha" in bsdf.inputs:
            for l in list(bsdf.inputs["Alpha"].links):
                nt.links.remove(l)
            bsdf.inputs["Alpha"].default_value = 1.0
    except Exception as e:
        warn("leaf alpha fix on %s: %s" % (mat.name, e))


def build_trees(site, manifest):
    rel = manifest.get("tree")
    path = asset_path(rel) if rel else None
    if not TREES or not path or not os.path.isfile(path):
        warn("tree model not found; trees skipped (run fetch_assets.py)")
        return []
    before = set(bpy.data.objects)
    vl = bpy.context.view_layer
    vl.active_layer_collection = vl.layer_collection
    try:
        import_gltf(path)
    except Exception as e:
        warn("tree import failed: %s" % e)
        return []
    vl.update()
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        warn("tree import produced no meshes")
        return []
    src = bpy.data.collections.new("TreeSource")       # not linked to the scene; instanced below
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        src.objects.link(o)
    for o in meshes:
        for m in o.data.materials:
            if m and "leaves" in m.name.lower():
                fix_leaf_alpha(m)

    # world-space bounds of the source tree
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    zmin = min(p.z for p in pts)
    zmax = max(p.z for p in pts)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    rmax = max(math.hypot(p.x - cx, p.y - cy) for p in pts)
    height = max(zmax - zmin, 1e-3)
    s = TREE_HEIGHT_M / height

    # flower clusters on the outer, upper canopy
    if np is not None and FLOWER_COUNT > 0:
        try:
            rng = np.random.default_rng(7)
            cand = []
            for o in meshes:
                nv = len(o.data.vertices)
                co = np.empty(nv * 3, np.float32)
                o.data.vertices.foreach_get("co", co)
                co = co.reshape(-1, 3)
                pick = co[rng.choice(nv, size=min(nv, 200000), replace=False)]
                mw = np.array(o.matrix_world, dtype=np.float32)
                wp = pick @ mw[:3, :3].T + mw[:3, 3]
                r = np.hypot(wp[:, 0] - cx, wp[:, 1] - cy)
                keep = (wp[:, 2] > zmin + 0.55 * height) & (r > 0.35 * rmax)
                cand.append(wp[keep])
            cand = np.concatenate(cand) if cand else np.zeros((0, 3))
            if len(cand):
                sel = cand[rng.choice(len(cand), size=min(FLOWER_COUNT, len(cand)), replace=False)]
                iv, ifc = _ico()
                verts, faces, mat_idx = [], [], []
                for i, p in enumerate(sel):
                    rad = float(rng.uniform(*FLOWER_RADIUS)) / s
                    b = len(verts)
                    verts += [(p[0] + a * rad, p[1] + bb * rad, p[2] + c * rad * 0.7) for a, bb, c in iv]
                    faces += [(b + f0, b + f1, b + f2) for f0, f1, f2 in ifc]
                    mat_idx += [i % len(FLOWER_COLORS)] * len(ifc)
                me = bpy.data.meshes.new("Tree.Flowers")
                me.from_pydata(verts, [], faces)
                me.update()
                for k, hx in enumerate(FLOWER_COLORS):
                    fm, fnt, fb = new_material("Gulmohar Flower %d" % k)
                    fb.inputs["Base Color"].default_value = hex_to_linear(hx)
                    fb.inputs["Roughness"].default_value = 0.6
                    me.materials.append(fm)
                me.polygons.foreach_set("material_index", mat_idx)
                me.update()
                fo = bpy.data.objects.new("Tree.Flowers", me)
                src.objects.link(fo)
        except Exception as e:
            warn("flower clusters failed: %s" % e)

    trees = []
    for i, (xg, zg, rot) in enumerate(TREE_POSITIONS):
        e = bpy.data.objects.new("Tree.%d" % (i + 1), None)
        e.instance_type = "COLLECTION"
        e.instance_collection = src
        e.scale = (s, s, s)
        e.rotation_euler = (0.0, 0.0, math.radians(rot))
        # rotate the canopy centre about the trunk, then place at the target
        off = Matrix.Rotation(math.radians(rot), 4, "Z") @ Vector((cx * s, cy * s, 0.0))
        e.location = (xg * UNIT_M - off.x, -zg * UNIT_M - off.y, -zmin * s)
        site.objects.link(e)
        trees.append(e)
        provisional("Gulmohar stand-in tree %d (Poly Haven jacaranda + flower clusters), %.1f m" % (i + 1, TREE_HEIGHT_M),
                    "street, ground-frame Three x %.2f z %.2f" % (xg, zg))
    info("trees: source height %.1f m scaled x%.2f, %d instances" % (height, s, len(trees)))
    return trees


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

    manifest = load_manifest()
    mats = build_materials(manifest)
    openings = load_openings()

    empties = {}
    for key in FLOOR_ORDER:
        empties[key] = import_floor(key, colls[key], detail, mats)

    # Floor slabs: terrazzo top, plaster edges / underside; overhang trims as notches
    for key in FLOOR_ORDER:
        s = FLOORS[key]
        hw, hd = s["width"] / 2, s["depth"] / 2
        voids = [three_rect_to_blender(v) for v in SLAB_VOIDS[key]]
        trims = (openings or {}).get("floors", {}).get(key, {}).get("slabTrim", []) if USE_SLAB_TRIM else []
        for t in trims:
            voids.append(three_rect_to_blender((t["x0"], t["z0"], t["x1"], t["z1"])))
        if trims:
            provisional("Slab overhang trimmed to ~30 cm, %s floor (%d cuts)" % (key, len(trims)),
                        "; ".join("%s edge x %.2f..%.2f z %.2f..%.2f (-%.2f m)"
                                  % (t["edge"], t["x0"], t["x1"], t["z0"], t["z1"], t["depth_m"]) for t in trims))
        add_slab("%s.slab" % key, (-hw, hw, -hd, hd), voids, 0.0, SLAB_T,
                 colls[key], empties[key], mats["Terrazzo"], side_mat=mats["Lime White"], bevel=True)

    for key in FLOOR_ORDER:
        nw, nb = build_windows(key, empties[key], colls[key], mats, openings)
        nd, ng, ns = build_door_heads(key, empties[key], colls[key], mats, openings)
        info("%s: %d windows framed (%d boxes), %d door heads, %d gap heads, %d slivers filled"
             % (key, nw, nb, nd, ng, ns))
    build_cladding_strips(empties, colls, mats)
    build_site_works(empties, colls, site, mats)

    # Finish planes
    fin_t = FINISH_T_M / UNIT_M
    for key, name, rect, mname in FINISHES:
        voids = [three_rect_to_blender(v) for v in SLAB_VOIDS[key]]
        add_slab("%s.%s" % (key, name), three_rect_to_blender(rect), voids,
                 fin_t, fin_t, colls[key], empties[key], mats[mname])

    # Second floor: terrace floor, parapet with coping, railing
    sec = FLOORS["second"]
    shw, shd = sec["width"] / 2, sec["depth"] / 2
    tx0, tx1 = -shw, TERRACE_X1
    t = PARAPET_T
    sec_voids = [three_rect_to_blender(v) for v in SLAB_VOIDS["second"]]
    add_slab("second.Terrace.Terracotta", (tx0, tx1, -shd, shd), sec_voids,
             fin_t, fin_t, colls["second"], empties["second"], mats["Terracotta"])
    lw = mats["Lime White"]
    par, cop, rail = BoxMesh(), BoxMesh(), BoxMesh()
    parapet_with_coping(par, cop, tx0, tx0 + t, -shd, shd, 0.0, PARAPET_H)
    parapet_with_coping(par, cop, tx0 + t, tx1, -shd, -shd + t, 0.0, PARAPET_H)
    parapet_with_coping(par, cop, tx0 + t, tx1, shd - t, shd, 0.0, PARAPET_H)
    if TERRACE_RAILING:
        zr = PARAPET_H + COPING_T
        railing(rail, tx0 + t / 2, -shd + t / 2, tx0 + t / 2, shd - t / 2, zr)
        railing(rail, tx0 + t / 2, -shd + t / 2, tx1, -shd + t / 2, zr)
        railing(rail, tx0 + t / 2, shd - t / 2, tx1, shd - t / 2, zr)
        provisional("Terrace railing (charcoal steel, %d horizontal bars, %.2f m)" % (len(RAIL_BARS), RAIL_H * UNIT_M),
                    "on the second-floor terrace parapet: west edge x %.2f, south/north edges x %.2f..%.2f (second-floor local)"
                    % (tx0, tx0, tx1))
    par.to_object("second.TerraceParapet", colls["second"], empties["second"], lw, bevel=True)
    cop.to_object("second.TerraceCoping", colls["second"], empties["second"], mats["Lime White Shade"], bevel=True)
    rail.to_object("second.TerraceRailing", colls["second"], empties["second"], mats["Charcoal Steel"])

    # Roof: Empty at the roof slab underside, child of Floor.second (in units)
    roof = bpy.data.objects.new("Floor.roof", None)
    roof.empty_display_type = "PLAIN_AXES"
    roof_coll.objects.link(roof)
    set_parent(roof, empties["second"])
    roof.location = (0.0, 0.0, ROOF_UNDERSIDE)
    rx0, rx1 = TERRACE_X1, shw
    roof_voids = [three_rect_to_blender(v) for v in ROOF_VOIDS]
    add_slab("roof.slab", (rx0, rx1, -shd, shd), roof_voids, SLAB_T, SLAB_T,
             roof_coll, roof, lw, bevel=True)
    z0, z1 = SLAB_T, SLAB_T + PARAPET_H
    rp, rc = BoxMesh(), BoxMesh()
    parapet_with_coping(rp, rc, rx0, rx1, -shd, -shd + t, z0, z1)
    parapet_with_coping(rp, rc, rx0, rx1, shd - t, shd, z0, z1)
    parapet_with_coping(rp, rc, rx0, rx0 + t, -shd + t, shd - t, z0, z1)
    parapet_with_coping(rp, rc, rx1 - t, rx1, -shd + t, shd - t, z0, z1)
    rp.to_object("roof.Parapet", roof_coll, roof, lw, bevel=True)
    rc.to_object("roof.Coping", roof_coll, roof, mats["Lime White Shade"], bevel=True)
    provisional("Copings on all parapets and the compound wall",
                "%.0f mm thick, %.0f mm overhang" % (COPING_T * UNIT_M * 1000, COPING_OVER * UNIT_M * 1000))

    # Street disc at Z = 0 (fades into the fog toward the house)
    n = GROUND_SEGMENTS
    verts = [(GROUND_RADIUS_M * math.cos(2 * math.pi * i / n),
              GROUND_RADIUS_M * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    me = bpy.data.meshes.new("Site.Street")
    me.from_pydata(verts, [], [list(range(n))])
    me.update()
    street = bpy.data.objects.new("Site.Street", me)
    site.objects.link(street)
    me.materials.append(mats["Asphalt"])

    trees = build_trees(site, manifest)

    # Box UVs + bevels
    vl = bpy.context.view_layer
    vl.update()
    for o in list(scene.objects):
        if o.type != "MESH" or o.name.startswith("Tree") or o.users_collection[0] == detail:
            continue
        if "BoxUV" not in o.data.uv_layers:
            box_uv(o.data, o.matrix_world.to_scale()[0])
    if BEVEL:
        for o in BEVEL_OBJECTS:
            add_bevel(o, o.matrix_world.to_scale()[0])
    info("bevel on %d objects" % (len(BEVEL_OBJECTS) if BEVEL else 0))

    house_bbox = compute_house_bbox()
    world = build_world(scene, manifest)
    fog = build_fog(scene, site, world)
    sun = build_sun(site)
    cam = build_camera(scene, site, house_bbox)
    cam_angle = build_angle_camera(site)
    cam_top = build_top_camera(site, house_bbox)
    scene.camera = cam
    setup_render(scene, world)
    comp_ok = build_compositor(scene) if FOG_MODE == "compositor" else False
    heads = [o for o in bpy.data.objects if o.name.endswith((".doorHeads", ".windowHeads", ".gapHeads"))]
    views = [
        ("01-dawn", cam, RENDER_PATH, [], comp_ok),
        ("02-angle", cam_angle, RENDER_ANGLE_PATH, [], comp_ok),
        # Plan view: no roof, haze, sun, trees, pergola or heads, so the plans read.
        ("03-top", cam_top, RENDER_TOP_PATH,
         [roof_coll, sun] + trees + heads + ([fog] if fog is not None else []), False),
    ]
    return scene, cam, sun, house_bbox, views


def compute_house_bbox():
    xs, ys = [], []
    for key, s in FLOORS.items():
        ox, oz = s["offset"]
        xs += [(ox - s["width"] / 2) * UNIT_M, (ox + s["width"] / 2) * UNIT_M]
        ys += [-(oz + s["depth"] / 2) * UNIT_M, -(oz - s["depth"] / 2) * UNIT_M]
    top = (FLOORS["second"]["level"] + ROOF_UNDERSIDE + SLAB_T + PARAPET_H + COPING_T) * UNIT_M
    return dict(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys), z0=0.0, z1=top,
                roof_front_y=-(FRONT_FACE_Z) * UNIT_M,
                base_front_y=-(COMPOUND_Z + COMPOUND_T / 2) * UNIT_M)


# =============================================================================
# World, fog, sun
# =============================================================================

def build_world(scene, manifest):
    world = bpy.data.worlds.new("Dawn")
    scene.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (700, 0)

    # camera-ray sky: board gradient, pink at the horizon to lilac at the top
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-900, 200)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-700, 200)
    r = ramp(nt, [(0.0, hex_to_linear(SKY_HORIZON)), (SKY_GRADIENT_TOP, hex_to_linear(SKY_ZENITH))])
    r.location = (-500, 200)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], r.inputs["Fac"])
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_cam.location = (200, 200)
    bg_cam.inputs["Strength"].default_value = SKY_CAMERA_STRENGTH
    nt.links.new(r.outputs["Color"], bg_cam.inputs["Color"])

    # lighting: tinted HDRI (or the same gradient without one)
    bg_light = nt.nodes.new("ShaderNodeBackground")
    bg_light.location = (200, -150)
    bg_light.inputs["Strength"].default_value = HDRI_STRENGTH
    hdri = asset_path(manifest.get("hdri")) if manifest.get("hdri") else None
    if hdri and os.path.isfile(hdri):
        try:
            env = nt.nodes.new("ShaderNodeTexEnvironment")
            env.location = (-500, -150)
            env.image = bpy.data.images.load(hdri, check_existing=True)
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.location = (-700, -150)
            mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(HDRI_ROTATION_DEG))
            nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
            tint = hex_to_linear(HDRI_TINT)
            lum = 0.2126 * tint[0] + 0.7152 * tint[1] + 0.0722 * tint[2]
            tint_n = (tint[0] / lum, tint[1] / lum, tint[2] / lum, 1.0)
            m, _f, a, b, res = mix_rgba(nt, "MULTIPLY", HDRI_TINT_AMOUNT)
            m.location = (-200, -150)
            nt.links.new(env.outputs["Color"], a)
            b.default_value = tint_n
            nt.links.new(res, bg_light.inputs["Color"])
            info("world: HDRI %s" % os.path.basename(hdri))
        except Exception as e:
            warn("HDRI setup failed (%s); gradient lighting" % e)
            nt.links.new(r.outputs["Color"], bg_light.inputs["Color"])
    else:
        warn("no HDRI; gradient lighting (run fetch_assets.py)")
        nt.links.new(r.outputs["Color"], bg_light.inputs["Color"])

    lp = nt.nodes.new("ShaderNodeLightPath")
    lp.location = (200, 450)
    ms = nt.nodes.new("ShaderNodeMixShader")
    ms.location = (450, 0)
    nt.links.new(lp.outputs["Is Camera Ray"], ms.inputs[0])
    nt.links.new(bg_light.outputs["Background"], ms.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs["Surface"])
    try:
        mist = world.mist_settings
        mist.start = MIST_START_M
        mist.depth = MIST_DEPTH_M
        mist.falloff = MIST_FALLOFF
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
    """Volume fog for FOG_MODE 'domain' / 'world'; 'compositor' fog is built in build_compositor."""
    try:
        if FOG_MODE == "world":
            nt = world.node_tree
            out = [n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputWorld"][0]
            vs = scatter_node(nt)
            nt.links.new(vs.outputs["Volume"], out.inputs["Volume"])
            return None
        if FOG_MODE != "domain":
            return None
        mat = bpy.data.materials.new("Fog")
        try:
            mat.use_nodes = True
        except Exception:
            pass
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
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


# =============================================================================
# Cameras
# =============================================================================

def solve_board_framing(bb):
    """Camera y and shift_y so the roof top lands at BOARD_TOP_FRAC and the street-wall base at
    BOARD_BASE_FRAC from the top of a level, frontal 50 mm frame."""
    aspect = RES_X / RES_Y
    fh = CAM_LENS_MM / (CAM_SENSOR_MM / aspect)        # focal / sensor height (AUTO fit = width)
    h = CAM_HEIGHT_M
    zt, yt = bb["z1"], bb["roof_front_y"]
    zb, yb = 0.0, bb["base_front_y"]
    span = BOARD_BASE_FRAC - BOARD_TOP_FRAC

    def f(ycam):
        return fh * ((zt - h) / (yt - ycam) + (h - zb) / (yb - ycam)) - span

    lo, hi = yb - 400.0, yb - 1.0          # f(lo) < 0 (far), f(hi) > 0 (near)
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    ycam = (lo + hi) / 2
    shift = (fh * (zt - h) / (yt - ycam) - (0.5 - BOARD_TOP_FRAC)) / aspect
    return ycam, shift


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
    cx = 0.0                                     # board 01: house centred on the plot
    cy_house = (bb["y0"] + bb["y1"]) / 2
    if CAM_DISTANCE_M is not None:
        cam_y = cy_house - CAM_DISTANCE_M
        aim = (bb["z0"] + bb["z1"]) / 2
        shift = (aim - CAM_HEIGHT_M) / (cy_house - cam_y) * CAM_LENS_MM / CAM_SENSOR_MM
    else:
        cam_y, shift = solve_board_framing(bb)
    if abs(cam_y) > GROUND_RADIUS_M - 2.0:
        warn("street camera at y %.1f is near the ground disc edge" % cam_y)
    cam.location = (cx, cam_y, CAM_HEIGHT_M)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)  # level, looking +Y
    cd.shift_y = shift
    cam["distance_to_house_centre_m"] = cy_house - cam_y
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
    y0 = min(bb["y0"], bb["base_front_y"]) - 0.5
    cx, cy = (bb["x0"] + bb["x1"]) / 2, (y0 + bb["y1"]) / 2
    ex, ey = bb["x1"] - bb["x0"], bb["y1"] - y0
    rotated = abs(round(TOP_ROTATE_DEG / 90.0)) % 2 == 1
    fw, fh = (ey, ex) if rotated else (ex, ey)
    cd.ortho_scale = max(fw, fh * RES_X / RES_Y) * TOP_MARGIN
    cam.location = (cx, cy, TOP_CAM_Z_M)
    cam.rotation_euler = (0.0, 0.0, math.radians(TOP_ROTATE_DEG))
    return cam


# =============================================================================
# Render settings, compositor fog, renders, board comparison
# =============================================================================

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
    try:
        cy.transparent_max_bounces = 32      # alpha-cut leaves
    except Exception:
        pass

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
            d.use = (d.type != "CPU") if gpus else True
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
        warn("view transform %s unavailable (%s); using %s" % (VIEW_TRANSFORM, e, VIEW_TRANSFORM_FALLBACK))
        try:
            vs.view_transform = VIEW_TRANSFORM_FALLBACK
        except Exception as e2:
            warn("view transform: %s" % e2)
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


def build_compositor(scene):
    """Fog = Mist pass x FOG_AMOUNT mixed toward FOG_COLOR; the sky (mist == 1) is left alone so the
    world's camera gradient survives."""
    fog = hex_to_linear(FOG_COLOR)
    try:
        if hasattr(scene, "compositing_node_group"):       # Blender 5.x
            tree = bpy.data.node_groups.new("Dawn Fog", "CompositorNodeTree")
            scene.compositing_node_group = tree
            rl = tree.nodes.new("CompositorNodeRLayers")
            rl.location = (-600, 0)
            out = tree.nodes.new("NodeGroupOutput")
            out.location = (500, 0)
            tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            less = math_node(tree, "LESS_THAN", b=0.9995)
            mul = math_node(tree, "MULTIPLY")
            amt = math_node(tree, "MULTIPLY", b=FOG_AMOUNT, clamp=True)
            mix, f, a, b, res = mix_rgba(tree, "MIX", 0.0)
            mist = rl.outputs["Mist"]
            tree.links.new(mist, less.inputs[0])
            tree.links.new(mist, mul.inputs[0])
            tree.links.new(less.outputs[0], mul.inputs[1])
            tree.links.new(mul.outputs[0], amt.inputs[0])
            tree.links.new(amt.outputs[0], f)
            tree.links.new(rl.outputs["Image"], a)
            b.default_value = fog
            tree.links.new(res, out.inputs[0])
        else:                                                # Blender 4.x
            scene.use_nodes = True
            tree = scene.node_tree
            tree.nodes.clear()
            rl = tree.nodes.new("CompositorNodeRLayers")
            comp = tree.nodes.new("CompositorNodeComposite")
            less = tree.nodes.new("CompositorNodeMath")
            less.operation = "LESS_THAN"
            less.inputs[1].default_value = 0.9995
            mul = tree.nodes.new("CompositorNodeMath")
            mul.operation = "MULTIPLY"
            amt = tree.nodes.new("CompositorNodeMath")
            amt.operation = "MULTIPLY"
            amt.use_clamp = True
            amt.inputs[1].default_value = FOG_AMOUNT
            mix = tree.nodes.new("CompositorNodeMixRGB")
            mist = rl.outputs["Mist"]
            tree.links.new(mist, less.inputs[0])
            tree.links.new(mist, mul.inputs[0])
            tree.links.new(less.outputs[0], mul.inputs[1])
            tree.links.new(mul.outputs[0], amt.inputs[0])
            tree.links.new(amt.outputs[0], mix.inputs[0])
            tree.links.new(rl.outputs["Image"], mix.inputs[1])
            mix.inputs[2].default_value = fog
            tree.links.new(mix.outputs[0], comp.inputs["Image"])
        try:
            scene.render.use_compositing = True
        except Exception:
            pass
        info("compositor fog: mist %.0f..%.0f m, amount %.2f" % (MIST_START_M, MIST_START_M + MIST_DEPTH_M, FOG_AMOUNT))
        return True
    except Exception as e:
        warn("compositor fog failed (%s); renders have no fog" % e)
        return False


def _load_pixels(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)


def _resize(a, w, h):
    """Bilinear resize of an (H, W, 4) array."""
    H, W = a.shape[:2]
    ys = np.linspace(0, H - 1, h)
    xs = np.linspace(0, W - 1, w)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, H - 1)
    x1 = np.minimum(x0 + 1, W - 1)
    wy = (ys - y0)[:, None, None]
    wx = (xs - x0)[None, :, None]
    top = a[y0][:, x0] * (1 - wx) + a[y0][:, x1] * wx
    bot = a[y1][:, x0] * (1 - wx) + a[y1][:, x1] * wx
    return top * (1 - wy) + bot * wy


def _save_pixels(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    arr = arr.copy()
    arr[..., 3] = 1.0
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def compare_with_board(render_path):
    """01-compare.png: render | board at equal height. 01-overlay.png: 50 % blend."""
    if np is None:
        warn("numpy unavailable; no comparison images")
        return
    if not (os.path.isfile(render_path) and os.path.isfile(BOARD_PATH)):
        warn("comparison skipped (missing %s or %s)" % (render_path, BOARD_PATH))
        return
    try:
        r = _load_pixels(render_path)
        b = _load_pixels(BOARD_PATH)
        h, w = r.shape[:2]
        bw = max(1, int(round(b.shape[1] * h / b.shape[0])))
        bs = _resize(b, bw, h)
        gap = max(4, w // 150)
        canvas = np.ones((h, w + gap + bw, 4), np.float32)
        canvas[:, :w] = r
        canvas[:, w + gap:] = bs
        _save_pixels(canvas, COMPARE_PATH)
        bo = _resize(b, w, h)
        _save_pixels(0.5 * r + 0.5 * bo, OVERLAY_PATH)
        info("wrote %s and %s" % (COMPARE_PATH, OVERLAY_PATH))
    except Exception as e:
        warn("board comparison failed: %s" % e)


def render_views(scene, views):
    if QUICK:
        scene.cycles.samples = QUICK_SAMPLES
        scene.render.resolution_percentage = QUICK_PERCENT
    info("rendering %d samples at %d%% of %dx%d ..."
         % (scene.cycles.samples, scene.render.resolution_percentage, RES_X, RES_Y))
    for name, cam, path, hidden, use_comp in views:
        saved = [(h, h.hide_render) for h in hidden]
        try:
            for h in hidden:
                h.hide_render = True
            try:
                scene.render.use_compositing = bool(use_comp)
            except Exception:
                pass
            scene.camera = cam
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            info("wrote %s" % path)
            if name == "01-dawn":
                compare_with_board(path)
        except Exception as e:
            warn("render %s failed: %s" % (name, e))
        finally:
            for h, v in saved:
                h.hide_render = v
    scene.camera = views[0][1]


def summary(scene, cam, sun, bb):
    info("---- summary ----")
    for c in bpy.data.collections:
        info("collection %-12s %3d objects" % (c.name, len(c.all_objects)))
    info("house bbox (m): x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f"
         % (bb["x0"], bb["x1"], bb["y0"], bb["y1"], bb["z0"], bb["z1"]))
    loc = cam.location
    info("street camera at (%.2f, %.2f, %.2f), %.1f m from house centre, shift_y %.3f"
         % (loc.x, loc.y, loc.z, cam["distance_to_house_centre_m"], cam.data.shift_y))
    info("fog mode: %s; view transform: %s" % (FOG_MODE, scene.view_settings.view_transform))
    info("provisional elements (%d):" % len(PROVISIONAL))
    for p in PROVISIONAL:
        info("  - " + p)
    info("blend:  %s" % BLEND_PATH)
    info("renders: %s" % ("skipped (--no-render)" if NO_RENDER else
                          ", ".join((RENDER_PATH, RENDER_ANGLE_PATH, RENDER_TOP_PATH, COMPARE_PATH, OVERLAY_PATH))
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
