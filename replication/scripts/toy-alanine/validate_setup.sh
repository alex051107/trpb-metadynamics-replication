#!/bin/bash

# Validation script: Check all files are present and correctly formatted
# Run this before submitting the job

echo "=========================================="
echo "Alanine Dipeptide Toy Test — File Validation"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# ============================================================================
# Check required files
# ============================================================================

echo "[1/4] Checking required files..."
echo ""

required_files=(
    "setup_alanine.sh"
    "plumed_metad.dat"
    "run_metad.mdp"
    "submit_metad.slurm"
    "analyze_fes.py"
    "README.md"
    "QUICKSTART.md"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✓ $file"
    else
        echo "  ✗ MISSING: $file"
        ((ERRORS++))
    fi
done

echo ""

# ============================================================================
# Check file permissions
# ============================================================================

echo "[2/4] Checking executable permissions..."
echo ""

executable_files=("setup_alanine.sh" "submit_metad.slurm" "analyze_fes.py")

for file in "${executable_files[@]}"; do
    if [[ -x "$file" ]]; then
        echo "  ✓ $file is executable"
    else
        echo "  ⚠ $file is NOT executable (fixing...)"
        chmod +x "$file"
        ((WARNINGS++))
    fi
done

echo ""

# ============================================================================
# Check bash syntax
# ============================================================================

echo "[3/4] Checking bash syntax..."
echo ""

for file in setup_alanine.sh submit_metad.slurm; do
    if bash -n "$file" 2>/dev/null; then
        echo "  ✓ $file (bash syntax OK)"
    else
        echo "  ✗ $file (bash syntax ERROR)"
        ((ERRORS++))
    fi
done

echo ""

# ============================================================================
# Check Python syntax
# ============================================================================

echo "[4/4] Checking Python syntax..."
echo ""

if python3 -m py_compile analyze_fes.py 2>/dev/null; then
    echo "  ✓ analyze_fes.py (Python syntax OK)"
else
    echo "  ✗ analyze_fes.py (Python syntax ERROR)"
    ((ERRORS++))
fi

echo ""

# ============================================================================
# Check key configuration values
# ============================================================================

echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo ""

echo "Setup phase:"
grep -E "CONDA_ENV|FF=|WATER=" setup_alanine.sh | sed 's/^/  /'

echo ""
echo "MetaDynamics parameters (plumed_metad.dat):"
grep -E "HEIGHT|SIGMA|BIASFACTOR|PACE" plumed_metad.dat | sed 's/^/  /'

echo ""
echo "Production MD parameters (run_metad.mdp):"
grep -E "^dt |^nsteps|^ref_t |^integrator" run_metad.mdp | sed 's/^/  /'

echo ""
echo "SLURM job parameters (submit_metad.slurm):"
grep "^#SBATCH" submit_metad.slurm | sed 's/^/  /'

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=========================================="
if [[ $ERRORS -eq 0 ]]; then
    echo "✓ Validation PASSED"
    echo ""
    echo "All files are present and ready to use."
    echo ""
    echo "Next steps:"
    echo "  1. bash setup_alanine.sh         # ~30 min"
    echo "  2. sbatch submit_metad.slurm    # ~1 hour"
    echo "  3. python3 analyze_fes.py       # ~5 min"
    exit 0
else
    echo "✗ Validation FAILED"
    echo ""
    echo "Errors found: $ERRORS"
    if [[ $WARNINGS -gt 0 ]]; then
        echo "Warnings: $WARNINGS (auto-fixed)"
    fi
    exit 1
fi
