"""Window boxes: the deep plaster frames that project around the street-facing
windows of the first and second floors (board, photos p03, p19). The
first-floor one also carries the projecting balcony ledge under the window,
ground-frame x -2.0..-0.3.

Street-facing windows are found from the GLB sill islands that sit on the
floor's south (street) face, so they follow the drawing."""
import bpy

DEPTH = 0.12        # how far the box projects from the wall, units
THICK = 0.06        # frame section, units
LEDGE_X = (-2.0, -0.3)   # ground frame, Three.js x
LEDGE_DEPTH = 0.18
LEDGE_T = 0.10
SILL_H = 22 / 96    # keep in sync with build_house.SILL_H
WINDOW_H = 0.86     # keep in sync with build_house.WINDOW_H
FACE_TOL = 0.40     # a sill within this of the slab edge is on the street face (front windows are inset ~0.3)


def _islands(sills):
    # Reuse build_house.mesh_islands when running inside the build
    import __main__
    fn = getattr(__main__, "mesh_islands", None)
    verts = [v.co[:] for v in sills.data.vertices]
    polys = [p.vertices[:] for p in sills.data.polygons]
    if fn is None:
        return []
    return fn(verts, polys)


def _frame(h, key, idx, x0, x1, y_wall, y_edge, z0, z1, coll, empty, mat):
    # From the (inset) wall face out past the slab edge: a deep box, as on the board
    yo, yi = y_edge - DEPTH, y_wall + 0.01          # outward is -y (street)
    t = THICK
    h["add_box"]("%s.WindowBox.%d.top" % (key, idx), x0 - t, x1 + t, yo, yi, z1, z1 + t, coll, empty, mat)
    h["add_box"]("%s.WindowBox.%d.bottom" % (key, idx), x0 - t, x1 + t, yo, yi, z0 - t, z0, coll, empty, mat)
    h["add_box"]("%s.WindowBox.%d.left" % (key, idx), x0 - t, x0, yo, yi, z0, z1, coll, empty, mat)
    h["add_box"]("%s.WindowBox.%d.right" % (key, idx), x1, x1 + t, yo, yi, z0, z1, coll, empty, mat)


def build(ctx):
    h, c, mats = ctx["helpers"], ctx["constants"], ctx["mats"]
    mat = mats["Lime White"]
    mats = dict(mats, **{m.name: m for m in bpy.data.materials if m.name == "Charcoal Plaster"})
    z0, z1 = SILL_H, SILL_H + WINDOW_H
    for key in ("first", "second"):
        f = c["FLOORS"][key]
        face_y = -f["depth"] / 2
        sills = bpy.data.objects.get("%s.sills" % key)
        if sills is None:
            h["warn"]("window_boxes: no %s.sills" % key)
            continue
        n = 0
        for (x0, x1, y0, y1) in _islands(sills):
            if (x1 - x0) < 0.18 or (y1 - y0) > 0.20:
                continue                      # not a window island (see build_windows)
            if abs(y0 - face_y) > FACE_TOL and abs(y1 - face_y) > FACE_TOL:
                continue                      # not on the street face
            m = mats.get("Charcoal Plaster", mat) if key == "second" else mat   # the band wraps this box
            _frame(h, key, n, x0, x1, min(y0, y1), face_y, z0, z1, ctx["colls"][key], ctx["empties"][key], m)
            n += 1
        h["info"]("window_boxes: %s %d street windows boxed" % (key, n))
    # Balcony ledge under the first-floor front window
    f = c["FLOORS"]["first"]
    ox = f["offset"][0]
    face_y = -f["depth"] / 2
    h["add_box"]("first.BalconyLedge", LEDGE_X[0] - ox, LEDGE_X[1] - ox,
                 face_y - LEDGE_DEPTH, face_y + 0.01, SILL_H - LEDGE_T, SILL_H,
                 ctx["colls"]["first"], ctx["empties"]["first"], mats["Lime White Shade"])
    return []
