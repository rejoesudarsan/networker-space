"""Shared helper for placing entourage (blender/entourage.blend) in the house.

The library's collections are linked, not appended, and placed as collection
instances: an Empty per placement, parented to a floor frame (Floor.<name>,
or Site.Units for the street) and counter-scaled so the asset stays in
metres while its position is given in that frame's Three.js units.

Switch it off with `-- --no-entourage` on the build_house.py command line or
SPACE_ENTOURAGE=0 in the environment; enabled() is then False and callers
fall back (garage_fitout keeps its plain car)."""
import math
import os
import sys

import bpy

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "entourage.blend")


def enabled():
    if "--no-entourage" in sys.argv or os.environ.get("SPACE_ENTOURAGE", "1") == "0":
        return False
    return os.path.exists(LIB)


def collection(name):
    """The library collection `name`, linked into this file once."""
    for c in bpy.data.collections:
        if c.name == name and c.library is not None:
            return c
    with bpy.data.libraries.load(LIB, link=True, relative=True) as (src, dst):
        if name not in src.collections:
            raise KeyError("entourage.blend has no collection %s" % name)
        dst.collections = [name]
    return dst.collections[0]


def place(ctx, name, frame, x, z, rot=0.0, y=0.0, coll=None, label=None):
    """Instance library collection `name` in `frame` ('street' or a floor
    key) at Three.js (x, y, z) units; rot in degrees about the vertical, 0 =
    the asset's front facing east (+X), 90 = north, -90 = toward the street.
    Returns the Empty."""
    if frame == "street":
        parent = bpy.data.objects["Site.Units"]
    else:
        parent = ctx["empties"][frame]
    u = ctx["constants"]["UNIT_M"]
    ob = bpy.data.objects.new("Entourage.%s" % (label or name), None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = collection(name)
    ob.empty_display_size = 0.3
    (coll or entourage_collection(ctx)).objects.link(ob)
    ob.parent = parent
    ob.location = (x, -z, y)
    ob.rotation_euler = (0.0, 0.0, math.radians(rot))
    ob.scale = (1 / u, 1 / u, 1 / u)
    return ob


def entourage_collection(ctx):
    c = bpy.data.collections.get("Entourage")
    if c is None or c.library is not None:
        c = ctx["helpers"]["get_collection"]("Entourage", ctx["scene"].collection)
    return c
