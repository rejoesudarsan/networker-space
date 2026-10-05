Make the website faster, more polished, clearer in its copy, and lead every visitor to a membership, one checklist item per iteration.

Context: `site/POLISH.md` (checklist and rules), `PRODUCT.md` and `DESIGN.md` (the brief), `reference/art-direction/` (the boards). The site is `site/` (Vite + Three.js). Work in this worktree on its branch; do not touch the main checkout.

Each iteration, do exactly this:
1. Read `site/POLISH.md`. Pick the FIRST `[ ]` item; `[?]` items wait for the user. If no `[ ]` items remain, output `<promise>SITE POLISHED</promise>` and stop.
2. Make sure a dev server for this worktree is running (`cd site && npm install` once, then `npx vite --port 5190 --strictPort` in the background; reuse it if it is already up).
3. Implement the item. Keep the change to what the item needs.
4. `cd site && npm run build` must pass.
5. Look at it: open a headless browser with `bb browser-automation open --backend local --headless --machine <this host id from bb status --json> --json`, load `http://localhost:5190/`, wait ~20 s, and screenshot at desktop (1280×800) and phone (390×844) sizes, ≤ 960 px. Scroll to the beat you changed. If it is wrong, fix it and look again. Close the session when done.
6. Tick the item in `site/POLISH.md` with a one-line note of what changed (and any number measured). Commit: `git add -A site && git commit -m "site: <item>"`, ending the message with the Co-Authored-By line from your attribution instructions. Do not push and do not deploy.
7. Append one line to `site/LOG.md`: the real time from `date '+%F %H:%M'`, the item, and anything approximated or left for the user.

Keep iterations short: one item, one commit. Do not edit `blender/` or `site/public/models/baked/`. If the same item fails three iterations in a row (check site/LOG.md), mark it `[-] skipped: <reason>` and move on. If an item needs a decision only the user can make (prices, tier names, form service, booking link), build what is certain and add a `[?]` item under "Needs your input" with the question.
