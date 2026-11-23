# MMA4002 final report: content skeleton

- **What this is:** everything worth carrying over from the group's earlier reports, sorted under the final report's headings (`Sections/*.tex`). Read it, then write each section from its block. Rule: **reuse, don't rewrite**.
- **Deadline: 18 Dec 2026.** Four deliverables: final report, presentation, video, group reflection ([Report plan](<Report plan.md>) R10).
- **No page limit, but keep it short:** one idea per subsection, numbers in tables, detail in appendices (R10).
- **The abstract matters most** (professor's advice, R11): write it last, from "Abstract building blocks" below, and have it reviewed.
- **Every course module and its theory must appear** (R12): the check is the "Module coverage" table near the end.
- Made 2026-11-23 from the sources in the table below. Assumptions are in the last part. Nothing here is new content: every bullet has a source.

**Source codes used below** (page = PDF page):

| Code | File |
|---|---|
| A1 | [A1 report](<../assignment-1-manufacturing-demonstrator-concept/MMA4002_Manufacturing_Demonstrator_Concept.pdf>), 8 p., Sept 2026 |
| A2 | [A2 report](<../assignment-2-product-architectures/Deliverable/MMA4002___Assignment_2_Product_Architectures.pdf>), 16 p., Oct 2026 |
| A3 | [A3 report](<../assignment-3-lean/MMA4002___Assignment_3_Lean.pdf>), 8 p., Oct 2026 |
| A4 brief | [task description](<../assignment-4-design-for-automatic-assembly/assignment-4-task-description.md>). **No group A4 report exists.** |
| A5 deck / script | [deck v2](<../assignment-5-industrial-review-board-presentation/MMA4002_IRB_Outdoor_Bench_v2.pptx>) (9 slides), [speaker script](<../assignment-5-industrial-review-board-presentation/IRB presentation script.docx>), 9 Nov 2026 |
| VIS | [vision picture report](<../3d-modeling-and-simulation/robot-cell/vision report/jig_vision_report.pdf>), 8 p., 17 Nov |
| VISD | [vision detailed report](<../3d-modeling-and-simulation/robot-cell/vision report/jig_vision_report_detailed.pdf>), 5 p., 13 Nov |
| PB / PB2 | [Part B](<../3d-modeling-and-simulation/assembly-experiment/report/part_b_report.pdf>) (7 p.), [Part B2](<../3d-modeling-and-simulation/assembly-experiment/report/part_b2_report.pdf>) (12 p.), 22 Nov |
| QA | [qa_notes.md](<../3d-modeling-and-simulation/qa_notes.md>) (dated Q&A, 15–17 Oct) |
| CT | [cycle_times.csv](<../3d-modeling-and-simulation/robot-cell/cycle_times.csv>) (RoboDK-era log, v3–v8) |
| VER | [versions.csv](<../3d-modeling-and-simulation/assembly-experiment/results/versions.csv>) (Part A: v3–v10 scored with the own tools, 20 Nov) |
| NS | [robot-cell Next steps.md](<../3d-modeling-and-simulation/robot-cell/Next steps.md>) |
| CH | [vision config_history.md](<../3d-modeling-and-simulation/robot-cell/tests/vision_lab/config_history.md>) (first real-robot vision session, 20 Nov) |
| V11 | [v11_1plank_RESUME.md](<../3d-modeling-and-simulation/robot-cell/tests/v11_1plank_RESUME.md>) (real-robot one-plank test, 20 Nov) |
| TMB / AMR | [TM bridge plan](<../3d-modeling-and-simulation/robot-cell/TM bridge plan.md>), [AMR delivery plan](<../3d-modeling-and-simulation/robot-cell/AMR delivery plan.md>) |
| EXP | [assembly-experiment README](<../3d-modeling-and-simulation/assembly-experiment/README.md>) |

**Read this first: which "cycle time" is which.** No full bench cycle has been timed on the real robot. Every time below is one of these:

| Kind | Meaning | Example |
|---|---|---|
| estimate | guessed in A3 | assembly 5 min (A3 p. 7) |
| programmed-speed time | path length at programmed speeds + gripper waits, no acceleration, no AMR (QA "How long does one assembly take") | v3 239.8 s (CT, VER) |
| with ramps | same, with a trapezoid speed profile | v9 319.6 s (VER) |
| mock run | the TMflow mock running the program | v9-full 468.4 s ([run_times.json](<../3d-modeling-and-simulation/robot-cell/tests/run_times.json>)) |

---

## Abstract building blocks

Don't copy: these are the facts the abstract should hold.

| # | Fact | Source |
|---|---|---|
| 1 | **Product:** an outdoor bench family for public spaces. Customers are municipalities, larger companies and institutions, who pay for the message the furniture gives, not the lowest price. | A1 p. 2, A2 p. 4 |
| 2 | **Idea behind it:** most people prefer traditional over contemporary architecture (Mouratidis 2026); the hypothesis is that this holds for outdoor furniture. | A1 p. 2, ref. p. 7 |
| 3 | **Family:** 3 modules (bench frame 2 variants, plank 2 variants, interface 1 variant). Products: bench or chair, with or without backrest (4 CAD models, V3). The website adds the mark on the top plank: none, laser-cut or logo shield. | A2 p. 5, pp. 8–9; [index.html](../index.html) |
| 4 | **Design for the robot:** one frame, one plank section (25 × 5 mm on the demonstrator), one interface clip, no fasteners, all parts straight down. Pocket play 0.2 mm per side + chamfers lets the robot be ±2.7 mm off. | A5 script slide 3; QA "The planks are rigid" |
| 5 | **Demonstrator:** scale 1:7.5, 3D-printed PLA parts, laser-cut wood planks tested. | A5 deck slide 3; A1 p. 4; A2 pp. 10–11 |
| 6 | **Process:** web configurator → order → cut and bend / print → kit → cobot assembly (Omron TM5-900 + Robotiq Hand-E) → mark and check → AMR delivery. | A5 deck slide 4–5; A1 p. 5 |
| 7 | **Lean:** takt 3.648 h per bench (1000 benches in 6 months) against ≈ 17.9 min of work per bench (estimates): the cell uses ≈ 8 % of the available time. | A3 pp. 6–7 |
| 8 | **Own simulator and one program for simulation and robot:** simulator page → Python bridge → TMflow Listen node → robot. The program is checked for reach, collisions and manipulability before the lab. | A5 script slides 5–6 |
| 9 | **Assembly time in simulation** (programmed speeds): first working cell v3 239.8 s; current v9 286.7 s with more functions (split guide, bench onto the AMR), 0 collisions; a blind AI agent got v3's task down to 89.8 s (−63 %), legal under 8 hard rules. | VER rows v3, v9; PB2 p. 1 |
| 10 | **Vision:** ArUco markers find the jigs to a median of 0.14 mm (worst 0.5 mm) in simulation; with the jigs moved up to 44 mm and turned 11°, program V10 lands within 0.94 mm where the taught program V9 misses by up to 91 mm. | VISD p. 1; VIS pp. 1, 4–5 |
| 11 | **Honest limit:** the full cycle has not run on the real robot. Done on the robot: bridge and gripper, taught plank picks, a one-plank test, camera calibration. | TMB; NS §0; V11; CH |

---

## Section by section

### Introduction

#### Background and problem statement
**Carry over**
- "The product concept chosen is family of 'classy' and non-modernistic outdoor furniture with a focus on benches." The end user sits on it; the customer (municipalities, cities, larger companies) pays. (A1 p. 2)
- Customers "care less about the price of each individual bench and more about the message the furniture conveys". (A1 p. 2)
- Most mass-produced designs are modernistic; "most people questioned preferred traditional architecture over contemporary (Mouratidis 2026)". Hypothesis: the same holds for outdoor furniture. (A1 p. 2; full reference A1 p. 7)
- Need in one line: "comfortable, affordable and aesthetically pleasing outdoor furniture" for "medium to large companies and governmental bodies like municipalities, schools, hospitals". (A2 p. 4)

**Figures to reuse**
- A1 Fig. 1 (p. 2): four AI-generated concept sketches (bench, bench no back, chair, other design). Label them as AI-generated, as A1 does.

**Update needed**
- A1 says price matters less; A2 p. 4 says "affordable". Pick one wording.

**Gap**
- A problem statement for the *manufacturing* side (why automate, what the demonstrator must prove). A2's main question can be borrowed: "How can the demonstrator's product architecture enable simpler, repeatable and scalable manufacturing while preserving required customer functions?" (A2 brief p. 1).

#### The manufacturing demonstrator
**Carry over**
- "As a full size bench would be too large to reasonably fit in the manulab, a scaled demonstrator is proposed", 3D-printed and/or laser-cut wood. (A1 p. 4)
- Scale 1:7.5 (A5 deck slide 3). Scale the product, not the interfaces: printed features would fall below what a 0.4 mm nozzle prints (QA "What to keep in mind when 3D printing", table of full/scaled/printed sizes).
- Cell: Omron TM5-900, Robotiq Hand-E, T-slot plate with base A, base B, plank rack and a two-part guide; AMR = Omron LD-250 model in the simulation. (A5 script slide 5; VISD p. 1; NS §0c)

**Figures to reuse**
- `bench_cad_3d.png`, `bench_cad_side_light.png`, `cell_iso.jpg`, `cell_v9.jpg` in [deck/media](<../assignment-5-industrial-review-board-presentation/deck/media/>).
- A2 Fig. 18 and 20 (pp. 12, 14): photos of the printed baseline bench and the target bench with one wooden plank.

**Gap**
- One sentence on what was built physically vs only simulated (see "3.1 Results"). A2 p. 15 still says "Final demonstrator: Not yet finished".

#### Objective and scope
**Carry over**
- IRB message: "the product is designed for the robot, the cell for the product". (A5 script slide 3)
- A1's plan had three steps: CAD and common architecture by ≈ 10 Oct, jigs and procedure by end of Oct, run and film it at least one week before the deadline. (A1 p. 6)

**Gap**
- The objectives themselves are not written anywhere as a list. They are needed, because "3.2 Results against the objectives" answers them. Candidates that the sources can answer: (1) a product family from few modules, (2) assembly by one cobot without fasteners, (3) one program for simulation and robot, (4) capacity against takt, (5) jig positions found by vision.
- Scope limits to state: scaled demonstrator, simulation times, AMR delivery planned but not run.

#### Team, roles and contributions
**Carry over**
- Authors on A1, A2, A3: Bjørge Skjelbreid Djuve, John Isak Hammer (title pages).
- IRB speaker split: John Isak slides 2–4 and "learned"; Bjørge slides 5–7 and "next". (A5 script)
- Git commits (all branches, 2026-11-23): bjorgex 71 + Bjørge Djuve 28, ihammer18 6. (`git shortlog -sn --all`)

**Gap**
- A contribution table (R3; A2 brief deliverable 8 asked for one and A2 has none). `diary/` is empty. Commit counts under-count CAD and lab work, so the table has to be written by hand.

#### Report structure
- New text, 3–4 lines. Nothing to carry over.

---

### 1 Theory

No earlier report has a theory section. What exists is terms used in passing. The theory has to come from the course reading in `MSc-MechAuto-NTNU/H26/MMA4002-DAM/1 Lectures & Reading/` (not read for this skeleton, see assumption 5).

#### 1.1 Modular product architecture and product families
**Carry over**
- Integral vs modular, in the group's words: in an integral architecture "all the parts are dependent on each other", in a modular one (e.g. modular sofas) "some sub modules can be removed or destroyed without breaking the entire system". (A2 p. 5)
- Platform + late differentiation: one standard platform, a small cheap part changes per customer (the ornament / crest on a standard socket). (QA "The back socket is in every S1")
- PFMP customer view and engineering view are the frame A2 used (A2 pp. 4, 6).

**Gap**
- Definitions from Ulrich 1995 (function-to-component mapping, interface types), Harlou (PFMP views) and the week-42 lecture. Note: the Ulrich PDF's text copy is empty (scan), so it must be read as a PDF.

#### 1.2 Design for automatic assembly (DFA2)
**Carry over**
- Nothing on DFA2 itself. DFA principles the group used by name: top-down handling, present parts in assembly orientation (PB pp. 3, 5); "fewer grips/releases, not better moves" (PB2 p. 1).
- Fixture rules: 3-2-1 locating, one datum, poka-yoke, lead-ins, access. (QA "What makes a good jig", table)

**Gap**
- The DFA2 method (R5.3: "Explain DFA2 methodology"): the week-39 lecture (Paul Madapilly, Kongsberg thrust-bearing case) is not in the course folder. **Biggest theory gap.**

#### 1.3 Lean manufacturing
**Carry over**
- Muda: buffers sized for supplier lead time + small margin, to avoid "tying capital in a giant warehouse full of spares". (A3 p. 3)
- Jidoka: "continuously automatically test the products with machines ... and stop the line if they don't", then fix the problem at the source. (A3 p. 4)
- VA / NNVA / unnecessary waste as green / orange / red node colours. (A3 pp. 4–5, Table 1 p. 7)
- Takt formula $T_{takt} = T_{avail} / D$. (A3 p. 6)

**Gap**
- Sources for the terms (Rother "Learning to See", Toyota Way Fieldbook) and one line on the lean games.

#### 1.4 Industry 4.0 and the digital-physical loop
**Carry over**
- Nothing written as theory. The practice is in A5 script slide 5 (the loop) and A1 p. 5 (configurator → order → parts → robots).

**Gap**
- A short definition from the three Industry 4.0 papers in the course folder, and the week-44 "selected Industry 4.0 topics": no notes from that day are in either repo.

#### 1.5 Robot simulation, offline programming and machine vision
**Carry over**
- A jig move as a 4 × 4 matrix: $p_{now} = T_{move}\, p_{taught}$, with $T_{move}$ = shift (x, y) + turn rz. (VISD p. 1)
- The three vision methods in one paragraph each: ArUco (corners to sub-pixel, ray cut with the marker height, 2D rigid fit), colour segmentation, SIFT + PnP. (VISD pp. 1–2)
- Why calibration error cancels: every jig is measured against the taught-layout photo taken with the same camera. (VISD p. 4)
- A 3-point taught base defines a frame (formulas). (QA "How do we give RoboDK the real position of the jig")
- Own tools vs RoboDK: forward kinematics within 0.005 mm (v7) / 0.05 mm (v3–v6); same first collision. ([OWN_TOOL.md](<../3d-modeling-and-simulation/robot-cell/tests/robot_sim/OWN_TOOL.md>) "Results against RoboDK")

**Gap**
- Manipulability and singularity in two lines (used in A5 slide 6 but not explained in any report).

---

### 2 Method

#### 2.1 Design process overview
**Carry over** (a timeline table is enough)

| When | Step | Source |
|---|---|---|
| Sept | concept, AI sketches, first website, sliding / dovetail interface ideas | A1 pp. 2–4, 8 |
| 15–17 Oct | interface candidates compared; strength checks; jig rules; RoboDK cells; v3 → v4 (split guide) | QA |
| Oct | A2: wedge interface → clip with two hooks; wood plank test; Lean VSM | A2 p. 7; A3 |
| 31 Oct – 2 Nov | v5–v8: jig V2/V3 on T-slot profiles | CT |
| 6–7 Nov | v8 on the real robot (taught plank picks); own simulator replaces RoboDK; guide split V6 proposed | NS §0–0e |
| 9 Nov | IRB presentation | A5 |
| 13–17 Nov | vision method test; V10 follows moved jigs | VISD, VIS |
| 20–22 Nov | real-robot vision session and one-plank test; assembly experiment Part A, B, B2 | CH, V11, PB, PB2 |

- "Because of curiosity and time constraints, we decided to simulate the assembly of our modules in RoboDK. This allowed us to test different assembly sequences". (A2 p. 5)
- IRB lessons: "Design the product and the cell together", "Fail in software first", "Simulation and real robot from one program". (A5 deck slide 8)

**Figures to reuse**
- A1 Fig. 5 (p. 6): Jira board, only if planning is discussed.

**Gap**
- A one-figure overview of the process (concept → architecture → cell → simulation → robot). None exists.

#### 2.2 Product concept and product family
**Carry over**
- Common platform = the seat / backrest planks; the same modules could be walls on planters and trash cans. (A1 p. 3)
- CAD V3 products: bench, bench with no back, chair, chair with no back. (A2 pp. 8–9, Fig. 8–11; STEP files in [benchesV3](<../3d-modeling-and-simulation/bench-cad/benchesV3/>))
- Configurator choices: size (bench / chair = half length), backrest (none / high), mark on the top plank (none / laser-cut / logo shield). (index.html)
- Frame: "one laser-cut flat bar, bent in a press brake"; the backrest arm is "the only variant, the same bar bent further"; "the bent bar is also the leg". (A5 script slide 3)

**Figures to reuse**
- A2 Fig. 8–11 (pp. 8–9): renders of the four V3 products.
- `p_none_laser.jpg`, `p_high_laser.jpg`, `p_high_shield.jpg`, `p_allee.jpg` in deck/media: configurator variants.
- A1 Fig. 6 (p. 8): first configurator. Replace with a current screenshot.

**Update needed**
- A1 family = benches + planters + trash cans (p. 3). The October concept had 6 products, C1/C2/B1/B2/P1/P2 (QA "How does one cobot assemble"). The built family is bench/chair × backrest × mark. Say which one is final and that planters were dropped (or are future scope).
- A1's interface ideas (sliding track, dovetail, p. 3–4) are history: one line.

**Gap**
- R9 asks for at least five variants: count them explicitly (2 sizes × 2 backrest × 3 marks = 12 configurations from the website options, my count).

#### 2.3 Product architecture: customer and engineering views
**Carry over**
- As-is and target customer view: physical variants (length long/short, backrest with/without) and customization (logos or emblems laser-cut/engraved, colours; target adds materials). (A2 Fig. 1 p. 4, Fig. 4 p. 6)
- As-is and target engineering view: function sitting → planks, fasteners, bench frame. (A2 Fig. 2 p. 4, Fig. 5 p. 6)
- "We have 3 modules. 1 bench frame module with 2 variations, 1 plank module with 2 variations and 1 variation of the interface module." (A2 p. 5)
- One critical interface: plank module to bench frame module. (A2 p. 6)
- Redesign action 1, interface: the old wedge was held "only using friction and plastic deformation", problems "lack of reusability and consistency in regards to tolerances"; "two hooks was added to the interface to better lock it in place". (A2 p. 7)
- Redesign action 2: planks laser-cut in wood. They connect tightly to the PLA interfaces, but were cut narrower than the PLA planks, "so there wasn't enough friction to hold them to the frame". (A2 p. 11)
- Interface numbers (not in A2): pocket 25.4 × 5.4 mm for a 25 × 5 mm plank, 0.2 mm per side; chamfers 1.5 mm (pocket) + 1 mm (plank end) give ≈ ±2.7 mm capture. (QA "The planks are rigid")
- Service: spare parts in stock or made in max 3.5 h. (A2 p. 6; A3 Fig. 1 "Print/cut parts, max 3.5 hours")

**Figures to reuse**
- A2 Fig. 1, 2, 4, 5: the PFMP views (redraw: as-is and target engineering views are identical).
- A2 Fig. 6–7 (p. 7), Fig. 16 (p. 10), Fig. 19 and 21 (pp. 13, 15): old and new interface, render and photo. `interface_cad_3d.png` in deck/media.
- A2 Fig. 12–15 (pp. 9–10): frame with and without back, long and short plank with the interface.

**Update needed**
- A2 p. 5 classifies the family as "largely based on an integral architecture". The IRB story and the 3-module list describe a modular one. Decide and argue it (R6: don't repeat A2 unchanged).
- The engineering view lists "Fasteners"; the product has none (A5 slide 3). Replace with the interface clip.
- "Variety is a future scope" (A2 p. 6) is out of date: the configurator and 4 CAD variants exist.
- "Quick manufacturing time of aprox. 18 minutes per bench" (A2 p. 6) is A3's estimated average work incl. rework (17.9 min, A3 p. 7), not a measured time.
- Fix captions: A2 Fig. 3 "Caption", Fig. 6 "Enter Caption", Fig. 9 says "Bench with back" for the no-back render.

**Gap** (R6, R7: all missing from A2)
- Baseline measurements: none. No indicator table (time/flow, complexity, quality, flexibility, automation readiness), no three trials.
- Interface specification: dimensions, tolerances, ownership are only in QA, not verified on parts.
- Before/after results table, trade-offs, next improvement for industrial production.
- Change log (problem, decision, change, effect) and contribution log.
- Result of the wider wood plank test ("Need to test further with a wider tree plank", A2 p. 11).

#### 2.4 DFA2 analysis of the initial design
**Carry over**
- **No DFA2 analysis exists.** What can stand in as the "initial design" evidence:
- Initial cell = v3: one double-sided guide B → A → B, frame 1 + planks flipped into frame 2, guide stays trapped. 239.8 s, 15.7 m TCP path, 120 moves (22 PTP / 98 Line), 9 grips, 8911 deg joint travel. (VER row v3; CT row v3)
- v3 against 8 hard rules: 28 violations (5 part collisions, 18 approach, 1 PTP near parts, 4 clearance < 10 mm). (PB p. 1, Table 1; EXP "Judge re-check")
- Findings from the first simulations: frames go onto the planks, not planks into frames; seat built upside down; tilted quarter turn to avoid the wrist singularity; risers under the nests. (QA "How does one cobot assemble", table "What the simulation changed")
- Hardest step: frame 2 onto six free plank tops; planks in frame 1 alone can lean 2.3°, ≈ 10 mm at the top. (QA "The planks are rigid")
- Trapped guide: after the second insertion the guide is "trapped between frame 1 and frame 2". (QA "Can the plank guide be double-sided", Open)

**Figures to reuse**
- PB Fig. 3 (p. 3): top view of v3 with the TCP path.
- `guide_split.jpg` in deck/media.

**Gap**
- The DFA2 evaluation itself on the initial product design (R5.4). **Biggest gap in the report.** It needs the method from the week-39 lecture and a scored table for the first interface / first bench.
- The A2 baseline bench (wedge interface, A2 Fig. 18–19) is the natural "initial design" for the product side; v3 is the initial design for the process side. Decide which one the DFA2 table scores (open question 2).

#### 2.5 Final design
**Carry over**
- Product: frame V3 (one bent bar), plank 25 × 5 mm section, interface clip with two hooks, no fasteners. (A5 script slide 3; A2 p. 7)
- Guide split: one rigid guide can't release both plank rows, so it is cut in two; each half only touches a plank on sides it can slide away from. (QA "The guide ends up trapped", incl. the inner/outer table)
- Guide split V6: the tooth between the back-rest slots moves from the big half to the small half; the new big half slides 200 mm out without touching a plank (old one blocked after 2.5 mm). (NS §0e)
- Jig history: V1 → V2 (bases turned 180°, 6 mm grid plate) → V3 on T-slot profiles → V5 → V6 proposal. (CT method column; NS)
- Flip: a turn about an axis along plate x, lifted 160 mm, bench held at its outer foot; collision-free. (NS §1)
- Stages of v8/v9: 5 planks rack → frame 1; guide halves; frame 1 + planks turned over into frame 2; halves out; bench to AMR. (NS §4; A5 script slide 7)

**Figures to reuse**
- [guide_split_v6_top.png](<../3d-modeling-and-simulation/jig-cad/Jig V6 proposal/guide_split_v6_top.png>), `jig_v3_3d.jpg`, `sim_planks.jpg`, `sim_guide.jpg`, `sim_flip.jpg`, `sim_guide_out.jpg` (deck/media).
- [bench_layout.png](<../3d-modeling-and-simulation/robot-cell/bench_layout.png>): cell layout.

**Update needed**
- A5 slide 8 lists "Build and test the new guide split (V6)" as next. In simulation v9 already uses it (VER row v9: "guide split V6", 0 part collisions). State whether V6 has been printed.
- NS §1–§5 describe v8 with 1 remaining hit (#120, big half locked). v9 removes it in simulation (VER: v8 2 part collisions, v9 0).

**Gap**
- R5.5: "discuss final result based on learnings from the methodology": a second DFA2 score for the final design, next to the initial one.
- Final BOM and final interface drawing with tolerances.

#### 2.6 Process design and concurrent engineering
**Carry over**
- Flow: configurator order → parts needed → in stock? AMR fetches : laser cut / print → robot cell → assembly with quality checks → final customization → ship. (A1 p. 5)
- IRB flow: order → cut and bend → kit → cobot assembly → mark and check → AMR delivery. (A5 deck slide 4)
- The loop: "simulator page → Python bridge → TMflow Listen node → TM5-900 + Hand-E"; "Same script for the mock and the real robot"; "Change a step on the page, save → the robot program is rebuilt". (A5 script slide 5)
- Concurrent engineering examples: "one plank and straight-down assembly → one jig"; trapped guide, flip clearance, arm through the bench "all found before the lab". (A5 script slide 8)
- Product changed because of the cell: tight fit + chamfers chosen so the robot can place planks; a two-level jig rejected because both frames have the same outline. (QA "The planks are rigid", Decision 2026-10-16)
- Cell changed because of the real robot: as-built offsets, rack −2.1 / −14.8 mm, base B +8.5 / −7.6 mm. (NS §0b)
- AMR: commands over ARCL (TCP, port 7171), drop-off found by a vision base because the AMR stops only to a few cm. (QA "Can the Omron mobile robot be integrated"; AMR)

**Figures to reuse**
- A1 Fig. 4 (p. 5): first flow chart (Miro). A3 Fig. 1 (p. 2) is the later, fuller version: use that one.
- `tmflow_mock.png`, `sim_overview.png`, `dashboard_v8.jpg` (deck/media): the mock TMflow, path + manipulability view, timeline.

**Update needed**
- A2 p. 5 says the simulation was done in RoboDK. From v8 the group's own tool is used (EXP "Geometry": v3–v7 RoboDK, v8+ own IK). Say both.
- AMR delivery is a plan (AMR "Status" column: to write / at the lab), not a result.

**Gap**
- Laser cutting / 3D printing as process steps (R9): no report gives print times, cut settings or the kitting step. A3 only has "max 3.5 h".

#### 2.7 Lean analysis of the production flow
**Carry over**
- Node colours and reasons (A3 pp. 4–5):

| Step | Class | Reason |
|---|---|---|
| Website order / process order | value adding | automated, decides parts early |
| Phone and email orders | necessary waste | take more human resources |
| Buffers | necessary waste | tie up capital, but prevent a stop |
| Loading magazines / jigs | necessary waste | no customer value, needed to produce |
| Assembly, customization | value adding | |
| Quality control, fixing | necessary waste | Jidoka is the way to remove it |
| Packaging (+ its QC) | necessary waste | protects during delivery |
| Transport (mobile robots) | unnecessary waste | no customer value, keep to a minimum |

- Takt: 24 h − 0.5 h setup − 0.5 h stops − 4 × 0.5 h breaks = 20 h/day; 20 × 30.4 × 6 = 3648 h; D = 1000 → 3.648 h/bench ≈ 13 133 s. (A3 p. 6)
- Fault-free cycle 1030 s = transport from buffer 5 min + assembly 5 min + custom job 2 min + QC 5 min + packaging 10 s. (A3 p. 7, Table 1)
- Rework: 1/100 parts repaired (60 min), 5/100 repackaged (2 min) → 11.7 h per 1000 → average 17.9 min/bench; takt / cycle ≈ 12; ≈ 8 % of available time used. (A3 p. 7)
- Buffer: 3 production days = 60 h → 201 benches of material. (A3 p. 7)

**Figures to reuse**
- A3 Fig. 1 (p. 2): flow map with coloured nodes and estimates. Needs a real caption (now "Caption").
- A3 Fig. 2 (p. 6): VSM with time ladder (made with Claude's help, as its caption says).
- A3 Table 1 (p. 7).

**Update needed**
- Assembly was estimated at 5 min = 300 s (A3 p. 7). Simulated v9: 286.7 s at programmed speeds, 319.6 s with ramps (VER row v9). The estimate holds; say it is now backed by simulation, not by the real robot. With 286.7 s the fault-free cycle is ≈ 1017 s (my arithmetic: 1030 − 300 + 286.7).
- Possible improved state: the blind-agent cell at 89.8 s (PB2 p. 1) would cut assembly by ≈ 197 s, but it moves plank loading to the operator (PB2 p. 12).
- "All process times below are estimates, not measured data" (A3 p. 6) still applies to transport, QC, customization and packaging.

**Gap**
- Lean applied to the cell itself: the experiment gives it (redundant plank push removed, −11.9 s, PB iter 9; guide trip removed, −47.5 s, PB iter 25) but nobody has written it as waste removal.
- A future-state map.

#### 2.8 Industry 4.0: vision, data and digital twin
**Carry over**
- Goal: "Before a run, the robot must know where each jig really stands." (VISD p. 1)
- Test design: 10 random layouts (seed 7), jigs moved up to ±30 mm and turned up to ±10°, two camera poses, markers on and off, lab-like disturbances (darker × 0.55, noise + blur, shadow band); 50 tries per case. (VISD p. 2)
- Lab procedure in 8 steps (print markers, calibrate lens and hand-eye, taught-layout photos, 10 mm check, build V10). (VIS p. 8)
- V10 = V9 with every taught point moved with its jig. (VIS p. 5)
- Real robot, 20 Nov: TMflow vision job with External Detection posts the image to the laptop; Techman calibration plate, 13 poses, 0.25 px, hand-eye spread 0.34 mm. (CH)
- Group's conclusion: vision is for **calibrating jig positions**; the exact grip points are still taught by hand. (CH "Discussion")
- Data links verified on the robot: Ethernet Slave 5891 (≈ 100 Hz) and Modbus 502 give joints and flange pose; Listen node 5890 takes scripts. (TMB "Verified on the robot today")
- Configurator → order: "production knows the variant before anything is cut". (A5 script slide 2)

**Figures to reuse**
- VISD Table 1 (p. 2) and Fig. 1 (p. 2, `figures/errors.pdf`): error per method.
- VIS Fig. 9–10 (pp. 4–5, `figures/wt_s6_measured.jpg`, `wt_s8_v9_vs_v10.jpg`): measured jigs, V9 vs V10.
- VIS Fig. 5–6 (pp. 2–3): calibration poses and board.

**Update needed**
- VISD (13 Nov) plans 5 markers incl. the rack; VIS (17 Nov) uses 3 markers and the rack stays where taught. Use the 17 Nov set-up.
- VISD p. 3 calls the TM camera route "not yet tried"; NS §0g says it can't send images. It worked on 20 Nov (CH). Use CH.
- Real landmark size: 50 mm outer frame, not 40 mm (CH).

**Gap**
- Real-robot vision accuracy: only one number exists (a ≈ 10 mm hand move read as 9.1 mm, CH). VIS p. 8 expects real errors "a few times larger" than the simulation.
- Link to the course's Industry 4.0 papers, and what "digital twin" means here (the 3D arm follows the real joints, NS §0).

#### 2.9 Verification and measurements
**Carry over** (how each thing was checked; numbers go in §3.1)
- Own tools: collision check (2 mm sampling), kinematics / reach, cycle time, manipulability. (EXP "Part A"; PB p. 1)
- Part A: one scorer for all versions v3–v10. (EXP; VER)
- Part B / B2 method: sandboxed blind agent, frozen judge (SHA-256 checked), 8 hard rules r1–r8, keep rule (fails a rule?, violations, cycle time, joint travel), written hypothesis per iteration; B2 adds a mandatory reason and Line rotation time. (PB p. 1; PB2 p. 1, Table 1)
- Real robot: teach tool and step tool (`step_run.py`), every run starts with RELEASE, speed 10–20 %. (NS §0, §0b; V11)
- Interface fit: several wedge widths tested until the fit was "fairly stiff while at the same time not too hard" for a collaborative robot. (A2 pp. 10–11)

**Gap**
- A2-style repeated trials (three per indicator) on the physical bench: none recorded.
- Press-fit force or pull-out test of the clip: none (QA pull-out values are estimates, "not tested").

---

### 3 Results and Discussion

#### 3.1 Results
**Carry over** (tables ready to paste)

Assembly versions, own tools, programmed speeds (VER):

| Version | What changed | Cycle [s] | With ramps [s] | TCP path [m] | Part collisions | Grips |
|---|---|---|---|---|---|---|
| v3 | one double-sided guide, guide trapped | 239.8 | 270.9 | 15.7 | 5 | 9 |
| v4 | guide in two halves, parking pad, AMR hand-over | 345.1 | 385.3 | 21.46 | 7 | 12 |
| v8 | Jig V3/V5 on T-slot profiles | 284.6 | 316.4 | 18.17 | 2 | 11 |
| v9 | guide split V6 | 286.7 | 319.6 | 18.68 | 0 | 11 |
| v10 | v9 moved to a camera-found layout | 295.9 | 329.3 | 19.81 | 0 | 11 |

Blind AI experiment (PB p. 1 Table 1; PB2 p. 2 Table 2):

| | v3 start | Part B best (iter 30) | Part B2 best (iter 45) |
|---|---|---|---|
| Cycle, programmed speeds | 239.8 s | 112.9 s (114.9 s with the B2 judge) | 89.8 s |
| Hard-rule violations | 28 | 0 | 0 |
| Joint travel | 8911 deg | 3670 deg | 2285 deg |
| TCP path | 15.7 m | 7.82 m | 3.75 m |
| Moves | 120 | 84 | 62 |
| Iterations kept / run | – | 29 / 30 | 36 / 53 |
| Cost | – | ≈ $41, 106 min | ≈ $67, 172 min |

- Biggest single steps: guide trip to base A dropped, −47.5 s (PB iter 25); planks start in slots in base A, plank jigs gone, −13.2 s (PB2 p. 1).
- Fixed cost left: ≈ 70 s of the 89.8 s is 28 slow 50 mm legs + 7 s gripper waits. (PB2 p. 1)

Vision in simulation (VISD p. 2 Table 1; VIS pp. 1, 5):

| Method | Median [mm] | Worst [mm] | Time per photo |
|---|---|---|---|
| ArUco | 0.14 | 0.5 | 0.2–0.4 s |
| Colour | 0.5–0.9 | 4.3 | ≈ 20 s |
| Features (SIFT) | 0.6–2.6 | 232 | ≈ 6 s |

- Jigs moved (Base A −44/+42 mm, +11°; Base B −29/−1 mm, −2°): found within 0.26 mm; V10 within 0.94 mm (median 0.37) over 117 moves; V9 up to 91 mm off and 5 moves collide. (VIS pp. 4–5)
- Calibration in simulation: reprojection 0.048 px; hand-eye 0.15 mm / 0.08°. (VIS p. 3; VISD p. 5 Table 2)

Real robot (no full cycle):
- Bridge: Line moves of exactly 20 mm and 50 mm; gripper hand-over ≈ 6 s. (TMB)
- Taught plank pick reached to 0.01 mm. (NS §0)
- One-plank test (v11): plank pick → place and both guide halves taught; stopped at the frame flip after a robot fault at 90 % speed. (V11)
- Camera: 0.25 px, hand-eye spread 0.34 mm. (CH)

Lean: takt 3.648 h, average cycle 17.9 min, ≈ 8 % load (A3 p. 7).

**Figures to reuse**
- [part_b2/fig_combined.png](<../3d-modeling-and-simulation/assembly-experiment/report/part_b2/fig_combined.png>) (PB2 Fig. 2): both runs in one curve. `fig_waterfall.png`, `fig_phases.png` in `report/part_b/` and `report/part_b2/`.
- PB2 Fig. 1 (p. 2): top view, start vs best.

**Gap**
- A measured real-robot assembly time (promised at the IRB: "Full cycle on the real robot, with the measured assembly time", A5 script slide 8).
- The A2 before/after table (R7).

#### 3.2 Results against the objectives
- Depends on the objectives list (Introduction gap). Each objective gets one row: target, result, source from 3.1.

#### 3.3 Trade-offs and limitations
**Carry over**
- More function costs time: v3 239.8 s → v4 345.1 s when the guide was split and the bench handed to the AMR. (VER; QA "How long does one assembly take")
- Dropping the guide trip: planks then enter frame 1 "on robot accuracy alone"; "a real process trade-off, not just a faster program". (PB p. 7)
- Planks in base-A slots: shorter robot work, but "moves handling to the person loading the cell". (PB2 p. 12)
- Simulated time only: "programmed speeds, no blending, no controller limits". (PB p. 7)
- The B2 brief steered the agent, so its early design changes "are partly our prompt". (PB2 p. 12)
- Vision limits: ideal simulated camera; only plane moves (x, y, rz); marker height error of 1 mm → up to ≈ 0.4 mm; the rack must not move. (VISD p. 5; VIS p. 8)
- Strength at full scale: a 95 × 28 mm plank over 1400 mm gives 28 MPa and 30 mm deflection (too much); needs a middle support or a 45 mm plank. (QA "Will the bench hold the load", "Can the bench do without the middle support")
- Wood swelling ≈ 2–3 % across the width; snap interfaces loosen outdoors. (QA "Could the plank end flex", "Which plank interfaces are strongest")
- Model vs real cell: Hand-E sits ≈ 2–3° tilted on the flange; real plank guide differs from the model; base A/B swapped and the rack ≈ 28 mm off in −Y. (NS §0; CH)
- Whole bench depends on each frame: a broken frame makes the bench unusable. (A2 p. 5)

**Update needed**
- The QA strength numbers are for the October wooden-plank concept with a 95 × 28 mm plank. Check they still fit the V3 flat-bar frame before quoting them.

#### 3.4 Industrial review board feedback
**Carry over**
- What was presented: 9 slides, website → product → factory flow → simulation; the wow factor was the simulator-to-robot loop. (A5 deck; A5 brief)
- Promised next steps: full cycle on the real robot, build and test guide split V6, two benches stacked on the AMR + docking. (A5 deck slide 8)

**Gap**
- **The board's feedback is not written down anywhere** (script, deck, repo notes, diary). It has to be recalled by the two of you. Without it this subsection is empty.

#### 3.5 Recommendations for industrial production
**Carry over**
- Jidoka instead of end-of-line QC; packaging right first time. (A3 pp. 4–5)
- Conveyor instead of manual / AMR loading of magazines in a real factory. (A3 p. 3)
- Fewer grips and releases is the next gain, not faster moves. (PB2 p. 1)
- Ask whether a phase is needed before tuning it (lesson L25). (PB p. 6)
- Full-scale interface: weld-on standard interfaces on one base frame (platform + late differentiation); stud welding ≈ 0.1 s per weld. (QA "... should the interfaces be welded on")
- Spare capacity: one cell covers 1000 benches in ≈ 8 % of the time, "more orders are needed to use it". (A3 p. 7)
- AMR docking needs a vision base or a mechanical guide. (QA "Can the Omron mobile robot be integrated")

**Gap**
- A2 brief phase 4.6: "Recommend the next improvement for repeated industrial production": pick one and argue it.

#### 3.6 Reflections
**Carry over**
- "We are still behind ... because we started pretty late (only one week before delivering this report)." (A1 p. 6)
- Near misses on the robot: a Direct Move on the Tool tab instead of Base sent the robot down into the rack (E-stop); a wrist swing at 90 % speed faulted the robot. (CH; V11)
- GRIP target must be fully closed (255), else every grip reports "object loss". (NS §0)
- AI use: sketches (A1 Fig. 1), website (A1 Fig. 6), VSM figure (A3 Fig. 2), Part B/B2 reports "written by Claude from the run logs" (PB p. 1). Declare it.

**Gap**
- Keep to a few lines and point to the separate group reflection (Report plan §4 item 3). Reflections on the course and Manulab (R5.7) are not written anywhere.

---

### 4 Conclusion

#### 4.1 Conclusions
- New text, from abstract facts 3, 4, 7, 9, 10, 11. One line per objective.

#### 4.2 Further work
**Carry over**
- Full cycle on the real robot with a measured time; print and test guide split V6; two benches on the AMR and docking. (A5 deck slide 8)
- Real robot: clear the bad taught point, continue from step 33, teach the flip. (V11)
- Apply $T_{move}$ on the real robot and run the 10 mm check. (VIS p. 8 steps 7–8)
- Model the Hand-E mounting tilt as a fixed tool rotation. (NS §0)
- AMR: ARCL script, goals, vision base, handshake. (AMR steps 1–6)
- Judge gap: fixtures overlapping each other are not checked. (PB2 p. 12)
- Trial insertion of planks without the guide; test the base-A plank slots on the real fixture. (PB p. 7; PB2 p. 12)
- Wider wooden plank test. (A2 p. 11)

#### 4.3 Demonstration video
**Carry over**
- Existing material: [v9-full_4x.mp4](<../assignment-5-industrial-review-board-presentation/v9-full_4x.mp4>) (one bench in the simulator, 4× speed), [Video of the Mock TMFLow and Simulation.mp4](<../assignment-5-industrial-review-board-presentation/Video of the Mock TMFLow and Simulation.mp4>), `v8_assembly_sim.mp4` and `v9_full_sim.mp4` in deck/media.
- Narration order is already written: planks → guide on → flip → guide halves out → bench onto the AMR. (A5 script slide 7)

**Gap**
- R5.8 asks for a video of the final product assembly **in Manulab**; R1 asks for a four-minute story. No real-robot footage is listed in the repo. The plan says no new filming, so the report must say the video is simulation + mock.

---

## Module coverage (R12)

| Course module | Theory | Method / Results | Feeds it | Coverage |
|---|---|---|---|---|
| Manufacturing demonstrator concept (A1) | Introduction | 2.2, 2.6 | A1, A5 deck, index.html | good |
| Industry 4.0 technology: Omron cobot, Manulab | 1.4, 1.5 | 2.6, 2.8, 3.1 | TMB, NS, V11, CH, A5 script | good in practice, **no theory text** |
| Selected Industry 4.0 topics (week 44) | 1.4 | 2.8 | nothing in the repo | **thin: no notes** |
| Design for Automatic Assembly (DFA2, Kongsberg case) | 1.2 | 2.4, 2.5 | no A4 report; QA, VER, PB/PB2 as evidence | **thin: method and scoring missing** |
| Lean manufacturing | 1.3 | 2.7, 3.5 | A3 | good; needs sources and the updated assembly time |
| Modular product architectures (Ulrich, Harlou, PFMP) | 1.1 | 2.3 | A2 | **thin: views are minimal, no measurements, classification unclear** |
| Industrial Review Board (A5) | – | 3.4 | A5 deck and script | **thin: feedback not recorded** |

---

## Contradictions between reports

| # | What | Source 1 | Source 2 |
|---|---|---|---|
| 1 | Cobot assembly time | "≈ 6.5 min cobot assembly (sim)" (A5 deck slide 4) | v9 286.7 s = 4.8 min, 319.6 s with ramps (VER); 5 min estimate (A3 p. 7); mock run 468.4 s (run_times.json). No source found for 6.5 min. |
| 2 | "18 minutes" | "manufacturing time of aprox. 18 minutes per bench" (A2 p. 6) | 17.9 min = estimated average work incl. rework (A3 p. 7) |
| 3 | v8 cycle time | 339.0–342.2 s (CT, RoboDK builds 2 Nov) and "about 333 s" (NS §1) | 284.6 s (VER, own tools, 20 Nov) |
| 4 | "Measured" v3 time | CT marks v3 239.8 s as `measure`; Report plan §3 calls it "measured" | It is a programmed-speed path time from simulation (QA), not a robot measurement |
| 5 | Packaging fault rate | 1/500 (A3 Fig. 1 p. 2) | 5/100 (A3 p. 7 text; 95 % pass in Fig. 2 p. 6) |
| 6 | QC time | C/T 20 min (A3 Fig. 2 box, p. 6) | 5 min (A3 Fig. 2 ladder, Table 1 p. 7) |
| 7 | Load jig time | C/T 10 min (A3 Fig. 2 box) | 5 min (A3 Fig. 1; Fig. 2 ladder) |
| 8 | First cycle step | "Transport from buffer 5 min", NNVA (A3 Table 1 p. 7) | "get config and load magazine/jig/fixture 5 min" (A3 Fig. 1); transport is red = unnecessary waste (A3 p. 5) |
| 9 | Architecture type | "largely based on an integral architecture" (A2 p. 5) | 3 modules and one standard interface (A2 p. 5); "modularity of the design" (A1 p. 2) |
| 10 | Fasteners | engineering view lists "Fasteners" (A2 Fig. 2, 5) | "No fasteners" (A5 deck slide 3) |
| 11 | Product family | benches + planters + trash cans (A1 p. 3); 6 products incl. planters (QA) | bench/chair × backrest (A2 pp. 8–9); + mark on the top plank (index.html) |
| 12 | Variety | "Variety is a future scope" (A2 p. 6) | configurator with 3 choices (A5 script slide 2) |
| 13 | Frame material/process | 3D-printed PLA demonstrator (A1 p. 4; A2 p. 11) | "laser-cut flat bar, bent in a press brake" (A5 script slide 3). Both true (demonstrator vs full scale), but say so. |
| 14 | Simulation tool | RoboDK (A2 p. 5; CT) | own tools from v8, "no RoboDK" (EXP; PB p. 1) |
| 15 | Guide | split guide V6 is "next" (A5 deck slide 8); guide needed | v9 already uses V6 in simulation (VER); the blind agent stops using the guide as a placing aid (PB p. 7) |
| 16 | Number of markers | 5 markers, rack found from a second photo (VISD pp. 3–4) | 3 markers, rack has none (VIS p. 1) |
| 17 | Marker size | 22 mm in the simulator (VISD p. 1), 30 mm printed (VISD p. 4) | real TM landmark outline 50 mm (CH) |
| 18 | TM camera | "can't send images to our scripts" (NS §0g) | works through External Detection (CH, 20 Nov) |
| 19 | Base names | start base B, finish base A (NS §4) | real cell: A and B swapped (CH) |
| 20 | Gripper | cell drawn with a Schunk EGP (AMR "Open questions"; NS §4) | lab robot has a Robotiq Hand-E (A5 script slide 5; NS §0) |
| 21 | Assignment numbering | course program p. 1: A2 = Design for Automatic Assembly, A4 = Modular Product Architectures | Canvas briefs and the repo folders: A2 = Product Architecture, A4 = DFA |
| 22 | Customer and price | price matters less (A1 p. 2) | "affordable" (A2 p. 4) |
| 23 | Title page | A1–A3: Dept. of Ocean Operations and Civil Engineering, two authors | `title.tex`: other course, department, one author (Report plan §4 item 6) |

---

## Open questions and assumptions

**Assumptions made for this file**
1. The A2 report is `assignment-2-product-architectures/Deliverable/MMA4002___Assignment_2_Product_Architectures.pdf` (found; the Report plan still says it is missing).
2. There is no group A4 report: the A4 folder holds only the task description. §2.4 is built from QA, VER and PB instead.
3. Chapter 3 has six subsections as in `Sections/3Discussion.tex` (3.1 Results first); the Report plan's outline table still lists five.
4. VER (own tools, 20 Nov) is the table to quote for version times, not CT, because one scorer covers v3–v10.
5. The course readings were not read for this file; Theory "Gap" bullets only name where the material is.
6. Git commit counts include all branches and the two names "bjorgex" and "Bjørge Djuve" are the same person.
7. Page numbers are PDF pages (A2 and A3 print different numbers at the foot).

**Open questions for the two of you**
1. What did the review board say on 9 Nov? (3.4 is empty without it.)
2. DFA2: which design is the "initial" one to score, the A2 baseline bench with the wedge interface or cell v3? Do you have the week-39 lecture slides?
3. Architecture: integral or modular? (contradiction 9)
4. Is the family final as bench/chair × backrest × mark, with planters dropped?
5. Was guide split V6 printed and tried? Was the wider wooden plank tested?
6. Where does "≈ 6.5 min" on IRB slide 4 come from?
7. Are there A2-type measurements (times, part counts, three trials) on the physical bench anywhere outside the repo?
8. Should the blind-agent result (89.8 s) be presented as the final design, or as an experiment next to v9/v10? PB p. 7 says the times are not comparable to v4–v10.
9. Is there any real-robot video to put in the demonstration video?
10. Week 44 "selected Industry 4.0 topics": which topics, and do notes exist?
