#!/usr/bin/env bash
# Watchdog for the overnight Blender details loop. Prints nothing when healthy.
# Reports when: Blender build is stuck (>40 min process), no commit in 90 min while items remain,
# or the loop state file disappeared while items remain.
REPO=/home/bb/projects/networker-space
cd "$REPO" || { echo "repo missing"; exit 1; }
remaining=$(grep -c '^- \[ \]' blender/DETAILS.md)
[ "$remaining" -eq 0 ] && exit 0
now=$(date +%s)
# stuck blender process
for p in $(pgrep -f "blender.*build_house.py"); do
  et=$(ps -o etimes= -p "$p" | tr -d ' ')
  if [ "${et:-0}" -gt 2400 ]; then kill "$p"; echo "killed stuck blender build pid $p after ${et}s"; fi
done
last=$(git log -1 --format=%ct -- blender 2>/dev/null || echo 0)
age=$(( (now - last) / 60 ))
loop=$([ -f .claude/.ralph-loop.local.md ] && echo yes || echo no)
if [ "$age" -gt 90 ] || [ "$loop" = no ]; then
  echo "{\"remaining\":$remaining,\"minutesSinceLastCommit\":$age,\"ralphLoopActive\":\"$loop\"}"
fi
