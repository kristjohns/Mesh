"""Synthesize every narration beat with Kokoro (ONNX) and record its duration.

usage: python tools/tts.py [--speed 1.0] [--voice af_heart] [--only id1,id2]
Writes build/audio/<id>.wav (24 kHz mono) and build/audio/durations.json.
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from narration import SCENES, TTS_SUBS  # noqa: E402

MODELS = os.environ.get("KOKORO_DIR", os.path.join(ROOT, "build", "models"))
OUT = os.path.join(ROOT, "build", "audio")


def fill_placeholders(text):
    summ = os.path.join(ROOT, "assets", "fea", "summary.json")
    if "{" not in text:
        return text
    if not os.path.exists(summ):
        return None
    s = json.load(open(summ))
    return text.format(PIPE_VM=s["narr_pipe_vm"], PEAK_VM=s["narr_peak_vm"])


def spoken(text):
    for a, b in TTS_SUBS:
        text = text.replace(a, b)
    # "0.577" -> "zero point five seven seven" is read correctly; make sure dashes become pauses
    text = re.sub(r"\s+", " ", text).strip()
    return text


def cap_pauses(a, sr, max_pause=0.30, thr=0.004, win_s=0.02):
    """Shorten internal silences longer than `max_pause` (keeps natural cadence, tighter pacing)."""
    win = int(win_s * sr)
    n = len(a) // win
    if n < 3:
        return a
    e = np.sqrt((a[:n * win].reshape(n, win) ** 2).mean(1))
    sil = e < thr
    keep = np.ones(len(a), dtype=bool)
    i = 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            run = (j - i) * win_s
            if run > max_pause and i > 0 and j < n:
                cut = int((run - max_pause) * sr)
                mid = (i * win + j * win) // 2
                keep[mid - cut // 2: mid - cut // 2 + cut] = False
            i = j
        else:
            i += 1
    return a[keep]


def trim(a, sr, thr_db=-50.0, pad=0.04):
    env = np.abs(a)
    thr = 10 ** (thr_db / 20) * max(env.max(), 1e-9)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return a
    i0 = max(0, idx[0] - int(pad * sr))
    i1 = min(len(a), idx[-1] + int(pad * sr))
    return a[i0:i1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    os.makedirs(OUT, exist_ok=True)
    dpath = os.path.join(OUT, "durations.json")
    durs = json.load(open(dpath)) if os.path.exists(dpath) else {}
    only = set(x for x in args.only.split(",") if x)

    for scene, segs in SCENES:
        for sid, text in segs:
            if only and sid not in only:
                continue
            t = fill_placeholders(text)
            if t is None:
                print(f"skip {sid} (needs FEA summary)")
                continue
            a, sr = k.create(spoken(t), voice=args.voice, speed=args.speed, lang="en-us")
            a = cap_pauses(trim(np.asarray(a, dtype=np.float32), sr), sr)
            # loudness normalisation to a common RMS (speech-active part)
            rms = np.sqrt(np.mean(a[np.abs(a) > 0.01] ** 2)) if np.any(np.abs(a) > 0.01) else 0.1
            a = np.clip(a * (0.085 / rms), -0.98, 0.98)
            sf.write(os.path.join(OUT, f"{sid}.wav"), a, sr, subtype="PCM_16")
            durs[sid] = round(len(a) / sr, 3)
            print(f"{scene:20s} {sid:5s} {durs[sid]:6.2f}s", flush=True)
            json.dump(durs, open(dpath, "w"), indent=1)
    tot = sum(durs.values())
    print(f"TOTAL {tot:.1f}s = {tot / 60:.2f} min over {len(durs)} beats")


if __name__ == "__main__":
    main()
