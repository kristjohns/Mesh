#!/bin/bash
# contact sheet of a preview render: tools/sheet.sh <Scene> [seconds between frames] [quality dir]
S=$1; I=${2:-5}; Q=${3:-480p15}
f=$(ls build/media/videos/*/$Q/$S.mp4 | head -1)
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
ffmpeg -v error -y -i "$f" -vf "fps=1/$I,scale=640:-1,drawtext=text='%{pts\:hms}':x=8:y=8:fontcolor=white:fontsize=18:box=1:boxcolor=black@0.5,tile=4x5:padding=4" -frames:v 1 build/sheet_$S.png
echo "$S duration $d s -> build/sheet_$S.png"
