## P3 30 ns extension submission

- Date: 2026-04-21
- Remote working directory: `/work/users/l/i/liualex/AnimaLab/metadynamics/probe_sweep/probe_P3`
- Submission script: `submit_p3_extend_30ns.sh`
- Active job id: `44956161`
- Active scheduler state after fix: `RUNNING`
- Active start time: `2026-04-21T22:23:12 EDT`

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

### Runtime notes

- First submit `44955975` failed immediately with `ExitCode 141:0` because `set -o pipefail` treated the old `grep ... | head -1` preflight snapshot as a fatal SIGPIPE.
- Second submit `44956108` still failed immediately with `ExitCode 141:0`; redirecting `convert-tpr` and `mdrun` output to dedicated local log files removed the remaining batch-pipe failure mode.
- During diagnosis, one manual login-node reproduction advanced the live restart state from `10000 ps` to `10009 ps` and appended `7` additional HILLS rows without creating `bck.*.HILLS` or `bck.*.COLVAR`. The active batch restart therefore continues from the current checkpoint at `10.009 ns`, not exactly `10.000 ns`.
