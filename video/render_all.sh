#!/bin/bash
# Render scene chunks with N parallel workers (longest first). Resumable: each chunk is written to
# <id>.part.mp4 and renamed when complete; scenes whose chunk already exists are skipped
# (FORCE=1 re-renders them).
#   ./render_all.sh                      -> the FEA video (build/chunks)
#   VIDEO=fatigue ./render_all.sh        -> the fatigue video (build/fatigue/chunks)
cd "$(dirname "$0")"
N=${N:-3}
VIDEO=${VIDEO:-fea}
if [ "$VIDEO" = "fatigue" ]; then
  DEF="f01_cold f04_hotspots f09_sncurve f02_basics f07_hotspot f11_check f10_miner f08_rainflow f13_outro f05_seastates f12_sensitivity f06_transfer f03_roadmap"
  B=build/fatigue
else
  DEF="s09_soil s05_solids s07_meshsize s10_template s11_wellhead s04_families s06_axisym s02_system s12_soilbc s03_strategy s01_intro s08_welds s13_verify s14_outro"
  B=build
fi
SCENES=${SCENES:-$DEF}
mkdir -p $B/logs $B/chunks
export VIDEO B FORCE
echo $SCENES | tr ' ' '\n' | xargs -P $N -I{} sh -c '
  if [ -z "$FORCE" ] && [ -f $B/chunks/{}.mp4 ]; then echo "skip {}"; exit 0; fi
  node render.mjs --video $VIDEO --scene {} --out $B/chunks/{}.part.mp4 > $B/logs/{}.log 2>&1 \
    && mv $B/chunks/{}.part.mp4 $B/chunks/{}.mp4 && echo "done {} $(date +%T)" || echo "FAILED {}"'
