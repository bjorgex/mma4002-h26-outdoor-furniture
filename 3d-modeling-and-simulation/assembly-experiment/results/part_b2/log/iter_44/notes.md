# iter 44: move 10 % of the rotation-limited Line #47 (Point70yttt) into the J2-limited PTP #48

## Hypothesis
Change type: program. toolbox/partial_rot.py step 59 f 0.9: Point70yttt keeps its TCP, gets 90 % of its rotation
(29.2 -> ~26.3 deg), so the Line becomes distance-limited (0.584 -> 0.574 s); PTP #48 Point80h stays J2-limited.
Expected -0.01 s (exact 89.95 -> ~89.94, still 89.9 rounded), joints about equal: most likely a tie, "NOT better".

## Reason
Evidence: move_times2 flags #47 as the only ROT-LIMITED Line in the cycle (29.2 deg in 57.4 mm, 0.584 vs 0.574 s);
the next PTP is J2-limited (26.4 deg), so its wrist joints have spare time. Alternatives: every other spare-rotation
slot (start pick legs, frame lift, base-B release) is closed by L37/L45/L49/L50/L66; a jig change that removes a
slow leg does not fit in the ~10 min left of the time budget. Principle: overlap wrist rotation with time already
paid by another joint. This is a last, small cleanup, not a real gain (L65: best sits at 89.9497 exact).

## Screenshots
(Time budget nearly used; only 08 opened. The change is one orientation tweak on a free move, rejected anyway.)
- 08 end: bench assembled in base B, planks upright in frame 2, nothing floating or crooked; arm at home.
- 00-07 and topview not opened.

## Result
Expected ~89.94 s (tie); got 90.0 s, 0 violations, joints 2275: NOT better, rejected. The reason did not hold: f 0.982
screened at 89.947 exact, but at f 0.9 the PTP #48 Point80h start orientation changed J4 by +3.5 deg and J2/J3 by
1.7/2.6 deg, so the PTP got slower than the 0.01 s the Line saved (L38/L58: moving a PTP end changes its limiting
delta). I scored f 0.9 without running exact27 on it (L55/L58 again).
