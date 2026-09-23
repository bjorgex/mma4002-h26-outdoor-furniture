# Kaia

Front page and 3D configurator for **Kaia** — a modular urban-furniture family of
cast side frames and timber boards. Coursework for **MMA4002 Design for Automated
Manufacturing**, NTNU Ålesund.

One cast side, one machined channel, boards that slide in lengthwise. The 60 × 35
board and the 30 mm cube spacer are the same in every variant, from the 600 mm
chair to the 2400 mm bench.

## What is in here

| File | What it is |
|---|---|
| `index.html` | The whole site. One file — page, configurator and QR code. No build step, no dependencies to install. |

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

## Admin sign-in

The plank-angle sliders and the **2D side editor** are design tools, not
customer controls, so they sit behind a sign-in — user `ntnu`, password
`mma4002`.

The side editor draws the selected side as an elevation (depth across, height
up, 0 = top of the foot) with the seat, back and arm-height guides shared by
every side. Drag a point to move it, double-click a bar to add a point,
right-click or <kbd>Delete</kbd> to remove one, and use the arrow keys to nudge
by 1 mm (<kbd>Shift</kbd> for 10). The point table takes exact values. The 3D
bench rebuilds as you edit. On the traced side every bar is editable; on the
parametric sides the legs are, and you can add extra bars, while the arm, web
and ornaments stay procedural. Edits are kept in that browser only — use
**Copy JSON** to take a profile into `SIDES` in `index.html`, and **Reset side**
to go back to the shipped one.

**This is a convenience gate, not security.** The check runs in the browser, so
anyone who opens the page source can read the password. It keeps the sliders out
of a visitor's way and nothing more. Do not put anything behind it that actually
needs protecting.

## Design notes

- The side elevation on the front page is drawn from the traced profile
  coordinates — the same numbers the Fusion model is built from, not an
  illustration.
- The **foot is not a separate part**. Each side design is cast with the foot
  that belongs to it, so the leg and the foot are one piece of iron.
- Plank stations are spaced by **arc length along the curve**, never along an
  axis, so the gaps stay parallel instead of opening into wedges.
- On a phone the 3D view pins to the top of the screen while the controls scroll
  underneath, so the bench stays visible while it is being changed.
