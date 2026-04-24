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

2. **Alignment convention — split into two sub-axes (PM correction 2026-04-23).** "Alignment" conflates two different operations; only one is settled.

   - **2a. Runtime alignment (settled, not the axis).** When PLUMED computes `s(R), z(R)` at each MD step, `PATHMSD` does optimal Kabsch alignment of the current frame against each reference frame internally (Belfast tutorial: path CV distance is MSD *after* optimal alignment; `PROPERTYMAP` / `RMSD TYPE=OPTIMAL` share this implementation; `PATHMSD` inherits from `PROPERTYMAP`). Manual pre-rotation of the trajectory does not change the runtime MSD metric. Both pipelines see the same aligned MSD per frame pair at runtime.
   - **2b. Path-construction alignment (UNSETTLED — the actual open question).** How the 15 reference frames themselves were built is *not* specified by the SI ("15 conformations, linear interpolation between the X-ray available data"). Choices that change the reference frames — and therefore change ⟨MSDᵢ,ᵢ₊₁⟩ and therefore change the Branduardi λ — include: (i) whether endpoints were Kabsch-aligned before linear interpolation, (ii) on which atom subset the endpoint alignment was performed (112 Cα vs full protein vs domain-restricted), (iii) whether intermediate crystals (5DVZ, 5DW0, 5DW3, 4HPX) were interposed vs pure two-point interpolation, (iv) chain and residue subset. If Miguel's actual 2019 `PATH.pdb` differs from ours on any of these axes, his neighbor MSD is different from ours, and his λ=80 Å⁻² may be the Branduardi-correct value *for his path*.

3. **Path density (downstream consequence of 2b).** Miguel's path has ⟨MSDᵢ,ᵢ₊₁⟩ ≈ 2.3/80 ≈ 0.029 Å² (inferred from his λ). Ours is 0.61 Å² (per-atom MSD from `generate_path_cv.py` on 15-frame 1WDW→3CEP linear interpolation, 112 Cα). Ratio ≈ 21× — exactly the residual ratio between 80 and 3.77. Adjacent Cα RMSD is ~0.17 Å on Miguel's path, ~0.78 Å on ours. Both are legitimate path densities *if* each was built from a self-consistent construction recipe; the difference in λ reflects the difference in construction, not an error in either.

## Falsification evidence — scoped to *our current path*

Self-projection of the 15 reference frames through PATHMSD under each candidate λ (UNITS=A, driver mode, 2026-04-23 Longleaf). **This tests λ on our 15-frame 1WDW→3CEP linear-interpolation bundle only; it does not falsify λ=80 as a value — it falsifies λ=80 *as a transplant onto our path*.**

| λ (Å⁻²) | s range | z range | Interpretation |
|---|---|---|---|
| 80 (transplanted from Miguel onto OUR path) | 1.000, 2.000, ... 15.000 (integer-snapped, clipped to nearest frame) | effectively 0 | Over-sharp *on our path*: exp(-80·0.61) ≈ 10⁻²¹; each frame projects purely onto itself, `s` is a step function of frame index, not continuous. Confirms 80 is mismatched to our path density; does NOT confirm 80 is wrong on Miguel's own path. |
| 3.77 (Branduardi formula on OUR path) | 1.092 → 14.907 monotonic | ≈ −0.049 Å² | Kernel-smooth; endpoints pulled slightly inward by the soft-min average (expected boundary effect). Matches historical FP-022 result expressed in the other unit convention (379.77 nm⁻²). |

Integer-snap under λ=80 is not a passing result on *our* path; it's a symptom of neighbor-weight collapse given ⟨MSD⟩=0.61 Å². On Miguel's ⟨MSD⟩≈0.029 Å² path, λ=80 would instead give the same kernel-smooth behavior we get at 3.77 on ours.

## Consequences for the Miguel contract

Everything else in Miguel's email is adopted verbatim (UNITS, ADAPTIVE=DIFF, SIGMA=1000 steps, HEIGHT=0.15, BIASFACTOR=10, PACE=1000, WALKERS_N=10, UPPER_WALLS AT=2.5 KAPPA=800, WHOLEMOLECULES ENTITY0=1-39268). Only `LAMBDA=80` is replaced with `LAMBDA=3.77`, because Branduardi's formula applied to our 15-frame 1WDW→3CEP linear-interpolation path gives 3.77, not 80.

**Explicit scope of this conclusion:**

- 3.77 is the self-consistent λ for *our current* `path_gromacs.pdb` (112 Cα, 15 frames, linear interpolation 1WDW→3CEP). Self-projection + FP-022 history both confirm this.
- 80 is likely the self-consistent λ for *Miguel's actual 2019* PATH.pdb, which may have been built with a different endpoint-alignment / subset / interpolation / intermediate-crystal recipe. The SI does not pin this down. We have not reconstructed his PATH.pdb.
- Therefore: 3.77 is correct *on this path*; 80 is not transplantable *onto this path*; but 80 is not "wrong" in any absolute sense — it's the Branduardi value on a denser path we have not yet rebuilt.

A faithful-replication path forward is not to run λ=80 on our path (that's a stress test, not replication), but to reconstruct Miguel's path-construction recipe — then see whether Branduardi on that path lands near 80 naturally. Until then, the two variables (path density, λ) remain entangled.

A future 1WDW→5DW0 anchor build will need its own λ audit (do not reuse 3.77).

## Logged failure patterns

- FP-022 corrigendum (2026-04-23): original 379.77 nm⁻² was correct; FP-027 re-opening was the error.
- FP-032: λ transferability across path densities. 80 Å⁻² is the likely Branduardi-correct λ for Miguel's own PATH.pdb; not transplantable onto ours. Path-construction recipe is the uncontrolled variable — see `path_construction_ABC_plan.md`.
- FP-033 (PM correction 2026-04-23): runtime alignment vs path-construction alignment must be kept separate. PATHMSD handles runtime alignment internally; path-construction alignment (how the 15 frames themselves were built) is NOT controlled by PLUMED and IS a real candidate for the λ-discrepancy axis.

## Files

- `plumed_template.dat` / `plumed_single.dat` — LAMBDA=3.77 hardcoded.
- `materialize_walkers.py` — LAMBDA_LITERAL assertion = "LAMBDA=3.77".
- `provenance.txt` per walker — records LAMBDA=3.77, rationale, equiv nm value, Miguel's 80 as non-transferable reference.
