"""
Narration script for the video "Low-Cycle vs High-Cycle Fatigue".

Each scene is a list of (segment_id, text). The text is used for the subtitles;
PRONUNCIATION maps words to spellings that the TTS engine pronounces correctly.
"""

PRONUNCIATION = {
    "Wöhler": "Vohler",
    "Neuber's": "Noyber's",
    "Neuber": "Noyber",
    "Masing": "Mahzing",
    "Chaboche": "Shaboshe",
    "von Mises": "fon Meezes",
    "Gerber": "Gairber",
    "Fatemi–Socie": "Fatehmee Sosee",
    "Melan's": "Melahn's",
    "ASME": "A S M E",
    "EN 13445": "E N thirteen four four five",
    "S355": "S three fifty-five",
    "FAT 80": "fat eighty",
    "FAT 225": "fat two twenty-five",
    "DNV-RP-C203": "D N V, R P, C two oh three",
    "PEEQ": "peek",
    "CalculiX": "Kalkyulix",
    "Abaqus": "Abbacus",
    "S–N": "S N",
    "strain–life": "strain life",
    "stress–strain": "stress strain",
    "log–log": "log log",
    "Coffin–Manson–Basquin": "Coffin Manson Basquin",
    "Coffin–Manson": "Coffin Manson",
    "Ramberg–Osgood": "Ramberg Osgood",
    "Palmgren–Miner": "Palmgren Miner",
    "Brown–Miller": "Brown Miller",
    "Smith–Watson–Topper": "Smith Watson Topper",
    "Armstrong–Frederick": "Armstrong Frederick",
    "K t": "K tee",
    "K f": "K eff",
    "K e": "K ee",
    "R equals": "R equals",
    "μm": "micrometres",
}

SCENES = [
    ("s01_intro", [
        ("a", "Every structure that vibrates, rotates, heats up or cools down is quietly counting load cycles."),
        ("b", "Fatigue, failure under repeated loads well below the static strength, is behind a large share of the mechanical and structural failures seen in service."),
        ("c", "And fatigue has two very different faces. In high-cycle fatigue the material stays elastic and survives millions of cycles. In low-cycle fatigue it yields on every cycle, and may fail after only hundreds or thousands."),
        ("d", "In this video we look at what separates the two, the methods used to predict fatigue life in each regime, and a question that confuses many analysts: what does accumulated plastic strain in a finite element model really tell you, and when is it a problem?"),
        ("e", "Everything is backed by nonlinear finite element simulations, run with a cyclic plasticity solver written for this study and checked against an independent code."),
    ]),
    ("s02_basics", [
        ("a", "Fatigue damage starts at the scale of the grains. Under cyclic shear, dislocations organise into persistent slip bands. Where these bands meet the free surface they push out tiny extrusions and intrusions, which act as micro-notches."),
        ("b", "A crack then grows a few grains deep along the slip planes. That is stage one. It then turns perpendicular to the largest principal stress and advances a little every cycle. That is stage two, and it leaves striations and, on a larger scale, beach marks on the fracture surface."),
        ("c", "Finally the remaining ligament can no longer carry the peak load, and it breaks in a single fast fracture."),
        ("d", "So fatigue life is crack initiation plus crack growth. Smooth parts in high-cycle fatigue spend most of their life initiating a crack. At sharp notches, at welds, and in low-cycle fatigue, crack growth takes a much larger share."),
        ("e", "To describe a load cycle we use the maximum and minimum stress, the stress range delta sigma, the amplitude sigma a, which is half the range, the mean stress sigma m, and the stress ratio R, the minimum over the maximum. R equals minus one is fully reversed loading. R equals zero is pulsating tension."),
    ]),
    ("s03_regimes", [
        ("a", "So what really separates low-cycle from high-cycle fatigue? It is not a magic number of cycles. It is plasticity."),
        ("b", "Plot stress against strain over one cycle. At a small amplitude the response is a straight line: elastic, with no energy dissipated. Push the amplitude past the cyclic yield point and the line opens into a hysteresis loop. Its width is the plastic strain range, and its area is the plastic work dissipated, every single cycle."),
        ("c", "When the plastic strain is large compared with the elastic strain, we are in low-cycle fatigue, with lives up to roughly ten thousand to a hundred thousand cycles, and strain is the variable that controls damage. When plastic strain is negligible, we are in high-cycle fatigue, and stress is the natural variable."),
        ("d", "You can see this on the strain–life curve. On log–log axes the elastic strain amplitude falls along a shallow straight line, Basquin's law, and the plastic strain amplitude along a steep one, the Coffin–Manson law. Their sum is the total strain–life curve."),
        ("e", "Where the two lines cross is the transition life. To its left, plasticity dominates and life is governed by ductility. To its right, elastic strain dominates and life is governed by strength. For the S355-type steel used in this video the transition is at about three thousand three hundred cycles. High-strength steels reach it much earlier."),
        ("f", "Beyond about ten million cycles lies the very-high-cycle regime, where cracks often start below the surface at inclusions, leaving a characteristic fish-eye. That is why many modern standards no longer assume a true endurance limit."),
        ("g", "And remember: in a real component, the bulk can stay elastic while a notch root yields. The surrounding elastic material then imposes a strain cycle on the notch. That is why local strain methods work so well, and why finite element analysis sits at the centre of both regimes."),
    ]),
    ("s04_hcf", [
        ("a", "High-cycle fatigue first: the world of stress and life."),
        ("b", "Since Wöhler's railway axle experiments in the eighteen-sixties, the basic tool has been the S–N curve: stress amplitude against cycles to failure on logarithmic axes. In the finite-life region, Basquin's equation makes it a straight line: the stress amplitude equals the fatigue strength coefficient times two N to the power b, a small negative exponent."),
        ("c", "Many steels show a knee and a fatigue limit, for smooth polished specimens typically around half the tensile strength, reached between one and ten million cycles. Aluminium alloys show no clear limit at all. Test data from small polished specimens is then reduced for surface finish, size, load type, temperature and the reliability you need."),
        ("d", "Next, mean stress. Tension opens cracks and shortens life, compression helps. The Haigh diagram plots the allowable amplitude against the mean stress. Goodman's line joins the fatigue limit to the ultimate strength, Gerber uses a parabola, and Soderberg's line ends at the yield strength and is the most conservative. Smith, Watson and Topper combine maximum stress and amplitude into one damage parameter."),
        ("e", "Then notches. The elastic stress concentration factor, K t, multiplies the nominal stress at the notch root. Our plate with a central hole gives K t equal to three point two five on the gross section, or two point four four on the net section, matching the classical Peterson value to within a fraction of a percent."),
        ("f", "The fatigue strength is reduced by less than K t suggests, because a steep stress gradient affects only a tiny volume of material. The fatigue notch factor, K f, and Peterson's notch sensitivity capture this. For a twenty millimetre hole in steel the notch sensitivity is close to one, so K f is practically K t."),
        ("g", "Welded joints need their own toolbox. The weld toe is a sharp notch with tensile residual stresses close to yield, which is also why weld S–N curves largely ignore the applied mean stress."),
        ("h", "With the nominal stress method you find your detail in a catalogue of detail categories, such as FAT 80, and use a simple beam-theory stress. It only works if your joint and loading match a catalogued detail."),
        ("i", "The structural hot-spot method uses a finite element model. Here is a fillet-welded attachment in bending. The surface stress rises toward the weld toe: a linear structural part plus a sharp, nonlinear notch peak. We read the surface stress at half a plate thickness and at one and a half thicknesses from the toe, and extrapolate linearly to the toe, as DNV-RP-C203 recommends. The result, ninety-nine megapascals, is the hot-spot stress, used with a hot-spot S–N curve such as DNV curve D."),
        ("j", "The effective notch stress method goes one step further. The toe is rounded with a fictitious one millimetre radius, the peak stress is computed directly, here two hundred and seventy-one megapascals, and compared with the FAT 225 curve."),
        ("k", "For this joint the routes agree: about one point one to one point five million cycles for a hundred megapascal nominal stress range. But each method has its own rules for meshing and read-out, and they must be followed exactly."),
        ("l", "Real loads are rarely constant. Rainflow counting breaks an irregular history into closed cycles, each with its own range and mean. Each cycle uses up a fraction n over N of the life at that range, and the Palmgren–Miner rule adds the fractions. Failure is predicted when the sum reaches one, and design codes add margin with design fatigue factors."),
        ("m", "Miner's rule ignores load-sequence effects, and multiaxial stresses need more: invariant criteria such as Sines and Crossland, the mesoscopic Dang Van criterion, or critical-plane criteria such as Findley."),
    ]),
    ("s05_lcf", [
        ("a", "Now low-cycle fatigue, where strain takes over."),
        ("b", "Under strain-controlled cycling, metals evolve. Soft, annealed materials harden cyclically, while cold-worked and high-strength materials tend to soften. After a while the loops stabilise, and the tips of the stable loops define the cyclic stress–strain curve, usually written in Ramberg–Osgood form with a cyclic strength coefficient, K prime, and a hardening exponent, n prime."),
        ("c", "Many steels show Masing behaviour: each hysteresis branch is the cyclic curve scaled by a factor of two, so any loop can be built from one curve."),
        ("d", "Life follows the Coffin–Manson–Basquin relation. The total strain amplitude is the elastic part, sigma f prime over E times two N to the b, plus the plastic part, epsilon f prime times two N to the c."),
        ("e", "Mean stress enters through Morrow's correction, which subtracts the mean stress from the fatigue strength coefficient, or through the Smith–Watson–Topper parameter: the maximum stress times the strain amplitude."),
        ("f", "How do we find the strain at a notch root? Neuber's rule says the local stress times the local strain equals the elastic value, K t times the nominal stress, squared, divided by E. That is a hyperbola, which we intersect with the cyclic curve. Glinka's rule equates strain energy densities instead. Neuber tends to overestimate the strain, Glinka to underestimate it."),
        ("g", "Or we run an elastic-plastic finite element analysis with a cyclic material model. In our notched plate at plus or minus one hundred and eighty megapascals, the computed strain amplitude at the hole is zero point three eight percent, neatly between Glinka at zero point three two and Neuber at zero point four three. The strain–life curve then gives about four thousand cycles."),
        ("h", "Other approaches use the hysteresis energy per cycle, or critical-plane strain parameters such as Brown–Miller and Fatemi–Socie for multiaxial and non-proportional loading."),
        ("i", "Design codes package this. ASME Section eight, Division two, offers an elastic route, where the stress range is amplified by a plasticity correction factor, K e, once it exceeds the shakedown limit, and an elastic-plastic route, where an effective strain range, the elastic stress range over E plus the equivalent plastic strain range from a cyclic analysis, enters the fatigue curve. DNV-RP-C203 likewise corrects elastic hot-spot stresses for plasticity in low-cycle fatigue, and adds the low-cycle damage to the high-cycle damage."),
    ]),
    ("s06_fea", [
        ("a", "Let's put this into a finite element model: a steel plate eighty millimetres wide with a twenty millimetre hole, modelled as a quarter with symmetry, in plane stress, with nine-node quadratic elements graded toward the hole."),
        ("b", "The material is an S355-type steel with a cyclic proportional limit of two hundred and fifty megapascals and three Chaboche nonlinear kinematic back-stresses, calibrated to the stabilised cyclic stress–strain curve. The solver uses implicit return mapping with a consistent tangent, and on the same cyclic problem it matches CalculiX to within about two percent."),
        ("c", "Four load cases tell the whole story."),
        ("d", "Case one: plus or minus seventy megapascals. The peak stress at the hole is two hundred and twenty-seven megapascals, below the proportional limit, so everything is elastic. The loop is a line, the accumulated plastic strain is zero, and the strain–life curve gives about five million cycles. This is high-cycle fatigue."),
        ("e", "Case two: zero to one hundred and forty megapascals. Elastically the hole would see four hundred and fifty-five megapascals, so the first loading yields the notch. On unloading, the elastic surroundings push the yielded material into compression and leave a residual stress. From the second cycle on, the response is purely elastic. This is elastic shakedown: the accumulated plastic strain jumps once, then stays flat."),
        ("f", "But look at the local mean stress: plus one hundred and fifteen megapascals. With a mean stress correction, the predicted life drops from five point six million to between six hundred thousand and one point six million cycles. Shakedown removes plastic cycling, not fatigue."),
        ("g", "Case three: plus or minus one hundred and eighty megapascals. Now the elastic stress range at the hole, nearly twelve hundred megapascals, is far above twice the yield strength, so yielding reverses every half cycle. The notch root settles into a closed, fat hysteresis loop. This is alternating plasticity, also called plastic shakedown, and it is the home of low-cycle fatigue. Life: about four thousand cycles."),
        ("h", "Case four: zero to two hundred and eighty-five megapascals. Now the net section yields, and the load keeps a high mean value. The loop no longer closes; it walks to the right, and the plate gets a little longer every cycle. This is ratcheting."),
        ("i", "Now compare the accumulated plastic strain at the notch root. Zero for the elastic case. A single step for shakedown. A steadily rising line for alternating plasticity, and a rising line for ratcheting too."),
        ("j", "And that is the catch. Cases three and four look alike in accumulated plastic strain, but they are completely different problems. One is a closed strain cycle that slowly initiates a fatigue crack. The other is a net strain that keeps growing until ductility is exhausted or the part deforms unacceptably."),
    ]),
    ("s07_aps", [
        ("a", "So what is accumulated plastic strain? In most finite element codes it is the equivalent plastic strain, PEEQ in Abaqus: the time integral of the square root of two thirds of the plastic strain rate contracted with itself."),
        ("b", "Because it integrates the magnitude of plastic flow, it can only increase. Every reversal adds to it, in whatever direction. Under uniaxial alternating plasticity it grows by twice the plastic strain range every cycle. At our notch root that is zero point eight two percent per cycle, while the strain itself just oscillates between plus and minus zero point three eight percent."),
        ("c", "So a large PEEQ alone does not tell you whether you have a fatigue problem, a ratcheting problem, or neither. You have to look at how the plastic strain tensor changes over a complete cycle."),
        ("d", "Under repeated loading, a structure settles into one of four responses. Elastic, with no yielding at all. Elastic shakedown, with yielding only in the first cycles. Alternating plasticity, a closed plastic cycle that repeats. And ratcheting, also called incremental collapse, with a net plastic strain increment in every cycle."),
        ("e", "Melan's theorem gives the condition for elastic shakedown: if some constant, self-equilibrating residual stress field exists that keeps the elastic stresses plus the residual stresses within yield at all times, the structure will shake down. For a perfectly plastic material that means the elastic stress range cannot exceed twice the yield strength, which is the basis of the ASME limit on the primary-plus-secondary stress range."),
        ("f", "Ratcheting needs two ingredients: a sustained primary load, like pressure, and a cyclic secondary stress, like a thermal gradient. The classic case is the Bree problem: a pressurised thin cylinder with a cycling temperature difference through the wall."),
        ("g", "Here Bree's diagram is computed numerically with a through-wall model: sixty-five hundred load combinations, primary stress on one axis, thermal stress range on the other, each cycled twenty-four times. Watch the regimes appear: elastic, shakedown, alternating plasticity once the thermal range passes twice yield, and two ratcheting regions. The computed map matches Bree's analytical boundaries at every point but one, which lies exactly on a boundary."),
        ("h", "The same physics appears in our notched plate. We apply a constant tension, then cycle a temperature field that is hot in the centre and cool at the edges. With a low tension, the hole edge yields back and forth, but the length of the plate stops changing: alternating plasticity. Double the tension, and the plate grows by twenty-two micrometres every cycle: structural ratcheting."),
        ("i", "The difference is the elastic core. In the safe case, part of the ligament never yields during a cycle and keeps carrying the primary load. In the ratcheting case, no elastic core is left."),
        ("j", "Material ratcheting is a separate effect, and it depends strongly on the hardening model. Under stress control with a mean stress, linear kinematic hardening predicts closed loops and no ratcheting at all. A single Armstrong–Frederick back-stress predicts strong ratcheting, almost two percent in fifteen cycles. A multi-component Chaboche model lands in between. If ratcheting matters, calibrate the model against ratcheting tests, not just a stress–strain curve."),
        ("k", "So how do you assess accumulated plastic strain in practice? First, run enough cycles. ASME requires at least three, and Eurocode 3 Part 1-6 uses the increment after the third cycle. Second, separate the response: extract the plastic strain increment over the last cycle, the plastic strain range, and the change in key dimensions from cycle to cycle."),
        ("l", "Third, apply the acceptance criteria. ASME Section eight, Division two, accepts the elastic-plastic ratcheting check if there is no plastic action, or an elastic core in the primary load-bearing boundary, or no permanent change in the overall dimensions. EN 13445 requires shakedown to be shown, for example with Melan's theorem. Eurocode 3 Part 1-6 limits the total accumulated equivalent plastic strain over the design life to twenty-five times the yield strain, about four point two percent for S355. And ASME's local strain criterion compares the accumulated equivalent plastic strain with a limit strain that falls with stress triaxiality, adding up damage for load sequences."),
        ("m", "Fourth, if the response is alternating plasticity, compute fatigue damage from the stabilised strain range with a strain–life method and add it to the high-cycle damage. If it ratchets, the net strain consumes ductility on top of fatigue. A simple engineering estimate adds a ductility exhaustion term, the ratchet strain over the fracture strain, to the fatigue damage. But in design codes, continued ratcheting is generally simply not acceptable."),
        ("n", "So, is accumulated plastic strain a problem? If it stops growing, the structure has shaken down, and you are back in high-cycle fatigue, with the right local mean stress. If it grows because of a closed cycle, it is low-cycle fatigue, governed by the plastic strain range, not by the accumulated total. And if it grows because the strain itself keeps drifting, that is ratcheting, and that is the case you must design out."),
    ]),
    ("s08_summary", [
        ("a", "Let's put it all together."),
        ("b", "Start with a linear-elastic analysis. If the equivalent stress range stays below twice the yield strength everywhere, the structure shakes down. Use high-cycle methods: local, hot-spot or notch stresses, corrected for mean stress, with rainflow counting and Miner's rule."),
        ("c", "If not, run an elastic-plastic analysis with a cyclic material model for several cycles. Check ratcheting: no growth of strains or dimensions from cycle to cycle, or an elastic core. Then take the stabilised loop, compute the low-cycle fatigue life from its strain range, check accumulated strain against local failure limits, and add the low- and high-cycle damage."),
        ("d", "High-cycle fatigue is about stress amplitude and strength. Low-cycle fatigue is about plastic strain range and ductility. And accumulated plastic strain only means something once you know which of the two, or whether ratcheting, is behind it."),
        ("e", "Thanks for watching."),
    ]),
]


def spoken(text):
    out = text
    for k in sorted(PRONUNCIATION, key=len, reverse=True):
        out = out.replace(k, PRONUNCIATION[k])
    return out


if __name__ == "__main__":
    total = 0
    for sid, segs in SCENES:
        w = sum(len(t.split()) for _, t in segs)
        total += w
        print(f"{sid:14s} {w:5d} words  ~{w/150*60:5.0f} s")
    print(f"total {total} words ~ {total/150:.1f} min")
