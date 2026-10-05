# Baked light for the website: checklist

Worked by a Ralph loop on Hetzner (bb-hetzner), one item per iteration (prompt: `blender/BAKE-RALPH.md`).
The site shows each floor as a single unlit mesh with its light baked into an atlas.
`blender/tools/bake_site.py` produces them in `site/public/models/baked/`:

- `<part>-<set>.gltf` plus `.bin` and `.jpg`
- `<part>-fixtures.gltf`, which holds glass and lamps

Parts are basement, ground, first, second, roof and site. Sets are day and night.

Markers: `[ ]` to do, `[x]` done, `[-]` skipped after three failures, `[?]` needs the user.

Rules:
- Bake from a fresh build. `git pull`, then `build_house.py -- --no-render`, then bake. Never bake a stale `space-house.blend`.
- **Done** means four things:
  1. The atlas has no black or garbage islands.
  2. A `tools/room_shot.py` Cycles render of the floor and the baked atlas agree in brightness and colour.
  3. There are no light leaks, which show as bright seams where walls meet the slab.
  4. There are no blotches left by the denoiser.
- Production settings are `--res 4096 --samples 256` for floors and `--res 2048 --samples 192` for roof and site. Lower them only if a bake takes more than 90 minutes, and note it.
- Commit the outputs and push to `main`, so the Mac thread can pull them.
- A part needs a re-bake whenever a fit-out module that builds on its floor changes after its atlas was baked. The **Re-bake** section lists these. Add a line there when `git log` shows such a change.

## Room dioramas (the homepage's room scenes; `--rooms`, from site/src/space/rooms.json)
Every space is baked alone, cut to the same kind of box, with identical light, so they read as one set (user request, 5 Oct 2026). Production: `--rooms <id> --res 2048 --samples 256`.
- [ ] room-lower-day
- [ ] room-cafe-day
- [ ] room-court-day
- [ ] room-event-day
- [ ] room-terrace-day

## Day set (whole floors: the street views)
- [ ] basement-day
- [ ] ground-day
- [ ] first-day
- [ ] second-day
- [ ] roof-day
- [ ] site-day

## Night set (sun off, sky at 4%, lamps and glow materials at 6x)
- [ ] night-light-check: render ground and first at night with `room_shot.py --engine cycles`. Pick emission strength and exposure so lamps and lanterns read as warm pools and the rooms are not black. Write the chosen numbers into `set_light("night")`.
- [ ] basement-night
- [ ] ground-night
- [ ] first-night
- [ ] second-night
- [ ] roof-night
- [ ] site-night

## Quality
- [ ] texel-density: check the café, court and terrace close-ups in the atlas at 4k. If furniture is blurry, raise the furniture's share of the atlas: scale its UV islands up before packing, or split the floor into two atlases.
- [ ] seams: find visible seams on large walls and floors. Fix them with margin, padding or island orientation.
- [ ] web-size: keep each floor's `.jpg` under 4 MB and `.bin` under 8 MB. Re-encode or decimate if they are bigger.

## Re-bake (append: `- [ ] <part>-<set>: <module> changed <date>`)
