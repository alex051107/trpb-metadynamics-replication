# 04 · Baseline single-walker run on naive path (job 45324928)

The control experiment. Same start.gro, same Miguel parameters, same single-walker protocol — but uses the pre-FP-034 *naive* `path_gromacs.pdb` (resid-number alignment, non-homologous residue pairing). Ran 16 ns, never escaped the Open basin.

## Files

| File | What it is |
|---|---|
| `baseline_45324928_stats.txt` | `path.s` histogram + statistics |

## Key outcome

```
Rows           : 81 479
Simulation time: 16.30 ns
min(s)         : 1.005  at t = ~first-frame
max(s)         : 1.896  at t ≈ midrun
Fraction at s<1.25 : 75.24 %
Fraction at s≥10   : 0.00 %
```

The walker is trapped at the Open endpoint. Under the pre-FP-034 coordinate system, no amount of bias accumulation made the walker access `s > 2`. This baseline is the control that proves the subsequent 6.8× widening in the pilot is due to the path-geometry fix alone.

Raw COLVAR (81 479 rows, 4.8 MB) lives at `chatgpt_pro_consult_45558834/raw_data/baseline_45324928_COLVAR` one level up.
