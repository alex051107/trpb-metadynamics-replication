#!/bin/bash

set -eu
set -o pipefail

INITIAL_RUN_DIR="${INITIAL_RUN_DIR:-../single_walker}"
N_WALKERS=10
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[setup_walkers] $*"; }

commit_frames() {
    local times_csv="$1"
    local -a times
    IFS=',' read -ra times <<< "$times_csv"

    [[ "${#times[@]}" -eq "$N_WALKERS" ]] \
        || die "--commit-frames needs exactly $N_WALKERS values, got ${#times[@]}"

    for t in "${times[@]}"; do
        [[ "$t" =~ ^[0-9]+(\.[0-9]+)?$ ]] \
            || die "time_ps '$t' is not numeric"
    done

    local tpr="$INITIAL_RUN_DIR/metad.tpr"
    local xtc="$INITIAL_RUN_DIR/traj_comp.xtc"
    local topol="$INITIAL_RUN_DIR/topol.top"
    local mdp="$INITIAL_RUN_DIR/metad.mdp"
    local pdb="path_gromacs.pdb"

    [[ -f "$tpr" ]]   || die "missing $tpr"
    [[ -f "$xtc" ]]   || die "missing $xtc"
    [[ -f "$topol" ]] || die "missing $topol"
    [[ -f "$mdp" ]]   || die "missing $mdp"
    [[ -f "$pdb" ]]   || die "missing $pdb (reference path PDB must be in multi_walker/)"
    [[ -f "plumed.dat" ]] || die "missing plumed.dat template in $SCRIPT_DIR"

    log "verifying trajectory time window via gmx check ..."
    local max_t
    max_t=$(gmx check -f "$xtc" 2>&1 \
            | awk '/Last frame/ { print $NF }' \
            | tail -1)
    [[ -n "$max_t" ]] || die "could not parse max time from gmx check output"
    log "trajectory max time = $max_t ps"

    for t in "${times[@]}"; do
        awk -v t="$t" -v m="$max_t" 'BEGIN { exit !(t+0 <= m+0 && t+0 >= 0) }' \
            || die "time_ps $t outside [0, $max_t]"
    done

    for i in $(seq 0 $((N_WALKERS - 1))); do
        local dir="walker_$i"
        local t_ps="${times[$i]}"
        log "walker_$i: dump frame at t=${t_ps} ps"

        mkdir -p "$dir"

        gmx trjconv \
            -s "$tpr" \
            -f "$xtc" \
            -o "$dir/start.gro" \
            -dump "$t_ps" \
            <<< "0" \
            > "$dir/trjconv.log" 2>&1

        [[ -f "$dir/start.gro" ]] || die "gmx trjconv failed for walker_$i"

        cp "$topol" "$dir/topol.top"
        cp "$mdp"   "$dir/metad.mdp"

        sed "s/WALKERS_ID=__WALKER_ID__/WALKERS_ID=$i/" \
            plumed.dat > "$dir/plumed.dat"

        if grep -q '__WALKER_ID__' "$dir/plumed.dat"; then
            die "sed substitution failed in $dir/plumed.dat"
        fi
        grep -q "WALKERS_ID=$i " "$dir/plumed.dat" \
            || die "WALKERS_ID=$i not found in $dir/plumed.dat after sed"
    done

    touch HILLS

    log "walker_0..walker_$((N_WALKERS - 1)) populated."
    log "next step: sbatch submit_array.sh"
}

propose_candidates() {
    local colvar="$1"
    [[ -f "$colvar" ]] || die "COLVAR file not found: $colvar"
    [[ -s "$colvar" ]] || die "COLVAR file is empty: $colvar"

    log "clustering COLVAR '$colvar' into $N_WALKERS clusters via KMeans(s, z)"

    python3 - <<PY
import sys, csv
import numpy as np

try:
    from sklearn.cluster import KMeans
except ImportError:
    sys.stderr.write("ERROR: scikit-learn not available. Run: pip install scikit-learn\n")
    sys.exit(2)

colvar = "$colvar"
n_clusters = $N_WALKERS

rows = []
with open(colvar) as fh:
    for line in fh:
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        rows.append((float(parts[0]), float(parts[1]), float(parts[2])))

if len(rows) < n_clusters * 5:
    sys.stderr.write(f"ERROR: only {len(rows)} COLVAR rows, need >= {n_clusters*5}\n")
    sys.exit(3)

data = np.array(rows)
X = data[:, 1:3]

Xn = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-12)

km = KMeans(n_clusters=n_clusters, n_init=20, random_state=42).fit(Xn)

rows_out = []
for cid in range(n_clusters):
    mask = km.labels_ == cid
    if not mask.any():
        continue
    centre_n = km.cluster_centers_[cid]
    d2 = ((Xn[mask] - centre_n) ** 2).sum(axis=1)
    local_idx = np.argmin(d2)
    frame_idx = int(np.where(mask)[0][local_idx])
    t, s, z = data[frame_idx]
    rows_out.append((cid, t, s, z, frame_idx))

rows_out.sort(key=lambda r: r[2])

with open("candidate_frames.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["cluster_id", "time_ps", "s", "z", "frame_idx"])
    for r in rows_out:
        w.writerow([r[0], f"{r[1]:.3f}", f"{r[2]:.4f}", f"{r[3]:.5f}", r[4]])

print()
print("Candidate frames (sorted by s):")
print(f"  {'cid':>3}  {'time_ps':>10}  {'s':>8}  {'z':>10}")
for r in rows_out:
    print(f"  {r[0]:>3}  {r[1]:>10.1f}  {r[2]:>8.3f}  {r[3]:>10.5f}")
print()
print(f"n_COLVAR_rows = {len(rows)}")
print(f"s range = [{data[:,1].min():.3f}, {data[:,1].max():.3f}]")
print(f"z range = [{data[:,2].min():.5f}, {data[:,2].max():.5f}]")
PY

    cat <<EOF

--------------------------------------------------------------------------------
NEXT STEP (MANDATORY per Yu Zhang 2026-04-09 L2859):

  Open candidate_frames.csv. For each row, in PyMOL:
    1. gmx trjconv -s $INITIAL_RUN_DIR/metad.tpr \\
           -f $INITIAL_RUN_DIR/traj_comp.xtc \\
           -dump <time_ps> -o probe_<cid>.gro
    2. Load probe_<cid>.gro in PyMOL, inspect COMM loop (residues 97-184)
    3. Confirm the 10 frames "cover approximately all conformational space"
       (SI p.S3). If two frames look too similar, re-run Phase 1 with a
       different seed or manually replace one cluster's time_ps.

When satisfied:
  bash setup_walkers.sh --commit-frames <t0>,<t1>,...,<t9>

where each t_i is the time_ps value from the confirmed candidate rows.
--------------------------------------------------------------------------------
EOF
}

if [[ $# -eq 0 ]]; then
    die "usage:
  Phase 1:  bash setup_walkers.sh <colvar_path>
  Phase 2:  bash setup_walkers.sh --commit-frames t0,t1,...,t9
optional:   INITIAL_RUN_DIR=<path> bash setup_walkers.sh ..."
fi

case "$1" in
    --commit-frames)
        [[ $# -eq 2 ]] || die "--commit-frames takes exactly one CSV arg"
        commit_frames "$2"
        ;;
    --candidates)
        [[ $# -eq 2 ]] || die "--candidates takes exactly one path arg"
        propose_candidates "$2"
        ;;
    -h|--help)
        grep '^#' "$0" | head -40
        ;;
    *)
        propose_candidates "$1"
        ;;
esac
