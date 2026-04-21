"""Step 3: O-endpoint local tangent alignment analysis.

For each snapshot from an early O-basin MetaD trajectory:
    1. Extract the 112 Cα of the COMM+base selection.
    2. Kabsch-align to path frame 1 (the O endpoint).
    3. Compute Δx_t = x_t − x_0 (N_atoms × 3).
    4. Compute the local O-end tangent:
           t_O = (x_2 − x_1) + 0.5·(x_3 − x_1)
    5. Report:
           ‖Δx_t‖   — magnitude of real Cartesian motion
           cos(θ)   — alignment of motion with chord tangent at O
           f_perp   — fractional off-tangent displacement

Interpretation (PM 2026-04-21):
    High ‖Δx_t‖, low cos(θ), high f_perp, with s stuck ≈ 1 in COLVAR → real motion
    exists but is perpendicular to the linear chord → path geometry weak at O endpoint.

Run locally or on Longleaf. Input:
    - path_gromacs.pdb (frames 1,2,3 needed)
    - xtc or multi-MODEL pdb trajectory of an early O-basin segment
    - (optional) matching COLVAR for cross-referencing s(t)
"""

import argparse
import sys
from pathlib import Path
import numpy as np

try:
    import MDAnalysis as mda
except ImportError:
    sys.exit("MDAnalysis required: pip install MDAnalysis")


COMM_RESIDS = list(range(97, 185))  # 97..184 inclusive
BASE_RESIDS = list(range(282, 306))  # 282..305 inclusive
EXPECTED_NATOMS = len(COMM_RESIDS) + len(BASE_RESIDS)  # 112


def load_frame_from_pdb(pdb_path: Path, model_idx: int) -> np.ndarray:
    """Return (N_atoms, 3) Cα coords for MODEL=model_idx (1-indexed) from a multi-MODEL PDB."""
    u = mda.Universe(str(pdb_path))
    if hasattr(u.trajectory, "n_frames") and u.trajectory.n_frames > 1:
        u.trajectory[model_idx - 1]
    ca = u.select_atoms("name CA")
    if len(ca) != EXPECTED_NATOMS:
        raise ValueError(f"{pdb_path} MODEL {model_idx}: expected {EXPECTED_NATOMS} Cα, got {len(ca)}")
    return ca.positions.copy()


def kabsch(ref: np.ndarray, mov: np.ndarray) -> np.ndarray:
    """Return mov rotated + translated onto ref (optimal RMSD). Both shape (N,3)."""
    rc = ref.mean(axis=0)
    mc = mov.mean(axis=0)
    R = ref - rc
    M = mov - mc
    H = M.T @ R
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    rot = Vt.T @ D @ U.T
    return (M @ rot.T) + rc


def analyse(traj: Path, topol: Path, path_pdb: Path, ca_selection: str, stride: int, max_frames: int):
    x1 = load_frame_from_pdb(path_pdb, 1)
    x2 = load_frame_from_pdb(path_pdb, 2)
    x3 = load_frame_from_pdb(path_pdb, 3)
    t_O = (x2 - x1) + 0.5 * (x3 - x1)
    t_O_flat = t_O.reshape(-1)
    t_norm = np.linalg.norm(t_O_flat)
    print(f"# O-end tangent magnitude ‖t_O‖ = {t_norm:.3f} Å  (reference scale)")

    u = mda.Universe(str(topol), str(traj))
    sel = u.select_atoms(ca_selection)
    if len(sel) != EXPECTED_NATOMS:
        raise ValueError(f"trajectory selection '{ca_selection}' matched {len(sel)} atoms, expected {EXPECTED_NATOMS}. "
                         "Adjust --ca-selection (e.g. 'name CA and resid 97-184 282-305').")

    print("# frame_idx  time_ps    ‖Δx_t‖(Å)    cos(θ)    f_perp    status")
    rows = []
    for ts in u.trajectory[::stride]:
        if max_frames and len(rows) >= max_frames:
            break
        x_t_raw = sel.positions.copy()
        x_t = kabsch(x1, x_t_raw)
        dx = (x_t - x1).reshape(-1)
        dx_norm = np.linalg.norm(dx)
        if dx_norm < 1e-6 or t_norm < 1e-6:
            cos_th = 0.0
            f_perp = 0.0
            status = "tiny-motion"
        else:
            cos_th = float(np.dot(dx, t_O_flat) / (dx_norm * t_norm))
            proj = (np.dot(dx, t_O_flat) / (t_norm * t_norm)) * t_O_flat
            perp = dx - proj
            f_perp = float(np.linalg.norm(perp) / dx_norm)
            if cos_th < 0.2 and f_perp > 0.9 and dx_norm > 0.5:
                status = "OFF-TANGENT (path suspect)"
            elif cos_th > 0.7:
                status = "aligned"
            else:
                status = "mixed"
        rows.append((ts.frame, ts.time, dx_norm, cos_th, f_perp, status))
        print(f"{ts.frame:8d}  {ts.time:9.1f}  {dx_norm:10.3f}  {cos_th:+8.3f}  {f_perp:8.3f}  {status}")

    # summary
    dxs = np.array([r[2] for r in rows])
    cos = np.array([r[3] for r in rows])
    fps = np.array([r[4] for r in rows])
    print("\n# SUMMARY")
    print(f"# n_frames_analysed = {len(rows)}")
    print(f"# ‖Δx_t‖ range = [{dxs.min():.2f}, {dxs.max():.2f}] Å   mean = {dxs.mean():.2f}")
    print(f"# cos(θ)   range = [{cos.min():+.3f}, {cos.max():+.3f}]   mean = {cos.mean():+.3f}")
    print(f"# f_perp   range = [{fps.min():.3f}, {fps.max():.3f}]   mean = {fps.mean():.3f}")
    off = np.sum((cos < 0.2) & (fps > 0.9) & (dxs > 0.5))
    print(f"# frames flagged OFF-TANGENT = {off} / {len(rows)}  ({100*off/max(1,len(rows)):.1f}%)")
    if off / max(1, len(rows)) > 0.5 and dxs.mean() > 0.5:
        print("# VERDICT: >50% of early frames have real motion that is ~perpendicular to the O-end chord.")
        print("#          This supports: linear Cartesian path is scientifically weak at the O endpoint.")
    elif dxs.mean() < 0.3:
        print("# VERDICT: walker is not moving much in Cartesian space either; the problem is NOT path tangent.")
    else:
        print("# VERDICT: motion is mixed relative to the tangent; tangent hypothesis not strongly supported.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trajectory", required=True, help="xtc / trr / multi-MODEL pdb of early O-basin MD")
    ap.add_argument("--topology", required=True, help="gro / pdb / tpr matching the trajectory")
    ap.add_argument("--path-pdb", required=True, help="path_gromacs.pdb (15 MODELs)")
    ap.add_argument("--ca-selection", default="name CA and resid 97-184 282-305",
                    help="MDAnalysis selection string for the 112 Cα")
    ap.add_argument("--stride", type=int, default=10, help="sample every N-th frame")
    ap.add_argument("--max-frames", type=int, default=200, help="cap on frames analysed")
    args = ap.parse_args()
    analyse(Path(args.trajectory), Path(args.topology), Path(args.path_pdb),
            args.ca_selection, args.stride, args.max_frames)


if __name__ == "__main__":
    main()
