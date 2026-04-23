# MetaD Pipeline Debug — 2026-04-04

> **Validation type**: Bug fix + before/after verification
> **Campaign**: osuna2019-benchmark
> **Stage**: Runner (Stage 3)

---

## Summary

Three bugs were discovered and fixed in the MetaDynamics pipeline during initial test runs on Longleaf. All three prevented GROMACS+PLUMED2 from producing valid CV traces. After fixing all three, a test run produced physically reasonable z(R) values.

---

## Bug 1: LAMBDA unit mismatch (FP-018)

### How found
Three parallel subagents (rmsd-checker, units-checker, fes-figure-reader) independently flagged that z(R) = -78 was unphysical. The units-checker traced the issue: SI reports λ = 0.029-0.034 Å⁻², but GROMACS+PLUMED uses nm internally. LAMBDA must be multiplied by 100 to convert Å⁻² → nm⁻².

### Before
```
path: PATHMSD REFERENCE=... LAMBDA=0.033910
```
z(R) output: **-78** (unphysical; expected ~0.5)

### After
```
path: PATHMSD REFERENCE=... LAMBDA=3.3910  # Å⁻² × 100 = nm⁻²
```
z(R) output: **0.49** (physically reasonable)

### Files fixed
- `replication/scripts/plumed_trpb_metad.dat`
- `replication/scripts/plumed_trpb_metad_single.dat`

---

## Bug 2: Backslash continuation not parsed by GROMACS 2026 (FP-019)

### How found
GROMACS 2026 mdrun with `-plumed` flag reported "SIGMA is compulsory" even though SIGMA was present in the file. Investigation revealed that GROMACS 2026's PLUMED interface re-parses the input and truncates lines at `\`, ignoring continuation lines.

### Before
```
metad: METAD ARG=path.sss,path.zzz \
  SIGMA=0.05 \
  ADAPTIVE=GEOM \
  ...
```
Error: "SIGMA is compulsory"

### After
```
metad: METAD ARG=path.sss,path.zzz SIGMA=0.2,0.1 ADAPTIVE=GEOM HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
```
No parsing errors.

### Files fixed
- `replication/scripts/plumed_trpb_metad.dat`
- `replication/scripts/plumed_trpb_metad_single.dat`

---

## Bug 3: conda-forge PLUMED 2.9.2 libplumedKernel.so incomplete (FP-020)

### How found
`plumed driver` (standalone binary) could parse PATHMSD and METAD correctly. But when GROMACS mdrun loaded libplumedKernel.so at runtime, PATHMSD reported "number of atoms in a frame should be more than zero" — the colvar/mapping/function modules were missing from the shared library.

### Resolution
- Source-compiled PLUMED 2.9.2 with `--enable-rpath` on Longleaf
- Switched from PATHMSD to FUNCPATHMSD (equivalent functionality, more robust PDB handling in mdrun context)
- Verified `plumed info --components` includes all required modules

### Files affected
- conda-forge plumed 2.9.2 package (not fixable; replaced by source build)

---

## Verification

| Metric | Before (all 3 bugs) | After (all 3 fixed) | Expected |
|--------|---------------------|---------------------|----------|
| z(R) | -78 | 0.49 | ~0.5 |
| s(R) | NaN / crash | 7.2 | 1-15 range |
| METAD parsing | "SIGMA is compulsory" | OK | OK |
| PATHMSD in mdrun | "number of atoms = 0" | OK (FUNCPATHMSD) | OK |

---

## Conclusion

**PASS** — All three bugs fixed. The MetaD pipeline now produces physically reasonable path CV values. The LAMBDA unit conversion (FP-018) was the most impactful bug, causing a ~100x error in the distance-from-path metric.


---

## 2026-04-15 Update — Historical-only note (FP-024)

The SIGMA=0.2,0.1 shown in the "After" block above was later found to be:
(a) non-functional with ADAPTIVE=GEOM because PLUMED 2.9 expects a single
    Cartesian nm SIGMA with GEOM; pair values are silently ignored or error.
(b) citing a non-existent SI p.S3 number (the 2019 SI is silent on SIGMA).

The live production value is now:
  `SIGMA=0.1 ADAPTIVE=GEOM SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05`

See `replication/validations/failure-patterns.md` (FP-024, FP-025) and
`replication/metadynamics/single_walker/plumed.dat` for the current config.

This historical note is preserved as-is for traceability.
