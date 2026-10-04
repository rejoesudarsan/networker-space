# Space house in Blender

`build_house.py` builds the house from scratch in Blender 5.2 LTS. It imports the four floor GLBs from `site/public/models/` and closes every window and door slot above its opening. Then it adds:

- slabs, the roof and parapets
- window frames and glass
- the plinth skirt, the street gate and front wall, and the gate steps
- the street, dawn light, haze and three cameras

It saves a `.blend` file and renders three views.

## Run

Quick iteration render: 32 samples at half resolution.

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py -- --quick
```

Full quality: 256 samples at 1536×1024.

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py
```

Build and save only, with no render:

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py -- --no-render
```

The script tries the Metal GPU first and falls back to the CPU. Watch the `[build_house]` lines in the terminal. They report how many windows and door heads were built on each floor, any warnings, and a final summary.

### Door openings data

The door positions come from `blender/data/openings.json`. This file sits alongside the script (it is not git-ignored) and was generated from the DWG by:

```
node /Users/rejoesudarsan/Dev/networker-space/blender/extract_openings.mjs
```

The extractor needs `/opt/homebrew/bin/dwg2dxf` and `site/node_modules`, which provides `dxf-parser` and `polygon-clipping`. Re-run it only if the DWG changes.

How it works:

- It reuses the DXF reading, wall pairing and floor origin from `site/scripts/build-house.mjs`, so its coordinates match the GLBs.
- It finds each door from the `door` layer. Doors are DOOR/DOOR1 blocks and loose swing arcs: the hinge is the arc centre and the closed leaf spans the wall gap. Pairs of leaves are merged into double doors.
- It measures the jambs against the wall outlines.
- It also lists two other kinds of opening:
  - `gaps`: wall gaps of 1 to 8 ft with no door symbol, such as archways and passages. These get a lintel at 7 ft; switch with `GAP_HEADS = "all" | "perimeter" | "none"`.
  - `slivers`: gaps under 1 ft between wall strips, which are drafting artefacts. These are filled full height; switch with `FILL_SLIVERS`.
- If the JSON file is missing, `build_house.py` warns and the door gaps stay full height.

## Output

- `blender/space-house.blend` is the scene, in metres. It is saved before rendering, so it survives a render crash.
- `blender/renders/01-dawn.png` is the street view at 50 mm, with level verticals.
- `blender/renders/02-angle.png` is a street-level view from the front-left corner at 35 mm, looking up the facade like photo p03.
- `blender/renders/03-top.png` is an orthographic top-down view of the plot. The street is on the right. To make the floor plans read, this view hides:
  - the roof and the haze
  - the window, door and gap heads, so openings show
  - the low sun; the plan is lit by the sky only

All three are PNG, 8-bit RGB, rendered with Cycles, denoised, using the AgX view transform. `renders/` and `*.blend1` are git-ignored.

## Opening the .blend

Run `open /Users/rejoesudarsan/Dev/networker-space/blender/space-house.blend`, or use File > Open in Blender. To look through a camera, pick `Camera.Street`, `Camera.Angle` or `Camera.Top`, then press Ctrl+Numpad 0.

Scene layout:

- `House/Basement`, `House/Ground`, `House/First`, `House/Second` each hold one floor, parented to an Empty called `Floor.<name>`. The Empty is scaled by 2.4384, so its children are in model units. Move the Empty to move the whole floor.
- Each floor contains:
  - `walls`, `columns` and `sills` from the GLB
  - `windowHeads`, `windowFrames` and `windowGlass`
  - `doorHeads`, `gapHeads` and `sliverFill`
  - the slab: terrazzo on top, plaster on its edges and underside
- `House/Ground` also holds `plinthSkirt`, `gateSteps`, `frontWall`, `copings` and `streetGate`.
- `House/Roof` holds the roof. `Floor.roof` is a child of `Floor.second`.
- `Site` holds:
  - the street disc
  - `Site.OfficeGate`, under the `Site.Units` Empty
  - the sun and the three cameras
  - the fog box, which is drawn as wireframe
- `Detail` holds the door swings and stair lines. It is hidden.

All numbers are in the constants block at the top of the script.

## Not built yet: confirm these positions first

Coordinates are floor-local Three.js units (x to the east, z toward the street; 1 unit = 8 ft). The cladding and window-box positions are rough estimates read off the board and the photos. The railing and tree positions come from the site code.

- **Grey cladding strip.** The full-height grey band on the street facade, right of centre on the board, carried up as the box around the second-floor window.
  - Front face of the first and second floors, at about ground-frame x 0.3 to 1.4, from the ground slab to the roof parapet.
  - Charcoal-grey textured plaster, not steel.
- **Window boxes.** The deep plaster frames that project around the street-facing windows on the board and in p03.
  - About 0.12 units deep, 0.06 thick.
  - Around the front windows of the first and second floors.
  - The first-floor one also forms the projecting balcony ledge under the window, at the first-floor front, about x -2.0 to -0.3.
- **Terrace railing.** Steel rail on top of the terrace parapet on the second floor.
  - Its open sides: west edge x = -2.29, and the north and south edges from x -2.29 to -0.95.
  - About 0.35 units above the parapet, with three horizontal bars, as on the board.
- **Gulmohars.** Positions in ground-floor units, street-level frame, from `site/src/world/world.js`:
  - flowering, height 3.6: (-4.6, z 6.3)
  - flowering, height 3.3: (5.8, z 6.3)
  - (-9.5, z 9.4)
  - not flowering: (9.8, z 9.4)
  - The board shows only the two front ones, flanking the house.

## Known approximations

- **Openings are approximate.**
  - **Window heads.** Window heads sit at a fixed height: sill 22 in plus 0.86 units. That is the value the site uses, not per-window CAD heights.
  - **Door heads.** Door heads are at 7 ft.
  - **Unmatched gaps.** Wall gaps with no door symbol get a 7 ft lintel. The extractor found none on the outer walls.
  - **Doors the extractor skipped.** A few door-layer items were not matched to a wall gap: sliding or wardrobe line pairs, and the compound gates. `openings.json` lists them under `rejected` and `offsite`.
- **Window frames are coarse.** They are simple boxes (rails, mullions about every 0.42 units, one glass pane) placed on the sill islands. Curved or broad sill areas get a head block but no frame, as on the site.
- **Sills are plaster, not teak.** The wall below each window uses Lime White, because the photos show plaster there. Set `SILL_MATERIAL = "Teak"` to change it back.
- **The roof is lower than the original spec.** It is treated like a floor slab: its top is at +1.45 storeys and it hangs below. The spec had its underside at +1.45, which left a gap above the walls. Set `ROOF_UNDERSIDE = STOREY` for the literal spec.
- **Walls are slightly taller than the spec:** 1.3042 units (storey height minus slab) instead of 1.30.
- **The roof covers the courtyard void.** Set `ROOF_VOIDS` to open it.
- **The roof stops short of the west wall.** Its west edge is at x = -0.95, about 11 cm inside the second-floor west wall face at -0.997. Set `TERRACE_X1 = -0.9974` to make them flush.
- **The street camera is about 56 m away.** At the spec's 22 m, the 50 mm lens can't fit the house. Override it with `CAM_DISTANCE_M` and `CAM_AIM_Z_M`.
- **The haze is a finite fog box.** It is 160×160×60 m with a density of 0.005 per metre. The spec's 0.012 read muddy at this distance. Set `FOG_MODE = 'world'` for a world volume instead.
- **The sun is stronger than the spec:** 4 instead of about 2, to get the bright facade on the board.
- **Not modelled:** slab overhang profiles, furniture, people and trees.
