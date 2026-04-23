# Email to Maria-Solano et al. — request for MetaD parameters

**Status**: REVISED DRAFT

---

**To**: Miguel A. Maria-Solano `<miguel.mariasolano@ewha.ac.kr>`
  (first author; now at Global AI Drug Discovery Center, Ewha Womans University, Seoul — Sun Choi's lab)

**Cc**:
- Sílvia Osuna `<silvia.osuna@udg.edu>` — senior author, UdG/ICREA
- Prof. Anima Anandkumar `<anima@caltech.edu>`
- Yu Zhang `<yuzhang@caltech.edu>`

*Note: Javier Iglesias-Fernández (second author) has a public direct email candidate `jiglesiasfrn@gmail.com` from a 2020 corresponding-author paper listing his present address as Nostrum Biodiscovery, but we have not yet confirmed a current institutional directory entry. The body of the message still asks Prof. Osuna to forward if appropriate.*

**From**: Zhenpeng Liu `<liualex@ad.unc.edu>`

**Subject**: Replication question on PATHMSD metadynamics in Maria-Solano et al., JACS 2019

---

Dear Dr. Maria-Solano,

I am an undergraduate at UNC Chapel Hill working with Prof. Anima Anandkumar's group at Caltech on computational studies of tryptophan synthase beta-subunit (TrpB). We are using the well-tempered metadynamics protocol from your 2019 JACS paper, *Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution* (DOI 10.1021/jacs.9b03646), as the starting point for our replication.

We have implemented the setup described in Supporting Information Section S3-S4 as closely as we can: the 15-frame open-to-closed path on the COMM-domain C-alpha atoms, PATHMSD, well-tempered metadynamics at 350 K, hill height 0.15 kcal/mol, deposition every 2 ps, bias factor 10, and adaptive Gaussian widths. We also verified offline that the reference path behaves sensibly at the endpoints. However, in our single-walker run the trajectory remains confined to the open basin, with s(R) staying around 1.0-1.6 over 50 ns, so we are unable to reproduce the initial broad sweep along the path that would be needed to seed the later 10-walker stage described in the SI.

Because of that, there are two implementation details we hoped to clarify:

1. For the 15-frame open-to-closed reference path, how were the frames structurally aligned before the PATHMSD calculation? In particular, was the path pre-aligned offline, or was any PLUMED runtime alignment used during the metadynamics calculation?

2. The SI states that an adaptive Gaussian width scheme was used, but we could not find the actual width parameters. Would you be willing to share what values were used for the initial Gaussian width and any lower or upper bounds in practice (for example, `SIGMA`, `SIGMA_MIN`, and `SIGMA_MAX`, or the equivalent settings in your PLUMED version)? This is the main parameter family we still cannot recover from the SI, and it seems the most likely reason our walker does not leave the open basin. If it is easier, even a representative PLUMED input file from the initial single-walker run or from Aex1, A-A, or Q2 would answer this directly.

If any of these files are already available in a repository or archive, a link would be equally helpful. Even a partial example would be greatly appreciated.

I was not able to verify a current email for Dr. Iglesias-Fernandez. Prof. Osuna, if appropriate, we would be grateful if you could forward this message to him as well.

Thank you very much for your time, and for the work that makes this study possible.

Best regards,

Zhenpeng Liu
Undergraduate, UNC Chapel Hill
Anandkumar Lab collaborator
liualex@ad.unc.edu

---

## Review checklist (fill before send)

- [x] Maria-Solano (1st author): `miguel.mariasolano@ewha.ac.kr` — Ewha Womans University, Seoul (eLife 2023 + NatComm 2024 + JPCL 2026 corresponding-author records)
- [x] Osuna (3rd/senior author): `silvia.osuna@udg.edu`
- [x] **Iglesias-Fernández (2nd author) candidate direct email**: `jiglesiasfrn@gmail.com` — public corresponding-author email in a 2020 Catalysts paper; present address listed as Nostrum Biodiscovery
- [x] Anima Anandkumar: `anima@caltech.edu`
- [x] Yu Zhang: `yuzhang@caltech.edu`
- [ ] Timing: Maria-Solano is in Seoul (UTC+9). Send tonight EDT → arrives tomorrow morning Seoul.
- [x] Removed the "Dr. Yu Zhang contacted Dr. Osuna last week" line.

## Fallback plan

If Maria-Solano bounces, his current PI Sun Choi (`sunchoi@ewha.ac.kr`) can be asked to forward. If Osuna's UdG address bounces, she is also reachable via ICREA at `silvia.osuna@icrea.cat`.
