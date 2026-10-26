# AMR delivery — the TM5-900 sets the bench on the Omron AMR, the AMR delivers it (plan, 2026-10-17)

Goal: the v4 cycle on the real hardware without manual steps: assembly → bench onto the AMR →
AMR drives to "Delivery" and back. The drop-off is found by the TM's wrist camera (a vision base
on the AMR plate), not by trusting where the AMR stops (only a few cm repeatable).
In RoboDK this becomes **v5** (`bench_cell_v5.py`, logged in `cycle_times.csv` like v3/v4).

## Pieces
| Piece | Role | Status |
|---|---|---|
| ARCL on the AMR | plain-text TCP commands (`goto <goal>`), status lines back; port 7171 by default | enable in MobilePlanner at the lab |
| Goals "BenchCell", "Delivery" | AMR stop by the table, and 2 m away | create in MobilePlanner |
| Landmark on the AMR plate | printed TM Landmark at a fixed spot on the plate | make + fix to the plate |
| TMflow vision job | camera finds the landmark → base "AMR plate" | set up at the lab |
| `amr_arcl.py` (laptop) | connect, `status`, `goto`, wait for "Arrived" | to write |
| Handshake TM ↔ laptop | "AMR ready" before the drop-off, "bench placed" after | Modbus 502 or Listen node — test which |
| RoboDK v5 | drop-off targets relative to a frame "AMR plate" (exported as its own base) + a camera view pose | from v4 |

## One bench
1. Laptop: AMR `goto BenchCell`, waits for "Arrived at BenchCell", sets "AMR ready".
2. TM: AssembleBench up to the bench being lifted out of base B (the AMR can drive in meanwhile).
3. TM waits for "AMR ready" → camera view pose above the plate → vision job updates base "AMR plate".
4. TM: bench down relative to "AMR plate", release, back off, home; sets "bench placed".
5. Laptop: AMR `goto Delivery`, waits for "Arrived", then back to "BenchCell" (or its home).

## Steps (each checked before the next)
0. **Lab info** — AMR model (LD-250 in the simulation?), IP (same subnet as the TM, `10.0.12.x`?),
   MobilePlanner access, ARCL password, Fleet Manager or not; TM camera + Landmark in TMflow 1.88.
1. **ARCL, read only** — `amr_arcl.py status` from the laptop: log in, status, list of goals.
   Check: answers come back; nothing moves.
2. **Goals** — "BenchCell" with the AMR ≥ 10 mm off the table (in the simulation its model reaches
   ~360 mm from its centre towards the table), "Delivery" 2 m along the table. Check: 10 stops at
   "BenchCell", measure x / y / angle spread → must fit the camera's field of view.
3. **Vision base** — Landmark on the plate, vision job "Find AMR plate" → base "AMR plate".
   Check: after each of 5 stops the TM goes to a taught point on the plate within ±1 mm.
4. **RoboDK v5** — v4 with the drop-off relative to "AMR plate" and the camera view pose; same
   checks as v4 (collisions, fingertips, end positions), TMflow export, cycle time logged.
   Check: the imported project's base "AMR plate" is the one the vision job updates.
5. **Handshake** — TMflow waits on "AMR ready" before step 3, sets "bench placed" after step 4;
   the laptop sets / reads them (Modbus user register or Listen node).
   Check: dry run with the AMR standing still, flag set by hand.
6. **Full run** — empty gripper first (slow, Manual mode), then with the bench.
7. **Later** — ARCL from TMflow itself (network node) so no laptop is needed, or Fleet Manager jobs.

## Safety
- The TM moves towards the plate only after "Arrived" (interlock), never while the AMR moves.
- The AMR's safety scanner fields near the table may stop it at "BenchCell": tune the goal / fields.
- The bench is lifted by one foot of frame 1: test by hand that the press fit holds first.

## Open questions
- Which AMR exactly, and its plate height (the simulation has the plate level with the ground base)?
- Is ARCL already enabled, do we get the password, is there a Fleet Manager?
- Landmark accuracy with the lab's light; licence for the vision job in TMflow 1.88?
- The lab robot has a Robotiq Hand-E (TM bridge plan), the cell is drawn with a Schunk EGP: which one?
