#!/bin/bash
# ============================================
# PLUMED + AMBER Setup Script for UNC Longleaf
# 一键安装 PLUMED 并接入 AMBER 24p3
# 复制整个脚本到 Longleaf 终端运行即可
# ============================================

set -e  # 出错即停

echo "====== Step 1: Loading modules ======"
module load anaconda/2024.02
module load amber/24p3
echo "Modules loaded OK"

echo ""
echo "====== Step 2: Creating conda environment ======"
if conda env list | grep -q "trpb-md"; then
    echo "Environment trpb-md already exists, activating..."
else
    conda create -n trpb-md python=3.10 -y
fi

# conda activate doesn't work in scripts without init
eval "$(conda shell.bash hook)"
conda activate trpb-md
echo "Environment activated: $CONDA_DEFAULT_ENV"

echo ""
echo "====== Step 3: Installing PLUMED ======"
conda install -c conda-forge plumed py-plumed -y
echo "PLUMED installed"

echo ""
echo "====== Step 4: Locating PLUMED kernel ======"
KERNEL_PATH=$(find "$CONDA_PREFIX" -name "libplumedKernel.so" 2>/dev/null | head -1)
if [ -z "$KERNEL_PATH" ]; then
    echo "ERROR: libplumedKernel.so not found!"
    exit 1
fi
echo "Found kernel at: $KERNEL_PATH"

echo ""
echo "====== Step 5: Testing PLUMED ======"
export PLUMED_KERNEL="$KERNEL_PATH"
plumed --version
echo "PLUMED works!"

echo ""
echo "====== Step 6: Testing AMBER pmemd.cuda ======"
PMEMD_PATH=$(which pmemd.cuda 2>/dev/null || echo "")
if [ -z "$PMEMD_PATH" ]; then
    echo "WARNING: pmemd.cuda not found in PATH"
    echo "Checking known location..."
    PMEMD_PATH="/nas/longleaf/rhel9/apps/amber/24p3/amber24gpu/bin/pmemd.cuda"
fi

if [ -f "$PMEMD_PATH" ]; then
    echo "pmemd.cuda found at: $PMEMD_PATH"
    ldd "$PMEMD_PATH" 2>/dev/null | grep -i plumed && echo "PLUMED pre-linked in AMBER" || echo "PLUMED not pre-linked (will use runtime mode via PLUMED_KERNEL)"
else
    echo "ERROR: pmemd.cuda not found"
fi

echo ""
echo "====== Step 7: Writing to ~/.bashrc ======"
# Only add if not already there
if ! grep -q "PLUMED_KERNEL" ~/.bashrc; then
    cat >> ~/.bashrc << EOF

# === TrpB MetaDynamics environment ===
module load anaconda/2024.02
module load amber/24p3
export PLUMED_KERNEL="$KERNEL_PATH"
EOF
    echo "Added to ~/.bashrc"
else
    echo "PLUMED_KERNEL already in ~/.bashrc, skipping"
fi

echo ""
echo "====== DONE ======"
echo ""
echo "Summary:"
echo "  PLUMED version: $(plumed --version 2>&1 | head -1)"
echo "  PLUMED kernel:  $KERNEL_PATH"
echo "  AMBER pmemd:    $PMEMD_PATH"
echo ""
echo "Next: run 'source ~/.bashrc' or log out and back in."
echo "Then test with: plumed driver --help"
