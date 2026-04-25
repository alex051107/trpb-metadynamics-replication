# Codex Round 0.5 — SI Protocol Precision Read (2026-04-25)

CCB task: `20260425-150747-316-80538`
Reviewer: Codex
Context: Follow-up to Round 0; clean-context, no prior conversation. Authoritative source: `papers/ja9b03646_si_001.pdf` p.S3-S4 + Fig S4 + Fig S5.

## Reply (verbatim)

> 1. Quote: SI p. S4, Well-tempered MetaD section: "After an initial metadynamics run" ... "extracted ten snapshots" ... "10 replicas."
>
>    Verdict: SI supports the "initial MetaD trajectory → ten extracted snapshots → 10-replica multiple-walker production" reading. It does **not** say all 10 walkers started from the same equilibrated structure. It also does **not** explicitly spell out "snapshot i becomes walker i," but that is the only workflow stated in the SI text.
>
> 2. Quote: SI p. S3, Path CV definition: "path of 15 conformations" ... "linear interpolation."
>
>    Verdict: SI says the PATH-CV reference path is the O→C 15-frame interpolation from X-ray structural data. It does **not** say to insert the 10 walker starting snapshots into the reference path, rebuild the path, or recompute λ after seed extraction. Therefore: keep the original 15-frame reference path fixed; walker starts are initial conditions, not CV-definition frames. Any rebuilt path using the 10 seeds would be non-SI.
>
> 3. Quote: SI p. S4 text says convergence was monitored by "energy difference"; Fig. S4/S5 captions say "ΔΔG mean value."
>
>    Verdict: Yes, Fig. S4 and S5 are the convergence plots described in the SI text.
>
>    - Fig. S4, p. S10: three panels for PfTrpS αβ complex, PfTrpB isolated, PfTrpB0B2 stand-alone; four colored curves for Ain/Aex1/A-A/Q2. x-axis = time (ns), y-axis = ΔΔG (kcal/mol), approximate y range −8 to +4 kcal/mol. Time ranges are ~0–70 ns for PfTrpS, ~0–50 ns for PfTrpB, ~0–50 ns for PfTrpB0B2.
>    - Fig. S5, p. S10: two panels for PfTrpA-PfTrpB0B2(Q2) and PfTrpB2(Ain). x-axis = time (ns), y-axis = ΔΔG (kcal/mol), y range −8 to +4 kcal/mol. Time ranges are ~0–90 ns and ~0–50 ns, respectively.
>
> 4. Quote: SI p. S4: "After an initial metadynamics run" and later "50 – 100 ns."
>
>    Verdict: Initial single-walker MetaD's role is only to generate a trajectory from which ten conformationally diverse snapshots are extracted. SI is **SILENT** on the duration of this initial run, whether it used one walker or more, and whether an initial-run FES was reported. It is sequential, not parallel: initial MetaD first, extraction second, 10-walker production third. Round 0 stays consistent: a 22 ns pilot is defensible only as this preparatory seed-discovery stage, not as SI production.

## Direct project implications

| SI says | We do |
|---|---|
| Initial MetaD → 10 CV-diverse seeds | Initial pilot 45699102 (22 ns) provides COLVAR + xtc; v3 materialize_v3_validation.py picks 10 seeds via select_seeds() ✓ |
| Path CV: 15-frame O→C linear interpolation, fixed | path_seqaligned_gromacs.pdb (post-FP-034) ✓ — NOT rebuilt |
| Walker starts ≠ path CV definition | Walker start.gro from initial pilot trajectory, NOT inserted into path ✓ |
| Convergence: ΔΔG between FEL regions over time (Fig S4/S5 style) | Will produce after 10-walker production runs 50-100 ns/walker |
