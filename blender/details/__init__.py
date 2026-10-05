"""Detail modules for the Space house. One file per checklist item in
blender/DETAILS.md. Each module defines

    def build(ctx):  -> None or a list of extra render views

where ctx is a dict with: scene, mats, empties (Floor.<key> empties keyed by
floor name), colls (floor collections), site (Site collection), house
(House collection), helpers (add_box, add_slab, get_collection, set_parent,
three_rect_to_blender, new_material, link_only, info, warn), constants
(UNIT_M, SLAB_T, STOREY, WALL_H, FLOORS, PARAPET_H, PARAPET_T, TERRACE_X1).

A returned view is (name, camera_object, output_path, hide_objects).
Add the module name to MODULES in the order items appear in DETAILS.md.
"""
import importlib
import traceback

MODULES = [
    "grey_cladding_strip",
    "window_boxes",
    "terrace_railing",
]


def build_all(ctx):
    views = []
    for name in MODULES:
        try:
            mod = importlib.import_module("details." + name)
            importlib.reload(mod)
            out = mod.build(ctx)
            if out:
                views.extend(out)
            ctx["helpers"]["info"]("detail %s built" % name)
        except Exception:
            ctx["helpers"]["warn"]("detail %s FAILED:\n%s" % (name, traceback.format_exc()))
    return views
