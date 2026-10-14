"""Generate narration audio per line with Kokoro TTS and write scene timing.

Usage: python3 tts.py [--video fatigue] [--only LINE_ID ...]
Outputs: <build>/audio/lines/<id>.wav (24 kHz mono) and the timing json of the video (projects.py)
"""
import json
import os
import sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from projects import project  # noqa: E402

P = project()
SCRIPT = P["script_path"]
OUT = os.path.join(P["build_dir"], "audio", "lines")
TIMING = P["timing_path"]
MODELS = os.path.join(os.path.dirname(ROOT), "tts_models")


def trim(x, sr, thr=0.004, pad=0.06):
    a = np.abs(x)
    idx = np.where(a > thr)[0]
    if len(idx) == 0:
        return x
    s = max(0, idx[0] - int(pad * sr))
    e = min(len(x), idx[-1] + int(pad * sr))
    return x[s:e]


def main():
    only = set(sys.argv[sys.argv.index("--only") + 1:]) if "--only" in sys.argv else None
    cfg = json.load(open(SCRIPT))
    os.makedirs(OUT, exist_ok=True)
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    timing = {"scenes": [], "sr": 24000}
    t_global = 0.0
    for sc in cfg["scenes"]:
        t = sc.get("preroll", 1.0)
        lines = []
        for ln in sc["lines"]:
            path = os.path.join(OUT, ln["id"] + ".wav")
            if not os.path.exists(path) or (only is not None and ln["id"] in only):
                samples, sr = k.create(ln["text"], voice=cfg["voice"], speed=ln.get("speed", cfg["speed"]),
                                       lang="en-us")
                samples = trim(samples, sr)
                sf.write(path, samples, sr)
                print("generated", ln["id"], f"{len(samples) / sr:.2f}s", flush=True)
            info = sf.info(path)
            dur = info.frames / info.samplerate
            lines.append(dict(id=ln["id"], start=round(t, 3), dur=round(dur, 3), text=ln["text"]))
            t += dur + ln.get("pause", 0.5)
        t -= sc["lines"][-1].get("pause", 0.5)
        duration = t + sc.get("postroll", 1.0)
        timing["scenes"].append(dict(id=sc["id"], duration=round(duration, 3), offset=round(t_global, 3),
                                     lines=lines))
        t_global += duration
    timing["total"] = round(t_global, 3)
    with open(TIMING, "w") as fh:
        json.dump(timing, fh, indent=1)
    print(f"total {t_global / 60:.2f} min")


if __name__ == "__main__":
    main()
