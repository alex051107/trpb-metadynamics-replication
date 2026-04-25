# TrpB MetaD Cartridge — Scoring Wrapper API Design

> **Status**: Design sketch (v0.1, 2026-04-22). No implementation yet — WT FES is still running.
> **Purpose**: Lock the interface before writing code so downstream consumers (Yu, Amin, future Raswanth integration) can reason about what calls they will make.
> **Related**: `新任务explore/MetaD_Cartridge_Feasibility_Memo_2026-04-22.md` §0.3 Deliverable 2.

---

## 1. What this wrapper is

A single Python package `trpb_cartridge` that takes any trajectory (MD, STAR-MD output, ConfRover output, short MetaD run) and returns a **mechanism-grounded evaluation report** against the TrpB MetaD reference.

The wrapper does **not**:
- Run MetaDynamics (that's PLUMED + GROMACS)
- Train models
- Modify trajectories

The wrapper **does**:
- Project frames onto the reference PATHMSD (s, z) axes
- Classify frames into O / PC / C / off-path / reactive-ready
- Compare trajectory-derived distributions to reference FES
- Compute a small set of catalytic geometry descriptors per frame
- Return everything as a structured report + optional plots

---

## 2. Minimum viable API (v0 target)

```python
from trpb_cartridge import load_cartridge, project_to_path, score_state_occupancy, report_catalytic_geometry

cart = load_cartridge("WT")   # or "Aex1", "variant_XYZ"
s, z = project_to_path(trajectory, cart)
occ  = score_state_occupancy(s, z, cart)
geom = report_catalytic_geometry(trajectory, cart)
```

Each call returns a small, pickle-able dataclass. No hidden state.

---

## 3. Function signatures

### 3.1 `load_cartridge(name: str) -> Cartridge`

Loads one of the published cartridge handles.

**Input**:
- `name`: `"WT"` | `"Aex1"` | `"variant_<tag>"` — resolves via a manifest in the package

**Returns**: a `Cartridge` dataclass with attributes:
- `path_pdb: Path` — the 15-frame PATHMSD reference structure
- `lambda_path: float` — PATHMSD λ (for the WT cartridge, ~0.034 in nm⁻²)
- `fes_grid: np.ndarray` — shape (N_s, N_z), reference free energy in kJ/mol, block-averaged
- `fes_ci: np.ndarray` — shape (N_s, N_z, 2), 95% CI bounds per bin
- `state_masks: dict[str, np.ndarray]` — keys `"O"`, `"PC"`, `"C"`, `"off_path"`, `"reactive_ready"`; each a boolean mask on the (s, z) grid
- `rare_state_frames: Path` — parquet file of reweighted rare-state frames + weights + ESS + block IDs
- `catalytic_descriptor_spec: dict` — definitions of the geometry descriptors (see §3.4)
- `provenance: dict` — git SHA of the MetaD run, force-field version, HILLS file hash

**不确定**:
- Whether WT `lambda_path` value will stay at 0.034 once path.pdb is reconciled with Miguel's version
- Whether `fes_grid` resolution should be chosen per-variant or unified

---

### 3.2 `project_to_path(trajectory, cartridge) -> (s: np.ndarray, z: np.ndarray)`

Projects a trajectory onto the cartridge's PATHMSD axes using the same λ and reference as the MetaD run.

**Input**:
- `trajectory`: path to xtc/dcd/pdb OR an MDAnalysis Universe OR a numpy (N_frames, N_atoms, 3) array
- `cartridge`: from `load_cartridge`

**Returns**:
- `s`: shape (N_frames,), path progress ∈ [1, N_ref_frames]
- `z`: shape (N_frames,), off-path distance in nm²

**Implementation note**: wraps PLUMED driver in subprocess if trajectory has a topology; if raw coords, uses `mdtraj` + PATHMSD in python.

**不确定**: whether python-native PATHMSD matches PLUMED driver to within numerical tolerance. Need a reference test against WT MetaD output.

---

### 3.3 `score_state_occupancy(s, z, cartridge) -> StateOccupancyReport`

Given projected (s, z) coordinates, compute state populations, compare to reference FES, flag failures.

**Returns** `StateOccupancyReport`:
- `occupancy: dict[str, float]` — population in each state (must sum to 1)
- `reference_occupancy: dict[str, float]` — same states, from cartridge reference
- `occupancy_residual: dict[str, float]` — `occupancy - reference`
- `chi2_vs_reference: float` — overall distributional distance (using cartridge block CI as denominator)
- `rare_state_recall: float` — fraction of cartridge rare-state frames this trajectory samples within ε
- `off_path_fraction: float` — fraction of frames with z > threshold
- `failure_flags: list[str]` — e.g. `["off_path_dominant"]`, `["missing_C_basin"]`, `["z_drift_late_time"]`

**载荷**: this is the single most useful output for Amin (benchmark) and Raswanth (filter).

---

### 3.4 `report_catalytic_geometry(trajectory, cartridge) -> CatalyticGeometryReport`

Computes the catalytic descriptors (per frame) and compares their distributions to reference.

**Default descriptors (v0)**:
1. K82(NZ) – PLP(C4') distance — Schiff-base proximity
2. PLP ring tilt vs Cα plane — Dunathan-like orientation proxy
3. indole tunnel gate distance — substrate access
4. E104(OE)–PLS(O3) distance — phenol H-bond proxy
5. Y301(OH)–PLS(N1) distance — pyridine N orientation proxy

(Spec lives in `cartridge.catalytic_descriptor_spec`.)

**Returns** `CatalyticGeometryReport`:
- `descriptor_values: dict[str, np.ndarray]` — shape (N_frames,) per descriptor
- `state_conditional_mean: dict[str, dict[str, float]]` — descriptor × state
- `js_divergence_vs_reference: dict[str, float]` — one JSD per descriptor
- `catalytic_readiness_score: float` — weighted combination; ∈ [0, 1]
- `failure_flags: list[str]`

**不确定**:
- Whether these 5 descriptors are sufficient or whether Yu will ask for reaction-state-specific ones (external aldimine, quinonoid)
- Whether `catalytic_readiness_score` weights should be hand-tuned or learned from Yu's MMPBSA ranking
- Whether ff14SB + GAFF produces descriptor values stable enough vs force-field noise

---

## 4. Use-case walkthroughs

### 4.1 Yu demo (D3 option A — primary)

```python
# Yu has been running OpenMM with simple 1D/2D CV; wants to know if PATHMSD
# gives a more meaningful diagnostic on the same trajectory.
cart = load_cartridge("WT")
s, z = project_to_path("yu_openmm_traj.dcd", cart)
occ = score_state_occupancy(s, z, cart)
print(occ.failure_flags)
# e.g. ["off_path_dominant", "missing_PC_basin"]
# → tells Yu her simple CV was driving sampling off the catalytic path
```

### 4.2 Amin demo (D3 option B)

```python
# Amin generates a 1 μs trajectory on TrpB using his STAR-MD fork
# and wants an enzyme-specific evaluation that ATLAS metrics can't give.
cart = load_cartridge("WT")
s, z = project_to_path("starmd_output.xtc", cart)
occ = score_state_occupancy(s, z, cart)
geom = report_catalytic_geometry("starmd_output.xtc", cart)
# Amin can now report:
#   - STAR-MD's conformational-coverage on ATLAS: X
#   - STAR-MD's state-occupancy error on TrpB: Y
#   - STAR-MD's catalytic-descriptor JSD: Z
# The enzyme-specific failure modes are legible, not hidden behind JSD-on-tICA.
```

### 4.3 Future Raswanth filter

```python
# After RFD3 generates N candidate backbones, Raswanth wants to flag
# "geometrically valid but dynamically incompetent" designs.
for design in rfd3_outputs:
    short_md = run_short_md(design)  # Yu's pipeline
    s, z = project_to_path(short_md, cart)
    if score_state_occupancy(s, z, cart).failure_flags:
        flag(design, reason="dynamically incompetent")
```

---

## 5. What this deliberately does NOT do

- Does not train a reward model (that's CRR, later)
- Does not run MetaD rescue (that's MNG, later)
- Does not condition a generative model (that's PP-Prior, later)
- Does not run QM/MM or DFT
- Does not handle reaction-state transitions (external aldimine → quinonoid) in v0 — only COMM conformational states

---

## 6. Open questions to resolve before v0 implementation

1. **path.pdb reconciliation** with Miguel — blocks everything downstream
2. **Whether Yu's OpenMM frames are reconciled topology with the PLUMED run** (atom indexing consistency)
3. **Whether Amin has any STAR-MD output on a TrpB-shaped input** or only on ATLAS proteins
4. **Whether block CI for `fes_ci` should come from reweighting blocks of the same run, or from multiple walkers** (will depend on Phase 2 10-walker outcome)
5. **Package name**: `trpb_cartridge` vs `metad_cartridge` — 若 Amin 未来想扩展到别的酶，后者更通用
6. **Whether to ship as pip-installable from day 1 or as a project-local module**

---

## 7. Revision history

- v0.1 (2026-04-22, Claude): initial design sketch; API frozen in signature, semantics flagged as UNVERIFIED where needed
- v0.2 (pending): after Miguel path reconciliation + WT FES sanity check
