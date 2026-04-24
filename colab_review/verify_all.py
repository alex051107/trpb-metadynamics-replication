#!/usr/bin/env python3
"""
Independent numerical verification for TrpB path-piecewise audit (2026-04-23).

Recomputes every numerical claim in the most recent path-piecewise audit
plus the 45324928 Miguel fallback run analysis. Pure numpy — no
MDAnalysis dependency. Runs anywhere (local Python 3.9+ or Google Colab).

Inputs expected in the same directory:
  * HILLS, COLVAR                — from 45324928 Longleaf output
  * direct_path_gromacs.pdb      — single_walker/path_gromacs.pdb (15 models, 112 Cα)
  * 1WDW.pdb, 3CEP.pdb           — O, C anchors
  * 5DW0.pdb, 5DW3.pdb, 5DVZ.pdb — PC candidates

Output: PASS/FAIL verdict per claim. Discrepancy > tolerance → FAIL.

Usage:
  python verify_all.py
"""

import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent

# ============================================================================
# Shared constants
# ============================================================================
COMM_RESIDUES = list(range(97, 185))
BASE_RESIDUES = list(range(282, 306))
ATOMS_OF_INTEREST = set(COMM_RESIDUES + BASE_RESIDUES)
LAMBDA = 3.77
CHAIN_MAP = {"1WDW": "B", "3CEP": "B",
             "5DW0": "A", "5DW3": "A", "5DVZ": "A"}

# ============================================================================
# Helpers
# ============================================================================
def parse_pdb_ca(path, chain, residues):
    found = {}
    with open(path) as f:
        for line in f:
            if not line.startswith("ATOM  "):
                continue
            if line[12:16].strip() != "CA" or line[16] not in " A":
                continue
            if line[21] != chain:
                continue
            try:
                r = int(line[22:26])
            except ValueError:
                continue
            if r not in residues or r in found:
                continue
            found[r] = np.array([float(line[30:38]),
                                 float(line[38:46]),
                                 float(line[46:54])])
    return found


def parse_multimodel(path):
    frames, cur = [], []
    with open(path) as f:
        for line in f:
            if line.startswith("MODEL"):
                cur = []
            elif line.startswith("ATOM"):
                cur.append([float(line[30:38]),
                            float(line[38:46]),
                            float(line[46:54])])
            elif line.startswith("ENDMDL") and cur:
                frames.append(np.array(cur))
                cur = []
    return frames


def kabsch_msd(m, t):
    cm, ct = m.mean(0), t.mean(0)
    M, T = m - cm, t - ct
    H = M.T @ T
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    return float(np.mean(np.sum(((R @ M.T).T - T)**2, axis=1)))


def project_pathmsd(cand, frames, lam):
    """PATHMSD s(R), z(R) with log-sum-exp stability. Fixed 2026-04-23
    (was using shift.max() AFTER in-place subtraction → z_biased by -MSD_min)."""
    msds = np.array([kabsch_msd(cand, fr) for fr in frames])
    raw = -lam * msds
    m = raw.max()
    stable = raw - m
    w = np.exp(stable)
    i = np.arange(1, len(frames) + 1)
    s = float(np.sum(i * w) / np.sum(w))
    log_sum = m + np.log(w.sum())
    z = float(-log_sum / lam)
    return s, z, msds


# ============================================================================
# Claim registry
# ============================================================================
PASSED, FAILED = [], []

def check(label, expected, actual, tol, unit=""):
    diff = abs(expected - actual)
    ok = diff <= tol
    (PASSED if ok else FAILED).append(label)
    marker = "✓" if ok else "✗"
    print(f"  {marker}  {label}: expected {expected}{unit}, actual {actual:.4f}{unit}, "
          f"|Δ|={diff:.4f} (tol {tol})")


# ============================================================================
# CLAIM 1 — direct path geometry
# ============================================================================
print("\n━━━ CLAIM 1: direct 1WDW→3CEP path geometry ━━━")
frames = parse_multimodel(ROOT / "direct_path_gromacs.pdb")
assert len(frames) == 15, f"expected 15 models, got {len(frames)}"
assert len(frames[0]) == 112, f"expected 112 atoms, got {len(frames[0])}"
print(f"  loaded {len(frames)} models × {len(frames[0])} atoms")

adj_msds = [kabsch_msd(frames[i], frames[i+1]) for i in range(14)]
mean_msd = np.mean(adj_msds)
cv = np.std(adj_msds) / mean_msd
lam_actual = 2.3 / mean_msd

check("direct path ⟨MSD⟩ (Å²)", 0.61, mean_msd, tol=0.01)
check("direct path CV (uniform spacing)", 0.0, cv, tol=0.01)
check("direct path λ (Å⁻²) from Branduardi", 3.80, lam_actual, tol=0.05)
# Note: plumed.dat stores 3.77 (rounded down a bit); keep that consistent
check("plumed.dat LAMBDA=3.77 vs recomputed", 3.77, lam_actual, tol=0.05)


# ============================================================================
# CLAIM 2 — piecewise 5DW0 path numbers
# ============================================================================
print("\n━━━ CLAIM 2: piecewise 1WDW→5DW0→3CEP (MODEL 8) ━━━")

def build_piecewise(pc_code):
    O_d = parse_pdb_ca(ROOT / "1WDW.pdb", "B", ATOMS_OF_INTEREST)
    PC_d = parse_pdb_ca(ROOT / f"{pc_code}.pdb", CHAIN_MAP[pc_code], ATOMS_OF_INTEREST)
    C_d = parse_pdb_ca(ROOT / "3CEP.pdb", "B", ATOMS_OF_INTEREST)
    common = sorted(set(O_d) & set(PC_d) & set(C_d))

    def stack(d):
        return np.stack([d[r] for r in common])

    O, PC, C = stack(O_d), stack(PC_d), stack(C_d)

    # Kabsch PC, C onto O
    def kabsch_apply(mob, tgt):
        cm, ct = mob.mean(0), tgt.mean(0)
        M, T = mob - cm, tgt - ct
        H = M.T @ T
        U, _, Vt = np.linalg.svd(H)
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        D = np.diag([1.0, 1.0, d])
        R = Vt.T @ D @ U.T
        return (R @ M.T).T + ct
    PC_a, C_a = kabsch_apply(PC, O), kabsch_apply(C, O)

    seg1 = [(1 - i/7) * O + (i/7) * PC_a for i in range(8)]
    seg2 = [(1 - i/7) * PC_a + (i/7) * C_a for i in range(8)]
    frames = seg1 + seg2[1:]

    rmsd_o_pc = np.sqrt(kabsch_msd(O, PC_a))
    rmsd_pc_c = np.sqrt(kabsch_msd(PC_a, C_a))
    return frames, rmsd_o_pc, rmsd_pc_c, len(common)


for pc_code, expected in [
    ("5DW0", {"rmsd_o_pc": 1.571, "rmsd_pc_c": 11.061,
              "msd_s1": 0.0504, "msd_s2": 2.4969,
              "cv": 0.960, "single_lam": 1.806}),
    ("5DW3", {"rmsd_o_pc": 1.447, "rmsd_pc_c": 10.988,
              "msd_s1": 0.0427, "msd_s2": 2.4638,
              "cv": 0.966, "single_lam": 1.835}),
]:
    frames, rmsd_o_pc, rmsd_pc_c, n_common = build_piecewise(pc_code)
    adj = [kabsch_msd(frames[i], frames[i+1]) for i in range(14)]
    msd_s1 = float(np.mean(adj[:7]))   # O→PC
    msd_s2 = float(np.mean(adj[7:]))   # PC→C
    mean_all = float(np.mean(adj))
    cv = float(np.std(adj) / mean_all)
    single_lam = 2.3 / mean_all

    print(f"\n  ── PC = {pc_code} (chain {CHAIN_MAP[pc_code]}, {n_common} common resids) ──")
    check(f"{pc_code}: O↔PC RMSD (Å)", expected["rmsd_o_pc"], rmsd_o_pc, tol=0.01)
    check(f"{pc_code}: PC↔C RMSD (Å)", expected["rmsd_pc_c"], rmsd_pc_c, tol=0.01)
    check(f"{pc_code}: ⟨MSD⟩ O→PC (Å²)", expected["msd_s1"], msd_s1, tol=0.001)
    check(f"{pc_code}: ⟨MSD⟩ PC→C (Å²)", expected["msd_s2"], msd_s2, tol=0.005)
    check(f"{pc_code}: neighbor_msd_cv", expected["cv"], cv, tol=0.01)
    check(f"{pc_code}: single λ (Å⁻²)", expected["single_lam"], single_lam, tol=0.005)


# ============================================================================
# CLAIM 3 — PC anchor projection onto direct path
# ============================================================================
print("\n━━━ CLAIM 3: PC-candidate projection onto direct path (λ=3.77) ━━━")
direct_frames = parse_multimodel(ROOT / "direct_path_gromacs.pdb")
resid_order = sorted(ATOMS_OF_INTEREST)

for code, expected_s in [("5DW0", 1.069), ("5DW3", 1.075), ("5DVZ", 1.067)]:
    d = parse_pdb_ca(ROOT / f"{code}.pdb", CHAIN_MAP[code], ATOMS_OF_INTEREST)
    if len(d) < 100:
        FAILED.append(f"{code} load failed (only {len(d)} Cα)")
        continue
    missing = [r for r in resid_order if r not in d]
    common = [r for r in resid_order if r in d]
    coords = np.stack([d[r] for r in common])
    if len(common) == 112:
        use_frames = direct_frames
    else:
        idx = [resid_order.index(r) for r in common]
        use_frames = [fr[idx] for fr in direct_frames]
    s, z, msds = project_pathmsd(coords, use_frames, LAMBDA)
    msd_min = float(msds.min())
    check(f"{code}: s(R) on direct path", expected_s, s, tol=0.005)
    # z should be close to MSD_min for highly-peaked kernel (5DW0 case)
    if z < msd_min - 0.1 or z > msd_min + 0.5:
        FAILED.append(f"{code}: z sanity check (z={z:.3f} vs msd_min={msd_min:.3f})")
        print(f"  ✗  {code}: z={z:.3f} but msd_min={msd_min:.3f} — unexpected relationship")
    else:
        PASSED.append(f"{code}: z sanity")
        print(f"  ✓  {code}: z={z:.3f}, MSD_min={msd_min:.3f} → kernel-averaged off-path Å²")


# ============================================================================
# CLAIM 4 — 45324928 Miguel fallback COLVAR / HILLS statistics
# ============================================================================
print("\n━━━ CLAIM 4: 45324928 Miguel fallback run numerics ━━━")
colvar = np.loadtxt(ROOT / "COLVAR", comments="#")
s_col = colvar[:, 1]
z_col = colvar[:, 2]
bias = colvar[:, 3]
uwall = colvar[:, 4]

max_s = s_col.max()
t_max = colvar[s_col.argmax(), 0]
p95_s = np.percentile(s_col, 95)
frac_z_above_23 = (z_col > 2.3).mean()
frac_wall_active = (uwall > 0.01).mean()

check("max_s (all-time)", 1.4964, max_s, tol=0.001)
check("time of max_s (ps)", 1300.6, t_max, tol=0.5)
check("p95(s)", 1.2835, p95_s, tol=0.01)
check("fraction(z > 2.3)", 0.2325, frac_z_above_23, tol=0.005)
check("fraction(wall active)", 0.0587, frac_wall_active, tol=0.005)

hills = np.loadtxt(ROOT / "HILLS", comments="#")
sig_ss = hills[:, 3]
sig_zz = hills[:, 4]
height = hills[:, 6]

check("σ_ss median", 0.0304, float(np.median(sig_ss)), tol=0.001)
check("σ_ss min", 0.0036, float(sig_ss.min()), tol=0.001)
check("σ_zz median", 0.1972, float(np.median(sig_zz)), tol=0.005)
check("σ_zz max", 4.0039, float(sig_zz.max()), tol=0.01)
check("height median (W-T scaling)", 0.1333, float(np.median(height)), tol=0.005)
check("n_hills", 1880, len(hills), tol=5)


# ============================================================================
# Summary
# ============================================================================
print("\n" + "═" * 70)
print(f" SUMMARY: {len(PASSED)} PASS, {len(FAILED)} FAIL")
print("═" * 70)
if FAILED:
    print("\nFailures:")
    for f in FAILED:
        print(f"  ✗ {f}")
    print("\nReview the discrepancy before trusting the audit.")
    exit(1)
else:
    print("\nAll claims reproduce within tolerance.")
    print("The path-piecewise audit verdict (reject PC-at-MODEL8 single-λ) is")
    print("mathematically grounded. Next: whether the direct path itself is")
    print("rate-limiting (wall4 45448011 + 45324928 @ 8-10 ns gate) remains open.")
