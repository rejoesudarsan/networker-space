# Space house in Blender

`build_house.py` builds the house from scratch in Blender 5.2 LTS and renders it against art-direction board 01 (`reference/art-direction/01-dawn-exterior.png`).

## Run

### 1. One-off: download the CC0 assets (about 290 MB)

```
python3 /Users/rejoesudarsan/Dev/networker-space/blender/fetch_assets.py
```

- This downloads the HDRI, seven texture sets and the tree model into `blender/assets/`. It then writes `assets/manifest.json` and `assets/LICENSES.md`.
- Files already on disk are skipped.
- `--no-tree` skips the 215 MB tree model.
- The asset folders are git-ignored; only the manifest and licence list are kept.
- Without the assets, the script still runs: it falls back to procedural materials and a gradient sky, and leaves out the trees.

### 2. Quick iteration render

32 samples at half resolution:

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py -- --quick
```

### Other runs

Full quality: 256 samples at 1536×1024.

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py
```

Build and save only, with no render:

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python /Users/rejoesudarsan/Dev/networker-space/blender/build_house.py -- --no-render
```

The script tries the Metal GPU first and falls back to the CPU. The `[build_house]` lines in the terminal report counts, warnings and every provisional element with its position.

## Output (`blender/renders/`)

| file | what |
|---|---|
| `01-dawn.png` | Street elevation at 50 mm. It is framed like board 01: level verticals, house centred, roof top at 26% from the top of the frame, street-wall base at 78%. |
| `01-compare.png` | The street render and board 01 side by side at equal height. |
| `01-overlay.png` | A 50% blend of the render and the board, for checking alignment. |
| `02-angle.png` | Street level from the front-left corner at 35 mm, looking up the facade like photo p03. |
| `03-top.png` | Orthographic plan view. The roof, heads, sun, haze and trees are hidden, and the street is on the right. |

`blender/space-house.blend` is saved before rendering.

## Data files

- **`data/openings.json`** comes from `node blender/extract_openings.mjs`. It reads the DWG with `/opt/homebrew/bin/dwg2dxf` and `site/node_modules`, and contains, per floor:
  - door, gap and sliver rectangles
  - window sill polygons
  - `slabTrim` notches: slab overhangs on the front and side edges cut back to about 30 cm past the wall. Overhangs deeper than about 1.3 m are treated as real balconies or terraces and kept, along with the second-floor terrace and the first-floor entrance-court balcony.
- **`assets/manifest.json`** is written by `fetch_assets.py`.

## How the look is built

- **Light.** The scene is lit by a Poly Haven sunrise HDRI tinted toward #E9C9C0 and rotated so its sun is in the east-south-east, plus a weak sun lamp (strength 1.5, colour #FFC394).
  - Camera rays see the board's sky gradient instead of the HDRI: #E9C9C0 at the horizon to #CFC6D3 at the top of the frame.
- **Fog.** The default `FOG_MODE = "compositor"` takes the Mist pass (12 m to 122 m, linear) and mixes the image toward #D1BFC2. The sky is left untouched.
  - `FOG_MODE = "domain"` uses a volume box instead, and `"world"` uses a world volume.
- **Street.** The street shader fades into an emissive fog colour from about 4.5 m in front of the compound wall, and to the sides beyond 11 m. The street therefore dissolves just before the wall, as on the board.
- **Colour.** The view transform is Khronos PBR Neutral, so palette colours stay close to their hex values. It falls back to AgX if that transform is missing.
- **Textures.** These are CC0 image textures on a per-object `BoxUV` map, made by box projection in metres. Each texture is tinted so its average colour matches the board 08 palette hex.
  - Plaster, teak, the grey cladding panel, sandstone, terracotta tile, asphalt and painted steel are textured.
  - Terrazzo, red oxide and foliage stay procedural.
- **Bevels.** Walls, columns, slab edges, heads, parapets, copings, window boxes, cladding and the compound wall get a Bevel modifier: 1.5 cm, 2 segments, 30° angle limit.
  - The GLBs are imported with flat shading, so faces stay flat.

## Provisional elements: confirm or correct the constants

All coordinates are Three.js plan units in the ground-floor frame (x to the east, z toward the street; 1 unit = 8 ft = 2.4384 m) unless marked floor-local. The terminal summary prints every one of them with its exact position.

| element | constant(s) | assumed plan element / position |
|---|---|---|
| Street compound wall, 1.5 m, plastered, coping, piers | `COMPOUND_*`, `PIER_*`, `SIDE_WALL_Z` | Front plot line at z 5.85, just in front of the gate steps (z 5.05–5.76), from x -3.30 to 3.25. Short side returns run back to the ground slab edge (z 5.0). |
| Pedestrian gate | `COMPOUND_GATES[0]` | x -3.10 to -2.35, in front of the entrance steps at x -2.75 |
| Vehicle gate | `COMPOUND_GATES[1]` | x -1.85 to -0.20, the parking-ramp notch in the ground slab |
| Office gate | `COMPOUND_GATES[2]` | x 1.25 to 3.05, the office-court notch in the ground slab |
| Gates | `GATE_*` | Charcoal steel, horizontal slats, 1.40 m high |
| Concrete pergola over the pedestrian gate (photo p05) | `PERGOLA_*` | x -3.32 to -2.12, z 5.0 to 5.95, top at 2.65 m |
| Plot boundary wall cut down to a kerb about 20 cm high (0.08 units) | `BOUNDARY_CUT_X`, `BOUNDARY_WALL_H` | Ground-floor walls west of x -2.95, along the side-passage boundary. This is the long blank wall on the left of the old render. |
| Window reveals | `WIN_REVEAL` | Frames and glass set 15 cm in from each window's outer wall face |
| Window boxes and sunshades | `WINDOW_BOX_*`, `SUNSHADE_*` | Street windows within 2 m of the front face (Three z 3.314), at least 0.6 m wide: 40 cm deep, 10 cm frame, sunshade 20 cm further out. Ground: x -0.78 to -0.23, -0.12 to 0.16, 1.31 to 2.42. First: x -1.06 to -0.22, -0.11 to 0.19, 1.31 to 2.46. Second: x -0.50 to -0.22. |
| Grey cladding box | `CLADDING_BOXES` | Around the second-floor window at x 0.63 to 1.63, running from the front face back to the window (about 0.8 m deep) |
| Grey cladding strip | `CLADDING_STRIPS` | Street face z 3.314. First floor x 0.25 to 1.25, between the centre and right windows. Second floor x 0.25 to 0.50, up to the parapet. |
| Slab overhang trims | `extract_openings.mjs` (`OVERHANG_IN`, `MAX_TRIM_IN`, `KEEP`) | First floor: 7 cuts, front and east edges. Second floor: 6 cuts, front and east edges. Kept: the second-floor terrace, and a first-floor balcony rectangle (floor-local x -2.1 to -1.3, z 0.5 to 2.2) over the entrance court (photo p24). |
| Copings | `COPING_T`, `COPING_OVER` | 5 cm thick, 3 cm overhang, on all parapets and the compound wall |
| Terrace railing | `TERRACE_RAILING`, `RAIL_*` | Charcoal steel with 3 horizontal bars, 0.9 m above the second-floor terrace parapet. It runs along the open west, north and south edges (second-floor-local x -2.29 to -0.95). |
| Two gulmohar stand-ins | `TREES`, `TREE_POSITIONS`, `TREE_HEIGHT_M`, `FLOWER_*` | Poly Haven jacaranda model with about 900 orange-red flower clusters, 9 m tall, on the street outside the wall at x -4.2 and x 4.6, z 6.6 |

## Known approximations

- **Openings.**
  - Window heads use a fixed height (sill plus 0.86 units) and door heads 7 ft, not per-opening heights from the drawings.
  - The window boxes are generic: one plaster frame per street window.
- **Trees.** The trees are a jacaranda model with sphere flower clusters, not a real gulmohar. The 1k glTF ships a JPG leaf texture with no alpha channel, so the alpha is keyed from the texture's brightness.
- **Board alignment.** The board was not drawn to scale, so the overlay will not line up exactly.
  - The camera solve matches only the roof top and the street-wall base.
  - The board's gates, pergola and trees sit wider apart than the plan allows.
- **Roof and walls.** Earlier changes still apply:
  - The roof slab is treated like a floor slab.
  - Walls are 1.3042 units tall.
  - The roof covers the courtyard void.
  - The roof stops short of the west wall (`TERRACE_X1`).
- **Not modelled:** furniture and people.
