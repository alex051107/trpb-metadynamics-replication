# Miguel-authoritative MetaD contract (2026-04-23)

This directory is the **single source of truth** for MetaD production
plumed.dat going forward. It supersedes `../single_walker/plumed.dat`,
`../probe_sweep/`, and `../pilot_matrix/`, all of which were built
against a CV contract that misread the SI's "adaptive Gaussian width
scheme" as `ADAPTIVE=GEOM`.

Authority: email from Miguel (original Osuna 2019 author) received
2026-04-23, reproduced verbatim in `miguel_email.md`.

## What changed vs our prior contract

See `miguel_email.md` § "Points of conflict". Short version:

- UNITS: **LENGTH=A ENERGY=kcal/mol** (not nm/kJ)
- LAMBDA: Miguel's email quotes `LAMBDA=80 Å⁻²` for HIS path. Branduardi's formula (λ ≈ 2.3/⟨MSD_adj⟩) on *our* 15-frame 1WDW→3CEP linear-interpolation path (⟨MSD⟩ ≈ 0.61 Å²) gives **`LAMBDA=3.77 Å⁻²`** (= 379.77 nm⁻², identical to our historical FP-022 value). Miguel's 80 is 21× too sharp *for our path density* (integer-snap / kernel-collapse artifact). This does NOT mean 80 is wrong on Miguel's own path — it likely reflects a denser path built from a construction recipe the SI does not fully specify. Path-construction recipe remains the uncontrolled variable; see FP-032, FP-033, and `lambda_audit_2026-04-23.md`.
- ADAPTIVE: **DIFF** (not GEOM) — SIGMA=1000 is a time window in steps
- 10 walkers mandatory — `WALKERS_DIR=HILLS_DIR WALKERS_N=10`
- UPPER_WALLS on p1.zzz AT=2.5 Å KAPPA=800
- WHOLEMOLECULES ENTITY0=1-39268 (our system atom count)
- NEIGH_STRIDE=100 NEIGH_SIZE=6 on PATHMSD
- PRINT STRIDE=100 FILE=COLVAR FMT=%8.4f

## Files

| File | Purpose |
|---|---|
| `miguel_email.md` | Verbatim email + conflict table + consequences |
| `plumed_template.dat` | 10-walker production template with `__WALKERS_ID__` placeholder |
| `plumed_single.dat` | Miguel's fallback recipe if we can only run a single walker: HEIGHT=0.3 BIASFACTOR=15 |
| `materialize_walkers.py` | Stamps out `walker_00/..walker_09/` subdirs with assertions |

## Usage

```bash
cd replication/metadynamics/miguel_2026-04-23
python3 materialize_walkers.py                # all 10
python3 materialize_walkers.py --only 3       # just walker_03
```

Each `walker_NN/` ends up with its own `plumed.dat` (WALKERS_ID=NN), a
copy of `path_gromacs.pdb`, the `metad.mdp` from single_walker, and a
`provenance.txt`. The shared `HILLS_DIR/` at the top level is where all
10 walkers synchronize via `WALKERS_RSTRIDE=3000`.

## Longleaf launch checklist (gated on SSH return)

1. Rsync this directory to `/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/`.
2. On Longleaf, `conda activate trpb-md`.
3. **Driver self-projection gate (PASSED 2026-04-23 with λ=3.77 Å⁻²):**
   ```bash
   plumed driver --plumed plumed_self.dat --mf_pdb path_driver.pdb
   ```
   with `plumed_self.dat` = `UNITS LENGTH=A` + `PATHMSD REFERENCE=path_driver.pdb LAMBDA=3.77` + `PRINT`. `path_driver.pdb` is `path_gromacs.pdb` with atom serials renumbered 1..112 per MODEL (FP-030: GROMACS full-system indexing is incompatible with driver's 112-atom view). Result: s 1.092 → 14.907 monotonic, z ≈ −0.049 Å² (kernel-average boundary effect, expected small).
   - λ=80 (Miguel's value for HIS path) was rejected **as a transplant onto our path**: integer-snap s + kernel weights ~10⁻²¹ between neighbor frames. This falsifies 80-on-our-path, NOT 80-in-absolute-terms. On his own denser path (⟨MSD⟩~20× smaller than ours), 80 is plausibly the Branduardi-correct value. See `lambda_audit_2026-04-23.md`, FP-032, FP-033. Open question: rebuild Miguel's actual PATH.pdb recipe (`path_construction_ABC_plan.md`, pending).
4. For each walker_NN, build a TPR from `start.gro + metad.mdp` (shared across walkers), submit as 10-way SLURM array on volta-gpu or a100-gpu.
5. Monitor: first HILLS row should appear at ~1 ps of sim time with Gaussian height ≈ 0.15 kcal/mol (check the sigma column — DIFF scheme populates a σ inferred from walker's recent path). First COLVAR should show s seeded around 1 (O-basin).

## Stop conditions

- Self-projection s range not ≈ [1, 15] monotonic → do not launch any walker; email Miguel for path density info.
- First HILLS row σ column shows a zero or inf → DIFF scheme parameterization is off; read walker_NN/HILLS manually to debug.
- After 1 ns sim time, no walker has wandered past s = 2 → normal for DIFF; wait until 5 ns.
- After 10 ns sim time, `max_s < 3` across all walkers → switch to Miguel's fallback config (`plumed_single.dat`: HEIGHT=0.3 BIASFACTOR=15) per his email §3.

## What we are NOT doing here

- Not blindly copying λ from Miguel's email. λ scales as 2.3 / ⟨MSD_adj⟩;
  path density varies between his and our anchor choices. Use the value
  Branduardi's formula gives for OUR path (3.77 Å⁻²), not his number.
- Not scanning SIGMA. DIFF's SIGMA=1000 is a time window, not a Gaussian
  width; scanning it is not in Miguel's recipe.
- Not using ADAPTIVE=GEOM. That whole axis was a misread of the SI.
- Not running single walker as the primary config. Miguel's template
  specifies WALKERS_N=10; single is a fallback.
