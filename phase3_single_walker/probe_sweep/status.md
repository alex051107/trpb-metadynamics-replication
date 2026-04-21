# Probe sweep live status

Auto-written by `routine_check.py` every 2 hours.

_Last tick: 2026-04-21T14:22:50Z_

**Winner:** none yet

## Per-probe saturation (key signal)

Columns show % of hills touching each bound. Anything >50 means that bound is binding and the adaptive width can't breathe.

| probe | ns | hills | max_s | O/PC/C | σ_s MIN | σ_s MAX | σ_z MIN | σ_z MAX | passes |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 1.36 | 679 | 1.15 | 1359/0/0 | 100.0 | 0.0 | 100.0 | 0.0 | wait |
| P2 | 1.36 | 682 | 1.15 | 1364/0/0 | 100.0 | 0.0 | 100.0 | 0.0 | wait |
| P3 | 1.39 | 694 | 1.11 | 1388/0/0 | 100.0 | 0.0 | 99.3 | 0.0 | wait |
| P4 | 1.23 | 615 | 1.10 | 1230/0/0 | 100.0 | 0.0 | 100.0 | 0.0 | wait |

## Ladder reminder

| probe | σ_s MIN / MAX | σ_z MIN / MAX |
|---|---|---|
| P1 | 0.5 / 1.0 | 0.005 / 0.05 |
| P2 | 0.5 / 1.5 | 0.005 / 0.05 |
| P3 | 0.7 / 1.5 | 0.005 / 0.05 |
| P4 | 0.5 / 1.0 | 0.005 / 0.03 |

## ΔG between O/PC/C (pseudo-FES, per SI S4 convergence monitor)

| probe | ΔG(PC−O) | ΔG(C−O) | ΔG(C−PC) |
|---|---|---|---|
| P1 | — | — | — |
| P2 | — | — | — |
| P3 | — | — | — |
| P4 | — | — | — |

## Raw fetch

```json
{
  "P1": {
    "colvar_lines": 1360,
    "hills_lines": 682
  },
  "P2": {
    "colvar_lines": 1365,
    "hills_lines": 685
  },
  "P3": {
    "colvar_lines": 1389,
    "hills_lines": 697
  },
  "P4": {
    "colvar_lines": 1231,
    "hills_lines": 618
  }
}
```

## Paper protocol reference

- Convergence: Osuna 2019 SI S4 — monitor ΔG between O/PC/C local minima vs time.
- Labels: O=s(R)∈[1,5), PC=[5,10), C=[10,15]; structure selection = cluster representative structures per minimum.
- Gate: max_s ≥ 7 AND ≥3 non-empty s-bins AND σ_s saturation < 50%. Full path s=15 is thermodynamically inaccessible from isolated Ain; seed diversity for Phase 4 is the real goal.
