# Chapter 03 — PLP Chemistry and TrpB Mechanism

**Audience**: You (Zhenpeng). You parameterized PLP-AEX, know the charge-balance, and built the tleap system. This chapter compresses the chemistry layer so you can **defend D/L selectivity arguments** in front of Amin and Raswanth.

**Why this matters for the Amin meeting**: Raswanth said in Slack 4/4 that the planar quinonoid intermediate loses chirality — meaning D-serine binding alone does not guarantee D-tryptophan product. Any MetaD work or ML evaluation metric that claims catalytic relevance must respect this fact. If you can't articulate the chirality-retention logic in one sentence, your metric proposal is weak.

---

## 3.1 The reaction (one sentence)

TrpB (tryptophan synthase β-subunit) takes **L-serine + indole → L-tryptophan + H₂O**, routed through a PLP cofactor covalently bound to Lys87. Lab goal: redesign the β-site and allosteric loops so the native enzyme instead catalyzes **D-serine + indole → D-tryptophan**.

---

## 3.2 The catalytic cycle — intermediates you care about

PLP (pyridoxal 5'-phosphate) in TrpB forms a Schiff base with **Lys87** in the resting state. This is called the "internal aldimine" (often labeled **E**, or **LLP** in PDB nomenclature; PDB 5DVZ has it).

```
     E (internal aldimine)           = PLP covalent to Lys87
       ↓ L-Ser binds, transaldimination
     E·Ain (external aldimine)       = PLP-Ser Schiff base; Lys87 free
       ↓ α-proton abstraction (Lys87 acts as base)
     E·Aex1 (quinonoid)              = planar π-conjugated carbanion; CHIRALITY LOST HERE
       ↓ dehydration
     E·A-A (α-aminoacrylate)         = covalent electrophile awaiting nucleophile
       ↓ indole binds, attacks Cβ
     E·Q₂/Q₃ (second quinonoid)      = C-C bond formed; planar
       ↓ Cα reprotonation (geometry determines L vs D!)
     E·Trp (external aldimine)
       ↓ transaldimination
     E (internal) + Trp released
```

**Key insight**: Stereochemistry of the product Trp is set **at the reprotonation step** of the second quinonoid, not at the L-Ser binding step. Whoever delivers H⁺ to the *re* face vs *si* face of the planar quinonoid determines L vs D Trp.

In native TrpB:
- Lys87 delivers H⁺ from the **re** face → L-Trp
- D-serine can bind → quinonoid forms (lost chirality) → but reprotonation still happens from re face → still L-Trp!

**Hence the engineering challenge**: you need either to move Lys87 so it protonates from the *si* face, or to introduce a different acid/base residue positioned for *si*-face delivery. This is deeper than just "make the pocket fit D-serine".

---

## 3.3 The Dunathan hypothesis

Harmon Dunathan (1966) proposed that PLP-enzyme reaction specificity (α-decarboxylation vs α-abstraction vs β-elimination) is controlled by the dihedral angle between the **C(α)–X bond to be broken** and the **PLP π-system**.

**Rule**: C(α)–X bond must be oriented roughly perpendicular (~90°) to the PLP plane. This aligns the σ*(C-X) orbital with the PLP π* for maximum stabilization of the resulting carbanion.

For TrpB (α-deprotonation step):
- C(α)–H should be ~90° to PLP plane → α-proton can be abstracted, forms quinonoid
- C(α)–COO⁻ should be in-plane → no decarboxylation

**For your metric proposal (Ch 07)**: a MetaD ground truth that tracks the **distribution of the C(α)–H ⊥ PLP dihedral angle over the trajectory** reveals whether the active site is geometrically competent. This is a chemistry-aware metric that STAR-MD and most ML-for-dynamics work ignores entirely.

**Concrete measurement**: define four atoms in PLP-Ser AEX — `Cα` (Ser), `Cβ` (Ser), `C4'` (PLP ring, aldimine carbon), `N1` (PLP pyridinium N). Compute the improper dihedral Cα-C4'-N1-(reference). Plot histogram over trajectory. Native TrpB peaks at ~85-95°; mis-oriented AEX would peak elsewhere.

---

## 3.4 Quinonoid chirality loss — the geometric argument

A quinonoid intermediate is a **planar**, π-conjugated, six-atom system: PLP ring + imine + Cα. The four substituents on Cα are (H, COO⁻, R-group, C4' imine). After H⁺ is abstracted, Cα becomes sp²-planar.

```
            H                    ---- H+ abstracted ----->          
           /                                                         
    R——C(α)——COO⁻                                  R——C(α)==N——PLP
           \                                                         
            N==PLP                                    COO⁻           
                                                                     
         sp³ Cα (chiral)                            sp² Cα (planar, achiral)
```

The chirality of the starting amino acid (L or D) is **lost** the instant the α-proton leaves. The product chirality depends entirely on which face of the planar Cα is re-protonated.

**Consequence for enzyme design**: You cannot control product stereochemistry by controlling substrate binding alone. You must also control the **re-protonation geometry** — which face of the Cα sp² plane is presented to the H-delivering base.

Raswanth's Slack note on 4/4 expressed exactly this concern. Any reward function that only checks "D-Ser fits in the pocket" is geometrically naive. You need a **second reward term** that checks "the H-delivery residue points at the *si* face of the Cα after H-abstraction".

---

## 3.5 TrpB structure and the COMM domain

TrpB is one β-subunit of a dimer of (αβ)-heterodimers. In the (αβ)₂ tetramer, the α-subunit makes indole from indole-3-glycerol phosphate, passing it through a ~25 Å intramolecular tunnel to the β-site. You are studying only the β-subunit.

**Key structural features of the β-subunit**:
- **Communication (COMM) domain** (residues 97–184): a mobile subdomain that swings between "open" (O), "partially closed" (PC), and "closed" (C) states. Lid closure sequesters the intermediate from bulk water — essential for catalysis.
- **PLP site**: Lys87 covalently linked to PLP C4'. β-β' subunit interface.
- **Substrate binding**: Ser approaches via the β-site gate.

**Path CV you built**: s(R) = 1 at O → 15 at C; λ = 379.77 nm⁻² for 112 Cα atoms in the COMM domain. Tracks the O→C conformational change.

**Why O→C matters for catalysis**: Open state = substrate exchange. Closed state = catalysis-competent geometry. The FES along s(R) tells you the thermodynamic penalty for the closed state — which is a proxy for how tight the engineered variants' allosteric coupling remains after mutations at 104-109/298/301.

---

## 3.6 PDB residues and their meaning

| PDB ID | Residue name | Meaning |
|--------|--------------|---------|
| 5DVZ | **LLP** | Internal aldimine (resting E state), PLP covalent to Lys87 |
| 5DW0 | **PLS** | External aldimine with L-Ser (Ain intermediate) |
| 4HPX | **0JO** | L-aminoacrylate intermediate (A-A) |

These are your reference states for path-CV reference frames and substate labeling. You used all three for the 15-frame O→C reference path.

---

## 3.7 Ligand parameterization — what you did and why it's defensible

PLP is a covalent cofactor with a charged phosphate (−2 at physiological pH), a conjugated pyridinium ring (+1 protonated N1), and an imine linkage. Net formal charge of the PLP-Ser-Lys complex should be −2 (phosphate −2, pyridinium +1, Ser carboxylate −1, Lys +0 since its amine is consumed in the Schiff base).

**Your protocol** (verified in failure-pattern log):
1. Build PLP-Ser-Lys covalent fragment in GaussView or Avogadro
2. Geometry-optimize at **HF/6-31G*** (ESP-compatible basis, following Kollman/Cornell RESP convention)
3. Compute electrostatic potential on a grid
4. Fit atomic charges to reproduce ESP, with constraints (equivalent atoms same charge; total charge to target)
5. Assign GAFF (or GAFF2) bonded parameters via antechamber
6. Generate `.mol2` + `.frcmod` files

**Where this could be wrong**:
- The imine C=N bond length and force constant in GAFF is approximate. For a PLP-Schiff base, the correct bond distance is ~1.28 Å; GAFF may give 1.30 Å. 1-2% error propagates to Dunathan-angle distributions.
- Dihedral around N(imine)-C4' is critical for Dunathan; if GAFF gets the torsional barrier wrong, the geometry distribution shifts. Validate against B3LYP-D3/6-311++G(2d,2p) scan for sanity.
- Protonation state ambiguity: the PLP N1 (pyridinium) is sometimes drawn as +1 sometimes 0. For physiological catalysis at pH ~7, N1 is typically neutral (pKa ~5). Check which state your `.mol2` file uses — a charge error here breaks the whole system by ±1e.

**Better alternatives you did not use but could defend if asked**:
- **OpenFF 2.0 (Sage)** — would give better torsion treatment for the conjugated ring-imine system
- **QM/MM with SCC-DFTB for PLP** — computationally expensive but avoids GAFF torsion errors
- **DFT-derived charges instead of RESP** — CM5 charges (Marenich 2012) are increasingly used as a modern alternative; claimed to be more transferable

**Honest limitation to acknowledge**: Your classical MM simulation cannot model the actual α-H abstraction (bond-breaking). You are studying the **conformational-change timescale** (O↔C, ~μs) not the **chemistry timescale** (proton transfer, ~ps). These are separate physics. If Amin asks about "can you simulate catalysis?", the honest answer is "no, we would need QM/MM; but we can quantify the conformational penalty to reach the catalysis-competent geometry, which is the bottleneck for engineered variants".

---

## 3.8 The D-serine problem — what the lab wants to redesign

Native TrpB has evolved for L-Ser. D-Ser binding:
1. **Fits sterically**: the pocket is not strictly enantioselective in binding (several kinetic studies show D-Ser turnover at reduced rate)
2. **Forms external aldimine**: Schiff base chemistry is not stereochemistry-sensitive at this step
3. **Quinonoid forms**: α-H abstraction works (planar intermediate; chirality lost)
4. **Re-protonation from the re face (by Lys87) → still L-Trp** — because the planar quinonoid has forgotten which enantiomer it came from

**Therefore**: a redesign that simply accepts D-Ser better is **insufficient**. You need to rearrange the active site so reprotonation happens from the *si* face instead. This is typically achieved by:
- Moving Lys87's sidechain position (or mutating Lys87 and introducing a new base elsewhere)
- Altering adjacent residues (104-109, 298, 301 are the target window in the current campaign) to reshape the face-access geometry
- Stabilizing D-products via specific H-bond partners for the newly-positioned COO⁻

**Pipeline implication**: Raswanth's design candidates must be validated not only for D-Ser binding energy but for **reprotonation-face geometry**. The standard MMPBSA binding-free-energy readout does NOT capture this. This is the gap you could fill with a Dunathan-like geometry score computed along an O→C MetaD trajectory.

---

## 3.9 Why TrpB is hard for ML-for-dynamics models

Relative to standard ML-for-dynamics targets (small globular proteins, apo state):

| Feature | Standard target | TrpB |
|---------|-----------------|------|
| Size | <384 AA | ~400 AA β-subunit; ~600 AA α-β |
| Ligands | None | Covalent PLP + substrate + water chains |
| Active-site chemistry | Irrelevant | Dominant |
| Timescales of interest | Local motion (ns) | O↔C (~μs), catalysis (ps) |
| Training data | ATLAS etc. | Essentially zero comparable systems |

STAR-MD and similar models trained on ATLAS (apo, small, no ligands) have **zero training signal** for TrpB-like systems. This is explicitly acknowledged in STAR-MD's Conclusion section ("extend to complexes and small-molecule interactions"). It is not a criticism of STAR-MD — it is an observation about the training regime.

Your MetaD work on TrpB-PLP-AEX produces exactly the kind of ligand-bound conformational ensemble that ML models will eventually need for training or validation. This is the bridge: **chemistry-aware MetaD ground truth → training/validation data for future ligand-aware ML models**.

---

## 3.10 Pros/cons — your PLP parameterization + MD stack for enzyme chemistry

**Strengths**:
- GAFF + RESP + ff14SB is the 2015-vintage consensus for enzyme MD. Huge literature.
- Your charge balance and protonation state verification passed sanity checks (39,268 atoms, neutral system, 4 Na⁺).
- Covalent Lys87-PLP-Ser linkage handled correctly via AmberTools tleap.

**Weaknesses**:
- GAFF torsions around imine not bulletproof — ~10% error possible in Dunathan angle distribution
- No QM/MM: cannot simulate chemistry step
- No polarizable force field: PLP's ionic phosphate + pyridinium benefits from explicit polarization; AMBER ff14SB is fixed-charge

**When this stack fails**:
- Claiming rate constants for the α-H abstraction step (needs QM/MM)
- Claiming binding ΔG with <1 kcal/mol accuracy (MMPBSA noise floor is 2-3 kcal/mol)
- Claiming "this variant will have D-selectivity" without explicit reprotonation-geometry analysis (the planar quinonoid problem)

**What it's good for**:
- Conformational ensembles over μs timescales → O↔C FES
- Qualitative trends across mutant variants (does the O→C barrier go up or down?)
- Ground truth for ML validation (discussed in Ch 07)

---

## 3.11 Video / tutorial recommendations

- **Richard Silverman — The Organic Chemistry of Enzyme-Catalyzed Reactions** (textbook, not video; the canonical reference for PLP chemistry chapter)
- **Frances Arnold lectures on enzyme evolution** (YouTube) — for directed evolution + TrpB context
- **David Baker / Possu Huang protein design talks** (YouTube) — for how theozyme thinking fits with computational design
- **PLP enzyme mechanism videos** on YouTube (search "PLP Dunathan hypothesis lecture") — several biochemistry departments have posted
- For RESP / antechamber hands-on: **AMBER tutorials site**, Tutorial A1 (charge derivation). Written walkthroughs, clearer than video.

---

## 3.12 "If someone asks me X, I say Y"

- **Q**: Why can't simply fitting D-serine into the active site give D-Trp?
  **A**: Because the catalytic mechanism routes through a planar quinonoid intermediate which is achiral. Stereochemistry is re-set at the reprotonation step, not at binding. Any successful redesign must control the reprotonation face.

- **Q**: What's the Dunathan hypothesis?
  **A**: In PLP enzymes, the C(α)–X bond that breaks must align roughly perpendicular to the PLP plane, so the σ*-π* orbital overlap stabilizes the transition state. For TrpB α-abstraction, C(α)–H ⊥ PLP plane is the catalysis-competent geometry.

- **Q**: Why GAFF and not something more modern?
  **A**: GAFF + RESP is the reference protocol from Osuna 2019 which we're replicating. If starting fresh, OpenFF 2.0 or GAFF2 would be defensible. Torsion errors in GAFF around the conjugated ring-imine are ~5-10% — measurable but not dominant for the O↔C conformational timescale.

- **Q**: Can you simulate the α-H abstraction step?
  **A**: No. That's a bond-breaking quantum-mechanical event; classical MM cannot model it. For that, we would need QM/MM (e.g. AMBER-ORCA or CP2K). Our simulation targets the conformational-change timescale (O↔C), which is the rate-limiting step in many variants, not the chemistry timescale.

- **Q**: What's your unique angle on enzyme-dynamics benchmarking?
  **A**: Current benchmarks like ATLAS have zero PLP-dependent or ligand-bound enzymes. Our TrpB-PLP-AEX MetaD ground truth fills that gap, and we can propose chemistry-aware metrics (Dunathan angle distribution, reprotonation-face geometry, lid-closure state occupancy) that standard Cα-RMSD evaluations miss.

---

**Next**: Chapter 04 (Protein design ML) — how Raswanth's RFD3 → MPNN → RF3 → GRPO pipeline works and where chemistry-aware judgment could improve it.
