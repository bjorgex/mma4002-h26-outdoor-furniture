# iter 43: small J5 pre-turn at the flip end Point85tt, sized by a measured link_3/4-to-guide distance

## Hypothesis
Change type: program. j5turn20 idx 69 D -1.5 on Point85tt (J5 122.1 -> ~120.7). The PTP gets ~1.5 deg shorter
(~-0.03 s), Point86 takes the turn in its spare rotation budget. Expected cycle 89.9 s (exact ~89.92, a tie) with
joint travel -1..-3 deg -> "better" on the tie-break; 0 violations if link_3/4 keeps > 0 mm to the guide.

## Reason
Evidence: L67 asked for a probe before a third attempt; the new scratch/elbow43.py (min distance link_3/link_4 vs
Guide per sample) shows the closest point of the flip is the END of PTP #56 Point85tt, not the Point86 descent:
best 5.3 mm there, D -4 (p41a) and D -6.5 (n42a) 0.0 mm. So the clearance falls ~1.3+ mm per deg of turn and the
xy shifts of iter 42 could not help. A turn of ~1.5 deg should keep ~3 mm. Alternatives: raising Point85tt to buy
clearance costs ~0.01 s/mm (iter 42), more than the turn gains; a guide CAD change does not fit in the time budget
left. Principle: overlap wrist rotation with Line time that is already paid.

## Screening
- scratch/elbow43.py: D -1.5 -> min 2.6 mm at the end of #56 / start of #57 (best 5.3, D -4 0.0, D -6.5 0.0).
- exact27: 89.924 s (best 89.950), rounds to 89.9 (tie).

## Screenshots
(Only 07, 08 opened; time budget nearly used. The change is one 1.5 deg orientation tweak, rejected anyway.)
- 07 frame 1 + planks released into frame 2 through the guide on base B, planks upright; arm at the low release pose
  at base B's -y edge, forearm beside (not in) the guide.
- 08 end: bench assembled in base B, arm back at home; nothing floating or crooked.
- 00-06 and topview not opened.

## Result
Expected 89.9 s with joints -1..-3 deg; got 89.9 s, 0 violations, joints 2278 (+3 vs 2275): NOT better. The reason held
for the geometry (the probe was right: the closest point is the PTP end, and D -1.5 stays clear at 2.6 mm) and for the
time (-0.026 s exact), but the joint-travel guess was wrong: the turned end adds J1/J2/J3/J6 changes (L48) that outweigh
the 1.3 deg of J5. Rejected. The base-B J5 turn is now measured closed: ~1.3 mm of elbow clearance per deg of turn,
5.3 mm available, < 0.1 s possible.
