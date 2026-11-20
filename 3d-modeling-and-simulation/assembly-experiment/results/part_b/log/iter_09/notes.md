# iter 09: drop the redundant plank push after every plank release

## Hypothesis
Change type: program (+ a new tool, toolbox/drop_push.py).
Biggest phase is planks (127.2 s). After each of the 6 plank releases the program does a "push home": slow up 35 mm,
close gripper (300 ms), slow down 20 mm onto the plank top (PLANK_PUSH, grip y 125), slow up 20 mm, open (300 ms),
then fast up 90.5 mm. The push TCP (release + 15 mm) equals the plank's top at its home pose (PLANK_PUSH - PLANK_GRIP
= 15 mm), i.e. each plank is already released at its home pose by the gripping insertion, so the push moves nothing.
Change: replace release -> [up 35 slow, DO1, down 20, up 20, DO0, fast up 90.5] by release -> [slow vertical up
50.5 mm, fast up 75 mm to the same transit point]. Gripper ends open as before.
Expected per plank: 1.75+0.3+1.0+1.0+0.3+0.9 = 5.25 s -> 2.53+0.75 = 3.28 s, -1.97 s; x6 = -11.8 s,
cycle 229.6 -> ~217.8 s; planks phase 127.2 -> ~115.4 s. Violations stay 0 (same path, fewer moves; r3 legs 50.5,
r4 PTP still 125 mm above the release point).
Physical note: in the real cell the push guarded against a plank sticking in the guide; in the model (and with the
gripper driving the plank to its home pose) it has no effect. Risk accepted for the demonstrator; can be put back
for a single plank if the cell shows sticking.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1 (turned over); base B shows frame 2 + pieces; planks still in the jig.
- 02 plank3 upright in the guide over frame 1, gripper ~50 mm above its top (no push), others in the jig.
- 03 plank6 placed: two upright in base A, nothing tilted; gripper clear above.
- 04 plank1 placed: three upright in the guide, three left in the jig.
- 05 plank5 placed: four upright; two in the jig; no plank crossing another.
- 06 plank2 placed: five upright; one left in the jig.
- 07 plank4 placed: all six upright in the guide / frame 1, jig empty, gripper above.
- 08 guide back on base B over frame 2; six free-standing planks in frame 1, all vertical and at the same height
  (same as iter 08, so the planks are home without the push); arm clear.
- 09 frame 1 + planks turned over and lowered into base B: planks vertical between the frames, gripper at the foot,
  arm over the plate edge (same pose as iter 08). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: same paths as iter 08; the plank place points just lose their short push detour (vertical only, not
  visible in top view).

## Result
Expected -11.8 s, violations 0. Got cycle 229.6 -> 217.7 s (-11.9 s), joints 8923 -> 8844 deg, 132 -> 120 moves,
violations 0 (r8 0: every plank within 2 mm of its bench place without the push). Phases: planks 127.2 -> 117.3,
guide 64.4 -> 62.4 (the phase split puts the last plank's retreat in the guide phase), others unchanged. Kept.
Next: plank place descent (fast to 75 mm above, then 75 mm slow = 3.75 s each) and pick lift (60 mm slow) - test
whether a 50.5 mm slow leg keeps r5 clearance >= 10 mm in the guide / jig slots.
