# Prep Pipeline Skeptic Validation

**Date**: 2026-04-01
**Campaign**: osuna2019_benchmark
**System**: PfTrpS(Ain), 39,268 atoms, ff14SB + GAFF, TIP3P
**Job**: Longleaf 40709153, COMPLETED in 32 min 56 sec
**Validator**: Claude (independent skeptic review)

---

## Checklist

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | All stages completed | **PASS** | Slurm log: min1→min2→heat1-7→equil, "All minimization/heating/equilibration outputs validated" |
| 2 | Exit code | **PASS** | sacct: ExitCode 0:0 |
| 3 | Temperature at target | **PASS** | equil avg: 349.95 K (target 350 K), RMS fluctuation: 1.66 K |
| 4 | Energy stability | **PASS** | Etot avg: -79,455 kcal/mol, final steps: -79,306 to -79,890 (normal NVT fluctuations) |
| 5 | No explosions/NaN | **PASS** | grep for error/NaN/fatal: none found |
| 6 | SHAKE integrity | **PASS** | SHAKE reported in output, no failures |
| 7 | File completeness | **PASS** | All 10 .rst7 + 10 .out files present and non-empty |
| 8 | File sizes consistent | **PASS** | min*.rst7 ~943 KB (no velocities), heat/equil.rst7 ~1.9 MB (with velocities) |
| 9 | Heating reached target | **PASS** | heat7 final: 352.11 K (correct, Langevin relaxes to 350 K in equil) |
| 10 | IEEE FP warnings | **INFO** | IEEE_UNDERFLOW_FLAG, IEEE_DENORMAL — standard pmemd.cuda GPU behavior, not errors |

## Performance

- Equil: 111.43 ns/day
- Estimated production wall time: 500 ns / 111.43 ns/day = ~4.5 days
- 72h walltime → ~333 ns per submission; needs 2 submissions total

## UNVERIFIED Items (carried from prep script)

1. **Trajectory write frequencies**: SI does not specify; using ntwx=5000 (10 ps) for operational convenience
2. **Restrained-reference coordinates**: SI doesn't specify; using min2.rst7 as reference for heating restraints

Both are reasonable defaults and do not affect scientific validity.

## Verdict

**PASS (HIGH CONFIDENCE)**

All thermodynamic indicators are within expected ranges. The system is properly equilibrated at 350 K with stable energy. Ready for 500 ns production submission.

## Recommendation

Submit `submit_production.sh` via sbatch. Monitor first ~10 ns output for continued stability.
