# Meeting Notes: Metadynamics Simulation Progress Review

**Date:** April 2, 2026  
**Attendees:** Alex (presenter), Dr. Zhang, Amin  
**Format:** Status review and technical verification

---

## Overview

This meeting was a progress check-in on the replication of well-tempered metadynamics simulations from Osuna and coworkers (JACS 2019, 141, 13049–13056). No new results were presented. The focus was on confirming the current pipeline state: the PLP cofactor parameterization, the Gaussian charge calculation setup, and the ongoing classical MD production run on Longleaf.

## Current Progress

### Simulation Environment

Both simulation engines are set up on UNC's Longleaf HPC. AMBER 24p3 (pmemd.cuda, GPU) handles classical MD, and GROMACS 2026.0 with PLUMED 2.9 (conda) is reserved for metadynamics. This matches the original paper, which used AMBER for prep/equilibration and GROMACS+PLUMED2 for enhanced sampling.

### PLP Cofactor Parameterization

The PLP cofactor was parameterized per the SI protocol: fragment extraction from the crystal structure, geometry optimization and ESP calculation in Gaussian 16 at HF/6-31G(d), RESP charge fitting, and GAFF atom type assignment via antechamber with parmchk2 for missing bonded parameters. The capped fragment (ACE-LLP-NME) carries a net charge of -2. Dr. Zhang reviewed the Gaussian input file during the meeting and confirmed the setup.

### Classical MD Production Run

The 500 ns NVT production run (PfTrpB with Ain intermediate) is running on Longleaf (Job 40806029). At meeting time, the job had been going for about 33 hours at ~168 ns/day, putting it at roughly 46% done with ~38 hours left. Should finish around April 4.

### Path Collective Variable

The 15-frame reference path for the path CV is ready. It was built by linear interpolation of C-alpha coordinates between the open state (1WDW, Pf-TrpB) and the closed state (3CEP, St-TrpB), using 112 C-alpha atoms from the COMM domain (residues 97-184) and base region (residues 282-305). The calculated lambda is 0.034 per angstrom squared, about 17% above the paper's value of 0.029. The difference comes from how the structures were aligned and has been documented.

## Next Steps

1. Complete the 500 ns classical MD production run (estimated April 4).
2. Convert the equilibrated AMBER system to GROMACS format and run a short validation MD.
3. Submit the first well-tempered metadynamics run with the prepared PLUMED input and path CV.
4. Prepare a tutorial covering software setup, PLP parameterization, and input file preparation.
5. Review the AMBER classical MD pipeline shared by Dr. Zhang.
