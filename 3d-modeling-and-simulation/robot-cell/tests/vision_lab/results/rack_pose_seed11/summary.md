# Jig vision: which method works best (sim, 5 random layouts, seed 11)

Error = found position of each jig's pivot vs the truth (mm) and its turn (deg). found = jig located / tries. Moves: up to +-30 mm, +-10 deg.

## Clean photos, by camera pose and markers

| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |
|---|---|---|---|---|---|---|---|
| aruco | top, markers on | 20/25 | 0.11 | 0.32 | 0.07 | 0.18 | 531 |

## Lab-like disturbances (top pose, markers on)

| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |
|---|---|---|---|---|---|---|---|
| aruco | clean | 20/25 | 0.11 | 0.32 | 0.07 | 0.18 | 531 |
| aruco | dark | 20/25 | 0.11 | 0.34 | 0.08 | 0.18 | 344 |
| aruco | noise | 20/25 | 0.11 | 0.36 | 0.06 | 0.26 | 248 |
| aruco | shadow | 20/25 | 0.12 | 0.33 | 0.08 | 0.18 | 252 |

## Per jig (clean, top, markers on)

| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |
|---|---|---|---|---|---|---|---|
| aruco | Base A | 5/5 | 0.23 | 0.30 | 0.10 | 0.17 | 531 |
| aruco | Base B | 5/5 | 0.12 | 0.28 | 0.08 | 0.18 | 531 |
| aruco | Plank rack | 0/5 | nan | nan | nan | nan | 531 |
| aruco | Guide small | 5/5 | 0.10 | 0.32 | 0.07 | 0.15 | 531 |
| aruco | Guide big | 5/5 | 0.05 | 0.05 | 0.04 | 0.08 | 531 |

## Not found: why

| method | jig | reason | times |
|---|---|---|---|
| aruco | Guide small | marker 4 (22 mm) not detected | 2 |
| aruco | Plank rack | marker 3 (22 mm) not detected | 21 |
