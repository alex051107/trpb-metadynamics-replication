# 03 · Pilot single-walker run (job 45515869)

First completed MetaD run on the corrected (sequence-aligned) path under Miguel's parameter contract. 8 ns, single walker, `start.gro` seeded from the 500 ns Ain cMD terminal frame.

## Files

| File | What it is | When you look at it |
|---|---|---|
| `submit_initial_single.sh` | SLURM submit script used to launch the pilot on UNC Longleaf `volta-gpu`. | To reproduce the pilot. |
| `plumed_single.dat` | PLUMED input for the pilot (single walker, `WALKERS_N=1`, Miguel primary parameters). | Source of truth for what was actually run. |
| `pilot_45515869_stats.txt` | Histogram of `path.s` + summary statistics (min / max / mean / std, fractions at `s < 1.25`, `s ≥ 10`, `s ≥ 12`). | First file to consult for the headline result. |

## Key outcomes

```
min(s) = 1.000  at t = 4920 ps
max(s) = 12.867 at t = 6085 ps   (single transient, ~120 ps wide)
mean(s) ≈ 5.0
plateau 437 – 6085 ps at max(s) ≈ 10.92, sustained 4.3 ns
```

Compared with the baseline (same start.gro, same Miguel params, naive path, 16 ns):
- Baseline `max(s) = 1.896`. Walker trapped at `s < 1.25` for 75.24 % of frames.
- Pilot on corrected path samples `s = 1..12` in half the wall-clock time.

The difference is 100 % attributable to `path.pdb` because nothing else changed.

## Caveats (must not be overclaimed)

- Pilot is **single-walker**. 10-walker production is required for a converged FES (see `06_v2_10walker_crashed/` and `07_v3_pipeline_plan/`).
- `max(s) = 12.87` is a single ~120 ps transient near the `UPPER_WALLS z = 2.5` boundary. It demonstrates that the corrected coordinate system exposes the `s = 12` region, not that a barrier has been crossed cleanly.
- `start.gro` projects to `s = 7.09` because it is near-equidistant to all 15 MODELs; this is a soft-min geometric artifact, not a biological PC-basin assignment. See Technical Manuscript § 4.4.

Raw COLVAR (40 193 rows, 2.3 MB) lives at `chatgpt_pro_consult_45558834/raw_data/pilot_45515869_COLVAR` one level up; not redistributed inside this package because of size.
