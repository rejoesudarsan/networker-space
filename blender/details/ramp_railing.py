"""The garage ramp and its railing (photos p03, p02).

The ramp: a concrete slope from the basement parking floor at z = 1.2
(basement frame) up to street level at the basement's front edge, between
x -2.2 and -0.61 (site/src/world/details.js PLAN.ramp). Brushed grooves across it.

The railing: charcoal steel, three horizontal bars, 0.36 units high, on the
ground slab round the ramp's mouth (the notch in the ground slab at
x -1.85..-0.2, z 3.2..5.01, ground frame): both sides and across the back,
as in details.js groundFloor()."""
import bmesh
import bpy

from . import _rail, _trees

RAMP_X = (-2.2, -0.61)      # basement frame, Three.js x
RAMP_FOOT = 1.2             # basement frame, Three.js z where the slope starts
MOUTH = (-1.85, 3.2, -0.2, 5.01)   # ground frame void (x0, z0, x1, z1)
OFF = 0.035


def _wedge(name, x0, x1, y_foot, y_head, rise, coll, parent, mat):
    """Slope from (y_foot, z 0) to (y_head, z rise). Blender y; street is -y."""
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in (
        (x0, y_foot, 0), (x1, y_foot, 0), (x1, y_head, 0), (x0, y_head, 0),
        (x0, y_head, rise), (x1, y_head, rise))]
    for f in ((0, 1, 2, 3), (0, 3, 4), (1, 5, 2), (0, 4, 5, 1), (3, 2, 5, 4)):
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ctx_parent(ob, parent)
    me.materials.append(mat)
    return ob


def ctx_parent(ob, parent):
    from mathutils import Matrix
    ob.parent = parent
    ob.matrix_parent_inverse = Matrix.Identity(4)


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    floors = c["FLOORS"]
    concrete = _trees.material(ctx, "Concrete", "#A8A297", 0.85)
    groove = _trees.material(ctx, "Concrete Joint", "#8E897F", 0.9)
    steel = ctx["mats"]["Charcoal Steel"]

    # Ramp in the basement frame. Street level is z 0 world; the basement
    # empty sits at its LEVEL, so the rise is -LEVEL.
    b = floors["basement"]
    rise = -b["level"]
    bhd = b["depth"] / 2
    x0, x1 = RAMP_X
    y_foot, y_head = -RAMP_FOOT, -bhd
    bcoll, bempty = ctx["colls"]["basement"], ctx["empties"]["basement"]
    _wedge("basement.Ramp", x0, x1, y_foot, y_head, rise, bcoll, bempty, concrete)
    # Grooves across the slope
    L = y_foot - y_head
    k = 0.07
    while k < 0.98:
        y = y_foot - L * k
        z = rise * k
        h["add_box"]("basement.RampGroove", x0 + 0.03, x1 - 0.03, y - 0.009, y + 0.009,
                     z - 0.004, z + 0.006, bcoll, bempty, groove)
        k += 0.09

    # Railing round the mouth, on the ground slab (ground frame, slab top = 0)
    gcoll, gempty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    ghd = floors["ground"]["depth"] / 2
    mx0, mz0, mx1, _ = MOUTH
    yb, yf = -(mz0 - OFF), -(ghd - 0.04)          # back of the mouth, front edge
    _rail.run(h, "ground.RampRail.W", (mx0 - OFF, yb), (mx0 - OFF, yf), 0.0, gcoll, gempty, steel)
    _rail.run(h, "ground.RampRail.E", (mx1 + OFF, yb), (mx1 + OFF, yf), 0.0, gcoll, gempty, steel)
    _rail.run(h, "ground.RampRail.Back", (mx0 - OFF, yb), (mx1 + OFF, yb), 0.0, gcoll, gempty, steel)
    return []


def finish(ctx):
    """Cut the basement's footprint out of the street disc, as the site does
    (world.js: the plot 'with a pit where the house sits'). Without it the
    disc runs through the half-sunk basement at street level and hides the ramp."""
    street = bpy.data.objects.get("Site.Street")
    if street is None:
        ctx["helpers"]["warn"]("ramp_railing: no Site.Street to cut")
        return
    c = ctx["constants"]
    b = c["FLOORS"]["basement"]
    unit = c["UNIT_M"]
    ox, oz = b["offset"]
    pad = 0.025
    x0, x1 = (ox - b["width"] / 2 - pad) * unit, (ox + b["width"] / 2 + pad) * unit
    y0, y1 = -(oz + b["depth"] / 2 + pad) * unit, -(oz - b["depth"] / 2 - pad) * unit
    bm = bmesh.new()
    bm.from_mesh(street.data)
    # Make sure the disc has enough edges to split cleanly, then cut
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    for co, no in (((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (-1, 0, 0)),
                   ((0, y0, 0), (0, 1, 0)), ((0, y1, 0), (0, -1, 0))):
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                     plane_co=co, plane_no=no)
    inside = [f for f in bm.faces
              if x0 - 1e-4 <= f.calc_center_median().x <= x1 + 1e-4
              and y0 - 1e-4 <= f.calc_center_median().y <= y1 + 1e-4]
    bmesh.ops.delete(bm, geom=inside, context="FACES")
    bm.to_mesh(street.data)
    bm.free()
    street.data.update()
    ctx["helpers"]["info"]("ramp_railing: cut basement pit %.2f..%.2f x %.2f..%.2f m from the street"
                           % (x0, x1, y0, y1))
