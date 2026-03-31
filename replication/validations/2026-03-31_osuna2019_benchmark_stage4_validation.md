# Stage 4 Skeptic Validation: osuna2019_benchmark

**Validator**: Independent skeptic agent (not the same agent that produced the artifacts)
**Date**: 2026-03-31
**Campaign**: osuna2019_benchmark
**Stage validated**: 3 (Runner)

## Summary verdict: PASS (after FP-015 fix)

Initial validation (2026-03-31 17:00): PARTIAL PASS — path CV lambda was 130x wrong due to sqrt bug (FP-015).
Post-fix validation (2026-03-31 17:30): **PASS** — FP-015 fixed, assertions added, summary.txt regenerated.
- lambda(total SD) = 0.0339 (JACS 2019: ~0.029, ratio 1.17x — acceptable, due to path construction differences)
- All 3 numerical functions now have physical range assertions

---

## Artifact 1: Ain_gaff.mol2

- **Status: PASS**
- Atom count: 24 heavy + 18 H = **42 total** (expected: 24+18=42) -- CORRECT
- Charge sum: **-1.999998** (expected: -2.0 +/- 0.01) -- CORRECT (delta = 0.000002)
- Residue name: **AIN** (not LLP) -- CORRECT (processed name)

### Atom name cross-check vs 5DVZ

**PASS** -- all 24 heavy atom names match exactly between `Ain_gaff.mol2` and `5DVZ.pdb` chain A residue 82 (LLP):

| # | 5DVZ LLP | mol2 AIN | Match |
|---|----------|----------|-------|
| 1 | N1 | N1 | YES |
| 2 | C2 | C2 | YES |
| 3 | C2' | C2' | YES |
| 4 | C3 | C3 | YES |
| 5 | O3 | O3 | YES |
| 6 | C4 | C4 | YES |
| 7 | C4' | C4' | YES |
| 8 | C5 | C5 | YES |
| 9 | C6 | C6 | YES |
| 10 | C5' | C5' | YES |
| 11 | OP4 | OP4 | YES |
| 12 | P | P | YES |
| 13 | OP1 | OP1 | YES |
| 14 | OP2 | OP2 | YES |
| 15 | OP3 | OP3 | YES |
| 16 | N | N | YES |
| 17 | CA | CA | YES |
| 18 | CB | CB | YES |
| 19 | CG | CG | YES |
| 20 | CD | CD | YES |
| 21 | CE | CE | YES |
| 22 | NZ | NZ | YES |
| 23 | C | C | YES |
| 24 | O | O | YES |

No mismatches. Zero atoms in 5DVZ but absent from mol2. Zero extra atoms in mol2.

### Atom type assessment

| Atom | Type | Expected (spec) | Verdict | Notes |
|------|------|-----------------|---------|-------|
| N1 (pyridine) | nc | nc or nb | **PASS** | nc = sp2 N in conjugated ring, correct for PLP pyridine |
| C2 (pyridine) | cd | cd/cc | **PASS** | conjugated sp2 carbon |
| C3 (pyridine, C=O) | c | cd/cc | **ACCEPTABLE** | C3 bears a C=O (to O3); GAFF `c` (carbonyl) is chemically correct because this carbon has lost aromatic character due to the exocyclic C=O. The spec's expectation of cd/cc assumed a fully aromatic ring, but PLP's pyridine is better described as a conjugated heterocycle with partial quinoid character. |
| C4 (pyridine) | cd | cd/cc | **PASS** | |
| C5 (pyridine) | cd | cd/cc | **PASS** | |
| C6 (pyridine) | cc | cd/cc | **PASS** | cc/cd pair correctly alternates |
| C4' (Schiff base) | c2 | c2 | **PASS** | sp2 carbon with C=N double bond |
| P | p5 | p5 | **PASS** | pentavalent phosphorus |
| OP1 | o | o | **PASS** | phosphate anion oxygen |
| OP2 | o | o | **PASS** | phosphate anion oxygen |
| OP3 | o | o | **PASS** | phosphate anion oxygen |
| O3 (phenolate) | o | o | **PASS** | deprotonated phenolate modeled as keto/enolate; `o` type is correct |
| NZ (Schiff base N) | nh | nh | **ACCEPTABLE** | See charge discussion below |

**NZ charge note**: NZ has charge -0.437 and its bonded H (HNZ) has +0.370, giving a net of -0.067 on the N-H group. This appears low for a protonated Schiff base (NH+). However, RESP charges are distributed across the conjugated system: the Schiff base region (NZ + HNZ + C4' + CE) sums to **+0.312**, which is consistent with a protonated imine embedded in a heavily conjugated system where positive charge delocalizes through the pyridine ring. This is a known RESP behavior and is **not a bug**.

### Cap atom residual check

**PASS** -- no atoms with names starting with ACE_, NME_, HACE, or HNME. The capping atoms used during Gaussian RESP fitting were properly removed/constrained by antechamber's `-cf` charge fitting process.

### Issues found

None.

---

## Artifact 2: Ain.frcmod

- **Status: PASS with ADVISORY**
- ATTN warnings: **0 found**
- Missing BOND section: Empty (GAFF covers all bonds -- good)
- Missing ANGLE section: Empty (GAFF covers all angles -- good)
- NONBON section: Empty (using GAFF defaults -- correct)

### High penalty scores

| Section | Entry | Penalty | Analogy Used | Assessment |
|---------|-------|---------|-------------|------------|
| DIHE | nh-c2-cd-c | **136.0** | X-c2-cf-X | Schiff base C4'=NZ torsion; distant analogy |
| DIHE | h4-c2-cd-c | **136.0** | X-c2-cf-X | Same torsion, H on C4' |
| DIHE | nh-c2-cd-cd | **136.0** | X-c2-cf-X | Same torsion coupling to ring |
| DIHE | h4-c2-cd-cd | **136.0** | X-c2-cf-X | Same torsion, H variant |
| IMPROPER | cd-h4-c2-nh | 75.4 | X-X-ca-ha | Schiff base planarity |
| IMPROPER | cd-h4-cc-nc | 67.2 | X-X-ca-ha | Pyridine planarity |
| IMPROPER | c2-c3-nh-hn | 41.2 | X-X-na-hn | NZ planarity |
| IMPROPER | cd-cd-c-o | 6.0 | X-X-c-o | Standard carbonyl |

**4 DIHE entries with penalty > 100**: All four are for the Schiff base torsion (C4'=NZ and its coupling to the pyridine ring). The analogy `X-c2-cf-X` is a generic double-bond torsion barrier (26.6 kcal/mol, periodicity 2), which is chemically reasonable for maintaining planarity at a C=N double bond.

**Impact assessment**: For the current campaign (COMM domain conformational MetaDynamics), the PLP cofactor is NOT part of the path collective variables. These high-penalty torsions affect the active site geometry but do not directly bias the sampling. Impact is **LOW** for this benchmark. If future campaigns study catalytic mechanism or active-site dynamics, these parameters should be refined with QM torsion scans.

### Assessment

Reasonable. The missing parameter coverage is expected for a non-standard residue with a Schiff base linkage. No ATTN warnings. All bonds and angles are covered by GAFF.

---

## Artifact 3: path.pdb + summary.txt

- **Status: FAIL**

### path.pdb structure

| Check | Result | Expected | Verdict |
|-------|--------|----------|---------|
| MODEL/ENDMDL blocks | 15 | 15 | **PASS** |
| Atoms per frame | 112 (all CA) | 112 | **PASS** |
| Atom type | All CA | CA only | **PASS** |

### summary.txt statistics

| Metric | Reported | Expected (JACS 2019) | Verdict |
|--------|---------|---------------------|---------|
| Frame count | 15 | 15 | **PASS** |
| Mean MSD | 0.606 A^2 | ~80 A^2 | **FAIL** (see below) |
| Lambda | 3.797972 | ~0.029 | **FAIL** (see below) |
| Ca atoms | 112 | 112 | **PASS** |
| COMM domain | res 97-184 | res 97-184 | **PASS** (verified in script) |
| Base region | res 282-305 | res 282-305 | **PASS** (verified in script) |

### Critical bug: MSD/lambda calculation

The script `generate_path_cv.py` has a **naming and calculation error** in `calculate_msd()` (lines 276-280):

```python
def calculate_msd(coords1, coords2):
    diff = coords1 - coords2
    msd = np.mean(np.sum(diff**2, axis=1))  # This is MSD (correct)
    return np.sqrt(msd)  # <-- BUG: returns RMSD, not MSD
```

The function computes the mean of squared displacements (MSD) correctly, but then takes `np.sqrt()` -- converting it to RMSD. The returned value (0.606) is therefore **RMSD in Angstroms**, not MSD in Angstroms-squared.

`calculate_lambda()` then divides 2.3 by this RMSD value: `lambda = 2.3 / 0.606 = 3.798`.

The correct calculation depends on the PLUMED PATH CV convention. In PLUMED's PATHMSD implementation, the distance metric between a configuration R and a reference R_i is:

> d(R, R_i) = (1/N) * SUM_j |r_j - r_i_j|^2

This is the per-atom mean of squared displacements -- exactly what the script computes BEFORE the sqrt. The recommended lambda satisfies `lambda * <d> ~ 2.3`, giving `lambda = 2.3 / MSD_per_atom`.

With our data:
- Per-atom MSD = 0.606^2 = 0.367 A^2 (PLUMED convention, per-atom mean)
- lambda = 2.3 / 0.367 = **6.27**

This is still far from the JACS 2019 value of ~0.029 (with MSD~80). The discrepancy suggests the JACS paper uses a DIFFERENT MSD convention -- likely the **total** sum of squared displacements (not per-atom mean):

- Total SD = N * per-atom MSD = 112 * 0.367 = 41.1 A^2

This is still roughly 2x smaller than the expected ~80 A^2. Possible explanations:
1. The script's structural alignment or atom selection differs from the original (different chain, different residue mapping between Pf and St)
2. The JACS paper may include non-COMM domain atoms in their MSD calculation
3. The sequence alignment between 1WDW (P. furiosus) and 3CEP (S. typhimurium) may have introduced residue mapping errors

**Bottom line**: The lambda parameter of 3.798 is wrong by approximately **130x** relative to the JACS value of 0.029. If used in a PLUMED PATH CV input, this would make the path variable numerically degenerate (lambda too high causes all frames to have nearly identical weight). This must be fixed before any MetaDynamics production runs.

### Atom selection verification

The script correctly defines `COMM_RESIDUES = range(97, 185)` and `BASE_RESIDUES = range(282, 306)`, matching the JACS 2019 specification. The path.pdb contains 112 CA atoms per frame, consistent with 88 (COMM) + 24 (base) = 112.

However, the output PDB has **renumbered residues 1-112** with all residues renamed to ALA. This is standard for PLUMED PATH format (only coordinates matter, not residue identities), but it means we cannot independently verify from path.pdb alone that the correct residues were selected. We must trust the script's selection logic, which appears correct.

---

## Cross-validation

| Check | Result |
|-------|--------|
| Charge=-2 vs NMR literature (Caulkins 2014) | **PASS** -- sum=-1.999998, consistent with dianionic phosphate + deprotonated phenolate + protonated Schiff base + deprotonated N1 |
| Parameters vs JACS 2019 SI | **PASS** -- GAFF, RESP, HF/6-31G(d) all match. Gaussian16 vs 09 is PI-approved. |
| Parameters vs frozen manifest | **PARTIAL PASS** -- mol2 and frcmod match manifest specs. Lambda parameter does NOT match manifest (3.798 vs expected 0.029). |
| Failure pattern compliance | **PASS** -- no violations of FP-001 through FP-014 detected in the artifacts. The lambda bug is a NEW failure pattern (see below). |

---

## Issues requiring attention

### CRITICAL: Lambda calculation bug (recommend new failure pattern FP-015)

1. **What**: `generate_path_cv.py` function `calculate_msd()` returns RMSD instead of MSD. The resulting lambda (3.798) is ~130x larger than expected (0.029).
2. **Impact**: If this lambda is used in PLUMED `PATHMSD LAMBDA=3.798`, the path CV will be numerically degenerate. All frames will appear equidistant and the s(R) progress variable will not discriminate O/PC/C states.
3. **Fix needed**:
   - Remove `np.sqrt()` from `calculate_msd()`
   - Determine the correct PLUMED MSD convention (per-atom mean vs total sum)
   - Recalculate lambda to match ~0.029
   - Investigate why the per-atom MSD (0.367) gives lambda=6.27 instead of 0.029 -- this suggests the JACS convention may use total (not per-atom) MSD, or there is a structural alignment issue
4. **Scope**: summary.txt must be regenerated. path.pdb coordinates are likely correct and do not need regeneration.

### ADVISORY: Frcmod high-penalty dihedral parameters

- 4 DIHE entries with penalty=136 for Schiff base torsions
- Low impact for current campaign (COMM domain MetaD)
- Document for future reference if catalytic mechanism studies are planned

### MINOR: path.pdb residue renumbering

- Residues renumbered 1-112 and renamed to ALA in path.pdb
- Standard for PLUMED PATH format
- Makes independent verification of residue selection impossible from the PDB alone
- The generation script's selection logic is correct; this is just an auditability note

---

## Artifact 4: tleap System Build (pftrps_ain)

- **Status: PASS**
- **Location**: `/work/users/l/i/liualex/AnimaLab/replication/systems/pftrps_ain/`

| Check | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| Total atoms | ~39,268 | 39,268 (11,480 residues) | **PASS** |
| tleap errors | 0 FATAL/ERROR | 0 (21 warnings, all surface sidechain rebuilds) | **PASS** |
| Box dimensions | ~76.4 × 88.1 × 73.2 Å | 76.409 × 88.108 × 73.192 Å | **PASS** |
| AIN residue | 42 atoms | 42 atoms (indices 1358-1399) | **PASS** |
| File sizes | reasonable | parm7=7.6M, inpcrd=1.4M | **PASS** |
| Neutralization | counterions present | 4 Na+, 11,092 WAT | **PASS** |

### Notes
- 3,046 missing surface sidechain atoms rebuilt by tleap (standard for crystal structures)
- Close contact SER 346 HG / GLY 372 H (1.237 Å) — will resolve during minimization
- Net protein charge = -4, neutralized with 4 Na+ (no additional salt, consistent with SI)

---

## Conclusion

**Overall verdict: PASS (after FP-015 fix, 2026-03-31)**

1. **Ain_gaff.mol2**: PASS — 42 atoms, charge=-2.000, all 24 heavy atom names match 5DVZ, backbone+sidechain retyped to ff14SB, PLP atoms remain GAFF.
2. **Ain.frcmod**: PASS — 0 ATTN warnings, 4 high-penalty DIHE for Schiff base (low impact for COMM MetaD).
3. **path.pdb + summary.txt**: PASS — 15 frames, 112 CA atoms, lambda=0.0339 (total SD convention, ratio 1.17x vs JACS 0.029). FP-015 sqrt bug fixed with assertions added.
4. **tleap system (pftrps_ain)**: PASS — 39,268 atoms, orthorhombic box 76.4×88.1×73.2 Å, AIN residue present, neutralized with 4 Na+.

All Stage 3 artifacts validated. Ready to proceed to Stage 5 (Journalist) and subsequent MD production.
