#!/bin/bash
# Step 1b of the diagnostic suite: self-project the 15 reference frames through
# production PATHMSD after renumbering atom serials to a driver-local 1..112 per
# MODEL. This is diagnostic-only and does not modify the production path file.
#
# Run on a Longleaf login node (plumed driver, < 5 s wall).
#
# Expected:
#   - ref_selfproj.dat has 15 rows
#   - s monotonic across frames 1..15
#   - middle frames near their integer index
#   - endpoints ~1.09 / ~14.91 (kernel-average bias at boundaries, not a bug)
#   - z small on every row

set -euo pipefail

WORK=/tmp/path_selfproj_renumbered_$$
SRC_PDB=/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/path_gromacs.pdb
DRV_PDB=/tmp/path_driver.pdb

mkdir -p "$WORK"
cd "$WORK"

cp "$SRC_PDB" path_gromacs.pdb

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

cat > plumed_self.dat <<'PLU'
p: PATHMSD REFERENCE=/tmp/path_driver.pdb LAMBDA=379.77
PRINT ARG=p.sss,p.zzz FILE=ref_selfproj.dat STRIDE=1 FMT=%12.6f
PLU

export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}
export PATH=/work/users/l/i/liualex/plumed-2.9.2/bin:${PATH}

echo "=== original path atom serial tail ==="
awk '/^ATOM/ {print $2}' path_gromacs.pdb | sort -n | uniq | tail -5
echo
echo "=== renumbered path atom serial tail ==="
awk '/^ATOM/ {print $2}' "$DRV_PDB" | sort -n | uniq | tail -5
echo
echo "=== model count ==="
grep -c '^MODEL' "$DRV_PDB"
echo
echo "=== running plumed driver on /tmp/path_driver.pdb ==="
plumed driver --plumed plumed_self.dat --mf_pdb "$DRV_PDB"
echo
echo "=== ref_selfproj.dat ==="
cat ref_selfproj.dat
echo
echo "=== row count ==="
awk 'BEGIN{n=0} !/^#/ {n++} END{print n}' ref_selfproj.dat
echo
echo "=== monotonic s check ==="
awk '
BEGIN { prev = -1e99; ok = 1 }
!/^#/ {
  if ($1 < prev) ok = 0
  prev = $1
}
END {
  if (ok) print "PASS"
  else print "FAIL"
}
' ref_selfproj.dat
echo
echo "=== expected: s monotonic; middle near integers; endpoints ~1.09 / ~14.91; z small ==="
echo "=== work dir: $WORK (rm -rf to clean) ==="
echo "=== driver path kept at: $DRV_PDB ==="
