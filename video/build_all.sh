#!/bin/bash
# Render all scenes at 1080p30, 4 in parallel
cd /home/user/Mesh/video
printf "%s\n" "s07_aps.py S07APS" "s04_hcf.py S04HCF" "s06_fea.py S06FEA" "s05_lcf.py S05LCF" "s03_regimes.py S03Regimes" "s02_basics.py S02Basics" "s01_intro.py S01Intro" "s08_summary.py S08Summary" \
  | xargs -P 4 -L 1 ./render.sh h
