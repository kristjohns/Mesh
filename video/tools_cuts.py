"""Choose the split points of the web player so every part stays under the artifact file limit.

Two steps around assemble.py:
  python3 tools_cuts.py [--video fatigue] candidates   -> <build>/kf_candidates.json: one keyframe in every
                                                          narration pause (between lines and scenes)
  python3 assemble.py [--video fatigue] --keyframes <build>/kf_candidates.json
  python3 tools_cuts.py [--video fatigue] choose       -> the cuts file of the project (web/*cuts.json):
                                                          the candidates that keep each part under LIMIT,
                                                          measured from the packet sizes of the master
Cuts always sit in a pause, so a part boundary never falls inside a spoken sentence.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from projects import project  # noqa: E402

P = project()
BUILD = P["build_dir"]
FPS = 30
LIMIT = 13.6e6          # bytes per part, video + audio, under the 15 MB file limit with room for the muxer
AUDIO_BPS = 160e3 / 8   # the AAC rate tools_webparts.py uses per part
CAND = os.path.join(BUILD, "kf_candidates.json")


def pauses():
    """mid-points of the gaps between narration lines, on the global timeline of the assembled video"""
    edl = json.load(open(os.path.join(BUILD, "edl.json")))
    timing = {s["id"]: s for s in json.load(open(P["timing_path"]))["scenes"]}
    spans = []
    for sid, off in zip(edl["ids"], edl["offsets"]):
        for ln in timing[sid]["lines"]:
            spans.append((off + ln["start"], off + ln["start"] + ln["dur"]))
    spans.sort()
    out = []
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        if b0 - a1 >= 0.35:
            out.append(round((a1 + b0) / 2 * FPS) / FPS)
    return out, edl


def packets(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "packet=pts_time,size", "-of", "csv=p=0", path]).decode()
    rows = []
    for line in out.splitlines():
        t, s = line.split(",")[:2]
        rows.append((float(t), int(s)))
    rows.sort()
    return rows


def main():
    mode = [a for a in sys.argv[1:] if a in ("candidates", "choose")]
    mode = mode[0] if mode else "candidates"
    cands, edl = pauses()
    if mode == "candidates":
        json.dump(cands, open(CAND, "w"))
        print(len(cands), "candidate keyframes ->", CAND)
        return
    total = round((edl["offsets"][-1] + edl["durations"][-1]) * FPS) / FPS
    pk = packets(P["out_path"])
    times = [t for t, _ in pk]
    cum = [0]
    for _, s in pk:
        cum.append(cum[-1] + s)
    import bisect

    def size(t0, t1):
        i0, i1 = bisect.bisect_left(times, t0 - 1e-6), bisect.bisect_left(times, t1 - 1e-6)
        return cum[i1] - cum[i0] + (t1 - t0) * AUDIO_BPS
    cuts, start = [], 0.0
    pts = cands + [total]
    for c in pts:
        while size(start, c) > LIMIT:
            prev = [p for p in cands if start < p < c]
            if not prev:
                raise SystemExit(f"no pause between {start:.1f}s and {c:.1f}s keeps a part under the limit")
            cuts.append(prev[-1])
            start = prev[-1]
    json.dump(cuts, open(P["cuts_path"], "w"))
    bounds = [0.0] + cuts + [total]
    for a, b in zip(bounds, bounds[1:]):
        print(f"{a:8.2f} - {b:8.2f}  {size(a, b) / 1e6:5.2f} MB")
    print(len(cuts) + 1, "parts ->", P["cuts_path"])


if __name__ == "__main__":
    main()
