#!/bin/bash
# submit_all.sh — 提交 10 个 walker MetaD jobs 到 Slurm
#
# 用法：
#   cd /work/users/l/i/liualex/AnimaLab/metadynamics/multi_walker
#   bash submit_all.sh
#
# 前提：setup_walkers.sh 已成功运行
#
# SI 原文 (JACS 2019, S4):
#   "Each replica was run for 50-100 ns, giving a total of 500-1000 ns
#    of simulation time per system"

set -eo pipefail

NWALKERS=10

echo "=== Submitting ${NWALKERS} MetaD walkers ==="

for i in $(seq 0 $((NWALKERS-1))); do
    DIR="walker_$(printf '%02d' $i)"

    if [ ! -d "${DIR}" ]; then
        echo "ERROR: ${DIR}/ not found. Run setup_walkers.sh first."
        exit 1
    fi

    if [ ! -f "${DIR}/start.gro" ]; then
        echo "ERROR: ${DIR}/start.gro not found."
        exit 1
    fi

    # 提交 walker job
    JOB_ID=$(sbatch --parsable --job-name="metad_w${i}" --chdir="${PWD}/${DIR}" submit_walker.sh)
    echo "  Walker ${i}: Job ${JOB_ID} submitted from ${DIR}/"
done

echo ""
echo "=== All ${NWALKERS} walkers submitted ==="
echo "Monitor: squeue -u liualex | grep metad_w"
echo "Check HILLS: wc -l walker_*/HILLS"
