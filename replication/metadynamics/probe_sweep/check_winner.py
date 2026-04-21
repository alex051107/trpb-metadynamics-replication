"""Purpose: score each probe's COLVAR+HILLS against the plan's success gate and pick a winner."""

import argparse
import glob
import json
import re
from pathlib import Path

import numpy as np
import yaml

BINS = [(1, 3), (3, 5), (5, 7), (7, 10), (10, 15)]


def read_colvar(path):
    return np.loadtxt(path, comments="#")


def read_hills(path):
    return np.loadtxt(path, comments="#")


def load_ladder(ladder_path):
    ladder = yaml.safe_load(Path(ladder_path).read_text())
    return {p["id"]: p for p in ladder["probes"]}


def score(probe_id, colvar, hills, smin, smax):
    s = colvar[:, 1]
    bin_counts = {f"[{lo},{hi})": int(np.sum((s >= lo) & (s < hi))) for lo, hi in BINS}
    non_empty_bins = sum(1 for v in bin_counts.values() if v > 0)
    sigma_s = hills[:, 3]
    saturation = float(np.mean(sigma_s <= smin[0] + 1e-4) * 100)
    metrics = {
        "probe_id": probe_id,
        "max_s": float(s.max()),
        "non_empty_bins": non_empty_bins,
        "sigma_s_saturation_pct": saturation,
        **bin_counts,
    }
    metrics["passes_primary"] = bool(metrics["max_s"] >= 7 and non_empty_bins >= 3 and saturation < 50)
    metrics["passes_secondary"] = bool(metrics["max_s"] >= 5 and saturation < 50)
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder", type=Path, default=Path(__file__).parent / "ladder.yaml")
    ap.add_argument("--probe-root", type=Path, default=Path(__file__).parent)
    ap.add_argument("--out-tsv", type=Path, default=Path(__file__).parent / "results.tsv")
    ap.add_argument("--out-winner", type=Path, default=Path(__file__).parent / "winner.txt")
    args = ap.parse_args()

    ladder = load_ladder(args.ladder)
    rows = []
    for pid, spec in ladder.items():
        colvar_path = args.probe_root / f"probe_{pid}" / "COLVAR"
        hills_path = args.probe_root / f"probe_{pid}" / "HILLS"
        if not colvar_path.exists() or not hills_path.exists():
            rows.append({"probe_id": pid, "status": "missing"})
            continue
        colvar = read_colvar(colvar_path)
        hills = read_hills(hills_path)
        rows.append(score(pid, colvar, hills, spec["smin"], spec["smax"]))

    if rows:
        keys = sorted({k for r in rows for k in r.keys()})
        with open(args.out_tsv, "w") as fh:
            fh.write("\t".join(keys) + "\n")
            for r in rows:
                fh.write("\t".join(str(r.get(k, "")) for k in keys) + "\n")

    winners = [r for r in rows if r.get("passes_primary")]
    if winners:
        winner = sorted(winners, key=lambda r: (-r["max_s"], r["sigma_s_saturation_pct"]))[0]
        args.out_winner.write_text(winner["probe_id"] + "\n")
    else:
        args.out_winner.write_text("")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
