# Follow-up email to Miguel Iglesias-Fernández — DRAFT (2026-04-23)

Status: draft, awaiting PM approval before sending.

Subject: TrpB COMM-domain MetaDynamics — follow-up on path construction

---

Dear Dr. Iglesias-Fernández,

Thank you again for your 2026-04-23 email clarifying the MetaDynamics
contract for the TrpB COMM-domain O→C replication. I have implemented
it faithfully (UNITS=A, ADAPTIVE=DIFF, SIGMA=1000, HEIGHT=0.15,
BIASFACTOR=10 for the 10-walker recipe; HEIGHT=0.3, BIASFACTOR=15 for
the single-walker fallback; WHOLEMOLECULES, UPPER_WALLS zzz AT=2.5
KAPPA=800, WALKERS_N=10 with shared HILLS_DIR and RSTRIDE=3000).

One open question I would like to ask about involves the PATHMSD
reference itself.

On our side, I built a 15-frame reference path by linear interpolation
between 1WDW (chain B, Open) and 3CEP (chain B, Closed), using the
112 Cα in residues 97-184 (COMM domain) + 282-305 (base region). The
per-atom mean squared displacement between adjacent frames is
⟨MSD_adj⟩ ≈ 0.606 Å², which gives a Branduardi λ = 2.3 / ⟨MSD⟩ ≈ 3.80 Å⁻².

In your 2026-04-23 email the example plumed.dat quotes LAMBDA=80 Å⁻² on
the PATHMSD action. If I interpret that value under the same Branduardi
heuristic, it implies ⟨MSD_adj⟩ ≈ 0.029 Å² — about 21× denser than our
path. We have also confirmed by self-projection through
`plumed driver` that λ=80 on our path causes integer-snap kernel
collapse, whereas λ=3.77 on our path gives the expected monotonic
s 1.09 → 14.91 behaviour — so λ and path-density appear to be
self-consistent on each path independently.

We have checked whether any of the structures commonly labelled βPC in
Table S1 can be re-used as a geometric midpoint anchor (MODEL 8) on our
path. Projected onto the 1WDW→3CEP direct path with λ=3.77, every
candidate we tested — 5DW0 chain A, 5DW3 chain A, 5DVZ chain A — lands
at s ≈ 1.07 with RMSD_to_1WDW ≈ 1.3–1.6 Å and RMSD_to_3CEP ≈ 11 Å.
In our 112-Cα CV subspace they are O-proximal rather than mid-path.

So we would very much appreciate any of the following, in descending
order of preference:

1. **The original `PATH.pdb` file used for the TrpB COMM-domain
   metadynamics in the 2019 JACS paper (and Osuna subsequent work).**
2. **The script or procedure used to generate it**, including whether
   endpoint structures were Kabsch-aligned on a specific atom subset
   before interpolation, whether intermediate crystal structures were
   interposed, and which chain / residue set was used.
3. **Diagnostic numbers on your path**: number of path frames, atom
   selection (residue ranges), adjacent-frame per-atom MSD, and
   self-projection s values for the 15 frames through PATHMSD.

Even just (3) would let us reproduce the path density directly rather
than inferring it from LAMBDA=80. At the moment, our replication
pipeline can reproduce your MetaD contract exactly on our own
interpolated path, but we cannot independently verify whether our path
corresponds to the same geometric object you ran on in 2019.

Thank you very much for your continued help. I'm happy to share our
current path file, λ audit, and diagnostic scripts if useful.

Best regards,
Zhenpeng Liu
Undergraduate research, University of North Carolina at Chapel Hill
liualex@ad.unc.edu

CC: Dr. Yu Chen (Anima Lab, Caltech) — advisor on the replication
