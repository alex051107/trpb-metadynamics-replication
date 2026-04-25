"""Toy well-tempered MetaD on alanine dipeptide using openmm-plumed plugin.

Verifies the full OpenMM→PLUMED hook path needed for the TrpB campaign:
- PlumedForce accepts a PLUMED script identical in syntax to plumed.dat
- HILLS/COLVAR are written by PLUMED
- Simulation runs 50 ps without NaN or force mismatch

CVs: phi, psi dihedrals (Ramachandran).
"""

import os, sys, time
from openmm import LangevinMiddleIntegrator, Platform, unit, app
from openmm.app import (
    ForceField, Simulation, DCDReporter, StateDataReporter, PDBFile, HBonds,
)
from openmm.unit import kelvin, picosecond, femtosecond, nanometer
from openmmplumed import PlumedForce

TEMP = 350 * kelvin
FRICTION = 1.0 / picosecond
DT = 2.0 * femtosecond
NSTEPS = 25_000  # 50 ps

ff = ForceField("amber14/protein.ff14SB.xml")
ala = PDBFile("alanine_dipeptide.pdb")  # vacuum

# Resolve PLUMED atom indices (1-based) dynamically from topology.
# phi = C(ACE) - N(ALA) - CA(ALA) - C(ALA)
# psi = N(ALA) - CA(ALA) - C(ALA) - N(NME)
def find(resname, atomname):
    for i, a in enumerate(ala.topology.atoms()):
        if a.residue.name == resname and a.name == atomname:
            return i + 1
    raise KeyError(f"{resname}:{atomname} not in topology")

c_ace, n_ala, ca_ala, c_ala, n_nme = (
    find("ACE", "C"), find("ALA", "N"), find("ALA", "CA"),
    find("ALA", "C"), find("NME", "N"),
)
print(f"phi atoms (1-based) = {c_ace},{n_ala},{ca_ala},{c_ala}")
print(f"psi atoms (1-based) = {n_ala},{ca_ala},{c_ala},{n_nme}")

PLUMED_SCRIPT = f"""
# Toy well-tempered MetaD on alanine dipeptide.
# Two dihedrals as CVs, Gaussians every 1 ps, bias factor 10 at 350 K.
phi: TORSION ATOMS={c_ace},{n_ala},{ca_ala},{c_ala}
psi: TORSION ATOMS={n_ala},{ca_ala},{c_ala},{n_nme}
METAD ...
    ARG=phi,psi
    PACE=500
    HEIGHT=1.2
    SIGMA=0.35,0.35
    BIASFACTOR=10
    TEMP=350
    FILE=HILLS
    LABEL=metad
... METAD
PRINT ARG=phi,psi,metad.bias FILE=COLVAR STRIDE=500
"""

system = ff.createSystem(
    ala.topology,
    nonbondedMethod=app.NoCutoff,
    constraints=HBonds,
)
system.addForce(PlumedForce(PLUMED_SCRIPT))

integrator = LangevinMiddleIntegrator(TEMP, FRICTION, DT)
platform_name = os.environ.get("OPENMM_PLATFORM", "CUDA")
platform = Platform.getPlatformByName(platform_name)
props = {"Precision": "mixed"} if platform_name == "CUDA" else {}
sim = Simulation(ala.topology, system, integrator, platform, props)
sim.context.setPositions(ala.positions)

print(f"atoms = {system.getNumParticles()}")
print(f"platform = {sim.context.getPlatform().getName()}")
print(f"forces = {[f.__class__.__name__ for f in system.getForces()]}")

sim.minimizeEnergy(maxIterations=200)
sim.context.setVelocitiesToTemperature(TEMP)

sim.reporters.append(DCDReporter("toy_metad.dcd", 500))
sim.reporters.append(StateDataReporter(
    sys.stdout, 500, step=True, potentialEnergy=True,
    temperature=True, speed=True, totalSteps=NSTEPS,
))

t0 = time.time()
sim.step(NSTEPS)
wall = time.time() - t0
ns_simulated = NSTEPS * DT.value_in_unit(unit.nanosecond)
print(f"WALL = {wall:.1f} s for {ns_simulated*1000:.1f} ps")
print(f"NS_PER_DAY = {ns_simulated / (wall / 86400):.1f}")

assert os.path.exists("HILLS"), "PLUMED did not emit HILLS"
assert os.path.exists("COLVAR"), "PLUMED did not emit COLVAR"
with open("HILLS") as f:
    nlines = sum(1 for _ in f if not _.startswith("#"))
print(f"HILLS rows = {nlines}")

print("TOY_METAD_OK")
