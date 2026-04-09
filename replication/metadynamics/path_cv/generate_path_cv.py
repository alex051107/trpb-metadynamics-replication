#!/usr/bin/env python3
"""
Generate 15-frame reference path for TrpB COMM domain O→C transition.

This script implements the path collective variables (Path CV) methodology from
Osuna et al. JACS 2019 (ja9b03646). It performs:
1. Download/load Open (1WDW) and Closed (3CEP) PDB structures
2. Sequence alignment of TrpB subunits (P. furiosus vs S. typhimurium)
3. Structural alignment of COMM domain (residues 97-184) + base region (282-305)
4. Linear interpolation to generate 15 frames
5. Frame validation via MSD calculations
6. λ parameter calculation (2.3 / MSD ≈ 0.029)
7. Output: individual PDB files + PLUMED PATH format (multi-model PDB)

Requirements:
  - MDAnalysis >= 2.5.0  (structural analysis, alignment)
  - BioPython >= 1.83   (sequence alignment, PDB I/O)
  - numpy
  - requests (for downloading PDBs)

Author: Zhenpeng Liu (liualex@ad.unc.edu)
Project: TrpB MetaDynamics Replication (Anima Lab, Caltech)
"""

import os
import sys
import argparse
import warnings
import numpy as np
from pathlib import Path
from typing import Tuple, List
import requests
from io import StringIO

# Suppress MDAnalysis warnings
warnings.filterwarnings('ignore', category=UserWarning)

try:
    import MDAnalysis as mda
except ImportError:
    mda = None

try:
    from Bio import PDB, pairwise2
except ImportError:
    PDB = None
    pairwise2 = None


# ============================================================================
# Configuration
# ============================================================================

# PDB codes and source structures
OPEN_PDB = "1WDW"      # P. furiosus (Pf), Open state
CLOSED_PDB = "3CEP"    # S. typhimurium (St), Closed state

# COMM domain residues (TrpB numbering)
COMM_RESIDUES = list(range(97, 185))     # 97-184 inclusive
BASE_RESIDUES = list(range(282, 306))    # 282-305 inclusive
ATOMS_OF_INTEREST = COMM_RESIDUES + BASE_RESIDUES

# Number of frames for interpolation
NUM_FRAMES = 15

# Paper-reported values for validation
# JACS 2019 quotes "mean square displacement between successive frames, 80"
# for λ = 2.3 / MSD ≈ 0.029. For this project we report both:
#   1. PLUMED-normalized per-atom MSD (RMSD ... SQUARED convention), in Å^2
#   2. JACS-style total squared displacement across all selected atoms, in Å^2
PAPER_MSD = 80.0
LAMBDA_SCALE = 2.3        # λ = LAMBDA_SCALE / MSD


# ============================================================================
# Helper Functions
# ============================================================================

def download_pdb(pdb_code: str, output_path: str) -> bool:
    """Download PDB file from RCSB PDB server."""
    url = f"https://files.rcsb.org/download/{pdb_code}.pdb"
    try:
        print(f"  Downloading {pdb_code} from RCSB...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(output_path, 'w') as f:
            f.write(response.text)
        print(f"  ✓ Saved to {output_path}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to download {pdb_code}: {e}")
        return False


def load_or_download_pdb(pdb_code: str, local_dir: str) -> str:
    """
    Load PDB from disk or download if not found.

    Returns:
        str: Path to PDB file
    """
    local_path = os.path.join(local_dir, f"{pdb_code}.pdb")

    if os.path.exists(local_path):
        print(f"Loading {pdb_code} from {local_path}")
        return local_path

    print(f"{pdb_code}.pdb not found locally. Attempting download...")
    os.makedirs(local_dir, exist_ok=True)

    if download_pdb(pdb_code, local_path):
        return local_path
    else:
        raise FileNotFoundError(f"Cannot locate or download {pdb_code}")


def extract_sequence_from_pdb(pdb_path: str, chain: str = 'B') -> Tuple[str, dict]:
    """
    Extract amino acid sequence from PDB file.

    Returns:
        Tuple of (sequence, residue_map)
        where residue_map = {resid: aa_code}
    """
    if PDB is None:
        print("ERROR: BioPython not installed. Install via: pip install biopython")
        sys.exit(1)

    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure('pdb', pdb_path)

    # Get first model, specified chain
    model = structure[0]
    if chain not in model:
        print(f"Chain {chain} not found. Available chains: {list(model.keys())}")
        chain = list(model.keys())[0]
        print(f"Using chain {chain} instead")

    chain_obj = model[chain]

    # Build sequence and residue map
    sequence = []
    residue_map = {}

    for residue in chain_obj:
        if PDB.is_aa(residue):
            resid = residue.get_id()[1]
            try:
                aa_code = PDB.Polypeptide.three_to_one(residue.get_resname())
            except (AttributeError, KeyError):
                from Bio.Data.IUPACData import protein_letters_3to1
                aa_code = protein_letters_3to1.get(residue.get_resname().capitalize(), "X")
            sequence.append(aa_code)
            residue_map[resid] = aa_code

    return ''.join(sequence), residue_map


def align_sequences(seq_open: str, seq_closed: str) -> dict:
    """
    Align two sequences and return mapping.
    Uses pairwise2 alignment from BioPython.

    Returns:
        dict with alignment info
    """
    if pairwise2 is None:
        print("ERROR: BioPython not installed. Install via: pip install biopython")
        sys.exit(1)

    alignments = pairwise2.align.globalxx(seq_open, seq_closed)

    if not alignments:
        print("WARNING: No sequence alignment found. Using 1:1 residue mapping.")
        return {"score": 0}

    best = alignments[0]
    print(f"Sequence alignment score: {best.score}")
    print(f"  Open (1WDW):  {best.seqA[:50]}...")
    print(f"  Closed (3CEP): {best.seqB[:50]}...")

    return {
        "score": best.score,
        "seqA": best.seqA,
        "seqB": best.seqB,
        "start_A": best.start,
        "start_B": best.start,
    }


def load_universe(pdb_path: str) -> "mda.Universe":
    """Load PDB into MDAnalysis Universe."""
    if mda is None:
        print("ERROR: MDAnalysis not installed. Install via: pip install MDAnalysis")
        sys.exit(1)
    return mda.Universe(pdb_path)


def extract_ca_coordinates(universe: "mda.Universe", residues: List[int]) -> np.ndarray:
    """
    Extract Cα coordinates for specified residues.

    Args:
        universe: MDAnalysis Universe
        residues: List of residue numbers

    Returns:
        np.ndarray of shape (N, 3) with Cα coordinates
    """
    # Select Cα atoms in specified residues
    selection_str = f"name CA and (resid {' or resid '.join(map(str, residues))})"
    try:
        atoms = universe.select_atoms(selection_str)
    except:
        # Fallback: try alternative selection
        print(f"  Selection string failed. Trying alternative...")
        atoms = universe.select_atoms("name CA")
        # Filter by residue
        atoms = atoms[np.isin(atoms.resids, residues)]

    if len(atoms) == 0:
        print(f"WARNING: No atoms selected with residues {residues}")
        # Return all Cα atoms
        atoms = universe.select_atoms("name CA")
        print(f"  Using all {len(atoms)} Cα atoms instead")

    coords = atoms.positions.copy()
    return coords


def align_structures(coords_open: np.ndarray, coords_closed: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align closed structure onto open structure using Cα atoms.
    Uses Kabsch algorithm (optimal RMSD alignment).

    Returns:
        Tuple of (aligned_open, aligned_closed)
    """
    # Center both structures
    centroid_open = np.mean(coords_open, axis=0)
    centroid_closed = np.mean(coords_closed, axis=0)

    open_centered = coords_open - centroid_open
    closed_centered = coords_closed - centroid_closed

    # Ensure same number of atoms (truncate if needed)
    n_atoms = min(len(open_centered), len(closed_centered))
    open_centered = open_centered[:n_atoms]
    closed_centered = closed_centered[:n_atoms]

    # Kabsch algorithm: find optimal rotation
    H = open_centered.T @ closed_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    # Ensure proper rotation (det(R) = 1)
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    # Apply rotation to closed structure
    closed_aligned = (R @ closed_centered.T).T

    # Re-center both to origin
    open_aligned = open_centered

    return open_aligned, closed_aligned


def interpolate_frames(coords_open: np.ndarray, coords_closed: np.ndarray,
                       num_frames: int = 15) -> List[np.ndarray]:
    """
    Generate linear interpolation between open and closed states.

    Returns:
        List of coordinate arrays, indexed 0 to num_frames-1
    """
    frames = []

    for i in range(num_frames):
        lambda_param = i / (num_frames - 1)  # 0 → 1
        frame = (1 - lambda_param) * coords_open + lambda_param * coords_closed
        frames.append(frame)

    return frames


def calculate_msd(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """
    Calculate PLUMED-normalized mean squared displacement (Å²).

    This matches the convention used by PLUMED's RMSD action with the
    SQUARED flag: (1/N) * sum_i |r_i - r_i_ref|^2 for equal weights.
    """
    diff = coords1 - coords2
    result = float(np.mean(np.sum(diff**2, axis=1)))
    assert result > 0, f"MSD must be positive, got {result}"
    assert result < 1000, f"MSD={result} Å² is unreasonably large — check units"
    return result


def calculate_total_squared_displacement(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """
    Calculate unnormalized total squared displacement (Å²) across all atoms.

    This is the quantity whose magnitude is closest to the JACS 2019
    statement that the "mean square displacement between successive frames"
    is approximately 80.
    """
    diff = coords1 - coords2
    result = float(np.sum(np.sum(diff**2, axis=1)))
    assert result > 0, f"Total SD must be positive, got {result}"
    assert 10 < result < 500, f"Total SD={result} Å² outside expected range 10-500 for protein domain path — check atom selection"
    return result


def calculate_rmsd(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """Calculate RMSD (Å) from the PLUMED-normalized MSD."""
    return float(np.sqrt(calculate_msd(coords1, coords2)))


def calculate_lambda(msd_value: float, convention: str = "plumed") -> float:
    """Calculate λ parameter: λ = LAMBDA_SCALE / MSD.

    IMPORTANT (FP-022, 2026-04-08):
        The default convention is now 'plumed' (per-atom MSD), NOT 'total_sd'.
        PLUMED's RMSD action outputs per-atom-normalized values:
            RMSD = sqrt((1/N_atoms) × Σ |r_i - r_i^ref|²)
        When fed into FUNCPATHMSD (directly or with SQUARED), d_i is either
        per-atom RMSD (nm) or per-atom MSD (nm²). The λ parameter must be
        computed on the same convention.

        Using "total_sd" (sum over atoms, NOT divided by N_atoms) gives a
        λ value that is N_atoms = 112 times too small for FUNCPATHMSD. This
        causes the path CV to collapse: adjacent-frame kernel weight becomes
        exp(-0.26) ≈ 0.77 instead of the target exp(-2.3) ≈ 0.10, so the
        CV cannot distinguish frames and all configurations map to s ≈ 8.

        See: replication/validations/2026-04-08_path_cv_lambda_bug.md

    Args:
        msd_value: MSD in Å² (per-atom if convention="plumed",
                   total sum if convention="total_sd")
        convention: "plumed" (DEFAULT, correct for FUNCPATHMSD)
                    or "total_sd" (legacy, kept only for comparison with
                    JACS 2019 SI's quoted "80 Å²")
    """
    result = LAMBDA_SCALE / msd_value
    if convention == "plumed":
        assert 0.1 < result < 100, (
            f"lambda(plumed)={result} Å⁻² outside expected range 0.1-100. "
            f"Expected ~3.8 Å⁻² for a linear O→C path in PfTrpB. "
            f"Did you accidentally pass total_sd instead of per-atom MSD?"
        )
    elif convention == "total_sd":
        assert 0.001 < result < 1.0, (
            f"lambda(total_sd)={result} outside range 0.001-1.0. "
            f"This convention is NOT correct for FUNCPATHMSD (see FP-022)."
        )
    else:
        raise ValueError(f"unknown convention: {convention}")
    return result


def write_pdb_frame(universe: "mda.Universe", coords: np.ndarray,
                   output_path: str, residues: List[int]) -> None:
    """
    Write a single frame to PDB file using original topology.
    """
    # Create a copy of the universe with new coordinates
    temp_universe = universe.copy()

    # Update coordinates for Cα atoms in our residues
    selection_str = f"name CA and (resid {' or resid '.join(map(str, residues))})"
    try:
        atoms = temp_universe.select_atoms(selection_str)
    except:
        atoms = temp_universe.select_atoms("name CA")
        atoms = atoms[np.isin(atoms.resids, residues)]

    # Update only the selected atoms
    atoms.positions[:] = coords

    # Write PDB
    temp_universe.atoms.write(output_path)


def write_plumed_path_file(universe: "mda.Universe", frames: List[np.ndarray],
                          output_path: str, residues: List[int]) -> None:
    """
    Write all frames in PLUMED PATH format (multi-model PDB file).
    Each MODEL...ENDMDL block represents one frame.

    FP-023 (2026-04-09): File MUST end with the last ENDMDL, not a trailing
    bare 'END' line. PLUMED's PATHMSD treats a trailing 'END' as the start
    of an empty (N+1)-th frame and aborts with
    "number of atoms in a frame should be more than zero". This function
    writes only MODEL/ENDMDL blocks and explicitly does NOT emit a trailing
    END marker.
    """
    with open(output_path, 'w') as f:
        for frame_idx, coords in enumerate(frames):
            f.write(f"MODEL        {frame_idx + 1:4d}\n")

            # Write all atoms with updated Cα coordinates
            atom_idx = 1
            selection_str = f"name CA and (resid {' or resid '.join(map(str, residues))})"
            try:
                ca_atoms = universe.select_atoms(selection_str)
            except:
                ca_atoms = universe.select_atoms("name CA")
                ca_atoms = ca_atoms[np.isin(ca_atoms.resids, residues)]

            # For each atom in the universe, write it with updated coords if in selection
            for atom in universe.atoms:
                resid = atom.resid
                if resid in residues:
                    # Find this atom in the ca_atoms selection
                    ca_idx = np.where((ca_atoms.resids == resid) &
                                     (ca_atoms.names == atom.name))[0]
                    if len(ca_idx) > 0:
                        pos = coords[ca_idx[0]]
                    else:
                        pos = atom.position
                else:
                    pos = atom.position

                # Write ATOM record
                line = (f"ATOM  {atom_idx:5d} {atom.name:4s} {atom.resname:3s} "
                       f"{atom.segid:1s}{atom.resid:4d}    "
                       f"{pos[0]:8.3f}{pos[1]:8.3f}{pos[2]:8.3f}"
                       f"  1.00  0.00           {atom.element:2s}\n")
                f.write(line)
                atom_idx += 1

            f.write("ENDMDL\n")

    # FP-023 safety check: ensure file does not end with a trailing bare END
    with open(output_path, 'r') as f:
        content = f.read()
    lines = content.rstrip("\n").split("\n")
    while lines and lines[-1].strip() == "END":
        lines.pop()
    with open(output_path, 'w') as f:
        f.write("\n".join(lines) + "\n")
    assert lines[-1].strip() == "ENDMDL", (
        f"path file must end with ENDMDL, got: {lines[-1]!r} (FP-023)"
    )


def parse_existing_path_pdb(path_file: str) -> List[np.ndarray]:
    """
    Parse a multi-model PATH PDB file and return a list of coordinate arrays.

    This mode avoids MDAnalysis/BioPython and is used for local summary-only
    validation when the path coordinates are already available.
    """
    frames: List[np.ndarray] = []
    current: List[List[float]] = []

    with open(path_file, 'r') as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.startswith("MODEL"):
                current = []
            elif line.startswith(("ATOM", "HETATM")):
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                current.append([x, y, z])
            elif line.startswith(("END", "ENDMDL")):
                if current:
                    frames.append(np.array(current, dtype=float))
                    current = []

    if current:
        frames.append(np.array(current, dtype=float))

    if not frames:
        raise ValueError(f"No frames parsed from {path_file}")

    n_atoms = len(frames[0])
    for idx, frame in enumerate(frames, start=1):
        if len(frame) != n_atoms:
            raise ValueError(
                f"Inconsistent atom count in {path_file}: frame 1 has {n_atoms} atoms, "
                f"frame {idx} has {len(frame)} atoms"
            )

    return frames


def write_summary_file(
    summary_file: Path,
    open_label: str,
    closed_label: str,
    chain_label: str,
    n_atoms: int,
    n_frames: int,
    rmsd_open_closed: float,
    msd_values: List[float],
    total_sd_values: List[float],
) -> None:
    avg_msd = float(np.mean(msd_values))
    std_msd = float(np.std(msd_values))
    avg_total_sd = float(np.mean(total_sd_values))
    std_total_sd = float(np.std(total_sd_values))
    avg_lambda_plumed = float(np.mean([calculate_lambda(v, "plumed") for v in msd_values]))
    avg_lambda_jacs = float(np.mean([calculate_lambda(v, "total_sd") for v in total_sd_values]))

    with open(summary_file, 'w') as f:
        f.write("Path CV Generation Summary\n")
        f.write("========================\n")
        f.write(f"Open structure: {open_label} chain {chain_label}\n")
        f.write(f"Closed structure: {closed_label} chain {chain_label}\n")
        f.write("COMM domain: residues 97-184\n")
        f.write("Base region: residues 282-305\n")
        f.write(f"Cα atoms used: {n_atoms}\n")
        f.write(f"RMSD (open vs closed): {rmsd_open_closed:.3f} Å\n")
        f.write(f"Number of frames: {n_frames}\n")
        f.write("\nConventions:\n")
        f.write("  PLUMED MSD = per-atom mean squared displacement (Å²)\n")
        f.write("  JACS MSD   = total squared displacement across all selected atoms (Å²)\n")
        f.write("\nMSD Statistics:\n")
        f.write(f"  Mean PLUMED MSD: {avg_msd:.3f} ± {std_msd:.3f} Å²\n")
        f.write(f"  Mean total SD:   {avg_total_sd:.3f} ± {std_total_sd:.3f} Å²\n")
        f.write("\nLambda Estimates:\n")
        f.write(f"  ★ λ (PLUMED convention, USE THIS): {avg_lambda_plumed:.4f} Å⁻² "
                f"= {avg_lambda_plumed * 100:.4f} nm⁻²\n")
        f.write(f"  λ (legacy total-SD, DO NOT USE):    {avg_lambda_jacs:.6f} Å⁻² "
                f"(wrong by factor N_atoms={n_atoms}, see FP-022)\n")
        f.write("\nReference (JACS 2019 SI):\n")
        f.write(f"  Reported MSD: ~{PAPER_MSD:.0f} Å² (interpreted as total SD)\n")
        f.write(f"  Our total SD: {avg_total_sd:.3f} Å² "
                f"(ratio {avg_total_sd / PAPER_MSD:.2f}x)\n")
        f.write("\nCRITICAL (FP-022, 2026-04-08):\n")
        f.write("  Always use the PLUMED convention λ (per-atom MSD) in plumed.dat.\n")
        f.write("  Always write 'RMSD ... TYPE=OPTIMAL SQUARED' in plumed.dat so the\n")
        f.write("  inputs to FUNCPATHMSD are per-atom MSD (nm² under GROMACS units).\n")
        f.write("  Using the legacy total-SD λ = 2.3/80 ≈ 0.029 Å⁻² gives a value 112×\n")
        f.write("  smaller than needed, collapses the path CV, and causes false PC\n")
        f.write("  confinement. See replication/validations/2026-04-08_path_cv_lambda_bug.md.\n")
        f.write("\nFrame-by-frame metrics:\n")
        for i, (msd, total_sd) in enumerate(zip(msd_values, total_sd_values), start=1):
            f.write(
                f"  {i:2d} → {i+1:2d}: "
                f"per-atom MSD = {msd:.4f} Å² ; "
                f"total SD = {total_sd:.3f} Å² ; "
                f"λ(plumed) = {calculate_lambda(msd, 'plumed'):.4f} Å⁻²\n"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Generate 15-frame reference path for TrpB O→C transition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use PDBs from current directory
  python generate_path_cv.py

  # Use PDBs from specific directory
  python generate_path_cv.py --pdb-dir /path/to/structures

  # Specify output directory
  python generate_path_cv.py --output-dir /path/to/output
        """
    )
    parser.add_argument("--pdb-dir", default="./",
                       help="Directory containing PDB files (default: ./)")
    parser.add_argument("--output-dir", default="./path_frames",
                       help="Output directory for frames (default: ./path_frames)")
    parser.add_argument("--chain", default="B",
                       help="TrpB subunit chain ID (default: B)")
    parser.add_argument("--num-frames", type=int, default=NUM_FRAMES,
                       help=f"Number of frames (default: {NUM_FRAMES})")
    parser.add_argument("--summary-only", action="store_true",
                       help="Recompute summary.txt from an existing path.pdb without rewriting coordinates")
    parser.add_argument("--path-file", default=None,
                       help="Existing multi-model path.pdb to analyze in --summary-only mode")

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("TrpB Path Collective Variables Generator")
    print("=" * 70)
    print(f"Open (O) structure:    {OPEN_PDB}  (P. furiosus)")
    print(f"Closed (C) structure:  {CLOSED_PDB}  (S. typhimurium)")
    print(f"COMM domain residues:  {COMM_RESIDUES[0]}-{COMM_RESIDUES[-1]}")
    print(f"Base region residues:  {BASE_RESIDUES[0]}-{BASE_RESIDUES[-1]}")
    print(f"Total atoms of interest: {len(ATOMS_OF_INTEREST)}")
    print(f"Number of frames:      {args.num_frames}")
    print(f"Output directory:      {output_dir}")
    print("=" * 70)

    if args.summary_only:
        path_file = args.path_file or str(output_dir / "path.pdb")
        print("\n[summary-only] Reading existing path file...")
        print(f"  Path file: {path_file}")
        frames = parse_existing_path_pdb(path_file)
        n_atoms = len(frames[0])
        rmsd = calculate_rmsd(frames[0], frames[-1])

        msd_values = []
        total_sd_values = []
        for i in range(len(frames) - 1):
            msd_values.append(calculate_msd(frames[i], frames[i + 1]))
            total_sd_values.append(calculate_total_squared_displacement(frames[i], frames[i + 1]))

        summary_file = output_dir / "summary.txt"
        write_summary_file(
            summary_file=summary_file,
            open_label=f"structures/{OPEN_PDB}.pdb",
            closed_label=f"structures/{CLOSED_PDB}.pdb",
            chain_label=args.chain,
            n_atoms=n_atoms,
            n_frames=len(frames),
            rmsd_open_closed=rmsd,
            msd_values=msd_values,
            total_sd_values=total_sd_values,
        )

        print("  Summary-only statistics:")
        print(f"    Mean per-atom MSD (PLUMED): {np.mean(msd_values):.4f} Å²")
        print(f"    Mean total SD (legacy):     {np.mean(total_sd_values):.3f} Å²")
        lam_plumed_avg = np.mean([calculate_lambda(v, 'plumed') for v in msd_values])
        print(f"    ★ λ (PLUMED, USE THIS):     {lam_plumed_avg:.4f} Å⁻²"
              f" = {lam_plumed_avg * 100:.4f} nm⁻²")
        print(f"  ✓ Wrote {summary_file}")
        return

    # ========== LOAD STRUCTURES ==========
    print("\n[1/7] Loading PDB structures...")
    try:
        open_pdb_path = load_or_download_pdb(OPEN_PDB, args.pdb_dir)
        closed_pdb_path = load_or_download_pdb(CLOSED_PDB, args.pdb_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # ========== EXTRACT SEQUENCES ==========
    print("\n[2/7] Extracting sequences and aligning...")
    seq_open, resmap_open = extract_sequence_from_pdb(open_pdb_path, args.chain)
    seq_closed, resmap_closed = extract_sequence_from_pdb(closed_pdb_path, args.chain)

    print(f"  Open sequence length:   {len(seq_open)}")
    print(f"  Closed sequence length: {len(seq_closed)}")

    # Align sequences
    align_info = align_sequences(seq_open, seq_closed)

    # ========== LOAD UNIVERSES ==========
    print("\n[3/7] Loading structures into MDAnalysis...")
    universe_open = load_universe(open_pdb_path)
    universe_closed = load_universe(closed_pdb_path)

    print(f"  Open:   {len(universe_open.atoms)} atoms, "
          f"{len(universe_open.residues)} residues")
    print(f"  Closed: {len(universe_closed.atoms)} atoms, "
          f"{len(universe_closed.residues)} residues")

    # ========== EXTRACT COORDINATES ==========
    print("\n[4/7] Extracting Cα coordinates...")
    print(f"  Selecting residues: {ATOMS_OF_INTEREST[0]}-{ATOMS_OF_INTEREST[-1]}")

    coords_open = extract_ca_coordinates(universe_open, ATOMS_OF_INTEREST)
    coords_closed = extract_ca_coordinates(universe_closed, ATOMS_OF_INTEREST)

    print(f"  Open Cα atoms:   {len(coords_open)}")
    print(f"  Closed Cα atoms: {len(coords_closed)}")

    # Ensure same number of atoms
    n_atoms = min(len(coords_open), len(coords_closed))
    coords_open = coords_open[:n_atoms]
    coords_closed = coords_closed[:n_atoms]

    # ========== ALIGN STRUCTURES ==========
    print("\n[5/7] Structural alignment (Kabsch)...")
    coords_open_aligned, coords_closed_aligned = align_structures(coords_open, coords_closed)

    rmsd = calculate_rmsd(coords_open_aligned, coords_closed_aligned)
    print(f"  RMSD between aligned structures: {rmsd:.3f} Å")

    # ========== INTERPOLATE FRAMES ==========
    print(f"\n[6/7] Interpolating {args.num_frames} frames...")
    frames = interpolate_frames(coords_open_aligned, coords_closed_aligned, args.num_frames)

    # ========== CALCULATE MSD VALUES ==========
    print("\n[7/7] Computing MSD between successive frames...")
    print("  Frame#  MSD_mean(Å²)  SD_total(Å²)  λ(total)")
    print("  " + "-" * 55)

    msd_values = []
    total_sd_values = []
    lambda_values = []

    for i in range(len(frames) - 1):
        msd = calculate_msd(frames[i], frames[i + 1])
        total_sd = calculate_total_squared_displacement(frames[i], frames[i + 1])
        # FP-022 fix: compute lambda from per-atom MSD (PLUMED convention),
        # NOT from total SD. The total SD convention is off by N_atoms = 112.
        lam = calculate_lambda(msd, convention="plumed")
        msd_values.append(msd)
        total_sd_values.append(total_sd)
        lambda_values.append(lam)
        print(f"  {i+1:2d}→{i+2:2d}    {msd:10.3f}   {total_sd:11.3f}   {lam:10.4f}")

    # Statistics
    avg_msd = np.mean(msd_values)
    std_msd = np.std(msd_values)
    avg_total_sd = np.mean(total_sd_values)
    std_total_sd = np.std(total_sd_values)
    avg_lambda = np.mean(lambda_values)

    print("  " + "-" * 55)
    print(f"  Mean PLUMED per-atom MSD: {avg_msd:7.3f} ± {std_msd:.3f} Å²")
    print(f"  Mean total SD (legacy):   {avg_total_sd:7.3f} ± {std_total_sd:.3f} Å²")
    print(f"  Mean λ (PLUMED, correct): {avg_lambda:10.4f} Å⁻²")
    print(f"                            = {avg_lambda * 100:10.4f} nm⁻²  ← write THIS into plumed.dat")
    print(f"  Paper MSD (reference):    {PAPER_MSD:7.3f} Å² (interpreted as total SD)")
    print(f"  Total-SD ratio:           {avg_total_sd / PAPER_MSD:.2f}x (1.0 = perfect match)")

    # ========== WRITE OUTPUT ==========
    print(f"\nWriting output files to {output_dir}...")

    # Write individual PDB frames
    frame_files = []
    for i, coords in enumerate(frames):
        frame_num = i + 1
        output_pdb = output_dir / f"frame_{frame_num:02d}.pdb"
        write_pdb_frame(universe_open, coords, str(output_pdb), ATOMS_OF_INTEREST)
        frame_files.append(output_pdb)
        print(f"  ✓ {output_pdb.name}")

    # Write PLUMED PATH format (multi-model PDB)
    plumed_path = output_dir / "path.pdb"
    write_plumed_path_file(universe_open, frames, str(plumed_path), ATOMS_OF_INTEREST)
    print(f"  ✓ {plumed_path.name} (PLUMED PATH format, 15 models)")

    # Write summary file
    summary_file = output_dir / "summary.txt"
    write_summary_file(
        summary_file=summary_file,
        open_label=f"{OPEN_PDB} (P. furiosus)",
        closed_label=f"{CLOSED_PDB} (S. typhimurium)",
        chain_label=args.chain,
        n_atoms=n_atoms,
        n_frames=args.num_frames,
        rmsd_open_closed=rmsd,
        msd_values=msd_values,
        total_sd_values=total_sd_values,
    )
    print(f"  ✓ {summary_file.name}")

    # ========== WRITE READY-TO-USE PLUMED SNIPPET ==========
    # Prevents copy-paste errors like FP-022 (wrong LAMBDA convention).
    lambda_nm2 = avg_lambda * 100.0  # Å⁻² → nm⁻² (GROMACS uses nm)
    snippet_path = output_dir / "plumed_path_cv.dat"
    with open(snippet_path, "w") as f:
        f.write("# Auto-generated PLUMED snippet — DO NOT edit LAMBDA by hand.\n")
        f.write("# Generated by generate_path_cv.py on {}.\n".format(
            __import__("datetime").datetime.now().isoformat(timespec="seconds")
        ))
        f.write("#\n")
        f.write("# LAMBDA was computed from per-atom MSD in the PLUMED convention:\n")
        f.write(f"#   mean per-atom MSD (adjacent frames) = {avg_msd:.4f} Å²\n")
        f.write(f"#   λ = 2.3 / MSD = {avg_lambda:.4f} Å⁻² = {lambda_nm2:.4f} nm⁻²\n")
        f.write("#\n")
        f.write("# CRITICAL: use SQUARED on each RMSD action. Without SQUARED, PLUMED\n")
        f.write("# feeds plain RMSD (nm) into FUNCPATHMSD, and the LAMBDA convention\n")
        f.write("# does not match. See FP-022 in failure-patterns.md.\n")
        f.write("#\n")
        for i in range(args.num_frames):
            f.write(f"r{i+1}: RMSD REFERENCE=frames/frame_{i+1:02d}.pdb TYPE=OPTIMAL SQUARED\n")
        args_list = ",".join(f"r{i+1}" for i in range(args.num_frames))
        f.write(f"path: FUNCPATHMSD ARG={args_list} LAMBDA={lambda_nm2:.4f}\n")
    print(f"  ✓ {snippet_path.name} (ready-to-use PLUMED snippet, includes LAMBDA)")

    # ========== FINAL SUMMARY ==========
    print("\n" + "=" * 70)
    print("SUCCESS: Path CV frames generated!")
    print("=" * 70)
    print(f"\nGenerated files:")
    print(f"  • {args.num_frames} individual PDB frames (frame_01.pdb through frame_{args.num_frames:02d}.pdb)")
    print(f"  • path.pdb (PLUMED PATH format multi-model file)")
    print(f"  • summary.txt (statistics and MSD values)")
    print(f"  • plumed_path_cv.dat (ready-to-use snippet with correct LAMBDA and SQUARED)")
    print(f"\nNext steps:")
    print(f"  1. Copy frames/ and plumed_path_cv.dat to Longleaf production directory")
    print(f"  2. Include plumed_path_cv.dat in your main plumed.dat, OR copy the path")
    print(f"     action line and RMSD actions into your main plumed.dat")
    print(f"  3. Use FUNCPATHMSD (not PATHMSD) — see FP-020 (atom serial issue)")
    print(f"  4. NEVER edit LAMBDA by hand; re-run this script if frames change")
    print(f"  5. Compare per-atom MSD against paper value (~{PAPER_MSD}/112 = {PAPER_MSD/112:.3f} Å²)")
    print("=" * 70)


if __name__ == "__main__":
    main()
