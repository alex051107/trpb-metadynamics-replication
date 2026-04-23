# Meeting Notes: Path CV Debug and OpenMM Pipeline Exploration

**Date:** April 9, 2026
**Attendees:** Alex Liu, Yu Zhang
**Format:** 1-on-1 technical review

---

## Overview

This meeting was a technical review of the first single-walker well-tempered metadynamics run in our replication of the path-CV sampling protocol from Maria-Solano and Osuna (JACS 2019, 141, 13049-13056). At the time of the meeting we are at the end of the initial single-walker stage, where we need a correctly-configured path CV run to unlock the 10-walker production step that follows.

The previous single-walker job (Job 41514529) stalled with the path progress variable confined to a narrow window, which turned out to be a unit-convention bug in the lambda parameter rather than a physical observation. This meeting walked through the bug, the fix, the verification, and a longer-term proposal to migrate the simulation stack onto OpenMM to align with the rest of the lab.

## Discussion

### SI MSD Convention Ambiguity and Lambda Correction

We confirmed the MSD value discrepancy and traced it to an ambiguity in the original paper. SI page S3 reports a per-path-frame MSD of approximately 80 Angstrom squared, while my own value is 0.6056 Angstrom squared per atom. The two numbers differ by a factor of 112, which equals the number of C-alpha atoms used in the path. The root cause is that the SI does not explicitly state how MSD was calculated. Their 80 is a total sum over all 112 atoms, while PLUMED's RMSD action expects a per-atom average. Without that clarification from the paper, my helper script calculate_msd() in generate_path_cv.py guessed the wrong convention and produced a lambda value that was a factor of 112 too small.

We agreed on the fix. The broken lambda was 3.391 nm^-2, which flattened the kernel weights across adjacent reference frames and left the CV unable to distinguish between conformations. The corrected lambda is 379.77 nm^-2, which uses the per-atom convention PLUMED actually needs. The two reported MSD values, SI's 80 and my 0.6056, are now each self-consistent within their own convention.

### Switch from FUNCPATHMSD back to PATHMSD

We also discussed why I originally used FUNCPATHMSD when the paper clearly describes a PATHMSD setup. The conda-forge build of PLUMED 2.9.2 ships a shared kernel library that is missing the PATHMSD module, so GROMACS crashed silently when it loaded the kernel at runtime. I used FUNCPATHMSD at the time as a workaround, but that workaround required setting the lambda convention manually, which is how the factor-of-112 bug was introduced. Rebuilding PLUMED 2.9.2 from source on Longleaf with all modules enabled fixed the root cause. The new plumed.dat uses PATHMSD in three action lines and matches the paper directly.

### Path Reference Frames

We clarified where the 15 frames of the path reference PDB come from. Only frame 1 (1WDW, Pf-TrpB open) and frame 15 (3CEP, St-TrpB closed) are real crystal structures. Frames 2 through 14 are linear Cartesian interpolations of C-alpha coordinates between the two endpoints. They are not physical intermediates of the conformational transition. They exist only as a coordinate system for the path CV to measure progress along the reaction direction.

### Setup Verification

We confirmed that the corrected setup passed the offline self-consistency test. Feeding the 15 reference frames back through the fixed plumed.dat using plumed driver returned s about 1.04 for frame 1 and s about 14.9 for frame 15, which matches the expected path endpoints. The new single-walker job (Job 42679152) was resubmitted to Longleaf on the morning of April 9 with the corrected plumed.dat and passed its first-minute health check (PATHMSD kernel loaded, bias accumulating, zero NaN). The job is expected to finish around April 12. We concluded that the current setup is ready to run to completion and there is no blocking issue on the path CV side.

## Next Steps

1. Run the 10-walker production using around 10 structurally diverse starting conformations. The selection will be made by visually picking frames that look as different as possible from the initial single-walker trajectory, rather than sampling at fixed time intervals.
2. Work through the OpenMM MD pipeline from the GitHub link shared during the meeting, and try running the current system using OpenMM's built-in metadynamics. The goal is to see whether it can reproduce the rest of the lab's existing workflow.
3. Check whether OpenMM can be connected to PLUMED as an interface. If it can, the existing PLUMED path CV setup could be reused inside an OpenMM simulation without rewriting the collective variables.
