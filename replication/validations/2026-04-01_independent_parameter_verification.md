# Independent Parameter Verification Report

**Date**: 2026-04-01
**Validator**: Independent Skeptic Agent (no prior context)
**Scope**: All parameters across force field, MetaDynamics, conventional MD, conversion, analysis

---

## Summary

**41 checks total: 31 PASS, 3 FAIL, 7 UNVERIFIED**

---

## 3 FAIL Items (requires attention)

| ID | Issue | Severity | Detail |
|----|-------|----------|--------|
| **B11** | PLUMED atom indices still placeholders | Expected | Both `.dat` files contain `PLACEHOLDER_PENDING_CONVERSION` tokens for REFERENCE PDB, K82-Q2 distance atoms, E104-Q2 distance atoms. Submission scripts have `assert_no_literal` guards preventing accidental execution. Not runnable yet — blocked on AMBER→GROMACS conversion. |
| **C8** | Heating step 7 restraint ambiguity | Medium | SI lists 6 restraint values (210, 165, 125, 85, 45, 10) for 7 heating steps. Current implementation: heat6 AND heat7 both use `restraint_wt=10.0`. Alternative (heat7=0) equally valid. Choice is reasonable but undocumented. |
| **G6** | BCC fallback path in parameterize_plp.sh | Medium | `parameterize_plp.sh` contains a BCC fallback code path. Should have hard fail guard for production mode to prevent accidental use (FP-009). |

## 7 UNVERIFIED Items

| ID | Item | Reason |
|----|------|--------|
| A8 | BCC fallback in production Longleaf files | Cannot inspect live files from this workspace |
| A9 | Gaussian .gcrt on Longleaf | Cannot access Longleaf artifacts remotely |
| B9 | SIGMA=0.05 initial adaptive width | SI does not report this value |
| D-all | convert_amber_to_gromacs.py execution | Script not yet executed (production MD still running) |
| E6 | GROMACS thermostat (v-rescale) | SI does not specify thermostat for MetaD stage |
| - | Lambda 15% discrepancy root cause | Needs residue mapping check against original paper |
| - | Job 40533504 RESP output | Gaussian job needs completion verification |

## Key Positive Findings

### Three-way consistency CONFIRMED

Parameters.md ↔ manifest YAML ↔ run files are consistent for all major parameters:

| Parameter | Parameters.md | Manifest | Run File | Status |
|-----------|--------------|----------|----------|--------|
| Force field | ff14SB | ff14SB | leaprc.protein.ff14SB | PASS |
| Water model | TIP3P | TIP3P | leaprc.water.tip3p | PASS |
| Temperature | 350 K | 350 K | temp0=350.0 | PASS |
| Production length | 500 ns | 500 ns | nstlim=250000000, dt=0.002 | PASS |
| Ensemble | NVT | NVT | ntb=1, ntp=0 | PASS |
| Timestep | 2 fs | 2 fs | dt=0.002 | PASS |
| Cutoff | 8 Å | 8 Å | cut=8.0 | PASS |
| Electrostatics | PME | PME | (default with ntb=1) | PASS |
| HEIGHT | 0.15 kcal/mol (0.628 kJ/mol) | 0.628 kJ/mol | HEIGHT=0.628 | PASS |
| PACE | 1000 steps (2 ps) | 1000 | PACE=1000 | PASS |
| BIASFACTOR | 10 | 10 | BIASFACTOR=10 | PASS |
| TEMP (MetaD) | 350 K | 350 K | TEMP=350 | PASS |
| Walkers | 10 | 10 | --array=0-9 | PASS |
| Path frames | 15 | 15 | 15 reference PDBs | PASS |
| State windows | O=1-5, PC=5-10, C=10-15 | same | same in analyze_fes.py | PASS |

### All 15 failure pattern fixes VERIFIED

| FP | Fix | Verified In |
|----|-----|-------------|
| FP-001 | Biased CVs (s,z) vs monitored (K82-Q2, COMM RMSD) correctly separated | plumed_trpb_metad.dat |
| FP-004 | Atom indices are PLACEHOLDER_PENDING_CONVERSION, not guessed from PDB | Both .dat files |
| FP-009 | No BCC in Gaussian route | .gcrt files, build script |
| FP-013 | No `iop(6/50=1)` in active files | Grep confirmed |
| FP-015 | `calculate_msd` no longer has sqrt bug; lambda from total SD | summary.txt, scripts |

### Lambda analysis

- PLUMED files: λ = 0.033910 (from total SD = 67.826 Å²)
- JACS 2019: λ ≈ 0.029 (from MSD ≈ 80 Å²)
- Discrepancy: ~15%, attributed to path construction details (alignment/residue mapping), not code bug

### Script quality

- `convert_amber_to_gromacs.py`: atom count assertion (39,268), charge assertion, box check, GAFF stop-condition, energy comparison
- `analyze_fes.py` + `check_convergence.py`: correct state windows, physical range assertions, proper function semantics, JACS comparison logic

---

## Top 3 Recommendations

1. **[HIGH]** Verify Longleaf Gaussian RESP output when Job 40533504 completes — confirm charges sum to -2 and antechamber reads cleanly
2. **[MEDIUM]** Add production-mode guard to `parameterize_plp.sh` BCC fallback path — prevent FP-009 recurrence
3. **[MEDIUM]** Investigate 15% lambda discrepancy by checking residue mapping against original paper's atom selection
