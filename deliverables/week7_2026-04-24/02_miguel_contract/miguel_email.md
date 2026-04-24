# Email from Miguel (original author of Osuna 2019 MetaD paper) — 2026-04-23

Received by Zhenpeng Liu. Reproduced verbatim below. This is the
authoritative source for our MetaD protocol going forward; any conflict
between this email and our earlier interpretation of the SI must be
resolved in favor of the email.

---

> Thank you for your interest in our metadynamics protocol.
>
> 1. During the metadynamics run, the path is aligned by default to the
>    protein to estimate s(R) and the MSD z(R). However, previous manual
>    alignment is convenient.
>
> 2. This is an example of a plumed input file for a walker:
>
> ```
> UNITS LENGTH=A ENERGY=kcal/mol
>
> RESTART
>
> WHOLEMOLECULES ENTITY0=1-5978
>
> p1: PATHMSD REFERENCE=PATH.pdb LAMBDA=80 NEIGH_STRIDE=100 NEIGH_SIZE=6
>
> METAD ARG=p1.sss,p1.zzz ADAPTIVE=DIFF SIGMA=1000 HEIGHT=0.15 PACE=1000
>       BIASFACTOR=10.0 TEMP=350.0
>       GRID_MIN=0.5,0.0 GRID_MAX=15.5,2.8 GRID_BIN=300,100
>       WALKERS_DIR=HILLS_DIR WALKERS_RSTRIDE=3000 WALKERS_ID=0 WALKERS_N=10
>
> UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800 LABEL=uwall
>
> PRINT ARG=* STRIDE=100 FILE=COLVAR FMT=%8.4f
> ```
>
> If you can't shake the COMM domain with a single run, I suggest
> increasing the hill height to 0.3, and the bias factor to 15.
>
> I hope this works for you,
>
> Miguel

---

## Points of conflict with our pre-email interpretation

| dimension | our reading of SI | Miguel's email (authoritative) |
|---|---|---|
| UNITS | GROMACS default (nm + kJ/mol) | **LENGTH=A ENERGY=kcal/mol** |
| LAMBDA | 379.77 nm⁻² (FP-022 derivation, per-atom MSD in nm²) | **80** (in Å⁻², i.e. per-atom MSD ≈ 0.029 Å² between adjacent frames) |
| ADAPTIVE | GEOM (we read "adaptive Gaussian width scheme" as the geometry-based Branduardi 2012 option) | **DIFF** (time-window / local-diffusion scheme) |
| SIGMA | 0.1 (Gaussian width in nm, scalar) | **1000** (in DIFF mode this is a number of steps: 1000 × 2 fs = 2 ps local time window) |
| Walkers | single walker | **WALKERS_N=10** with `WALKERS_DIR=HILLS_DIR` |
| Upper wall | none | **UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800** |
| Pre-alignment | none | `WHOLEMOLECULES ENTITY0=1-N` every step |
| PATHMSD optimization | default (all 15 ref frames searched every step) | `NEIGH_STRIDE=100 NEIGH_SIZE=6` |
| Fallback for stuck single run | unknown — we've been scanning σ | **raise HEIGHT to 0.3 and BIASFACTOR to 15** |
| COLVAR stride | 500 | **100 with FMT=%8.4f** |
| GRID | none declared | **s in [0.5, 15.5] with 300 bins; z in [0.0, 2.8] with 100 bins** |

## Consequences for work already done

1. **probe_sweep is invalidated as evidence about the paper's protocol.**
   P1–P5 scanned SIGMA_MIN/SIGMA_MAX under `ADAPTIVE=GEOM`. The paper
   uses `ADAPTIVE=DIFF` with `SIGMA=1000` (time window). The σ saturation
   signals we measured are consequences of GEOM's Jacobian-based reshape,
   not the DIFF scheme, and therefore do not speak to whether the paper's
   MetaD can reach s > 3 on our system.

2. **pilot_matrix (the 2×2 plan) is invalidated as designed.** Pilots 2
   and 4 tuned `sigma_seed` (initial Gaussian SIGMA), which has different
   semantics in DIFF. The anchor-set axis (Pilots 3/4, 1WDW→5DW0) is
   still a legitimate question but must be re-run on the DIFF contract.

3. **FP-022 (λ=379.77 nm⁻²) is unit-specific, not wrong.** Our derivation
   was internally consistent under the nm convention with per-atom MSD,
   but the paper operates in Å and used λ=80 directly. The two numbers
   represent different operating points (Miguel's path has adjacent-frame
   RMSD ~0.17 Å; our reference path has adjacent-frame RMSD ~0.78 Å), so
   `80 Å⁻²` does not equal `379.77 nm⁻²` via unit conversion (that
   conversion gives 8000 nm⁻²). Whether the λ number transfers depends
   on how closely our 15-frame linear interpolation matches the paper's
   path density, which we can only verify by a self-projection test.

4. **FP-029 (GEOM vs DIFF semantics) corrigendum.** The core claim (do
   not conflate GEOM and DIFF) still stands. What we got wrong inside
   the FP was the direction: we assumed the SI's "adaptive Gaussian
   width scheme" meant GEOM; it actually means DIFF. The FP now serves
   as a warning about which direction the conflation went.

5. **Every run we have to date (500 ns cMD aside) used the wrong CV
   contract.** Specifically: Job 41514529 (50 ns walltime), probe_P1–P5
   (5–30 ns each), pilot_matrix (not yet launched). All future MetaD on
   this system should use the Miguel contract.

## New plumed.dat for our system

See `plumed_template.dat` (multi-walker, WALKERS_N=10, WALKERS_ID=__WID__)
and `plumed_single.dat` (single-walker, HEIGHT=0.3 BIASFACTOR=15 per
Miguel's fallback recipe). Our system has 39268 atoms so
`WHOLEMOLECULES ENTITY0=1-39268`.

## Outstanding decisions still needing Miguel or PM input

- Does "previous manual alignment" (email §1) mean Kabsch-aligning the
  trajectory before passing it to PATHMSD, or aligning the reference
  path pdb to a canonical orientation? We assume the latter (path is
  pre-aligned to MODEL 1, PLUMED handles per-frame alignment internally
  via RMSD.cpp).
- Miguel's system has 5978 atoms (WHOLEMOLECULES ENTITY0=1-5978). That
  is roughly 1/7 of our 39268-atom system (different solvent buffer /
  ion count / maybe multimer stoichiometry). No action required beyond
  substituting our atom count, but this divergence is worth flagging if
  the 10-walker run behaves anomalously.
- Does Miguel's path have 15 frames like ours, or more? If his
  adjacent-frame RMSD is ~4× smaller than ours, his path is likely
  ~60 frames or built from a denser reaction-coordinate scan. We should
  ask in a follow-up if the self-projection gate fails.
