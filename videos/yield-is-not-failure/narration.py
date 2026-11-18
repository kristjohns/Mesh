"""Narration for "Yield Is Not Failure" - every number comes from the analyses in fe/cases.py."""

SCENES = [
    ("Y00_Open", [
        ("n1", "In the last film, our subsea transition piece reached its highest stress at the fillet root. "
               "Now increase the load by seventy percent. The linear elastic answer at the fillet is 558 "
               "megapascals, far above the yield strength of 355."),
        ("n2", "But that number is fiction. Steel cannot carry stress far beyond yield; it deforms "
               "plastically, and the extra load flows into the material around it. The elastic-plastic "
               "analysis shows a plastic zone a few millimetres across, and a peak plastic strain of 0.18 "
               "percent."),
        ("n3", "So the steel has yielded. Has anything failed? Answering that takes a different analysis, "
               "and different criteria. Here are five finite element cases that show how engineers decide."),
    ]),
    ("Y01_Why", [
        ("w1", "Start with the material. Structural steel yields at a strain of about 0.17 percent, but it "
               "can stretch fifteen percent or more before it necks, and further still before it fractures. "
               "Yield is the start of the plastic range, not the end of the material."),
        ("w2", "And plasticity redistributes stress. In a beam, the outer fibres yield first. They stop "
               "taking extra stress, so further moment is carried by the fibres further in. The stress "
               "profile flattens from a triangle towards a rectangle, and the beam keeps carrying load."),
        ("w3", "Once yield is allowed, the failure modes that matter are different. Plastic collapse: "
               "unbounded deformation at constant load. Local failure: ductile fracture where strain and "
               "triaxiality are high. Ratcheting: strain that grows every cycle. Fatigue. And buckling. "
               "Yield itself is not on the list."),
        ("w4", "Each needs its own analysis and its own acceptance criterion. Design-by-analysis rules define "
               "them: ASME Section Eight Division Two and EN 13445 for pressure equipment, and DNV-RP-C208 "
               "for offshore structures."),
    ]),
    ("Y02_Method", [
        ("k1", "The tool is elastic-plastic finite element analysis. At every Gauss point, the solver "
               "predicts an elastic trial stress. If it lies outside the von Mises yield surface, it is "
               "returned radially onto the surface, and plastic strain grows along the normal."),
        ("k2", "The load is applied in increments, each solved by Newton-Raphson iteration with the "
               "consistent tangent. When the structure can no longer carry more load, the iterations stop "
               "converging: the numerical signature of plastic collapse."),
        ("k3", "Two material models are used: elastic, perfectly plastic for limit-load analysis, and the "
               "true stress-strain curve, with its yield plateau and strain hardening."),
        ("k4", "The solver used here was written for this film and checked against Hill's exact solution for "
               "a thick cylinder under pressure. First yield: 224 megapascals, against 224. Collapse: 413, "
               "against 414."),
        ("k5", "These methods move the safety margin from the stress to the load. Instead of asking whether "
               "a stress is below an allowable, they multiply the design loads by a factor and ask whether "
               "the structure still stands: 1.5 for a limit-load analysis, 2.4 for a full elastic-plastic "
               "analysis, and 1.7 for local strain."),
    ]),
    ("Y03_Plate", [
        ("p1", "Case one: a 20-millimetre S three fifty-five plate, 200 millimetres wide, with a 60-millimetre "
               "hole, in tension. The stress concentration factor on the net section is 2.36, so the edge "
               "of the hole yields at about 420 kilonewtons."),
        ("p2", "Keep loading. Plasticity spreads from the hole in inclined bands, and the load keeps rising. "
               "Only when the bands reach the edges of the plate does the curve level off: the limit load, "
               "996 kilonewtons, matching yield strength times net area."),
        ("p3", "First yield occurred at 42 percent of the collapse load. The criterion is a limit-load "
               "analysis. ASME uses an elastic, perfectly plastic model with a yield stress of 1.5 times "
               "the allowable stress, and requires a converged solution at 1.5 times the design loads."),
        ("p4", "Here, that permits a design load of about 550 kilonewtons, where the elastic peak at the hole "
               "is 460 megapascals: well above yield, and acceptable against plastic collapse. It is the same "
               "answer as the classical rule that the average stress on the net section must not exceed the "
               "allowable. The peak at the hole never enters."),
    ]),
    ("Y04_Beam", [
        ("b1", "Case two: the constant-moment region of a steel beam, 100 by 50 millimetres, bent by a "
               "controlled end rotation. The outer fibres yield at 29.6 kilonewton metres. Plasticity then "
               "spreads inward from both faces, around a shrinking elastic core."),
        ("b2", "The moment approaches the fully plastic moment, 44.4 kilonewton metres: one and a half times "
               "first yield, the shape factor of a rectangle. The finite element curve follows the "
               "closed-form solution to within a fraction of a percent."),
        ("b3", "With the real stress-strain curve, hardening means the curve never quite flattens. So where "
               "is collapse? The twice-elastic-slope method: draw a line from the origin with half the "
               "elastic stiffness. It cuts the curve at 43.0 kilonewton metres, the collapse moment, and the "
               "allowable is two-thirds of that."),
        ("b4", "That two-thirds is no accident. For a rectangle, two-thirds of the plastic moment is first "
               "yield. It is also why elastic stress rules allow membrane plus bending stress up to 1.5 times "
               "the allowable: the shape factor of a rectangle. Redistribution is already built into the "
               "elastic rules."),
    ]),
    ("Y05_Cylinder", [
        ("c1", "Case three: a high-pressure subsea body, modelled as a thick cylinder with a 100-millimetre "
               "bore and a 200-millimetre outside diameter, in a 75 k s i forging, rated for 20,000 p s i. "
               "At that pressure it is elastic: the bore reaches 319 megapascals."),
        ("c2", "The elastic-plastic design check asks a harder question: does it still carry 2.4 times the "
               "design pressure? At 48,000 p s i, the elastic answer at the bore would be 766 megapascals. "
               "The elastic-plastic analysis shows the inner 31 percent of the wall yielded, the plastic "
               "front exactly where Hill's solution puts it, and a converged solution. It passes."),
        ("c3", "Collapse only comes at 413 megapascals, three times the rating. And when the pressure is "
               "released, the elastic outer wall squeezes the yielded bore, leaving a residual hoop stress "
               "of minus 284 megapascals, the principle behind auto-frettage."),
        ("c4", "Because the overpressure stayed below twice the first-yield pressure, unloading is elastic, "
               "and later pressure cycles stay elastic too. API 17 T R 8, for high-pressure subsea equipment, "
               "builds on these same elastic-plastic methods."),
    ]),
    ("Y06_Fillet", [
        ("f1", "Case four returns to our transition piece, under an axial stress of 150 megapascals in the "
               "pipe wall. The fillet's stress concentration factor is 2.19, so the elastic peak is 329 "
               "megapascals, just below yield. Yield begins at 1.08 times the design load."),
        ("f2", "Protection against local failure is checked by an elastic-plastic analysis at 1.7 times the "
               "design loads, with the true stress-strain curve. The plastic zone stays at the fillet root, "
               "and the peak equivalent plastic strain is 0.18 percent."),
        ("f3", "The limit is a strain, adjusted for triaxiality, because ductility falls as hydrostatic "
               "tension rises. For S three fifty-five, the uniaxial strain limit is about 40 percent. At the "
               "fillet's triaxiality of 0.56, it falls to 26 percent. The demand, plus any strain from forming, "
               "must stay below it. Here it is 0.18 percent: under one percent of the capacity."),
        ("f4", "Neuber's rule, the classic hand estimate, gives 0.24 percent: conservative, as expected. At a "
               "smooth notch in ductile steel, local yield is rarely the problem. Fatigue at that notch can "
               "be."),
    ]),
    ("Y07_Bree", [
        ("r1", "Case five adds time: a thin cylinder under constant pressure, with a temperature difference "
               "through the wall that cycles on and off. This is the classic Bree problem. The first heat-up "
               "yields both surfaces. What happens next decides everything."),
        ("r1b", "Bree mapped the outcomes on one diagram: the pressure stress on one axis, the thermal stress "
                "on the other, both divided by yield. Below the line where they sum to one, every cycle is "
                "elastic. Our three analyses sit in three different regions."),
        ("r2", "At moderate pressure and thermal load, the first cycle leaves residual stresses that keep "
               "every later cycle elastic. The plastic strain stops at 0.14 percent, and the diameter stays "
               "fixed. The cylinder has shaken down."),
        ("r3", "With a lower pressure but a larger thermal range, the surfaces yield in tension and compression "
               "every cycle, but "
               "the diameter stops changing. That is alternating plasticity: no ratcheting, but a plastic "
               "strain range that must be assessed for low-cycle fatigue."),
        ("r4", "Raise the pressure, and the strain steps forward every cycle, without limit. That is "
               "ratcheting, and it does end in failure. The criterion is a cyclic elastic-plastic analysis: "
               "after a few cycles, there must be shakedown, an elastic core, or no progressive change in "
               "dimensions."),
    ]),
    ("Y08_Criteria", [
        ("s1", "So here are the criteria. Against plastic collapse: a converged limit-load analysis at 1.5 "
               "times the loads, or an elastic-plastic analysis at 2.4 times, or a collapse load from the "
               "twice-elastic-slope method. EN 13445 adds a five percent limit on principal structural "
               "strain."),
        ("s2", "Against local failure: plastic strain below the triaxial strain limit, at 1.7 times the "
               "loads. Against ratcheting: shakedown, or an elastic core, under the cyclic loads. Fatigue, "
               "buckling and fracture keep their own checks, and serviceability, such as a flange that must "
               "stay tight, can limit deformation further."),
        ("s3", "Notice what is not on the list: the peak von Mises stress from a linear elastic analysis. "
               "Yielding is allowed. Collapse, rupture, ratcheting and fatigue are not."),
        ("s4", "When the elastic contour turns red, the analysis is not over. Ask which failure mode you are "
               "protecting against, and run the analysis that can see it."),
    ]),
]

TTS_SUBS = [
    ("von Mises", "von Meezus"),
    ("ASME", "Azmee"),
    ("Neuber", "Noyber"),
    ("fillet", "fillit"),
    ("EN 13445", "E N one three four four five"),
    ("DNV-RP-C208", "D N V, R P, C two oh eight"),
    ("Newton-Raphson", "Newton Raphson"),
    ("auto-frettage", "auto fret-ahzh"),
]

CAPTION_SUBS = [
    ("S three fifty-five", "S355"),
    ("k s i", "ksi"),
    ("p s i", "psi"),
    ("API 17 T R 8", "API 17TR8"),
    ("auto-frettage", "autofrettage"),
]
