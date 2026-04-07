#!/bin/bash
# setup_walkers.sh — 从 single-walker MetaD 轨迹提取 10 个 snapshots，
# 创建 10 个 walker 目录，准备 10-walker MetaD 生产运行
#
# 用法：
#   cd /work/users/l/i/liualex/AnimaLab/metadynamics/multi_walker
#   bash setup_walkers.sh
#
# 前提：
#   1. single_walker/metad.xtc 已完成（50 ns）
#   2. single_walker/metad.tpr 存在
#   3. single_walker/frames/ 下有 15 个 path reference PDB
#   4. conda activate trpb-md
#
# SI 原文 (JACS 2019, S4):
#   "After an initial metadynamics run, we extracted ten snapshots for
#    each system covering approximately all the conformational space available."

set -eo pipefail

SINGLE_DIR="../single_walker"
NWALKERS=10
TOPOL="${SINGLE_DIR}/topol.top"
MDP="metad.mdp"
PLUMED="plumed.dat"

# --- 检查前提 ---
for f in "${SINGLE_DIR}/metad.xtc" "${SINGLE_DIR}/metad.tpr" "${TOPOL}" "${MDP}" "${PLUMED}"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: $f not found"
        exit 1
    fi
done

if [ ! -d "${SINGLE_DIR}/frames" ]; then
    echo "ERROR: ${SINGLE_DIR}/frames/ not found (need 15 path reference PDBs)"
    exit 1
fi

# --- Step 1: 提取 10 个均匀分布的 snapshots ---
echo "=== Step 1: Extracting 10 snapshots from single-walker trajectory ==="

# 获取轨迹总帧数和时间
LAST_TIME=$(gmx check -f "${SINGLE_DIR}/metad.xtc" 2>&1 | grep "Last frame" | awk '{print $NF}' || true)
if [ -z "$LAST_TIME" ]; then
    # fallback: 从 COLVAR 最后一行读取
    LAST_TIME=$(tail -1 "${SINGLE_DIR}/COLVAR" | awk '{print $1}')
fi
echo "Total simulation time: ${LAST_TIME} ps"

# 均匀选取 10 个时间点（跳过最前面 10% 作为 equilibration）
python3 -c "
import numpy as np
t_max = float('${LAST_TIME}')
t_start = t_max * 0.1  # skip first 10%
times = np.linspace(t_start, t_max, ${NWALKERS})
with open('extract_times.ndx', 'w') as f:
    for t in times:
        f.write(f'{t:.1f}\n')
print('Extraction times (ps):')
for i, t in enumerate(times):
    print(f'  Walker {i:02d}: {t:.1f} ps')
"

# 用 gmx trjconv 提取每个 snapshot
for i in $(seq 0 $((NWALKERS-1))); do
    TIME=$(sed -n "$((i+1))p" extract_times.ndx)
    echo "Extracting walker_${i} at t=${TIME} ps ..."
    echo "System" | gmx trjconv \
        -f "${SINGLE_DIR}/metad.xtc" \
        -s "${SINGLE_DIR}/metad.tpr" \
        -o "snapshot_${i}.gro" \
        -dump "${TIME}" \
        2>/dev/null
done

echo "Extracted ${NWALKERS} snapshots"

# --- Step 2: 创建 walker 目录 ---
echo ""
echo "=== Step 2: Creating walker directories ==="

for i in $(seq 0 $((NWALKERS-1))); do
    DIR="walker_$(printf '%02d' $i)"
    mkdir -p "${DIR}"

    # 起始构型
    cp "snapshot_${i}.gro" "${DIR}/start.gro"

    # 拓扑（symlink 节省空间）
    ln -sf "$(realpath ${TOPOL})" "${DIR}/topol.top"

    # PLUMED 和 MDP（copy，因为 walker 可能需要独立修改）
    cp "${PLUMED}" "${DIR}/plumed.dat"
    cp "${MDP}" "${DIR}/metad.mdp"

    # Path reference frames（symlink）
    ln -sf "$(realpath ${SINGLE_DIR}/frames)" "${DIR}/frames"

    echo "  Created ${DIR}/ with start.gro from t=$(sed -n "$((i+1))p" extract_times.ndx) ps"
done

# 清理临时文件
rm -f extract_times.ndx snapshot_*.gro

echo ""
echo "=== Setup complete ==="
echo "  ${NWALKERS} walker directories created"
echo "  Next: run 'bash submit_all.sh' to submit all walkers"
echo ""
echo "  Directory structure:"
echo "  multi_walker/"
for i in $(seq 0 $((NWALKERS-1))); do
    echo "  ├── walker_$(printf '%02d' $i)/"
done
echo "  ├── plumed.dat (template)"
echo "  ├── metad.mdp (template)"
echo "  ├── setup_walkers.sh (this script)"
echo "  └── submit_all.sh"
