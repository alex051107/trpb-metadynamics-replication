#!/bin/bash
# Purpose: project the 15 reference frames of path_gromacs.pdb back through the
# production PATHMSD definition (same REFERENCE, same LAMBDA=379.77). Ideal
# output: frame k -> s≈k, z≈0. Any frame with out-of-order s or z significantly
# above 0 is evidence of a reference / atom-order / path-geometry bug.
#
# Run on Longleaf login node (no sbatch; driver is ~1s of work).

set -e

WORK=/tmp/path_selfproj_$$
mkdir -p "$WORK"
cd "$WORK"

cp /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/path_gromacs.pdb .

cat > plumed_self.dat <<'PLU'
path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77
PRINT ARG=path.sss,path.zzz FILE=self_projection.colvar STRIDE=1 FMT=%12.6f
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
plumed driver --plumed plumed_self.dat --ipdb path_gromacs.pdb 2>&1 | tail -15
echo
echo "=== self_projection.colvar ==="
cat self_projection.colvar
echo
echo "=== expected: frame k -> s≈k, z≈0 ==="
echo "=== work dir kept: $WORK (delete with: rm -rf $WORK) ==="
