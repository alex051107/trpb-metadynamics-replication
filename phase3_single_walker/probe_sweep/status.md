# Probe sweep live status

Auto-written by `routine_check.py` every 2 hours.

_Last tick: 2026-04-23T16:53:40Z_

**Winner:** none yet

## Per-probe saturation (key signal)

Columns show % of hills touching each bound. Anything >50 means that bound is binding and the adaptive width can't breathe.

| probe | ns | hills | max_s | O/PC/C | σ_s MIN | σ_s MAX | σ_z MIN | σ_z MAX | passes |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 10.00 | 5000 | 1.15 | 10001/0/0 | 100.0 | 0.0 | 98.0 | 0.0 | wait |
| P2 | 10.00 | 5000 | 1.30 | 10001/0/0 | 99.9 | 0.0 | 98.9 | 0.0 | wait |
| P3 | 28.80 | 14397 | 1.28 | 28797/0/0 | 100.0 | 0.0 | 93.5 | 0.0 | wait |
| P4 | 10.00 | 5000 | 1.64 | 10001/0/0 | 98.3 | 0.0 | 94.8 | 0.0 | wait |
| P5 | 10.00 | 5000 | 1.33 | 10001/0/0 | 95.5 | 1.6 | 100.0 | 0.0 | wait |

## Ladder reminder

| probe | σ_s MIN / MAX | σ_z MIN / MAX |
|---|---|---|
| P1 | 0.5 / 1.0 | 0.005 / 0.05 |
| P2 | 0.5 / 1.5 | 0.005 / 0.05 |
| P3 | 0.7 / 1.5 | 0.005 / 0.05 |
| P4 | 0.5 / 1.0 | 0.005 / 0.03 |
| P5 | 0.5 / 1.0 | 0.02 / 0.05 |

## ΔG between O/PC/C (pseudo-FES, per SI S4 convergence monitor)

| probe | ΔG(PC−O) | ΔG(C−O) | ΔG(C−PC) |
|---|---|---|---|
| P1 | — | — | — |
| P2 | — | — | — |
| P3 | — | — | — |
| P4 | — | — | — |
| P5 | — | — | — |

## Raw fetch

```json
{
  "P1": {
    "colvar_lines": 10002,
    "hills_lines": 5003
  },
  "P2": {
    "colvar_lines": 10002,
    "hills_lines": 5003
  },
  "P3": {
    "colvar_lines": 28800,
    "hills_lines": 14406
  },
  "P4": {
    "colvar_lines": 10002,
    "hills_lines": 5003
  },
  "P5": {
    "colvar_lines": 10002,
    "hills_lines": 5003
  }
}
```

## Paper protocol reference

- Convergence: Osuna 2019 SI S4 — monitor ΔG between O/PC/C local minima vs time.
- Labels: O=s(R)∈[1,5), PC=[5,10), C=[10,15]; structure selection = cluster representative structures per minimum.
- Gate: max_s ≥ 7 AND ≥3 non-empty s-bins AND σ_s saturation < 50%. Full path s=15 is thermodynamically inaccessible from isolated Ain; seed diversity for Phase 4 is the real goal.
