# GroupMeeting 2026-04-17 — Drill Prep (cold-read survival)

> **This is the rehearsal document.** Read this cold ~30 min before the
> meeting and you should be able to field Yu's per-parameter drill
> without scrambling. If any entry's answer won't survive 3 layers of
> follow-up ("what / formula / where in SI / did you verify / what if
> you tuned it"), expand it.
>
> Target readout: **4 of 5 cold-read test questions answered fluently,
> 1 rough**. Self-test at the end of this doc.
>
> **Organization**:
> - 6A — sensitivity tuning sketch (for every tunable parameter)
> - 6B — failure modes if unfixed (per FP entry)
> - 6C — code walkthrough (actual commands)
> - 6D — honest-broker for weak claims
> - 6E — FP-027 systemic fix
> - Self-test — 5 cold-read questions

---

## 6A. Sensitivity tuning sketch — "调大调小会怎么样?"

For every numerical knob, 3 bullets: what if 2× larger, what if 2× smaller, why the current value is reasonable.

### LAMBDA = 379.77 nm⁻²

- **2× larger (759.54)**: adjacent-frame kernel weight drops to
  `exp(-λ·MSD_adj × 2) = exp(-4.6) = 0.010`. Walker snaps hard to the
  nearest reference frame → s becomes effectively a step function,
  `ds/dx ≈ 0` between frames, bias loses grip on protein atoms. Walker
  gets stuck at integer s values.
- **2× smaller (189.89)**: adjacent-frame kernel weight rises to
  `exp(-2.3/2) = exp(-1.15) = 0.317`. Multiple frames contribute
  comparably at any walker position → s is smeared across frames,
  resolution along the path axis degrades, FES loses basin structure.
- **Sweet spot**: the `λ = 2.3 / MSD_adj` rule places adjacent-frame
  weight at `exp(-2.3) = 0.100` — the Branduardi 2007 balance between
  resolution and smoothness. Our value 379.77 is self-consistent via
  frame projection: frame_1 → s=1.09, frame_8 → s=8.00, frame_15 → s=14.91.

### SIGMA = 0.1 nm (Cartesian, seed for ADAPTIVE=GEOM)

- **2× larger (0.2 nm)**: initial Gaussian geometric seed wider →
  early bias fills s-space faster but with coarser resolution. Could
  over-smooth early basins. PLUMED adapts, so long-run behavior
  similar, but transient before adaptive kicks in sees degraded FES.
- **2× smaller (0.05 nm)**: this is exactly the pre-fix value →
  FP-024 collapse (Gaussians to 0.011 s-units, walker trapped). With
  the new SIGMA_MIN floor, 0.05 might actually still work — but
  defensively we moved up to 0.1 to avoid edge-case.
- **Sweet spot**: not in SI. PLUMED docs don't fix a default. We
  doubled from the collapsed value (0.05 → 0.1) as a geometric guess;
  the SIGMA_MIN floor is what actually enforces the real constraint.

### SIGMA_MIN = [0.3, 0.005]  (per-CV lower bound, CV units)

- **[0.1, 0.001] (smaller)**: s-floor would barely restrain the
  adaptive collapse from FP-024. We'd risk reverting to Gaussians of
  0.01–0.02 s-units and walker trapping. Z-floor near observed noise
  level; could let noise-sized Gaussians deposit, no benefit.
- **[0.5, 0.01] (larger)**: s-floor would force Gaussians to span
  ~3.6% of path axis → would smooth out adjacent-basin energy
  differences (for example can't resolve Aex1 vs Ain at s≈1 if they
  sit within 0.5 s-units of each other).
- **Sweet spot**: [0.3, 0.005] chosen as ~2% of path axis (0.3 / 14 ≈
  0.021) — enough to span multi-frame kernel overlap, below basin
  width. Z-floor just above observed z-noise (0.002) in Job 42679152
  COLVAR.

### SIGMA_MAX = [1.0, 0.05]  (per-CV upper bound, CV units)

- **[2.0, 0.1]**: Gaussians could be 14% of path axis wide → would
  spread bias over multiple basins, no local resolution. Bias becomes
  a featureless slope on FES.
- **[0.5, 0.02]**: tighter ceiling; adaptive σ in pristine regions
  can't expand — might oscillate between SIGMA_MIN and SIGMA_MAX
  without settling to the physically appropriate width.
- **Sweet spot**: 1.0 is ~7% of axis (fits a typical basin), 0.05 is
  above typical z range but below unphysical.

### HEIGHT = 0.628 kJ/mol (initial Gaussian height, well-tempered)

- **2× larger (1.256 kJ/mol)**: bias accumulates faster → shorter
  total sim to reach effective FES, but risk of over-shooting
  thermodynamic bias (system kicked into rare unphysical
  configurations before well-tempered damping engages).
- **2× smaller (0.314 kJ/mol)**: bias accumulates slower → longer
  run to reach convergence. Walker may take 2× longer to escape O.
- **Sweet spot**: SI-specified 0.15 kcal/mol = 0.628 kJ/mol. Direct
  quote, not tunable from our side.

### PACE = 1000 steps (Gaussian deposition frequency)

- **500 steps**: 2× more Gaussians → finer temporal resolution of bias
  build-up, but 2× disk/memory for HILLS and slightly slower mdrun.
- **2000 steps**: 2× fewer Gaussians → coarser build-up; walker may
  escape/settle between deposits, breaking well-tempered assumption.
- **Sweet spot**: 2 ps / 2 fs = 1000 steps. SI quotes "every 2 ps";
  direct match.

### BIASFACTOR = 10 (well-tempered γ parameter)

- **20**: higher effective temperature, faster barrier-crossing but
  slower FES convergence; walker explores more regions before
  settling. Good for hard systems.
- **5**: lower effective T, less aggressive biasing; convergence
  faster but less exploration. Walker may underfill basins.
- **Sweet spot**: SI-specified 10. Direct quote. ΔE_T = (γ-1)/γ × ΔE ≈
  0.9 × ΔE bias damping asymptote.

### TEMP = 350 K (thermostat)

- **300 K (typical room T)**: smaller thermal fluctuations; slower
  barrier crossing at fixed bias. FES barriers measured would be
  physically different (different kinetics, but same equilibrium if
  bias is converged).
- **400 K**: faster fluctuations, more escape events, but protein
  stability risks (thermophile denaturation above ~370 K in vitro).
- **Sweet spot**: 350 K = *P. furiosus* physiological temp. SI quote;
  thermophile.

### NUM_FRAMES = 15 (path CV reference)

- **30**: finer path resolution, each s-unit covers less structural
  change → LAMBDA would need recalculation (2.3/new_MSD_adj with
  smaller MSD → λ ~4× bigger). Linear interpolation denser.
- **8**: coarser path, MSD_adj larger → smaller LAMBDA (~100). CV more
  forgiving of walker position between frames but loses resolution for
  Aex1/Ain-type differences.
- **Sweet spot**: SI specifies 15 frames. Matches.

### CV atom set = 112 Cα (COMM 97-184 + base 282-305)

- **Add more atoms (e.g., 200 Cα)**: including non-COMM residues
  would dilute the COMM motion signal with rigid-body tumbling of
  fixed parts. Path would need to be redefined.
- **Fewer atoms (e.g., 60 Cα only in COMM)**: drop the base region
  would break SI replication (SI explicitly includes 282-305). Also
  loses the pivot-point information for the hinge motion.
- **Sweet spot**: SI specifies 97-184 + 282-305 by Figure S1 + p.S3
  text. Direct quote.

### nsteps (probe) = 5,000,000 → extended to 25,000,000

- **Longer (50 million = 100 ns single walker)**: more chance for
  barrier crossing, but 50% longer walltime (no return on sunk cost
  if still stuck).
- **Shorter (2.5 million = 5 ns probe)**: wouldn't catch the t=8-10 ns
  escape signal we saw in Job 43813633.
- **Sweet spot**: 10 ns probe enough to diagnose SIGMA floor behavior;
  50 ns extension matches per-walker time in SI's 10-walker protocol.

---

## 6B. Failure modes if unfixed

For each recent FP, what the simulation would look like without the
fix + the fastest diagnostic signature.

### FP-022 (without fix) — LAMBDA 112× off

Without per-atom MSD convention correction, LAMBDA stayed at 3.391 nm⁻²
(total-SD convention). Kernel weight at adjacent frame becomes
`exp(-3.391 × 0.0778)` where 0.0778 is per-atom *RMSD* not MSD → weight
≈ `exp(-0.264) = 0.77`. All 15 frames contribute nearly equally at any
walker position → s is always in a narrow range centered on the
average index (≈7-8) regardless of actual position. Job 41514529
exhibited exactly this: s confined to [7.77, 7.83] for 46 ns, 0 real
sampling. Diagnostic signature: s range width < 0.2 over long time.

**How to re-verify if Yu asks**: project any frame back through the
CV. `frame_1` should give `s ≈ 1`. If with your LAMBDA it gives `s ≈ 4`
instead, LAMBDA is wrong. Self-consistency test is the single fastest
check.

### FP-024 (without fix) — SIGMA collapse under ADAPTIVE=GEOM

Without SIGMA_MIN, ADAPTIVE=GEOM shrinks per-CV Gaussian to ~0.011
s-units = 0.07% of the [1,15] path axis. 25,000 such needle Gaussians
deposit at s ≈ 1, creating a deep narrow well (~48 kJ/mol bottom at
s=1) with zero-gradient between walker position and nearest basin
edge. Walker cannot "feel" the bias pushing it out along s. Walker
stays in O basin for full 50 ns.

**Diagnostic signature**: HILLS column 4 (sigma_path.sss) shows values
< 0.02 early in the run. COLVAR path.sss stays in [1.0, 1.6] without
approaching 2 even at late times. Job 42679152 exhibited exactly this.

### FP-025 (without fix) — fabricated `[SI p.S3]` SIGMA citation

If we'd trusted the tutorial's fake "SIGMA=0.2,0.1 [SI p.S3]" citation,
we'd have been applying a value with no defensible source while
believing we were following SI. Yu would have caught this under drill
("where exactly in SI p.S3 is 0.2,0.1?" → nowhere). Worse: we'd have
no FP-025 entry meaning we might propagate the error to other systems
(multi-walker, GenSLM comparison, etc.).

**Diagnostic signature**: grep SI PDF for "SIGMA" or "0.2,0.1" — no
match. Tutorial-source paper trail ends at an AI that fabricated it.

### FP-026 (without fix) — checkpoint restart clobbers HILLS

Without `convert-tpr -extend`, GROMACS would exit immediately at
restart time: `metad.tpr` says "nsteps=5,000,000, simulation already
complete at checkpoint". Job would burn 60 sec of walltime doing
nothing. Without `RESTART` directive in plumed_restart.dat, PLUMED
would open HILLS in write mode, back up existing 5003-row HILLS to
bck.0.HILLS, and start depositing Gaussians from scratch. The 10 ns of
bias history and the FP-024 fix validation would be gone.

**Diagnostic signature**: log message "simulation already complete"
(the GROMACS bug) or presence of `bck.0.HILLS` (the PLUMED bug) in the
run directory after restart.

### FP-027 (without Codex catch) — recurrent SI misread

Without Codex adversarial review, I would have spent another day+ on
the alignment-method diagnostic path: regenerating path_gromacs.pdb
with scaffold alignment, resubmitting a probe, repeating the wrong
diagnosis chain. Eventually would have realized the original 379.77
was right, but at cost of ~3 extra days and no systemic defense
against the next SI-ambiguity trap.

**Diagnostic signature**: any new numerical diagnostic that claims "SI
says X, we have Y, we're off by N×" without first reading
`summary.txt` / `PARAMETER_PROVENANCE.md` / `failure-patterns.md` for
pre-existing interpretation. If the existing repo has an interpretation
and you're not reading it, you're repeating FP-027.

---

## 6C. Code walkthrough — "show me the actual command"

For each procedure mentioned in the deck, the exact command and 3-bullet rationale.

### Path CV generation (reference file for PATHMSD)

```
python3 replication/metadynamics/path_cv/generate_path_cv.py --num-frames 15
```

- Reads `replication/structures/1WDW.pdb` chain B + `3CEP.pdb` chain B
- Extracts 112 Cα from residues 97-184 + 282-305; Kabsch aligns 3CEP
  onto 1WDW using the 112 atoms themselves (method A — self-align)
- Linearly interpolates 15 frames; writes `path_gromacs.pdb` (MODEL/
  ENDMDL blocks) and `summary.txt` (λ recommendation + MSD statistics)

### CV audit — does path CV project known structures sensibly?

```
cd .worktrees/cv-audit
/tmp/aln_env/bin/python project_structures.py
echo "exit code: $?"   # 0 = pass, 2 = missing inputs, 3 = invariant fail, 4 = crash
```

- Script resolves paths via `Path(__file__).parent` (branch-local,
  hermetic — no live RCSB downloads)
- Projects 6 PDBs (1WDW, 3CEP, 4HPX, 5DW0, 5DVZ, 5DW3) onto the
  PATHMSD frames, computes s/z via `s = Σ i·exp(-λ·MSDᵢ) / Σ
  exp(-λ·MSDᵢ)`
- Hard-gates: endpoints in [0.8,1.5]/[14.5,15.2]; SI-expected O/C
  ranges for key intermediates; z ≤ tolerance. Exit 3 on any violation

### Checkpoint restart — extend 10→50 ns without losing bias history

```
# Step 1: extend tpr by 40 ns (in ps)
gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr

# Step 2: mdrun with -cpi loads state; plumed_restart.dat has RESTART
gmx mdrun -s metad_ext.tpr -cpi metad.cpt \
          -deffnm metad -plumed plumed_restart.dat \
          -ntmpi 1 -ntomp 8
```

- `-extend 40000` avoids the "simulation already complete" bug; without
  it, `-nsteps` alone is not honored (FP-026)
- `plumed_restart.dat` line 1: `RESTART` — forces PLUMED's HILLS into
  append mode; without it PLUMED backs up and clobbers (FP-026)
- `-deffnm metad` keeps output filenames same as pre-run (xtc, cpt,
  edr, log, gro) so COLVAR and HILLS continue by name

### FES reconstruction (post-run, not yet executed)

```
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 2.908
```

- `--kt 2.908` is kJ/mol at 350 K (= kB·T · NA / 1000; GROMACS units)
- NOT 0.695 kcal/mol; that would give FES 4.184× too large (FP-021)
- `--mintozero` shifts minimum to 0 for visual comparison with SI

### Parameter provenance verification (grep drill)

```
# check every number on slides maps to a defense row
grep -E '[0-9]+\.[0-9]+|[0-9]+ nm|[0-9]+ ns|kJ/mol|kcal' reports/GroupMeeting_2026-04-17_Outline.md
# cross-reference against
grep -E '[0-9]+\.[0-9]+' reports/GroupMeeting_2026-04-17_Parameter_Defense.md
```

---

## 6D. Honest-broker for weak claims

The 5 cold-read-fail questions with full defenses.

### Q1: "SIGMA_MIN=0.3 — where does 0.3 come from, what's the formula?"

**Honest answer**:
- No formula from SI (SI says only "adaptive Gaussian width scheme,"
  no numerical SIGMA_MIN).
- 0.3 is our choice, chosen as roughly 2% of the [1,15] path axis
  (14 s-units × 0.021 ≈ 0.3). 2% is the judgment call — it's wide
  enough that adjacent reference frames overlap in kernel space (so
  bias can "cross" between frames), narrow enough that basin structure
  within s-units is preserved.
- **What would weaken this**: if 0.1 also works (walker escapes under
  lower floor), 0.3 is over-restrictive. If 0.5 fails (oscillation or
  washed basins), 0.3 is under-restrictive. We haven't tested the
  sensitivity — single run at 0.3 only. Drill-prep 6A has the
  hypothetical tunings.
- **Commitment**: if Job 44008381 at 25 ns doesn't show max s > 3,
  tuning SIGMA_MIN is one of the Phase 3 branches we consider.

### Q2: "max s=1.393 — is that escape or still O basin?"

**Honest answer**:
- **Still O basin.** SI defines O = s∈[1,5]. 1.39 is inside O. I was
  NOT claiming full escape.
- What we *have*: evidence of *beginning* escape in the last 2 ns —
  s↔z Pearson correlation went from -0.31 (t=4-6 ns, orthogonal) to
  +0.49 (t=8-10 ns, aligned). +0.49 is the classical activated-barrier
  signature: walker's motion along the path axis becomes correlated
  with motion perpendicular, which is how real barrier crossings look
  (the walker "drags" orthogonal coordinates as it climbs).
- What we *don't have*: stable occupancy at s > 2, so we can't claim
  true escape yet. It might also be a 2-ns fluctuation that will
  revert.
- **How 50 ns extension answers this**: if walker reaches s > 3 within
  25 ns, that's beyond thermal noise → real escape. If walker plateaus
  at s ≈ 1.4 for 15+ ns, the 2-ns jump was noise.
- **Bail-out rule**: if max s < 3 at 25 ns, abort 50 ns and go Phase 3
  (4HPX-seeded dual-walker).

### Q3: "SI '80' vs your 379.77 — FP-027 was a misread. How do I know you didn't misread again?"

**Honest answer**:
- Fair pushback. FP-027 is about me mis-interpreting SI; Yu is right
  to be skeptical of any new SI claim.
- The 379.77 comes from OUR derivation: `λ = 2.3 / MSD_adj`. Our
  MSD_adj is self-computed from our 15 reference frames (0.006056 nm²
  per-atom mean). 2.3 is the PLUMED rule-of-thumb from Branduardi 2007
  (also in PLUMED docs).
- We do NOT derive 379.77 from SI's "80" at all. SI's "80" is the
  number Osuna computed for THEIR path; it's not an input to our
  calculation.
- What SI's "80" MIGHT mean (unresolved ambiguity): summary.txt
  interprets it as total SD Å² (sum over 112 atoms, matches 0.85× our
  67.826 Å² total SD). That's plausible but not proven. Other reading
  (λ=80 nm⁻²) is what tripped FP-027 up.
- **Key defense**: regardless of how SI's "80" is read, our path CV is
  verified **independently** of SI via the CV audit (Slide 8). 4HPX, a
  Pf structure we didn't use to build the path, projects to s=14.91,
  matching the closed-state StTrpS (3CEP). Cross-species physics
  validates the CV, orthogonal to SI semantic ambiguity.

### Q4: "10-walker snapshots — did you actually use your eyes in PyMOL, or did you let a script pick?"

**Honest answer**:
- As of today (2026-04-16 evening), 10-walker selection hasn't been
  executed yet. Job 44008381 needs to complete first (2026-04-18+).
- Yu's directive (2026-04-09 transcript L2859): use eyes, not
  strided. I did NOT take this to mean "eyes ONLY with no scripting."
- Proposed workflow: (1) load COLVAR in Python, bin by (s, z) into
  ~20 bins, pick medoid per bin; (2) extract those frames from metad.xtc
  as PDB files; (3) open all in PyMOL simultaneously; (4) visually
  reject any that look too similar; (5) keep 10 structurally distinct.
- So: script narrows the candidates, eyes make the final decision.
- **What could weaken**: if script-suggested medoids all cluster in O
  because walker stayed there, eye-inspection step cannot rescue —
  we'd need actual PC/C frames (4HPX-seeded Phase 3).
- **Commitment**: I'll show Yu the script + list of candidate frames
  + PyMOL screenshot at next meeting; not just a list of frame indices.

### Q5: "Frame 8 of interpolated path — is it biophysically sensible, or just trust linear Cartesian interp?"

**Honest answer**:
- Frame 8 is NOT a physical intermediate — it's a linear Cartesian
  interpolation between 1WDW and 3CEP (at λ_interp = 7/14 = 0.5). Its
  biophysical realism is NOT established. I know this.
- SI treats frames 2-14 the same way — as reference coordinates for
  the path CV, not as physical structures the simulation must pass
  through. The walker navigates the real free-energy landscape; the
  reference path just defines s/z coordinates.
- Self-consistency: frame 8 projects to s=8.00 exactly (by
  construction). That confirms the CV math, not the physics of frame 8.
- **What would weaken this**: if frame 8 has steric clashes or
  unphysical torsions, the walker approaching s ≈ 8 might be forced
  through unphysical configurations just to match frame 8's coord
  pattern. But PLUMED's Kabsch at runtime removes rigid-body alignment,
  so only internal deformation matters, and linear interp mostly
  preserves local geometry if endpoints are similar enough (10.9 Å
  total RMSD, ~0.78 Å per Cα per adjacent frame — small enough that
  linear is OK).
- **Commitment**: if Phase 2 10-walker fails to reach PC, one
  debugging step is verifying frame 8 (and 5, 10) via energy
  minimization — do they relax to plausible conformations?

---

## 6E. FP-027 systemic fix — "how do I know you won't misread SI again?"

Yu can legitimately ask this. The answer must go beyond "I'll be more careful."

**Four concrete structural fixes**:

1. **PARAMETER_PROVENANCE.md** (new this week) — every numerical
   parameter now has a mandated source tag. Any SI re-reading starts by
   looking up the existing row. If my new reading contradicts the existing
   source tag, I MUST either provide evidence why the existing tag was
   wrong OR keep the existing interpretation.

2. **Codex adversarial review before diagnostic pivots** — this is what
   caught FP-027. Rule: any time I propose changing a significant parameter
   or CV based on new SI re-reading, run `/codex:adversarial-review` on the
   proposal before executing. Codex has no context from my conversation, so
   it can't fall for the same misread.

3. **Repo transcript as prior** — `.local_scratch/4.9 组会.md` is
   preserved. Yu's prior statements (e.g., alignment-method ambiguity,
   L381-387, flagged a week ago) are part of the context I must check
   before making fresh claims. Same for any project notes that already
   interpreted a number.

4. **Rule 21 added to failure-patterns.md**: "SI numeric
   re-interpretation must read this repo's existing notes first; user-
   confirmed facts are priors." This is now a hard rule I'm expected
   to follow going forward.

**Honest caveat**: these fixes don't prevent ALL forms of misread.
They prevent the specific pattern of "reinterpret SI without checking
what the repo already said." For wholly new SI content I haven't
touched before, the defense is #2 — run it past Codex before acting
on a big claim.

---

## Cold-read self-test

Read the 5 questions below. Time yourself: can you answer each out loud
in ≤ 90 seconds, including follow-ups?

1. "SIGMA_MIN=0.3 — where does 0.3 come from, what's the formula?"
   → 6A SIGMA_MIN + 6D Q1

2. "max s=1.393 — is that escape or still O basin?"
   → 6D Q2

3. "SI '80' vs your 379.77 — FP-027 was a misread. How do I know you
   didn't misread again?"
   → 6D Q3 + 6E

4. "10-walker snapshots — did you actually use your eyes in PyMOL?"
   → 6D Q4

5. "Frame 8 of interpolated path — is it biophysically sensible?"
   → 6D Q5

**Target**: 4/5 fluent, 1/5 rough = acceptable. 0-2/5 fluent = go back
and re-read. Time budget: 5 min total for the 5 questions.

---

## Quick reference card (print before meeting)

```
λ=379.77 nm⁻²:  2.3 / 0.006056 nm²  (per-atom MSD, SI-derived)
SIGMA=0.1 nm:   Cartesian seed (SI silent, our choice, 2× of FP-024 value)
SIGMA_MIN=0.3,0.005: 2% of path axis for s; above z-noise (our choice)
HEIGHT=0.628:   0.15 kcal/mol × 4.184 (SI-quote)
PACE=1000:      2 ps / 2 fs (SI-derived)
BIASFACTOR=10:  SI-quote
TEMP=350 K:     SI-quote, thermophile

max s=1.393:    still O basin (SI O=1-5); last 2 ns +0.49 corr = escape signature
4HPX → s=14.91: cross-species Pf/St match, path CV physically correct
SI "80":        total SD Å² (summary.txt), not λ. FP-027 misread caught by Codex.
```
