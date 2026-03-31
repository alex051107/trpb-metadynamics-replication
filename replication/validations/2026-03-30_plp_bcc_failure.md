# Validation Note: PLP BCC Charge Calculation Failure

**Date**: 2026-03-30
**Stage**: Runner (premature -- should have been Librarian first)
**Campaign**: osuna2019-benchmark

## What was attempted

Ran `antechamber -c bcc -at gaff2` on LLP (PLP-K82 Schiff base) extracted from 5DVZ chain A.

## Tests run

| Test | Input | Result | Verdict |
|------|-------|--------|---------|
| BCC no-H, nc=0 | LLP_chainA.pdb (24 atoms) | mol2 generated but atom types wrong (c1/c2 instead of ca/nb) | **FAIL** |
| BCC with-H, nc=0 | LLP_chainA_H.pdb (42 atoms) | SCF non-convergence after 1000 steps | **FAIL** |
| BCC with-H, nc=-2 | LLP_chainA_H.pdb (42 atoms) | SCF non-convergence after 1000 steps | **FAIL** |
| Gasteiger, nc=-2 | LLP_chainA_H.pdb (42 atoms) | mol2 generated (atom typing only) | **PASS** |
| Gaussian RESP input generation | LLP_ain_gas.mol2 → gcrt | .gcrt file generated with correct keywords | **PASS** |

## Conclusion

- BCC charges are NOT viable for PLP (phosphate + conjugated system too complex for AM1)
- Must use RESP via Gaussian (which is what the SI specifies)
- Gaussian input file `LLP_ain_resp.gcrt` is ready: HF/6-31G*, 42 atoms, charge=-2, mult=1
- Slurm script created but NOT submitted (pending proper pipeline stage completion)

## Failure patterns logged

- FP-009: BCC SCF non-convergence on PLP
- FP-010: atom typing errors without hydrogens
- FP-011: skipping pipeline stages

## Next steps (after Librarian/Janitor stages complete)

1. Confirm charge=-2 with PI (protonation state dependent)
2. Submit Gaussian RESP calculation
3. Use Gaussian output for antechamber -c resp
