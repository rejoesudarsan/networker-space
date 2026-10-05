Build the Blender model of the house with its details, one checklist item per iteration.

Context: `blender/README.md` (pipeline), `blender/DETAILS.md` (checklist and rules), `PHOTO-LABELS.md`, `docs/house-understanding/`. Blender runs on this host as `/snap/bin/blender` (5.2 LTS); fall back to `/usr/bin/blender` (4.0) if the snap one fails to start. Work in `/home/bb/projects/networker-space`.

Each iteration, do exactly this:
1. Read `blender/DETAILS.md`. Pick the FIRST unchecked item. If every item is checked, output `<promise>DETAILS COMPLETE</promise>` and stop.
2. Look at the photo(s) and plan it cites (Read the jpg/png). Look at the last renders in `blender/renders/` to see the current state.
3. Implement it as `blender/details/<slug>.py` following the rules in DETAILS.md. Keep the change to that file plus the registration and the one call site.
4. Build and render quick views:
   `/snap/bin/blender -b --factory-startup --python blender/build_house.py -- --quick 2>&1 | grep -E "\[build_house\]|Error|Traceback" | tail -30`
   If it errors, fix and rebuild. Never tick an item whose build fails.
5. Read the renders (`blender/renders/*.png`) and judge whether the item is visible, in the right place, and plausible against the photo. If not, adjust once and rebuild. If the item is not visible in any of the three default cameras, add a render view for it in your detail file (see `detail-cameras`).
6. Tick the item in `blender/DETAILS.md`, add a one-line note under it if something was approximated, and commit: `git add -A blender && git commit -m "blender: <slug>"`. Do not push.
7. Append one line to `blender/LOG.md`: date, slug, build time, what was approximated.

Keep iterations short: one item, one commit. Do not refactor unrelated code. Do not rewrite `build_house.py` structure. If the same item fails three iterations in a row (check LOG.md), mark it `[-] skipped: <reason>` and move on.
