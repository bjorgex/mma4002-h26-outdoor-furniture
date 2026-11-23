# Final report plan: MMA4002 Design for Automated Manufacturing

> **Content skeleton (2026-11-23):** what to carry over from the earlier reports, per section, is in [MMA_FinalReport_Skelleton.md](<MMA_FinalReport_Skelleton.md>) (short version; the long one is [MMA_FinalReport_Skelleton (full).md](<MMA_FinalReport_Skelleton (full).md>)).
>
> **Outline shortened 2026-11-23** at Bjørge's request ("shorten down on points") by merging subsections: Introduction 5→3, Theory 5→3, Method 9→6, Results and Discussion 6→4, Conclusion 3→2. The `%` comments were merged with their headings, so every source pointer is kept.
>
> **Lean and Industry 4.0 split 2026-11-23** (Bjørge's decision): Theory 1.3 Lean manufacturing + 1.4 Industry 4.0, Method 2.5 Lean analysis of the production flow + 2.6 Industry 4.0: vision, data and digital twin, Verification moves to 2.7. Theory is now 4 subsections, Method 7.

Status 2026-11-23: skeleton with draft notes. Every `Sections/*.tex` file has the `\subsection` headings. Under each heading
is a `%` comment that says what goes there and which group material feeds it, then a visible `\draftnote{...}`
(Carry over / Reuse / Fix / gap, from the content skeleton) with `\figplaceholder` boxes for the figures. Both
commands are defined at the top of `Sections/0Introduction.tex`; remove them and all notes before hand-in.
§3.1 Results holds four real tables (cell versions, assembly experiment, vision methods, takt against cycle).
No prose has been written yet.
It compiles with `latexmk -pdf -shell-escape main.tex`. `-shell-escape` is needed because `packages.sty` loads
`minted`. Overleaf does this by itself.

Folder layout is unchanged from the Overleaf export (`Final_Report_MMA4002.zip`), so it can be uploaded back as is.
`main.pdf` is a local preview build and doesn't need to go to Overleaf.

## Path shorthands used in the section comments

| Shorthand | Path |
|---|---|
| DAM | `MSc-MechAuto-NTNU/H26/MMA4002-DAM/` (course folder, read only) |
| Course presentation | DAM `1 Lectures & Reading/MMA4002_ Course Presentation 2026.pdf` |
| Course program | DAM `0 Syllabus and setup/Course program Design for Automated Manufacturing 2026.pdf` |
| A1 brief | DAM `3 Assignments/1 Manufacturing Demonstrator Concept/Provided/MMA4002_Assignment_1_2026.pdf` |
| A2 brief | DAM `3 Assignments/2 Product Architecture/Assignment_2_Product_Architecture and DFM_2026.pdf` (copy in group repo `assignment-2-product-architectures/`) |
| A4 brief | DAM `3 Assignments/4 Design for Automatic Assembly/Provided/Assignment 4 brief (Canvas copy).md` (= group repo `assignment-4-design-for-automatic-assembly/assignment-4-task-description.md`) |
| A5 brief | group repo `assignment-5-industrial-review-board-presentation/assignment-5-task-description.md` |
| A1 report | group repo `assignment-1-manufacturing-demonstrator-concept/MMA4002_Manufacturing_Demonstrator_Concept.pdf` |
| A3 report | group repo `assignment-3-lean/MMA4002___Assignment_3_Lean.pdf` |
| A5 deck | group repo `assignment-5-industrial-review-board-presentation/` (`deck/media/`, `.pptx`, script, videos) |
| robot-cell, bench-cad, jig-cad, concept-models, assembly-experiment | under group repo `3d-modeling-and-simulation/` |

## 1. What the final report must contain

No single "final report" brief was found. The requirements below are put together from these sources:

| # | Requirement | Source (file, page) |
|---|---|---|
| R1 | The final delivery is a **portfolio** of four parts: a **technical report** (engineering choices, methods, evidence and result), the **industrial review**, a **demonstration video** (four-minute story of the product and the automated process) and an **individual reflection note** (contribution, learning, perspective). | Course presentation p.15 |
| R2 | "Assessment rewards traceable reasoning, not only a polished final demo." | Course presentation p.15 |
| R3 | Document individual contributions; use the assignments as project evidence. | Course presentation p.13 |
| R4 | Integrate the four platforms: Lean, Industry 4.0, product architecture, DFAA. | Course presentation pp.6-10 (p.10 sums it up) |
| R5 | "For final report, all of the below sections are to be included": 1 Introduction (problem statement/background, product details, objective of the report); 2 Concept design with sketches/3D models (features, main functions); 3 Methodology of the design process, including an explanation of DFA2; 4 DFA2 applied to the initial design; 5 Final design, discussed against what the methodology showed; 6 Process design: how concurrent engineering kept design and manufacturing together; 7 Reflections (own learning, the course, Manulab); 8 Video of the final product assembly in Manulab. | A4 brief (Canvas copy, one page, no page numbers) |
| R6 | Final exam delivery: update the **target Customer View and Engineering View** to match the built and tested demonstrator. Include the final module and interface definitions, verified results and key lessons. Show changes made after testing; don't repeat A2 unchanged. | A2 brief p.4, "Connection to the final exam delivery" |
| R7 | A2 evidence that the final versions should update: at least four indicators before/after (one from each category, three trials where practical), the summary results table, critical interfaces defined and verified, trade-offs, and the next improvement for industrial production. | A2 brief pp.2-4 |
| R8 | Both the product development and the manufacturing development; a "specialisation area" (the wow factor); learning and further development. | A5 brief (Canvas copy) |
| R9 | The A1 content still applies to the final product: customer need, product family (at least five variants or continuous configuration), platform/modules/interfaces, a process map with laser cutting/3D printing, cobot assembly, AMR transport and fixtures/jigs/grippers, plus Lean (at least three waste or risk sources) and Industry 4.0. | A1 brief p.1 |
| R10 | **Deadline 18 Dec 2026.** Hand in four things: the **final report**, the **presentation**, the **video**, and the **final reflection**. **No page limit, but keep it short** (group's choice): one idea per subsection, numbers in tables, detail in appendices. File formats still unknown. | Bjørge, from the week-47 exam guidelines (2026-11-23) |
| R12 | **Every course module and its theory must appear in the report** (Bjørge, 2026-11-23). Modules: (1) manufacturing demonstrator concept (A1); (2) Industry 4.0 technology: Omron cobot, Manulab, plus the selected Industry 4.0 topics in week 44; (3) Design for Automatic Assembly (DFA2, Kongsberg thrust-bearing case); (4) Lean manufacturing (lean games, VSM, Toyota Way / Learning to See); (5) Modular product architectures (Ulrich 1995, Harlou, PFMP views); (6) Industrial Review Board presentation (A5). Each module gets one short theory paragraph (Theory chapter) and is used in at least one Method/Results part, so the coverage is visible without making the report long. | Course program p.1, Bjørge |
| R11 | **The abstract matters most**: it must describe what the project is about, well and compactly (professor's advice). Write it carefully, last, and have it reviewed. | Professor, via Bjørge (2026-11-23) |

## Working rule: reuse, don't rewrite (Bjørge, 2026-11-23)
Before writing any section, read the group's own reports for it (A1, A2 in `assignment-2-product-architectures/`,
A3, A4, A5 deck/script, vision report, assembly-experiment reports, robot-cell notes; table in §3) and carry
over their text, figures, tables and numbers, shortened and updated. New text only where nothing exists yet
or where results changed after testing. Note the source in a `%` comment next to each reused part.

## 2. Outline (as built in `Sections/`)

| File | Heading | Requirements covered |
|---|---|---|
| `Abstract.tex` | (one paragraph, written last) | R1 |
| `0Introduction.tex` (unnumbered) | Background and problem statement · The demonstrator, objective and scope · Team and contributions | R5.1, R3, R9 |
| `1Theory.tex` | 1.1 Modular product architecture and product families · 1.2 Design for automatic assembly (DFA2) · 1.3 Lean manufacturing · 1.4 Industry 4.0 (incl. robot simulation, offline programming and machine vision). One short paragraph per course module. | R4, R5.3, R12 |
| `2Method.tex` | 2.1 Product concept and product family (opens with two lines on the design process) · 2.2 Product architecture: customer and engineering views · 2.3 DFA2: from the initial to the final design · 2.4 Process design and concurrent engineering (the robot cell) · 2.5 Lean analysis of the production flow (VSM, takt) · 2.6 Industry 4.0: vision, data and digital twin · 2.7 Verification and measurements | R5.2-R5.6, R6, R7, R8, R9 |
| `3Discussion.tex` (chapter title "Results and Discussion") | 3.1 Results (tables) · 3.2 Discussion (results against the objectives, trade-offs and limitations) · 3.3 Review board feedback and recommendations for industrial production · 3.4 Reflections (a few lines, points to the group reflection) | R2, R5.7, R7, R8 |
| `4Conclusion.tex` | 4.1 Conclusions and further work · 4.2 Demonstration video | R5.8, R1 (video) |

## 3. Source material per section

| Section | Existing group material |
|---|---|
| Introduction | A1 report sec. 1.1 (customer, value proposition, Mouratidis 2026), sec. 1.5 (demonstrator), sec. 3 (plan, Jira); `index.html`; `bench-cad/`; A5 deck media (`bench_cad_3d.png`, `cell_iso.jpg`); `git log` + `diary/` for the contribution table |
| Theory (1.1–1.4) | Course reading in DAM `1 Lectures & Reading/` (Ulrich 1995, Harlou, Rother "Learning to See", Toyota Way Fieldbook, the three Industry 4.0 papers, product architecture lecture); DFAA lecture (week 39, not in the folder); `robot-cell/vision report/jig_vision_report.tex`; `robot-cell/tests/robot_sim/OWN_TOOL.md` |
| 2.1 Concept/product family (+ design process) | `3d-modeling-and-simulation/qa_notes.md` (dated decision log), `diary/`, git history; A1 report secs. 1.2-1.4; `concept-models/` (`furniture.py`, `assemblies/*.stl`, B1/B2/C1/C2/P1/P2); DAM `3 Assignments/1 .../images/`; `index.html` (backrest none/high × decoration laser/shield); A5 deck `p_*.jpg` |
| 2.2 Architecture views | The group's A2 report: `assignment-2-product-architectures/Deliverable/MMA4002___Assignment_2_Product_Architectures.pdf` (added 2026-11-23); `concept-models/furniture.py`, `interface_options.py`, `interface_candidates.py`, `interface_test/`; qa_notes interface Q&As |
| 2.3 DFA2: initial to final design | Initial: `robot-cell/bench_cell_v3.py`; `robot-cell/cycle_times.csv` (v3 row: 239.8 s; labelled `measure` in the CSV but it is a simulation path time, not a real-robot time); `assembly-experiment/` Part A (`results/versions.csv`, `score_run.py`); qa_notes v3→v4. Final: `bench-cad/BenchInterfaceV2.STEP`, `BenchWOBackrestV2.STEP`; `jig-cad/`; `robot-cell/jig_v5.py`, `guide_split_v6.py`; `cycle_times.csv`; A5 deck media |
| 2.4 Process design | `robot-cell/robot_cell.py`, `bench_cell_v*.py`, `bench_layout.png`, `bench_tmflow/`, `AMR delivery plan.md`, `amr_*.py`, `TM bridge plan.md`; `simulations-html/`; A1 report sec. 2.1 (flow chart, Miro) |
| 2.5 Lean analysis of the production flow | A3 report (VSM, node colouring, takt 3.648 h/bench for D = 1000 / 6 months, 1030 s estimated cycle); Miro VSM; replace the estimates with `cycle_times.csv` |
| 2.6 Industry 4.0: vision, data and digital twin | `robot-cell/vision report/jig_vision_report.pdf` (+ `_detailed`), `tests/vision_lab/` (README, `config_history.md`, `results/`), `Vision and gripper over Modbus plan.md`, `TM bridge plan.md`, `index.html` |
| 2.7 Verification | `cycle_times.csv`, `tests/run_times.json`, `assembly-experiment/report/part_b_report.pdf`, `part_b2_report.pdf` (114.9 → 89.8 s, 53 iterations), `concept-models/interface_test/` |
| 3 Results and Discussion | Results tables: the 2.3–2.7 sources; qa_notes (strength, scale, interface trade-offs); vision report limitations; A5 `IRB presentation script.docx`; `robot-cell/Next steps.md`; A3 report sec. 2 |
| 4 Conclusion / video | `robot-cell/Next steps.md`, `tests/v11_1plank_RESUME.md`; A5 videos (`v9-full_4x.mp4`, `Video of the Mock TMFLow and Simulation.mp4`) |

## 4. Open questions

1. ~~No Results section~~ **Answered 2026-11-23:** chapter 3 is now "Results and Discussion" (same file
   `Sections/3Discussion.tex`, so `main.tex` and the Overleaf structure are unchanged). It opens with a
   "Results" subsection of tables; Method only says how. Old note: The template goes Theory → Method → Discussion → Conclusion. For now, results sit inside
   each Method subsection. A separate `Sections/3Results.tex` would read better, but it needs a new file plus one
   `\import` line in `main.tex`. That's a group decision because it changes the Overleaf structure.
2. ~~Exam guidelines (week 47)~~ **Answered 2026-11-23:** deadline 18 Dec; four deliverables (report,
   presentation, video, reflection); no page limit, keep it short; see R10. The reflection is a **group**
   reflection, not individual (Bjørge, 2026-11-23). Still unknown: file formats.
3. ~~Reflection~~ **Answered 2026-11-23:** the final reflection is a separate **group** deliverable (R10), not
   individual. Proposal: keep the report's §3.4 Reflections to a few lines and point to the reflection document,
   so nothing is written twice.
4. ~~Video~~ **Answered 2026-11-23:** no new filming. The video uses the existing material (simulations, A5 videos); the report says so.
5. **A2 group report** isn't in the repo (only the brief is), and the A4 brief says nothing about page limits. Where
   is the group's A2 report (Overleaf?), and were the PFMP views drawn in Miro?
6. **Template leftovers in `title.tex`:** the course reads "AIS4003 - Fundamentals of Automation and Mechatronics
   Engineering", the department is "ICT and Natural Sciences" (A1/A3 use "Ocean Operations and Civil Engineering"),
   only one author is listed (John Isak Hammer; A1/A3 list Bjørge Skjelbreid Djuve and John Isak Hammer), and the
   date is "1st November 2026". These were left untouched on purpose. Fix them in Overleaf.
7. `references.bib` still holds the template's example entries (Sagan, Ghia, IMT wiki), none of them cited. Swap in
   the course reading and the Mouratidis reference from the A1 report.
8. The appendix import in `main.tex` is commented out. Should the appendix hold the A2-style before/after data,
   TMflow screenshots and the vision report?
