"""Build the soundtrack: narration + procedural ambient music + synthesized SFX, and subtitles.

Usage: python3 audio.py [--video fatigue]  -> <build>/audio/mix.wav, <build>/subtitles.srt, <build>/edl.json
"""
import json
import os
import re
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt

ROOT = os.path.dirname(os.path.abspath(__file__))
import sys  # noqa: E402
sys.path.insert(0, ROOT)
from projects import project  # noqa: E402

P = project()
BUILD = P["build_dir"]
SR = 48000
XFADE = 0.6  # seconds of cross-fade between scene chunks
rng = np.random.default_rng(7)

timing = json.load(open(P["timing_path"]))
scenes = timing["scenes"]
offsets = []
t = 0.0
for sc in scenes:
    sc["duration"] = round(sc["duration"] * 30) / 30  # exactly what the renderer produces
    offsets.append(t)
    t += sc["duration"] - XFADE
TOTAL = t + XFADE
N = int(TOTAL * SR) + SR
print(f"total {TOTAL:.1f} s")


def db(x):
    return 10 ** (x / 20)


def lowpass(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x, axis=0)


def highpass(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x, axis=0)


def bandpass(x, f1, f2, order=2):
    sos = butter(order, [f1 / (SR / 2), f2 / (SR / 2)], btype="band", output="sos")
    return sosfilt(sos, x, axis=0)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# --------------------------------------------------------------------------- narration
voice = np.zeros(N)
for sc, off in zip(scenes, offsets):
    for ln in sc["lines"]:
        x, sr = sf.read(os.path.join(BUILD, "audio", "lines", ln["id"] + ".wav"))
        if x.ndim > 1:
            x = x.mean(axis=1)
        x = resample_poly(x, SR, sr)
        i0 = int((off + ln["start"]) * SR)
        voice[i0:i0 + len(x)] += x[: max(0, min(len(x), N - i0))]
voice = highpass(voice, 70)
# loudness normalisation of speech (RMS over active parts)
act = np.abs(voice) > 0.01
rms = np.sqrt(np.mean(voice[act] ** 2))
voice *= db(-19.0) / rms
# gentle compression of peaks
voice = np.tanh(voice * 1.4) / 1.4

# sidechain envelope for ducking
env = np.abs(voice)
k_att, k_rel = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.6 * SR))
# fast vectorised envelope follower on decimated signal
dec = 480
e = env[: len(env) // dec * dec].reshape(-1, dec).max(axis=1)
sm = np.zeros_like(e)
a_att, a_rel = np.exp(-1 / (0.05 * SR / dec)), np.exp(-1 / (0.7 * SR / dec))
for i in range(1, len(e)):
    a = a_att if e[i] > sm[i - 1] else a_rel
    sm[i] = a * sm[i - 1] + (1 - a) * e[i]
duck_env = np.interp(np.arange(N), np.arange(len(sm)) * dec, sm)
duck = 1.0 - 0.55 * np.clip(duck_env / 0.08, 0, 1)   # about -7 dB under speech

# --------------------------------------------------------------------------- music: pads
chords = [[38, 45, 53, 57, 64], [34, 41, 50, 57, 62], [36, 43, 52, 55, 62], [33, 40, 48, 55, 60]]
CH = 12.0  # seconds per chord


def pad_chord(notes, dur, bright):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros((n, 2))
    for j, m in enumerate(notes):
        f0 = midi(m)
        for det, pan in [(-5, 0.25), (0, 0.5), (6, 0.75)]:
            f = f0 * 2 ** (det / 1200)
            ph = rng.uniform(0, 2 * np.pi, 9)
            sig = np.zeros(n)
            for h in range(1, 9):
                if f * h > 6000:
                    break
                sig += np.sin(2 * np.pi * f * h * tt + ph[h]) / (h ** (1.6 - 0.5 * bright))
            vib = 1 + 0.002 * np.sin(2 * np.pi * (0.13 + 0.05 * j) * tt)
            sig *= vib
            out[:, 0] += sig * (1 - pan)
            out[:, 1] += sig * pan
    # slow swell
    a = np.minimum(1, tt / 3.5) * np.minimum(1, (dur - tt) / 3.5)
    out *= (a ** 1.5)[:, None]
    return out / np.max(np.abs(out))


loop_len = int(len(chords) * CH * SR)
step = int(CH * SR)
ov = int(3.5 * SR)


def build_loop(bright):
    loop = np.zeros((loop_len + ov, 2))
    for i, c in enumerate(chords):
        p = pad_chord(c, CH + 3.5, bright)
        s0 = i * step
        loop[s0:s0 + len(p)] += p[: len(loop) - s0]
    # wrap the tail into the start for seamless tiling
    loop[:ov] += loop[loop_len:loop_len + ov]
    return loop[:loop_len]


print("synthesising pads ...")
dark = lowpass(build_loop(0.0), 900)
bright = lowpass(build_loop(1.0), 2400)
reps = N // loop_len + 1
dark = np.tile(dark.astype(np.float32), (reps, 1))[:N]
bright = np.tile(bright.astype(np.float32), (reps, 1))[:N]
tt = (np.arange(N) / SR).astype(np.float64)
wb = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 95.0 - 1.2)
music = (dark * (1 - wb[:, None]) + bright * wb[:, None]).astype(np.float32)
del dark, bright
music *= db(-23)

# sub drone + bells
drone = np.sin(2 * np.pi * midi(26) * tt) * 0.6 + np.sin(2 * np.pi * midi(38) * tt + 0.5) * 0.25
drone *= (0.6 + 0.4 * np.sin(2 * np.pi * tt / 23.0))
music += np.c_[drone, drone] * db(-33)
bells = np.zeros((N, 2), dtype=np.float32)
pent = [74, 76, 79, 81, 86, 88]
tb = 4.0
while tb < TOTAL - 4:
    m = pent[rng.integers(len(pent))]
    f = midi(m)
    n = int(3.0 * SR)
    i0 = int(tb * SR)
    tl = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * tl) + 0.3 * np.sin(2 * np.pi * 2.01 * f * tl)) * np.exp(-tl * 1.6) * np.minimum(1, tl / 0.01)
    pan = rng.uniform(0.2, 0.8)
    seg_len = min(n, N - i0)
    bells[i0:i0 + seg_len, 0] += s[:seg_len] * (1 - pan)
    bells[i0:i0 + seg_len, 1] += s[:seg_len] * pan
    tb += rng.uniform(3.5, 7.5)
music += bells * db(-34)

# ocean bed on the underwater scenes
ocean = np.cumsum(rng.standard_normal((N, 2)).astype(np.float32), axis=0)
ocean = highpass(ocean, 20)
ocean = lowpass(ocean, 380)
ocean /= np.max(np.abs(ocean))
ocean *= (0.7 + 0.3 * np.sin(2 * np.pi * tt / 9.0))[:, None]
ow = np.zeros(N)
for sc, off in zip(scenes, offsets):
    if sc["id"] in P["ocean"]:
        a, b = off, off + sc["duration"]
        ow += np.clip((tt - a) / 2.0, 0, 1) * np.clip((b - tt) / 2.0, 0, 1)
music += (ocean * ow[:, None] * db(-27)).astype(np.float32)
del ocean

# --------------------------------------------------------------------------- SFX
def noise(n):
    return rng.standard_normal(n)


def sfx_whoosh(d=1.1):
    n = int(d * SR)
    x = noise(n)
    tl = np.arange(n) / SR
    out = np.zeros(n)
    # swept band-pass approximated by summing a few fixed bands with moving gains
    for k, fc in enumerate([300, 600, 1200, 2400, 4800]):
        b = bandpass(x, fc * 0.7, fc * 1.4)
        centre = (k + 0.5) / 5
        g = np.exp(-((tl / d - centre) ** 2) / 0.03)
        out += b * g
    out *= np.sin(np.pi * tl / d) ** 2
    return out / np.max(np.abs(out))


def sfx_thud():
    n = int(0.9 * SR)
    tl = np.arange(n) / SR
    f = 70 * np.exp(-tl * 3) + 38
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl * 6)
    s += lowpass(noise(n), 900) * np.exp(-tl * 40) * 0.6
    return s / np.max(np.abs(s))


def sfx_click():
    n = int(0.35 * SR)
    tl = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 2300 * tl) * 0.6 + np.sin(2 * np.pi * 3700 * tl) * 0.4) * np.exp(-tl * 40)
    s += bandpass(noise(n), 2000, 6000) * np.exp(-tl * 90) * 0.5
    s2 = np.zeros(n)
    s2[int(0.07 * SR):] = s[: n - int(0.07 * SR)] * 0.7
    return (s + s2) / np.max(np.abs(s + s2))


def sfx_scan(d=3.0):
    n = int(d * SR)
    tl = np.arange(n) / SR
    f = 300 + 900 * (tl / d) ** 1.5
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * 0.2
    s += bandpass(noise(n), 2000, 7000) * 0.25
    s *= np.sin(np.pi * tl / d) ** 2
    return s / np.max(np.abs(s))


def sfx_hit():
    n = int(4.0 * SR)
    tl = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(55 * np.exp(-tl * 0.8) + 30) / SR) * np.exp(-tl * 1.2)
    s += lowpass(noise(n), 400) * np.exp(-tl * 8) * 0.5
    sh = np.zeros(n)
    for m in [74, 79, 81, 86]:
        sh += np.sin(2 * np.pi * midi(m) * tl) * np.exp(-tl * 0.9) * 0.15
    s += sh
    return s / np.max(np.abs(s))


def sfx_chapter():
    n = int(3.0 * SR)
    tl = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(48 * np.exp(-tl * 1.5) + 34) / SR) * np.exp(-tl * 2.2) * 0.8
    for m in [69, 76, 81]:
        s += np.sin(2 * np.pi * midi(m) * tl) * np.exp(-tl * 1.4) * 0.12 * np.minimum(1, tl / 0.02)
    s += sfx_whoosh(1.2).__array__()[:n] * 0.0 if False else 0
    return s / np.max(np.abs(s))


def sfx_drone():
    n = int(9.0 * SR)
    tl = np.arange(n) / SR
    s = np.sin(2 * np.pi * midi(26) * tl) * 0.7 + lowpass(noise(n), 200) * 0.8
    s *= np.minimum(1, tl / 6.0) * np.minimum(1, (9 - tl) / 2.5)
    return s / np.max(np.abs(s))


def sfx_outro():
    n = int(6.0 * SR)
    tl = np.arange(n) / SR
    s = np.zeros(n)
    for m in [50, 57, 62, 65, 69]:
        s += np.sin(2 * np.pi * midi(m) * tl) / 5
    s *= np.minimum(1, tl / 2.5) * np.exp(-np.maximum(0, tl - 3) * 0.9)
    return s / np.max(np.abs(s))


SFX = {"whoosh": (sfx_whoosh, -25), "thud": (sfx_thud, -21), "click": (sfx_click, -26), "scan": (sfx_scan, -27),
       "hit": (sfx_hit, -17), "chapter": (sfx_chapter, -20), "drone": (sfx_drone, -22), "outro": (sfx_outro, -24)}
fx = np.zeros((N, 2), dtype=np.float32)
for sc, off in zip(scenes, offsets):
    mp = os.path.join(BUILD, "meta", sc["id"] + ".json")
    if not os.path.exists(mp):
        continue
    meta = json.load(open(mp))
    for ev in meta.get("sfx", []):
        fn, gain = SFX[ev["type"]]
        s = fn() * db(gain)
        i0 = int((off + ev["t"]) * SR)
        if i0 >= N:
            continue
        L = min(len(s), N - i0)
        pan = 0.5
        fx[i0:i0 + L, 0] += s[:L] * (1 - pan) * 1.4
        fx[i0:i0 + L, 1] += s[:L] * pan * 1.4

# --------------------------------------------------------------------------- reverb on music + fx
print("reverb ...")
ir_len = int(2.8 * SR)
tl = np.arange(ir_len) / SR
ir = np.c_[noise(ir_len), noise(ir_len)] * np.exp(-tl * 2.4)[:, None]
ir = lowpass(ir, 5000)
ir /= np.sqrt(np.sum(ir ** 2, axis=0))
wet_in = (music * duck[:, None] + fx).astype(np.float32)
del music, fx
wet = np.c_[fftconvolve(wet_in[:, 0], ir[:, 0])[:N], fftconvolve(wet_in[:, 1], ir[:, 1])[:N]]
bed = (wet_in * 0.75 + wet * 0.45).astype(np.float32)
del wet, wet_in

# fades
fade = np.clip(tt / 2.5, 0, 1) * np.clip((TOTAL - tt) / 4.0, 0, 1)
mix = bed * fade[:, None] + np.c_[voice, voice] * 0.98
peak = np.max(np.abs(mix))
mix = np.tanh(mix * (0.95 / max(peak, 1e-6)) * 1.2) / np.tanh(1.2)
mix *= db(-1.0)
os.makedirs(os.path.join(BUILD, "audio"), exist_ok=True)
sf.write(os.path.join(BUILD, "audio", "mix.wav"), mix[: int(TOTAL * SR)].astype(np.float32), SR, subtype="PCM_16")
print("wrote mix.wav", mix.shape)

# --------------------------------------------------------------------------- subtitles
DISPLAY = [("D N V, R P, C two-oh-three", "DNV-RP-C203"), ("P Y curve", "p-y curve"), ("P Y springs", "p-y springs"),
           ("T Z curves", "t-z curves"), ("T Z springs", "t-z springs"), ("Q Z curve", "Q-z curve"), ("Q Z spring", "Q-z spring"),
           ("S N curves", "S-N curves"), ("pre-load", "preload"), ("thirty-six inch", "36-inch"), ("twenty inch", "20-inch"),
           ("seven point three meganewtons", "7.3 MN"), ("one point four meganewton metres", "1.4 MNm"), ("three meganewton metres", "3 MNm"),
           # fatigue video
           ("C two-oh-three", "C203"), ("S N ", "S-N "), ("delta sigma", "Δσ"), ("a bar,", "ā,"), ("B one", "B1"), ("W three", "W3"),
           ("point one t", "0.1t"), ("high-low", "hi-lo"), ("Three hundred and fifty metres", "350 metres"),
           ("ten thousand load cycles", "10,000 load cycles"), ("ninety-seven point seven percent", "97.7%"),
           ("three metres below", "3 metres below"), ("three metres under", "3 metres under"), ("below two metres", "below 2 metres"),
           ("above six metres", "above 6 metres"), ("less than two percent", "less than 2%"), ("fifty kilonewtons", "50 kN"),
           ("one point six", "1.6"), ("one point one five", "1.15"), ("six millimetres", "6 mm"), ("one point one seven", "1.17"),
           ("fourteen hundred cycles", "1,400 cycles"), ("three-hour", "3-hour"), ("ten million cycles", "10 million cycles"),
           ("one million cycles", "1 million cycles"), ("slope of five", "slope of 5"), ("twenty-five millimetres", "25 mm"),
           ("thirty-eight millimetre", "38 mm"), ("nine percent", "9%"), ("less than one percent", "less than 1%"),
           ("between three and six metres", "between 3 and 6 metres"), ("within ten percent", "within 10%"),
           ("from one to ten", "from 1 to 10"), ("we use ten", "we use 10"), ("three hundred and thirty days", "330 days"),
           ("sixteen hundred and sixty days", "1,660 days"), ("a hundred and sixty-six days", "166 days"),
           ("a hundred and twenty days", "120 days"), ("seventy percent", "70%"), ("ten percent more", "10% more"),
           ("ten millimetres", "10 mm"), ("instead of six", "instead of 6"), ("sixty-eight days", "68 days"),
           ("m is three", "m is 3"), ("factor of eight", "factor of 8"), ("Step one", "Step 1"), ("Step two", "Step 2"),
           ("Step three", "Step 3"), ("Step four", "Step 4"), ("Step five", "Step 5"), ("Step six", "Step 6")]


def disp(s):
    for a, b in DISPLAY:
        s = s.replace(a, b)
    return s


def fmt(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


cues = []
for sc, off in zip(scenes, offsets):
    for ln in sc["lines"]:
        text = disp(ln["text"])
        parts = re.split(r"(?<=[.?!:])\s+", text)
        chunks = []
        for p in parts:
            while len(p) > 84:
                cut = p.rfind(", ", 0, 84)
                if cut < 30:
                    cut = p.rfind(" ", 0, 84)
                chunks.append(p[: cut + 1].strip())
                p = p[cut + 1:].strip()
            if p:
                chunks.append(p)
        total_chars = sum(len(c) for c in chunks)
        t0 = off + ln["start"]
        for c in chunks:
            d = ln["dur"] * len(c) / total_chars
            cues.append((t0, t0 + d, c))
            t0 += d
with open(os.path.join(BUILD, "subtitles.srt"), "w") as fh:
    for i, (a, b, c) in enumerate(cues, 1):
        if len(c) > 42:
            mid = c.rfind(" ", 0, len(c) // 2 + 8)
            c = c[:mid] + "\n" + c[mid + 1:]
        fh.write(f"{i}\n{fmt(a)} --> {fmt(b - 0.02)}\n{c}\n\n")
json.dump(dict(xfade=XFADE, offsets=offsets, durations=[s["duration"] for s in scenes], ids=[s["id"] for s in scenes], total=TOTAL),
          open(os.path.join(BUILD, "edl.json"), "w"), indent=1)
print("subtitles:", len(cues))
