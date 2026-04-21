# Probe Sweep — SIGMA_MIN/MAX (P1..P4)

Diagnosis-first sweep. See `/Users/liuzhenpeng/.claude/plans/clever-tickling-sparrow.md` for context.

## Local materialisation

```
python3 launch_sweep.py
```

Writes `probe_P1/ … probe_P4/` with substituted `plumed.dat`, `metad.mdp`, `path_gromacs.pdb`, and `provenance.txt`.

## Upload and submit on Longleaf

```
rsync -av replication/metadynamics/probe_sweep/ longleaf:/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/
ssh longleaf 'cd /work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep && sbatch submit_probe_array.sh'
```

## Mid-run diagnostic

```
python3 diagnose_hills.py probe_P1/HILLS --smin-s 0.5 --smax-s 1.0 --smin-z 0.005 --smax-z 0.05
```

## Pick a winner (after all 4 probes finish)

```
python3 check_winner.py
cat results.tsv winner.txt
```

Winner gate: `max s ≥ 7` AND ≥3 non-empty s-bins AND σ_s saturation < 50%.
