"""The second-floor terrace (photo p33). The terracotta tile floor is already
built by build_house.py (second.Terrace.Terracotta, 30 cm tile texture); this
adds what p33 shows along the house wall (x = TERRACE_X1, the terrace's east
edge): the long weathered timber bench on low supports near the north end,
and the deep plastered eave of the roof slab over the terrace edge (in
finish(), since the roof is made after the details run). Second frame and
roof frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix

from . import _trees

BENCH = dict(z0=-3.3, z1=-2.25, depth=0.17, h=0.17)
EAVE = 0.38            # how far the roof slab reaches out over the terrace


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    coll, empty = ctx["colls"]["second"], ctx["empties"]["second"]
    wood = _trees.material(ctx, "Weathered Teak", "#8C8273", 0.9)
    x1 = c["TERRACE_X1"]
    b = BENCH
    fin = 0.0085
    xa, xb = x1 - b["depth"] - 0.02, x1 - 0.02
    h["add_box"]("second.TerraceBench.top", xa, xb, -b["z1"], -b["z0"], b["h"] - 0.03, b["h"], coll, empty, wood)
    for zz in (b["z0"] + 0.08, (b["z0"] + b["z1"]) / 2, b["z1"] - 0.08):
        h["add_box"]("second.TerraceBench.leg", xa + 0.02, xb - 0.02, -(zz + 0.03), -(zz - 0.03), fin, b["h"] - 0.03,
                     coll, empty, wood)
    return []


def finish(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    if bpy.data.objects.get("second.Terrace.Terracotta") is None:
        h["warn"]("terrace: second.Terrace.Terracotta missing")
    roof = bpy.data.objects.get("Floor.roof")
    coll = ctx.get("roof_coll") or bpy.data.collections.get("Roof")
    if roof is None:
        h["warn"]("terrace: no Floor.roof for the eave")
        return
    sd = c["FLOORS"]["second"]["depth"] / 2
    x1 = c["TERRACE_X1"]
    h["add_box"]("roof.TerraceEave", x1 - EAVE, x1, -sd, sd, 0.0, c["SLAB_T"], coll, roof, ctx["mats"]["Lime White"])
