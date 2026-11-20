# iter 10: shorten the slow plank-place descent from 75 to 50.5 mm

## Hypothesis
Change type: program (+ tool toolbox/shorten_slow.py).
Biggest phase is still planks (117.3 s). Every plank place goes fast down 50.5 mm (to TCP release + 75) and then
slow 75 mm at 20 mm/s (3.75 s). r3 needs only the last 50 mm slow. Change: the fast Line before each plank release
leg ends 24.5 mm lower (release + 50.5), the slow leg becomes 50.5 mm. Per plank: 0.5+3.75 -> 0.75+2.525 s,
-0.98 s; x6 = ~-5.9 s, cycle 217.7 -> ~211.8 s. Risk: r5 (fast Line, carried plank within 10 mm of the guide slot /
plank jig neighbours) or r1; if r5 fires, the plank already enters the guide slot above release + 50.5.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1 (turned over), base B shows frame 2 + pieces, planks still in the jig.
- 02 plank3 upright in the guide over frame 1, gripper just above it; 5 planks left in the jig.
- 03 plank6 placed: two upright in base A, both vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two left in the jig.
- 06 plank2 placed: five upright, one left in the jig; no plank crossing another.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2; six free-standing planks in frame 1, all vertical, same height; arm clear.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between frames; arm over plate edge
  (same as iter 09). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: identical paths to iter 09 (the change is vertical only).

## Result
Expected -5.9 s, violations 0. Got cycle 217.7 -> 211.8 s (-5.9 s), planks phase 117.3 -> 111.4, other phases
unchanged, joints 8844 deg (same), violations 0 at 2 mm (free-move clearance min still 31.8 mm). Kept.
Next: pick lift (60 mm slow -> 50.5, ~-2.3 s), frame release leg (75 -> 50.5, ~-1 s), guide legs.
