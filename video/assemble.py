"""Assemble the final video: mux each rendered scene with its narration track,
concatenate, loudness-normalise, and embed subtitles.

Usage: python assemble.py [quality_dir=1080p30] [out=output/LCF_vs_HCF_fatigue.mp4]
"""
import os, sys, json, subprocess, textwrap, glob

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
AUD = os.path.join(HERE, "audio")
OUTDIR = os.path.join(HERE, "output")
SCENES = [("s01_intro", "S01Intro"), ("s02_basics", "S02Basics"), ("s03_regimes", "S03Regimes"),
          ("s04_hcf", "S04HCF"), ("s05_lcf", "S05LCF"), ("s06_fea", "S06FEA"), ("s07_aps", "S07APS"),
          ("s08_summary", "S08Summary")]


def run(cmd):
    print(" ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True)


def probe_dur(fn):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fn],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def srt_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def build_srt(timing, offsets, fn):
    """One cue per sentence-sized chunk, timed proportionally to its length."""
    cues = []
    for (sid, _), off in zip(SCENES, offsets):
        for gid, seg in timing[sid]["segments"].items():
            text = seg["text"]
            # split into balanced chunks of at most ~84 characters, preferring punctuation
            words = text.split()
            n = max(1, -(-len(text) // 84))
            target = len(text) / n
            chunks, cur = [], []
            for i, w in enumerate(words):
                cur.append(w)
                L = len(" ".join(cur))
                remaining = len(words) - i - 1
                if remaining and len(chunks) < n - 1 and (L >= target or (L >= 0.7 * target and w.endswith((".", ",", ":", "?", ";")))):
                    chunks.append(" ".join(cur)); cur = []
            if cur:
                chunks.append(" ".join(cur))
            total_chars = sum(len(c) for c in chunks)
            t = off + seg["start"]
            for c in chunks:
                d = seg["dur"] * len(c) / total_chars
                cues.append((t, t + d - 0.05, "\n".join(textwrap.wrap(c, 44))))
                t += d
    with open(fn, "w") as fh:
        for k, (a, b, txt) in enumerate(cues, 1):
            fh.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")
    return len(cues)


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "1080p30"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(OUTDIR, "LCF_vs_HCF_fatigue.mp4")
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = os.path.join(BUILD, "assemble")
    os.makedirs(tmp, exist_ok=True)
    timing = json.load(open(os.path.join(AUD, "timing.json")))
    parts, offsets, t0 = [], [], 0.0
    for sid, cls in SCENES:
        vids = glob.glob(os.path.join(BUILD, f"media_{cls}", "videos", sid, q, f"{cls}.mp4"))
        assert vids, f"missing render for {cls} ({q})"
        v = vids[0]
        a = os.path.join(AUD, f"{sid}.wav")
        T = timing[sid]["total"]
        vd = probe_dur(v)
        print(f"{sid}: video {vd:.2f}s, audio {T:.2f}s")
        o = os.path.join(tmp, f"{sid}.mkv")
        last = sid == SCENES[-1][0]
        if last:
            # let the closing card breathe, then fade picture and sound out
            T = max(T, vd) + 2.0
        vf = f"[0:v]tpad=stop_mode=clone:stop_duration=6,trim=duration={T:.3f},setpts=PTS-STARTPTS"
        af = f"[1:a]aresample=48000,apad,atrim=duration={T:.3f},asetpts=PTS-STARTPTS"
        if last:
            vf += f",fade=t=out:st={T-1.2:.3f}:d=1.2"
            af += f",afade=t=out:st={T-1.2:.3f}:d=1.2"
        fresh = os.path.exists(o) and os.path.getmtime(o) > max(os.path.getmtime(v), os.path.getmtime(a), os.path.getmtime(__file__))
        if not fresh:
            # pad video (clone last frame) / audio (silence) to the narration length
            run(["ffmpeg", "-loglevel", "error", "-y", "-i", v, "-i", a,
                 "-filter_complex", vf + "[v];" + af + "[a]",
                 "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                 "-r", "30", "-c:a", "pcm_s16le", o])
        parts.append(o)
        offsets.append(t0)
        t0 += T
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{p}'\n")
    joined = os.path.join(tmp, "joined.mkv")
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    srt = os.path.splitext(out)[0] + ".srt"
    n = build_srt(timing, offsets, srt)
    print(f"subtitles: {n} cues -> {srt}")
    # final encode: loudness-normalised AAC, H.264 tuned for animation, soft subtitles
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", joined, "-i", srt,
         "-map", "0:v", "-map", "0:a", "-map", "1:s",
         "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-tune", "animation", "-pix_fmt", "yuv420p",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
         "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
         "-metadata", "title=Low-Cycle vs High-Cycle Fatigue - life prediction, accumulated plastic strain and ratcheting",
         "-movflags", "+faststart", out])
    print("final:", out, f"{probe_dur(out):.1f}s", f"{os.path.getsize(out)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
