# λ audit 2026-04-23 — why we keep 3.77 Å⁻² instead of Miguel's 80

## Context

Miguel Iglesias-Fernández's 2026-04-23 email quotes:

> `p1: PATHMSD REFERENCE=... LAMBDA=80 NEIGH_STRIDE=100 NEIGH_SIZE=6`

under `UNITS LENGTH=A ENERGY=kcal/mol`. Read literally, this is `LAMBDA=80 Å⁻²`, which in nm convention is `LAMBDA = 80 × (10 Å / nm)² = 8000 nm⁻²`. Our long-standing value is `LAMBDA=379.77 nm⁻²` (= 3.77 Å⁻²) — a 21× difference AFTER unit conversion is accounted for. The question: is the difference alignment, units, or path density?

## Why PATHMSD `LAMBDA` matters

PLUMED's `PATHMSD` computes `s(R)` and `z(R)` as

```
s(R) = Σ i·exp(-λ·MSDᵢ(R)) / Σ exp(-λ·MSDᵢ(R))
z(R) = -1/λ · ln [ Σ exp(-λ·MSDᵢ(R)) ]
```

Branduardi's heuristic: λ ≈ 2.3 / ⟨MSDᵢ,ᵢ₊₁⟩ (2.3 ≈ ln 10 gives neighbor weight ~10⁻¹, which makes `s` smooth). Here ⟨MSDᵢ,ᵢ₊₁⟩ is the **per-atom, mass-weighted, Kabsch-aligned** mean squared displacement between adjacent reference frames.

## Three candidate explanations considered

1. **Unit mismatch.** Switching from nm⁻² to Å⁻² is a 100× factor (1 Å⁻² = 100 nm⁻²). This alone converts our 379.77 nm⁻² → 3.7977 Å⁻², not 80. So units explain a 100× factor — they do not explain Miguel's 80.

2. **Alignment convention (user's hypothesis).** Hypothesis: Miguel runs PATHMSD without alignment; we Kabsch-align when we compute MSD, so our MSD is smaller, so our λ is larger. **REJECTED** (verified by Codex independent read of PLUMED 2.9 `PathMSD.cpp`): `PATHMSD` itself does optimal Kabsch alignment at every step for every reference frame internally. Miguel does not hand-align; PLUMED aligns for him. Both pipelines therefore see the same aligned MSD per frame pair. Alignment is not the axis.

3. **Path density (the actual axis.) ** Miguel's path is built from ~15 frames across a tighter geometric range than ours. His ⟨MSDᵢ,ᵢ₊₁⟩ ≈ 2.3/80 ≈ 0.029 Å². Ours is 0.61 Å² (per-atom MSD from `generate_path_cv.py` on 15-frame 1WDW→3CEP linear interpolation, 112 Cα). Ratio ≈ 21× = exactly the residual ratio between 80 and 3.77.

   Said differently: adjacent Cα RMSD is ~0.17 Å on Miguel's path, ~0.78 Å on ours. Both are legitimate path densities; λ simply scales inversely with MSD to preserve neighbor weight ~0.1.

## Falsification evidence

Self-projection of the 15 reference frames through PATHMSD under each candidate λ (UNITS=A, driver mode, 2026-04-23 Longleaf):

| λ (Å⁻²) | s range | z range | Interpretation |
|---|---|---|---|
| 80 (Miguel's) | 1.000, 2.000, ... 15.000 (integer-snapped, clipped to nearest frame) | effectively 0 | Over-sharp: exp(-80·0.61) ≈ 10⁻²¹; each frame projects purely onto itself, `s` is a step function of frame index, not continuous. Useless as a CV gradient. |
| 3.77 (ours) | 1.092 → 14.907 monotonic | ≈ −0.049 Å² | Kernel-smooth; endpoints pulled slightly inward by the soft-min average (expected boundary effect). Matches historical FP-022 result expressed in the other unit convention (379.77 nm⁻²). |

Integer-snap under λ=80 is not a passing result; it's a symptom of neighbor weight collapse. The CV would be zero-gradient almost everywhere and plateau-jumping at frame boundaries.

## Consequences for the Miguel contract

Everything else in Miguel's email is adopted verbatim (UNITS, ADAPTIVE=DIFF, SIGMA=1000 steps, HEIGHT=0.15, BIASFACTOR=10, PACE=1000, WALKERS_N=10, UPPER_WALLS AT=2.5 KAPPA=800, WHOLEMOLECULES ENTITY0=1-39268). Only `LAMBDA=80` is replaced with `LAMBDA=3.77`, and the replacement is documented on Miguel's own framework (Branduardi's formula + path density).

This is not a rejection of Miguel's MetaD contract; it's the path-density-specific instantiation of it. A future 1WDW→5DW0 anchor build will need its own λ audit (do not reuse 3.77).

## Logged failure patterns

- FP-022 corrigendum (2026-04-23): original 379.77 nm⁻² was correct; FP-027 re-opening was the error.
- FP-032: λ transferability across path densities. Miguel's 80 is correct for HIS path, not transferable.

## Files

- `plumed_template.dat` / `plumed_single.dat` — LAMBDA=3.77 hardcoded.
- `materialize_walkers.py` — LAMBDA_LITERAL assertion = "LAMBDA=3.77".
- `provenance.txt` per walker — records LAMBDA=3.77, rationale, equiv nm value, Miguel's 80 as non-transferable reference.
