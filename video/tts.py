"""Generate narration audio per segment with Kokoro (ONNX) and build per-scene
tracks plus a timing file used to synchronise the animations.

Usage: python tts.py <kokoro_model_dir>
"""
import os, sys, json
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from script import SCENES, spoken

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "audio")
VOICE, SPEED, LANG = "af_heart", 1.0, "en-us"
SR = 24000
LEAD, GAP, TAIL = 0.6, 0.45, 0.9      # seconds


def main(model_dir):
    k = Kokoro(os.path.join(model_dir, "kokoro-v1.0.onnx"), os.path.join(model_dir, "voices-v1.0.bin"))
    os.makedirs(AUD, exist_ok=True)
    timing = {}
    only = set(sys.argv[2:])
    for sid, segs in SCENES:
        if only and sid not in only:
            continue
        pieces = [np.zeros(int(LEAD * SR), np.float32)]
        t = LEAD
        seg_t = {}
        for gid, text in segs:
            fn = os.path.join(AUD, f"{sid}_{gid}.wav")
            samples, sr = k.create(spoken(text), voice=VOICE, speed=SPEED, lang=LANG)
            assert sr == SR
            # trim leading/trailing near-silence
            a = np.abs(samples)
            nz = np.nonzero(a > 0.01 * a.max())[0]
            samples = samples[max(nz[0] - 600, 0): min(nz[-1] + 1200, len(samples))]
            sf.write(fn, samples, SR)
            d = len(samples) / SR
            seg_t[gid] = {"start": round(t, 3), "dur": round(d, 3), "text": text}
            pieces.append(samples.astype(np.float32))
            t += d
            pieces.append(np.zeros(int(GAP * SR), np.float32))
            t += GAP
        pieces.append(np.zeros(int((TAIL - GAP) * SR), np.float32))
        t += TAIL - GAP
        track = np.concatenate(pieces)
        sf.write(os.path.join(AUD, f"{sid}.wav"), track, SR)
        timing[sid] = {"total": round(len(track) / SR, 3), "segments": seg_t}
        print(f"{sid}: {len(track)/SR:.1f} s")
    tf = os.path.join(AUD, "timing.json")
    old = json.load(open(tf)) if (only and os.path.exists(tf)) else {}
    old.update(timing)
    json.dump(old, open(tf, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
