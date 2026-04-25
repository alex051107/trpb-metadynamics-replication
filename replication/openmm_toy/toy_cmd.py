"""Toy cMD on alanine dipeptide (vacuum, AMBER ff14SB, NVT) to verify OpenMM.

Vacuum + NVT keeps this a minimum-surface-area proof-of-concept — no barostat,
no box collapse. The point is to prove:
- openmm loads ff14SB, builds a System from a tleap-written PDB
- LangevinMiddleIntegrator runs 50 ps without NaN
- chosen platform (CPU or CUDA via OPENMM_PLATFORM env) accepts the context

Solvated/production runs happen later via md_setup, not here.
"""

import os, sys, time
from openmm import LangevinMiddleIntegrator, Platform, unit, app
from openmm.app import (
    ForceField, Simulation, DCDReporter, StateDataReporter, PDBFile, HBonds,
)
from openmm.unit import kelvin, picosecond, femtosecond

TEMP = 350 * kelvin
FRICTION = 1.0 / picosecond
DT = 2.0 * femtosecond
NSTEPS = 25_000  # 50 ps
REPORT_EVERY = 500

ff = ForceField("amber14/protein.ff14SB.xml")
ala = PDBFile("alanine_dipeptide.pdb")

system = ff.createSystem(
    ala.topology,
    nonbondedMethod=app.NoCutoff,
    constraints=HBonds,
)

integrator = LangevinMiddleIntegrator(TEMP, FRICTION, DT)
platform_name = os.environ.get("OPENMM_PLATFORM", "CUDA")
platform = Platform.getPlatformByName(platform_name)
props = {"Precision": "mixed"} if platform_name == "CUDA" else {}
sim = Simulation(ala.topology, system, integrator, platform, props)
sim.context.setPositions(ala.positions)

print(f"atoms = {system.getNumParticles()}")
print(f"platform = {sim.context.getPlatform().getName()}")

sim.minimizeEnergy(maxIterations=200)
sim.context.setVelocitiesToTemperature(TEMP)

sim.reporters.append(DCDReporter("toy_cmd.dcd", REPORT_EVERY))
sim.reporters.append(StateDataReporter(
    sys.stdout, REPORT_EVERY,
    step=True, potentialEnergy=True, temperature=True,
    speed=True, remainingTime=True, totalSteps=NSTEPS,
))

t0 = time.time()
sim.step(NSTEPS)
wall = time.time() - t0
ns_simulated = NSTEPS * DT.value_in_unit(unit.nanosecond)
print(f"WALL = {wall:.1f} s for {ns_simulated*1000:.1f} ps")
print(f"NS_PER_DAY = {ns_simulated / (wall / 86400):.1f}")

final = sim.context.getState(getPositions=True)
with open("toy_cmd_final.pdb", "w") as f:
    PDBFile.writeFile(sim.topology, final.getPositions(), f)

print("TOY_CMD_OK")
