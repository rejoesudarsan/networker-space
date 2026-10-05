Build the Blender model of the house with its details, one checklist item per iteration.

Context: `blender/README.md` (pipeline), `blender/DETAILS.md` (checklist and rules), `PHOTO-LABELS.md`, `docs/house-understanding/`. Blender runs on this host as `/snap/bin/blender` (5.2 LTS); fall back to `/usr/bin/blender` (4.0) if the snap one fails to start. Work in `/home/bb/projects/networker-space`.

Each iteration, do exactly this:
1. Read `blender/DETAILS.md`. Pick the FIRST unchecked item. If every item is checked, output `<promise>DETAILS COMPLETE</promise>` and stop.
2. Look at the photo(s) and plan it cites (Read the jpg/png). Look at the last renders in `blender/renders/` to see the current state.
3. Implement it as `blender/details/<slug>.py` following the rules in DETAILS.md. Keep the change to that file plus the registration and the one call site.
4. Preview before building. Render a close-up of just the new detail on the last saved scene (about 15 s):
   `/snap/bin/blender -b blender/space-house.blend --python blender/tools/preview.py -- <module> 2>&1 | grep -E "\[preview\]|Error|Traceback"`
   Read `blender/renders/preview-<module>-1.png` (close-up) and `-2.png` (context). Compare with the cited photo. If it is wrong, in the wrong place, or missing, fix the module and preview again. Use `--dir sx,sy,sz` to look from another side (e.g. `--dir 0,-1,0.3` from the street, `--dir 0,0,1` from above). For anything inside the house add `--cut <floor>` to hide the floors above it (e.g. `--cut ground`). Do not run the full build until the preview looks right.
5. Full build with quick renders:
   `/snap/bin/blender -b --factory-startup --python blender/build_house.py -- --quick 2>&1 | grep -E "\[build_house\]|Error|Traceback" | tail -30`
   If it errors, or logs `detail <module> FAILED`, fix and rebuild. Never tick an item whose build fails. Read the three renders in `blender/renders/` to confirm nothing else broke.
6. Tick the item in `blender/DETAILS.md`, add a one-line note under it if something was approximated, and commit: `git add -A blender && git commit -m "blender: <slug>"`, ending the message with the Co-Authored-By line from your attribution instructions. Do not push.
7. Append one line to `blender/LOG.md`: the real time from `date '+%F %H:%M'`, slug, build time, what was approximated.

Keep iterations short: one item, one commit. Do not refactor unrelated code. Do not rewrite `build_house.py` structure. If the same item fails three iterations in a row (check LOG.md), mark it `[-] skipped: <reason>` and move on.
