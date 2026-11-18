"""Assemble the final film: concatenate scene renders, lay the narration on the logged beat times,
add a quiet procedural ambient score (ducked under the voice), subtitles, loudness normalisation.

usage: python tools/assemble.py [--quality 1080p30] [--out build/von_mises_stress.mp4] [--no-music]
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from narration import CAPTION_SUBS, SCENES  # noqa: E402

BUILD = os.path.join(ROOT, "build")
SR = 48000
ORDER = ["S01_Opening", "S02a_Micro", "S02b_Decomposition", "S03a_Derivation", "S03b_RMSShear", "S03c_Cartesian",
         "S04a_CasesAB", "S04b_CasesCD", "S04c_CaseE", "S05_YieldSurface", "S06_Tresca", "S07a_FEAModel",
         "S07b_FEAMethod", "S07c_FEAResults", "S07d_FEAPitfalls", "S08_Design", "S09_Conclusion"]
FILES = {"S01": "s01_opening", "S02": "s02_micro", "S03": "s03_derivation", "S04": "s04_cases", "S05": "s05_surface",
         "S06": "s05_surface", "S07": "s07_fea", "S08": "s08_design", "S09": "s08_design"}
TEXT = {k: v for _, segs in SCENES for k, v in segs}


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def video_path(scene, quality):
    return os.path.join(BUILD, "media", "videos", FILES[scene[:3]], quality, f"{scene}.mp4")


def fill(text):
    s = json.load(open(os.path.join(ROOT, "assets", "fea", "summary.json")))
    return text.replace("{PIPE_VM}", str(s["narr_pipe_vm"])).replace("{PEAK_VM}", str(s["narr_peak_vm"]))


def caption(text):
    t = fill(text)
    for a, b in CAPTION_SUBS:
        t = t.replace(a, b)
    t = re.sub(r"\bsigma\b", "σ", t)
    t = re.sub(r"\btau\b", "τ", t)
    return t


# ------------------------------------------------------------------ music
def ambient_score(n_out, beats_mask, seed=3, sr=12000):
    """Slow minor-key pad (Dm - Bb - F - C), chorus-detuned additive voices, long reverb, ducked under speech.

    Synthesised at 12 kHz (content < 1.5 kHz) and upsampled to the output rate.
    """
    rng = np.random.default_rng(seed)
    SR = sr
    n = int(np.ceil(n_out * sr / 48000)) + 8
    t = np.arange(n) / SR
    hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    chords = [[38, 45, 53, 60, 64], [34, 41, 50, 57, 62], [41, 48, 57, 60, 64], [36, 43, 52, 55, 62]]  # MIDI
    seg = 9.0                                     # seconds per chord
    out = np.zeros(n, dtype=np.float64)
    nseg = int(np.ceil(n / SR / seg)) + 1
    fade = 3.5
    for k in range(nseg):
        notes = chords[k % len(chords)]
        t0 = k * seg - fade
        i0, i1 = max(0, int(t0 * SR)), min(n, int((t0 + seg + 2 * fade) * SR))
        if i0 >= i1:
            continue
        tt = t[i0:i1] - t0
        env = np.clip(tt / fade, 0, 1) * np.clip((seg + 2 * fade - tt) / fade, 0, 1)
        env = env * env * (3 - 2 * env)
        block = np.zeros(i1 - i0)
        for j, m in enumerate(notes):
            f = hz(m)
            amp = (0.9 if j == 0 else 0.55) / len(notes)
            for det in (-0.0017, 0.0018):
                ph = rng.uniform(0, 2 * np.pi)
                lfo = 1 + 0.25 * np.sin(2 * np.pi * (0.05 + 0.03 * j) * tt + ph)
                block += amp * lfo * (np.sin(2 * np.pi * f * (1 + det) * tt + ph) +
                                      0.28 * np.sin(2 * np.pi * 2 * f * (1 + det) * tt + 2 * ph) +
                                      0.08 * np.sin(2 * np.pi * 3 * f * (1 + det) * tt + 3 * ph))
        out[i0:i1] += block * env
    # gentle sub drone on D
    out += 0.12 * np.sin(2 * np.pi * hz(26) * t) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.02 * t))
    # reverb: exponentially decaying noise impulse (2.8 s)
    L = int(2.8 * SR)
    ir = rng.standard_normal(L) * np.exp(-np.arange(L) / (0.7 * SR))
    ir[0] = 6.0
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(out, ir)[:n]
    mix = 0.55 * out + 0.75 * wet
    mix /= np.max(np.abs(mix)) + 1e-9
    mix = resample_poly(mix, 48000 // sr, 1)[:n_out]
    n = n_out
    SR = 48000
    # ducking envelope from the narration mask (attack 0.25 s, release 0.8 s)
    duck = np.where(beats_mask, 0.42, 1.0)
    k_ = int(0.5 * SR)
    win = np.hanning(2 * k_ + 1); win /= win.sum()
    duck = np.convolve(duck, win, mode="same")
    # global fade in/out
    g = np.ones(n)
    g[:int(4 * SR)] = np.linspace(0, 1, int(4 * SR))
    g[-int(6 * SR):] = np.linspace(1, 0, int(6 * SR))
    return (mix * duck * g * 10 ** (-24 / 20)).astype(np.float32)


# ------------------------------------------------------------------ subtitles
def srt_time(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def split_caption(text, maxlen=84):
    sents = re.split(r"(?<=[.:;?!])\s+", text)
    chunks, cur = [], ""
    for s in sents:
        for w in s.split():
            if len(cur) + len(w) + 1 > maxlen and cur:
                chunks.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        if len(cur) > maxlen * 0.55:
            chunks.append(cur); cur = ""
    if cur:
        chunks.append(cur)
    return chunks


def wrap2(s, width=44):
    if len(s) <= width:
        return s
    words = s.split(); best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        sc = max(len(a), len(b))
        if best is None or sc < best[0]:
            best = (sc, a + "\n" + b)
    return best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="1080p30")
    ap.add_argument("--out", default=os.path.join(BUILD, "von_mises_stress.mp4"))
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()

    durs = json.load(open(os.path.join(BUILD, "audio", "durations.json")))
    offsets, total = {}, 0.0
    lst = os.path.join(BUILD, "concat.txt")
    with open(lst, "w") as f:
        for s in ORDER:
            p = video_path(s, a.quality)
            d = probe_duration(p)
            offsets[s] = total
            total += d
            f.write(f"file '{p}'\n")
            print(f"{s:22s} {d:7.2f}s  @ {offsets[s]:7.2f}s")
    print(f"TOTAL {total:.1f}s = {total / 60:.2f} min")

    n = int(np.ceil(total * SR)) + SR
    voice = np.zeros(n, dtype=np.float32)
    mask = np.zeros(n, dtype=bool)
    cues = []
    for s in ORDER:
        tl = json.load(open(os.path.join(BUILD, "timeline", f"{s}.json")))
        for key, t0 in tl["beats"]:
            w, sr = sf.read(os.path.join(BUILD, "audio", f"{key}.wav"), dtype="float32")
            w = resample_poly(w, SR, sr).astype(np.float32)
            i0 = int(round((offsets[s] + t0) * SR))
            voice[i0:i0 + len(w)] += w[:max(0, n - i0)]
            mask[i0:i0 + len(w)] = True
            # captions, timed by character share within the beat
            txt = caption(TEXT[key])
            parts = split_caption(txt)
            L = sum(len(p_) for p_ in parts)
            tt = offsets[s] + t0
            for p_ in parts:
                dd = durs[key] * len(p_) / L
                cues.append((tt, tt + dd - 0.05, wrap2(p_)))
                tt += dd
    mix = voice.copy()
    if not a.no_music:
        mix += ambient_score(n, mask)
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    wav = os.path.join(BUILD, "mix.wav")
    sf.write(wav, mix[:int(total * SR)], SR, subtype="PCM_24")
    srt = os.path.join(BUILD, "von_mises_stress.srt")
    with open(srt, "w") as f:
        for i, (t0, t1, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(t0)} --> {srt_time(t1)}\n{txt}\n\n")
    vid = os.path.join(BUILD, "video_only.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-i", srt,
                    "-map", "0:v", "-map", "1:a", "-map", "2:s",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000",
                    "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                    "-metadata", "title=The Physics of Failure - Understanding von Mises Stress",
                    "-movflags", "+faststart", a.out], check=True)
    print("wrote", a.out, f"({os.path.getsize(a.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
