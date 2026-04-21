#!/bin/bash
#SBATCH --job-name=aex1_openmm_smoke_v100
#SBATCH --partition=volta-gpu
#SBATCH --qos=gpu_access
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/logs/%x_%j.out
#SBATCH --error=/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/logs/%x_%j.err

# Wrapper around the common Aex1 OpenMM batch body. This keeps the smoke run on
# V100 hardware separate from the queued A100 confirmation job while reusing the
# exact same CUDA-probe -> full-build -> 1 ns smoke flow.

set -eo pipefail

REMOTE_ROOT="${REMOTE_ROOT:-/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm}"
SCRIPT_DIR="${SCRIPT_DIR:-${REMOTE_ROOT}/scripts}"
BUILD_DIR="${BUILD_DIR:-${REMOTE_ROOT}/build}"
RUN_DIR="${RUN_DIR:-${REMOTE_ROOT}/smoke_v100}"
SOURCE_PDB="${SOURCE_PDB:-${REMOTE_ROOT}/inputs/5DW0.pdb}"
MODE="${MODE:-smoke}"
PROD_NS="${PROD_NS:-1}"
NVT_NS="${NVT_NS:-0.5}"
NPT_NS="${NPT_NS:-0.5}"
REPORT_PS="${REPORT_PS:-100}"
STATE_PS="${STATE_PS:-1000}"

export REMOTE_ROOT SCRIPT_DIR BUILD_DIR RUN_DIR SOURCE_PDB MODE PROD_NS NVT_NS NPT_NS REPORT_PS STATE_PS

bash "${SCRIPT_DIR}/aex1_cmd_prod.sbatch"
