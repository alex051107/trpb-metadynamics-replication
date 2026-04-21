"""Periodic probe-sweep monitor: pull COLVAR/HILLS from Longleaf, diagnose, commit, push, PR on winner.

Designed to be fired every 2h by a cron tick. Encodes the Osuna 2019 SI S4
convergence protocol (ΔG between O/PC/C local minima over time) plus a
four-way saturation check on the adaptive Gaussian widths:

  σ_s MIN (floor), σ_s MAX (ceiling), σ_z MIN (floor), σ_z MAX (ceiling)

If any of the four hits >50% of hills, the adaptive bounds are binding and
the diagnosis needs to be revisited — that signal is the whole point of
this monitor per PM review.

Labels per SI S4:
  O  = s(R) ∈ [1, 5)
  PC = s(R) ∈ [5, 10)
  C  = s(R) ∈ [10, 15]

Winner gate (revised from original "reach s=15"): max_s ≥ 7 AND ≥3
non-empty s-bins AND σ_s saturation < 50%. Main-text SI notes that isolated
Ain is thermodynamically confined to O, so the realistic goal is seeding
diverse walkers for Phase 4, not full path coverage.

Idempotent — safe to re-run; only commits status.md on change.
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SWEEP_DIR = Path(__file__).resolve().parent
REMOTE_HOST = "longleaf"
REMOTE_PATH = "/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/"
PROBES = ["P1", "P2", "P3", "P4"]
S_BINS = {"O": (1, 5), "PC": (5, 10), "C": (10, 15)}  # SI S4 labels
PRIMARY_GATE = {"max_s": 7.0, "non_empty_bins": 3, "sigma_sat_pct": 50.0}

# HILLS columns after `#! FIELDS time path.sss path.zzz sigma_s sigma_zz sigma_zs height biasf`
COL_TIME = 0
COL_S = 1
COL_Z = 2
COL_SIGMA_S = 3
COL_SIGMA_ZZ = 4


def run(cmd, check=True, capture=True, timeout=600):
    return subprocess.run(
        cmd, shell=isinstance(cmd, str), check=check,
        capture_output=capture, text=True, timeout=timeout,
    )


def rsync_probe_outputs():
    """Pull COLVAR/HILLS for all 4 probes. Skip trajectories and checkpoints."""
    pulled = {}
    for pid in PROBES:
        local = SWEEP_DIR / f"probe_{pid}"
        local.mkdir(exist_ok=True)
        remote = f"{REMOTE_HOST}:{REMOTE_PATH}probe_{pid}/"
        try:
            run([
                "rsync", "-av", "--timeout=60",
                "--include=COLVAR", "--include=HILLS",
                "--include=*.log", "--include=*.out",
                "--exclude=*.cpt", "--exclude=*.xtc", "--exclude=*.tpr",
                "--exclude=*", remote, str(local) + "/",
            ], check=False, timeout=180)
            pulled[pid] = {
                "colvar_lines": sum(1 for _ in open(local / "COLVAR")) if (local / "COLVAR").exists() else 0,
                "hills_lines": sum(1 for _ in open(local / "HILLS")) if (local / "HILLS").exists() else 0,
            }
        except subprocess.TimeoutExpired:
            pulled[pid] = {"error": "rsync timeout"}
    return pulled


def saturation_four_way(hills, smin_s, smax_s, smin_z, smax_z, tol=1e-4):
    """Percent of hills touching each of the four adaptive-width bounds.

    Returns dict with keys sigma_s_min_pct, sigma_s_max_pct, sigma_z_min_pct,
    sigma_z_max_pct — each 0..100. Any value above PRIMARY_GATE['sigma_sat_pct']
    means that bound is binding.
    """
    if hills.ndim < 2 or hills.shape[0] == 0:
        return {k: float("nan") for k in [
            "sigma_s_min_pct", "sigma_s_max_pct",
            "sigma_z_min_pct", "sigma_z_max_pct",
        ]}
    sigma_s = hills[:, COL_SIGMA_S]
    sigma_zz = hills[:, COL_SIGMA_ZZ]
    return {
        "sigma_s_min_pct": float(np.mean(sigma_s <= smin_s + tol) * 100),
        "sigma_s_max_pct": float(np.mean(sigma_s >= smax_s - tol) * 100),
        "sigma_z_min_pct": float(np.mean(sigma_zz <= smin_z + tol) * 100),
        "sigma_z_max_pct": float(np.mean(sigma_zz >= smax_z - tol) * 100),
    }


def bin_coverage(colvar):
    """O/PC/C bin counts (SI S4 labels)."""
    if colvar.ndim < 2 or colvar.shape[0] == 0:
        return {k: 0 for k in S_BINS}
    s = colvar[:, COL_S]
    return {label: int(np.sum((s >= lo) & (s < hi))) for label, (lo, hi) in S_BINS.items()}


def pseudo_dg_between_minima(colvar, bias_col=3, kT=350 * 0.0083145):
    """Tick-level progress signal: pseudo-FES ΔG between O/PC/C.

    Full FES comes from sum_hills at the end; this is the walking-ΔG monitor
    SI S4 asks for. Only returns pairs whose source bins both have ≥10 frames.
    """
    if colvar.ndim < 2 or colvar.shape[0] < 100 or colvar.shape[1] <= bias_col:
        return {}
    s = colvar[:, COL_S]
    bias = colvar[:, bias_col]
    mins = {}
    for label, (lo, hi) in S_BINS.items():
        mask = (s >= lo) & (s < hi)
        if mask.sum() < 10:
            mins[label] = None
            continue
        w = np.exp(bias[mask] / kT - np.max(bias[mask] / kT))
        mins[label] = float(-kT * np.log(w.sum()))
    dg = {}
    for a, b in [("PC", "O"), ("C", "O"), ("C", "PC")]:
        if mins.get(a) is not None and mins.get(b) is not None:
            dg[f"dG_{a}_minus_{b}_kJmol"] = mins[a] - mins[b]
    return dg


def score_probe(pid, spec):
    colvar_path = SWEEP_DIR / f"probe_{pid}" / "COLVAR"
    hills_path = SWEEP_DIR / f"probe_{pid}" / "HILLS"
    out = {"probe": pid, "status": "missing"}
    if not (colvar_path.exists() and hills_path.exists()):
        return out
    try:
        colvar = np.loadtxt(colvar_path, comments="#")
        hills = np.loadtxt(hills_path, comments="#")
    except Exception as e:
        out["status"] = f"read_error: {e}"
        return out
    if colvar.ndim < 2 or hills.ndim < 2:
        out["status"] = "empty"
        return out
    sat = saturation_four_way(hills, spec["smin"][0], spec["smax"][0], spec["smin"][1], spec["smax"][1])
    cov = bin_coverage(colvar)
    non_empty = sum(1 for v in cov.values() if v > 0)
    max_s = float(colvar[:, COL_S].max())
    any_bound_binding = any(v >= PRIMARY_GATE["sigma_sat_pct"] for v in sat.values() if not np.isnan(v))
    passes = (
        max_s >= PRIMARY_GATE["max_s"]
        and non_empty >= PRIMARY_GATE["non_empty_bins"]
        and sat["sigma_s_min_pct"] < PRIMARY_GATE["sigma_sat_pct"]
    )
    out.update({
        "status": "ok",
        "ns_elapsed": float(colvar[-1, COL_TIME] / 1000.0),
        "n_hills": int(hills.shape[0]),
        "max_s": max_s,
        "coverage": cov,
        "non_empty_bins": non_empty,
        "any_bound_binding": bool(any_bound_binding),
        "passes_primary": bool(passes),
        **sat,
        **pseudo_dg_between_minima(colvar),
    })
    return out


def load_ladder():
    import yaml
    data = yaml.safe_load((SWEEP_DIR / "ladder.yaml").read_text())
    return {p["id"]: p for p in data["probes"]}


def pick_winner(results):
    winners = [r for r in results if r.get("passes_primary")]
    if not winners:
        return None
    return sorted(winners, key=lambda r: (-r["max_s"], r["sigma_s_min_pct"]))[0]


def fmt_pct(v):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.1f}"


def write_status(results, winner, pulled, ladder):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status_path = SWEEP_DIR / "status.md"
    lines = [
        "# Probe sweep live status",
        "",
        "Auto-written by `routine_check.py` every 2 hours.",
        "",
        f"_Last tick: {ts}_",
        "",
        f"**Winner:** {winner['probe']} (max_s={winner['max_s']:.2f})" if winner else "**Winner:** none yet",
        "",
        "## Per-probe saturation (key signal)",
        "",
        "Columns show % of hills touching each bound. Anything >50 means that bound is binding and the adaptive width can't breathe.",
        "",
        "| probe | ns | hills | max_s | O/PC/C | σ_s MIN | σ_s MAX | σ_z MIN | σ_z MAX | passes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        if r.get("status") != "ok":
            lines.append(f"| {r['probe']} | — | — | — | — | — | — | — | — | {r.get('status','?')} |")
            continue
        cov = r["coverage"]
        lines.append(
            f"| {r['probe']} | {r['ns_elapsed']:.2f} | {r['n_hills']} | {r['max_s']:.2f} | "
            f"{cov['O']}/{cov['PC']}/{cov['C']} | "
            f"{fmt_pct(r['sigma_s_min_pct'])} | {fmt_pct(r['sigma_s_max_pct'])} | "
            f"{fmt_pct(r['sigma_z_min_pct'])} | {fmt_pct(r['sigma_z_max_pct'])} | "
            f"{'PASS' if r['passes_primary'] else 'wait'} |"
        )
    lines += [
        "",
        "## Ladder reminder",
        "",
        "| probe | σ_s MIN / MAX | σ_z MIN / MAX |",
        "|---|---|---|",
    ]
    for pid in PROBES:
        spec = ladder[pid]
        lines.append(f"| {pid} | {spec['smin'][0]} / {spec['smax'][0]} | {spec['smin'][1]} / {spec['smax'][1]} |")
    lines += [
        "",
        "## ΔG between O/PC/C (pseudo-FES, per SI S4 convergence monitor)",
        "",
        "| probe | ΔG(PC−O) | ΔG(C−O) | ΔG(C−PC) |",
        "|---|---|---|---|",
    ]
    for r in results:
        if r.get("status") != "ok":
            lines.append(f"| {r['probe']} | — | — | — |")
            continue
        lines.append(
            f"| {r['probe']} | "
            f"{r.get('dG_PC_minus_O_kJmol', '—')} | "
            f"{r.get('dG_C_minus_O_kJmol', '—')} | "
            f"{r.get('dG_C_minus_PC_kJmol', '—')} |"
        )
    lines += [
        "",
        "## Raw fetch",
        "",
        "```json",
        json.dumps(pulled, indent=2),
        "```",
        "",
        "## Paper protocol reference",
        "",
        "- Convergence: Osuna 2019 SI S4 — monitor ΔG between O/PC/C local minima vs time.",
        "- Labels: O=s(R)∈[1,5), PC=[5,10), C=[10,15]; structure selection = cluster representative structures per minimum.",
        "- Gate: max_s ≥ 7 AND ≥3 non-empty s-bins AND σ_s saturation < 50%. Full path s=15 is thermodynamically inaccessible from isolated Ain; seed diversity for Phase 4 is the real goal.",
    ]
    status_path.write_text("\n".join(lines) + "\n")
    return status_path


def git_commit_push(status_path, winner):
    os.chdir(REPO_ROOT)
    branch = run("git rev-parse --abbrev-ref HEAD").stdout.strip()
    diff = run(f"git status --porcelain {status_path}", check=False).stdout.strip()
    if not diff:
        return False, branch
    tag = f"winner={winner['probe']}" if winner else "running"
    run(f"git add {status_path}", check=False)
    run(["git", "commit", "-m", f"probe sweep tick ({tag})"], check=False)
    push = run(f"git push origin {branch}", check=False)
    return push.returncode == 0, branch


def open_pr_if_winner(winner, branch):
    if not winner:
        return None
    body = textwrap.dedent(f"""
    ## Probe sweep winner: {winner['probe']}

    - max_s = {winner['max_s']:.2f} (gate ≥ 7)
    - non-empty s-bins = {winner['non_empty_bins']} (gate ≥ 3)
    - σ_s MIN saturation = {winner['sigma_s_min_pct']:.1f}% (gate < 50)
    - σ_s MAX saturation = {winner['sigma_s_max_pct']:.1f}%
    - σ_z MIN saturation = {winner['sigma_z_min_pct']:.1f}%
    - σ_z MAX saturation = {winner['sigma_z_max_pct']:.1f}%

    Coverage O/PC/C: {winner['coverage']['O']}/{winner['coverage']['PC']}/{winner['coverage']['C']}

    Merge to patch `phase3_single_walker/plumed.dat` with the winning SIGMA_MIN/MAX values.
    """).strip()
    res = run([
        "gh", "pr", "create",
        "--title", f"Probe sweep winner: {winner['probe']}",
        "--body", body,
        "--base", "master",
        "--head", branch,
    ], check=False)
    return res.stdout.strip() if res.returncode == 0 else res.stderr.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-rsync", action="store_true")
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--no-pr", action="store_true")
    args = ap.parse_args()

    pulled = {} if args.skip_rsync else rsync_probe_outputs()
    ladder = load_ladder()
    results = [score_probe(pid, ladder[pid]) for pid in PROBES]
    winner = pick_winner(results)
    status_path = write_status(results, winner, pulled, ladder)

    print(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "winner": winner["probe"] if winner else None,
        "results": results,
    }, indent=2, default=str))

    if args.no_commit:
        return 0
    committed, branch = git_commit_push(status_path, winner)
    if committed and winner and not args.no_pr:
        pr = open_pr_if_winner(winner, branch)
        print(f"PR: {pr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
