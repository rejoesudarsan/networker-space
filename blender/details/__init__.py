"""Detail modules for the Space house. One file per checklist item in
blender/DETAILS.md. Each module defines

    def build(ctx):  -> None or a list of extra render views

where ctx is a dict with: scene, mats, empties (Floor.<key> empties keyed by
floor name), colls (floor collections), site (Site collection), house
(House collection), helpers (add_box, add_slab, get_collection, set_parent,
three_rect_to_blender, new_material, link_only, info, warn), constants
(UNIT_M, SLAB_T, STOREY, WALL_H, FLOORS, PARAPET_H, PARAPET_T, TERRACE_X1).

A returned view is (name, camera_object, output_path, hide_objects).

A module may also define finish(ctx). It runs at the end of the build, after
the roof, the street disc and the lights exist, for edits to those.
Add the module name to MODULES in the order items appear in DETAILS.md.
"""
import importlib
import traceback

MODULES = [
    "grey_cladding_strip",
    "window_boxes",
    "terrace_railing",
    "gulmohar_trees",
    "ramp_railing",
    "front_compound_wall_and_fern_planter",
    "office_outside_stair",
    "neighbour_massing",
    "entrance_court_floor_and_bench",
    "outside_stair_to_first",
    "first_floor_porch",
    "front_lawn_and_steps",
    "side_garden_passage",
    "living1_teak_floor",
    "dining1_display_unit",
    "kitchen1_galley",
    "caretaker_red_oxide",
    "stair_to_basement",
    "court1_big_tree",
    "garage_fitout",
    "office_den",
    "court2_flagstones_olive",
    "court2_nest_pendants",
    "court2_skylight",
    "court2_louvred_doors",
    "steel_stair_to_second",
    "family2_sliding_teak_door",
    "kitchen2",
    "terrace_terracotta",
    "bedroom5_bathtub",
    "passage_over_void",
    "cafe",
    "event_space",
    "court_library",
    "terrace_evening",
    "game_room_first",
    "quiet_rooms_second",
    "basement_work_games",
    "family2_ps5",
    "club_rooms",
    "gulmohar_refine",
    "room_lights",
    "street_wet",
    "detail_cameras",
    "entourage",
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


def finish_all(ctx):
    for name in MODULES:
        try:
            mod = importlib.import_module("details." + name)
            if hasattr(mod, "finish"):
                mod.finish(ctx)
                ctx["helpers"]["info"]("detail %s finished" % name)
        except Exception:
            ctx["helpers"]["warn"]("detail %s finish FAILED:\n%s" % (name, traceback.format_exc()))
