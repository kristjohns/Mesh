#!/bin/bash
# Render Manim scenes in parallel.
#   tools/render_scenes.sh <quality: l|h> <parallel jobs> Scene1 Scene2 ...
# quality l = 854x480@15 (preview), h = 1920x1080@30 (final)
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
MANIM="${MANIM:-manim}"
Q="$1"; P="$2"; shift 2
declare -A FILE=(
  [S01_Opening]=s01_opening.py [S02a_Micro]=s02_micro.py [S02b_Decomposition]=s02_micro.py
  [S03a_Derivation]=s03_derivation.py [S03b_RMSShear]=s03_derivation.py [S03c_Cartesian]=s03_derivation.py
  [S04a_CasesAB]=s04_cases.py [S04b_CasesCD]=s04_cases.py [S04c_CaseE]=s04_cases.py
  [S05_YieldSurface]=s05_surface.py [S06_Tresca]=s05_surface.py
  [S07a_FEAModel]=s07_fea.py [S07b_FEAMethod]=s07_fea.py [S07c_FEAResults]=s07_fea.py [S07d_FEAPitfalls]=s07_fea.py
  [S08_Design]=s08_design.py [S09_Conclusion]=s08_design.py )
if [ "$Q" = "h" ]; then FLAGS="-r 1920,1080 --fps 30"; else FLAGS="-ql"; fi
mkdir -p "$HERE/build/logs"
cd "$HERE/scenes"
for s in "$@"; do echo "$s"; done | xargs -P "$P" -I{} bash -c \
  "$MANIM $FLAGS ${FILE[S01_Opening]:+} \$(python3 -c \"import sys; d=dict(x.split('=') for x in sys.argv[2:]); print(d[sys.argv[1]])\" {} $(for k in "${!FILE[@]}"; do printf '%s=%s ' "$k" "${FILE[$k]}"; done)) {} > $HERE/build/logs/{}_$Q.log 2>&1; echo \"{} exit=\$?\""
