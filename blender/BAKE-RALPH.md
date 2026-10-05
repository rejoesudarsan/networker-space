Bake the house's light for the website, one checklist item per iteration.

Context:
- `blender/BAKE.md`: the checklist and its rules.
- `blender/tools/bake_site.py`: the bake. Its options are in the docstring at the top.
- `blender/README.md`: the build pipeline.
- `blender/tools/room_shot.py`: open-topped close-ups of rooms. It supports `--engine cycles`.
- Blender is `/snap/bin/blender` (5.2 LTS). This host has no GPU, so bakes run on the CPU, and that is expected.
- Work in `/home/bb/projects/networker-space` on branch `site-realism`.

Each iteration, do exactly this:
1. Run `git pull --rebase origin site-realism`. Read `blender/BAKE.md` and pick the first `[ ]` item; `[?]` items wait for the user. Then check `git log --since=<date of the last bake commit> -- blender/details`. If a fit-out module changed after the bake of a part it builds on, add a Re-bake line first. If no `[ ]` items remain, output `<promise>BAKE COMPLETE</promise>` and stop.
2. Build fresh: `/snap/bin/blender -b --factory-startup --python blender/build_house.py -- --no-render 2>&1 | grep -E "\[build_house\]|FAILED|Error" | tail -20`. If any detail logs FAILED, note it in `blender/LOG.md` and continue; the item is still baked.
3. Bake the item: `/snap/bin/blender -b blender/space-house.blend --python blender/tools/bake_site.py -- --floors <part> --set <day|night> --res <res> --samples <samples> 2>&1 | grep -E "\[bake\]|Error|Traceback"`.
4. Check the result:
   - Read the atlas jpg.
   - Render a Cycles reference of the main room of that part with room_shot.py and Read it. Main rooms: café on ground `0.56,1.3,2.46,3.25`, court on first `0.76,0.12,2.56,1.74`, office on basement `-0.62,-0.52,2.05,1.93`, terrace on second `-2.36,-3.5,-0.78,3.42`.
   - Look for black islands, leaks, seams and denoiser blotches.
   - If something is wrong, fix `bake_site.py` (UV packing, margins, light set) and re-bake.
   - Never tick an item whose output you have not looked at.
5. Tick the item in `blender/BAKE.md`, adding a one-line note if anything was approximated. Commit only the outputs and the files you changed: `git add blender/BAKE.md blender/LOG.md blender/tools/bake_site.py site/public/models/baked && git commit -m "bake: <item>"`, ending the message with your Co-Authored-By line. Then run `git push origin site-realism`, rebasing first if the push is rejected.
6. Append one line to `blender/LOG.md`: the date and time from `date '+%F %H:%M'`, the item, how long the bake took, and anything approximated.

Keep iterations to one item and one commit. Do not edit fit-out modules, the site code or `build_house.py`; other threads own them. If the same item fails three iterations in a row (check LOG.md), mark it `[-] skipped: <reason>` and move on. If an item needs a decision only the user can make, mark it `[?]` with the question.
