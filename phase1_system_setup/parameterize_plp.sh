#!/bin/bash

set -e
set -u

PROJECT_DIR="/work/users/l/i/liualex/AnimaLab"
PARAM_DIR="${PROJECT_DIR}/parameters"
STRUCT_DIR="${PROJECT_DIR}/structures"
LOG_DIR="${PROJECT_DIR}/logs"

mkdir -p "${PARAM_DIR}"/{plp_structures,resp_charges,mol2,frcmod,tleap_inputs}
mkdir -p "${LOG_DIR}"

export AMBER_BIN="${AMBER}/bin"

INTERMEDIATES=("Ain" "Aex1" "A-A" "Q2")

declare -A PDB_FILES=(
    ["Ain"]="5DVZ"
    ["Aex1"]="5DW0"
    ["A-A"]="4HPX"
    ["Q2"]="PLACEHOLDER"
)

declare -A RESIDUE_NAMES=(
    ["Ain"]="LLP"
    ["Aex1"]="PLS"
    ["A-A"]="0JO"
    ["Q2"]="UNKNOWN"
)

declare -A EXPECTED_ATOM_COUNTS=(
    ["Ain"]="24"
    ["Aex1"]="22"
    ["A-A"]="0"
    ["Q2"]="0"
)

declare -A CHAIN_SELECTION=(
    ["Ain"]="A"
    ["Aex1"]="A"
    ["A-A"]="A"
    ["Q2"]="A"
)

declare -A CHARGES=(
    ["Ain"]="-2"
    ["Aex1"]="-2"
    ["A-A"]="-2"
    ["Q2"]="-2"
)

declare -A MULTIPLICITIES=(
    ["Ain"]="1"
    ["Aex1"]="1"
    ["A-A"]="1"
    ["Q2"]="1"
)

echo "=========================================="
echo "PLP Parameterization Workflow"
echo "=========================================="
echo "Project dir: ${PROJECT_DIR}"
echo "Output dir: ${PARAM_DIR}"
echo "Timestamp: $(date)"
echo ""

echo "Step 1: Extracting PLP-intermediate residues from PDB files..."
echo ""

extract_residue_from_pdb() {
    local pdb_code=$1
    local intermediate=$2
    local resname=$3
    local chain=$4
    local expected_count=$5
    local pdb_file="${STRUCT_DIR}/${pdb_code}.pdb"
    local output_pdb="${PARAM_DIR}/plp_structures/${intermediate}_raw.pdb"

    echo "  Processing ${intermediate} (${pdb_code}, chain ${chain}, residue ${resname})..."

    if [ "${pdb_code}" = "PLACEHOLDER" ]; then
        echo "    SKIP: No PDB assigned for ${intermediate} yet."
        return 1
    fi

    if [ "${resname}" = "UNKNOWN" ]; then
        echo "    SKIP: Residue name unknown for ${intermediate}."
        echo "    ACTION: Download ${pdb_code}.pdb and run:"
        echo "      grep '^HETATM' ${pdb_code}.pdb | awk '{print \$4}' | sort -u"
        return 1
    fi

    if [ ! -f "${pdb_file}" ]; then
        echo "    ERROR: PDB file not found: ${pdb_file}"
        echo "    ACTION: Download with:"
        echo "      wget -O ${pdb_file} https://files.rcsb.org/download/${pdb_code}.pdb"
        return 1
    fi

    grep -E "^(HETATM|ATOM  )" "${pdb_file}" \
        | awk -v res="${resname}" -v ch="${chain}" \
              '{rn=substr($0,18,3); gsub(/ /,"",rn); cid=substr($0,22,1); if(rn==res && cid==ch) print}' \
        > "${output_pdb}" 2>/dev/null

    local actual_count
    actual_count=$(wc -l < "${output_pdb}" | tr -d ' ')

    if [ "${actual_count}" -eq 0 ]; then
        echo "    ERROR: No atoms found for residue ${resname} chain ${chain} in ${pdb_file}"
        echo "    DEBUG: Available HETATM residue names in this PDB:"
        grep "^HETATM" "${pdb_file}" | awk '{print substr($0,18,3)}' | sort -u | head -10
        return 1
    fi

    echo "    Extracted ${actual_count} atoms to ${output_pdb}"

    if [ "${expected_count}" -gt 0 ] && [ "${actual_count}" -ne "${expected_count}" ]; then
        echo "    WARNING: Expected ${expected_count} atoms but got ${actual_count}."
        echo "             Check for alternate conformations (altLoc) or missing atoms."
    else
        echo "    Atom count matches expected (${expected_count})."
    fi

    echo "    Atom names extracted:"
    awk '{printf "      %s\n", substr($0,13,4)}' "${output_pdb}"

    echo ""
}

for intermediate in "${INTERMEDIATES[@]}"; do
    pdb_code="${PDB_FILES[$intermediate]}"
    resname="${RESIDUE_NAMES[$intermediate]}"
    chain="${CHAIN_SELECTION[$intermediate]}"
    expected="${EXPECTED_ATOM_COUNTS[$intermediate]}"

    extract_residue_from_pdb "${pdb_code}" "${intermediate}" "${resname}" "${chain}" "${expected}" \
        || echo "    Skipping ${intermediate}..."
done

echo ""
echo "Step 1 complete. Raw residue structures in ${PARAM_DIR}/plp_structures/"
echo ""

echo "Step 2: Adding ACE/NME caps for Gaussian QM input..."
echo ""
echo "  WHY: The modified residues (LLP, PLS) include backbone atoms"
echo "       (N, CA, C, O). For QM charge calculation, we must cap the"
echo "       backbone termini to avoid artificial charges from dangling bonds."
echo "       ACE caps the N-terminus; NME caps the C-terminus."
echo ""

add_caps_for_qm() {
    local intermediate=$1
    local raw_pdb="${PARAM_DIR}/plp_structures/${intermediate}_raw.pdb"
    local capped_pdb="${PARAM_DIR}/plp_structures/${intermediate}_capped.pdb"

    if [ ! -f "${raw_pdb}" ]; then
        echo "  SKIP: ${raw_pdb} not found."
        return 1
    fi

    echo "  Processing ${intermediate}..."

    local cap_script="${PARAM_DIR}/plp_structures/${intermediate}_cap.in"

    cat > "${cap_script}" << CAP_EOF

source leaprc.ff14SB
source leaprc.gaff

mol = loadpdb ${raw_pdb}

savepdb mol ${capped_pdb}
quit
CAP_EOF

    echo "    Generated capping script: ${cap_script}"
    echo ""
    echo "    RECOMMENDED MANUAL APPROACH:"
    echo "    1. Open ${raw_pdb} in PyMOL"
    echo "    2. Add ACE cap: place CH3-CO group bonded to backbone N"
    echo "    3. Add NME cap: place NH-CH3 group bonded to backbone C"
    echo "    4. Add hydrogens (reduce or PyMOL h_add)"
    echo "    5. Save as ${capped_pdb}"
    echo "    6. Verify: total atoms = heavy atoms + hydrogens + cap atoms"
    echo ""
}

for intermediate in "${INTERMEDIATES[@]}"; do
    add_caps_for_qm "${intermediate}" || echo "  Continuing..."
done

echo "Step 2 complete."
echo ""

echo "Step 3: Preparing Gaussian 16 input for RESP charge fitting..."
echo ""
echo "  Protocol (from SI): RESP charges at HF/6-31G(d) level"
echo "  Software: Gaussian 16c02 (available on Longleaf)"
echo "  Workflow:"
echo "    1. antechamber converts capped PDB to Gaussian input (.com)"
echo "    2. Gaussian 16 runs QM geometry optimization + ESP"
echo "    3. antechamber extracts RESP charges from Gaussian output"
echo ""

create_gaussian_input() {
    local intermediate=$1
    local charge=${CHARGES[$intermediate]}
    local mult=${MULTIPLICITIES[$intermediate]}

    local input_pdb="${PARAM_DIR}/plp_structures/${intermediate}_capped.pdb"
    if [ ! -f "${input_pdb}" ]; then
        input_pdb="${PARAM_DIR}/plp_structures/${intermediate}_raw.pdb"
    fi

    if [ ! -f "${input_pdb}" ]; then
        echo "  SKIP: No PDB found for ${intermediate}."
        return 1
    fi

    local gauss_input="${PARAM_DIR}/resp_charges/${intermediate}_opt.com"
    local gauss_log="${PARAM_DIR}/resp_charges/${intermediate}_opt.log"

    echo "  Creating Gaussian 16 input for ${intermediate}..."
    echo "    Input PDB: ${input_pdb}"
    echo "    Charge: ${charge}, Multiplicity: ${mult}"

    "${AMBER_BIN}/antechamber" \
        -i "${input_pdb}" \
        -fi pdb \
        -o "${gauss_input}" \
        -fo gcrt \
        -gv 1 \
        -ge "${gauss_log}" \
        -nc "${charge}" \
        -m "${mult}" \
        -at gaff \
        2>&1 | tee "${LOG_DIR}/antechamber_gcrt_${intermediate}.log"

    if [ ! -f "${gauss_input}" ]; then
        echo "    ERROR: antechamber failed to create Gaussian input."
        echo "    Falling back to manual template..."

        cat > "${gauss_input}" << GAUSS_EOF
%chk=${intermediate}_opt.chk
%nprocshared=8
%mem=8GB

${intermediate} PLP-intermediate geometry optimization for RESP charges

${charge} ${mult}
[PLACEHOLDER: paste Cartesian coordinates here from ${input_pdb}]
[FORMAT: Element  X.xxxxxx  Y.yyyyyy  Z.zzzzzz]

GAUSS_EOF

        echo "    Template created: ${gauss_input}"
        echo "    [HUMAN DECISION] Fill in coordinates manually."
    else
        echo "    Gaussian input created: ${gauss_input}"
    fi

    if [ -f "${gauss_input}" ]; then
        if ! grep -q "Pop=MK" "${gauss_input}"; then
            echo "    Patching Gaussian route line for RESP ESP keywords..."
            sed -i.bak 's|# HF/6-31G\*|#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt|' "${gauss_input}" 2>/dev/null || true
            echo "    NOTE: Verify the route line manually before submitting."
        fi
    fi

    echo ""
}

for intermediate in "${INTERMEDIATES[@]}"; do
    create_gaussian_input "${intermediate}" || echo "  Continuing..."
done

echo "Step 3 complete. Gaussian inputs in ${PARAM_DIR}/resp_charges/"
echo ""
echo "  MANUAL STEPS REQUIRED:"
echo "  ====================="
echo "  1. [HUMAN DECISION] Verify charge/multiplicity for each intermediate"
echo "  2. Submit Gaussian jobs on Longleaf:"
echo "     module load gaussian/16c02    # [CHECK: module avail gaussian]"
echo "     cd ${PARAM_DIR}/resp_charges/"
echo "     for f in *.com; do"
echo "       g16 \$f"
echo "     done"
echo "  3. Check for normal termination:"
echo "     grep 'Normal termination' *.log"
echo "  4. Extract RESP charges (see Section 5)."
echo ""

echo "Step 4: Running antechamber to assign GAFF atom types and RESP charges..."
echo ""
echo "  NOTE: This step requires completed Gaussian .log files from Step 3."
echo "        If Gaussian has not been run yet, production mode hard-fails instead"
echo "        of falling back to BCC charges (FP-009: RESP only for PLP)."
echo ""

run_antechamber() {
    local intermediate=$1
    local charge=${CHARGES[$intermediate]}
    local mult=${MULTIPLICITIES[$intermediate]}
    local resname="${RESIDUE_NAMES[$intermediate]}"

    local gauss_log="${PARAM_DIR}/resp_charges/${intermediate}_opt.log"
    local output_mol2="${PARAM_DIR}/mol2/${intermediate}_gaff.mol2"

    if [ -f "${gauss_log}" ] && grep -q "Normal termination" "${gauss_log}"; then
        echo "  Processing ${intermediate} with RESP charges from Gaussian..."

        "${AMBER_BIN}/antechamber" \
            -i "${gauss_log}" \
            -fi gout \
            -o "${output_mol2}" \
            -fo mol2 \
            -at gaff \
            -c resp \
            -nc "${charge}" \
            -m "${mult}" \
            -rn "${resname}" \
            2>&1 | tee "${LOG_DIR}/antechamber_resp_${intermediate}.log"

    else
        echo "FATAL: BCC fallback triggered in production mode. FP-009 prohibits BCC for PLP. Use RESP only."
        exit 1
    fi

    if [ -f "${output_mol2}" ]; then
        echo "    MOL2 saved: ${output_mol2}"

        local mol2_atoms
        mol2_atoms=$(grep -c "^[[:space:]]*[0-9]" "${output_mol2}" 2>/dev/null || echo "0")
        echo "    Atoms in MOL2: ${mol2_atoms}"
    else
        echo "    ERROR: antechamber failed for ${intermediate}"
        return 1
    fi

    echo ""
}

for intermediate in "${INTERMEDIATES[@]}"; do
    run_antechamber "${intermediate}" || echo "  Continuing with next intermediate..."
done

echo "Step 4 complete. MOL2 files with GAFF atoms in ${PARAM_DIR}/mol2/"
echo ""

echo "Step 5: Running parmchk2 to generate missing GAFF parameters..."
echo ""

run_parmchk2() {
    local intermediate=$1
    local input_mol2="${PARAM_DIR}/mol2/${intermediate}_gaff.mol2"
    local output_frcmod="${PARAM_DIR}/frcmod/${intermediate}.frcmod"

    if [ ! -f "${input_mol2}" ]; then
        echo "  SKIP: ${intermediate} (MOL2 not found)"
        return 1
    fi

    echo "  Processing ${intermediate}..."

    "${AMBER_BIN}/parmchk2" \
        -i "${input_mol2}" \
        -f mol2 \
        -o "${output_frcmod}" \
        2>&1 | tee "${LOG_DIR}/parmchk2_${intermediate}.log"

    if [ -f "${output_frcmod}" ]; then
        echo "    frcmod saved: ${output_frcmod}"

        local missing
        missing=$(grep -c "ATTN" "${output_frcmod}" 2>/dev/null || echo "0")
        echo "    Missing/estimated parameters: ${missing}"
        if [ "${missing}" -gt 0 ]; then
            echo "    [WARNING] Review high-penalty terms manually:"
            grep "ATTN" "${output_frcmod}" | head -5
        fi
    else
        echo "    ERROR: parmchk2 failed for ${intermediate}"
        return 1
    fi

    echo ""
}

for intermediate in "${INTERMEDIATES[@]}"; do
    run_parmchk2 "${intermediate}" || echo "  Continuing..."
done

echo "Step 5 complete. frcmod files in ${PARAM_DIR}/frcmod/"
echo ""

echo "Step 6: Creating tleap input for system assembly..."
echo ""
echo "  NOTE: The modified residue (LLP/PLS) is covalently bonded to K82/Ser."
echo "        tleap needs explicit bond commands to connect the cofactor to the protein."
echo "        This requires knowing the residue number of K82 in the processed PDB."
echo ""

create_tleap_input() {
    local intermediate=$1
    local resname="${RESIDUE_NAMES[$intermediate]}"
    local pdb_code="${PDB_FILES[$intermediate]}"
    local chain="${CHAIN_SELECTION[$intermediate]}"

    local output_parm="${PARAM_DIR}/tleap_inputs/${intermediate}_complete.parm7"
    local output_inpcrd="${PARAM_DIR}/tleap_inputs/${intermediate}_complete.inpcrd"
    local tleap_script="${PARAM_DIR}/tleap_inputs/${intermediate}_build.in"

    local input_mol2="${PARAM_DIR}/mol2/${intermediate}_gaff.mol2"
    local input_frcmod="${PARAM_DIR}/frcmod/${intermediate}.frcmod"
    local protein_pdb="${STRUCT_DIR}/${pdb_code}_chain${chain}_prepared.pdb"

    echo "  Creating tleap script for ${intermediate}..."
    echo "  [HUMAN DECISION] Before running tleap:"
    echo "    1. Prepare ${protein_pdb} (extract chain ${chain}, remove waters/ions, add H)"
    echo "    2. Remove the modified residue from the protein PDB"
    echo "    3. Verify residue numbering matches bond commands below"

    cat > "${tleap_script}" << TLEAP_EOF

source leaprc.protein.ff14SB
source leaprc.gaff
source leaprc.water.tip3p

${resname} = loadmol2 ${input_mol2}
loadamberparams ${input_frcmod}

check ${resname}

solvatebox Complex TIP3PBOX 10.0

addions Complex Na+ 0
addions Complex Cl- 0

check Complex

saveamberparm Complex ${output_parm} ${output_inpcrd}

savepdb Complex ${output_parm%.parm7}.pdb

quit
TLEAP_EOF

    echo "    tleap script saved: ${tleap_script}"
    echo ""
}

for intermediate in "${INTERMEDIATES[@]}"; do
    if [ "${PDB_FILES[$intermediate]}" != "PLACEHOLDER" ]; then
        create_tleap_input "${intermediate}" || echo "  Continuing..."
    else
        echo "  SKIP: ${intermediate} (no PDB assigned)"
    fi
done

echo "Step 6 complete. tleap scripts in ${PARAM_DIR}/tleap_inputs/"
echo ""

echo ""
echo "=========================================="
echo "PARAMETERIZATION WORKFLOW COMPLETE"
echo "=========================================="
echo ""

echo "Summary of outputs:"
echo "  1. Raw residue PDBs:    ${PARAM_DIR}/plp_structures/*_raw.pdb"
echo "  2. Capping scripts:     ${PARAM_DIR}/plp_structures/*_cap.in"
echo "  3. Gaussian inputs:     ${PARAM_DIR}/resp_charges/*.com"
echo "  4. MOL2 (GAFF atoms):   ${PARAM_DIR}/mol2/"
echo "  5. frcmod (missing):    ${PARAM_DIR}/frcmod/"
echo "  6. tleap scripts:       ${PARAM_DIR}/tleap_inputs/"
echo ""

echo "HUMAN DECISIONS REQUIRED BEFORE PRODUCTION:"
echo "  [ ] 1. Download 4HPX.pdb and verify 0JO atom count:"
echo "        grep '^HETATM.*0JO' 4HPX.pdb | wc -l"
echo "  [ ] 2. Build Q2 model (from MD snapshot or manual construction)"
echo "  [ ] 3. Verify charge/multiplicity for each intermediate"
echo "        Open capped PDBs in PyMOL, count protons, determine net charge"
echo "  [ ] 4. Cap backbone termini (ACE/NME) on extracted residues"
echo "        Recommended: PyMOL Builder or Chimera AddH"
echo "  [ ] 5. Run Gaussian 16 QM optimizations:"
echo "        module load gaussian/16c02   # verify: module avail gaussian"
echo "        cd ${PARAM_DIR}/resp_charges/"
echo "        for f in *.com; do g16 \$f; done"
echo "  [ ] 6. Re-run antechamber with RESP charges from Gaussian .log"
echo "  [ ] 7. Review frcmod files for high-penalty extrapolated parameters"
echo "  [ ] 8. Prepare protein PDBs (single chain, remove modified residue)"
echo "  [ ] 9. Define covalent bonds in tleap scripts (K82-NZ to PLP-C4')"
echo "  [ ] 10. Run tleap and check for errors:"
echo "         cd ${PARAM_DIR}/tleap_inputs/"
echo "         for f in *_build.in; do tleap -f \$f 2>&1 | tee \${f%.in}.log; done"
echo ""

echo "References:"
echo "  - AMBER manual: https://ambermd.org/doc12/"
echo "  - GAFF: Wang et al., J Comp Chem. 2004, 25, 1157"
echo "  - RESP: Bayly et al., J Phys Chem. 1993, 97, 10269"
echo "  - SI protocol: ja9b03646_si_001.pdf (GAFF + RESP at HF/6-31G(d))"
echo ""

echo "Timestamp: $(date)"
echo ""
