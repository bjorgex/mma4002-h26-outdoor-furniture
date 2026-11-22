# iter 23: hide more of the home-trip J5 turn in the last lift Line Point88ht (and slow leg Point88t)

## Hypothesis
Change type: program. Turn Point88ht (the 59.5 mm fast lift after the frame release, TCP z 398 -> 458) by J5 -D
(scratch/j5turn20.py), optionally also Point88t (slow 20.5 mm leg, rot 10.2 of a 51 deg budget), then put home back
on the joint path Point88ht -> P16s0t (home_on_path f 0.85). Expected: home PTP J5 110 -> ~94-98 deg, -0.2..-0.35 s
(92.5 -> ~92.2 s), 0 violations. Risk: elbow (link_3) vs the guide on base B (L37/L45), r5 clearance.

## Reason
Evidence: toolbox/move_times2.py on the iter-22 best: #62 home PTP 2.20 s, J5-limited (110 deg; J4 85 next), while
the Line before it, #61 Point88ht (59.5 mm, 0.59 s), turns only 15.4 of the 29.7 deg its distance pays for. A probe
(j5turn20 on Point88ht, D -10/-15/-20) lowers J5 by 9-19 deg while J3 stays at -62.4 (no elbow fold): unlike L37/L45
(J5 turn at the low release pose), at TCP z 458 the elbow is already folded up and does not drop. Alternatives: a
shallower base A pocket so the frame lift can turn (jig_cad, ~0.4 s but uncertain, iter 21), a structural change
(two-plank grips) too large for the ~80 min left. This one is program-only and uses existing tools.
Principle: overlap wrist travel with move time that is paid anyway.

## Screening (2 mm, --no-shots unless noted)
- Point88ht J5 -15 / -20 (+ home_on_path f 0.85): 92.3 / 92.2 s programmed, r1 3 / 4: Guide/link_3 at #61/#62 and
  link_6/plank4 at #1/#2 (home 10-13 mm lower) - L51 (J1/J2 change drops the elbow even with J3 constant).
- + Point88t J5 -15 too: J5 home 94 deg, same elbow problem (not screened further).
- Point88ht moved 20-30 mm inward (TCP z kept 458), J5 -20, home f 0.8: 92.2 s, r1 4 (Guide/link_3/4/5) - worse.
- elbow-filtered orientations (scratch/probe08c.py, idx 75, 30 deg): best J5 113-117 needs 21-29 deg more tool turn,
  the Line becomes rot-limited: 92.5 / 92.6 s, no gain.
- Side tries on the frame approach: ptp_along Point80h f 0.15 / 0.2: 92.4 s but r4 "TCP < 100 mm above Base A"
  (base A top 41.2, Point80h TCP 142.5 = 1.3 mm slack); Point80h moved toward the grip at the same z or out of base A's
  footprint (y > 190): the J2-limited PTP gets slower by what the Line saves (0.0 / +0.1 s); Point70y lowered 40/65 mm:
  the PTP turns J4-limited (+0.1 s). The frame approach is balanced (J2 = J4 = ~37 deg).
- Scored the hypothesis variant (D -15) to record it.

## Screenshots
- 00 start: layout unchanged; arm at home (slightly lower than iter 22), planks 1-3 in base A, 4-6 in jig 2, guide on
  base B; nothing floating.
- 01 plank6 released upright in frame 1's far column; gripper vertical above it.
- 02 plank5 released next to it; plank4 alone in jig 2.
- 03 plank4 released; far column full, jig 2 empty.
- 04 plank3 released in the y-124 row (outer end), upright.
- 05 plank1 released next to plank3, upright.
- 06 plank2 released; all six planks upright in frame 1, base A slots empty.
- 07 frame 1 + planks flipped into frame 2 through the guide on base B; arm at the release pose over the -y edge,
  elbow low over base B (the turned lift that follows hits the guide with link_3, as the score says).
- 08 end: bench assembled in base B, arm at home; nothing out of place.
- topview: same paths as iter 22.

## Result
Expected -0.2..-0.35 s, 0 violations; got 92.3 s programmed but r1 3 (Guide/link_3 at #61/#62, link_6/plank4 at #1).
The reason did not hold: J3 stayed constant in the IK, but J1/J2 shift and still drop the elbow onto the guide (L51);
the elbow-safe orientations need more tool rotation than the Line can pay for. Rejected. The release side of the home
J5 trip is now exhausted (iter 08, 17, 23), and the frame approach is balanced; the next gains need a jig change
(shallower base A so the frame lift can turn, L49) or a structural change (fewer slow legs).
