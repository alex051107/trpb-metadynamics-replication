# GroupMeeting 2026-04-17 — Parameter Defense Table

> **Purpose**: single-source-of-truth for every numerical parameter that
> appears on any slide in `GroupMeeting_2026-04-17.pptx`. Each row = a
> one-sentence answer Zhenpeng can say aloud without scrambling. If a row
> is missing or the one-liner won't hold up to a 3-layer follow-up, add
> the detail to `GroupMeeting_2026-04-17_Drill_Prep.md` Section 6A
> (sensitivity) or 6D (honest-broker).
>
> **Source-type legend**: SI-quote = literal quote from Osuna 2019 SI. SI-derived = derived via stated formula from SI quantities. SI-implied = SI mentions qualitatively, value is ours. PLUMED-default = PLUMED 2.9 manual default or formula. GROMACS-inherent = unit convention. Our-choice = no SI/software mandate.
>
> **Cross-ref**: `replication/parameters/PARAMETER_PROVENANCE.md` for the full runtime parameter table; this doc is the SLIDE-SPECIFIC version.

---

## Slide 2 — Recap

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| LAMBDA (old) | 3.3910 nm⁻² | legacy-bug from FP-015/022 | — | "what was the bug before?" → see FP-022 |
| LAMBDA (corrected last week) | 379.77 nm⁻² | SI-derived (2.3/MSD_adj per atom) | self-consistency test 2026-04-08 | "re-explain where 379.77 came from" |
| Job 42679152 length | 50 ns | Our-choice | metad_probe.mdp nsteps=25,000,000 | "why 50 ns not 100?" → SI replicates are 50-100 ns |

---

## Slide 3 — Job 42679152 result

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| s(R) range | [1.00, 1.63] over 50 ns | `np.loadtxt('COLVAR')[:,1].min/max` | Longleaf COLVAR of Job 42679152 | "exact command to reproduce?" → `python3 -c "import numpy; d=numpy.loadtxt('COLVAR',comments='#'); print(d[:,1].min(), d[:,1].max())"` |
| Number of Gaussians | 25,000 | `wc -l HILLS` minus 2 (header) | Longleaf HILLS | "why exactly 25000?" → 50 ns / 2 ps PACE = 25,000 |
| Accumulated bias | 48 kJ/mol | `np.loadtxt('COLVAR')[:,3].max()` | Longleaf COLVAR | "kJ or kcal?" → kJ; 48/4.184 ≈ 11.5 kcal/mol |
| Fraction time at s<1.1 | >99% | numpy boolean mask | - | "how confident is >99%?" → 49,720 of 50,000 frames; exact 99.44% |
| σ_path.sss collapse range | 0.011–0.072 s-units | HILLS column 4 min/max | Longleaf HILLS | "is this per-CV or global?" → per-CV in CV units, from HILLS column header |
| Path axis length | 14 s-units (1 → 15) | PATHMSD frame count | `path_gromacs.pdb` has 15 MODEL blocks | "why 15?" → SI p.S3 specifies 15 frames |

---

## Slide 4 — FP-024 root cause

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| SIGMA (pre-fix) | 0.05 nm | previous plumed.dat | FP-025 investigation | "was 0.05 in SI?" → No. SI only says "adaptive width scheme"; 0.05 was our choice (FP-025) |
| SIGMA unit | Cartesian nm | PLUMED 2.9 METAD docs | quoted verbatim: "Sigma is one number that has distance units" | "how do you know it's nm?" → GROMACS default length unit is nm; PLUMED follows |
| Gaussian width collapsed to | 0.011 s-units | HILLS column 4 first rows | - | "how do you go from nm to s-units?" → ADAPTIVE=GEOM projects Cartesian σ onto each CV; see PLUMED's METAD.cpp |

---

## Slide 5 — SIGMA floor fix

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| SIGMA (new) | 0.1 nm | Our-choice | 2× previous; geometric seed | "why exactly 0.1?" → doubled the collapsing value; see Drill_Prep 6A SIGMA |
| SIGMA_MIN[s] | 0.3 | Our-choice | path axis is 14 units; 0.3 ≈ 2% of axis, enough to span multiple frames | "why 2%?" → see Drill_Prep 6A SIGMA_MIN |
| SIGMA_MIN[z] | 0.005 nm² | Our-choice | Job 42679152 z observed range 0.002-0.13 nm²; 0.005 below typical noise | "why 0.005 not 0.01?" → at z-floor barely above observed noise level |
| SIGMA_MAX[s] | 1.0 | Our-choice | ~7% of axis; prevents washing out basin structure | "why 1.0 not 2.0?" → 2.0 would be 14% of axis, wider than a typical basin |
| SIGMA_MAX[z] | 0.05 nm² | Our-choice | above typical z range; safety ceiling | - |
| HEIGHT | 0.628 kJ/mol | SI-derived | SI p.S3 "0.15 kcal/mol" × 4.184 | "kcal vs kJ?" → 1 kcal = 4.184 kJ; GROMACS uses kJ |
| PACE | 1000 steps | SI-derived | "deposited every 2 ps" / 2 fs timestep | "why 2 ps?" → quoted from SI directly |
| BIASFACTOR | 10 | SI-quote | SI p.S3 "bias factor of 10" | - |
| TEMP | 350 K | SI-quote | SI p.S3 "at 350 K"; P. furiosus thermophile | "why 350 not 300?" → species' physiological temp; thermostat target |
| LAMBDA | 379.77 nm⁻² | SI-derived | 2.3/MSD_adj; see Slide 2 | "same as last week?" → yes, unchanged |
| Probe length (Job 43813633) | 10 ns | Our-choice | 5,000,000 steps × 2 fs | "why 10 ns probe not 50?" → fast validation of SIGMA fix before long run |

---

## Slide 6 — Probe dynamics

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| max s(R) | 1.393 | `np.loadtxt('COLVAR')[:,1].max()` | Longleaf COLVAR of Job 43813633 | "O region or past it?" → still O (SI: O=1-5); see Drill_Prep 6D |
| Fraction t∈[0,8ns] at s<1.05 | 99.3–99.8% | numpy histogram | Agent C analysis | - |
| Fraction t∈[8,10ns] at s<1.05 | 73.0% | same | - | "what made the difference?" → bias accumulated enough to tip into escape trajectory |
| First s>1.2 timestamp | 9.137 ns | index of first row where s>1.2 | - | "within noise?" → sustained, not single-frame spike (confirmed by neighboring rows) |
| s↔z Pearson correlation (full) | +0.343 (p<1e-270) | scipy.stats.pearsonr | Agent C | - |
| s↔z correlation t=[0,2] | +0.14 | same, windowed | - | "weak early coupling?" → normal thermal; before bias takes effect |
| s↔z correlation t=[4,6] | -0.31 | same | - | "negative — orthogonal?" → walker fluctuating perpendicular to path |
| s↔z correlation t=[8,10] | +0.49 | same | - | **"what does +0.49 mean?"** → see Drill_Prep 6D "escape or O basin" |
| Escape velocity t=[0,2] | 0.000086 per ps | d(max_s)/dt | - | "units?" → s-units per ps |
| Escape velocity t=[8,10] | 0.000192 per ps | same | - | "ratio?" → 2.23× faster in last window |
| Local bias at s≈1.0 | 55.5 kJ/mol | COLVAR bias column | - | "vs kT?" → kT=2.908 kJ/mol at 350K, so ~19× kT |
| Typical barrier reference | 25 kJ/mol | JACS 2019 Fig 2a | reported values | "is 55 enough?" → yes in principle; being rejected because bias hasn't localized in escape direction |

---

## Slide 7 — FP-027 wrong turn

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| SI "80" — my misread | λ=80 nm⁻² | WRONG; SI p.S3 text | Codex adversarial review | "what's the correct read?" → total SD Å² (see summary.txt) |
| SI "80" — correct read | total SD Å² | summary.txt line 23-25 | self-computed total SD = 67.826 Å² | "how off?" → ratio 67.826/80 = 0.85× (matches within 15%) |
| Our per-atom MSD | 0.006056 nm² = 0.6056 Å² | computed from 15 frames | summary.txt line 16 | "same or different from SI's 80?" → SI's 80 = total over 112 atoms; our per-atom avg = 0.6056 Å² |
| 112 | N_atoms in CV | COMM 97-184 + 282-305 | path_gromacs.pdb | "exactly where from?" → SI p.S3 explicit |
| time wasted on wrong direction | 3+ hours | - | - | "systemic fix?" → see Drill_Prep 6E |

---

## Slide 8 — CV audit

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| s(1WDW) | 1.09 | `project_structures.py` output | exit code 0 | "why not exactly 1?" → PATHMSD formula s=Σi·w_i/Σw_i; pure endpoint gives ~1.03 due to kernel width |
| s(3CEP) | 14.91 | same | - | "why not 15?" → symmetric reason to 1WDW |
| s(4HPX) | 14.91 | same | - | "4HPX is Pf, 3CEP is St — why same s?" → both are closed-COMM; path CV recognizes structural similarity across species |
| s(5DW0) | 1.07 | same | - | "5DW0 is Aex1 — isn't Aex1 different from Ain?" → same COMM-open conformation; path CV measures domain motion not substrate |
| s(5DVZ) | 1.07 | same | - | - |
| s(frame 1 self) | 1.0913 | PATHMSD self-consistency | project_structures.py | "what should frame 1 give?" → 1.0 ideally; 1.09 is close |
| s(frame 8 self) | 8.0000 | same | exact by symmetry | "why exactly 8?" → midpoint of 15 frames; PATHMSD is symmetric |
| s(frame 15 self) | 14.9087 | same | - | - |
| z(R) range | -0.00025 to 0.025 nm² | project_structures.py output | - | "can z be negative?" → yes; PATHMSD z = -(1/λ)·log(Σ exp(-λ·MSD)) can go slightly negative when walker perfectly matches a frame |
| CV residues | 112 Cα | 97-184 (COMM) + 282-305 (base) | SI p.S3 | "why these specific residues?" → SI Figure S1 specifies; we use same |

---

## Slide 9 — Checkpoint restart

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| convert-tpr -extend value | 40000 ps | chosen to reach 50 ns total | GROMACS docs: `-extend` is in ps | "why not -nsteps?" → `-nsteps` alone doesn't override "simulation complete" status; FP-026 |
| RESTART directive | required in plumed_restart.dat | PLUMED 2.9 RESTART docs | - | "why not auto-detect?" → PLUMED docs warn: "not all MD codes send restart info" |
| HILLS row count pre-restart | 5003 | `wc -l HILLS` before extend | - | "5003 includes headers?" → yes, 2 header + 5001 data rows |
| HILLS row count post-restart | 5106+ | same after extension | runtime check | "proves append?" → yes, + no bck.*.HILLS + first data row unchanged (pre-flight assert in extend_to_50ns.sh) |
| Extend total nsteps | 25,000,000 | 50 ns × 500,000 steps/ns | convert-tpr output | - |
| SIGMA/HEIGHT/PACE for extension | UNCHANGED from probe | plumed_restart.dat diff from plumed.dat | md5 normalized diff empty | "what changed then?" → only RESTART added at top |
| 25 ns decision-gate thresholds | max s ≥ 5 / 3-5 / <3 | Our-choice | SI's O=1-5, PC=5-10, C=10-15 | "why not at 10 ns?" → 10 ns we already probed; 25 ns gives real signal above noise |

---

## Slide 10 — Process + next steps

| Parameter | Value | Source | Verified | Why would Yu ask / answer |
|-----------|-------|--------|----------|---------------------------|
| Number of FP entries (as of today) | 27 | `grep "^## FP-" failure-patterns.md \| wc -l` | - | "how many added this week?" → 4 (FP-024, 025, 026, 027) |
| General rules count | 21 | grep in failure-patterns.md | - | - |
| Branches pushed | 3 | `fix/fp024-sigma-floor`, `feature/probe-extension-50ns`, `diag/cv-audit` | `git branch -r` | "why 3 separate?" → isolate SIGMA fix from CV audit from restart infra |
| Repo visibility | PRIVATE | `gh repo view` | - | "when made private?" → 2026-04-16 |
| 10-walker plan — walkers | 10 | SI-quote p.S3 | - | "why 10 not 15 or 5?" → SI specifies 10 walkers |
| 10-walker plan — per-walker length | 50-100 ns | SI-quote p.S3 | - | "total?" → 500-1000 ns accumulated across walkers |
| Target FES comparison date | 2026-04-24 | Our-choice (self-imposed) | - | - |

---

## Numbers Yu might pull out of past transcripts (2026-04-09 context)

These are references from last week's transcript that may come up:

| Reference | Value | Context |
|-----------|-------|---------|
| ratio 80 vs 0.6056 = 132 | ~132× (per-atom MSD convention error) | Yu asked about this 2026-04-09 (L393); fixed via 2.3/0.6056 = 379.77 |
| Job 41514529 s range | [7.77, 7.83] | pre-fix FUNCPATHMSD run, documented in summary.txt |
| 46.3 ns of Job 41514529 | - | walltime limit on the broken run |
| 5003 rows COLVAR on Job 43813633 | - | post-probe baseline |
| "Anstrand 与 Nano" Yu flagged L459 | unit confusion SI itself | acknowledged but not central to today |
