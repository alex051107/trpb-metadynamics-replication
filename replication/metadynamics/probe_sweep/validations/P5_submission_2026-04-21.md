## P5 10 ns diagnostic submission

- Date: 2026-04-21
- Remote working directory: `/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep`
- Submission script: `submit_probe_p5_10ns.sh`
- Submitted job id: `44956006`
- Scheduler state at submission check: `PENDING`
- Scheduler start estimate at submission check: `N/A`

### P5 tuning surface

- `SIGMA_MIN=0.5,0.02`
- `SIGMA_MAX=1.0,0.05`

### Locked factors reused verbatim

- `LAMBDA=379.77`
- `SIGMA=0.1`
- `HEIGHT=0.628`
- `PACE=1000`
- `BIASFACTOR=10`
- `TEMP=350`
- `ADAPTIVE=GEOM`

### Launch notes

- Fresh launch only; no restart or checkpoint continuation
- Uses the same `start.gro` and `topol.top` source as P1-P4
- Uses the 10 ns `metad_probe.mdp` materialization, not the earlier 5 ns staging file
