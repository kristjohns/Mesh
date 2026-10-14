#!/bin/bash
# Render scene chunks with N parallel workers (longest first).
#   ./render_all.sh                      -> the FEA video (build/chunks)
#   VIDEO=fatigue ./render_all.sh        -> the fatigue video (build/fatigue/chunks)
cd "$(dirname "$0")"
N=${N:-3}
VIDEO=${VIDEO:-fea}
if [ "$VIDEO" = "fatigue" ]; then
  DEF="f09_sncurve f07_hotspot f02_basics f11_check f10_miner f08_rainflow f05_seastates f04_hotspots f01_cold f12_sensitivity f06_transfer f03_roadmap f13_outro"
  LOGS=build/fatigue/logs
else
  DEF="s09_soil s05_solids s07_meshsize s10_template s11_wellhead s04_families s06_axisym s02_system s12_soilbc s03_strategy s01_intro s08_welds s13_verify s14_outro"
  LOGS=build/logs
fi
SCENES=${SCENES:-$DEF}
mkdir -p $LOGS
echo $SCENES | tr ' ' '\n' | xargs -P $N -I{} sh -c "node render.mjs --video $VIDEO --scene {} > $LOGS/{}.log 2>&1; echo \"done {} \$(date +%T)\""
