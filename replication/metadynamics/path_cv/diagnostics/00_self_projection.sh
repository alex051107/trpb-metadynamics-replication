#!/bin/bash
# Step 1 of the diagnostic suite: self-project 15 reference frames through production PATHMSD.
# Run on Longleaf login node (plumed driver, < 5s wall).
#
# Expected (per PM 2026-04-21):
#   - s monotonic across frames 1..15
#   - Middle frames near their integer index
#   - Endpoints ~1.09 and ~14.91 (kernel-average bias at boundaries, not a bug)
#   - z small on every row

set -e

WORK=/tmp/path_selfproj_$$
mkdir -p "$WORK"
cd "$WORK"

cp /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/path_gromacs.pdb .

cat > plumed_self.dat <<'PLU'
p: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77
PRINT ARG=p.sss,p.zzz FILE=ref_selfproj.dat STRIDE=1 FMT=%12.6f
PLU

export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}
export PATH=/work/users/l/i/liualex/plumed-2.9.2/bin:${PATH}

echo "=== plumed version ==="
plumed --version 2>&1 | head -3
echo
echo "=== path_gromacs.pdb model count ==="
grep -c "^MODEL" path_gromacs.pdb
echo
echo "=== running plumed driver ==="
plumed driver --plumed plumed_self.dat --mf_pdb path_gromacs.pdb 2>&1 | tail -15
echo
echo "=== ref_selfproj.dat ==="
cat ref_selfproj.dat
echo
echo "=== expected: s monotonic; middle near integers; endpoints ~1.09 / ~14.91; z small ==="
echo "=== work dir: $WORK (rm -rf to clean) ==="
