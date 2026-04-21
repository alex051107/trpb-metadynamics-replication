"""Purpose: inspect a HILLS file for adaptive-width saturation and emit a 3-panel diagnostic plot + JSON summary."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

EXPECTED_FIELDS = [
    "time", "path.sss", "path.zzz",
    "sigma_path.sss_path.sss", "sigma_path.zzz_path.zzz", "sigma_path.zzz_path.sss",
    "height", "biasf",
]


def read_hills(path):
    with open(path) as fh:
        header = fh.readline().strip().split()
    assert header[:2] == ["#!", "FIELDS"], f"unexpected first line: {header[:2]}"
    fields = header[2:]
    assert fields == EXPECTED_FIELDS, f"FIELDS mismatch: got {fields}"
    data = np.loadtxt(path, comments="#")
    return data, fields


def saturation_stats(data, sigma_min_s, sigma_max_s, sigma_min_z, sigma_max_z):
    sigma_s = data[:, 3]
    sigma_zz = data[:, 4]
    n = len(data)
    return {
        "total_hills": int(n),
        "sigma_s_at_floor": int(np.sum(sigma_s <= sigma_min_s + 1e-4)),
        "sigma_s_at_floor_pct": float(np.mean(sigma_s <= sigma_min_s + 1e-4) * 100),
        "sigma_s_at_ceiling": int(np.sum(sigma_s >= sigma_max_s - 1e-4)),
        "sigma_s_at_ceiling_pct": float(np.mean(sigma_s >= sigma_max_s - 1e-4) * 100),
        "sigma_zz_below_floor": int(np.sum(sigma_zz < sigma_min_z)),
        "sigma_zz_below_floor_pct": float(np.mean(sigma_zz < sigma_min_z) * 100),
        "sigma_s_min": float(sigma_s.min()),
        "sigma_s_max": float(sigma_s.max()),
        "sigma_s_mean": float(sigma_s.mean()),
    }


def plot(data, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = data[:, 0] / 1000.0
    s = data[:, 1]
    z = data[:, 2]
    sigma_s = data[:, 3]
    sigma_zz = data[:, 4]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].plot(t, sigma_s, lw=0.5)
    axes[0].set_xlabel("time (ns)"); axes[0].set_ylabel(r"$\sigma_s$"); axes[0].set_title("sigma_s vs time")
    axes[1].plot(t, sigma_zz, lw=0.5)
    axes[1].set_xlabel("time (ns)"); axes[1].set_ylabel(r"$\sigma_{zz}$"); axes[1].set_title("sigma_zz vs time")
    axes[2].scatter(s, z, s=1, alpha=0.3)
    axes[2].set_xlabel("s"); axes[2].set_ylabel("z"); axes[2].set_title("(s,z) hill centers")
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hills", type=Path)
    ap.add_argument("--smin-s", type=float, default=0.3)
    ap.add_argument("--smax-s", type=float, default=1.0)
    ap.add_argument("--smin-z", type=float, default=0.005)
    ap.add_argument("--smax-z", type=float, default=0.05)
    ap.add_argument("--out-png", type=Path, default=None)
    args = ap.parse_args()
    data, _ = read_hills(args.hills)
    stats = saturation_stats(data, args.smin_s, args.smax_s, args.smin_z, args.smax_z)
    out_png = args.out_png or args.hills.with_suffix(".diag.png")
    plot(data, out_png)
    stats["out_png"] = str(out_png)
    stats["hills"] = str(args.hills)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
