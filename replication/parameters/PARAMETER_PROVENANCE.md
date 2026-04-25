# Parameter Provenance — every numerical parameter in Job 43813633+44008381 setup

> **Purpose**: for every number used in the running MetaD simulation, state
> (1) the source, (2) how we verified it, (3) known alternate interpretations
> if any, (4) status. This doc is the single authoritative reference for
> parameter truth in this campaign. If a number appears elsewhere and conflicts
> with this table, this table wins.
>
> **Updated**: 2026-04-16 after Codex adversarial review + offline CV audit.

---

## Source legend

| Code | Meaning |
|------|---------|
| **SI-quote** | SI has a verbatim quote stating this value. Must be grep-able against `papers/ja9b03646_si_001.pdf`. |
| **SI-derived** | Derived from SI text using a stated formula (e.g., λ from MSD_adj). Both formula and input must trace to SI-quote. |
| **SI-implied** | SI mentions the quantity but without explicit value; we chose within range stated. |
| **PLUMED-default** | PLUMED 2.9 docs default value or formula. Must cite doc URL. |
| **GROMACS-inherent** | GROMACS unit convention or default. |
| **Our-choice** | No SI/software mandate; we chose based on reasoning that must be stated. |
| **Legacy-bug** | Historical wrong value; kept here for traceability, not for use. |

---

## Path CV parameters (`plumed.dat` PATHMSD line)

### `LAMBDA = 100.79 Å⁻²` (current SI-faithful value, post 2026-04-25 audit)

| Field | Value |
|-------|-------|
| Source | SI-derived (Branduardi 2.3/⟨MSD_adj⟩ formula applied to OUR seq-aligned path) |
| SI formula | "The λ parameter was computed as 2.3 multiplied by the inverse of the mean square displacement between successive frames, 80." (SI p.S3) — the SI's literal "80" is path-specific to Maria-Solano's denser path; the prescription itself is the formula |
| Our seq-aligned path's ⟨MSD_adj⟩ (per-atom, post FP-034) | 0.0228 Å² |
| Our λ = 2.3 / ⟨MSD_adj⟩ | 100.79 Å⁻² |
| Codex R0/R0.5/R4 verdict (2026-04-25, clean-context SI re-read) | SI-faithful Branduardi value on OUR path = 100.79; Miguel email's literal 80 is 26% under (kernel weight ratio 0.10 vs Miguel's 0.16); both within heuristic tolerance but 100.79 is the formula-correct value |
| λ change impact (Codex R4 reprojection on pilot trajectory) | max \|Δs(λ=80→100.79)\| = 0.054, mean \|Δs\| = 0.0158 — well below half a TARGETS window (0.66) |
| Status | ✅ active 2026-04-25 onward; all post-2026-04-25 plumed.dat files use LAMBDA=100.79 |

### `LAMBDA = 80 Å⁻²` (Miguel email literal, 2026-04-23 to 2026-04-25)

| Field | Value |
|-------|-------|
| Status | **[SUPERSEDED 2026-04-25 by Branduardi self-computation = 100.79 on our path]** |
| Used by | pilot 45699102 (running at superseded value; Codex R4 verified existing seed picks remain valid under new λ); v3 validation bundle prior to 2026-04-25 patch |
| Why superseded | Miguel's literal 80 derives from his denser path; SI's actual prescription is the Branduardi formula, which on our seq-aligned path gives 100.79 |
| Provenance | Miguel email 2026-04-23, see `replication/metadynamics/miguel_2026-04-23/miguel_email.md` |

### `LAMBDA = 379.77 nm⁻²` (legacy, pre-FP-034 path)

| Field | Value |
|-------|-------|
| Status | **[SUPERSEDED 2026-04-23 by FP-034 fix; further superseded 2026-04-25 by 100.79 on seq-aligned path]** |
| Why superseded | (1) FP-034: legacy value derives from naive resid-number-mapped path with ⟨MSD⟩ inflated 26× by cross-species mismatch; (2) 2026-04-25 audit: even on the legacy path, the SI formula gives a different number than 80; the right path-specific value on the post-FP-034 seq-aligned path is 100.79 Å⁻² |
| Legacy formula | 2.3 / 0.6056 Å² = 379.77 nm⁻² (under nm-units convention) |
| Preserved for | FP-022 / FP-027 / FP-034 audit traceability; do NOT reuse |
| **Known alternate interpretation of SI "80"** (preserved for posterity) | summary.txt line 23-25 reads "80" as total SD Å² (not λ). Total SD interpretation 67.826 Å² matches SI's 80 within 15%; this argument is now superseded — Codex R0.5 confirmed SI's "80" is Maria-Solano's path-specific λ value, not a unit-ambiguous total SD |

### `REFERENCE = path_gromacs.pdb`

| Field | Value |
|-------|-------|
| Source | SI-quote (path endpoints + residue selection) |
| O endpoint | 1WDW chain B (PfTrpS, P. furiosus) — SI Figure S1 caption |
| C endpoint | 3CEP chain B (StTrpS, S. typhimurium) — SI Figure S1 caption |
| Atom selection | 112 Cα from residues 97-184 (COMM) + 282-305 (base region) — SI p.S3 |
| Interpolation | 15 frames linear Cartesian between O and C endpoints — SI p.S3 |
| Pre-alignment | Kabsch on the 112 Cα themselves — Our-choice (SI doesn't specify) |
| Total RMSD(O,C) in our frame | 10.895 Å per-atom mean (summary.txt) |
| Secondary verification | Direct resid matching validated (both 1WDW and 3CEP chain B have 112/112 CV residues); MDAnalysis script `generate_path_cv.py` |
| Generation commit | 43a810c, first shipped 2026-04-06; path_gromacs.pdb runtime file committed 669e303 on 2026-04-09 |
| Status | ✅ endpoints byte-match SI description; interpolation method self-consistent; CV audit (2026-04-16) confirms physical correctness |

---

## MetaD parameters (`plumed.dat` METAD line)

### `ARG = path.sss, path.zzz`

| Field | Value |
|-------|-------|
| Source | PLUMED-default (PATHMSD component names) |
| PLUMED 2.9 docs | "sss" = position on path, "zzz" = distance from path |
| Status | ✅ |

### `SIGMA = 0.1`

| Field | Value |
|-------|-------|
| Source | Our-choice (SI silent on numerical value) |
| SI quote | "The adaptive Gaussian width scheme... was used" (SI p.S3) — references Branduardi 2012, no numerical SIGMA |
| Semantic (PLUMED 2.9 METAD docs) | "Sigma is one number that has distance units" — single Cartesian scalar in nm for ADAPTIVE=GEOM |
| Why 0.1 nm | Doubled from earlier 0.05 (FP-024 fix 2026-04-15); chosen as reasonable geometric seed for adaptive Gaussian kernel |
| Status | ✅ FP-024 remediated; pending probe-extension verification |

### `ADAPTIVE = GEOM`

| Field | Value |
|-------|-------|
| Source | SI-quote (adaptive width used) + PLUMED-default (GEOM is one of two variants) |
| Alternatives | DIFF (dot-product of CV gradients) |
| Why GEOM | Standard for PATHMSD; Branduardi 2012 default |
| Status | ✅ |

### `SIGMA_MIN = 0.3, 0.005`

| Field | Value |
|-------|-------|
| Source | Our-choice (SI silent) + PLUMED-default (no default, must set for ADAPTIVE) |
| PLUMED 2.9 METAD docs | "the lower bounds for the sigmas (in CV units) when using adaptive hills" |
| s-axis floor 0.3 | Our choice: path axis spans [1,15] = 14 s-units, floor = ~2% of axis |
| z-axis floor 0.005 nm² | Our choice: observed z in Job 42679152 was 0.002-0.13 nm² (FP-024); floor just below typical |
| Why this exists | Prevents ADAPTIVE=GEOM sigma from collapsing (FP-024 observed collapse to 0.011 s-units, 1% of axis) |
| Status | ✅ FP-024 remediated |

### `SIGMA_MAX = 1.0, 0.05`

| Field | Value |
|-------|-------|
| Source | Our-choice (SI silent) |
| s-axis ceiling 1.0 | ~7% of axis; prevents Gaussian spreading to wash out structure |
| z-axis ceiling 0.05 nm² | Above typical z range but below unphysical |
| Status | ✅ |

### `HEIGHT = 0.628` (kJ/mol)

| Field | Value |
|-------|-------|
| Source | SI-quote (direct) + unit conversion |
| SI quote | "Initial Gaussian potentials of height 0.15 kcal·mol⁻¹" (SI p.S3) |
| Conversion | 0.15 × 4.184 = 0.6276 ≈ 0.628 kJ/mol |
| Status | ✅ |

### `PACE = 1000` (steps)

| Field | Value |
|-------|-------|
| Source | SI-derived from deposition interval |
| SI quote | "deposited every 2 ps of MD simulation at 350 K" (SI p.S3) |
| Derivation | 2 ps / 2 fs timestep = 1000 steps |
| Status | ✅ |

### `BIASFACTOR = 10`

| Field | Value |
|-------|-------|
| Source | SI-quote (direct) |
| SI quote | "well-tempered adaptative bias with a bias factor of 10" (SI p.S3) |
| Status | ✅ |

### `TEMP = 350` (K)

| Field | Value |
|-------|-------|
| Source | SI-quote (direct) |
| SI quote | "2 ps of MD simulation at 350 K" (SI p.S3) |
| Physical rationale | P. furiosus is thermophile; PfTrpB experiments at 75 °C |
| Status | ✅ |

---

## Multi-walker parameters (`multi_walker/plumed.dat` METAD line — Phase 2 only)

### `WALKERS_N = 10`

| Field | Value |
|-------|-------|
| Source | SI-quote |
| SI quote | "multiple-walkers metadynamics simulations with **10 replicas** were computed" (SI p.S3–S4, "Well-tempered MetaDynamics" section) |
| Status | ✅ direct SI number, no ambiguity |

### `WALKERS_RSTRIDE = 1000` (steps = 2 ns at PACE=1000 / dt=2 fs)

| Field | Value |
|-------|-------|
| Source | Our-choice (SI silent on sync stride) |
| Rationale | PLUMED tutorial convention: sync interval should be several × PACE so HILLS is large enough to matter when shared, but << total per-walker duration (50–100 ns) so walkers don't drift. 2 ns = 1000 Gaussians per sync is the standard choice. |
| PLUMED docs | https://www.plumed.org/doc-v2.9/user-doc/html/_m_u_l_t_i_p_l_e_w_a_l_k_e_r_s.html |
| Secondary verification | TBD after Phase 2 first run — if walkers drift apart too much (COLVAR ranges non-overlapping), reduce to 500 |
| Status | ⚠️ Our-choice, un-tested; flag for review after first 10-walker run |

### `WALKERS_DIR = ../`

| Field | Value |
|-------|-------|
| Source | Our-choice (directory layout decision) |
| Rationale | Shared HILLS.0..HILLS.9 sits in parent `multi_walker/`; each walker reads siblings' HILLS there. Alternative: single shared HILLS file with `WALKERS_DIR=.` — same effect but requires file-locking. The per-walker file pattern (`HILLS.<id>`) is PLUMED's default safe option. |
| Status | ✅ (standard PLUMED pattern) |

### Initial-structure selection for 10 walkers

| Field | Value |
|-------|-------|
| Source | SI-implied + Yu 2026-04-09 directive (L2859) |
| SI quote | "we extracted ten snapshots for each system **covering approximately all the conformational space available**" (SI p.S3–S4) |
| Yu directive | "用你的眼睛在 PyMOL 里挑, 不能每隔 N frame 取一个" (2026-04-09 transcript L2859) |
| Our implementation | Two-phase `multi_walker/setup_walkers.sh`: Phase 1 proposes 10 via KMeans(s,z) on COLVAR; Phase 2 requires user to pass `--commit-frames t1,…,t10` only after PyMOL visual QA. Script refuses to bypass the human-in-the-loop. |
| Status | ✅ (enforced by script design) |

---

## MD integration parameters (`metad_probe.mdp`)

### `dt = 0.002` (ps = 2 fs)

| Field | Value |
|-------|-------|
| Source | SI-quote (direct) |
| SI quote | "a 2 fs timestep" (SI p.S3) |
| Status | ✅ |

### `nsteps = 5,000,000` (probe, to be extended to 25,000,000 via convert-tpr -extend)

| Field | Value |
|-------|-------|
| Source | Our-choice (probe duration) |
| Rationale | 10 ns probe: verify SIGMA floor fix before committing to 50+ ns production |
| Now | Extended to 25,000,000 (50 ns total) via `gmx convert-tpr -extend 40000` 2026-04-16 |
| Status | ✅ |

---

## Force field (from tleap, established at system build 2026-03-31)

| Parameter | Value | Source |
|-----------|-------|--------|
| Protein FF | ff14SB | SI-quote: "AMBER ff14SB" |
| Water FF | TIP3P | SI-quote: "TIP3P water model" |
| Ion FF | JC (Joung-Cheatham) | AMBER default; SI doesn't specify |
| PLP cofactor charge | -2 | 2026-03-30 literature review of Caulkins 2014 NMR (see validations/2026-03-30_plp_protonation_literature_review.md) |
| PLP GAFF charges | RESP from Gaussian 16 HF/6-31G* | Our PLP parameterization pipeline; SI-quote that they used "HF/6-31G*"  |

---

## Known legacy / superseded values (do NOT use)

| Parameter | Wrong value | When | Bug ref | Correct |
|-----------|-------------|------|---------|---------|
| LAMBDA | 3.3910 | pre 2026-04-08 | FP-022 | 379.77 (per-atom MSD convention + PATHMSD) |
| LAMBDA | 0.033910 | pre 2026-04-04 | FP-018 | (same, unit fix Å⁻²→nm⁻²) |
| MSD (via calculate_msd) | 3.798 (RMSD, not MSD) | pre 2026-03-31 | FP-015 | 0.6056 Å² per-atom MSD |
| SIGMA (fixed) | 0.2, 0.1 | some tutorials | FP-025 | SI doesn't specify; we chose 0.1 with SIGMA_MIN floor |
| SIGMA (no floor) | 0.05 with no SIGMA_MIN/MAX | pre 2026-04-15 (Job 42679152) | FP-024 | 0.1 + SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05 |

---

## How to use this document

1. **Before modifying any parameter**, read the relevant row. Cite it in your commit message.
2. **Before trusting an SI "quote" someone cites**, grep for it in `papers/ja9b03646_si_001.pdf` via `pdfgrep` or `pdftotext | grep`.
3. **Before overriding the current value**, read the "Known alternate interpretation" if any. Don't re-interpret if the ambiguity is moot (e.g., LAMBDA's SI-80 ambiguity is moot because CV audit passes).
4. **When adding a new parameter**, copy a row's structure: source, verification, status.
5. **If a parameter fails verification**, add a new FP entry in `failure-patterns.md`, update this table, and move the old value to the "legacy" section.

---

## Secondary verification actions taken for this doc (2026-04-16)

| Action | Result |
|--------|--------|
| Read SI p.S3 verbatim for SIGMA | Confirmed SI has no numerical SIGMA; only "adaptive Gaussian width scheme" |
| Read summary.txt lines 23-25 for λ interpretation | "Reported MSD: ~80 Å² (interpreted as total SD) / Our total SD: 67.826 Å² (ratio 0.85x)" — treat "80" as total SD, NOT as λ |
| Fetch PLUMED 2.9 PATHMSD docs via jina-reader | Confirmed "sss"/"zzz" component naming, OPTIMAL default alignment, LAMBDA in plumed units (nm⁻² for GROMACS) |
| Fetch PLUMED 2.9 RESTART docs | Confirmed RESTART directive needed for HILLS append; "not all MD codes send PLUMED restart info, if unsure always put RESTART" |
| CV audit via offline projection (`.worktrees/cv-audit/project_structures.py`) | 1WDW→s=1.09, 3CEP→s=14.91, 4HPX→s=14.91, 5DW0→s=1.07, z range [-0.00025, 0.02451] nm² — path CV physically correct |
| Codex adversarial review | Caught the SI-"80"-as-λ misinterpretation (FP-027); confirmed FP-022 validation is narrow but fine for its scope |
