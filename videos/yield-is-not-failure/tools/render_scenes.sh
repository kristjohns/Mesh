#!/bin/bash
# Render Manim scenes in parallel.
#   tools/render_scenes.sh <quality: l|h> <parallel jobs> Scene1 Scene2 ...
# quality l = 854x480@15 (preview), h = 1920x1080@30 (final)
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
MANIM="${MANIM:-manim}"
Q="$1"; P="$2"; shift 2
declare -A FILE=(
  [Y00_Open]=y00_open.py [Y01_Why]=y00_open.py [Y02_Method]=y02_method.py
  [Y03_Plate]=y03_plate_beam.py [Y04_Beam]=y03_plate_beam.py
  [Y05_Cylinder]=y05_cyl_fillet.py [Y06_Fillet]=y05_cyl_fillet.py
  [Y07_Bree]=y07_bree_criteria.py [Y08_Criteria]=y07_bree_criteria.py )
if [ "$Q" = "h" ]; then FLAGS="-r 1920,1080 --fps 30"; else FLAGS="-ql"; fi
mkdir -p "$HERE/build/logs"
cd "$HERE/scenes"
for s in "$@"; do echo "$s"; done | xargs -P "$P" -I{} bash -c \
  "$MANIM $FLAGS \$(python3 -c \"import sys; d=dict(x.split('=') for x in sys.argv[2:]); print(d[sys.argv[1]])\" {} $(for k in "${!FILE[@]}"; do printf '%s=%s ' "$k" "${FILE[$k]}"; done)) {} > $HERE/build/logs/{}_$Q.log 2>&1 || $MANIM $FLAGS \$(python3 -c \"import sys; d=dict(x.split('=') for x in sys.argv[2:]); print(d[sys.argv[1]])\" {} $(for k in "${!FILE[@]}"; do printf '%s=%s ' "$k" "${FILE[$k]}"; done)) {} > $HERE/build/logs/{}_$Q.log 2>&1; echo \"{} exit=\$?\""
