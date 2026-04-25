#!/bin/bash
#SBATCH --job-name=openmm_toy
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=openmm_toy_%j.out
#SBATCH --error=openmm_toy_%j.err
export OPENMM_PLATFORM=CPU

set -eo pipefail
module purge
source /nas/longleaf/rhel9/apps/anaconda/2024.02/etc/profile.d/conda.sh
conda activate md_setup_trpb

cd "$SLURM_SUBMIT_DIR"
echo "=== ENV ==="
python -c "import openmm; print('openmm', openmm.__version__)"
python -c "from openmmplumed import PlumedForce; print('openmm-plumed OK')"

echo "=== Build alanine dipeptide PDB via tleap ==="
rm -f alanine_dipeptide.pdb leap.log
tleap -f - <<'EOF'
source leaprc.protein.ff14SB
mol = sequence { ACE ALA NME }
savepdb mol alanine_dipeptide.pdb
quit
EOF
head -3 alanine_dipeptide.pdb
echo "atom count: $(grep -c '^ATOM' alanine_dipeptide.pdb)"

# PLUMED atom indices (1-based) are recomputed after tleap — find phi/psi atoms
python - <<'PY'
from openmm.app import PDBFile
p = PDBFile("alanine_dipeptide.pdb")
names = [(i+1, a.name, a.residue.name) for i,a in enumerate(p.topology.atoms())]
for x in names: print(x)
PY

echo "=== TOY cMD ==="
mkdir -p run_cmd && cp alanine_dipeptide.pdb run_cmd/
(cd run_cmd && python ../toy_cmd.py)

echo "=== TOY MetaD (PLUMED plugin) ==="
mkdir -p run_metad && cp alanine_dipeptide.pdb run_metad/
(cd run_metad && python ../toy_metad.py)

echo "=== DONE ==="
