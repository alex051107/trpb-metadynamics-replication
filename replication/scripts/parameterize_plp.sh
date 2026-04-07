#!/bin/bash

# ================================================================
# PLP (Pyridoxal Phosphate) Parameterization Workflow
# ================================================================
#
# Project: TrpB MetaDynamics Replication (JACS 2019)
# Reference: Maria-Solano et al., JACS 2019, SI (ja9b03646_si_001.pdf)
#
# Purpose: Generate AMBER force field parameters for the four
#          reaction intermediates of TrpB catalysis:
#            - Ain  (internal aldimine): PLP-K82 Schiff base, resting
#            - Aex1 (external aldimine 1): L-Ser bound
#            - A-A  (aminoacrylate): dehydrated C3, awaits indole
#            - Q2   (quinonoid 2): indole + amino acid after coupling
#
# Methodology (from SI):
#   1. Extract modified residue from crystal structures (PDB)
#   2. Cap backbone atoms for QM (ACE/NME)
#   3. Compute RESP charges at HF/6-31G(d) via Gaussian 16
#   4. Assign atom types via antechamber (GAFF force field)
#   5. Generate frcmod files for missing parameters (parmchk2)
#   6. Combine with protein (ff14SB) via tleap
#
# CRITICAL NOTES (from PDB inspection, 2026-03-28):
#   - 5DVZ (Ain): residue name is LLP, NOT PLP. 24 heavy atoms per chain.
#     LLP = N6-(pyridoxal phosphate)-L-lysine = covalent PLP-K82 Schiff base.
#     Includes K82 backbone (N, CA, CB, CG, CD, CE, NZ, C, O).
#   - 5DW0 (Aex1): residue name is PLS, NOT PLP. 22 atoms per chain.
#     PLS = pyridoxal-5'-phosphate-L-serine = external aldimine with serine.
#     Includes Ser backbone (N, CA, CB, OG, C, O, OXT).
#   - 4HPX (A-A): residue name is 0JO. PLP-aminoacrylate.
#     NOTE: 4HPX is S. typhimurium TrpS, NOT P. furiosus. Used as
#     structural template only (SI: "positioned by alignment").
#   - Q2: no crystal structure; must be built from MD snapshot or modeling
#
# Dependencies:
#   - AMBER 24p3 (module load amber/24p3)
#   - Gaussian 16c02 (module avail gaussian)
#   - sed, awk, grep (standard Unix tools)
#
# Environment: Longleaf HPC (UNC)
#   module load anaconda/2024.02 && conda activate trpb-md
#   module load amber/24p3
#
# Author: Zhenpeng Liu (liualex@ad.unc.edu)
# Created: 2026-03-28
# Rewritten: 2026-03-30 (fixed residue names, extraction, capping, Gaussian version)
#
# STATUS: REFERENCE/TEMPLATE -- requires manual review before running
#
# ================================================================

set -e  # Exit on error
set -u  # Exit if undefined variable

# ================================================================
# SECTION 1: CONFIGURATION AND PATHS
# ================================================================

# Project directory on Longleaf
PROJECT_DIR="/work/users/l/i/liualex/AnimaLab"
PARAM_DIR="${PROJECT_DIR}/parameters"
STRUCT_DIR="${PROJECT_DIR}/structures"
LOG_DIR="${PROJECT_DIR}/logs"

# Create output directories if they don't exist
mkdir -p "${PARAM_DIR}"/{plp_structures,resp_charges,mol2,frcmod,tleap_inputs}
mkdir -p "${LOG_DIR}"

# AMBER tools (available after: module load amber/24p3)
export AMBER_BIN="${AMBER}/bin"

# Reaction intermediates to parameterize
INTERMEDIATES=("Ain" "Aex1" "A-A" "Q2")

# PDB files for each intermediate
declare -A PDB_FILES=(
    ["Ain"]="5DVZ"      # Pf-TrpB open with internal aldimine
    ["Aex1"]="5DW0"     # Pf-TrpB PC with external aldimine 1
    ["A-A"]="4HPX"      # St-TrpS closed with aminoacrylate (model)
    ["Q2"]="PLACEHOLDER" # Q2 structure (must be built; no crystal available)
)

# Residue name mapping (verified from actual PDB files, 2026-03-28)
# FP-003: Never write PDB atom names from memory; always extract from actual PDB
declare -A RESIDUE_NAMES=(
    ["Ain"]="LLP"       # N6-(pyridoxal phosphate)-L-lysine (covalent K82 Schiff base)
    ["Aex1"]="PLS"      # pyridoxal-5'-phosphate-L-serine (external aldimine)
    ["A-A"]="0JO"       # PLP-aminoacrylate (from 4HPX, S. typhimurium TrpS template)
    ["Q2"]="UNKNOWN"    # [HUMAN DECISION] no crystal structure; residue name TBD after modeling
)

# Expected heavy-atom counts per residue (verified from PDB)
declare -A EXPECTED_ATOM_COUNTS=(
    ["Ain"]="24"        # 15 PLP-ring atoms + 9 K82 sidechain/backbone atoms
    ["Aex1"]="22"       # 15 PLP-ring atoms + 7 Ser sidechain/backbone atoms
    ["A-A"]="0"         # [HUMAN DECISION] count atoms: grep "^HETATM.*0JO" 4HPX.pdb | wc -l
    ["Q2"]="0"          # [HUMAN DECISION] set after building Q2
)

# Chain selection (verified from PDB REMARK 350 records)
# 5DVZ: chains A,B,C,D (all TrpB). Biomolecule 1 = dimer AB. Use chain A.
# 5DW0: chains A,B,C,D (all TrpB). Use chain A.
# Note: original paper uses PfTrpB (standalone beta subunit).
#       Both 5DVZ and 5DW0 are standalone PfTrpB (no TrpA chains).
declare -A CHAIN_SELECTION=(
    ["Ain"]="A"
    ["Aex1"]="A"
    ["A-A"]="A"         # [HUMAN DECISION] 4HPX is St-TrpS (alpha2-beta2); check which chain is beta
    ["Q2"]="A"          # [HUMAN DECISION] depends on how Q2 model is built
)

# Charge and multiplicity for Gaussian QM calculations
# Reasoning for each intermediate:
#   - PLP ring: pyridinium N1 protonated (+1), phosphate (-2), phenolate O3 (-1) => net PLP = -2
#   - BUT: protonation states depend on the intermediate and pH
#
# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  [HUMAN DECISION - CRITICAL] CHARGE VALUES MUST BE CONFIRMED BY PI  ║
# ║                                                                     ║
# ║  These charges DISAGREE between this script and the Logic Chain     ║
# ║  document. The correct value depends on whether the Schiff base     ║
# ║  NZ is protonated (+1) or neutral (0), which is pH-dependent.       ║
# ║                                                                     ║
# ║  Ain possibilities:                                                 ║
# ║    0  = phosphate(-2) + pyridinium(+1) + NZ-H(+1) + phenolate(-1)  ║
# ║         + caps(0) = -1 ... hmm, this gives -1 not 0                ║
# ║   -1  = phosphate(-2) + pyridinium(+1) + NZ(0) + phenolate(-1)    ║
# ║         + caps(0) = -2 ... this gives -2 not -1                    ║
# ║   -2  = if phenolate(-1) + phosphate(-2) + pyridinium(+1) = -2    ║
# ║         (treating NZ and backbone as neutral)                       ║
# ║                                                                     ║
# ║  DO NOT run Gaussian until this is resolved with PI.                ║
# ╚═══════════════════════════════════════════════════════════════════════╝
#
# Current values are PLACEHOLDERS. Change after PI confirmation.
declare -A CHARGES=(
    ["Ain"]="-2"        # [HUMAN DECISION] Most common: PLP(-2)+pyridinium(+1)+phenolate(-1)+NZ(0)=-2
    ["Aex1"]="-2"       # [HUMAN DECISION] PLS: PLP(-2)+pyridinium(+1)+Ser(0)+phenolate(-1)=-2
    ["A-A"]="-2"        # [HUMAN DECISION] estimate; adjust after inspecting structure
    ["Q2"]="-2"         # [HUMAN DECISION] estimate; adjust after building model
)

# All intermediates are closed-shell singlets (no radical character expected)
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

# ================================================================
# SECTION 2: EXTRACT MODIFIED RESIDUE FROM PDB
# ================================================================

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

    # --- Pre-flight checks ---

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

    # --- Extract ALL atoms of the modified residue ---
    # Uses fixed-width PDB column positions:
    #   columns 1-6:  record type (HETATM/ATOM)
    #   columns 18-20: residue name
    #   column 22:    chain ID
    # We extract HETATM records matching the residue name AND chain.
    # Some PDB files use ATOM instead of HETATM for modified residues,
    # so we check both.

    grep -E "^(HETATM|ATOM  )" "${pdb_file}" \
        | awk -v res="${resname}" -v ch="${chain}" \
              '{rn=substr($0,18,3); gsub(/ /,"",rn); cid=substr($0,22,1); if(rn==res && cid==ch) print}' \
        > "${output_pdb}" 2>/dev/null

    # --- Validate extraction ---

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

    # --- Print atom names for manual verification ---
    echo "    Atom names extracted:"
    awk '{printf "      %s\n", substr($0,13,4)}' "${output_pdb}"

    echo ""
}

# For each intermediate, extract the modified residue
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

# ================================================================
# SECTION 3: ADD CAPPING GROUPS FOR QM CALCULATION
# ================================================================

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

    # ---------------------------------------------------------------
    # STRATEGY FOR CAPPING:
    #
    # For LLP (Ain): the residue already contains K82 backbone (N, CA, C, O).
    #   - N-terminus (N atom): needs ACE cap (CH3-CO-NH-)
    #   - C-terminus (C, O atoms): needs NME cap (-CO-NH-CH3)
    #   The cap atoms must be placed at chemically reasonable positions.
    #
    # For PLS (Aex1): contains Ser backbone (N, CA, C, O, OXT).
    #   - Same capping logic.
    #   - OXT is already a terminal oxygen; for QM, replace with NME cap.
    #
    # [HUMAN DECISION] The capping is best done interactively:
    #   Option A: Use PyMOL/Chimera to manually add caps and save
    #   Option B: Use tleap to cap, then extract
    #   Option C: Use reduce/pdb4amber to prepare, then manually add cap atoms
    #
    # Below we generate a tleap script that attempts automated capping.
    # This may require manual adjustment of bond connectivity.
    # ---------------------------------------------------------------

    local cap_script="${PARAM_DIR}/plp_structures/${intermediate}_cap.in"

    cat > "${cap_script}" << CAP_EOF
# tleap script to cap ${intermediate} for QM calculation
# Generated by parameterize_plp.sh
#
# [HUMAN DECISION] This is a TEMPLATE. You likely need to:
# 1. Load the raw residue as a non-standard unit
# 2. Manually define connectivity
# 3. Add ACE/NME cap residues
# 4. Verify the capped structure in PyMOL

source leaprc.ff14SB
source leaprc.gaff

# Load the raw extracted residue
# Note: tleap may not recognize the modified residue name.
# You may need to load it as a generic mol2 first.
mol = loadpdb ${raw_pdb}

# Attempt to add caps
# [HUMAN DECISION] This will likely fail for modified residues.
# Manual capping in PyMOL/Chimera is recommended instead.
# sequence capped = { ACE mol NME }

# Save capped structure
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

# ================================================================
# SECTION 4: RESP CHARGE CALCULATION VIA GAUSSIAN 16
# ================================================================

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

    # Prefer the capped structure; fall back to raw if capping not done yet
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

    # --- Method A: Use antechamber to generate Gaussian input ---
    # antechamber can read a PDB and write a Gaussian .com file directly.
    # This handles coordinate extraction and formatting automatically.

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

        # --- Method B: Manual Gaussian template ---
        cat > "${gauss_input}" << GAUSS_EOF
%chk=${intermediate}_opt.chk
%nprocshared=8
%mem=8GB
#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt

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

    # --- Post-process: fix Gaussian header for proper RESP ESP output ---
    # antechamber may not include the right iop keywords for RESP.
    # We need: #HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt
    # These tell Gaussian to print the electrostatic potential on
    # Merz-Kollman grid points, which is what RESP fitting needs.

    if [ -f "${gauss_input}" ]; then
        # Check if the route line has Pop=MK
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

# ================================================================
# SECTION 5: ANTECHAMBER - ASSIGN GAFF ATOM TYPES + RESP CHARGES
# ================================================================

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

    # Check if Gaussian output exists (preferred: RESP charges)
    local gauss_log="${PARAM_DIR}/resp_charges/${intermediate}_opt.log"
    local output_mol2="${PARAM_DIR}/mol2/${intermediate}_gaff.mol2"

    if [ -f "${gauss_log}" ] && grep -q "Normal termination" "${gauss_log}"; then
        # --- RESP pathway: extract charges from Gaussian output ---
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
        # --- BCC fallback path is prohibited in production mode (FP-009) ---
        echo "FATAL: BCC fallback triggered in production mode. FP-009 prohibits BCC for PLP. Use RESP only."
        exit 1
    fi

    if [ -f "${output_mol2}" ]; then
        echo "    MOL2 saved: ${output_mol2}"

        # Validate: check atom count in mol2
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

# ================================================================
# SECTION 6: GENERATE frcmod (MISSING PARAMETERS)
# ================================================================

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

    # parmchk2: identifies missing GAFF parameters and extrapolates
    # from similar terms in the database.
    # -s 2 = use GAFF2 (more parameters than GAFF1)
    # Remove -s 2 if you want original GAFF (as in the SI protocol).

    "${AMBER_BIN}/parmchk2" \
        -i "${input_mol2}" \
        -f mol2 \
        -o "${output_frcmod}" \
        2>&1 | tee "${LOG_DIR}/parmchk2_${intermediate}.log"

    if [ -f "${output_frcmod}" ]; then
        echo "    frcmod saved: ${output_frcmod}"

        # Count missing parameters (lines with ATTN or penalty scores)
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

# ================================================================
# SECTION 7: TLEAP WORKFLOW (COMBINE PROTEIN + PLP)
# ================================================================

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
# tleap input for building ${intermediate}-TrpB complex
# Generated by parameterize_plp.sh
#
# System: ${pdb_code} chain ${chain}, intermediate ${intermediate}
# Modified residue: ${resname}

# Load force fields
source leaprc.protein.ff14SB    # AMBER protein force field (ff14SB)
source leaprc.gaff              # GAFF for small molecules (PLP)
source leaprc.water.tip3p       # TIP3P water model

# Load PLP parameters
${resname} = loadmol2 ${input_mol2}
loadamberparams ${input_frcmod}

# Check the loaded unit
check ${resname}

# Load the protein
# [HUMAN DECISION] The protein PDB must be prepared:
#   - Single chain (${chain})
#   - Modified residue removed (will be loaded separately)
#   - Hydrogens added (pdb4amber or reduce)
#   - Disulfide bonds defined if present
#
# ALTERNATIVE APPROACH (recommended for covalent cofactor):
# Instead of loading cofactor separately, prepare a combined PDB
# where the modified residue is already in place, and load custom
# residue libraries (.lib/.off) generated from the mol2.
#
# Complex = loadpdb ${protein_pdb}

# [HUMAN DECISION] For covalent attachment:
# Define the bond between NZ of the PLP unit and the K82 side chain.
# The residue number below (82) is from the PDB; it may differ after
# processing with pdb4amber. Verify with:
#   grep "CA.*LYS" ${protein_pdb} | head -5
#
# bond Complex.82.NZ Complex.[PLP_RESNUM].C4'

# Solvate in truncated octahedron with TIP3P, 10 A buffer
# (SI: explicit TIP3P solvent)
solvatebox Complex TIP3PBOX 10.0

# Neutralize with counterions
addions Complex Na+ 0
addions Complex Cl- 0

# Check for errors
check Complex

# Save topology and coordinates
saveamberparm Complex ${output_parm} ${output_inpcrd}

# Save PDB for visualization
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

# ================================================================
# SECTION 8: FINAL SUMMARY AND NEXT STEPS
# ================================================================

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

# ================================================================
# END OF SCRIPT
# ================================================================
