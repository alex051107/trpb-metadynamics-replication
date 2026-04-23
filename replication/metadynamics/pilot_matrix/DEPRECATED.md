# DEPRECATED 2026-04-23

This directory is superseded by `replication/metadynamics/miguel_2026-04-23/`.

## Why

`pilot_matrix/` was a 2×2 plan (anchor set × SIGMA seed) built on top of
`ADAPTIVE=GEOM` with the assumption that `SIGMA=0.1` is a Gaussian width
in nm. Miguel's email of 2026-04-23 (`../miguel_2026-04-23/miguel_email.md`)
shows the paper uses `ADAPTIVE=DIFF SIGMA=1000` (time window in steps),
so both pilot axes (SIGMA seed and anchor interaction with SIGMA seed)
lose their meaning under the correct scheme. FP-031 covers the pivot;
FP-032 covers the separate λ correction.

The anchor-set axis (1WDW→3CEP vs 1WDW→5DW0) is still a legitimate
scientific question, but it must be re-posed under the Miguel contract,
not inside this 2×2 scaffold.

## What to read instead

- `../miguel_2026-04-23/` — primary launch path, 10-walker production
- `../../validations/failure-patterns.md` FP-031, FP-032 — rationale

## Status of pilot launches

Nothing in this directory was submitted to Longleaf. The `ladder.yaml`,
`plumed_template.dat`, `launch_pilots.py`, and README were scaffolding
only. Safe to ignore; do not launch from here.
