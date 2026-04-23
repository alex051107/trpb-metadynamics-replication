#!/bin/bash
# Run the Ain-vs-Aex1 path projection attribution check on Longleaf.
#
# Expected to run on a login node (plumed driver, ~tens of seconds) inside
# the trpb-md conda env. Workflow per ChatGPT Pro 2026-04-23:
#   1. Project Ain 500 ns cMD window onto current path -> COLVAR
#   2. Project Aex1 cMD window onto same path -> COLVAR
#   3. Compare via compare_projections.py (4 readouts + verdict)
#
# Trajectory format notes:
#   - Ain cMD output is AMBER .nc (pmemd.cuda). MDAnalysis reads .nc with a
#     .parm7 topology.
#   - Aex1 cMD output is OpenMM .dcd. MDAnalysis reads .dcd with a .pdb
#     topology (the initial minimized pdb works).
#
# Windows:
#   - Ain: 100-105 ns (settled, well past early relaxation at 500 ns total)
#   - Aex1: 10-15 ns if prod has reached that point; override via AEX1_BEGIN_NS
#     / AEX1_END_NS env vars if production is still short.
#
# Environment assumptions:
#   conda env trpb-md is active -> plumed, python, MDAnalysis are on PATH.
#
# Outputs:
#   ${OUTDIR}/ain_proj.colvar
#   ${OUTDIR}/aex1_proj.colvar
#   ${OUTDIR}/comparison.md
#   ${OUTDIR}/comparison.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTOR="${SCRIPT_DIR}/project_to_path.py"
COMPARER="${SCRIPT_DIR}/compare_projections.py"

ANIMA_ROOT="${ANIMA_ROOT:-/work/users/l/i/liualex/AnimaLab}"
PATH_PDB="${PATH_PDB:-${ANIMA_ROOT}/metadynamics/single_walker/path_gromacs.pdb}"
LAMBDA_VAL="${LAMBDA_VAL:-379.77}"

AIN_TRAJ="${AIN_TRAJ:-${ANIMA_ROOT}/classical_md/output/prod_500ns.nc}"
AIN_TOP="${AIN_TOP:-${ANIMA_ROOT}/system_build/pftrps_ain.parm7}"
AIN_BEGIN_NS="${AIN_BEGIN_NS:-100}"
AIN_END_NS="${AIN_END_NS:-105}"
AIN_STRIDE="${AIN_STRIDE:-1}"

AEX1_TRAJ="${AEX1_TRAJ:-${ANIMA_ROOT}/classical_md/aex1_openmm/prod/prod.dcd}"
AEX1_TOP="${AEX1_TOP:-${ANIMA_ROOT}/classical_md/aex1_openmm/build/aex1_initial.pdb}"
AEX1_BEGIN_NS="${AEX1_BEGIN_NS:-10}"
AEX1_END_NS="${AEX1_END_NS:-15}"
AEX1_STRIDE="${AEX1_STRIDE:-1}"

OUTDIR="${OUTDIR:-${ANIMA_ROOT}/analysis/path_projection_attribution_$(date -u +%Y%m%dT%H%M%SZ)}"
PLUMED_EXE="${PLUMED_EXE:-plumed}"

mkdir -p "${OUTDIR}"
echo "[out] ${OUTDIR}"

ns_to_ps() { python3 -c "print(float('$1') * 1000.0)"; }

AIN_BEGIN_PS=$(ns_to_ps "${AIN_BEGIN_NS}")
AIN_END_PS=$(ns_to_ps "${AIN_END_NS}")
AEX1_BEGIN_PS=$(ns_to_ps "${AEX1_BEGIN_NS}")
AEX1_END_PS=$(ns_to_ps "${AEX1_END_NS}")

echo "[ain] window ${AIN_BEGIN_NS}-${AIN_END_NS} ns, stride ${AIN_STRIDE}"
python3 "${PROJECTOR}" \
    --traj "${AIN_TRAJ}" --top "${AIN_TOP}" \
    --path-pdb "${PATH_PDB}" \
    --begin-ps "${AIN_BEGIN_PS}" --end-ps "${AIN_END_PS}" \
    --stride "${AIN_STRIDE}" \
    --output-colvar "${OUTDIR}/ain_proj.colvar" \
    --plumed-exe "${PLUMED_EXE}" \
    --lambda-val "${LAMBDA_VAL}" \
    --label "ain_cMD_${AIN_BEGIN_NS}-${AIN_END_NS}ns"

echo "[aex1] window ${AEX1_BEGIN_NS}-${AEX1_END_NS} ns, stride ${AEX1_STRIDE}"
python3 "${PROJECTOR}" \
    --traj "${AEX1_TRAJ}" --top "${AEX1_TOP}" \
    --path-pdb "${PATH_PDB}" \
    --begin-ps "${AEX1_BEGIN_PS}" --end-ps "${AEX1_END_PS}" \
    --stride "${AEX1_STRIDE}" \
    --output-colvar "${OUTDIR}/aex1_proj.colvar" \
    --plumed-exe "${PLUMED_EXE}" \
    --lambda-val "${LAMBDA_VAL}" \
    --label "aex1_cMD_${AEX1_BEGIN_NS}-${AEX1_END_NS}ns"

echo "[compare]"
python3 "${COMPARER}" \
    "${OUTDIR}/ain_proj.colvar" \
    "${OUTDIR}/aex1_proj.colvar" \
    --json "${OUTDIR}/comparison.json" \
    | tee "${OUTDIR}/comparison.md"

echo "[done] ${OUTDIR}"
