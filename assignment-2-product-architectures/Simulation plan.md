# Simulation plan: cobot cell + mobile robot for the furniture demonstrator

**Goal:** a RoboDK simulation that shows the automated process for the modular furniture:
the mobile robot brings a kit, the TM cobot assembles it in a jig, the mobile robot takes the
finished product away. All of it built from our own 3D models, so the robot program is
written against the simulation first and only re-taught (frames) on the real cell.

Target: ready for the Manulab demonstrator work in weeks 43–45 and the Industrial Review Board
presentation (Assignment 5, week 46).

## 1. Tools (installed 2026-10-16)

| Tool | Status | Used for |
|---|---|---|
| RoboDK 6.1.1 (`C:\RoboDK`) | installed, 30-day trial | cell, simulation, export to TM program |
| Omron TM models (`C:\RoboDK\Library\Omron-TM`) | TM5-700/900, TM12, TM14, TM5S–TM30S | the cobot |
| Omron LD-250 (RoboDK library) | available | the mobile robot (LD-60/90: use LD-250 model, same footprint class) |
| Techman post-processors | installed | RoboDK → TMflow program |
| `robodk` Python API (root `requirements.txt`) | installed | build the station from a script, repeatable |
| build123d (already in use) | installed | jigs, kit tray, gripper fingers, same style as `furniture.py` |
| TMflow / MobilePlanner | lab PCs | final program on the real robots |

**Licence:** trial runs out ~2026-11-15, and after that program export is capped at 50
instructions. Ask Manulab for a classroom seat before then.

## 2. Inputs needed from the group

- [ ] **Demonstrator models** (pushed to this folder): which products are shown, and at what scale.
- [ ] **TM model** in Manulab (TM5-900? TM12?) → sets reach and payload.
- [ ] **Mobile robot model** (LD-60 / LD-90 / LD-250) and whether a cart or a top module is used.
- [ ] **Gripper**: Robotiq 2F-85 or Schunk Co-act EGP (both in `OAT_2.TM_TR070. Gripper Guide.pptx`).

**Scale check (why it matters):** full-size W1 = 1500 mm, but a TM5-900 reaches 900 mm.
At scale $1{:}s$:

| Scale | W1 | W2 | plank $W \times T$ | pitch $P$ | fits 2F-85 (85 mm)? |
|---|---|---|---|---|---|
| 1:3 | 500 | 170 | 31.7 × 9.3 | 35 | yes |
| 1:4 | 375 | 127.5 | 23.8 × 7 | 26.3 | yes |
| 1:5 | 300 | 102 | 19 × 5.6 | 21 | yes, thin for a snap hook |

Default if nothing else is said: **1:3** with the TM5-900. A bench (B1) then fits in a
$\approx 500 \times 170$ mm jig, well inside reach.

## 3. Process to simulate (one station + mobile robot)

```
Laser / 3D print  →  Kitting (manual)  →  LD: kit tray to cobot cell  →  TM: assembly in jig
        →  TM: quality check (vision/force)  →  LD: finished product to outbound  →  next order
```

Cobot sequence per product (same operations for every variant, only counts and positions change):

1. Pick S1 / S2 side frame from the kit tray → place in the frame jig (variant-dependent spacing).
2. B1/B2 only: place the S3 stretcher between the frames.
3. Pick planks one by one → place at pitch $P$ → press down with a force node until the
   interface snaps (interface 14 snap hook).
4. Check: count/position (vision) or press-force threshold → OK / NOK bit to the line.
5. Signal the mobile robot (Modbus/I/O) that the product is ready.

## 4. Jigs and fixtures to design (build123d → STL → RoboDK)

| ID | Part | Design rule |
|---|---|---|
| J1 | **Frame assembly jig** | one base plate for all products; locator pockets for S1/S2 at both spacings (chair 510, bench 1500, scaled); poka-yoke: a frame fits only the right way round |
| J2 | **Kit tray** on the mobile robot | one tray, pockets for frames, stretcher and planks; same pick positions for every variant, empty pockets for parts a product doesn't need |
| J3 | **Gripper fingers** | one finger pair for planks, frames and stretcher (no tool change → zero changeover) |
| J4 | **Docking / tray locator** in the cell | fixes the tray to ±1 mm when the mobile robot docks, so the cobot targets hold |

Every target is taught **relative to the J1 / J4 frames**, so on the real cell only those
two frames are re-taught.

## 5. Build steps (scripted, one file each, in `AI Output/Cell simulation/`)

| Step | File | Checkpoint |
|---|---|---|
| 1 | `scale_parts.py` | demonstrator parts exported at the chosen scale, sizes printed |
| 2 | `jigs.py` | J1–J4 as STL; parts drop into the jig in the viewer |
| 3 | `station.py` | cell: table, TM, jig, docking spot, LD-250, parts; saves `furniture_cell.rdk` |
| 4 | `programs.py` | one program per product (B1, B2, C1, C2) + mobile-robot moves; reach/collision check |
| 5 | run + record | simulation video, cycle-time table per variant |
| 6 | export | TM programs via the Techman post → test load in TMflow |

## 6. Results for the presentation

- `furniture_cell.rdk` station + a video of B1 and C2 being built back to back (mixed model, no changeover).
- Cycle time per variant $\to$ compare with takt time (feeds the Lean / VSM part).
- The jig/tray drawings as evidence for DFAA: one jig, one gripper, one kit tray for all variants.

## 7. Open questions / risks

| Risk | Effect | Mitigation |
|---|---|---|
| snap force too high for the cobot | plank doesn't seat | check press force in the force node; fall back to a softer interface (7) at small scale |
| thin printed planks at 1:4–1:5 | snap hooks break | use 1:3, or laser-cut plywood planks |
| mobile robot docking error ±10–20 mm | cobot misses the tray | J4 mechanical locator, or a TM vision landmark on the tray |
| RoboDK trial ends | can't export | Manulab classroom seat |
