# iter 33: tighten three remaining PTP/Line end slacks (P16s0tt, Point88htt, Point80h) to cross the 89.95 s rounding step

## Hypothesis
Three small end-point moves, each screened alone at 2 mm, then bundled (L55): (a) start PTP end P16s0tt TCP z 372 -> 370
(Line #3 Point26t is distance-limited, -0.02 s); (b) frame-release lift end Point88htt TCP z 453 -> 451.5 (Line #61
distance-limited, -0.015 s, PTP home changes a little); (c) Point80h slid ~1 mm down its Line (TCP z 142.5 -> ~141.5,
base A box floor 141.2, -0.01 s). Expected exact 89.985 -> ~89.94 s (rounds to 89.9), 0 violations. Change type: program.

## Reason
Evidence: scratch/exact27.py on the iter-32 best gives 89.985 s, 0.035 s above the 89.95 rounding step (L55/L58).
toolbox/move_times2.py shows every movable move at a rule floor, but three with small measured slack: P16s0tt at 372
where L54 found 368 hitting (link_6 / plank4) and 372 clean (nothing between screened); Point88htt at 453 where L56
found 450 hitting (link_3 / guide) and 453 clean; Point80h at TCP 142.5 vs the r4 base A box floor 141.2 (L59).
Why this and not something else: with 48 min of budget left a structural change (fewer slow legs / grips, a different
frame grip for a smaller J5 round trip - L28/L34/L40) cannot be built and verified in one session; the J5 pre-turns
near base B are capped by the elbow (L37/L45/L51), and home is already on the joint path (J5 130 deg total between the
release lift and the first pick, split without loss). These three are the only measured slacks left.
DFA / cell principle: none (shortest motion; no new events). Risk: (a)/(b) sit between a known-clean and a known-hit
value, so screen each at 2 mm alone first.

## Screenshots
- 00 start: frame 1 + pieces in base A, frame 2 under the guide in base B (on its riser), planks upright in the base A edge slots / plank jig; arm at home over the far edge. Same as iter 32.
- 01 plank6 released: plank6 stands in frame 1, the other five upright in their slots; gripper just above, nothing floating.
- 02 plank5 released: two planks in frame 1, upright; arm pose as before.
- 03 plank4 released: three planks in frame 1, all vertical; nothing crooked.
- 04 plank3 released: four planks in frame 1, the last two in their slots.
- 05 plank1 released: five planks, upright, parallel.
- 06 plank2 released: all six planks in frame 1, slots empty; gripper above the last plank.
- 07 frame 1 released: frame 1 + planks upside down through the guide in base B, planks vertical, arm reaching the base B edge from the -y side, nothing in another part.
- 08 end: bench assembled in base B under the guide, base A empty, arm back at home.
- topview: TCP path as in iter 32 (changes are 1-2 mm in z only); the plank zig-zag and frame approach PTP still outside the plank rows.

## Result
Expected ~89.94 s exact, got 89.9 s (exact 89.940), 0 violations, joints 2312 deg (unchanged). Per change (exact27):
(a) P16s0tt -0.020 s (planks phase), (b) Point88htt -0.015 s (home), (c) Point80h -0.009 s (frame phase); each clean
alone at 2 mm and bundled. The reason held: the three slacks were real and inside the clean side of the known floors
(372 -> 370 above the 368 link_6 hit; 453 -> 451.5 above the 450 elbow hit; 141.5 vs base A floor 141.2). Kept. This
was the last cheap slack: everything movable is now within ~1-2 mm of a rule floor; further gains need structural
change (fewer slow legs / grips, a different frame grip for the J5 round trip).
