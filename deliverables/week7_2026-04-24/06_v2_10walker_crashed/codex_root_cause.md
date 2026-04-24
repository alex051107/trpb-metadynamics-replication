# Codex root-cause diagnosis of v2 crash

Dispatched via `ask codex` 2026-04-24 17:21. Response captured below verbatim.

## Verdict

> "Most consistent with biased-pilot coordinate seeds being launched directly into fresh production without local relaxation. The common atom pair 4463-4465 across walkers points to a reproducible bad-contact / constraint instability in the seed ensemble, not random GPU failure. Missing velocities in dumped `.gro` also means production likely regenerated / assigned velocities inconsistently with a pre-biased geometry. PLUMED walls/bias can amplify once geometry destabilises, but negative `metad.bias` is downstream corruption after LINCS/SETTLE failure, not primary PLUMED physics."

## Why the atom pair 4463-4465 is the smoking gun

The same two atoms (4463 and 4465, a CH3 methyl hydrogen constraint in the same residue across all walkers) are the first constraint to stretch in every walker. This reproducibility — same system, same initial constraint strain — rules out random GPU failure. It is a **seed-ensemble property**: every seed frame drawn from the pilot xtc is carrying the same bad-contact pattern because every pilot-frame geometry has been under continuous MetaD bias for 8 ns.

## Why .gro without velocities is the amplifier

`gmx trjconv -dump t` outputs a .gro containing only positions, no velocities. When `gmx grompp` then builds `metad.tpr` from that .gro, the `.mdp` either:
- regenerates velocities from a Maxwell-Boltzmann distribution at T, which on an already-stressed geometry produces non-equilibrium kinetic energy partitioning, OR
- assumes existing velocities (in which case the `.gro` parser sees zeros and mdrun starts cold-ish).

Either way, the atoms that were already stressed under bias do not relax within the first few steps; LINCS cannot re-converge the methyl constraint; SETTLE fails on adjacent waters; GROMACS segfaults.

## v3 fix (Codex-prescribed)

1. EM 1000 steps, `emtol = 1000 kJ/mol/nm` — eliminates the bad contacts.
2. NVT 100 ps at 350 K with `gen_vel = yes` and PLUMED OFF — regenerates a proper velocity distribution on a relaxed geometry.
3. Production MetaD from the NVT checkpoint with `gen_vel = no` and PLUMED ON.

The full v3 submit script and assertion suite are in `../07_v3_pipeline_plan/`.

## Assertion suite to prevent recurrence

```python
assert len(seed_frames) == 10
assert len({x.frame_index for x in seed_frames}) == 10, "duplicate seed frame"
assert min(np.diff(sorted(x.s for x in seed_frames))) > 0.25, "seed s too clustered"
assert np.std([x.s for x in seed_frames]) > 2.0, "seed s variance too low"

def gro_has_velocities(path):
    rows = open(path).read().splitlines()[2:-1]
    return all(len(r.split()) >= 9 for r in rows[:100])
# if start.gro has no velocities, MUST route through NVT settle
```

Closes (will close on successful v3) these failure-pattern entries:
- FP-030 homogeneous-start (already closed by v2 CV-diverse seeds)
- new FP-035 to register: biased-seed LINCS instability + velocity-absence requirement
