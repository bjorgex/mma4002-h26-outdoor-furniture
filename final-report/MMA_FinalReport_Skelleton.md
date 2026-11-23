# MMA4002 final report: content skeleton (short)

> Long version with every fact, table and all 23 contradictions: [MMA_FinalReport_Skelleton (full).md](<MMA_FinalReport_Skelleton (full).md>). Outline and requirements R1–R12: [Report plan.md](<Report plan.md>).
>
> **2026-11-23:** Lean and Industry 4.0 are separate sections (Theory 1.3 / 1.4, Method 2.5 / 2.6; Verification is now 2.7). The long version still uses its own, older and longer numbering. The content of this file is also in `Sections/*.tex` as visible draft notes, with the result tables built in 3.1.

- **Deadline: 18 Dec 2026.**
- **Four deliverables:** final report, presentation, video, group reflection (R10).
- **Keep it short:** no page limit, one idea per subsection, numbers in tables, detail in appendices. Reuse the earlier reports, don't rewrite.
- **The abstract matters most** (R11): write it last, from the building blocks below, and have it reviewed.
- **Every course module must appear** (R12): check it against "Module coverage" near the end.

**Source codes** (page = PDF page):

| Code | File |
|---|---|
| A1 | [A1 report](<../assignment-1-manufacturing-demonstrator-concept/MMA4002_Manufacturing_Demonstrator_Concept.pdf>), Sept 2026 |
| A2 | [A2 report](<../assignment-2-product-architectures/Deliverable/MMA4002___Assignment_2_Product_Architectures.pdf>), Oct 2026 |
| A3 | [A3 report](<../assignment-3-lean/MMA4002___Assignment_3_Lean.pdf>), Oct 2026 |
| A5 deck / script | [deck v2](<../assignment-5-industrial-review-board-presentation/MMA4002_IRB_Outdoor_Bench_v2.pptx>), [speaker script](<../assignment-5-industrial-review-board-presentation/IRB presentation script.docx>), 9 Nov 2026 |
| MEDIA | figures and videos in [deck/media](<../assignment-5-industrial-review-board-presentation/deck/media/>) |
| VIS / VISD | [vision picture report](<../3d-modeling-and-simulation/robot-cell/vision report/jig_vision_report.pdf>) (17 Nov), [detailed report](<../3d-modeling-and-simulation/robot-cell/vision report/jig_vision_report_detailed.pdf>) (13 Nov) |
| PB / PB2 | [Part B](<../3d-modeling-and-simulation/assembly-experiment/report/part_b_report.pdf>), [Part B2](<../3d-modeling-and-simulation/assembly-experiment/report/part_b2_report.pdf>), 22 Nov |
| QA / EXP | [qa_notes.md](<../3d-modeling-and-simulation/qa_notes.md>) (dated Q&A, 15–17 Oct), [assembly-experiment README](<../3d-modeling-and-simulation/assembly-experiment/README.md>) |
| CT / VER | [cycle_times.csv](<../3d-modeling-and-simulation/robot-cell/cycle_times.csv>) (RoboDK era, v3–v8), [versions.csv](<../3d-modeling-and-simulation/assembly-experiment/results/versions.csv>) (v3–v10, own tools, 20 Nov) |
| CH / V11 | [vision config_history.md](<../3d-modeling-and-simulation/robot-cell/tests/vision_lab/config_history.md>), [v11_1plank_RESUME.md](<../3d-modeling-and-simulation/robot-cell/tests/v11_1plank_RESUME.md>) (real robot, 20 Nov) |
| NS / TMB / AMR | [robot-cell Next steps.md](<../3d-modeling-and-simulation/robot-cell/Next steps.md>), [TM bridge plan](<../3d-modeling-and-simulation/robot-cell/TM bridge plan.md>), [AMR delivery plan](<../3d-modeling-and-simulation/robot-cell/AMR delivery plan.md>) |

**Which "cycle time" is which:** no full bench cycle has been timed on the real robot. A3 times are estimates; VER and CT times are simulation path times at programmed speeds (no acceleration, no AMR); "with ramps" adds a trapezoid speed profile; a mock run is the TMflow mock running the program.

## Abstract building blocks

- **Product:** an outdoor bench family for public spaces; customers (municipalities, larger companies, institutions) pay for the message the furniture gives. Idea: most people prefer traditional over contemporary architecture (Mouratidis 2026). (A1 p. 2, A2 p. 4)
- **Family:** 3 modules (bench frame 2 variants, plank 2 variants, interface 1 variant); bench or chair, with or without backrest (4 CAD models); the website adds a mark on the top plank. (A2 pp. 5, 8–9; [index.html](../index.html))
- **Design for the robot:** one frame, one plank section (25 × 5 mm on the demonstrator), one interface clip, no fasteners, all parts straight down; 0.2 mm play per side + chamfers lets the robot be ±2.7 mm off. (A5 script slide 3; QA "The planks are rigid")
- **Demonstrator and process:** scale 1:7.5, 3D-printed PLA, laser-cut wood planks tested; web configurator → order → cut and bend / print → kit → cobot assembly (Omron TM5-900 + Robotiq Hand-E) → mark and check → AMR delivery. (A5 deck slides 3–5; A1 pp. 4–5; A2 pp. 10–11)
- **Lean:** takt 3.648 h per bench (1000 benches in 6 months) against ≈ 17.9 min of work per bench (estimates): ≈ 8 % of the available time. (A3 pp. 6–7)
- **One program for simulation and robot:** simulator page → Python bridge → TMflow Listen node → robot. Simulated assembly: first cell v3 239.8 s, current v9 286.7 s with more functions and 0 collisions; a blind AI agent got v3's task down to 89.8 s (−63 %). (A5 script slides 5–6; VER; PB2 p. 1)
- **Vision:** ArUco markers find the jigs to a median of 0.14 mm (worst 0.5 mm) in simulation; with the jigs moved up to 44 mm and turned 11°, program V10 lands within 0.94 mm where the taught V9 misses by up to 91 mm. (VISD p. 1; VIS pp. 1, 4–5)
- **Honest limit:** the full cycle has not run on the real robot. Done on the robot: bridge and gripper, taught plank picks, a one-plank test, camera calibration. (TMB; NS §0; V11; CH)

## Introduction

### Background and problem statement
- **Carry over:**
  - "The product concept chosen is family of 'classy' and non-modernistic outdoor furniture with a focus on benches." The end user sits on it; the customer pays and cares more about the message than the price. (A1 p. 2)
  - "most people questioned preferred traditional architecture over contemporary (Mouratidis 2026)"; hypothesis: the same holds for outdoor furniture. (A1 p. 2, reference p. 7)
  - Manufacturing question to borrow: "How can the demonstrator's product architecture enable simpler, repeatable and scalable manufacturing while preserving required customer functions?" (A2 brief p. 1)
- **Reuse:** A1 Fig. 1 (p. 2), four AI-generated concept sketches; label them as AI-generated.
- **Fix / gap:** A1 says price matters less, A2 p. 4 says "affordable": pick one. No problem statement for the manufacturing side exists yet.

### The demonstrator, objective and scope
- **Carry over:**
  - A full-size bench is too large for Manulab, so the demonstrator is scaled 1:7.5, 3D-printed and/or laser-cut wood. (A1 p. 4; A5 deck slide 3)
  - Cell: Omron TM5-900, Robotiq Hand-E, T-slot plate with base A, base B, plank rack and a two-part guide; the AMR is an Omron LD-250 model in the simulation. (A5 script slide 5; VISD p. 1; NS §0c)
  - Message: "the product is designed for the robot, the cell for the product". (A5 script slide 3)
- **Reuse:** `bench_cad_3d.png`, `cell_iso.jpg` (MEDIA); A2 Fig. 18 and 20 (pp. 12, 14), photos of the printed benches.
- **Fix / gap:** the objectives are not written anywhere as a list. Candidates the sources can answer: family from few modules, assembly by one cobot without fasteners, one program for simulation and robot, capacity against takt, jig positions found by vision. State the scope limits (scaled demonstrator, simulation times, AMR delivery planned but not run) and what was built vs only simulated; A2 p. 15 still says "Final demonstrator: Not yet finished".

### Team and contributions
- **Carry over:**
  - Authors on A1–A3: Bjørge Skjelbreid Djuve, John Isak Hammer (title pages). IRB split: John Isak slides 2–4 and "learned"; Bjørge slides 5–7 and "next". (A5 script)
- **Fix / gap:** a contribution table (R3) has to be written by hand: A2 has none, `diary/` is empty, and git commit counts under-count CAD and lab work.

## 1 Theory

One short paragraph per course module. No earlier report has a theory section; the theory comes from the course reading (not read for this skeleton).

### 1.1 Modular product architecture and product families
- **Carry over:**
  - Integral: "all the parts are dependent on each other"; modular: "some sub modules can be removed or destroyed without breaking the entire system". (A2 p. 5)
  - Platform + late differentiation: one standard platform, a small cheap part changes per customer. (QA "The back socket is in every S1")
  - The PFMP customer view and engineering view are the frame A2 used. (A2 pp. 4, 6)
- **Fix / gap:** definitions from Ulrich 1995, Harlou and the week-42 lecture. The Ulrich text copy is empty (scan), so read the PDF.

### 1.2 Design for automatic assembly (DFA2)
- **Carry over:**
  - Nothing on DFA2 itself. Principles used by name: top-down handling, parts presented in assembly orientation (PB pp. 3, 5); "fewer grips/releases, not better moves" (PB2 p. 1).
  - Fixture rules: 3-2-1 locating, one datum, poka-yoke, lead-ins, access. (QA "What makes a good jig", table)
- **Fix / gap:** the DFA2 method itself (R5.3). The week-39 lecture (Paul Madapilly, Kongsberg thrust-bearing case) is not in the course folder. **Biggest theory gap.**

### 1.3 Lean manufacturing
- **Carry over:**
  - Muda: buffers sized for lead time, not "a giant warehouse full of spares". (A3 p. 3)
  - Jidoka: test automatically, stop the line, fix at the source. (A3 p. 4)
  - Value adding / necessary / unnecessary waste as green / orange / red (A3 pp. 4–5); $T_{takt} = T_{avail} / D$ (A3 p. 6).
- **Fix / gap:** sources for the lean terms (Rother "Learning to See", Toyota Way Fieldbook) and one line on the lean games.

### 1.4 Industry 4.0
Includes robot simulation, offline programming and machine vision.
- **Carry over:**
  - Nothing written as theory; the practice is the simulator-to-robot loop (A5 script slide 5) and configurator → order → parts → robots (A1 p. 5).
  - Vision: a jig move is a 4 × 4 matrix, $p_{now} = T_{move}\, p_{taught}$ (shift x, y + turn rz); calibration error cancels because every jig is measured against the taught-layout photo from the same camera. (VISD pp. 1, 4)
- **Reuse:** the method paragraphs for ArUco, colour segmentation and SIFT + PnP, shortened. (VISD pp. 1–2)
- **Fix / gap:** an Industry 4.0 definition from the three course papers; no notes exist from the week-44 topics; manipulability and singularity need two lines.

## 2 Method

### 2.1 Product concept and product family
- **Carry over:**
  - Design process in two lines: Sept concept and sketches → Oct interface, RoboDK cells, A2, A3 → early Nov jigs on T-slot profiles, v8 on the real robot, own simulator → 9 Nov IRB → 13–22 Nov vision, one-plank test, assembly experiment (A1, QA, CT, NS, VIS, PB). Lessons: "Design the product and the cell together", "Fail in software first", "Simulation and real robot from one program". (A5 deck slide 8)
  - CAD V3 products: bench, bench with no back, chair, chair with no back; the common platform is the planks. (A2 pp. 8–9; A1 p. 3)
  - Configurator choices: size (bench / chair = half length), backrest (none / high), mark on the top plank (none / laser-cut / logo shield). (index.html)
  - Frame: "one laser-cut flat bar, bent in a press brake"; the backrest arm is "the only variant, the same bar bent further". (A5 script slide 3)
- **Reuse:** A2 Fig. 8–11 (pp. 8–9), renders of the four products; `p_none_laser.jpg`, `p_high_laser.jpg`, `p_high_shield.jpg` (MEDIA).
- **Fix / gap:** say which family is final: A1 had benches + planters + trash cans (p. 3), October had 6 products (QA), the built one is bench/chair × backrest × mark. R9 needs at least five variants: count them (2 × 2 × 3 = 12 website configurations, counted for this skeleton).

### 2.2 Product architecture: customer and engineering views
- **Carry over:**
  - "We have 3 modules. 1 bench frame module with 2 variations, 1 plank module with 2 variations and 1 variation of the interface module." One critical interface: plank to bench frame. (A2 pp. 5–6)
  - Redesign: the old wedge was held "only using friction and plastic deformation"; "two hooks was added to the interface to better lock it in place". Wood planks were cut narrower than the PLA ones, "so there wasn't enough friction to hold them to the frame". (A2 pp. 7, 11)
  - Interface numbers: pocket 25.4 × 5.4 mm for a 25 × 5 mm plank (0.2 mm per side); chamfers 1.5 mm + 1 mm give ≈ ±2.7 mm capture. (QA "The planks are rigid")
- **Reuse:** A2 Fig. 1, 2, 4, 5 (pp. 4, 6), the PFMP views, redrawn; A2 Fig. 6–7 (p. 7), old and new interface.
- **Fix / gap:** A2 p. 5 says "largely based on an integral architecture" but lists 3 modules: decide and argue it. The engineering view lists "Fasteners" (the product has none); "Variety is a future scope" (A2 p. 6) is out of date. Missing from A2 (R6, R7): indicator table with three trials, interface specification with tolerances verified on parts, before/after table, change log, result of the wider wood plank test.

### 2.3 DFA2: from the initial to the final design
- **Carry over:**
  - **No DFA2 analysis exists.** Initial cell v3: one double-sided guide that stays trapped; 239.8 s, 15.7 m TCP path, 120 moves, 9 grips; 28 violations of the 8 hard rules. (VER row v3; PB p. 1)
  - Hardest step: frame 2 onto six free plank tops; planks in frame 1 alone can lean 2.3°, ≈ 10 mm at the top. (QA "The planks are rigid")
  - Final product: frame V3 (one bent bar), plank 25 × 5 mm, interface clip with two hooks, no fasteners. (A5 script slide 3; A2 p. 7)
  - Guide split V6: the guide is cut in two; the new big half slides 200 mm out without touching a plank (the old one blocked after 2.5 mm). v9 uses it: 0 part collisions. (NS §0e; VER row v9)
- **Reuse:** PB Fig. 3 (p. 3), top view of v3 with the TCP path; [guide_split_v6_top.png](<../3d-modeling-and-simulation/jig-cad/Jig V6 proposal/guide_split_v6_top.png>).
- **Fix / gap:** the DFA2 scoring of the initial and the final design (R5.4, R5.5). **Biggest gap in the report.** Decide which design is "initial" (the A2 bench with the wedge interface, or cell v3) and state whether V6 has been printed.

### 2.4 Process design and concurrent engineering
- **Carry over:**
  - Flow: order → cut and bend → kit → cobot assembly → mark and check → AMR delivery. Assembly stages: 5 planks rack → frame 1; guide halves; frame 1 + planks turned over into frame 2; halves out; bench to AMR. (A5 deck slide 4; NS §4)
  - The loop: "simulator page → Python bridge → TMflow Listen node → TM5-900 + Hand-E"; "Same script for the mock and the real robot". (A5 script slide 5)
  - Concurrent engineering: "one plank and straight-down assembly → one jig"; trapped guide, flip clearance, arm through the bench "all found before the lab". (A5 script slide 8)
- **Reuse:** A3 Fig. 1 (p. 2), the flow map (fuller than A1 Fig. 4); [bench_layout.png](<../3d-modeling-and-simulation/robot-cell/bench_layout.png>); `tmflow_mock.png` (MEDIA).
- **Fix / gap:** say both tools: RoboDK for v3–v7, own tool from v8 (EXP). AMR delivery is a plan, not a result (AMR). Nothing is written on laser cutting, 3D printing or kitting as process steps (R9); A3 only has "max 3.5 h".

### 2.5 Lean analysis of the production flow
- **Carry over:**
  - Takt: 20 h/day × 30.4 × 6 = 3648 h; D = 1000 → 3.648 h/bench ≈ 13 133 s. (A3 p. 6)
  - Fault-free cycle 1030 s = transport 5 min + assembly 5 min + custom job 2 min + QC 5 min + packaging 10 s; with rework 17.9 min/bench on average, ≈ 8 % of the available time. (A3 p. 7)
- **Reuse:** A3 Fig. 2 (p. 6) VSM and Table 1 (p. 7).
- **Fix / gap:** the 5 min assembly estimate is now backed by simulation (v9 286.7 s, 319.6 s with ramps), not by the real robot; the other A3 times are still estimates. Lean on the cell itself is not written (push removed −11.9 s, guide trip removed −47.5 s, PB); no future-state map.

### 2.6 Industry 4.0: vision, data and digital twin
- **Carry over:**
  - Vision: "Before a run, the robot must know where each jig really stands." V10 = V9 with every taught point moved with its jig. Vision calibrates jig positions; grip points are still taught by hand. (VISD p. 1; VIS p. 5; CH)
  - Real robot, 20 Nov: TMflow vision job with External Detection; 13 poses, 0.25 px, hand-eye spread 0.34 mm. Data links: Ethernet Slave 5891 (≈ 100 Hz), Modbus 502, Listen node 5890. (CH; TMB)
- **Reuse:** VIS Fig. 9–10 (pp. 4–5), measured jigs and V9 vs V10.
- **Fix / gap:** use the 17 Nov set-up (3 markers), CH for the TM camera, landmark 50 mm. Real-robot vision accuracy has one number (a ≈ 10 mm move read as 9.1 mm, CH). Link to the course's Industry 4.0 papers, and say what "digital twin" means here.

### 2.7 Verification and measurements
- **Carry over:**
  - Own tools: collision check (2 mm sampling), kinematics / reach, cycle time, manipulability; one scorer for all versions v3–v10. (EXP; VER)
  - Part B / B2: sandboxed blind agent, frozen judge (SHA-256 checked), 8 hard rules, a written hypothesis per iteration. (PB p. 1; PB2 p. 1)
  - Real robot: teach tool and step tool (`step_run.py`), every run starts with RELEASE, speed 10–20 %. (NS §0, §0b; V11)
- **Fix / gap:** no repeated trials (three per indicator) on the physical bench; no press-fit or pull-out test of the clip (QA values are estimates).

## 3 Results and Discussion

### 3.1 Results
- **Carry over** (ready-made tables are in the full version):
  - Versions, programmed speeds / with ramps, part collisions (VER): v3 239.8 / 270.9 s, 5; v4 345.1 / 385.3 s, 7; v8 284.6 / 316.4 s, 2; v9 286.7 / 319.6 s, 0; v10 295.9 / 329.3 s, 0.
  - Blind AI experiment: v3 239.8 s, 28 violations → Part B 112.9 s (114.9 s with the B2 judge), 0 → Part B2 89.8 s, 0; joint travel 8911 → 3670 → 2285 deg; iterations kept 29 / 30 and 36 / 53. (PB p. 1; PB2 p. 2)
  - Vision in simulation: ArUco median 0.14 mm, worst 0.5 mm; colour 0.5–0.9 mm, worst 4.3 mm; SIFT 0.6–2.6 mm, worst 232 mm. Jigs moved: V10 within 0.94 mm over 117 moves, V9 up to 91 mm off and 5 moves collide. (VISD p. 2; VIS pp. 4–5)
  - Real robot, no full cycle: bridge Line moves of exactly 20 mm and 50 mm; taught plank pick reached to 0.01 mm; the one-plank test stopped at the frame flip after a robot fault at 90 % speed; camera 0.25 px, 0.34 mm. (TMB; NS §0; V11; CH)
- **Reuse:** [fig_combined.png](<../3d-modeling-and-simulation/assembly-experiment/report/part_b2/fig_combined.png>) (PB2 Fig. 2), both runs in one curve; VISD Table 1 (p. 2).
- **Fix / gap:** a measured real-robot assembly time (promised at the IRB, A5 script slide 8) and the A2 before/after table (R7) are missing.

### 3.2 Discussion
- **Carry over:**
  - More function costs time: v3 239.8 s → v4 345.1 s when the guide was split and the bench handed to the AMR. (VER)
  - Blind-agent trade-offs: without the guide trip the planks enter frame 1 "on robot accuracy alone"; planks in base-A slots "moves handling to the person loading the cell". (PB p. 7; PB2 p. 12)
  - Limits: simulated times at "programmed speeds, no blending, no controller limits" (PB p. 7); vision in an ideal simulated camera, plane moves only (VISD p. 5; VIS p. 8); real cell differs from the model: Hand-E ≈ 2–3° tilted, base A/B swapped, rack ≈ 28 mm off (NS §0; CH).
  - Full scale: a 95 × 28 mm plank over 1400 mm gives 28 MPa and 30 mm deflection; needs a middle support or a 45 mm plank. (QA "Will the bench hold the load")
- **Fix / gap:** needs the objectives list from the Introduction (one row per objective: target, result, source). The QA strength numbers are for the October wooden-plank concept: check them against the V3 frame before quoting.

### 3.3 Review board feedback and recommendations for industrial production
- **Carry over:**
  - Presented: 9 slides, website → product → factory flow → simulation; the wow factor was the simulator-to-robot loop. Promised: full cycle on the real robot, guide split V6, two benches stacked on the AMR + docking. (A5 deck; promises on slide 8)
  - Recommendations: jidoka instead of end-of-line QC and a conveyor instead of manual / AMR loading of magazines (A3 pp. 3–5); fewer grips and releases is the next gain, not faster moves (PB2 p. 1).
  - One cell covers 1000 benches in ≈ 8 % of the time: "more orders are needed to use it". (A3 p. 7)
- **Fix / gap:** **the board's feedback is not written down anywhere**; it has to be recalled. Pick one "next improvement for repeated industrial production" and argue it (A2 brief phase 4.6).

### 3.4 Reflections
- **Carry over:**
  - "We are still behind ... because we started pretty late". (A1 p. 6)
  - Near misses: a Direct Move on the Tool tab instead of Base sent the robot down into the rack (E-stop); a wrist swing at 90 % speed faulted the robot. (CH; V11)
  - AI use to declare: sketches (A1 Fig. 1), website (A1 Fig. 6), VSM figure (A3 Fig. 2), Part B/B2 reports "written by Claude from the run logs" (PB p. 1).
- **Fix / gap:** keep it to a few lines and point to the separate group reflection. Nothing is written on the course and Manulab (R5.7).

## 4 Conclusion

### 4.1 Conclusions and further work
- **Carry over:**
  - Conclusions are new text: one line per objective, numbers from the abstract building blocks.
  - Further work: full cycle on the real robot with a measured time; print and test guide split V6; two benches on the AMR and docking. (A5 deck slide 8)
  - Real robot: clear the bad taught point, continue from step 33, teach the flip (V11); apply $T_{move}$ and run the 10 mm check (VIS p. 8); wider wooden plank test (A2 p. 11).

### 4.2 Demonstration video
- **Carry over:**
  - Existing material: [v9-full_4x.mp4](<../assignment-5-industrial-review-board-presentation/v9-full_4x.mp4>), [Video of the Mock TMFLow and Simulation.mp4](<../assignment-5-industrial-review-board-presentation/Video of the Mock TMFLow and Simulation.mp4>), `v8_assembly_sim.mp4`, `v9_full_sim.mp4` (MEDIA). Narration order is written: planks → guide on → flip → guide halves out → bench onto the AMR. (A5 script slide 7)
- **Fix / gap:** R5.8 asks for a video of the assembly in Manulab and R1 for a four-minute story; there is no real-robot footage and no new filming is planned, so the report must say the video is simulation + mock.

## Module coverage (R12)

| Course module | Theory | Method / Results | Coverage |
|---|---|---|---|
| Manufacturing demonstrator concept (A1) | Introduction | 2.1, 2.4 | good |
| Industry 4.0 technology: Omron cobot, Manulab | 1.4 | 2.4, 2.6, 2.7, 3.1 | good in practice, **no theory text** |
| Selected Industry 4.0 topics (week 44) | 1.4 | 2.6 | **thin: no notes** |
| Design for Automatic Assembly (DFA2, Kongsberg case) | 1.2 | 2.3 | **thin: method and scoring missing** |
| Lean manufacturing | 1.3 | 2.5, 3.1, 3.3 | good; needs sources and the updated assembly time |
| Modular product architectures (Ulrich, Harlou, PFMP) | 1.1 | 2.2 | **thin: views minimal, no measurements, classification unclear** |
| Industrial Review Board (A5) | – | 3.3 | **thin: feedback not recorded** |

## Contradictions that affect quoted numbers

The full list of 23 is in the long version; numbers in brackets are its row numbers.

| What | Source 1 | Source 2 |
|---|---|---|
| Cobot assembly time (1) | "≈ 6.5 min cobot assembly (sim)" (A5 deck slide 4); no source found | v9 286.7 s, 319.6 s with ramps (VER); 5 min estimate (A3 p. 7); mock run 468.4 s |
| "18 minutes" (2) | "manufacturing time of aprox. 18 minutes per bench" (A2 p. 6) | 17.9 min = estimated average work incl. rework (A3 p. 7) |
| v8 cycle time (3) | 339.0–342.2 s (CT, RoboDK) and "about 333 s" (NS §1) | 284.6 s (VER, own tools) |
| "Measured" v3 time (4) | CT marks 239.8 s as `measure` | it is a simulation path time at programmed speeds (QA) |
| Packaging fault rate (5) | 1/500 (A3 Fig. 1 p. 2) | 5/100 (A3 p. 7 text; Fig. 2 p. 6) |
| QC time (6) | 20 min (A3 Fig. 2 box, p. 6) | 5 min (A3 Fig. 2 ladder, Table 1 p. 7) |
| Load jig time (7) | 10 min (A3 Fig. 2 box) | 5 min (A3 Fig. 1; Fig. 2 ladder) |
| Markers (16, 17) | 5 markers, 22 mm in the simulator, 30 mm printed (VISD) | 3 markers (VIS p. 1); real TM landmark 50 mm (CH) |

## Open questions

1. What did the review board say on 9 Nov? (3.3 is empty without it.)
2. DFA2: which design is the "initial" one to score, the A2 bench with the wedge interface or cell v3? Do you have the week-39 lecture slides?
3. Architecture: integral or modular?
4. Should the blind-agent result (89.8 s) be presented as the final design, or as an experiment next to v9/v10? PB p. 7 says the times are not comparable to v4–v10.
5. Are there A2-type measurements (times, part counts, three trials) on the physical bench anywhere outside the repo?
6. Was guide split V6 printed and tried, and was the wider wooden plank tested?
