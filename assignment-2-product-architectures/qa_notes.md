## Q: What makes a good jig? The nests in the robot cell are flat boxes. How does a part stay put, and how does a human load it right?
<!-- asked: 2026-10-16 -->
A jig must **locate** (every part in one exact place, every time), **hold** (stay there while the robot pushes) and be **foolproof** (it can only go in one way). Rules from fixture design:

| Rule | Meaning | In our cell |
|---|---|---|
| **3-2-1 locating** | 6 DOF fixed by 3 points on a base plane, 2 on a side, 1 at the end, no more (more = binding) | frame top rail on the plate (3), fence along the front post (2), end stop at the outer face (1) |
| **one datum, push towards it** | push / clamp force always points *into* a fixed locator | S1 left sits against a fixed end stop; planks and S1 right are pushed **towards it**, so every reaction goes into the stop |
| **nest only where it locates** | pocket walls / pins only on surfaces that matter; leave the rest free | comb ribs in the gaps between the planks fix $y$ (pitch $P$); nothing near the plank ends, where the frames go |
| **poka-yoke** | a feature that makes the wrong part or wrong way impossible | mirror parts (S1L/S1R, S5L/S5R, S6L/S6R) get mirrored pockets with a key; W1 and W2 differ in length; face-up/-down by a rib in the plank's end cut |
| **lead-ins** | chamfers on every pocket / pin | loading by hand and robot placement both tolerate a few mm error |
| **access** | locators visible to the operator; reliefs where fingers / tools go | finger reliefs at the grip points; low walls ($\le \tfrac12$ part height) |
| **tray datums** | the kitting tray itself is located on the table (round pin + diamond pin) | one robot program for every tray refill |

Printed (FDM, PLA) jigs: holes print small, pins large. Use $0.2$–$0.3$ mm clearance per side, walls $\ge 2$ mm, and print one test pocket first. Thin features that must be stiff, like the rod rest blade (1 mm between the planks), are better laser-cut steel in a printed slot.

Riser height: tested in RoboDK. 120 mm works; 60 and 30 mm fail at the **flip**. The wrist is horizontal at the post both upside down (nest) and upright (finish), so the two grip heights add up to $2 \cdot$ riser $+$ frame height. One of them is always low, so the riser stays at about 120 mm. Lower risers need a different flip, e.g. a turnover fixture.

Sources: [Carr Lane, fixture design principles](https://www.carrlane.com/engineering-resources/fixture-design-priciples), [Applied Engineering, Jig and Fixture Design](https://go-applied.com/wp-content/uploads/2014/12/Jig-and-Fixture-Design.pdf), [Vention, trays for machine-tending cells](https://vention.io/blogs/machine-tending-designing-trays-and-drawer-systems-for-machine-tending-robot-cells-274), [Sovol, 3D-printed jigs](https://www.sovol3d.com/blogs/news/3d-printed-jigs-and-fixtures-how-to-design-reliable-workshop-aids), [Oakland Univ. FDM guidelines](https://www.secs.oakland.edu/~latcha/ME4999/fdm_design_guidelines_2017-1.pdf).

## Q: How does one cobot assemble the demonstrator (RoboDK simulation)?
<!-- asked: 2026-10-16 -->
Omron TM5-900, one gripper with two TCPs (fingers $+$ suction cup on a stroke cylinder), parts from Fusion (`robot_cell/`). Result: every step reachable, no robot/gripper collision, parts within $0.002$ mm of the design.

| Product | Steps | Cycle (100 mm/s, 60°/s) |
|---|---|---|
| C1 chair | 9 | $\approx 69$ s |
| C2 chair with back | 13 | $\approx 95$ s |
| B1 bench | 11 | $\approx 86$ s |
| B2 bench with back | 15 | $\approx 112$ s |
| P1 planter | 22 | $\approx 170$ s |
| P2 planter long | 22 | $\approx 170$ s |

C1/B1: after the flip the two ornaments S6 drop straight into the sockets. P1/P2: the 4 posts are **one part S4** turned $0/90/180/270°$ (checked: identical solids). Front wall module (2 posts pushed onto 4 front planks in a nest) → carried over and pushed onto the 8 side planks standing at the finish station → rear module the same way.

Sequence (B2): seat planks face down into a nest → rod onto a rest blade → **S1 left/right lowered beside the plank ends and pushed on** (all barbs click at once) → rod quarter turn → flip the seat module upright → back planks face down into a back nest → S5 pushed on → back module: pegs straight down into the sockets.

What the simulation changed:

| Finding | Why | Fix in the cell |
|---|---|---|
| frames go onto the planks, not planks into the frames | a rigid plank can't enter a closed channel at an angle | nest holds the planks at pitch $P$, robot pushes the frame sideways |
| seat built upside down | at 1:7.5 the wrist can't reach under the seat to turn the rod | rod turned from above, then one wrist flip ($J_6$ 180°) |
| quarter turn from $+60°$ to $-30°$ | tool pointing horizontally along the cell = wrist singularity ($J_5 \approx 0$) | tilted start and end |
| risers under the nests, longer fingers (113 mm) | wrist housing hits the table / frames | room under the wrist |
| back module built face down, placed from behind | the wrist would otherwise reach over the seat | — |

The field move (push deep, slide back) stays for replacing one plank by hand: real wood bends.

## Q: What to keep in mind when 3D printing the demonstrator (bench 1500 → 200 mm)?
<!-- asked: 2026-10-16 -->
Scale $s = \tfrac{200}{1500} = \tfrac{1}{7.5}$. **Scale the products, not the interfaces** — scaled features drop below what a 0.4 mm nozzle can print:

| Feature | Full | $\times s$ | Printed (PLA, FDM 0.4) |
|---|---|---|---|
| frame member | 50 | 6.7 | **10** (room for channel, socket, rod) |
| wall | 3 | 0.4 | 1.2 (3 lines) |
| prong width | 10 | 1.3 | 2 |
| cut length | 50 | 6.7 | 10 (keeps PLA under $\approx 30$ MPa) |
| barb | 1 | 0.13 | 0.5 |
| clearance per side | 0.5 | 0.07 | 0.25 |
| saw cut under prongs | 2 | 0.27 | 0.6 |
| plank end inside frame | 23.5 | 3.1 | 4 |
| bayonet ramp rise | 3 | 0.4 | 1 |

PLA snap check: $\sigma = \tfrac{1.5\, E\, \delta\, b}{L^2} = \tfrac{1.5 \cdot 3500 \cdot 0.25 \cdot 2}{10^2} \approx 26$ MPa (PLA yields at $\approx 50$–$60$).
- **Orientation:** planks flat (prongs bend along the layers), frames on their side (channels vertical, no overhang).
- Holes print small: $+0.1$–$0.2$ mm; chamfer bottom edges 0.4 mm (elephant's foot).
- PLA is brittle: snap once, gently. Print one plank end + one channel as a test piece first.

## Q: Interface only in the top half of the plank end, bottom half solid and square?
<!-- asked: 2026-10-16 -->
Works **with a thin horizontal saw cut at mid height** under the prongs (otherwise the prongs are glued to the bottom half and can't bend):

| | Full-depth cut | Top-half interface + mid-height saw cut |
|---|---|---|
| prongs | $10 \times 28$ | $10 \times 13$ (same $\sigma \approx 30$ MPa, half the force: $\approx 0.13$ kN) |
| carries the load at the frame mouth | 2 prongs, $560$ mm² → $\tau \approx 2.7$ MPa | solid $95 \times 13$ tongue, $1235$ mm² → $\tau \approx 1.2$ MPa |
| seen from above | a hole through the plank | a shallow recess |
| underside | split | flat and square |

Mid span is unchanged — the bench still needs the middle support or a taller W1.

## Q: Can the bench do without the middle support (it's ugly)? Does a half-depth end cut help?
<!-- asked: 2026-10-16 -->
**No** — the end cut only changes the plank's ends; the problem is bending at **mid span**, where the section is the full $95 \times 28$ either way. What helps is height $h$: $\sigma \propto 1/h^2$, $\delta \propto 1/h^3$.

| Bench plank W1 (span 1400, 1000 N on one plank) | $\sigma$ | $\delta$ |
|---|---|---|
| $95 \times 28$ | 28 MPa ✗ | 30 mm ✗ |
| $95 \times 45$, ends stepped down to 28 (same interface) | 11 MPa ✓ | 7 mm ✓ |

$$\tfrac{\sigma_{45}}{\sigma_{28}} = \left(\tfrac{28}{45}\right)^2 \approx 0.39, \qquad \tfrac{\delta_{45}}{\delta_{28}} = \left(\tfrac{28}{45}\right)^3 \approx 0.24$$
Step on the **underside** (seat top stays level), sloped not square (a square inside corner splits).

## Q: What if the cut in the plank end only goes half way through the thickness?
<!-- asked: 2026-10-16 -->
The uncut half is a $75 \times 14$ mm wood plate **joining the two prongs**. To bend inwards they would have to squeeze that plate in its own plane — practically rigid. So the spring is gone.

| Pros (cut from below) | Cons |
|---|---|
| top face intact: **no visible opening** | prongs can't bend → **no snap**; barbs only go in by crushing wood (very high force, weak, loosens) |
| shear area at the frame mouth $560 \to 1610$ mm², $\tau$ about $\tfrac13$ | (cut from the top instead: holds water) |
| a pocket open downwards drains | |

Keeps both: through cut, but plank end deeper in the frame (wider member), so most of the cut is hidden.

## Q: Will the bench (1400 mm span) and the plank-end interface hold the load?
<!-- asked: 2026-10-16 -->
Plank $95 \times 28$, $E \approx 11$ GPa, worst case $F = 1000$ N at mid span on **one** plank (simply supported):
$$
\begin{aligned}
I &= \tfrac{b h^3}{12} = \tfrac{95 \cdot 28^3}{12} \approx 1.74 \times 10^5\ \text{mm}^4, \qquad W = \tfrac{b h^2}{6} \approx 1.24 \times 10^4\ \text{mm}^3 \\
\sigma &= \tfrac{F L / 4}{W}, \qquad \delta = \tfrac{F L^3}{48 E I}
\end{aligned}
$$

| Span $L$ | $\sigma$ | $\delta$ | |
|---|---|---|---|
| 410 (chair) | 8 MPa | 0.8 mm | ✓ |
| 1400 (bench, no support) | 28 MPa | 30 mm | ✗ (design strength $\approx 15$–$20$ MPa) |
| 700 (bench + middle support S8) | 14 MPa | 4 mm | ✓ |

**Weak spot = the split end:** at the frame mouth only the two $10 \times 28$ prongs carry the end reaction $V$: $\tau = \tfrac{1.5 V}{2 \cdot 10 \cdot 28}$ → $V = 1000$ N gives $\tau \approx 2.7$ MPa, near softwood's shear strength ($\approx 2.5$–$4$ MPa). Fine for sitting; for a person standing on one plank end use hardwood (oak) or wider prongs. The steel frames are far from their limit.

## Q: The back socket is in every S1 — what goes in it on a chair without a back? A customer-designed ornament (e.g. a city crest)?
<!-- asked: 2026-10-16 -->
S1 stays **one part** for C1 and C2, so every S1 has the $30 \times 30$ socket; on C1 it would be an open hole → fill it with a short **ornament on the same split peg**. Good idea:

| Why it works | Watch out for |
|---|---|
| closes the socket — nothing looks unfinished | **abuse:** a tall piece is a lever; keep it low ($\lesssim 100$ mm) and solid |
| **mass customization / late differentiation:** the platform (S1, W2) stays standard, only a small cheap part changes per customer | **safety:** no points or sharp edges at the back of a seat (clothes, children); rounded outline |
| cheap to make: laser-cut plate (crest) welded to a standard peg | it must not look like a broken-off back: low and clearly decorative |
| the socket becomes an **accessory port**: back, ornament, sign, cup holder… all on one interface | |

Same socket on top of the planter posts S4 → the same ornaments fit chair and planter.

## Q: Could the plank end flex instead (a cut in the wood) so the frame only needs a fixed catch?
<!-- asked: 2026-10-15 -->
**Yes — feasible, and better for the architecture:** the spring sits in the cheap, replaceable part; the frame is a plain channel with a recess (easy to print or weld).

Split the end with a **horizontal kerf** (parallel to the faces) → two prongs of thickness $t$, barb on the outer face of each. Prong as a cantilever, $E \approx 10$ GPa, width $b = 95$ mm, tip deflection $\delta = 1.5$ mm:
$$
\begin{aligned}
I &= \tfrac{b t^3}{12} = \tfrac{95 \cdot 12^3}{12} \approx 1.4 \times 10^4\ \text{mm}^4 \\
F &= \tfrac{3 E I \delta}{L^3} \approx 0.6\ \text{kN} \quad (L = 100\ \text{mm}) \\
\sigma &= \tfrac{F L\, t/2}{I} \approx 27\ \text{MPa}
\end{aligned}
$$
$\sigma$ is below wood's bending strength ($\approx 40$–$80$ MPa) only with a long kerf ($L \gtrsim 100$ mm), so the kerf runs out of the frame (thin line on the plank edges).

| Risk | Counter |
|---|---|
| splits along the grain at the kerf root | drilled stop hole at the root; **plywood** (cross layers) doesn't split |
| creep — wood loses its spring over years | barb only has to hold, not clamp |
| swelling $\approx 2$–$3\,\%$ across the width ($\approx 2$ mm) | clearance in the channel, or plywood / thermo-wood |
, or should the interfaces be welded on? Could the frame be cast instead?
<!-- asked: 2026-10-15 -->
**Bent tabs in a closed tube: not feasible.** A tube laser can cut the U-slot, but bending the tab up (with a hook) needs a die *inside* the closed $50 \times 50 \times 3$ tube.

**Weld-on interfaces: yes** — one identical base frame for every product, product-specific interface welded on afterwards = **platform + late differentiation** (postponement). Weld before coating. Use standard, robot-friendly processes:

| Interface | Process |
|---|---|
| 5 keyhole stud | **stud welding** — headed stud (like a shear-connector stud), $\approx 0.1$ s per weld, gun on a robot |
| 1 pin, 8 fir tree | stud welding |
| 14 snap hook | laser-cut + press-brake bent **clip strip**, one strip per row welded in a fixture (pitch $P = 105$ mm set by the laser, not by hand) |

**Cast frame:** fine for rigid features (bosses, keyhole slots, hooks to slide under) — they come free in the mould. **Not for snaps:** cast iron is brittle, a deflecting hook cracks; ductile iron / cast aluminium are better but the spring should be in the plank side. High tooling cost → pays off only at volume; one pattern is enough since S1 is shared.

## Q: Which plank interfaces are strongest, which slide on vs. snap, and why does the snap-hook groove run the whole plank?
<!-- asked: 2026-10-15 -->
| # | Interface | How it goes on | Holds by | Pull-out strength |
|---|---|---|---|---|
| 14 | wide snap hook | straight down, snaps | form lock (hook in groove) | best — 40 mm hooks, est. same range as an M8 bolt ($\approx 3$–$5$ kN, not tested) |
| 5 | keyhole | down, then **slide** 25 mm along the plank | form lock (stud head under T-slot) | good, but can slide back out the same way |
| 7 | snap hook | straight down, snaps | form lock | medium — $15$ mm hooks |
| 8 | fir tree | straight down (press) | barbs bite the wood | medium, drops after wet/dry cycles |
| 1, 2, 3 | pin, fin, tab | straight down (press) | friction | weakest, loosens outdoors |

**Groove through the whole plank (7, 14):** one saw/router pass along each edge, and the plank has no "right end". But it gives **no stop along the length** — the hooks hold the plank down and sideways, not lengthwise, so it can be snapped on shifted or slide later. Fix: a **stopped groove** (pocket only where the clips are, $x = 5..45$ mm from each end), which locates the plank and blocks sliding. → Done 2026-10-15 for 7 and 14 (pocket = tab length $+ 2$ mm).

## Q: How easy is it to export a RoboDK program to TMflow?
<!-- asked: 2026-10-16 -->
Tested with a pick-and-place on the TM5-900 (`robot_cell/tests/tmflow_export_test.py`, output in `robot_cell/tests/tmflow_test/`).

| RoboDK post | Output | Into TMflow | Result |
|---|---|---|---|
| **Omron** (use this) | `.zip` → `.flow` + `.dat` + TCP | USB `TMROBOT/TM_Export/<folder>/Projects/` → System → Import/Export | native TMflow **1.72** project: Point, SET, WaitFor nodes; speeds ($60\ °/\mathrm{s} \to 32\,\%$, $100$ mm/s) and $500$ ms wait correct |
| Techman_TMscript | `.scpt` | TMflow 2.x script project only | Line in `"CPP"` = $100\,\%$ speed, not $100$ mm/s; Cartesian PTP without the pose config |
| Omron_Remote | `.script` + `.py` | Listen node, port $5890$ | timed wait becomes `Pause()`, PTP speed $0\,\%$ |

Fix on the robot after import: gripper output (exported as Control Box DO 0), TCP mass ($0$ kg), blending on pick/place points (exported with $1\,\%$ blend, precise positioning off).

**Licence:** generating programs needs a paid/trial licence. The trial covers one running RoboDK instance only; a second instance falls back to *Free* (no program generation, no saving a station with a robot).

## Q: The planks are rigid — how do we make sure the robot hits the frame interfaces (Bench V1, built on its side)?
<!-- asked: 2026-10-16 -->
**CAD as modelled:** window $25.4 \times 5.4$ mm for a $25 \times 5$ mm plank → gap $g = 0.2$ mm per side, no chamfer on window or plank end → capture range $\pm 0.2$ mm.

| Error source | Size |
|---|---|
| TM5-900 repeatability | $\pm 0.05$ mm |
| offline program vs real cell (robot accuracy, jig placement) | $\approx 1$–$2$ mm unless taught |
| FDM parts | $\pm 0.1$–$0.3$ mm |
| plank tilt $\theta$ in the fingers, lever $L = 235$ mm | $e = L \tan\theta$: $0.5° \to 2$ mm |

Planks standing in frame 1 alone (depth $t = 10$ mm, play $2g = 0.4$ mm):
$$\theta_{max} = \arctan\frac{2g}{t} \approx 2.3°, \qquad e_{top} = 240 \tan\theta_{max} \approx 10 \text{ mm}$$
→ frame 2 onto six free plank tops is the hardest step.

| Fix | Effect |
|---|---|
| **lead-ins**: window chamfer $c_w = 1.5$ mm, plank end chamfer $c_p = 1$ mm | capture $\approx c_w + c_p + g = \pm 2.7$ mm |
| **two-level jig**: frame 2 on ledges 240 mm above frame 1, planks dropped through both | plank guided by 2 windows 230 mm apart, no "6 at once" step |
| release in the chamfer / push with closed fingers, soft pads | part self-aligns (force control only with an F/T sensor) |
| teach the jig base on the robot (3 points or TM Landmark) | offline error → $\approx$ repeatability |

**Decision (2026-10-16):** keep the order frame 1 → planks → frame 2, all straight down; **tight fit** in the windows (planks stand straight) + chamfers (CAD); the robot **pushes each part home** with closed fingers after the release, frame 2 at 3 solid spots, last 40 mm at 10 mm/s (`robot_cell/bench_cell.py`). A fixed two-level jig was rejected: both frames have the same outline, so ledges holding frame 2 block frame 1's way down.

## Q: How do we give RoboDK the real position of the jig: touch every corner with the arm, or use vision?
<!-- asked: 2026-10-16 -->
**3 touched points define a frame** (a 4th only as a check): origin $O$, a point $P_x$ on the $x$ edge, a point $P_{xy}$ on the plate:
$$\hat x = \frac{P_x - O}{\lVert P_x - O\rVert},\quad \hat z = \frac{\hat x \times (P_{xy} - O)}{\lVert \hat x \times (P_{xy} - O)\rVert},\quad \hat y = \hat z \times \hat x$$
TMflow does this itself (Base Manager, 3-point base). Needs a pointed tip with a correct TCP.

| Way | How | Use |
|---|---|---|
| **named base** | RoboDK program uses frame "Jig" → TMflow export carries base "Jig" (type C), all points relative to it | re-teach "Jig" on the robot → whole program follows |
| type in 6 numbers | read X Y Z RX RY RZ of the taught base in TMflow | keeps RoboDK (collision check) in sync |
| **Ethernet Slave log** | port 5891, robot streams selected items at 100 Hz, read-only | hand-guide to a point, log it; good for many points |
| **TM Landmark (vision)** | wrist camera finds a printed marker → vision base each cycle | jig that moves (AMR, removable jig); needs calibration + light, less precise than a careful touch |

One base plate with all fixtures at designed positions → **one** base to teach.

## Q: Can the plank guide be double-sided, so it moves from base A (frame 1) to a mirrored base B (frame 2)?
<!-- asked: 2026-10-16 -->
**Yes.** Flipped onto the mirrored base, the guide's slot pattern matches frame 2 — but the lead-in must then be on both faces.

| | original guide | `JigGuide_DoubleSided.STEP` |
|---|---|---|
| entry (each lead-in face) | $29.8 \times 11.25$ mm, top only | $29.8 \times 11.25$ mm, **both** faces |
| lead-in depth | 28 mm | 15 mm per face |
| straight section ($25.65 \times 5.65$ mm) | 12 mm, bottom | 10 mm, middle |
| slots placed for | older frame V0 | **BenchInterfaceV1** |

**Found while doing it:** the jig was drawn around the older frame (`BenchInterfaceV0_wBackRest`, backrest $\approx 1.6°$ different). Back slots of the original guide sit $0.4 / 1.3 / 2.1$ mm off planks 4/5/6 (clearance only $0.33$ mm per side), and the V1 backrest top runs $\approx 2$ mm into the base pocket → base and guide need the V1 frame.

**Open:** after the second insertion the guide is **trapped between frame 1 and frame 2** around the planks (closed slots) → it must split in two or have slots open to one side, or frame 2 gets chamfered windows instead. Two $180 \times 180$ bases do not fit side by side on the $270 \times 310$ work plate.

## Q: The guide ends up trapped between frame 1 and frame 2 — can we make a guide that doesn't trap it?
<!-- asked: 2026-10-17 -->
**Yes: cut it in two along the plank rows.** Together the halves close every slot (same funnels); each half only touches a plank on sides it can slide away from. Coordinates of the guide on base A: bench up $= +y$, $\mathbf w = (0.174, 0.985)$ along the back planks, $\mathbf t = (0.985, -0.174)$ across them (pointing back).

| | **inner half** (seat corner + front end) | **outer half** (under the seat + behind the backrest) |
|---|---|---|
| seat slots | wall on top | wall underneath + both ends (U) |
| back slots | front wall + both ends (U) | wall behind |
| way out | forward $-\mathbf t$, then up $+y$ | down $-y$, then back $+x$ |

A wall with outward normal $\mathbf n$ (from the plank) lets its half move along $\mathbf d$ only if $\mathbf d \cdot \mathbf n \ge 0$:

$$
\begin{aligned}
\text{inner: } \mathbf d &= -\mathbf t: && \mathbf d\cdot(-\mathbf t) = 1, \quad \mathbf d \cdot (\pm \mathbf w) = 0 \;(\text{ends slide}), \quad \mathbf d \cdot (0, 1) = 0.17 \
\text{outer: } \mathbf d &= (0, -1): && \mathbf d\cdot(0,-1) = 1, \quad \mathbf d \cdot (\pm 1, 0) = 0 \;(\text{ends slide}), \quad \mathbf d \cdot \mathbf t = 0.17
\end{aligned}
$$

One rigid piece can't do both rows (it would need pure $\pm y$ and pure $\pm\mathbf t$ at once).

**Built as version v4** (`jig_parts_v4.py` → `CAD/Jig V1/v4 split guide/`, cell `bench_cell_v4.py`; v3 = one guide, `bench_cell_v3.py`):

| | |
|---|---|
| cut | through the middle of the grip pocket ($y$ $-80 \dots -60$, cut at $-70$) |
| carrying the guide | fingers in the middle clamp both halves → the version-3 moves unchanged |
| one half | fingers $5$ mm to its side ($8$ mm fingers in $10$ mm) |
| end of the program | inner out $8$ mm, outer out $8$ mm; each lifted $50$ mm, pushed back onto a $180 \times 380 \times 80$ pad behind the bases |
| then | bench gripped at frame 1's foot from above, set down on the AMR beside base A ($-y$); AMR drives $2$ m along the table and back |
| check | 3D: overlap with planks / other half $= 0$ along both ways out; RoboDK: no collisions, fingertips inside (except the hand-over), every part ends within $0.003$ mm |

## Q: How long does one assembly take with each assembly-method version?
<!-- asked: 2026-10-17 -->
Logged per version in `robot_cell/cycle_times.csv` (`python robot_cell/cycle_times.py`; every build adds a row). Time = the robot program's path at its **programmed speeds** + gripper waits, no accelerations; AMR drive not included.

| version | method | one bench | path |
|---|---|---|---|
| v3 (`bench_cell_v3.py`) | one double-sided guide B→A→B; guide trapped, no hand-over | $240$ s | $15.9$ m |
| v4 (`bench_cell_v4.py`) | guide in two halves, halves onto a pad, bench onto the AMR | $345$ s | $21.5$ m |

v4 per phase: guide to A $34$ s, planks $124$ s, guide to B $36$ s, frame 1 + planks $46$ s, inner half $39$ s, outer half $34$ s, bench to the AMR $28$ s. The planks dominate ($6 \times 21$ s, mostly the $20$ mm/s moves near parts).

RoboDK's own estimate (Program → Update) is unreliable here ($81$ s or $212$ s for the same v4 program); a real-time RoboDK simulation of v4 took $353$ s, close to the $345$ s calculated. The robot's real time comes from the lab.

## Q: Can the Omron mobile robot be integrated so it delivers the bench automatically (network / TMflow)?
<!-- asked: 2026-10-17 -->
**Yes.** Omron's AMRs take commands over the network through **ARCL**, a plain-text TCP server on the AMR (or its Fleet Manager), enabled in MobilePlanner; port $7171$ is the one seen in practice. Commands like `goto <goal>`; the AMR answers with status lines (e.g. "Arrived at …"). Syntax: ARCL Reference Guide.

| Way | How | Use |
|---|---|---|
| **PC script** (first) | laptop reads the TM (Ethernet Slave $5891$ / Modbus $502$, already used) and sends ARCL to the AMR | quick test at the lab, no TMflow changes |
| TMflow directly | socket node at the end of AssembleBench: `goto Delivery`, wait for "Arrived" | final, no PC; check the node in TMflow 1.88 |
| Fleet Manager | jobs (`queuePickup …`) via ARCL on the fleet manager | if the lab runs one |

Cycle: AMR `goto BenchCell` → arrived → TM places the bench → TM/PC `goto Delivery` → AMR drives and returns.

**Catch:** the AMR stops at a goal only to within a few cm → the drop-off needs a **vision base** (TM Landmark on the plate, re-found each time) or a mechanical docking guide at the table.

**Needed from the lab:** AMR model + IP, ARCL enabled + its password, goals "BenchCell" and "Delivery" in the AMR's map, permission to command it.
