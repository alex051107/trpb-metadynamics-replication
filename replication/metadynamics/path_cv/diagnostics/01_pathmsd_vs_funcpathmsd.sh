#!/bin/bash
# Step 2: PATHMSD vs FUNCPATHMSD equivalence check.
# Uses the 15 reference frames themselves as input (each should produce a consistent (s,z) pair
# between the two definitions). Also samples 10 representative snapshots from probe_P1's COLVAR trajectory.
# Run on Longleaf login node, ~30s.

set -e

WORK=/tmp/path_compare_$$
mkdir -p "$WORK"
cd "$WORK"

BASE=/work/users/l/i/liualex/AnimaLab/metadynamics
cp ${BASE}/single_walker/path_gromacs.pdb .

export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}
export PATH=/work/users/l/i/liualex/plumed-2.9.2/bin:${PATH}

echo "=== split multi-MODEL path into 15 single-frame PDBs ==="
python3 - <<'PY'
lines = open("path_gromacs.pdb").readlines()
frames = []
cur = []
for ln in lines:
    if ln.startswith("MODEL"):
        cur = [ln]
    elif ln.startswith("ENDMDL"):
        cur.append(ln)
        frames.append(cur)
        cur = []
    elif cur is not None:
        cur.append(ln)
print(f"found {len(frames)} frames")
for i, frame in enumerate(frames, 1):
    body = [l for l in frame if l.startswith(("ATOM", "HETATM", "TER"))]
    with open(f"frame{i:02d}.pdb", "w") as f:
        f.write("".join(body))
        f.write("END\n")
PY
ls frame*.pdb | wc -l

echo
echo "=== build dual-CV plumed input ==="
# FUNCPATHMSD uses per-atom MSD (SQUARED) inputs; λ convention must match PATHMSD.
ARGS=""
cat > plumed_compare.dat <<'HDR'
# PATHMSD (built-in multi-frame action) ↔ FUNCPATHMSD (explicit RMSD reconstruction)
# Same λ, same 112 Cα, same reference file layout.
HDR

for i in $(seq -f "%02g" 1 15); do
  echo "r${i}: RMSD REFERENCE=frame${i}.pdb TYPE=OPTIMAL SQUARED" >> plumed_compare.dat
done

# Build comma-separated ARG list r01,r02,...,r15
ARGS=$(printf "r%02d," $(seq 1 15) | sed 's/,$//')
cat >> plumed_compare.dat <<PLU

pf: FUNCPATHMSD ARG=${ARGS} LAMBDA=379.77
pp: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77

# Note: FUNCPATHMSD outputs are .s and .z; PATHMSD outputs are .sss and .zzz.
PRINT ARG=pp.sss,pp.zzz,pf.s,pf.z FILE=path_compare.dat STRIDE=1 FMT=%12.6f
PLU

echo "=== plumed input ==="
head -5 plumed_compare.dat
echo "..."
tail -6 plumed_compare.dat

echo
echo "=== run driver over the 15-frame reference (self-consistency) ==="
plumed driver --plumed plumed_compare.dat --mf_pdb path_gromacs.pdb 2>&1 | tail -10

echo
echo "=== path_compare.dat (15 rows = 15 reference frames) ==="
echo "columns: pp.sss  pp.zzz  pf.s  pf.z"
cat path_compare.dat
echo
echo "=== pass criterion: |pp.sss - pf.s| / pp.sss < 0.01 and |pp.zzz - pf.z| < 0.01 on every row ==="
python3 - <<'PY'
import numpy as np
data = np.loadtxt("path_compare.dat", comments="#")
if data.ndim == 1:
    data = data[None, :]
# cols: time, pp.sss, pp.zzz, pf.s, pf.z
s_pp, z_pp, s_pf, z_pf = data[:, 1], data[:, 2], data[:, 3], data[:, 4]
rel_s = np.abs(s_pp - s_pf) / np.clip(np.abs(s_pp), 1e-9, None)
abs_z = np.abs(z_pp - z_pf)
print(f"max |rel s-diff| = {rel_s.max():.3e}  (gate < 1e-2)")
print(f"max |abs z-diff| = {abs_z.max():.3e}  (gate < 1e-2)")
if rel_s.max() < 1e-2 and abs_z.max() < 1e-2:
    print("VERDICT: PATHMSD and FUNCPATHMSD AGREE → no metric inconsistency")
else:
    print("VERDICT: DISAGREE → technical bug (atom mapping or λ convention); fix before interpreting production")
PY
echo
echo "=== work dir: $WORK ==="
