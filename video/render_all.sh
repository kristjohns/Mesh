#!/bin/bash
# Render all scene chunks with N parallel workers (longest first).
cd "$(dirname "$0")"
N=${N:-3}
SCENES=${SCENES:-"s09_soil s05_solids s07_meshsize s10_template s11_wellhead s04_families s06_axisym s02_system s12_soilbc s03_strategy s01_intro s08_welds s13_verify s14_outro"}
echo $SCENES | tr ' ' '\n' | xargs -P $N -I{} sh -c 'node render.mjs --scene {} > build/logs/{}.log 2>&1; echo "done {} $(date +%T)"'
