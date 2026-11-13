# Jig vision: which method works best (sim, 10 random layouts, seed 7)

Error = found position of each jig's pivot vs the truth (mm) and its turn (deg). found = jig located / tries. Moves: up to +-30 mm, +-10 deg.

## Clean photos, by camera pose and markers

| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |
|---|---|---|---|---|---|---|---|
| aruco | top, markers on | 40/50 | 0.14 | 0.44 | 0.07 | 0.26 | 404 |
| aruco | side, markers on | 40/50 | 0.34 | 0.49 | 0.21 | 0.37 | 214 |
| colour | top, markers off | 40/50 | 0.49 | 2.93 | 0.05 | 6.50 | 21498 |
| colour | top, markers on | 40/50 | 0.44 | 1.97 | 0.05 | 0.45 | 21144 |
| colour | side, markers off | 40/50 | 0.94 | 4.33 | 0.17 | 2.55 | 18975 |
| colour | side, markers on | 40/50 | 0.89 | 4.10 | 0.15 | 4.55 | 20338 |
| features | top, markers off | 40/50 | 0.64 | 8.51 | 0.12 | 0.90 | 5813 |
| features | top, markers on | 44/50 | 0.67 | 5.50 | 0.11 | 1.56 | 5098 |
| features | side, markers off | 32/50 | 2.62 | 231.83 | 0.42 | 171.92 | 6042 |
| features | side, markers on | 41/50 | 2.35 | 38.49 | 0.24 | 8.67 | 6218 |

## Lab-like disturbances (top pose, markers on)

| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |
|---|---|---|---|---|---|---|---|
| aruco | clean | 40/50 | 0.14 | 0.44 | 0.07 | 0.26 | 404 |
| aruco | dark | 40/50 | 0.14 | 0.44 | 0.07 | 0.26 | 331 |
| aruco | noise | 40/50 | 0.12 | 0.43 | 0.06 | 0.24 | 222 |
| aruco | shadow | 40/50 | 0.13 | 0.45 | 0.08 | 0.26 | 410 |
| colour | clean | 40/50 | 0.44 | 1.97 | 0.05 | 0.45 | 21144 |
| colour | dark | 40/50 | 0.42 | 1.97 | 0.05 | 0.45 | 13800 |
| colour | noise | 40/50 | 0.54 | 1.99 | 0.10 | 0.65 | 16562 |
| colour | shadow | 40/50 | 0.42 | 1.96 | 0.08 | 0.45 | 19691 |
| features | clean | 44/50 | 0.67 | 5.50 | 0.11 | 1.56 | 5098 |
| features | dark | 42/50 | 0.94 | 8.98 | 0.12 | 3.42 | 4474 |
| features | noise | 41/50 | 0.66 | 3.58 | 0.18 | 0.93 | 5512 |
| features | shadow | 47/50 | 0.73 | 5.51 | 0.14 | 1.43 | 3972 |

## Per jig (clean, top, markers on)

| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |
|---|---|---|---|---|---|---|---|
| aruco | Base A | 10/10 | 0.16 | 0.44 | 0.13 | 0.26 | 404 |
| aruco | Base B | 10/10 | 0.15 | 0.23 | 0.07 | 0.15 | 404 |
| aruco | Plank rack | 0/10 | nan | nan | nan | nan | 404 |
| aruco | Guide small | 10/10 | 0.10 | 0.31 | 0.03 | 0.13 | 404 |
| aruco | Guide big | 10/10 | 0.04 | 0.15 | 0.04 | 0.11 | 404 |
| colour | Base A | 10/10 | 1.24 | 1.97 | 0.05 | 0.35 | 21144 |
| colour | Base B | 10/10 | 0.38 | 1.18 | 0.20 | 0.45 | 21144 |
| colour | Plank rack | 0/10 | nan | nan | nan | nan | 21144 |
| colour | Guide small | 10/10 | 0.50 | 0.95 | 0.05 | 0.15 | 21144 |
| colour | Guide big | 10/10 | 0.33 | 0.62 | 0.05 | 0.20 | 21144 |
| features | Base A | 10/10 | 0.39 | 3.15 | 0.15 | 0.79 | 5098 |
| features | Base B | 10/10 | 0.30 | 0.67 | 0.11 | 0.23 | 5098 |
| features | Plank rack | 4/10 | 4.08 | 5.50 | 0.73 | 1.56 | 5098 |
| features | Guide small | 10/10 | 1.05 | 2.58 | 0.12 | 0.72 | 5098 |
| features | Guide big | 10/10 | 0.81 | 1.16 | 0.04 | 0.17 | 5098 |

## Not found: why

| method | jig | reason | times |
|---|---|---|---|
| aruco | Plank rack | marker 3 (22 mm) not detected | 50 |
| colour | Plank rack | grey/unsaturated: colour doesn't separate it | 100 |
| features | Base A | PnP failed (10 matches) | 1 |
| features | Base A | PnP failed (12 matches) | 1 |
| features | Base A | PnP failed (13 matches) | 1 |
| features | Base A | PnP failed (6 matches) | 2 |
| features | Base A | PnP failed (7 matches) | 3 |
| features | Base A | PnP failed (8 matches) | 2 |
| features | Base A | PnP failed (9 matches) | 2 |
| features | Base A | only 5 matched keypoints | 1 |
| features | Guide big | PnP failed (18 matches) | 1 |
| features | Guide big | PnP failed (8 matches) | 1 |
| features | Guide small | PnP failed (11 matches) | 1 |
| features | Guide small | PnP failed (13 matches) | 1 |
| features | Guide small | PnP failed (6 matches) | 4 |
| features | Guide small | PnP failed (7 matches) | 5 |
| features | Guide small | PnP failed (8 matches) | 4 |
| features | Guide small | PnP failed (9 matches) | 4 |
| features | Guide small | only 4 matched keypoints | 1 |
| features | Guide small | only 5 matched keypoints | 6 |
| features | Plank rack | PnP failed (10 matches) | 2 |
| features | Plank rack | PnP failed (6 matches) | 17 |
| features | Plank rack | PnP failed (7 matches) | 6 |
| features | Plank rack | PnP failed (8 matches) | 10 |
| features | Plank rack | PnP failed (9 matches) | 3 |
| features | Plank rack | only 1 matched keypoints | 3 |
| features | Plank rack | only 2 matched keypoints | 8 |
| features | Plank rack | only 3 matched keypoints | 7 |
| features | Plank rack | only 4 matched keypoints | 2 |
| features | Plank rack | only 5 matched keypoints | 19 |
