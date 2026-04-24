# Prompt for external review (ChatGPT Pro / Colab / peer)

## What we want you to check

I'm worried about rabbit-hole risk on the TrpB MetaDynamics replication. I've just completed a path-piecewise audit and need independent verification that the conclusions are not overfit to my own reasoning.

Attached folder `colab_review/` contains 33 numerical claims and a reproducer script `verify_all.py`. Please:

1. **Run `python3 verify_all.py`** and confirm `33 PASS, 0 FAIL`. If any claim fails, tell me which.
2. **Sanity-check the methodology**, not just the numbers:
   - Is the PATHMSD formula I used for projections correct? (`s(R) = Σi·exp(-λ·MSDᵢ) / Σexp(-λ·MSDᵢ)`, `z(R) = -1/λ·ln Σ exp(-λ·MSDᵢ)`)
   - Is λ = 2.3 / ⟨MSD_adj⟩ the Branduardi convention for per-atom MSD?
   - For a candidate C whose MSD_min to any reference frame ≈ 2.47 Å², is z(R) ≈ MSD_min (my output) physically meaningful — i.e., is z the kernel-averaged off-path distance?
3. **Check whether my interpretation holds**:
   - Claim: "5DW0 / 5DW3 / 5DVZ are all at s≈1.07 on the direct 1WDW→3CEP path (λ=3.77 Å⁻²), so forcing them at MODEL 8 creates a path with neighbor_msd_cv = 0.96 (vs Belfast healthy ≤ 0.15) — reject."
   - Is this airtight? Are there other path constructions (not per-segment Branduardi) that would rescue this design?
4. **Flag anything suspicious**:
   - Chain selection: 1WDW uses chain B, 3CEP uses chain B, 5DW0/5DW3/5DVZ use chain A (they are β homodimers). Is this the right chain for TrpB β-subunit comparison?
   - Residue selection 97-184 + 282-305 (= 112 Cα). Does this correctly correspond to the COMM domain + base region across P. furiosus (1WDW) and S. typhimurium (3CEP)?

## One specific numerical claim I want a second opinion on

HILLS file from PLUMED 2.9 with `ADAPTIVE=DIFF SIGMA=1000 SIGMA_MIN=0.1,0.01 kerneltype=stretched-gaussian multivariate=true` reports σ_ss with median 0.030 — BELOW the declared SIGMA_MIN=0.1 floor for that CV.

Codex (another AI) claimed: "PLUMED 2.9 source applies SIGMA_MIN/MAX inside FlexibleBin::getInverseMatrix() BEFORE the hill is built. For multivariate hills, HILLS writes a Cholesky factor of the final multivariate covariance. So σ_ss < 0.1 in HILLS does not prove that actual deposited sigma was clamped to 0.1 but HILLS stored pre-clamp raw value."

Is this a correct reading of PLUMED 2.9 source? If not, is σ_ss below SIGMA_MIN a real violation?

## What the audit is trying to decide

Whether to **stop investing in PC-anchor-based path repair** (the 5DW0/5DW3 at MODEL 8 design), and instead:
- Email Miguel (original paper author) asking for his PATH.pdb / path-generation script
- Run the wall-relaxation falsification pilot (45448011, AT=2.5 → 4.0) before any further parameter changes
- Let Miguel's aggressive single-walker fallback (45324928, currently at 3.76 ns, max_s=1.50) continue only to an 8–10 ns hard gate

The audit's negative finding — "literature βPC labels are O-proximal in our 112-Cα PATHMSD subspace, not mid-path" — would be published as a substantive methodology conclusion, not treated as a failure.

## What NOT to spend time on

- Don't propose alternative MetaD parameter sets. We're explicitly NOT adjusting HEIGHT / SIGMA_MIN / BIASFACTOR within this review.
- Don't propose alternative reaction coordinates. PATHMSD is fixed.
- Don't debate λ=80 (Miguel's value) vs λ=3.77 (ours). That's FP-033, parked.
- Don't propose to rebuild PATH.pdb with different endpoint-alignment recipes. That's the separate A/B/C plan, also parked.

## Expected form of your response

1. `verify_all.py` PASS/FAIL report
2. Methodology critique (3-5 bullets)
3. Interpretation critique (is the audit conclusion airtight?)
4. One or two flagged concerns (things I might have missed)
5. Verdict: audit is reproducible / audit has a flaw at X / audit has an unexamined assumption at Y

Please keep response under 500 words total.
