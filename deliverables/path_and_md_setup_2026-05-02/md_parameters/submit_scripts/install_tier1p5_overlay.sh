#!/bin/bash
set -euo pipefail

SRC=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_production_2026-04-25
DST=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_tier1p5
OVERLAY=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/_tier1p5_overlay_tmp

if [[ -e "${DST}" ]]; then
  echo "ERROR: ${DST} already exists; refusing to overwrite." >&2
  exit 30
fi
if [[ ! -f "${SRC}/seed_manifest.tsv" ]]; then
  echo "ERROR: missing ${SRC}/seed_manifest.tsv" >&2
  exit 31
fi
if [[ ! -f "${SRC}/walker_00/path_seqaligned_gromacs.pdb" ]]; then
  echo "ERROR: missing path_seqaligned_gromacs.pdb in production walker_00" >&2
  exit 32
fi

mkdir -p "${DST}"
cp "${SRC}/seed_manifest.tsv" "${DST}/seed_manifest.tsv"
cp "${OVERLAY}/submit_array_3walker.sh" "${DST}/submit_array_3walker.sh"
cp "${OVERLAY}/submit_array_10walker.sh" "${DST}/submit_array_10walker.sh"
chmod +x "${DST}/submit_array_3walker.sh" "${DST}/submit_array_10walker.sh"

for n in $(seq 0 9); do
  idx=$(printf "%02d" "${n}")
  mkdir -p "${DST}/walker_${idx}"
  for f in start.gro topol.top em.mdp path_seqaligned_gromacs.pdb provenance.txt; do
    cp "${SRC}/walker_${idx}/${f}" "${DST}/walker_${idx}/${f}"
  done
  cp "${OVERLAY}/nvt.mdp" "${DST}/walker_${idx}/nvt.mdp"
  cp "${OVERLAY}"/metad_stage*.mdp "${DST}/walker_${idx}/"
  cp "${OVERLAY}/metad_prod.mdp" "${DST}/walker_${idx}/metad_prod.mdp"
  wid=$((10#${idx}))
  for f in "${OVERLAY}"/plumed_stage*.dat "${OVERLAY}/plumed_prod.dat"; do
    base=$(basename "${f}")
    sed "s/__WALKERS_ID__/${wid}/g" "${f}" > "${DST}/walker_${idx}/${base}"
  done
done

cat > "${DST}/README_TIER1P5.txt" <<'EOF'
Tier 1.5 staged directory. Do not sbatch until PM approval.

Launch commands:
  cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_tier1p5
  sbatch submit_array_3walker.sh
  sbatch submit_array_10walker.sh

Scripts fail if HILLS_DIR_tier1p5 already exists from a previous run.
EOF

echo "Installed ${DST}"
find "${DST}" -maxdepth 2 -type f | sort | wc -l
