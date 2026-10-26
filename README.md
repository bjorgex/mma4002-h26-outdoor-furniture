# Outdoor Furniture

Front page and 3D configurator for a modular outdoor-furniture family: one bent
flat-bar frame, laser-cut and press-brake formed, with timber planks dropped
straight into slotted pockets cut into the bar. Coursework for **MMA4002 Design
for Automated Manufacturing**, NTNU Ålesund.

One frame, two states — with or without the backrest arm — and one choice per
order: the top plank is either laser-cut with a mark or fitted with a separate
logo shield. No cast sides, no separate foot, no assembly fasteners in the
frame itself.

## What is in here

| File | What it is |
|---|---|
| `index.html` | The whole site. One file — page, configurator and QR code. No build step, no dependencies to install. |
| `index_assignment1_old.html` | Archived snapshot of the earlier cast-iron, ten-side-design configurator, kept for reference. |

The page pulls two things from the open web at runtime: **three.js r128** from
cdnjs and **Archivo / IBM Plex Mono** from Google Fonts. Everything else,
including the QR encoder, is inlined.

## Running it

Open `index.html` in a browser. That is the whole procedure.

To serve it locally instead:

```
python3 -m http.server 8000
```

then open `http://localhost:8000`.

## Publishing with GitHub Pages

1. Push this repository to GitHub as a **public** repo.
2. **Settings → Pages → Build and deployment**: source *Deploy from a branch*,
   branch `main`, folder `/ (root)`.
3. Wait about a minute. The site appears at
   `https://<user>.github.io/<repo>/`.

Then open `index.html`, find `var SITE_URL = "";` near the bottom and put that
address in it. The QR code beside the configurator title encodes `SITE_URL` when
it is set, and the address the page happens to be served from when it is not.

## Design notes

- The frame profile on the front page and in the 3D view is traced straight off
  the CAD (`3d-modeling-and-simulation/bench-cad/BenchWOBackrestV2.STEP` and
  `BenchInterfaceV2.STEP`) by slicing the frame solid and reading its outer wire
  and slot pockets — not an illustration, and not rescaled, since these are
  prototype/demonstrator sizes rather than a final production spec.
- The **foot is not a separate part**. The same bent bar that forms the seat
  rail (and, with a backrest, the brace behind it) reaches the ground on its
  own.
- Seat and back planks are single boards dropped into slotted pockets cut
  straight into the bar — no tenons, no spacer cubes.
- On a phone the 3D view pins to the top of the screen while the controls scroll
  underneath, so the bench stays visible while it is being changed.
