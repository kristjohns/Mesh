"""The videos built from this folder. Every tool takes --video <id> (default: fea)."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

PROJECTS = {
    "fea": dict(
        script="narration/script.json", timing="data/timing.json", build="build",
        out="fea_best_practice_subsea_wellhead", cuts="web/cuts.json",
        title="Meshing with Purpose - FEA best practice, subsea wellhead & template case study",
        ocean=("s01_intro", "s02_system", "s14_outro"), poster=35.5,
        chapters=[("", "Introduction"), ("", "The system we are modelling"),
                  ("", "Questions first: global and local models"), ("1", "Choosing the element type"),
                  ("", "Inside the solid family: locking and hourglassing"), ("", "Axisymmetric or 3D?"),
                  ("2", "Choosing the mesh size"), ("", "Welds and hot-spot stress"),
                  ("3", "Modelling the soil: p-y springs"), ("4", "Interfaces: conductor housing and template"),
                  ("", "Interfaces: conductor housing and HP housing"), ("", "Interfaces: conductor and soil"),
                  ("5", "Verification"), ("", "Takeaways")],
    ),
    "fatigue": dict(
        script="narration/fatigue_script.json", timing="data/fatigue_timing.json", build="build/fatigue",
        out="every_wave_counts_fatigue_dnv_rp_c203", cuts="web/fatigue_cuts.json",
        title="Every Wave Counts - fatigue design of a subsea wellhead with DNV-RP-C203",
        ocean=("f01_cold", "f04_hotspots", "f13_outro"), poster=40.2,
        maxrate="5M",  # keeps every web part under the artifact file limit
        chapters=[("", "Cold open"), ("", "Fatigue in a nutshell"), ("", "The C203 chain"),
                  ("", "Where will it crack?"), ("1", "Sea states and riser loads"),
                  ("2", "From force to moment"), ("", "From moment to nominal stress"), ("", "Hot-spot stress from the FE model"),
                  ("", "Misalignment at the girth weld"), ("3", "Rainflow counting"), ("4", "Choosing the S-N curve"),
                  ("", "Reading the S-N equation"), ("5", "Miner's rule and long-term damage"), ("", "The Weibull shortcut"),
                  ("6", "Design fatigue factor and results"), ("", "What moves the answer"), ("", "Buying back margin"), ("", "Recap")],
    ),
}


def project(argv=None):
    argv = sys.argv if argv is None else argv
    vid = argv[argv.index("--video") + 1] if "--video" in argv else "fea"
    P = dict(PROJECTS[vid])
    P["id"] = vid
    P["build_dir"] = os.path.join(ROOT, P["build"])
    P["timing_path"] = os.path.join(ROOT, P["timing"])
    P["script_path"] = os.path.join(ROOT, P["script"])
    P["cuts_path"] = os.path.join(ROOT, P["cuts"])
    P["out_path"] = os.path.join(os.path.dirname(ROOT), "output", P["out"] + ".mp4")
    return P
