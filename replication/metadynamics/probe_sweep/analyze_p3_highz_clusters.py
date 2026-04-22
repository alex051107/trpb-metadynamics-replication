#!/usr/bin/env python3
"""Cluster the high-z tail of probe_P3 against audited TrpB references."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import MDAnalysis as mda
import numpy as np
from MDAnalysis.analysis.rms import rmsd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

COMMON_RESIDS = [*range(97, 185), *range(282, 285), *range(286, 306)]
SELECTION_EXPR = " or ".join(f"resid {resid}" for resid in COMMON_RESIDS)
TRAJ_SELECTION = f"name CA and ({SELECTION_EXPR})"


@dataclass(frozen=True)
class ReferenceSpec:
    label: str
    pdb_path: Path
    chain: str


REFERENCE_SPECS = [
    ReferenceSpec("1WDW", Path("/work/users/l/i/liualex/AnimaLab/structures/1WDW.pdb"), "B"),
    ReferenceSpec("5DW0", Path("/work/users/l/i/liualex/AnimaLab/structures/5DW0.pdb"), "A"),
    ReferenceSpec("5DW3", Path("/work/users/l/i/liualex/AnimaLab/structures/5DW3.pdb"), "A"),
    ReferenceSpec("3CEP", Path("/work/users/l/i/liualex/AnimaLab/structures/3CEP.pdb"), "B"),
    ReferenceSpec("4HPX", Path("/work/users/l/i/liualex/AnimaLab/structures/4HPX.pdb"), "B"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--probe-dir",
        type=Path,
        default=Path("/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/probe_P3"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/probe_P3/P3_highz_cluster_analysis.md"),
    )
    parser.add_argument("--seed", type=int, default=20260421)
    return parser.parse_args()


def load_reference_coords() -> dict[str, np.ndarray]:
    coords = {}
    for spec in REFERENCE_SPECS:
        u = mda.Universe(str(spec.pdb_path))
        ordered = []
        for resid in COMMON_RESIDS:
            sel = u.select_atoms(f"chainID {spec.chain} and name CA and resid {resid}")
            if len(sel) == 0:
                raise SystemExit(f"{spec.label} chain {spec.chain} missing CA for resid {resid}")
            ordered.append(sel[0].position.copy())
        coords[spec.label] = np.array(ordered, dtype=float)
    return coords


def load_traj_and_highz(probe_dir: Path):
    colvar = np.loadtxt(probe_dir / "COLVAR", comments="#")
    time_to_z = {int(round(t)): float(z) for t, z in zip(colvar[:, 0], colvar[:, 1 + 1])}

    u = mda.Universe(str(probe_dir / "start.gro"), str(probe_dir / "metad.xtc"))
    sel = u.select_atoms(TRAJ_SELECTION)
    if len(sel) != len(COMMON_RESIDS):
        raise SystemExit(f"trajectory selection has {len(sel)} atoms, expected {len(COMMON_RESIDS)}")
    if not np.array_equal(sel.resids, np.array(COMMON_RESIDS, dtype=int)):
        raise SystemExit("trajectory residue order mismatch")

    times = []
    z_values = []
    for ts in u.trajectory:
        time_ps = int(round(ts.time))
        if time_ps not in time_to_z:
            raise SystemExit(f"trajectory time {time_ps} ps missing in COLVAR")
        times.append(time_ps)
        z_values.append(time_to_z[time_ps])

    times = np.array(times, dtype=int)
    z_values = np.array(z_values, dtype=float)
    z_threshold = float(np.quantile(z_values, 0.9))
    highz_mask = z_values >= z_threshold
    frame_indices = np.where(highz_mask)[0]
    if len(frame_indices) < 10:
        raise SystemExit(f"high-z subset too small: {len(frame_indices)} frames")

    return u, sel, times, z_values, z_threshold, frame_indices


def compute_feature_matrix(u, sel, frame_indices: np.ndarray, reference_coords: dict[str, np.ndarray]):
    labels = [spec.label for spec in REFERENCE_SPECS]
    feature_rows = []
    kept_times = []
    for idx in frame_indices:
        u.trajectory[idx]
        coords = sel.positions.copy()
        feature_rows.append([rmsd(coords, reference_coords[label], superposition=True) for label in labels])
        kept_times.append(int(round(u.trajectory.time)))
    return np.array(feature_rows, dtype=float), np.array(kept_times, dtype=int), labels


def choose_k(features: np.ndarray, seed: int):
    best = None
    max_k = min(5, len(features) - 1)
    for k in range(3, max_k + 1):
        model = KMeans(n_clusters=k, random_state=seed, n_init=20)
        labels = model.fit_predict(features)
        score = silhouette_score(features, labels)
        if best is None or score > best[0]:
            best = (score, k, labels, model)
    if best is None:
        raise SystemExit("unable to choose cluster count")
    return best


def interpret(cluster_rows, pc_like_fraction):
    top_cluster = max(cluster_rows, key=lambda row: row["frame_fraction"])
    if top_cluster["closest_reference"] in {"5DW0", "5DW3"} or pc_like_fraction >= 0.5:
        verdict = "PC-like"
        detail = (
            "The dominant high-z population sits closer to PC references (5DW0/5DW3) than to the open or closed endpoints."
        )
    else:
        verdict = "generic diffusion"
        detail = (
            "The high-z population does not consolidate around the PC references; it looks more like off-path wandering than PC-like pre-closure."
        )
    return verdict, detail


def write_markdown(
    output_path: Path,
    times: np.ndarray,
    z_values: np.ndarray,
    z_threshold: float,
    frame_indices: np.ndarray,
    cluster_rows,
    silhouette: float,
    chosen_k: int,
    verdict: str,
    detail: str,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P3 high-z cluster analysis",
        "",
        "## Method",
        "",
        "- Probe: `probe_P3` completed 10 ns trajectory (`metad.xtc`, 10 ps stride) with matching `COLVAR`.",
        f"- High-z subset: top 10% of XTC-aligned frames, threshold `z >= {z_threshold:.6f}` ({len(frame_indices)} / {len(times)} frames).",
        "- Atom set: 111 common Cα atoms from residues 97-184 and 282-305, excluding residue 285 because `5DW3` chain A lacks it.",
        "- Reference-chain mapping follows the earlier CV audit convention: `1WDW=B`, `3CEP=B`, `4HPX=B`, `5DW0=A`, `5DW3=A`.",
        f"- Clustering: KMeans on the 5-reference RMSD feature vectors, `k` chosen by silhouette over 3..5; selected `k={chosen_k}` with silhouette `{silhouette:.4f}`.",
        "",
        "## Cluster Table",
        "",
        "| Cluster | Closest reference | Mean RMSD (A) | Frame fraction | Mean z | Mean time (ps) |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for row in cluster_rows:
        lines.append(
            f"| C{row['cluster']} | {row['closest_reference']} | {row['mean_rmsd_a']:.3f} | {row['frame_fraction']:.3f} | {row['mean_z']:.6f} | {row['mean_time_ps']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"{verdict}: {detail}",
            "",
            "Reference ordering for the RMSD feature vectors was `1WDW, 5DW0, 5DW3, 3CEP, 4HPX`.",
        ]
    )

    output_path.write_text("\n".join(lines) + "\n")


def main():
    args = parse_args()
    ref_coords = load_reference_coords()
    u, sel, times, z_values, z_threshold, frame_indices = load_traj_and_highz(args.probe_dir)
    features, kept_times, ref_labels = compute_feature_matrix(u, sel, frame_indices, ref_coords)
    silhouette, chosen_k, cluster_labels, _ = choose_k(features, args.seed)

    cluster_rows = []
    pc_like_fraction = 0.0
    for cluster_id in sorted(set(cluster_labels)):
        mask = cluster_labels == cluster_id
        mean_vec = features[mask].mean(axis=0)
        closest_idx = int(np.argmin(mean_vec))
        closest_ref = ref_labels[closest_idx]
        fraction = float(mask.mean())
        if closest_ref in {"5DW0", "5DW3"}:
            pc_like_fraction += fraction
        cluster_rows.append(
            {
                "cluster": int(cluster_id) + 1,
                "closest_reference": closest_ref,
                "mean_rmsd_a": float(mean_vec[closest_idx]),
                "frame_fraction": fraction,
                "mean_z": float(z_values[frame_indices][mask].mean()),
                "mean_time_ps": float(kept_times[mask].mean()),
            }
        )

    verdict, detail = interpret(cluster_rows, pc_like_fraction)
    write_markdown(
        args.output_md,
        times,
        z_values,
        z_threshold,
        frame_indices,
        cluster_rows,
        silhouette,
        chosen_k,
        verdict,
        detail,
    )
    print(f"verdict={verdict}")
    print(f"clusters={cluster_rows}")
    print(f"output_md={args.output_md}")


if __name__ == "__main__":
    main()
