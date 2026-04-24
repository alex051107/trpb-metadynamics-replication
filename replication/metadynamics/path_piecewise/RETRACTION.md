# RETRACTION (2026-04-23, same day)

The path_piecewise audit in this directory was **conducted on the
buggy naive-resid-mapping reference path** (single_walker/path_gromacs.pdb).
Its negative conclusion — "βPC labels are O-proximal, not geometric
midpoint" — is **itself an artifact of the bug it was supposed to test
around**.

## What the original audit claimed

| Structure | s(R) on naive path | Verdict |
|---|---|---|
| 5DW0 chain A | 1.069 | "O-proximal, not PC" |
| 5DW3 chain A | 1.075 | "O-proximal, not PC" |
| 5DVZ chain A | 1.067 | "O-proximal, not PC" |

## What the corrected audit shows

After fixing cross-species residue mapping (Needleman-Wunsch 1WDW-B vs
3CEP-B → uniform +5 offset, see FP-034 and `../path_seqaligned/`):

| Structure | s(R) on sequence-aligned path | Verdict (updated) |
|---|---|---|
| 5DW0 chain A | **9.455** | mid-path PC intermediate ✓ |
| 5DW3 chain A | **8.508** | mid-path PC intermediate ✓ |
| 5DVZ chain A | **5.371** | early PC intermediate ✓ |
| 4HPX chain A | 14.898 | C-end reference ✓ |

**The biological βPC labels were correct all along.** They land at
plausible geometric midpoints once the path is built with proper
residue-to-residue mapping. Our negative finding was produced by the
same bug it was trying to work around.

## What remains valid from this directory

- `generate_piecewise_path.py` — works fine, correctly audits a
  user-supplied 3-anchor path. But the specific PC-at-MODEL-8 design it
  tested was not the right question.
- `scan_pc_anchors.py` — works fine, the PATHMSD projection logic is
  correct (after z(R) log-sum-exp bug fix at commit 0dc49ab). The
  updated projection values on the corrected path are in
  `../path_seqaligned/VERIFICATION_REPORT.md`.

## What should be ignored

- `README.md` verdict section ("5DW0/5DW3 are O-proximal") — invalid
- Both path_5DW0/summary.txt and path_5DW3/summary.txt verdicts — the
  MODEL-8 neighbor_msd_cv = 0.96 number is still mathematically correct
  for those specific piecewise paths, but the conclusion that βPC
  labels can't serve as midpoints is wrong

## Why we keep this directory at all

Historical record of the debugging path. The FP-034 write-up explicitly
cites path_piecewise as a downstream-contamination example so future
agents see the chain: naive mapping bug → spurious βPC rejection →
3 days lost debugging → FP-034 discovery. Deleting this directory
would erase that lesson.
