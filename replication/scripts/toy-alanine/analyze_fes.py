#!/usr/bin/env python3

"""
Alanine Dipeptide MetaDynamics Analysis
=====================================

Converts PLUMED HILLS file to free energy surface (FES) and generates 2D plot.

Steps:
1. Call 'plumed sum_hills' to compute FES from HILLS
2. Load the resulting FES grid (phi vs psi)
3. Plot 2D landscape with contours
4. Save as PNG and print statistics

Author: Claude Code
Date: 2026-03-28
"""

import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap

# ============================================================================
# Configuration
# ============================================================================

HILLS_FILE = "HILLS"
COLVAR_FILE = "COLVAR"
FES_OUTPUT = "fes.dat"
PNG_OUTPUT = "fes_alanine.png"

# ============================================================================
# Step 1: Convert HILLS to FES using plumed sum_hills
# ============================================================================

def compute_fes():
    """
    Run 'plumed sum_hills' to convert HILLS file to free energy surface.
    Output: fes.dat (2D grid of phi, psi, free energy)
    """
    print("=" * 60)
    print("Computing Free Energy Surface from HILLS")
    print("=" * 60)

    if not os.path.exists(HILLS_FILE):
        print(f"ERROR: {HILLS_FILE} not found in current directory!")
        print("Did you run 'gmx mdrun -plumed plumed_metad.dat'?")
        sys.exit(1)

    print(f"[1/3] Running: plumed sum_hills --hills {HILLS_FILE}")

    # Construct plumed command
    cmd = [
        "plumed",
        "sum_hills",
        "--hills", HILLS_FILE,
        "--outfile", FES_OUTPUT,
        "--mintozero"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"ERROR: plumed sum_hills failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            sys.exit(1)
        print("✓ FES computed successfully")
        print(f"✓ Output: {FES_OUTPUT}")
    except FileNotFoundError:
        print("ERROR: 'plumed' command not found!")
        print("Make sure to activate conda: conda activate trpb-md")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: plumed sum_hills timed out (>60 sec)")
        sys.exit(1)

    print()

# ============================================================================
# Step 2: Load and parse FES grid
# ============================================================================

def load_fes():
    """
    Load FES data from fes.dat (produced by plumed sum_hills).

    Format (typical):
      phi     psi     fes
      -180.0  -180.0  15.4
      -180.0  -175.0  14.2
      ...

    Returns:
      phi_vals: 1D array of phi angles (unique, sorted)
      psi_vals: 1D array of psi angles (unique, sorted)
      fes_grid: 2D array of free energies (phi × psi)
    """
    print("[2/3] Loading FES data from", FES_OUTPUT)

    if not os.path.exists(FES_OUTPUT):
        print(f"ERROR: {FES_OUTPUT} not found!")
        print("Make sure plumed sum_hills succeeded.")
        sys.exit(1)

    # Read file, skip comments and empty lines
    phi_set = set()
    psi_set = set()
    data_points = []

    with open(FES_OUTPUT, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            try:
                phi = float(parts[0])
                psi = float(parts[1])
                fes = float(parts[2])
                phi_set.add(phi)
                psi_set.add(psi)
                data_points.append((phi, psi, fes))
            except ValueError:
                continue

    if not data_points:
        print("ERROR: No valid data found in", FES_OUTPUT)
        sys.exit(1)

    # Sort and create grid
    phi_vals = np.array(sorted(phi_set))
    psi_vals = np.array(sorted(psi_set))

    # Create 2D grid (phi on rows, psi on columns)
    fes_grid = np.full((len(phi_vals), len(psi_vals)), np.nan)

    for phi, psi, fes in data_points:
        i = np.where(phi_vals == phi)[0][0]
        j = np.where(psi_vals == psi)[0][0]
        fes_grid[i, j] = fes

    print(f"✓ Loaded {len(data_points)} grid points")
    print(f"  Phi range: [{phi_vals.min():.1f}, {phi_vals.max():.1f}]°")
    print(f"  Psi range: [{psi_vals.min():.1f}, {psi_vals.max():.1f}]°")
    print(f"  Grid size: {len(phi_vals)} × {len(psi_vals)}")
    print()

    return phi_vals, psi_vals, fes_grid

# ============================================================================
# Step 3: Plot 2D Free Energy Landscape
# ============================================================================

def plot_fes(phi_vals, psi_vals, fes_grid):
    """
    Create 2D contour plot of phi vs psi free energy landscape.

    Features:
    - Contour lines for energy levels (0, 2, 5, 10, 20 kJ/mol)
    - Color gradient from low (blue) to high (red) energy
    - Marked minima regions (Ramachandran plot)
    """
    print("[3/3] Generating 2D FEL plot...")

    fig, ax = plt.subplots(figsize=(10, 9), dpi=150)

    # Create meshgrid for contour plot
    PHI, PSI = np.meshgrid(psi_vals, phi_vals)

    # Plot filled contour (color gradient)
    levels = np.linspace(np.nanmin(fes_grid), np.nanmax(fes_grid), 50)
    contourf = ax.contourf(PHI, PSI, fes_grid, levels=levels, cmap='RdYlBu_r', alpha=0.8)

    # Overlay contour lines at specific energies
    contour_levels = [0, 2, 5, 10, 20]
    contour = ax.contour(PHI, PSI, fes_grid, levels=contour_levels,
                         colors='black', alpha=0.4, linewidths=0.8)

    # Label contours
    ax.clabel(contour, inline=True, fontsize=8, fmt='%1.0f')

    # Add colorbar
    cbar = plt.colorbar(contourf, ax=ax, label='Free Energy (kJ/mol)')

    # Mark typical alanine dipeptide regions
    # Alpha-helix region: phi ≈ -60°, psi ≈ -45°
    # Beta-sheet region: phi ≈ -120°, psi ≈ +120°
    ax.plot(-60, -45, 'r*', markersize=15, label='α-helix minimum', zorder=5)
    ax.plot(-120, 120, 'g*', markersize=15, label='β-sheet minimum', zorder=5)

    # Labels and title
    ax.set_xlabel('Psi (ψ) angle [degrees]', fontsize=12, fontweight='bold')
    ax.set_ylabel('Phi (ϕ) angle [degrees]', fontsize=12, fontweight='bold')
    ax.set_title('Alanine Dipeptide Free Energy Landscape\n(Well-Tempered MetaDynamics, 10 ns)',
                 fontsize=14, fontweight='bold')

    # Set limits (standard Ramachandran plot range)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-180, 180)

    # Grid and legend
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=10)

    plt.tight_layout()

    # Save figure
    plt.savefig(PNG_OUTPUT, dpi=150, bbox_inches='tight')
    print(f"✓ Plot saved: {PNG_OUTPUT}")
    print()

# ============================================================================
# Step 4: Print Statistics
# ============================================================================

def print_statistics(phi_vals, psi_vals, fes_grid):
    """Print free energy statistics and minima locations."""
    print("=" * 60)
    print("Free Energy Statistics")
    print("=" * 60)

    # Find min and max energies
    fes_min = np.nanmin(fes_grid)
    fes_max = np.nanmax(fes_grid)
    fes_mean = np.nanmean(fes_grid)

    print(f"Minimum FE:  {fes_min:8.2f} kJ/mol")
    print(f"Maximum FE:  {fes_max:8.2f} kJ/mol")
    print(f"Mean FE:     {fes_mean:8.2f} kJ/mol")
    print(f"Range (ΔG):  {fes_max - fes_min:8.2f} kJ/mol")
    print()

    # Find global minimum
    min_idx = np.nanargmin(fes_grid)
    min_i, min_j = np.unravel_index(min_idx, fes_grid.shape)
    phi_min = phi_vals[min_i]
    psi_min = psi_vals[min_j]

    print(f"Global minimum at:")
    print(f"  φ = {phi_min:7.1f}°")
    print(f"  ψ = {psi_min:7.1f}°")
    print(f"  FE = {fes_grid[min_i, min_j]:7.2f} kJ/mol")
    print()

    # Expected regions
    print("Expected minima (Ramachandran plot):")
    print("  α-helix:  φ ≈ -60°,  ψ ≈ -45°  (most stable)")
    print("  β-sheet:  φ ≈ -120°, ψ ≈ +120° (secondary)")
    print()

    # Energy at expected minima
    def find_nearest_energy(phi_target, psi_target):
        i = np.argmin(np.abs(phi_vals - phi_target))
        j = np.argmin(np.abs(psi_vals - psi_target))
        return phi_vals[i], psi_vals[j], fes_grid[i, j]

    phi_a, psi_a, fe_a = find_nearest_energy(-60, -45)
    phi_b, psi_b, fe_b = find_nearest_energy(-120, 120)

    print(f"α-region energy: {fe_a:7.2f} kJ/mol at φ={phi_a:.0f}°, ψ={psi_a:.0f}°")
    print(f"β-region energy: {fe_b:7.2f} kJ/mol at φ={phi_b:.0f}°, ψ={psi_b:.0f}°")
    print(f"ΔG(α→β):        {fe_b - fe_a:7.2f} kJ/mol")
    print()

    # Estimate time to converge (from COLVAR)
    if os.path.exists(COLVAR_FILE):
        try:
            colvar_data = np.loadtxt(COLVAR_FILE, comments='#')
            if len(colvar_data) > 0:
                n_steps = len(colvar_data)
                # Assuming 2 ps per step (dt=0.002, STRIDE=100 in PRINT)
                time_ns = n_steps * 2 / 1000
                print(f"Sampling time (from COLVAR): {time_ns:.1f} ns")
                print(f"Number of COLVAR entries: {n_steps}")
        except:
            pass

    print()

# ============================================================================
# Main
# ============================================================================

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " Alanine Dipeptide MetaDynamics Analysis ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Step 1: Compute FES
    compute_fes()

    # Step 2: Load FES data
    phi_vals, psi_vals, fes_grid = load_fes()

    # Step 3: Plot FEL
    plot_fes(phi_vals, psi_vals, fes_grid)

    # Step 4: Statistics
    print_statistics(phi_vals, psi_vals, fes_grid)

    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - {FES_OUTPUT}: Raw free energy surface grid")
    print(f"  - {PNG_OUTPUT}: 2D contour plot (phi vs psi)")
    print()

if __name__ == "__main__":
    main()
