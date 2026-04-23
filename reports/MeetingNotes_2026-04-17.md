# Meeting Notes 2026-04-17

**Date:** April 17, 2026
**Attendees:** Alex Liu, Yu Zhang
**Format:** 1-on-1, ~15 min

## Summary

Walked through why Job 42679152 (50 ns single walker) finished mechanically but stayed stuck in the O basin, and the SIGMA fix deployed April 15. Job 44008381 is the 50 ns continuation from the 10 ns probe checkpoint; at meeting time it had reached 27.68 ns with max s(R) = 3.49.

## Discussion

- **Why the last job got stuck.** SIGMA was set to the PLUMED default 0.05 nm. ADAPTIVE=GEOM shrank the per-CV Gaussian widths to ~0.01 s-units, making every hill a needle. 25,000 needles piled at s≈1.05 built a deep but locally flat well, so the walker felt no force.
- **Fix (2026-04-15).** Raised SIGMA to 0.1 nm. Added SIGMA_MIN=0.3,0.005 (per-CV floor in s-units and nm²) and SIGMA_MAX=1.0,0.05 (ceiling). SI does not specify these values; both floors are my choice.
- **Tutorial citation error.** An earlier tutorial draft quoted `SIGMA=0.2,0.1` as if from SI p.S3. Full-text search of the SI confirms SI gives no numerical SIGMA. Removed the fake citation.
- **Restart protocol.** Extended Job 43813633 (10 ns probe) to 50 ns via two steps: `gmx convert-tpr -extend 40000`, then `gmx mdrun -cpi metad.cpt` with `RESTART` on line 1 of plumed.dat so HILLS appends instead of rotating to bck.0.HILLS.
- **Current run (Job 44008381).** 5 ns windowed max s trend: 1.18 → 1.39 → 1.46 → 1.81 → 2.79 → 3.49. Monotonic, consistent with walker climbing out of O toward PC.
- **Decision gate at 50 ns.** max s ≥ 5 → Phase 2 (10 walkers). 3 ≤ max s < 5 → wait for full 50 ns. max s < 3 → regroup.

## Post-meeting status (20:30 EDT)

Job 44008381 at 34.94 ns, max s(R) = 4.13. sigma_path.sss holding at the 0.30 floor. On track to finish within walltime.

## Next Steps

1. Monitor Job 44008381 to 50 ns and apply the decision gate.
2. If Phase 2: pick ~10 diverse starting snapshots by PyMOL inspection (not strided frames), per Yu's April 9 direction.
3. FES reconstruction + JACS 2019 Fig 2a comparison by April 24.
4. Shared repo: https://github.com/alex051107/trpb-metadynamics-replication
5. Send draft email to Maria-Solano (CC Osuna, Amin, Yu) asking for the plumed.dat files of Aex1 / A-A / Q2 and the 15-frame path alignment method.
