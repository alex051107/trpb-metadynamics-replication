# Probe sweep live monitor

Periodic diagnostic for the SIGMA_MIN/MAX probe ladder (P1..P4) on Longleaf.

## What it does

Every 2 hours:

1. `rsync` COLVAR and HILLS for each probe from `longleaf:/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/probe_P*/`.
2. Score each probe: max s(R), O/PC/C bin coverage (per Osuna 2019 SI S4), four-way saturation check on the adaptive Gaussian widths (σ_s/σ_z against their MIN and MAX bounds), and a pseudo-FES ΔG between local minima for tick-level convergence monitoring.
3. Rewrite `status.md`, commit only on change, push.
4. If any probe passes the winner gate (`max_s ≥ 7 AND ≥3 non-empty s-bins AND σ_s saturation < 50%`), open a PR titled `Probe sweep winner: <PID>`.

## Run locally

```
python3 routine_check.py
```

Flags:

- `--skip-rsync` — dev only; use already-pulled files.
- `--no-commit` — dev only.
- `--no-pr` — dev only.

## Why MIN and MAX both matter

Adaptive Gaussian widths (PLUMED `ADAPTIVE=GEOM`) only respect `SIGMA_MIN`/`SIGMA_MAX` when they try to cross those bounds. If a bound is never touched, tuning it is pointless. If a bound is touched > 50% of the time, that bound is **binding** — the adaptive scheme wants to go past it but can't, and the bias deposition is no longer adapting to local geometry.

The monitor tracks all four (σ_s MIN, σ_s MAX, σ_z MIN, σ_z MAX) so we catch either floor-clipping (the diagnosis from Job 44008381: σ_s pegged at floor 85% of the time) or ceiling-clipping (would mean the ladder needs to widen, not raise).

## Paper protocol reference

- Osuna 2019 SI S4 — convergence monitored by ΔG between O/PC/C local minima over simulation time.
- Structure selection — cluster representative snapshots from each local energy minimum (= what `routine_check.py`'s coverage bins feed into).
- Well-tempered MetaD defaults from SI S3 — BIASFACTOR=10, HEIGHT=0.628 kJ/mol, PACE=1000 steps, TEMP=350 K, LAMBDA=379.77 (PATHMSD per-atom MSD convention).
