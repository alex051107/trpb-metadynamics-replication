# DEPRECATED 2026-04-23

This entire directory is superseded by
`replication/metadynamics/miguel_2026-04-23/`.

## Why

`probe_sweep/ladder.yaml` and its five probe runs (P1–P5) were designed to
scan `SIGMA_MIN` / `SIGMA_MAX` under `ADAPTIVE=GEOM`. Miguel's email of
2026-04-23 (see `../miguel_2026-04-23/miguel_email.md`) confirms that the
Osuna 2019 protocol uses `ADAPTIVE=DIFF` with `SIGMA=1000` (a time window
in integrator steps, not a Gaussian width). FP-031 logs the root cause.

Consequence: P1–P5 results do NOT bear on the paper's MetaD recipe. The
σ floor/ceiling saturation observed is a GEOM-specific artifact, not a
DIFF-scheme failure mode. No evidence from this directory survives the
pivot.

## What to read instead

- `../miguel_2026-04-23/miguel_email.md` — authoritative contract
- `../miguel_2026-04-23/plumed_template.dat` — 10-walker production
- `../miguel_2026-04-23/plumed_single.dat` — single-walker fallback
- `../../validations/failure-patterns.md` FP-031, FP-032 — rationale

## Archive status

Raw COLVAR / HILLS / slurm outputs are kept here for forensics only
(so the saturation pattern can be re-examined when we write up the
failure mode). Do not re-use `plumed_template.dat` or `ladder.yaml`
from this directory for any new launch.
