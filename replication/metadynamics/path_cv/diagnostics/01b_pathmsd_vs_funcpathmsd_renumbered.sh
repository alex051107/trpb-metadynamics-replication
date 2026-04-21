#!/bin/bash
# Step 2b: PATHMSD vs FUNCPATHMSD equivalence check using a driver-local
# renumbered copy of the production path reference. This is diagnostic-only and
# does not modify the production path file.
#
# Run on a Longleaf login node, ~30 s.

set -euo pipefail

WORK=/tmp/path_compare_renumbered_$$
SRC_PDB=/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/path_gromacs.pdb
DRV_PDB="$WORK/path_driver_multi.pdb"

mkdir -p "$WORK"
cd "$WORK"

cp "$SRC_PDB" path_gromacs.pdb

export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}
export PATH=/work/users/l/i/liualex/plumed-2.9.2/bin:${PATH}

echo "=== renumber multi-MODEL path to driver-local 1..112 serials ==="
awk '
BEGIN { serial = 0 }
/^MODEL/ { serial = 0; print; next }
/^ATOM/  {
  serial++
  printf "%-6s%5d%s\n", substr($0,1,6), serial, substr($0,12)
  next
}
{ print }
' path_gromacs.pdb > "$DRV_PDB"

echo "=== split renumbered multi-MODEL path into 15 single-frame PDBs ==="
python3 - <<'PY'
from pathlib import Path

src = Path("path_driver_multi.pdb")
text = src.read_text().splitlines(keepends=True)
frames = []
cur = None
for ln in text:
    if ln.startswith("MODEL"):
        cur = [ln]
    elif ln.startswith("ENDMDL"):
        cur.append(ln)
        frames.append(cur)
        cur = None
    elif cur is not None:
        cur.append(ln)

print(f"found {len(frames)} frames")
assert len(frames) == 15, f"expected 15 frames, found {len(frames)}"

for i, frame in enumerate(frames, 1):
    body = [l for l in frame if l.startswith(("ATOM", "HETATM", "TER"))]
    out = Path(f"frame{i:02d}.pdb")
    out.write_text("".join(body) + "END\n")
PY
ls frame*.pdb | wc -l

echo
echo "=== build dual-CV plumed input ==="
cat > plumed_compare.dat <<'HDR'
# PATHMSD (built-in multi-frame action) ↔ FUNCPATHMSD (explicit RMSD reconstruction)
# Same λ, same 112 Cα, same reference file layout, driver-local renumbered serials.
HDR

for i in $(seq -f "%02g" 1 15); do
  echo "r${i}: RMSD REFERENCE=frame${i}.pdb TYPE=OPTIMAL SQUARED" >> plumed_compare.dat
done

ARGS=$(printf "r%02d," $(seq 1 15) | sed 's/,$//')
cat >> plumed_compare.dat <<PLU

pf: FUNCPATHMSD ARG=${ARGS} LAMBDA=379.77
pp: PATHMSD REFERENCE=${DRV_PDB} LAMBDA=379.77

PRINT ARG=pp.sss,pp.zzz,pf.s,pf.z FILE=path_compare.dat STRIDE=1 FMT=%12.6f
PLU

echo "=== plumed input ==="
head -5 plumed_compare.dat
echo "..."
tail -5 plumed_compare.dat

echo
echo "=== run driver over the 15-frame renumbered reference ==="
plumed driver --plumed plumed_compare.dat --mf_pdb "$DRV_PDB"

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
    print("VERDICT: DISAGREE → metric inconsistency (alignment convention or λ semantics)")
PY
echo
echo "=== work dir: $WORK ==="
