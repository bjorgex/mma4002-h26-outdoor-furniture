# iter 21: J5 pre-turn in the slow frame lift (Point81 -> Point80t) to shorten the J5-limited flip

## Hypothesis
Change type: program. The frame flip PTP pair (#54 Pvia 0.48 s, #55 Point85t 2.44 s) is J5-limited: J5 runs
-23.9 (Point80Lt) -> 0 (Pvia) -> 122.1 (Point85t). The slow lift after the frame grip #51 Point81 -> Point80t is
40 mm at 20 mm/s (2.0 s), so it may turn the tool up to 100 deg for free; it turns only 9.9 deg. Turn Point80t,
Point80ut and Point80Lt each about the J5 axis by +D (scratch/turn21.py: orientation of FK(J5 + D), TCP held, IK),
and raise Pvia's J5 by the same D, so the Point85t PTP's J5 delta drops by ~D. Expected -0.2 s (D 10) .. -0.4 s
(D 20), 0 violations. Risk: the frame + planks tilt while still in base A's pocket (r1 vs base A / pieces), the elbow
folds (J3, L48) so Pvia's J3 delta grows (rebalance), or the swung frame clips something on the flip.

## Reason
Evidence: toolbox/move_times2.py on the iter-20 best: Pvia + Point85t = 2.92 s, both J5-limited; Pvia -> Point85t has
J4 72.9 / J1 38.5 / J6 38.6 against J5 122.1, so Pvia's J5 can move up ~45 deg before another joint limits. The
release side (Point86, Point88*) is elbow-capped over the guide (L37, L45), so the J5 saving has to come from the grip
side, and the only slow leg with unused rotation budget there is the 40 mm lift Point81 -> Point80t (90 deg unused).
Iter 20 used up Point80Lt's budget. Alternatives: the plank phase is ~96 % rule-fixed (slow legs + waits; transfers
0.24-0.6 s), the home PTP is on-path (start + end PTP = direct J5 travel), skipping the return home would be gaming.
Principle: overlap motion with an already-paid fixed-cost event (re-orient inside a slow leg, L36).

## Screening (2 mm, --no-shots; scratch/turn21.py D DV [K split], then scratch/set_joints.py rebalances Pvia)
J5 follows only ~0.85 D at fixed TCP and J3 folds ~2 deg per D (L48), so Pvia's J3/J6/J1 were rebalanced each time.
- a D 10, no split, Pvia J3 -50 J6 0: 93.0 s, r1 2 (#51 Point80t: Base A vs plank1/2/4/5/6; #53 Point80Lt: Base A/frame1).
- b D 20, no split, Pvia J3 -57 J6 -2 J1 -23: 92.8 s, r1 2 (same kind, + piece A3).
- c D 20, slow leg split at 20 mm (no turn below): 92.8 s, r1 2 (#53 Point80ut, #54 Point80Lt: Base A/frame1).
- d D 10 split 20: 93.0 s, same 2 hits; e D 15 split 25: 92.9 s, same; f D 5 split 20: same 2 hits.
Scored b (the fastest) to document the dead end.

## Screenshots
- 00 start: unchanged layout; arm at home beyond the far edge, planks 1-3 in base A slots, 4-6 in jig 2, guide on
  base B; nothing floating.
- 01-06 plank releases (6, 5, 4, 3, 1, 2): identical to iter 20 (program unchanged up to the frame grip); planks
  upright in frame 1 on base A, the plank ends reach down into base A.
- 07 frame 1 + planks released: flipped and seated through the guide into frame 2 on base B, planks vertical; arm at
  the usual release pose over the -y edge.
- 08 end: bench assembled in base B, arm at home.
- topview: same paths as iter 20; the flip PTP arc from the frame foot differs slightly (lower via point).
The shots do not show the hits: they are mid-move (the frame tilting during the lift out of base A).

## Result
Expected -0.2..-0.4 s, 0 violations; got 92.8 s (-0.4 s) but r1 2 -> rejected (not legal). The time evidence held
(the J5 saving shows up 1:1 in the flip PTP), the geometry assumption did not: frame 1 + the planks stay engaged in
base A (the plank ends stand in base A's floor slots, the frame in the pocket) for the whole 50 mm slow lift, and the
judge only tolerates the grip-pose contacts for the first two moves after the grip. Any tilt (even D 5) in these
moves makes a new contact, and tilting only above the pocket (Point80Lt) costs as much Line time as it saves (rotation
budget = distance/2). A J5 pre-turn on the grip side needs a shallower base A pocket / plank-end slots (jig_cad), not
a program change.
