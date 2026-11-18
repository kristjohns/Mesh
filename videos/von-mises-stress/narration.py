"""Narration script for "The Physics of Failure – Understanding von Mises Stress".

Each scene is a list of (segment_id, text) beats.  The same text drives
  * the voice-over  (tools/tts.py applies TTS_SUBS for pronunciation),
  * the animation timing (scenes read the measured duration of every beat),
  * the subtitles   (tools/assemble.py applies CAPTION_SUBS for display).

Math is written the way it is spoken ("sigma v m"); CAPTION_SUBS turns it back
into symbols for the subtitle track.  {PIPE_VM} / {PEAK_VM} are filled in from
the finite element results (assets/fea/summary.json).
"""

SCENES = [
    ("S01_Opening", [
        ("o1", "A drive shaft. A riser joint. A subsea connector. In service, steel is rarely loaded "
               "one way at a time: it is pulled, bent and twisted, all at once."),
        ("o2", "Inside, the loads build up a stress field. Zoom in to a single material point, and on "
               "the faces of an infinitesimal cube, three normal stresses pull or push, while three "
               "shear stresses slide the faces past one another. Together they form the Cauchy stress "
               "tensor: symmetric, with six independent components."),
        ("o3", "But the strength we measure comes from a uniaxial tension test, as a single number: the "
               "yield strength. So how do we decide whether a full three-dimensional stress state will "
               "make the material yield?"),
        ("o4", "Checking each component against the yield strength fails immediately. A shaft in pure "
               "torsion yields when its shear stress reaches only about fifty-eight percent of the "
               "tensile yield strength. And a solid specimen squeezed equally from all sides, far "
               "beyond that strength, does not yield at all."),
        ("o5", "We need one equivalent stress, built from the whole tensor, comparable with the tension "
               "test. To find it, we must first understand what yielding physically is."),
    ]),
    ("S02a_Micro", [
        ("m1", "Structural steel is a polycrystal: an aggregate of grains, each a nearly perfect lattice "
               "of iron atoms, each oriented differently."),
        ("m2", "Inside a grain, plastic deformation happens by slip: planes of atoms shearing past one "
               "another along close-packed directions, leaving the lattice intact and the volume "
               "unchanged."),
        ("m3", "Sliding a whole plane at once would break every bond across it simultaneously, needing "
               "roughly the shear modulus over two pi: gigapascals. Real metals yield orders of "
               "magnitude lower."),
        ("m4", "The reason is the dislocation: a line defect, here an extra half-plane of atoms. Under "
               "shear it glides, re-forming bonds one row at a time. When it exits, the crystal has "
               "slipped by one atomic spacing."),
        ("m5", "What drives it is the shear stress resolved onto the slip plane, in the slip direction: "
               "Schmid's law. Even a crystal in pure tension yields by shear, on inclined planes."),
        ("m6", "Now press equally from all sides. The traction on every plane is purely normal: no "
               "plane carries shear. No resolved shear, no glide, no yielding, as Bridgman's "
               "high-pressure experiments confirmed."),
    ]),
    ("S02b_Decomposition", [
        ("d1", "So we split the stress tensor in two. The mean stress, sigma m, one third of the trace, "
               "defines a hydrostatic part: sigma m times the identity. What remains is the deviatoric "
               "stress, s, with zero trace."),
        ("d2", "In an isotropic material, hydrostatic stress makes a cube grow or shrink, but it stays "
               "a cube: volume changes, shape does not."),
        ("d3", "Under pure shear, it distorts at constant volume: shape changes, volume does not."),
        ("d4", "Under combined loading, it does both, and only the distortion is linked to slip."),
        ("d5", "That is why the criterion we want is based on distortion energy, rather than the total "
               "strain energy that Beltrami proposed. Total energy includes volume change, and would "
               "predict yielding under pure pressure."),
    ]),
    ("S03a_Derivation", [
        ("v1", "Start with the principal stresses. In one particular orientation, every shear stress "
               "vanishes. The normal stresses that remain, sigma one, sigma two and sigma three, are "
               "the eigenvalues of the tensor: the roots of its characteristic equation."),
        ("v2", "Its coefficients, I one, I two and I three, are invariants, independent of our choice "
               "of axes. For an isotropic material, a yield criterion can depend only on these."),
        ("v3", "The mean stress is one third of I one. Subtracting it gives the principal deviators, "
               "s one, s two and s three, which always sum to zero, and do not change when all three "
               "stresses shift together."),
        ("v4", "Now the energy: one half of stress, double-dotted with strain. In Hooke's law, the mean "
               "stress drives volume change through the bulk modulus, K, and the deviator drives "
               "distortion through the shear modulus, G."),
        ("v5", "Multiply out, and the cross terms vanish, because the identity double-dotted with s is "
               "the trace of s: zero. The energy separates exactly, into a volumetric part and a "
               "distortional part: s double-dot s, over four G."),
        ("v6", "Half of s double-dot s is the second deviatoric invariant, J two. So the distortion "
               "energy is J two over two G."),
        ("v7", "Now the key step. Because the deviators sum to zero, the sum of their squares can be "
               "written using only their differences. And a difference of deviators is a difference of "
               "principal stresses: the mean cancels. So J two is one sixth of the sum of the squared "
               "principal stress differences."),
        ("v8", "Huber, von Mises and Hencky proposed that yielding begins when the distortion energy "
               "reaches its value at yield in a tension test: sigma one equal to the yield strength, "
               "written sigma capital Y to distinguish it from the component sigma y, and the other "
               "two zero."),
        ("v9", "Equate the two energies. The shear modulus cancels: the criterion does not depend on "
               "the elastic constants. What remains defines the von Mises equivalent stress: the square "
               "root of one half the sum of the squared principal stress differences. Equivalently, "
               "root three J two."),
    ]),
    ("S03b_RMSShear", [
        ("r1", "There is a physical reading, too. Average the squared shear stress over every plane "
               "through the point: the root-mean-square shear stress is proportional to root J two. "
               "For a polycrystal, with slip systems in every direction, the von Mises stress measures "
               "the shear available to drive slip."),
    ]),
    ("S03c_Cartesian", [
        ("c1", "Solvers report Cartesian components. In x, y and z, each shear stress appears twice in "
               "s double-dot s, since tau x y equals tau y x. So it contributes its full square to J "
               "two, and three times its square to sigma v m squared."),
        ("c2", "The normal stresses enter as squares minus cross products, which depend only on their "
               "differences."),
        ("c3", "Yielding begins when sigma v m reaches sigma Y. Precisely: the onset of yield at a "
               "point, in an isotropic, ductile, pressure-insensitive material, with equal yield in "
               "tension and compression. It says nothing about ultimate failure. Necking and fracture "
               "come much later, governed by different physics."),
    ]),
    ("S04a_CasesAB", [
        ("a1", "Let's test the criterion on five loading cases. Case A, uniaxial tension: sigma one "
               "equals sigma, the others are zero. Two differences equal sigma, one is zero, and sigma "
               "v m equals sigma, exactly."),
        ("a2", "By construction: the criterion was calibrated on this test. Yet even here, a "
               "hydrostatic part, sigma over three, plays no role."),
        ("b1", "Case B, pure shear: only tau x y is non-zero. The Cartesian form leaves three tau "
               "squared, so sigma v m is root three tau, and yield in shear occurs at sigma Y over root "
               "three: 0.577 sigma Y. For S three fifty-five steel, about 205 megapascals."),
        ("b2", "Why root three? Rotate the element by forty-five degrees: pure shear is a tension tau "
               "and a compression minus tau, at right angles. Its principal differences are tau, tau "
               "and two tau: a sum of squares of six tau squared, against two sigma squared for "
               "tension. So shear reaches the critical distortion at a stress root three times lower."),
    ]),
    ("S04b_CasesCD", [
        ("cc1", "Case C, equal biaxial tension, as in a thin spherical shell. The differences are zero, "
                "sigma and sigma: again, sigma v m equals sigma."),
        ("cc2", "Why? Equal biaxial tension is a hydrostatic tension sigma, plus a uniaxial compression, "
                "minus sigma, in the third direction. The hydrostatic part is invisible, so despite two "
                "equal stresses, the state carries a full uniaxial measure of distortion."),
        ("dd1", "Case D, hydrostatic stress: all three principal stresses equal p. Every difference "
                "vanishes, so sigma v m is zero, at any pressure."),
        ("dd2", "A solid steel part at three thousand metres carries thirty megapascals of hydrostatic "
                "compression, and zero von Mises stress. A sealed pipe beside it, with one atmosphere "
                "inside, carries a large compressive hoop stress, and can yield or collapse. It is the "
                "pressure difference that distorts."),
        ("dd3", "Here the classical theory has limits: soils, concrete, polymers and porous metals are "
                "pressure-sensitive, and need criteria like Drucker Prager or Gurson. And in steel, "
                "hydrostatic tension causes no yield, yet it drives void growth and reduces ductility."),
    ]),
    ("S04c_CaseE", [
        ("e1", "Case E: a shaft under axial force and torque. At the surface, the axial force gives a "
               "normal stress sigma, and the torque a shear stress tau. The von Mises stress is the "
               "square root of sigma squared plus three tau squared."),
        ("e2", "In the sigma tau plane, that is an ellipse through sigma Y and sigma Y over root three. "
               "In 1931, Taylor and Quinney tested thin-walled tubes in exactly this combination; their "
               "yield points lay closer to this ellipse than to the maximum shear prediction."),
    ]),
    ("S05_YieldSurface", [
        ("y1", "Now see it all at once. With the principal stresses as coordinates, every stress state "
               "is a point. The line where all three are equal is the hydrostatic axis. Perpendicular "
               "to it lie the deviatoric planes; the one through the origin is the pi plane."),
        ("y3", "A stress point splits into a component along the axis, set by the mean stress, and a "
               "component in the deviatoric plane: the deviator itself, at a distance root two J two "
               "from the axis."),
        ("y4", "The von Mises condition fixes J two, so it fixes that distance: root two-thirds sigma "
               "Y, everywhere along the axis and all the way around it. The yield surface is a circular "
               "cylinder."),
        ("y5", "Circular, because the criterion ignores the Lode angle around the axis, which carries "
               "the third invariant. Infinitely long, because moving along the axis is pure hydrostatic "
               "stress."),
        ("y6", "Slice it with the plane sigma three equals zero, and out comes the plane-stress yield "
               "ellipse, with uniaxial tension, pure shear and equal biaxial tension exactly where we "
               "computed them."),
        ("y7", "Now increase the loads proportionally. The point moves out along a ray, and meets the "
               "cylinder when the load factor equals sigma Y over sigma v m: the safety factor against "
               "first yield. A hydrostatic path never reaches it."),
    ]),
    ("S06_Tresca", [
        ("t1", "The other classical criterion is Tresca's, from 1864: yielding begins when the maximum "
               "shear stress, half the largest principal stress difference, reaches sigma Y over two. "
               "Tresca pictures slip on the single most stressed plane; von Mises averages shear over "
               "all planes."),
        ("t2", "Its surface is a hexagonal prism around the same axis. In the pi plane, the hexagon is "
               "inscribed in the von Mises circle: they agree at the six vertices, the uniaxial and "
               "equal-biaxial states, and differ most at the midpoints of the sides, which are pure "
               "shear."),
        ("t3", "So Tresca is always equal or more conservative. In pure shear, it predicts yield at 0.5 "
               "sigma Y, against 0.577 for von Mises: about fifteen percent apart. Most ductile metals "
               "fall closer to von Mises."),
        ("t4", "And von Mises is smooth: its normal, the direction of plastic flow, is unique "
               "everywhere. That enables the robust radial return algorithm used for metal plasticity "
               "in essentially every finite element code. At Tresca's corners, the flow direction is "
               "ambiguous."),
    ]),
    ("S07a_FEAModel", [
        ("f1", "Now a real analysis: a forged steel transition for a subsea tubular, where the wall "
               "steps up to a thick hub through a shoulder fillet, under axial force, bending and "
               "torque."),
        ("f2", "It is meshed with quadratic tetrahedra, refined toward the fillet, where the stress "
               "gradients are steep."),
    ]),
    ("S07b_FEAMethod", [
        ("f3", "The solver finds the nodal displacements. In each element, it differentiates them at "
               "the integration points to get strain, and Hooke's law gives the full stress tensor at "
               "every Gauss point; then principal stresses from its eigenvalues, and von Mises stress "
               "from its invariants."),
        ("f4", "For plotting, results are extrapolated to the nodes and averaged. Averaging components, "
               "then computing von Mises, differs from averaging von Mises values; and large jumps "
               "between unaveraged values flag a mesh that is too coarse."),
    ]),
    ("S07c_FEAResults", [
        ("f5", "Here is the raw tensor in cylindrical coordinates: axial stress from tension and "
               "bending, shear from the torque, and hoop and radial stresses only at the step. None of "
               "them alone tells you whether the steel yields."),
        ("f6", "Combined point by point, they give one field: the von Mises stress. About {PIPE_VM} "
               "megapascals in the pipe wall, rising to {PEAK_VM} at the root of the fillet."),
        ("f7", "Why the peak? Picture the load flowing through the wall: at the shoulder, the flow "
               "lines turn into the hub, and crowd together at the fillet. The tighter the radius, the "
               "higher the peak."),
    ]),
    ("S07d_FEAPitfalls", [
        ("f8", "At a real fillet, refining the mesh makes the peak converge. Model the corner as "
               "perfectly sharp, and elasticity predicts a singularity: stress rising like r to the "
               "power minus 0.46. Each refinement reports a higher peak, without limit: a number set by "
               "your element size, not by your design."),
        ("f9", "So never take the maximum at face value. Check convergence, and model real radii. "
               "Where codes require it, linearize the stresses through the wall into membrane, bending "
               "and peak components, and apply the right limit to each."),
        ("f10", "And remember the material model. A linear elastic analysis reports stresses above "
                "yield, while real steel yields locally and redistributes the load. A local elastic "
                "peak above sigma Y calls for an elastic-plastic or fatigue assessment; it is not proof "
                "of failure."),
    ]),
    ("S08_Design", [
        ("g1", "Let's finish with numbers. The yield strength is 355 megapascals. At the critical "
               "point, the principal stresses are 240, 80 and minus 40 megapascals."),
        ("g2", "The mean stress is 280 over three: 93.3 megapascals. Subtracting it gives the "
               "deviators: 146.7, minus 13.3 and minus 133.3, which sum to zero."),
        ("g3", "The principal differences are 160, 120 and minus 280. Their squares, 25,600, 14,400 "
               "and 78,400, sum to 118,400. Half of that is 59,200."),
        ("g4", "The square root gives the von Mises stress: 243.3 megapascals, confirmed by three J two "
               "from the deviators."),
        ("g5", "The safety factor against first yield is 355 over 243.3: 1.46, a utilization of 69 "
               "percent. Tresca gives 1.27: more conservative. The largest principal stress alone would "
               "give 1.48: slightly unconservative, because it ignores the compressive third stress."),
        ("g6", "Keep the terms distinct. Yield strength is a material property. Equivalent stress "
               "describes the stress state at a point. The safety factor is their ratio. And the design "
               "allowable is what a code permits: the yield strength reduced by partial or usage "
               "factors for uncertainty and consequence."),
        ("g7", "And staying below yield is necessary, not sufficient. Welded joints fail in fatigue at "
               "stresses far below yield. Slender members and shells buckle. Cracks cause fracture, "
               "governed by toughness. And excessive deformation can make a connector leak long before "
               "anything yields."),
    ]),
    ("S09_Conclusion", [
        ("z1", "So here is the central insight. A material does not yield because one stress component "
               "becomes large. Every stress state has a hydrostatic part, which changes volume, and a "
               "deviatoric part, which changes shape. In ductile metals, distortion drives slip, and "
               "distortion governs yielding."),
        ("z2", "The von Mises stress measures exactly that: the square root of one half the sum of the "
               "squared principal stress differences."),
        ("z3", "Von Mises stress transforms a complex three-dimensional stress state into one "
               "physically meaningful quantity that can be compared against the material's uniaxial "
               "yield strength."),
    ]),
]

# Spelling -> pronunciation for the TTS front end (espeak-ng phonemizer).
TTS_SUBS = [
    ("von Mises", "von Meezus"),
    ("Cauchy", "Koh-shee"),
    ("Huber", "Hoober"),
    ("fillet", "fillit"),
    ("Lode angle", "Lohda angle"),
    ("Drucker Prager", "Drucker Prahger"),
    ("re-forming", "ree-forming"),
]

# Spoken math -> displayed symbols for subtitles (longest phrases first).
CAPTION_SUBS = [
    ("sigma v m squared", "σ_vm²"),
    ("sigma capital Y", "σ_Y"),
    ("sigma Y over root three", "σ_Y/√3"),
    ("sigma Y over sigma v m", "σ_Y/σ_vm"),
    ("sigma Y over two", "σ_Y/2"),
    ("0.577 sigma Y", "0.577 σ_Y"),
    ("0.5 sigma Y", "0.5 σ_Y"),
    ("root two-thirds sigma Y", "√(2/3) σ_Y"),
    ("sigma v m", "σ_vm"),
    ("sigma Y", "σ_Y"),
    ("sigma y", "σ_y"),
    ("sigma m", "σ_m"),
    ("sigma one", "σ₁"),
    ("sigma two", "σ₂"),
    ("sigma three", "σ₃"),
    ("sigma over three", "σ/3"),
    ("sigma tau plane", "σ–τ plane"),
    ("tau x y", "τ_xy"),
    ("tau y x", "τ_yx"),
    ("s double-dot s", "s:s"),
    ("s one", "s₁"),
    ("s two", "s₂"),
    ("s three", "s₃"),
    ("I one", "I₁"),
    ("I two", "I₂"),
    ("I three", "I₃"),
    ("root three J two", "√(3J₂)"),
    ("root two J two", "√(2J₂)"),
    ("root J two", "√J₂"),
    ("J two over two G", "J₂/2G"),
    ("J two", "J₂"),
    ("root three tau", "√3 τ"),
    ("root three", "√3"),
    ("three tau squared", "3τ²"),
    ("six tau squared", "6τ²"),
    ("two sigma squared", "2σ²"),
    ("sigma squared", "σ²"),
    ("M squared plus three quarters T squared", "M² + ¾T²"),
    ("r to the power minus 0.46", "r^−0.46"),
    ("pi plane", "π-plane"),
    ("S three fifty-five", "S355"),
    ("shear modulus over two pi", "shear modulus over 2π"),
    ("minus sigma", "−σ"),
    ("minus tau", "−τ"),
    ("Drucker Prager", "Drucker–Prager"),
]
