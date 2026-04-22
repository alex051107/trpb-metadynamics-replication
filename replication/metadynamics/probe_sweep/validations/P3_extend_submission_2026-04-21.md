## P3 30 ns extension submission

- Date: 2026-04-21
- Remote working directory: `/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/probe_P3`
- Submission script: `submit_p3_extend_30ns.sh`
- Submitted job id: `44955975`
- Scheduler state at submission check: `PENDING`
- Scheduler start estimate at submission check: `N/A`

### Locked MetaD factors preserved

- `LAMBDA=379.77`
- `SIGMA=0.1`
- `HEIGHT=0.628`
- `PACE=1000`
- `BIASFACTOR=10`
- `TEMP=350`
- `SIGMA_MIN=0.7,0.005`
- `SIGMA_MAX=1.5,0.05`

### Restart protocol

- Extends `metad.tpr` by `20000 ps` using `gmx convert-tpr -extend`
- Generates `plumed_restart.dat` as `plumed.dat + RESTART`
- Asserts normalized `plumed.dat` equivalence before launch
- Fails hard on `bck.*.HILLS` or `bck.*.COLVAR`
- Fails hard if the first HILLS/COLVAR data row changes after restart
