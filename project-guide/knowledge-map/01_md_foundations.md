# Chapter 01 — MD Foundations (Quick Reference)

**Audience**: You (Zhenpeng). You've spent 6 weeks in MD. This chapter is **not** a tutorial — it's a compressed reference so you can defend every choice in your stack.

**How to use**: Read once. When someone asks "why TIP3P and not TIP4P-D?", flip here. All sections end with a pros/cons paragraph and "when to depart from default".

---

## 1.1 The MD loop (30-second version)

```
for t in 1..N:
    F_i = -∇U(r_1, ..., r_N)          # force from force-field
    v_i(t+Δt/2) = v_i(t-Δt/2) + F_i/m_i · Δt     # velocity Verlet, half-step
    r_i(t+Δt)   = r_i(t) + v_i(t+Δt/2) · Δt      # position update
    apply thermostat (rescale v)       # NVT
    apply barostat (rescale box)       # NPT
    write frame every K steps          # trajectory
```

Time step Δt is set by the fastest motion resolved. With HMR (hydrogen mass repartitioning, m_H: 1.008 → ~4 u), we safely use 4 fs. Without HMR, 2 fs is the ceiling.

**You use**: 4 fs HMR for AMBER-side conventional MD; 2 fs (no HMR) for GROMACS + PLUMED MetaD (standard in Osuna SI).

---

## 1.2 Force fields — the core choice

A force field is U(r) = sum over bonded (bonds, angles, dihedrals, impropers) + non-bonded (vdW + electrostatics) terms with parameters fit to QM or experiment.

### Protein force fields
| FF | Year | Notes | When |
|----|------|-------|------|
| **AMBER ff14SB** | 2015 | What you use. Main-chain φ/ψ re-fit from QM; good for folded proteins | Default for catalytic enzymes; Osuna 2019 used it |
| AMBER ff19SB | 2020 | CMAP-corrected φ/ψ; arguably better for disordered regions | Pick this only if IDRs matter |
| CHARMM36m | 2016/2020 | Competitive with ff14SB; CMAP-based; NAMD-native | If comparing to GROMACS-CHARMM literature |
| OPLS-AA/M | 2015 | Jorgensen lab; different sidechain torsions | Rare in enzyme design community |
| Amber99SB-disp | 2018 | Paul Robustelli / DE Shaw; explicit disordered-protein fix | IDP-centric studies only |
| a99SB-ILDN | 2010 | Shaw lab; sidechain ILDN fix — superseded by ff14SB in practice | Legacy literature reproduction |

**Big picture**: Since ~2015 the community has converged on ff14SB (or ff19SB) + CHARMM36m as the safe defaults for globular proteins. Anything older (ff99, ff99SB) is deprecated. Deep-learning-force-fields (ANI, MACE, Allegro) exist but are not yet drop-in replacements for 500-ns MD of enzymes.

### Ligand force field
GAFF (General AMBER Force Field, Wang 2004) + RESP charges is the 2000s→2020s standard for small molecules in AMBER ecosystem. You used this for PLP.

**Alternatives**:
- **GAFF2** (Wang 2019) — modest torsion re-fit; should use GAFF2 if starting today. Compatible with ff14SB.
- **OpenFF** (Open Force Field, Wang 2020 / Sage 2.0) — community-open alternative, SMIRNOFF format. Increasingly dominant. Better parameterization transparency.
- **CGenFF** (Vanommeslaeghe 2010) — CHARMM side.
- **QM-derived charges**: RESP is AM1-BCC's more-accurate grandfather. RESP needs HF/6-31G* ESP. Use for PLP because it's a charged, conjugated system and needs care.

**Why PLP is subtle**: PLP-AEX is a charged, highly conjugated Schiff base covalent to Lys. GAFF's bond-stretch and torsion parameters around the C=N Schiff base are acceptable but imperfect. An expert would do a small QM/MM validation (see Ch 03).

---

## 1.3 Water models

| Model | Geometry | κ_isoT, D (self-diffusion) | Notes |
|-------|----------|----------------------------|-------|
| **TIP3P** | 3-site rigid, OPC-H-H | Known-wrong self-diffusion (~5.2 vs 2.3×10⁻⁹ m²/s experimental) | What you use. Osuna used it. Standard in AMBER |
| SPC/E | 3-site rigid | Better thermodynamics than TIP3P | CHARMM community legacy |
| TIP4P/2005 | 4-site (extra charge on M-site) | Closest to experimental density and diffusion | GROMACS-heavy groups |
| TIP4P-D | 4-site tuned for IDPs (Piana 2015) | Heavier dispersion to prevent IDP over-compaction | Pick this only if studying disordered proteins |
| OPC | 4-site (Izadi 2014) | Arguably best-all-around | Emerging default in AMBER |

**Why TIP3P for TrpB**: because the Osuna paper used it; you replicate. If you were starting de novo, TIP4P/2005 or OPC would be defensible but break comparison to published data.

---

## 1.4 Thermostats and barostats

**Thermostats** (target T):
- Berendsen — legacy; rescales velocities smoothly but produces **wrong ensemble** (not canonical). Never use for production. OK for equilibration.
- Langevin — adds friction γ + random force; exact canonical sampling. You use this in AMBER.
- Nosé-Hoover (and NH-chains) — deterministic, canonical. Standard in GROMACS.
- v-rescale (Bussi 2007) — stochastic velocity rescaling; fast + canonical. Excellent default. Your GROMACS MetaD uses this or NH.

**Barostats** (target P):
- Berendsen — equilibration only.
- Parrinello-Rahman — anisotropic, canonical (with some caveats). Standard for production NPT.
- C-rescale / stochastic cell rescaling (Bernetti 2020) — modern alternative; used in GROMACS ≥ 2021.

Your stack: v-rescale thermostat + Parrinello-Rahman (or C-rescale) barostat. Standard choice, no defense needed.

---

## 1.5 Long-range electrostatics

Cutoff-based electrostatics are wrong. Everyone uses PME (Particle Mesh Ewald, Darden 1993). Direct-space cutoff 10 Å, grid spacing ≤ 0.12 nm, order 4 splines. Your defaults are fine.

**Alternative**: Lennard-Jones PME (LJ-PME) — treats dispersion with Ewald too. Increasingly used; costs ~10% more. Not required for Osuna replication.

---

## 1.6 Constraints

- **SHAKE / LINCS**: constrain covalent bonds to hydrogens. Lets you use 2-fs time step.
- **HMR** (hydrogen mass repartitioning, Hopkins 2015): redistribute H mass to heavy atom → 4-fs time step. You use this on AMBER side.

Known issues: HMR subtly alters sidechain dynamics amplitudes at the 5–10% level — matters for very precise fluctuation measurements, negligible for conformational-change metadynamics.

---

## 1.7 The software ecosystem

| Software | Strength | Weakness | Your use |
|----------|---------|----------|----------|
| **AMBER 24 (pmemd.cuda)** | Fastest GPU implementation; best for large protein MD; TI/FEP well-developed | Closed source (partial); AMBER file ecosystem | Conventional 500 ns MD |
| **GROMACS 2026** | Open source; excellent performance; PLUMED integration | AMBER force field translation layer imperfect | MetaD with PLUMED |
| **OpenMM** | Python-first; custom forces easy; research-friendly | Slower than GROMACS/AMBER for large systems (but narrowing) | Lab's GenSLM infra (not used by you) |
| **NAMD** | Scales to petascale; best for huge systems (>1M atoms) | Slower than GROMACS for small systems | Not used in this project |
| **Desmond / Anton** | Proprietary; Anton is custom hardware (DE Shaw, microsecond ~ overnight) | Cost; closed | Not available to student |

**Critical subtlety you should know**: GROMACS 2026 + PLUMED compatibility required source-building PLUMED 2.9.2 because conda's libplumedKernel.so was incomplete. This is FP-020 in your failure-pattern log. Don't forget this when asked "why not just conda install".

---

## 1.8 Equilibration protocols (standard)

After tleap builds your system:

1. **EM (energy minimization)** — steepest descent + L-BFGS, <10⁻² kJ/mol/nm gradient. Remove atomic clashes. ~5 min wall.
2. **NVT heating** — restraint protein heavy atoms (k = 1000 kJ/mol/nm²), ramp T from 0 → 350 K over 100-500 ps. v-rescale or Langevin.
3. **NPT equilibration** — release restraints in 2-3 stages over 500-1000 ps. Volume relaxes.
4. **Production** — remove all restraints. Start recording. For MetaD, this is when PLUMED kicks in.

Total equilibration: ~2-3 ns for a 40k-atom system. Your Osuna replication protocol does this.

---

## 1.9 Analysis zoo (names to know)

**Geometric**:
- RMSD — root-mean-square deviation to reference; measures overall motion
- RMSF — root-mean-square fluctuation per atom; reveals flexibility
- SASA — solvent-accessible surface area; pocket burial
- Radius of gyration (Rg) — global compactness
- Native contacts fraction (Q) — fraction of close-contact pairs preserved vs reference

**Temporal/statistical**:
- Autocorrelation function ⟨X(0)·X(t)⟩ — characteristic relaxation times
- Block averaging — uncertainty quantification accounting for correlation
- PCA / Essential dynamics (Amadei 1993) — dominant linear modes
- **tICA** (time-lagged ICA, Pérez-Hernández 2013) — slow-mode identification; **always prefer over PCA** for conformational change analysis
- MSM (Markov state model, Pande / Noé / Chodera) — rigorous kinetic framework
- Committor / splitting probability — Bayesian "is this frame on its way to state A or B?"

**Free energy**:
- Umbrella sampling + WHAM/MBAR — rigorous PMF along known CV
- Metadynamics reweighting — recover PMF from bias trajectory
- Alchemical FEP/TI — ligand binding ΔG; not relevant to your current work

---

## 1.10 Pros/cons summary — what your stack is good at, what it isn't

**You are using, basically, the 2015-vintage consensus stack + PLUMED for MetaD.**

**Strengths**:
- Maximum defensibility — every choice has a citation. Osuna's JACS 2019 uses the same stack.
- Reproducibility — frozen manifest ensures others can reproduce.
- GPU-efficient — pmemd.cuda is near peak silicon efficiency.
- Amin, Yu, Raswanth all know this stack by name.

**Weaknesses**:
- TIP3P has known water-diffusion artifacts. TIP4P-D or OPC would be incrementally better, but break replication comparison.
- GAFF1 for PLP is "OK" not "state of the art". OpenFF or DFT-derived parameters would be incrementally better.
- No QM/MM. For D/L selectivity discussion you cannot simulate bond-breaking — the Schiff base and quinonoid protonation step is pure QM territory. This is an inherent limit of classical MD and must be acknowledged.
- 350 K is above physiological for most enzymes; defensible for P. furiosus thermophile, marginal if anyone redesigns for mesophilic hosts.
- Finite-size effects — 40k atoms with ~0.6 nm buffer is small for a protein dimer; if the protein drifts near the PBC image, artifacts creep in. You've checked this (system-build validation).

**When your stack breaks**:
- Bond formation/breaking (Schiff base chemistry, proton transfer)
- Electronic polarization (strong in charged systems like PLP-Lys)
- Very slow conformational changes (>10 μs) — Anton territory
- IDP equilibria (needs TIP4P-D + a99SB-disp or CHARMM36m-d)

---

## 1.11 Videos / tutorials for re-grounding

Fast reference material if you need to refresh:

- **Alessandra Magistrato / Giovanni Bussi — "Molecular Dynamics: Theory and Applications"** (ICTP lectures, YouTube). Good intro to integrators, thermostats.
- **GROMACS tutorial by Justin Lemkul** (free online at mdtutorials.com / YouTube) — widely used teaching material; Lysozyme-in-water walk-through.
- **Bussi lab metadynamics lectures** (YouTube) — covers PLUMED from basics.
- **AMBER tutorial series** (ambermd.org/tutorials) — written not video but canonical.

For citation arithmetic and software choices, the **Best Practices articles from LiveCoMS** (Living Journal of Computational Molecular Science) are gold. Search "LiveCoMS Best Practices MD".

---

## 1.12 "If someone asks me X, I say Y"

- **Q**: Why TIP3P and not OPC? 
  **A**: We replicate Osuna 2019 which used TIP3P. OPC or TIP4P-D would be marginally more accurate but breaks benchmark comparison. Water-dynamics artifacts from TIP3P are well-characterized and do not dominate the protein slow modes we care about.

- **Q**: Why 350 K? 
  **A**: TrpB is from *Pyrococcus furiosus*, a thermophile with T_opt ~ 100 °C. The Osuna group chose 350 K as a compromise between physiological (~370 K) and standard MD practice (300 K). We replicate.

- **Q**: Why AMBER for conventional MD and GROMACS for MetaD?
  **A**: pmemd.cuda is the fastest GPU code. For MetaD, we need PLUMED, and PLUMED has best integration with GROMACS. ParmEd converts topologies bit-exact between ecosystems. Cross-validated with identical energy traces.

- **Q**: Why not OpenMM everywhere?
  **A**: Performance. For a 40k-atom system and 500 ns, AMBER pmemd.cuda is ~1.5-2x faster than OpenMM on A100. The lab uses OpenMM for design-pipeline ML inference where custom forces matter; for production MD, AMBER wins.

- **Q**: Why not QM/MM?
  **A**: We are studying the conformational-change (O→C) timescale, not the chemistry (bond-breaking) step. MM is rigorous for this regime. Chemistry would need QM/MM (e.g. ONIOM, AMBER-ORCA) and is a different study.

- **Q**: Couldn't you use ML force fields (MACE-MP, Allegro)?
  **A**: Not yet at scale for 500 ns + 40k atoms. MACE-MP-0 can do small molecules at this scale but protein + solvent at ns/day is still in the 10-20 range for MACE — more than 10x slower than AMBER. And MACE-MP for PLP has not been validated for catalysis. This is a 2027-2028 bet, not 2026.

---

**Next**: Chapter 02 (Enhanced sampling landscape) — where metadynamics sits among all the rare-event sampling options, and whether your choice of PATHMSD + WTMetaD is still optimal or if OPES/WE would beat it.
