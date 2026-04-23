# 2×2 pilot matrix (anchor set × initial SIGMA seed)

ChatGPT Pro's 2026-04-22 reframing: the separable variables still on the
table after the probe sweep closed (P1–P5 all stalled ≤ 1.64) are

| axis | options | rationale |
|---|---|---|
| anchor set | {1WDW→3CEP (current), 1WDW→5DW0} | linear interpolation is weakest at the O-end chord; 5DW0 (chain A) is the literature PC intermediate and projects to s ≈ 1.07 on the current path — stronger near-O anchor. |
| initial SIGMA seed | {0.1 (probe sweep), 0.3} | probe sweep only scanned SIGMA_MIN/SIGMA_MAX; the **initial** SIGMA for the very first Gaussian was never tuned. ADAPTIVE=GEOM will rescale but the first few hundred ps seed the entire bias surface. |

Pilots are run 3 ns first → gate → winner extends to 10 ns. The probe
sweep contract in `../probe_sweep/` stays locked at SIGMA=0.1 (SI-strict);
this directory is explicitly the SIGMA-seed unlock axis.

| Pilot | Anchor set | SIGMA seed | Status |
|---|---|---|---|
| Pilot 1 | 1WDW→3CEP (current) | 0.1 | ≡ probe_P1 at 5 ns, CLOSED max_s=1.64 |
| Pilot 2 | 1WDW→3CEP (current) | 0.3 | TO LAUNCH — same `path_gromacs.pdb`, new plumed_template |
| Pilot 3 | 1WDW→5DW0 | 0.1 | requires 5DW0 anchor build + self-projection gate + λ re-derivation |
| Pilot 4 | 1WDW→5DW0 | 0.3 | same as Pilot 3 + SIGMA seed change |

## Decision logic (Pro's 3 ns gate)

- Any pilot with `max_s > 3.0` at 3 ns → extend that pilot to 10 ns, that's the winner.
- All four stall ≤ 1.64 → the path-CV + ADAPTIVE=GEOM machinery is exhausted on this system; escalate to either piecewise-path (different CV topology) or biasing-framework change (WT-MetaD → OPES, or add anchor-adjacent CV).
- Mixed escape → prefer anchor-set change over SIGMA seed (chemistry > hyperparameter).

## Files

- `ladder.yaml` — pilot manifest (same schema as probe_sweep/ but with sigma_seed field).
- `plumed_template.dat` — parameterized `__SIGMA_SEED__` + same PATHMSD + λ=379.77 + ADAPTIVE=GEOM.
- `launch_pilots.py` — materialize pilots with assertions; defers to probe_sweep paths for Pilot 1/2, new path for 3/4.
- `README.md` — this file.

## λ for 1WDW→5DW0

λ = 379.77 nm⁻² is FP-022-settled for the *current* 1WDW→3CEP anchor set. A
new anchor set changes the RMSD matrix between adjacent frames, so λ must
be re-derived from the new path (closest-frame RMSD average). The value
does not transfer; the procedure is in
`replication/parameters/JACS2019_MetaDynamics_Parameters.md` §2.

## Caveats

- This directory is not SI-strict. The JACS 2019 paper gives no guidance
  on initial SIGMA seed; 0.3 is an operational choice motivated by the
  probe-sweep evidence that 0.1 never broadened enough to escape O-basin.
- 5DW0 chain A has different ligand (PLS, Aex1) than 1WDW (Ain). Cα
  backbone is substantially similar in the COMM domain (~0.8 Å RMSD), so
  the path geometry is mostly a chord-change, not a chemistry-change.
