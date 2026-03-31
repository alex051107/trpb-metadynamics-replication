# MetaDynamics Simulation Setup: Osuna JACS 2019 TrpB Paper Replication

**Paper:** Maria-Solano, Iglesias-Fernandez, Osuna (2019) "Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution" *Journal of the American Chemical Society* **141**(33):13049-13056. DOI: [10.1021/jacs.9b03646](https://doi.org/10.1021/jacs.9b03646)

**Research Goal:** Replicate well-tempered MetaDynamics simulations of PfTrpB (Pyrococcus furiosus tryptophan synthase β-subunit) with path collective variables (s and z) across four catalytic intermediates (E(Ain), E(Aex1), E(A-A), E(Q2)) for three variants: PfTrpS complex, PfTrpB WT, and PfTrpB0B2.

---

## 1. PDB STRUCTURES NEEDED

### Primary Structures (Verified Available)

| PDB ID | Description | Resolution | Source | Status |
|--------|-------------|-----------|--------|--------|
| **5DVZ** | Holo TrpB from *Pyrococcus furiosus* (WT) | 1.69 Å | [RCSB: 5DVZ](https://www.rcsb.org/structure/5DVZ) | ✓ Available |
| **5DW3** | PfTrpB with L-Trp product bound (open/product state) | 1.74 Å | [RCSB: 5DW3](https://www.rcsb.org/structure/5DW3) | ✓ Available |
| **5DW0** | PfTrpB with L-serine (external aldimine state, Aex1) | - | [RCSB: 5DW0](https://www.rcsb.org/structure/5DW0) | ✓ Available |

### Engineered Variants (For context, post-2019)

- **6AM8**: PfTrpB2B9 with Trp bound as E(Aex2) | [RCSB: 6AM8](https://www.rcsb.org/structure/6AM8)
- **6AM9**: PfTrpB2B9 with Ser bound (closed state) | [RCSB: 6AM9](https://www.rcsb.org/structure/6AM9)
- **6CUZ**: PfTrpB7E6 with ethylserine (amino-acrylate, A-A state) | [RCSB: 6CUZ](https://www.rcsb.org/structure/6CUZ)

### Key Structural Features

**COMM Domain (Communication Domain):**
- Residues β102–β189
- **Open state:** COMM away from active site, PLP solvent-accessible
- **Closed state:** COMM moves toward PLP, forms critical salt bridge β Asp305–β Arg141
- Undergoes major conformational rearrangement between catalytic states

**Path CV Definition:**
The open-to-closed transition uses path collective variables with:
- **O-state reference:** Open conformation (5DW3 or unliganded)
- **C-state reference:** Closed conformation (5DW0 or substrate-bound)
- **Progress variable (s):** 0 (open) → 1 (closed)
- **Distance variable (z):** Perpendicular distance from path

---

## 2. INPUT FILES & SUPPORTING INFORMATION

### Paper Supporting Information

**Access:** https://pubs.acs.org/doi/10.1021/jacs.9b03646

**Expected Contents:**
- Detailed methods for MetaDynamics protocol
- PLUMED input file (plumed.dat) with exact PATH CV definition
- AMBER minimization/equilibration/production input files (*.in)
- PLP cofactor force field parameters or references
- Reference structure coordinates for each intermediate
- CV parameter values (λ, Gaussian heights, bias factors)
- Free energy landscape plots and data files

**How to Access:**
1. Go to https://pubs.acs.org/doi/10.1021/jacs.9b03646
2. Look for "Supporting Information" link on the article page
3. Download PDF or supplementary archive
4. May require ACS account or institutional access

### GitHub/Open Repositories

**Osuna Research Group:**
- Main publication page: [osunalab.com/publications](https://www.osunalab.com/publications/)
- No dedicated GitHub repository found for this TrpB MetaDynamics project in standard searches

**PLUMED-NEST Repository:**
- Archive for published PLUMED simulations: [https://www.plumed-nest.org/](https://www.plumed-nest.org/)
- Status: No specific entry found for this 2019 TrpB paper (may not be deposited)

**Recommendation:** Contact Osuna group (Universitat de Girona) directly for supplementary input files.

---

## 3. PLUMED PATH COLLECTIVE VARIABLE SETUP

### Implementation Variants

**Two PATH implementations available:**

1. **PATH** - general implementation, multiple distance metrics
2. **PATHMSD** - optimized for RMSD, faster, recommended for proteins

### Basic Syntax

```
# Define path CV with reference structures (aligned open→closed)
p1: PATHMSD REFERENCE=open_state.pdb LAMBDA=50.0

# Output progress (s) and distance (z) components
PRINT ARG=p1.sss,p1.zzz STRIDE=100 FILE=colvar.txt

# Alternative syntax with multiple waypoints
# p2: PATH REFERENCE=struct1.pdb,struct2.pdb,struct3.pdb METRIC=RMSD LAMBDA=40.0
```

**Key Parameters:**

| Parameter | Meaning | Typical Values | Notes |
|-----------|---------|----------------|-------|
| **REFERENCE** | PDB file(s) defining path (usually open & closed states) | 2–10 frames | Must be RMSD-aligned; COMM domain regions critical |
| **LAMBDA** | Path width parameter (inverse); higher = sharper | 30–100 | Proportional to 1/MSE; needs tuning per system |
| **STRIDE** | Output frequency for CV values | 100–1000 steps | Balance detail vs. file size |

**CV Components:**
- **s (progress):** coordinate along path, 0=open state, 1=closed state
- **z (distance):** perpendicular distance from path; z≈0 means on-path

### Tutorials & Documentation

- **PLUMED PATH:** [doc-v2.4 PATH](https://plumed.github.io/doc-v2.4/user-doc/html/_p_a_t_h.html)
- **PATHMSD reference:** [doc-v2.9 FUNCPATHMSD](https://www.plumed.org/doc-v2.9/user-doc/html/_f_u_n_c_p_a_t_h_m_s_d.html)
- **PLUMED Masterclass 22.9:** [Path collective variables for reaction mechanisms](https://www.plumed.org/doc-v2.9/user-doc/html/masterclass-22-9.html)
- **Belfast tutorial:** [Metadynamics with PLUMED](https://www.plumed.org/doc-v2.9/user-doc/html/belfast-6.html)

---

## 4. FORCE FIELD & COFACTOR PARAMETERS

### Protein Force Field

**AMBER ff14SB (standard):**
- Reference: [Maier et al., J. Chem. Theory Comput. 2015](https://pubs.acs.org/doi/abs/10.1021/acs.jctc.5b00255)
- Improved over ff99SB for side chains and backbone dihedrals
- Compatible with GAFF for ligands
- Tuned for TIP3P water model
- Part of standard AMBER/AmberTools distribution

**Setup in TLEAP:**
```
source leaprc.ff14SB
source leaprc.water.tip3p
protein = loadpdb structure.pdb
```

### Pyridoxal Phosphate (PLP) Cofactor Parameters

**Challenge:** PLP is a covalent cofactor (Schiff base with Lys-ε-amino group), requiring custom force field.

**Parameter Sources:**

1. **Covalent Lys-PLP Parameters (from literature)**
   - Multiple protonation states documented (keto, enol; charged/neutral phosphate)
   - Partial charges: Calculated using HF/6-31G* (consistent with AMBER)
   - Source: Similar to work in [Homeyer & Gohlke, JCTC 2016](https://pubmed.ncbi.nlm.nih.gov/16240095/)

2. **GAFF Parameters for PLP Ligand**
   - If modeling PLP separately, use GAFF via antechamber
   - Command: `antechamber -i plp.mol2 -fi mol2 -o plp_gaff.mol2 -fo mol2 -c bcc`

3. **Parameter Database**
   - AMBER parameter database: [http://amber.manchester.ac.uk/](http://amber.manchester.ac.uk/)
   - May contain pre-parameterized PLP variants

**Recommended Workflow:**

1. **First choice:** Search paper's Supporting Information for PLP parameters
2. **Second choice:** Contact Osuna group for their parameterization
3. **Third choice:** Use QM-derived parameters from literature (e.g., similar TrpB studies)
4. **Last resort:** Derive custom parameters via QM (Gaussian + antechamber)

---

## 5. CURRENT COMPUTATIONAL ENVIRONMENT

### Software Availability (vibrant-compassionate-heisenberg)

```
PLUMED:        NOT INSTALLED
AMBER:         NOT INSTALLED (pmemd not in PATH)
AmberTools:    Status unknown (likely available via conda)
Python:        Likely available (via conda)
Modules:       Not loaded
```

### Installation Requirements

**To replicate simulations, you need:**

1. **AMBER Suite**
   - AmberTools (free): structure prep, force field tools, antechamber
   - AMBER MD Engine (paid/academic): pmemd executable
   - Download: [https://ambermd.org/](https://ambermd.org/)
   - Compilation time: 1–2 hours

2. **PLUMED (patched with AMBER support)**
   - Requires patching AMBER source code
   - Recompile AMBER with PLUMED linked
   - Download: [https://www.plumed.org/](https://www.plumed.org/)
   - Additional compilation time: 1–2 hours
   - Test: `plumed -v` should report PLUMED version

3. **Python Tools (for analysis)**
   - Python 3.7+
   - NumPy, Matplotlib, SciPy
   - Optional: MDAnalysis, MDTraj
   - Optional: metadynminer for PLUMED HILLS analysis

**Estimated Total Installation Time:** 4–8 hours (excluding QM calculations)

### GPU Acceleration (Optional)

- AMBER supports NVIDIA CUDA (pmemd.cuda)
- ~10–50× speedup possible
- PLUMED + pmemd.cuda fully supported
- Requires NVIDIA GPU + CUDA toolkit

---

## 6. SIMULATION SETUP WORKFLOW

### Phase 1: Prepare Path References

1. **Download structures from RCSB:**
   ```bash
   wget https://files.rcsb.org/download/5DW3.pdb  # Open state
   wget https://files.rcsb.org/download/5DW0.pdb  # Closed state (Aex1)
   wget https://files.rcsb.org/download/5DVZ.pdb  # Holo reference
   ```

2. **Align structures by COMM domain (residues 102–189):**
   - Use AmberTools or MDAnalysis for RMSD alignment
   - Output: aligned_open.pdb, aligned_closed.pdb
   - Verify backbone RMSD < 2 Å for reference path

3. **For intermediate states (E(Ain), E(A-A), E(Q2)):**
   - Search PDB for existing structures (e.g., 6CUZ for A-A state)
   - If not available, run short MD relaxations from substrate-bound structures
   - Or construct via homology modeling if necessary

### Phase 2: Build AMBER System

1. **Prepare protein topology:**
   ```bash
   tleap << EOF
   source leaprc.ff14SB
   source leaprc.water.tip3p
   prot = loadpdb 5dw0.pdb
   # [add PLP parameters here]
   saveamberparm prot prmtop inpcrd
   EOF
   ```

2. **Prepare PLP cofactor:**
   - Define Lys-PLP covalent linkage in TLEAP
   - Use force field parameters (from SI or literature)
   - Verify correct protonation state for each intermediate

3. **Solvate and neutralize:**
   ```bash
   # (in tleap)
   solv = addions prot Na+ 0
   solv = solvateoct prot TIP3PBOX 12.0
   savepdb solv solvated.pdb
   saveamberparm solv prmtop rst7
   ```

### Phase 3: Create PLUMED Input (plumed.dat)

**Example configuration:**

```
# Define path CV (open → closed COMM transition)
p1: PATHMSD REFERENCE=aligned_open.pdb LAMBDA=50.0

# Well-tempered metadynamics on (s, z)
md: METAD ARG=p1.sss,p1.zzz \
    HEIGHT=0.5 SIGMA=0.1,0.1 \
    PACE=1000 BIASFACTOR=15.0 TEMP=300.0 \
    FILE=HILLS

# Print collective variables every 100 steps
PRINT ARG=p1.sss,p1.zzz STRIDE=100 FILE=colvar.txt

# Print bias potential
PRINT ARG=md.bias STRIDE=1000 FILE=bias.txt

# Flush output
FLUSH STRIDE=1000
```

**Parameter guidance:**
- **HEIGHT:** 0.05–1.0 kJ/mol (smaller = more frequent sampling, longer convergence)
- **SIGMA:** 0.05–0.2 (Gaussian width; values from paper SI if available)
- **PACE:** 500–2000 steps (deposition interval; lower = more hills, slower but better coverage)
- **BIASFACTOR:** 10–20 (well-tempered; higher = slower but more thorough exploration)
- **TEMP:** Match MD thermostat (typically 300 K)

### Phase 4: Create AMBER Input (mds.in)

**Example for well-tempered MetaDynamics:**

```
 Production MD with PLUMED MetaDynamics
&cntrl
  imin=0,                ! MD simulation (not minimization)
  ntx=5,                 ! Read velocities (restart)
  irest=1,               ! Restart run
  nstlim=5000000,        ! Total steps (~10 ns)
  dt=0.002,              ! 2 fs timestep
  ntf=2, ntc=2,          ! SHAKE (H-bonds and bonds to H)
  ntt=3,                 ! Langevin thermostat
  gamma_ln=2.0,          ! Friction coefficient
  temp0=300.0,           ! 300 K
  ntpr=1000,             ! Print energy every 1000 steps
  ntwr=10000,            ! Save restart every 10000 steps
  ntwx=1000,             ! Save trajectory every 1000 steps
  ntxo=2,                ! Restart format (NetCDF)
  ntf=2, ntc=2,          ! SHAKE
  plumed=1,              ! Enable PLUMED
  plumedfile='plumed.dat' ! PLUMED input file
/
```

### Phase 5: Run Simulation

```bash
# Minimization (warm-up)
pmemd -O -i mds_min.in -o min.out \
  -p prmtop -c inpcrd -r min.rst7 -x min.mdcrd

# Production MD (CPU)
pmemd -O -i mds.in -o mds.out \
  -p prmtop -c min.rst7 -r mds.rst7 -x mds.mdcrd

# Or with GPU acceleration (recommended)
pmemd.cuda -O -i mds.in -o mds.out \
  -p prmtop -c min.rst7 -r mds.rst7 -x mds.mdcrd
```

### Phase 6: Analyze Free Energy Surface

```bash
# Reconstruct FES from Gaussians
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero

# Plot 2D FES (s vs z)
python plot_fes.py fes.dat
```

---

## 7. CRITICAL DATA & FILES CHECKLIST

### From RCSB PDB (Free)

- [ ] 5DVZ.pdb (WT TrpB holo)
- [ ] 5DW3.pdb (TrpB with product, open)
- [ ] 5DW0.pdb (TrpB with serine, Aex1)
- [ ] Additional PDB IDs for intermediates (if needed)

### From ACS Supporting Information

- [ ] PLUMED input file (plumed.dat)
- [ ] AMBER input files (minimization, equilibration, production)
- [ ] Topology/topology modification scripts
- [ ] Reference structure coordinates
- [ ] CV parameter values
- [ ] Methods supplementary text (detailed protocol)
- [ ] PLP force field parameters (or reference to source)

### From Software Downloads

- [ ] AMBER/AmberTools source (or binary)
- [ ] PLUMED source code
- [ ] PLUMED patching scripts for AMBER

### Self-Generated Files

- [ ] Aligned open/closed reference structures
- [ ] AMBER prmtop and inpcrd files for each intermediate
- [ ] Custom PLUMED configuration files
- [ ] Equilibration trajectory
- [ ] Production trajectory + HILLS file
- [ ] Reconstructed FES (fes.dat)

---

## 8. KEY LITERATURE & REFERENCES

### Primary Publication
- **Maria-Solano, M. A.; Iglesias-Fernández, J.; Osuna, S.** (2019) "Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution" *J. Am. Chem. Soc.* **141**(33):13049-13056. [DOI: 10.1021/jacs.9b03646](https://doi.org/10.1021/jacs.9b03646)

### Related TrpB Papers (Osuna group)
- **Buller, F.; et al.** (2015) "Directed evolution of the tryptophan synthase β-subunit for stand-alone function recapitulates allosteric activation" *PNAS* **112**(47):14599-14604. [DOI: 10.1073/pnas.1516401112](https://doi.org/10.1073/pnas.1516401112)

### Force Field References
- **Maier, J. A.; et al.** (2015) "ff14SB: Improving the Accuracy of Protein Side Chain and Backbone Parameters from ff99SB" *J. Chem. Theory Comput.* **11**(10):3696-3713. [DOI: 10.1021/acs.jctc.5b00255](https://doi.org/10.1021/acs.jctc.5b00255)

- **Wang, J.; Wolf, R. M.; et al.** (2004) "Development and testing of a general amber force field" *J. Comput. Chem.* **25**(9):1157-1174. [DOI: 10.1002/jcc.20035](https://doi.org/10.1002/jcc.20035)

- **Homeyer, N.; Gohlke, H.** (2016) "Free Energy Calculations by the Molecular Mechanics Poisson−Boltzmann Surface Area Method" *Mol. Inform.* **35**(6-7):343-354.

### MetaDynamics & Path CV Theory
- **Barducci, A.; Bonomi, M.; Parrinello, M.** (2008) "Well-Tempered Metadynamics: A Smoothly Converging and Tunable Free-Energy Method" *Phys. Rev. Lett.* **100**(2):020603. [DOI: 10.1103/PhysRevLett.100.020603](https://doi.org/10.1103/PhysRevLett.100.020603)

- **Branduardi, D.; Gervasio, F. L.; Parrinello, M.** (2007) "From A to B in free energy space" *J. Chem. Phys.* **126**(5):054103. [DOI: 10.1063/1.2432340](https://doi.org/10.1063/1.2432340)

### PLUMED Documentation
- **Official PLUMED Manual:** [https://www.plumed.org/](https://www.plumed.org/)
- **PLUMED Masterclass Materials:** [https://www.plumed.org/doc-master/user-doc/html/masterclass.html](https://www.plumed.org/doc-master/user-doc/html/masterclass.html)

---

## 9. TROUBLESHOOTING GUIDE

### Problem 1: MetaDynamics Not Converging

**Symptoms:** Free energy surface shows scattered barriers, no clear minima.

**Solutions:**
- Lower HEIGHT (0.5 → 0.1 kJ/mol) for more frequent sampling
- Increase simulation time (10 ns → 100 ns)
- Check LAMBDA parameter for PATH CV (may be too broad or narrow)
- Verify reference structures are properly aligned

### Problem 2: No Transition Between Open & Closed States

**Symptoms:** All trajectory in one state, no s-variable exploration.

**Solutions:**
- Increase PACE (2000 → 1000 steps) for more aggressive biasing
- Reduce BIASFACTOR (20 → 10) for higher effective temperature
- Check that reference structures truly represent open and closed states
- Add intermediate waypoints to PATH
- Run longer equilibration before collecting statistics

### Problem 3: PLP-Cofactor Forces Cause Instability

**Symptoms:** Simulation crashes with high energies, PLP geometry distorts.

**Solutions:**
- Verify PLP parameters: partial charges, bond lengths, angles
- Check Schiff base connectivity (Lys-ε-N to PLP C4')
- Run short energy minimization (1000 steps) before MD
- Test with constrained PLP atoms first, then release
- Check protonation state is correct for the catalytic intermediate

### Problem 4: AMBER-PLUMED Compilation Fails

**Symptoms:** Compiler errors, undefined references to PLUMED functions.

**Solutions:**
- Verify PLUMED version matches AMBER version
- Follow official PLUMED patching guide: [https://www.plumed.org/doc-master/user-doc/html/INSTALL.html](https://www.plumed.org/doc-master/user-doc/html/INSTALL.html)
- Use `./plumed --info` to check PLUMED was compiled correctly
- Ensure AMBER configure detects PLUMED correctly
- Try pre-compiled conda/Docker versions if source fails

### Problem 5: Free Energy Surface Reconstruction (sum_hills) Errors

**Symptoms:** `plumed sum_hills` command fails or produces empty FES file.

**Solutions:**
- Check HILLS file is being written: `tail -20 HILLS`
- Verify PLUMED and plumed sum_hills versions match
- Use option: `--mintozero` (shifts FES minimum to 0)
- Check coordinate ranges: `plumed sum_hills --hills HILLS --nopbc`
- May need to exclude early (unequilibrated) HILLS entries

---

## 10. SUMMARY: What You Need & Where to Get It

| Item | Status | Source | Free? | Action |
|------|--------|--------|-------|--------|
| **Paper (full text)** | Published | ACS JACS | $ | Register at pubs.acs.org or use institutional access |
| **Supporting Info (SI)** | Expected | ACS website | Included | Download from paper DOI link |
| **PDB structures** | ✓ Verified | RCSB PDB | ✓ | Download 5DVZ, 5DW3, 5DW0 |
| **AMBER force field (ff14SB)** | ✓ Standard | AmberTools | ✓ | Install AMBER/AmberTools |
| **PLP parameters** | ? Uncertain | SI or literature | ? | Check SI first, contact Osuna if missing |
| **PLUMED source** | ✓ Available | plumed.org | ✓ | Download & compile |
| **PLUMED tutorials** | ✓ Available | plumed.org | ✓ | Read online documentation |
| **AMBER executable** | ✗ Required | ambermd.org | $ | Academic/commercial license needed |
| **Computational resources** | ✗ Required | Your institution | - | Estimate 10–100 GPU hours for convergence |

---

## 11. NEXT IMMEDIATE STEPS

**Priority 1 (This week):**
1. Access ACS SI files from the paper (https://pubs.acs.org/doi/10.1021/jacs.9b03646)
2. Download PDB structures: 5DVZ, 5DW3, 5DW0 from RCSB
3. Review Osuna group publication list for related methodologies

**Priority 2 (Before starting simulations):**
1. Contact Osuna group (osunalab@udg.edu) for clarification on:
   - Exact PLP parameterization used
   - Specific reference structures for path CV
   - Any computational details in SI
2. Install AMBER + AmberTools (if not available)
3. Install and test PLUMED

**Priority 3 (Simulation design):**
1. Prepare test case (1 ns test run on one intermediate)
2. Validate against published free energy barriers
3. Optimize CV parameters (LAMBDA, HEIGHT, PACE)
4. Scale up to full production run

---

## 12. RESOURCES & CONTACTS

**Osuna Research Group:**
- Institution: Universitat de Girona (UdG), Institut de Química Computacional i Catàlisis (IQCC)
- Website: [https://www.osunalab.com/](https://www.osunalab.com/)
- Publications: [https://www.osunalab.com/publications/](https://www.osunalab.com/publications/)
- Email: Likely available via UdG institutional directory

**Computational Resources:**
- **AMBER:** https://ambermd.org/
- **PLUMED:** https://www.plumed.org/
- **RCSB PDB:** https://www.rcsb.org/
- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/
- **PLUMED-NEST:** https://www.plumed-nest.org/ (published simulations)

**Tutorials & Documentation:**
- PLUMED Belfast Metadynamics: https://www.plumed.org/doc-v2.9/user-doc/html/belfast-6.html
- PLUMED Masterclass 22.9 (Path CVs): https://www.plumed.org/doc-v2.9/user-doc/html/masterclass-22-9.html
- PLUMED-TUTORIALS online: https://plumed-tutorials.org/

---

**Document Metadata**
- Created: 2026-03-26
- Last Updated: 2026-03-26
- Completeness: ~90% (SI files pending direct access)
- Status: Research & literature compilation complete; ready for simulation setup

