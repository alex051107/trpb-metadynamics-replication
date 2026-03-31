#!/bin/bash
# Gaussian 16 submission script for capped Ain RESP fitting.
# Intended destination on Longleaf:
#   /work/users/l/i/liualex/AnimaLab/parameterization/ain/

#SBATCH --job-name=llp_ain_resp
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --partition=general
#SBATCH --output=llp_ain_resp_%j.out

set -euo pipefail

module purge
module load gaussian/16c02
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

INPUT_GCRT="${1:-LLP_ain_resp_capped.gcrt}"
SCRATCH_DIR="${TMPDIR:-/tmp}/${USER}/gaussian/${SLURM_JOB_ID}"

mkdir -p "${SCRATCH_DIR}"
trap 'rm -rf ${SCRATCH_DIR}' EXIT
export GAUSS_SCRDIR="${SCRATCH_DIR}"

cd "${SLURM_SUBMIT_DIR}"

echo "Starting Gaussian 16 RESP job"
echo "Input: ${INPUT_GCRT}"
echo "Scratch: ${GAUSS_SCRDIR}"
echo "Host: $(hostname)"
date

g16 "${INPUT_GCRT}"

date
echo "Gaussian job complete"
