# MetaDynamics Setup Files Index

> **Project**: TrpB MetaDynamics Replication (JACS 2019)
> **Date**: 2026-03-28
> **Reference**: Maria-Solano et al., JACS 2019, 141, 13049–13056

This directory contains all files needed to set up and run well-tempered metadynamics simulations on Longleaf HPC.

---

## Files Overview

### 1. PLUMED Templates (WTMetaD input)

| File | Purpose | When to use |
|--|--|--|
| **plumed_trpb_metad.dat** | Multi-walker well-tempered MetaD (10 replicas) | Production runs (50–100 ns per walker × 10) |
| **plumed_trpb_metad_single.dat** | Single-walker exploration (quick validation) | Initial ~20 ns test to verify setup |

**Key parameters** (from JACS 2019 SI):
- Path CVs: s(R) = progress along O→C, z(R) = deviation from path
- Well-tempered MetaD: HEIGHT=0.628 kJ/mol, PACE=1000 (2 ps), BIASFACTOR=10
- Temperature: 350 K (thermophilic enzyme *Pf*TrpB)
- Atoms: Cα of residues 97–184 (COMM) + 282–305 (base)

**What to do**:
1. Replace `[PLACEHOLDER_*]` with actual atom indices from your GROMACS topology
2. Generate 15-frame reference path (O→C) from 1WDW and 3CEP structures
3. Use `plumed_trpb_metad_single.dat` for initial 50 ns test
4. Use `plumed_trpb_metad.dat` for 10-walker production

---

### 2. PLP Parameterization (Force field setup)

| File | Purpose | When to use |
|--|--|--|
| **parameterize_plp.sh** | Automation script for all 4 intermediates | Generate AMBER topology files |
| **README_plp_param.md** | Detailed guide with troubleshooting | Understand each step of parameterization |

**Intermediates** (4 catalytic states):
- **Ain**: Internal aldimine (resting state)
- **Aex1**: External aldimine 1 (L-Ser bound)
- **A-A**: Aminoacrylate (awaits indole)
- **Q₂**: Quinonoid 2 (post-coupling)

**Workflow** (antechamber → Gaussian → parmchk2 → tleap):
1. Extract PLP from PDB files
2. Assign GAFF atom types via antechamber
3. Optimize geometry + compute RESP charges in Gaussian09 (manual, HF/6-31G(d))
4. Generate missing force field parameters with parmchk2
5. Build solvated systems with tleap

**What to do**:
1. Run `bash parameterize_plp.sh` (creates directories + templates)
2. Complete Gaussian optimizations (off-site or on queue)
3. Re-extract RESP charges and regenerate MOL2 files
4. Execute `bash parameters/run_all_tleap.sh` to finalize topologies

---

## Typical Workflow

### Phase 1: Preparation (Weeks 1–2)

```
1. Run parameterize_plp.sh
   └─ Generates MOL2 + tleap scripts for all 4 intermediates

2. Gaussian09 RESP optimization (manual)
   └─ HF/6-31G(d) geometry opt + ESP charges

3. Complete force field setup
   └─ Run tleap → get .parm7 + .inpcrd for each intermediate

4. Generate reference path (1WDW → 3CEP)
   └─ Linear interpolation, 15 frames
```

### Phase 2: Testing (Weeks 2–3)

```
1. Conventional MD (500 ns per intermediate)
   └─ Using AMBER: pmemd.cuda, ff14SB, TIP3P, 350 K

2. Single-walker MetaD test (~20–50 ns)
   └─ Using plumed_trpb_metad_single.dat
   └─ Verify path CV convergence

3. Validate FES landscape
   └─ Check for O and C minima
   └─ Assess z(R) values (should be low = on-path)
```

### Phase 3: Production (Weeks 3–6)

```
1. Multi-walker MetaDynamics (10 replicas)
   └─ Using plumed_trpb_metad.dat
   └─ 50–100 ns per walker = 500–1000 ns total

2. Reconstruct FEL
   └─ plumed sum_hills --hills HILLS --out fes.dat

3. Analyze metastable states
   └─ Cluster O, PC, C conformations
   └─ Compute transition barriers
```

---

## Environment Setup

### Longleaf HPC (UNC)

```bash
# Load modules
module load amber/24p3           # AMBER 24p3
conda activate trpb-md           # PLUMED 2.9, GROMACS 2026.0

# Check installation
which antechamber              # should be in $AMBER/bin
which tleap                    # should be in $AMBER/bin
which gmx                      # GROMACS with PLUMED support
plumed --version               # should be 2.9
```

### Project Directory

```
/work/users/l/i/liualex/AnimaLab/
├── structures/               # PDB files (1WDW, 3CEP, 5DVZ, 5DW0, 5DW3, etc.)
├── parameters/               # Force field files (GAFF, RESP, frcmod)
├── scripts/                  # This directory (PLUMED inputs, parameterization)
├── runs/                     # Simulation output directories
├── logs/                     # SLURM and tool logs
└── analysis/                 # FES, trajectory analysis
```

---

## Quick Reference

### Replacing Placeholders

In `plumed_trpb_metad.dat` and `plumed_trpb_metad_single.dat`:

```bash
# Extract atom indices from topology
gmx dump -s topol.tpr 2>&1 | grep -A 2 "K82\|Q2\|E104\|residue 97\|residue 282"

# Update placeholders:
# [PLACEHOLDER_K82_N_ATOM_INDEX]     → e.g., 1234
# [PLACEHOLDER_Q2_C_ATOM_INDEX]      → e.g., 5678
# [PLACEHOLDER_E104_OE_ATOM_INDEX]   → e.g., 3456
# [PLACEHOLDER_FRAME_LIST]           → path to frame_*.pdb files
# [PLACEHOLDER_COMM_ATOM_LIST]       → atom indices for residues 97–184
```

### Key Parameters from Paper

| Parameter | Value | Note |
|--|--|--|
| HEIGHT | 0.628 kJ/mol | = 0.15 kcal/mol from SI |
| PACE | 1000 steps | = 2 ps at dt=0.002 |
| BIASFACTOR | 10 | Effective temp = 350 × 10 = 3500 K |
| TEMP | 350 K | Thermophilic organism |
| SIGMA (path) | Adaptive | Auto-tunes to local FES |
| λ | 0.029 | Path CV Gaussian width |
| Walkers | 10 | Parallel replicas |

---

## Files Generated

### After parameterize_plp.sh:

```
parameters/
├── plp_structures/           # Extracted PLP from PDB
│   ├── Ain_plp.pdb
│   ├── Aex1_plp.pdb
│   ├── A-A_plp.pdb
│   └── Q2_plp.pdb
├── mol2/                     # GAFF atom types
│   ├── *_gaff.mol2           # Initial (BCC charges)
│   └── *_resp.mol2           # After RESP optimization
├── resp_charges/             # Gaussian09 templates
│   ├── Ain_opt.com
│   ├── Aex1_opt.com
│   ├── A-A_opt.com
│   └── Q2_opt.com
├── frcmod/                   # Missing parameters
│   ├── Ain.frcmod
│   ├── Aex1.frcmod
│   ├── A-A.frcmod
│   └── Q2.frcmod
└── tleap_inputs/             # System assembly
    ├── Ain_build.in
    ├── Aex1_build.in
    ├── A-A_build.in
    ├── Q2_build.in
    └── *_complete.parm7 + .inpcrd (final outputs)
```

### After MetaDynamics runs:

```
runs/
├── single_test/              # Single-walker validation
│   ├── COLVAR                # s, z vs time
│   ├── HILLS                 # Bias potentials
│   ├── traj.xtc              # Trajectory
│   └── fes.dat               # Reconstructed FEL
└── multi_walker/             # Production (10 walkers)
    ├── walker_0/, walker_1/, ...
    │   ├── COLVAR
    │   ├── HILLS
    │   └── traj.xtc
    └── fes_combined.dat      # Final FEL (all walkers summed)
```

---

## References

1. **JACS 2019**: Maria-Solano et al., *JACS* 2019, **141**, 13049–13056
   - DOI: 10.1021/jacs.9b03646
   - SI: ja9b03646_si_001.pdf

2. **PLUMED**: Tribello et al., *Comput Phys Commun* 2014, **185**, 604–613

3. **MetaDynamics**: Laio & Parrinello, *PNAS* 2002, **99**, 12562–12566

4. **AMBER/GAFF**: Wang et al., *J Comput Chem* 2004, **25**, 1157–1174

5. **RESP**: Bayly et al., *J Phys Chem* 1993, **97**, 10269–10280

---

## Contact

- **Author**: Zhenpeng Liu (liualex@ad.unc.edu)
- **Lab**: Anima Lab, Caltech (summer research position)
- **HPC**: UNC Longleaf (liualex@longleaf.unc.edu)
- **Created**: 2026-03-28
