# Blender house: details checklist

Worked by a Ralph loop. One item per iteration. Tick an item only after the
headless build succeeds, the renders are looked at, and the item is visible
and plausible in them. Coordinates are floor-local Three.js units unless
stated (x east, z toward the street, 1 unit = 8 ft); convert with
`three_rect_to_blender` / the `Floor.<name>` empties as `build_house.py` does.
Photo numbers refer to `PHOTO-LABELS.md`; the images are
`docs/house-understanding/img/pNN.jpg`. Plans are in
`docs/house-understanding/plans/*.png`.

Rules for every item:
- Add it as a function in `blender/details/<slug>.py` (one file per item),
  registered in `blender/details/__init__.py`, and called from
  `build_house.py` after the site works. Never paste geometry into
  `build_house.py` itself.
- Use the materials from `build_materials()`; add a new one there only if none fits.
- Keep geometry simple: boxes, cylinders, extruded curves, a few hundred faces per item.
- Parent floor-bound items to their `Floor.<name>` empty so they move with the cutaway.

## Facade and site (from README "Not built yet", board, p03, p05, p19)
- [x] grey-cladding-strip: full-height charcoal textured-plaster band on the street facade, ground frame x 0.3..1.4, from ground slab to roof parapet, on first and second floors.
  - note: one box per floor on the slab-edge plane, 0.02 proud; at ground level it sits on the first-floor plane, which is set back from the ground-floor front, as in p03.
- [x] window-boxes: projecting plaster frames (0.12 deep, 0.06 thick) around the street-facing windows of first and second floors; first-floor one extends as a balcony ledge x -2.0..-0.3.
  - note: boxes found from GLB sill islands within 0.4 of the street edge (2 on first, 1 on second); they run from the inset wall out past the slab edge; the second-floor one uses Charcoal Plaster because it sits in the band.
- [ ] terrace-railing: three-bar steel rail 0.35 above the second-floor terrace parapet; west edge x -2.29, north and south edges x -2.29..-0.95.
- [ ] gulmohar-trees: four trees at ground units (-4.6, z 6.3) h 3.6 flowering, (5.8, z 6.3) h 3.3 flowering, (-9.5, z 9.4), (9.8, z 9.4) not flowering. Trunk + 3 to 5 canopy blobs, red-orange blossom material on the flowering ones.
- [ ] ramp-railing: charcoal steel railing along the side drive ramp down to the basement garage (p03, p02); follow the ramp opening in the ground slab.
- [ ] front-compound-wall-and-fern-planter: check `frontWall`/`streetGate` exist; add the fern planter beside gate no. 1172 (p05) and the house number plate.
- [ ] office-outside-stair: outside stair from the open-to-sky court up to the basement office entrance with a steel rail (plan basement, p03).
- [ ] neighbour-massing: plain neighbour blocks and compound walls on both sides and across the street, positions from `site/src/world/world.js` `neighbours`.

## Entrance court and gardens (p24, p6, p36, p21, p9)
- [ ] entrance-court-floor-and-bench: stone floor in the entrance court and the green bench against the wall (p24).
- [ ] outside-stair-to-first: the outside stair from the entrance court up to the first-floor porch with steel railing and the frangipani at its foot (p6, p4).
- [ ] first-floor-porch: washed-concrete porch floor, mesh railing, grass pendant at the first-floor entrance (p4).
- [ ] front-lawn-and-steps: raised lawn outside Living 1 with the garden steps up to it (p21, p36).
- [ ] side-garden-passage: west garden strip with potted plants and steps (p9).

## Ground floor interiors (p25, p27, p28, p13, p15, p20)
- [ ] living1-teak-floor: teak floor in Living 1, brass lanterns hanging, glazed doors to the lawn (p25, p27).
- [ ] dining1-display-unit: teak display unit against the wall of Dining 1 (p28).
- [ ] kitchen1-galley: black granite counters both sides of the galley, mauve laminate fronts (p13).
- [ ] caretaker-red-oxide: red-oxide floor in the caretaker room (p15).
- [ ] stair-to-basement: the inside stair under the DOUBLE HEIGHT box down to basement Court 1, wooden balustrade, blue glass lantern (p20).

## Basement (p2, p10, p31)
- [ ] court1-big-tree: the big tree in basement Court 1 rising through the ground-floor double-height void; trunk + canopy reaching above the ground slab.
- [ ] garage-fitout: block-wall texture on the parking walls, a ladder, one simple car (p2).
- [ ] office-den: pinboard, desk, chair, whiteboard in the Office/Den (p10, p31).

## First floor (p1, p11, p14, p8, p35, p16, p26)
- [ ] court2-flagstones-olive: sandstone flagstones in the Double HT Court and the olive tree in a planter (p11, p14).
- [ ] court2-nest-pendants: three woven nest pendants hanging from the skylight into the court (p1, p11).
- [ ] court2-skylight: skylight frame and glass over the court void above the second floor, roof void opened (`ROOF_VOIDS`) (p1).
- [ ] court2-louvred-doors: teak louvred doors between the court and Living 2 (p1, p11, p14).
- [ ] steel-stair-to-second: steel stair with timber treads beside the court up to the second floor (p8, p35).
- [ ] family2-sliding-teak-door: the sliding teak door and cove light in Family 2 (p16).
- [ ] kitchen2: light-wood cabinets and double sink (p26).

## Second floor and terrace (p29, p30, p32, p33, p34)
- [ ] terrace-terracotta: terracotta tile floor on the long terrace.
- [ ] bedroom5-bathtub: bathtub in the second-floor bath (p29).
- [ ] passage-over-void: the passage railing over the courtyard void and the study nook (p30).

## Cameras and renders
- [ ] detail-cameras: add cameras `Camera.Court2`, `Camera.Court1`, `Camera.Entrance`, `Camera.Terrace` framed like p1, p20, p24, p30, so each detail can be checked from a photo-matched view; render them in `--quick` mode.
