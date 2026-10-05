"""Photo-matched cameras for checking details, rendered with the default
views (quick mode included): renders/04-court2.png (p11, the Double HT Court
toward its north wall and the nests), 05-court1.png (p20, across the
ground-floor void to Court 1's tree), 06-entrance.png (p24, the entrance
court and bench), 07-terrace.png (p33, down the terrace). Positions are the
eye-level views that matched the photos while building the details:
ground-frame Three.js x, z and height above the street in metres. finish()
tries to hide the outdoor haze for interior views, but the haze is built
after finish() runs, so today nothing is hidden (the haze is thin; harmless).
The scene is lit for dawn outside, so the interior views are dark, Court 1's
most of all; they are for checking layout, not for presentation. These four
renders add about 4 minutes to a --quick build."""
import math
import os

import bpy
from mathutils import Vector

CAMS = [  # name, file, eye (x, z, h_m), target (x, z, h_m), lens mm, interior
    ("Court2", "04-court2.png", (1.9, 1.35, 6.6), (0.95, -0.35, 8.3), 16, True),
    ("Court1", "05-court1.png", (0.05, 0.2, 3.35), (1.3, -0.5, 1.6), 16, True),
    ("Entrance", "06-entrance.png", (-2.0, 1.25, 3.4), (-1.9, -0.3, 2.6), 16, True),
    ("Terrace", "07-terrace.png", (-1.0, -3.6, 10.6), (-1.3, 2.0, 9.6), 20, False),
]
_HIDDEN = {}


def build(ctx):
    U = ctx["constants"]["UNIT_M"]
    W = lambda p: Vector((p[0] * U, -p[1] * U, p[2]))
    site = ctx["site"]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "renders")
    views = []
    for name, fname, eye, tgt, lens, interior in CAMS:
        cam = bpy.data.objects.new("Camera.%s" % name, bpy.data.cameras.new("Camera.%s" % name))
        site.objects.link(cam)
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.location = W(eye)
        cam.rotation_euler = (W(tgt) - W(eye)).to_track_quat("-Z", "Y").to_euler()
        hidden = []
        _HIDDEN[name] = (hidden, interior)
        views.append(("%s" % fname[:-4], cam, os.path.join(out, fname), hidden))
    return views


def finish(ctx):
    fog = [o for o in bpy.data.objects if "fog" in o.name.lower() or "haze" in o.name.lower()]
    for name, (hidden, interior) in _HIDDEN.items():
        if interior:
            hidden.extend(fog)
    ctx["helpers"]["info"]("detail cameras: %d views, haze hidden indoors (%d objects)" % (len(_HIDDEN), len(fog)))
