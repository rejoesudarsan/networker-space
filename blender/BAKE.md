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
- Production settings are `--res 4096 --samples 256` for floors (first and second ran past 90 min at 256: use 192 for them) and `--res 2048 --samples 192` for roof and site. Lower them only if a bake takes more than 90 minutes, and note it.
- Commit the outputs and push to `main`, so the Mac thread can pull them.
- A part needs a re-bake whenever a fit-out module that builds on its floor changes after its atlas was baked. The **Re-bake** section lists these. Add a line there when `git log` shows such a change.

## Room dioramas (the homepage's room scenes; `--rooms`, from site/src/space/rooms.json)
Every space is baked alone, cut to the same kind of box, with identical light, so they read as one set (user request, 5 Oct 2026). Production: `--rooms <id> --res 2048 --samples 256`.
- [x] room-lower-day (slab underside takes ~9% of the atlas, never seen from above; left for texel-density)
- [x] room-cafe-day (hidden base floor plane 1.3 mm under the planks bakes black, ~4% of the atlas; never visible)
- [x] room-court-day (the double-height void at the north-west reads as an open hole, since rooms bake alone; the wicker pendant hangs in it)
- [x] room-event-day
- [x] room-terrace-day (small wall fixtures read as soft dark smudges at this texel density; see texel-density)

## Day set (whole floors: the street views)
- [x] basement-day
- [x] ground-day (.bin 7.6 MB, close to the 8 MB budget)
- [x] first-day (bake took 100 min at 4096/256, over the 90 min line; kept, but bake first-night at --samples 192)
- [x] second-day (103 min at 4096/256, over the 90 min line; kept, but bake second-night at --samples 192)
- [x] roof-day (no main room: checked the unlit view and atlas)
- [x] site-day (gulmohar leaves + blossom moved to site-fixtures in flat colour; site-day.bin 9.1 MB and site-fixtures.bin 9.6 MB, over budget: see web-size)

## Night set (sun off, sky at 4%, lamps and glow materials at 6x)
- [x] night-light-check: render ground and first at night with `room_shot.py --engine cycles`. Pick emission strength and exposure so lamps and lanterns read as warm pools and the rooms are not black. Write the chosen numbers into `set_light("night")`.
  - chosen: sky 4%, glow materials 6x, club lamps at full power (as before), saved at exposure 0 instead of the day's -0.4; checked on Cycles shots of the café and the court and a test bake of the café.
- [x] basement-night
- [x] ground-night
- [ ] first-night
- [ ] second-night
- [ ] roof-night
- [ ] site-night

## Quality
- [ ] texel-density: check the café, court and terrace close-ups in the atlas at 4k. If furniture is blurry, raise the furniture's share of the atlas: scale its UV islands up before packing, or split the floor into two atlases.
- [ ] seams: find visible seams on large walls and floors. Fix them with margin, padding or island orientation.
- [ ] web-size: keep each floor's `.jpg` under 4 MB and `.bin` under 8 MB. Re-encode or decimate if they are bigger.

## Re-bake (append: `- [ ] <part>-<set>: <module> changed <date>`)
- [ ] room-lower-day: basement_work_games changed 2026-10-05 (office -> lounge with RC football)
- [ ] room-court-day: bake_site.py now bakes the entourage in (two people in the court) 2026-10-06
- [ ] room-terrace-day: bake_site.py now bakes the entourage in (woman on the bench) 2026-10-06
- [ ] room-cafe-day: short walls, buried faces dropped, coffee counter moved 2026-10-06
- [ ] room-event-day: short walls, buried faces dropped 2026-10-06
- [ ] basement-day: short walls, buried faces dropped 2026-10-06
- [ ] ground-day: short walls, club_rooms, café counter 2026-10-06
- [ ] first-day: short walls, club_rooms 2026-10-06
- [ ] second-day: short walls, club_rooms 2026-10-06
- [ ] roof-day: buried faces dropped 2026-10-06
- [ ] site-day: busy street (entourage) 2026-10-06
- [ ] basement-night: short walls, buried faces dropped 2026-10-06
- [ ] ground-night: short walls, club_rooms, café counter 2026-10-06
