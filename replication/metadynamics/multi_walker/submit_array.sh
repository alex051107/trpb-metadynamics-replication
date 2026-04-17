#!/bin/bash
#SBATCH --job-name=trpb_multi_walker
#SBATCH --partition=volta-gpu
#SBATCH --qos=gpu_access
#SBATCH --nodes=1
#SBATCH --ntasks=10
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:10
#SBATCH --time=72:00:00
#SBATCH --mem=64G
#SBATCH --output=multi_walker-%j.out
#SBATCH --error=multi_walker-%j.err

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

cd "$SLURM_SUBMIT_DIR"

echo "=== Pre-flight asserts ==="
for i in $(seq 0 9); do
    dir="walker_$i"
    [[ -d "$dir" ]]              || { echo "FAIL: $dir missing"; exit 1; }
    [[ -f "$dir/start.gro" ]]    || { echo "FAIL: $dir/start.gro missing"; exit 1; }
    [[ -f "$dir/topol.top" ]]    || { echo "FAIL: $dir/topol.top missing"; exit 1; }
    [[ -f "$dir/metad.mdp" ]]    || { echo "FAIL: $dir/metad.mdp missing"; exit 1; }
    [[ -f "$dir/plumed.dat" ]]   || { echo "FAIL: $dir/plumed.dat missing"; exit 1; }
    grep -q "WALKERS_ID=$i " "$dir/plumed.dat" \
        || { echo "FAIL: $dir/plumed.dat does not have WALKERS_ID=$i"; exit 1; }
    grep -q '__WALKER_ID__' "$dir/plumed.dat" \
        && { echo "FAIL: $dir/plumed.dat still has __WALKER_ID__ sentinel"; exit 1; }
done
[[ -f path_gromacs.pdb ]] || { echo "FAIL: path_gromacs.pdb missing"; exit 1; }
echo "pre-flight OK: all 10 walkers staged, path_gromacs.pdb present"

echo "=== Environment ==="
echo "PLUMED_KERNEL:   $PLUMED_KERNEL"
echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "LAMBDA:          379.77 nm^-2 (PATHMSD per-atom MSD, 2026-04-09 pivot)"
echo "WALKERS_N:       10 (Osuna SI p.S3-S4)"
echo "WALKERS_RSTRIDE: 1000 steps = 2 ns (our choice, SI silent)"

echo "=== Per-walker grompp ==="
for i in $(seq 0 9); do
    dir="walker_$i"
    if [[ ! -f "$dir/metad.tpr" ]]; then
        echo "grompp walker_$i"
        (cd "$dir" && gmx grompp \
            -f metad.mdp \
            -c start.gro \
            -p topol.top \
            -o metad.tpr \
            -maxwarn 2 > grompp.log 2>&1)
    fi
done
echo "grompp OK"

echo "=== Production mdrun -multidir ==="
mpirun -np 10 gmx_mpi mdrun \
    -multidir walker_0 walker_1 walker_2 walker_3 walker_4 walker_5 \
              walker_6 walker_7 walker_8 walker_9 \
    -deffnm metad \
    -plumed plumed.dat \
    -maxh 71.5 \
    -cpi metad.cpt \
    -noappend

echo "=== Post-flight checks ==="
for i in $(seq 0 9); do
    dir="walker_$i"
    echo "--- $dir ---"
    ls -lh "$dir/COLVAR" "$dir/metad.log" 2>/dev/null || true
    [[ -f "$dir/COLVAR" ]] && { echo "head COLVAR:"; head -3 "$dir/COLVAR"; \
                                echo "tail COLVAR:"; tail -3 "$dir/COLVAR"; }
    if ls "$dir"/bck.*.HILLS 2>/dev/null; then
        echo "WARN: $dir has bck.*.HILLS — FP-026 may have fired, inspect immediately"
    fi
done

echo "=== Shared HILLS (parent multi_walker/) ==="
ls -lh HILLS* 2>/dev/null || echo "no shared HILLS files found (unexpected)"
wc -l HILLS* 2>/dev/null || true

echo "=== Done at $(date) ==="
