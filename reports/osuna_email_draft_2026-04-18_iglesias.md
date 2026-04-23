# Email to Iglesias-Fernández (2nd author) — replication follow-up

**Status**: READY TO SEND (v3, 2026-04-18 — recipient corrected to the address printed in the JACS 2019 paper itself)

---

**To**: Javier Iglesias-Fernández `<javier.iglesias@udg.edu>`
  (2nd co-corresponding author of JACS 2019 — the exact address
  printed under the author list on the paper's title page / SI p.S1;
  the Nostrum gmail in v2 was wrong, use the UdG address on record)

**Cc**:
- Sílvia Osuna `<silvia.osuna@udg.edu>` — senior author
- Miguel A. Maria-Solano `<miguel.mariasolano@ewha.ac.kr>` — first author
  (already contacted 2026-04-17, keeping in the loop)
- Prof. Anima Anandkumar `<anima@caltech.edu>`
- Yu Zhang `<yuzhang@caltech.edu>`

**From**: Zhenpeng Liu `<liualex@ad.unc.edu>`

**Subject**: Replication question on PATHMSD metadynamics in Maria-Solano et al., JACS 2019

---

Dear Dr. Iglesias-Fernández,

I am an undergraduate at UNC Chapel Hill working with Prof. Anima Anandkumar's group at Caltech on computational studies of tryptophan synthase beta-subunit (TrpB). We are using the well-tempered metadynamics protocol from your 2019 JACS paper, *Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution* (DOI 10.1021/jacs.9b03646), as the starting point for our replication. I wrote to Dr. Maria-Solano yesterday with the same question and, knowing that the simulations in the paper were largely your joint work, I am reaching out to you in parallel in case a short pointer from either of you can unblock us.

We have implemented the setup described in Supporting Information Section S3-S4 as closely as we can: the 15-frame open-to-closed path on the COMM-domain C-alpha atoms, PATHMSD, well-tempered metadynamics at 350 K, hill height 0.15 kcal/mol, deposition every 2 ps, bias factor 10, and adaptive Gaussian widths. We also verified offline that the reference path behaves sensibly at the endpoints. However, in our single-walker run the trajectory remains confined to the open basin, with s(R) staying around 1.0-1.6 over 50 ns, so we are unable to reproduce the initial broad sweep along the path that would be needed to seed the later 10-walker stage described in the SI.

Because of that, there are two implementation details we hoped to clarify:

1. For the 15-frame open-to-closed reference path, how were the frames structurally aligned before the PATHMSD calculation? In particular, was the path pre-aligned offline, or was any PLUMED runtime alignment used during the metadynamics calculation? We ask because the choice of alignment has already produced roughly a ten-percent-plus difference between our projected s(R) values and what Fig. 2a of the paper shows for the same endpoints, so this is one piece of the setup where we are clearly off.

2. The SI states that an adaptive Gaussian width scheme was used, but we could not find the actual width parameters. Would you be willing to share what values were used for the initial Gaussian width and any lower or upper bounds in practice (for example, `SIGMA`, `SIGMA_MIN`, and `SIGMA_MAX`, or the equivalent settings in your PLUMED version)? This is the main parameter family we still cannot recover from the SI, and it seems the most likely reason our walker does not leave the open basin. If it is easier, even a representative PLUMED input file from the initial single-walker run or from Aex1, A-A, or Q2 would answer this directly.

If any of these files are already available in a repository or archive, a link would be equally helpful. Even a partial example would be greatly appreciated.

Thank you very much for your time, and for the work that makes this study possible.

Best regards,

Zhenpeng Liu
Undergraduate, UNC Chapel Hill
liualex@ad.unc.edu

---

## v2 vs v1 changes

| v1 | v2 | Why |
|----|----|-----|
| Long intro listing all our env (GROMACS 2026, PLUMED 2.9.2, `ADAPTIVE=GEOM`) | Removed — mirrors original Maria draft | Keep the ask minimal; same questions, cleaner |
| Body contained our best-guess SIGMA values | Removed | Would push him toward confirming our guess instead of telling us his actual numbers |
| Alignment question was abstract | Added: "the choice of alignment has already produced roughly a ten-percent-plus difference between our projected s(R) values and what Fig. 2a shows for the same endpoints" | Concrete stake — tells him why this specific question matters to us, not just theoretical curiosity |
| "We will keep Dr. Maria-Solano and Prof. Osuna in the loop on any reply" | Removed | She's already in CC, no need to say it |

## Send checklist

- [x] Addressed to Iglesias-Fernández; Maria-Solano + Osuna in CC (already emailed 1st author yesterday)
- [x] Anandkumar + Yu Zhang in CC per John's April 17 request
- [x] Same two questions as the Maria-Solano email (not re-derived)
- [x] Alignment paragraph mentions the ~10%+ s(R) deviation as the specific cost of not knowing the alignment method
- [x] No SIGMA guesses given — leave room for him to tell us his actual values
- [ ] **Timing**: UdG is in Girona, Spain (UTC+2). Send tonight EDT → arrives tomorrow AM CET
- [x] Recipient verified: `javier.iglesias@udg.edu` matches the address printed
  under the author list in the JACS 2019 paper (p.1 footnote) — same institutional
  domain as Osuna's `silvia.osuna@udg.edu`. The gmail used in v2 was from an
  unrelated 2020 Catalysts paper and is not the address on record for JACS 2019.

## Fallback plan

- 48 h no reply from either author → send directly to Osuna (`silvia.osuna@udg.edu`).
- If UdG address bounces → ICREA backup `silvia.osuna@icrea.cat`.
- Parallel: check PLUMED-NEST (`https://www.plumed-nest.org/browse.html`) and any OsunaLab GitHub org for archived inputs — no harm doing this even before a reply.
