#!/usr/bin/env python3
"""Run Aex1 OpenMM cMD from a prebuilt system.xml + initial PDB.

Lab-reference alignment:
- `hengma1001/md_setup` models the lab's preference for explicit protein/ligand
  preparation and a scripted classical-MD handoff rather than notebook-style
  ad hoc runs.

Deviations from `hengma1001/md_setup`:
- Uses OpenMM instead of AMBER `pmemd.cuda` because Phase B explicitly changes
  only the cMD engine while holding the TrpB chemistry/path machinery fixed.
- Uses XML/state checkpoints rather than Amber restart files because restartable
  OpenMM production is the requirement here.
- Keeps HMR off and timestep at 2 fs for the first-pass smoke/prod path to
  minimize surprises relative to the reviewed B5 brief.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

from openmm import LangevinIntegrator, MonteCarloBarostat, Platform, XmlSerializer, unit
from openmm.app import DCDReporter, PDBFile, Simulation, StateDataReporter
from openmm.unit import atmosphere, femtosecond, kelvin, picosecond


DEFAULT_TEMP_K = 350.0
DEFAULT_PRESSURE_ATM = 1.0
DEFAULT_FRICTION_PER_PS = 1.0
DEFAULT_TIMESTEP_FS = 2.0
DEFAULT_NVT_NS = 0.5
DEFAULT_NPT_NS = 0.5
DEFAULT_PROD_NS = 500.0
DEFAULT_REPORT_PS = 100.0
DEFAULT_STATE_PS = 1000.0
DEFAULT_PLATFORM = "CUDA"
DEFAULT_PRECISION = "mixed"
DEFAULT_BAROSTAT_INTERVAL = 25
TOTAL_STEPS_TOL = 1.0e-9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-xml", type=Path, required=True)
    parser.add_argument("--initial-pdb", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--platform", default=os.environ.get("OPENMM_PLATFORM", DEFAULT_PLATFORM))
    parser.add_argument("--precision", default=os.environ.get("OPENMM_PRECISION", DEFAULT_PRECISION))
    parser.add_argument("--temp-k", type=float, default=DEFAULT_TEMP_K)
    parser.add_argument("--pressure-atm", type=float, default=DEFAULT_PRESSURE_ATM)
    parser.add_argument("--friction-per-ps", type=float, default=DEFAULT_FRICTION_PER_PS)
    parser.add_argument("--timestep-fs", type=float, default=DEFAULT_TIMESTEP_FS)
    parser.add_argument("--nvt-ns", type=float, default=DEFAULT_NVT_NS)
    parser.add_argument("--npt-ns", type=float, default=DEFAULT_NPT_NS)
    parser.add_argument("--prod-ns", type=float, default=DEFAULT_PROD_NS)
    parser.add_argument("--report-ps", type=float, default=DEFAULT_REPORT_PS)
    parser.add_argument("--state-ps", type=float, default=DEFAULT_STATE_PS)
    parser.add_argument("--barostat-interval", type=int, default=DEFAULT_BAROSTAT_INTERVAL)
    return parser.parse_args()


def ns_to_steps(ns: float, timestep_fs: float) -> int:
    steps = ns * 1_000_000.0 / timestep_fs
    if abs(round(steps) - steps) > TOTAL_STEPS_TOL:
        raise ValueError(f"ns={ns} with timestep_fs={timestep_fs} does not map cleanly to integer steps")
    return int(round(steps))


def ps_to_steps(ps: float, timestep_fs: float) -> int:
    steps = ps * 1_000.0 / timestep_fs
    if abs(round(steps) - steps) > TOTAL_STEPS_TOL:
        raise ValueError(f"ps={ps} with timestep_fs={timestep_fs} does not map cleanly to integer steps")
    return int(round(steps))


def load_system(system_xml_path: Path):
    return XmlSerializer.deserialize(system_xml_path.read_text())


def select_platform(platform_name: str, precision: str) -> Tuple[Platform, Dict[str, str]]:
    platform = Platform.getPlatformByName(platform_name)
    props = {"Precision": precision} if platform.getName() == "CUDA" else {}
    return platform, props


def create_simulation(
    system_xml_path: Path,
    pdb: PDBFile,
    platform_name: str,
    precision: str,
    temp_k: float,
    friction_per_ps: float,
    timestep_fs: float,
    use_barostat: bool,
    pressure_atm: float,
    barostat_interval: int,
) -> Simulation:
    system = load_system(system_xml_path)
    if use_barostat:
        system.addForce(MonteCarloBarostat(pressure_atm * atmosphere, temp_k * kelvin, barostat_interval))
    integrator = LangevinIntegrator(temp_k * kelvin, friction_per_ps / picosecond, timestep_fs * femtosecond)
    platform, props = select_platform(platform_name, precision)
    simulation = Simulation(pdb.topology, system, integrator, platform, props)
    return simulation


def save_state_xml(simulation: Simulation, path: Path) -> None:
    state = simulation.context.getState(
        getPositions=True,
        getVelocities=True,
        getEnergy=True,
        getForces=False,
        getParameters=True,
        enforcePeriodicBox=True,
    )
    path.write_text(XmlSerializer.serialize(state))


def load_state_xml(simulation: Simulation, path: Path) -> None:
    simulation.context.setState(XmlSerializer.deserialize(path.read_text()))


def write_final_pdb(simulation: Simulation, path: Path) -> None:
    state = simulation.context.getState(getPositions=True, enforcePeriodicBox=True)
    with path.open("w") as handle:
        PDBFile.writeFile(simulation.topology, state.getPositions(), handle, keepIds=True)


def run_chunked(simulation: Simulation, total_steps: int, chunk_steps: int, checkpoint_path: Path) -> int:
    completed = 0
    while completed < total_steps:
        step_now = min(chunk_steps, total_steps - completed)
        simulation.step(step_now)
        completed += step_now
        save_state_xml(simulation, checkpoint_path)
    return completed


def run_stage(
    simulation: Simulation,
    stage_name: str,
    stage_steps: int,
    report_steps: int,
    state_steps: int,
    total_stage_steps: int,
    workdir: Path,
    append: bool = False,
) -> Dict[str, float]:
    dcd_path = workdir / f"{stage_name}.dcd"
    log_path = workdir / f"{stage_name}.log"
    checkpoint_path = workdir / f"{stage_name}_state.xml"
    final_state_path = workdir / f"{stage_name}_final_state.xml"
    final_pdb_path = workdir / f"{stage_name}_final.pdb"

    simulation.reporters.append(
        DCDReporter(str(dcd_path), report_steps, append=append)
    )
    simulation.reporters.append(
        StateDataReporter(
            str(log_path),
            report_steps,
            step=True,
            time=True,
            potentialEnergy=True,
            kineticEnergy=True,
            totalEnergy=True,
            temperature=True,
            speed=True,
            progress=True,
            remainingTime=True,
            totalSteps=total_stage_steps,
            separator="\t",
            append=append,
        )
    )

    t0 = time.time()
    completed = run_chunked(simulation, stage_steps, state_steps, checkpoint_path)
    wall = time.time() - t0
    save_state_xml(simulation, final_state_path)
    write_final_pdb(simulation, final_pdb_path)
    for reporter in list(simulation.reporters):
        reporter_file = getattr(reporter, "_out", None)
        if reporter_file is not None and not reporter_file.closed:
            reporter_file.flush()
    simulated_ns = stage_steps * simulation.integrator.getStepSize().value_in_unit(unit.nanosecond)
    ns_per_day = simulated_ns / (wall / 86400.0) if wall > 0 else float("inf")
    return {
        "stage_steps": completed,
        "stage_ns": simulated_ns,
        "wall_s": wall,
        "ns_per_day": ns_per_day,
        "checkpoint_path": str(checkpoint_path),
        "final_state_path": str(final_state_path),
        "final_pdb_path": str(final_pdb_path),
    }


def append_json(path: Path, payload: Dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    pdb = PDBFile(str(args.initial_pdb))

    report_steps = ps_to_steps(args.report_ps, args.timestep_fs)
    state_steps = ps_to_steps(args.state_ps, args.timestep_fs)
    nvt_steps = ns_to_steps(args.nvt_ns, args.timestep_fs)
    npt_steps = ns_to_steps(args.npt_ns, args.timestep_fs)
    prod_steps_total = ns_to_steps(args.prod_ns, args.timestep_fs)

    summary_path = args.workdir / "run_summary.json"
    prod_progress_path = args.workdir / "prod_progress.json"
    stage_summary: Dict[str, Dict] = {}

    print(f"system_xml={args.system_xml}")
    print(f"initial_pdb={args.initial_pdb}")
    print(f"workdir={args.workdir}")
    print(f"platform={args.platform}")
    print(f"precision={args.precision}")
    print(f"nvt_steps={nvt_steps}")
    print(f"npt_steps={npt_steps}")
    print(f"prod_steps_total={prod_steps_total}")
    print(f"report_steps={report_steps}")
    print(f"state_steps={state_steps}")

    nvt_final_state = args.workdir / "nvt_final_state.xml"
    npt_final_state = args.workdir / "npt_final_state.xml"
    prod_state = args.workdir / "prod_state.xml"
    prod_final_state = args.workdir / "prod_final_state.xml"

    if not nvt_final_state.exists():
        sim_nvt = create_simulation(
            args.system_xml,
            pdb,
            args.platform,
            args.precision,
            args.temp_k,
            args.friction_per_ps,
            args.timestep_fs,
            use_barostat=False,
            pressure_atm=args.pressure_atm,
            barostat_interval=args.barostat_interval,
        )
        sim_nvt.context.setPositions(pdb.positions)
        sim_nvt.context.setVelocitiesToTemperature(args.temp_k * kelvin)
        stage_summary["nvt"] = run_stage(
            sim_nvt,
            "nvt",
            nvt_steps,
            report_steps,
            state_steps,
            nvt_steps,
            args.workdir,
        )
        print(f"NVT_NS_PER_DAY={stage_summary['nvt']['ns_per_day']:.3f}")

    if not npt_final_state.exists():
        sim_npt = create_simulation(
            args.system_xml,
            pdb,
            args.platform,
            args.precision,
            args.temp_k,
            args.friction_per_ps,
            args.timestep_fs,
            use_barostat=True,
            pressure_atm=args.pressure_atm,
            barostat_interval=args.barostat_interval,
        )
        load_state_xml(sim_npt, nvt_final_state)
        stage_summary["npt"] = run_stage(
            sim_npt,
            "npt",
            npt_steps,
            report_steps,
            state_steps,
            npt_steps,
            args.workdir,
        )
        print(f"NPT_NS_PER_DAY={stage_summary['npt']['ns_per_day']:.3f}")

    prod_steps_done = 0
    prod_append = False
    sim_prod = create_simulation(
        args.system_xml,
        pdb,
        args.platform,
        args.precision,
        args.temp_k,
        args.friction_per_ps,
        args.timestep_fs,
        use_barostat=True,
        pressure_atm=args.pressure_atm,
        barostat_interval=args.barostat_interval,
    )
    if prod_progress_path.exists() and prod_state.exists():
        progress = json.loads(prod_progress_path.read_text())
        prod_steps_done = int(progress.get("prod_steps_done", 0))
        load_state_xml(sim_prod, prod_state)
        prod_append = True
    else:
        load_state_xml(sim_prod, npt_final_state)

    prod_steps_remaining = prod_steps_total - prod_steps_done
    if prod_steps_remaining < 0:
        raise ValueError(f"prod_steps_done={prod_steps_done} exceeds prod_steps_total={prod_steps_total}")

    sim_prod.reporters.append(
        DCDReporter(str(args.workdir / "prod.dcd"), report_steps, append=prod_append)
    )
    sim_prod.reporters.append(
        StateDataReporter(
            str(args.workdir / "prod.log"),
            report_steps,
            step=True,
            time=True,
            potentialEnergy=True,
            kineticEnergy=True,
            totalEnergy=True,
            temperature=True,
            speed=True,
            progress=True,
            remainingTime=True,
            totalSteps=prod_steps_total,
            separator="\t",
            append=prod_append,
        )
    )

    prod_t0 = time.time()
    while prod_steps_done < prod_steps_total:
        step_now = min(state_steps, prod_steps_total - prod_steps_done)
        sim_prod.step(step_now)
        prod_steps_done += step_now
        save_state_xml(sim_prod, prod_state)
        append_json(
            prod_progress_path,
            {
                "prod_steps_done": prod_steps_done,
                "prod_steps_total": prod_steps_total,
                "prod_ns_done": prod_steps_done * args.timestep_fs / 1_000_000.0,
                "prod_ns_total": args.prod_ns,
            },
        )
    prod_wall = time.time() - prod_t0
    save_state_xml(sim_prod, prod_final_state)
    write_final_pdb(sim_prod, args.workdir / "prod_final.pdb")
    prod_ns = prod_steps_total * args.timestep_fs / 1_000_000.0
    prod_ns_per_day = prod_ns / (prod_wall / 86400.0) if prod_wall > 0 else float("inf")
    stage_summary["prod"] = {
        "stage_steps": prod_steps_total,
        "stage_ns": prod_ns,
        "wall_s": prod_wall,
        "ns_per_day": prod_ns_per_day,
        "checkpoint_path": str(prod_state),
        "final_state_path": str(prod_final_state),
        "final_pdb_path": str(args.workdir / "prod_final.pdb"),
    }
    print(f"PROD_NS_PER_DAY={prod_ns_per_day:.3f}")

    append_json(
        summary_path,
        {
            "platform": args.platform,
            "precision": args.precision,
            "temp_k": args.temp_k,
            "pressure_atm": args.pressure_atm,
            "friction_per_ps": args.friction_per_ps,
            "timestep_fs": args.timestep_fs,
            "nvt_ns": args.nvt_ns,
            "npt_ns": args.npt_ns,
            "prod_ns": args.prod_ns,
            "report_ps": args.report_ps,
            "state_ps": args.state_ps,
            "stage_summary": stage_summary,
        },
    )
    print(f"summary_json={summary_path}")
    print("AEX1_CMD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
