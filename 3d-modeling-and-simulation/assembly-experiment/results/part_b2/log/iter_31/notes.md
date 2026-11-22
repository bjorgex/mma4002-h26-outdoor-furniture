# iter 31: slide the frame-approach PTP end Point80h further down its diagonal Line (f ~0.1-0.2)

## Hypothesis
Change type: program. #48 Point80h PTP (J4-limited, 0.78 s) is followed by the fast Line #49 Point80 (77.1 mm,
0.77 s, distance-limited). Point80h is ~120 mm from the frame grip point Point81, so the r4 near-point rule (100 mm)
leaves ~20 mm. Slide Point80h along the Line with toolbox/ptp_along.py (f 0.1 / 0.15 / 0.2 = 7.7 / 11.6 / 15.4 mm):
expected Line -0.08..-0.15 s, the PTP a little longer (+0.0..0.04 s, L58), net ~-0.05..-0.12 s; exact 90.240 ->
~90.13 -> 90.1 s at f 0.2, 0 violations. Risks: r4 box over frame 1 / base A at the lower end, r4 box over plank4
under the PTP start (L29), elbow/link_6 over the placed planks.

## Reason
Evidence: toolbox/move_times2.py on the iter-30 best: #49 Point80 d 77.1 mm, rot 0, 0.77 s - the longest distance-
limited fast Line left; Point80h sits ~120 mm from Point81 (computed from the TCPs in move_times2: dx 38.5, dy -30.7,
dz 109.3), so it is ~20 mm above its r4 near-point floor. Run B's iter 29 stopped at f 0.76 after its r4 problem came
from the PTP START box over plank4 (L29), which iter 30 of B2 since moved further away; the end itself was never
re-derived from the binding constraint (L53). Alternatives: Point85tt / Point88htt / Point70ytt / Point26t are at
measured floors (L54, L56, L58); a base A pocket change (L49) does not fit the ~50 min left.
Principle: shortest route - end fast Lines ~102-105 mm from the nearest event (L30).

## Change
- `./py toolbox/ptp_along.py design/program.json --ptp Point80h --line Point80 --f 0.1/0.15/0.2/0.25`
  (scratch/n31a-d): TCP z 142.5 -> 136.6 / 133.6 / 130.6 / 127.7. scratch/exact27.py: 90.240 -> 90.166 / 90.129 /
  90.102 / 90.075 s.
- 2 mm screens of b, c, d: all 90.1 s but r4 1 "PTP move #48 (Point80h): TCP < 100 mm above Base A".
  scratch/cell_bounds.py: Base A top z 41.2 -> floor 141.2; Point80h was already at 142.5 (L59).
- Fallback: keep z 142.5, move Point80h sideways toward the point above Point80 (toolbox/set_ptp_xyz.py --ref Point80,
  0 / 50 / 75 % of the way, scratch/n31e-g): exact 90.436 / 90.217 / 90.256 s - the J4/J2-limited PTP grows by about
  what the Line saves; best -0.023 s, does not change the rounded 90.2.
- Scored n31c (iterate.py score) for the record. No tool change.

## Screenshots
- 00 start: layout unchanged; planks upright in base A's slots, frame 1 in base A, guide on base B, arm at home.
- 01 plank6 released upright in the far column, gripper above; planks 4/5 still in their slots.
- 02 plank5 released beside plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, gripper above, nothing floating.
- 04 plank3 released in the outer row; planks 1/2 still in base A's slots.
- 05 plank1 released beside plank3, upright.
- 06 plank2 released; all six planks upright in frame 1, gripper above.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical; arm in the usual
  release pose at the -y edge.
- 08 end: bench assembled in base B, arm at home; nothing floating, crooked or interpenetrating.
- topview: same paths as iter 30; the frame-approach PTP end is ~15 mm further down the diagonal, barely visible.

## Result
Expected -0.05..-0.12 s with 0 violations; got 90.1 s (exact 90.102) but r4 1 (TCP < 100 mm above Base A) at every
lowered variant. The reason did not hold: I checked only the near-point distance to the grip (~120 mm, so 20 mm of
slack); the binding limit is the Base A box (top 41.2 + 100 = 141.2), and Point80h was already 1.3 mm above it (L59).
Sideways moves at the same height lengthen the PTP and gain only 0.02 s. Rejected. Point80h is at its floor; a lower
frame approach would need base A lower (a jig change) or an end outside base A's footprint.
