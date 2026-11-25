#!/bin/bash
# usage: render.sh <quality: l|h> <scene_file> <SceneClass>
Q=$1; F=$2; C=$3
cd /home/user/Mesh/video/scenes
manim -q$Q --disable_caching --media_dir /home/user/Mesh/video/build/media_$C "$F" "$C" > /home/user/Mesh/video/build/log_${C}_${Q}.txt 2>&1
echo "$C ($Q) exit $?"
