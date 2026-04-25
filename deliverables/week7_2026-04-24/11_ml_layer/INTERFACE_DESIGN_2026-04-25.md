# MetaD → ML Interface Design (data shapes only)

> Date: 2026-04-25 | Author: Claude (designer)
> Scope: schemas, file layouts, function signatures. Math is out of scope.
> Companions: `MetaD_to_ML_Label_Contract_2026-04-25.md` (L0/L1/L2/L3 semantics), `replication/cartridge/API_DESIGN.md`. This doc is the **shape**; the contract is the **semantics**. Production runs (10 walkers × 250+ ns, biasfactor=15, T=350 K, PACE=1000 fs, COLVAR STRIDE=200 fs) are assumed converged.

## §1 Overview

Three artifacts:

- **`frame_descriptors.parquet`** — one row per saved frame (s, z, time, walker, weights). Parquet because columnar, typed, walker-filterable.
- **`fes_grid.npz`** — reweighted FES on a regular (s, z) grid + block CI + state masks. NPZ because it is dense 2-D arrays sharing axes.
- **`label_manifest.csv`** — row-by-row provenance ledger from Label Contract §8. CSV because Skeptic diffs it line-by-line at gate review.

A fourth artifact, **`joint_features.parquet`**, joins the frame table with sequence-level GenSLM embeddings and well-tempered reweight factors — the actual ML input. Whether `genslm_embed` is populated or `null` is the gating question of §4.

## §2 Inputs from MetaD

PLUMED `plumed.dat` declares `LENGTH=A ENERGY=kcal/mol`, so raw `p1.zzz` is **Å²**, display RMSD is `sqrt(p1.zzz)` Å, FES is **kcal/mol**.

| input | path pattern | columns | unit chain | cadence | converged size |
|---|---|---|---|---|---|
| HILLS | `runs/{run_id}/HILLS_DIR/HILLS.{walker_id}` | `time, p1.sss, p1.zzz, sigma_×3, height, biasf` | ps; –; Å²; Å²; kcal/mol; – | PACE 1000 × 2 fs = **2 ps/hill** | 250 ns × 10 walkers ≈ 1.25 M hills, ~120 MB Parquet |
| COLVAR | `runs/{run_id}/COLVAR_DIR/COLVAR.{walker_id}` | `time, p1.sss, p1.zzz, @3.bias, uwall.bias, uwall.force2` | ps; –; Å²; kcal/mol | STRIDE 100 × 2 fs = **0.2 ps/row** | 12.5 M rows, ~120 MB |
| FES | `runs/{run_id}/fes_sumhills.dat` | `p1.sss, p1.zzz, file.free, 2 deriv` | –; Å²; kcal/mol | one shot per `sum_hills` invocation | grid 301×141 = 42 441 rows, ~3 MB |

```python
def read_colvar(p):
    df = pl.read_csv(p, separator=r"\s+", comment_prefix="#",
        schema={"time_ps":pl.Float64,"s":pl.Float64,"zzz_A2":pl.Float64,
                "bias_kcalmol":pl.Float64,"uwall_kcalmol":pl.Float64,
                "uwall_force2":pl.Float64})
    assert (df["zzz_A2"]>=0).all() and df["s"].is_between(0.5,15.5).all()
    assert (df.filter(pl.col("zzz_A2")<=2.5)["uwall_kcalmol"]==0).all()  # wall AT=2.5
    return df
# read_hills(): same pattern; assert biasf ∈ [1,16], height>0, s ∈ [0.5,15.5].
# read_fes(): np.loadtxt → reshape (301,141); assert finite; zero-shift to min.
```

## §3 Outputs to ML

### 3.1 `frame_descriptors.parquet` (L0/L1)

One row per kept COLVAR frame (after burn-in). Sample size: 10 walkers × 250 ns / 0.2 ps × 0.92 (post-burn-in) ≈ **11.5 M rows** ≈ 120 MB.

| column | dtype | unit / range | role |
|---|---|---|---|
| `system_id`, `sequence_id` | str | e.g. `WT_PfTrpB`, `GenSLM-230`, `NdTrpB` | feature key |
| `intermediate` | enum {`Ain`,`Aex1`,`Q2`} | — | feature key |
| `walker_id` | uint8 | 0..9 | grouping |
| `frame_idx`, `time_ps` | u32, f32 | ps | feature |
| `s_path` | f32 | [1,15] dimensionless | feature |
| `z_path_A2` | f32 | [0, 2.8] Å² (raw; PLUMED grid max from `--max 15.5,2.8`) | feature |
| `z_path_A` | f32 | [0, 1.673] Å (= √z_path_A2; SI Fig 3 RMSD axis) | feature |
| `bias_kcalmol` | f32 | kcal/mol | for reweighting |
| `state_pseudo` | enum {O,PC,C,off} + str `state_reason` | reason can be e.g. `pre_O_like` | label (L1) |
| `valid_for_L0`/`valid_for_L1` | bool | — | mask |
| `path_hash`, `mask_version`, `reject_reason` | str | — | provenance |

### 3.2 `fes_grid.npz`

| key | shape | dtype | unit | role |
|---|---|---|---|---|
| `s_axis` | (301,) | f32 | dimensionless | feature axis |
| `z_axis_A2` | (141,) | f32 | Å² | feature axis |
| `F_kcalmol` | (301,141) | f32 | kcal/mol | label (L2) |
| `block_ci_low/high_kcalmol` | (301,141) | f32 | kcal/mol | label uncertainty |
| `mask_O / mask_PC / mask_C / mask_off` | (301,141) | bool | — | geometry label |
| `prob_reweighted` | (301,141) | f32 | ∑=1 | weight |
| `convergence_grade` | dict | `{status: {PASS,PROVISIONAL,FAIL}, reason: str, ess_min: f32, block_ci_max: f32, max_weight_frac: f32}` | gate (per Codex audit 2026-04-25 fix) |
| `meta` | dict | path_hash, λ, T, biasfactor, run_ids | provenance |

### 3.3 `joint_features.parquet`

ML input table; schema in §5.

### 3.4 `label_manifest.csv`

Row-per-`(sequence_id, label_name)`. Schema imported verbatim from Label Contract §8.

## §4 GenSLM interaction surface

Direct from Lambert 2026 p3: "we employed the **25M** parameter GenSLM and fine-tuned it on … 30,000 unique trpB nucleotide sequences corresponding to **22,800 unique amino acid sequences** … **Embeddings from the GenSLM model** were used to compare … using t-SNE." From Zvyagin 2023: codon-level tokenizer (64 codons + special tokens), GPT-NeoX autoregressive transformer. **Code+checkpoints**: `github.com/AI-ProteinDesign/GenSLM-TrpB` (MIT, fine-tuned 25M + Supplementary Data 1 nucleotide FASTA); base at `github.com/ramanathanlab/genslm`.

Pinned: input = DNA → codon-level tokens with BOS=`ATG`; sequences are **306–421 codon tokens (= 918–1263 nucleotides; 1 codon token represents 3 nt)** — corrected per Codex audit 2026-04-25; the prior version inverted the unit (nt ↔ codon-token); the underlying numbers (306–421 AA, 918–1263 nt) match Lambert 2026 methods. Inference fits a single 16 GB GPU; embeddings exposed (Lambert Fig 2A used them for t-SNE).

**BLOCKED — must close before populating `genslm_embed`**:
1. `d_model` of released 25M-TrpB checkpoint (not stated in text; likely 384 or 512 — typical GPT-NeoX-25M). **Mechanically extractable today** (added per Codex Round 2 NICE-TO-HAVE) — one-shot:
   ```bash
   tmp=$(mktemp -d) && git clone --depth 1 https://github.com/AI-ProteinDesign/GenSLM-TrpB "$tmp" >/dev/null 2>&1 && python3 - <<'PY'
   import json, pathlib
   hits=[]
   for p in pathlib.Path("$tmp").rglob("config.json"):
       d=json.loads(p.read_text())
       v=d.get("hidden_size", d.get("n_embd", d.get("d_model")))
       if v is not None: hits.append(int(v))
   assert len(set(hits)) == 1, hits
   print(hits[0])
   PY
   ```
   Returns the integer `hidden_size`. If multiple `config.json` files disagree, the assert fires and we ask the authors. No need to bother Lambert / Dharuman unless this returns something unexpected.
2. Pooling rule used for Fig 2A (mean / CLS / last-token). ASK GenSLM authors OR replicate Fig 2A and grid-search.
3. Per-residue vs per-sequence — v0 needs only per-sequence.
4. Whether codon-level embedding meaningfully differs from AA-level: **UNVERIFIED**; if no, ESM-2 fallback admissible.

Until (1)+(2) close, `genslm_embed = null`; dtype reserved as `array[float32, dim=TBD]`. The interface compiles either way.

## §5 Joint feature/label table — `joint_features.parquet`

One row = one (sequence, frame) pair.

| column | dtype | range / unit | role | mandatory |
|---|---|---|---|---|
| `row_id` | str (uuid) | — | key | yes |
| `sequence_id` | str | `WT_PfTrpB`/`GenSLM-230`/`NdTrpB` | feature key | yes |
| `walker_id` | u8 | 0..9 | split unit | yes |
| `time_ps` | f32 | [0, 500_000] | feature | yes |
| `s_path` | f32 | [1, 15] dimensionless | feature | yes |
| `z_path_A2` | f32 | [0, 2.8] Å² (PLUMED grid max) | feature | yes |
| `z_path_A` | f32 | [0, 1.673] Å (= √z_path_A2; SI Fig 3 axis) | feature | derived |
| `F_kcalmol` | f32 | [0, ~25] kcal/mol; bilinear-interp from `fes_grid.npz` at (s, z) | label (L2) | yes |
| `bias_kcalmol` | f32 | [0, ~30] kcal/mol; from COLVAR | for reweighting | yes |
| `weight_w_t` | f32 | (0, ∞), ∑=1 after normalize | sample weight | yes |
| `state_pseudo` | enum | {O,PC,C,off} | label (L1) | yes |
| `state_reason` | str ∪ {null} | e.g. `pre_O_like`, `wall_clipped`; merged from former `pre_O` enum (Codex audit fix) | provenance | optional |
| `state_mask_l2` | enum ∪ {null} | only set if `convergence_grade.status=PASS` | label (L2) | optional |
| `genslm_embed` | array[f32, dim=TBD] | see §4 | feature | optional |
| `label_grade` | enum | {TRAIN,EVAL_ONLY,UNCERTAIN,REJECTED} | gate | yes |
| `path_hash`, `mask_version` | str | — | provenance | yes |

Range constraints enforced as Parquet column statistics + a `validate_joint(df)` function. Until L2 gates pass, every row carries `label_grade ∈ {EVAL_ONLY, UNCERTAIN}`.

**ML split unit (Codex Round 2 fix)**: split by `(sequence_id, run_id)` or `(sequence_id, intermediate)` — **NOT** `(sequence_id, walker_id)`. Walkers within the same MetaD run share the deposited bias and HILLS; they are not independent samples. Splitting at walker level under-estimates generalization error. The previous version (Round 1) had walker-level splits — this is now corrected.

## §6 Function signatures

```python
def collect_metad_run(
    walkers_dir: Path,           # contains HILLS.{i}, COLVAR.{i}
    n_walkers: int = 10,
    burn_in_policy: BurnInPolicy = BurnInPolicy.NONE,  # required to be explicit; was burn_in_ns=10 silent default — fixed per Codex audit. options: FIXED_NS(value), AUTO_S_HIST_PLATEAU, NONE
    sequence_id: str = "WT_PfTrpB",
    intermediate: str = "Ain",
    path_hash: str = "",
    mask_version: str = "v1",
) -> pl.DataFrame:
    """Returns §5 schema with genslm_embed=None and weight_w_t=None.
    Asserts: HILLS.{i}/COLVAR.{i} exist for i in range(n_walkers); time monotonic;
    no NaN in s/z; path_hash matches fes_grid.meta.path_hash."""

def reweight_to_unbiased(
    df: pl.DataFrame,
    biasfactor: float,             # REQUIRED — must come from run metadata, NOT a silent default. Was 15.0 default; Codex Round 2 caught this as a decision-level risk (production run might use different value)
    T: float,                      # REQUIRED — same rationale; from run metadata
    method: str = "tiwary_parrinello_2015",
) -> pl.DataFrame:
    """Adds 'weight_w_t'. Asserts weights finite & positive.

    Two-tier ESS gate (revised per Codex audit 2026-04-25 — original 0.05*N was
    too lax for TRAIN labels):
      - PROVISIONAL floor: ESS_global > 0.05*N (matches original lax gate)
      - TRAIN floor: ESS_per_state > 0.10*N_state for every state in
        {O, PC, C} AND max(w)/sum(w) < 0.01 AND block_ci_max < 1.5 kcal/mol
    On TRAIN-floor fail: tags label_grade='UNCERTAIN' and writes
    reweight_diagnostics.json — does not raise.

    method='tiwary_parrinello_2015' is the canonical default for our setup
    (well-tempered MetaD, biasfactor=15, T=350, ADAPTIVE=DIFF). WHAM and MBAR
    are validation alternatives, not default replacements.
    The actual reweighting math fits behind any estimator with this signature;
    matrix-projection is future work."""

def attach_genslm_embeddings(
    df: pl.DataFrame,
    model_handle: str,           # e.g. "AI-ProteinDesign/GenSLM-TrpB-25M"
    pool: str,                   # REQUIRED (no silent default — Codex audit 2026-04-25); load-bearing per §4 BLOCKED #2; one of {mean, cls, last_token}
    cache_path: Path | None = None,
) -> pl.DataFrame:
    """v0 SPEC ONLY. Adds genslm_embed of shape (dim=TBD); broadcast per
    sequence_id (sequence-level, not per-frame). Caches at
    cache_path/{sequence_id}.{pool}.npy. BLOCKED on §4 (1)&(2);
    raises NotImplementedError until resolved.

    `pool` is required (was `pool='mean'` silent default — Codex caught that
    mean is unverified for the GenSLM-TrpB checkpoint and should not be a
    silent assumption)."""
    raise NotImplementedError("§4 BLOCKED 1, 2 must close first")
```

All three return / mutate `pl.DataFrame`, so they compose:
`attach_genslm_embeddings(reweight_to_unbiased(collect_metad_run(...)))`.

## §7 Open questions for PM

1. Tabular framework: Polars — YES, or pandas — NO?
2. Energy unit canonical: kcal/mol — YES, or kJ/mol — NO?
3. `z` storage: keep raw Å² + derived Å — YES, or only Å — NO?
4. Burn-in: (A) flat 10 ns/walker, (B) adaptive until s-histogram stabilizes, (C) none?
5. Build now with `genslm_embed=null` placeholder — YES, or block on §4 — NO?
6. GenSLM granularity v0: (A) per-sequence, (B) per-residue, (C) both?
7. Reweighting default: (A) Tiwary-Parrinello c(t), (B) Branduardi binless, (C) iterative WHAM?
8. Grid: keep 301×141 — YES, or unify variants on coarser shared grid — NO?
9. CV split unit (revised per Codex Round 2): (A) `(sequence_id, run_id)` — production-run level, walkers within a run NOT independent, (B) `(sequence_id, intermediate)` — only L2-safe across {Ain, Aex1, Q2}, (C) time-block within walker — leakage risk?
10. `state_masks.json` format: (A) bin lists, (B) Shapely polygon, (C) numpy boolean grid?
11. **Activity proxy** for L2/L3 supervised target (added 2026-04-25 per Codex audit — was the highest-leverage missing question; STATE digest §3 also flagged it): (A) Yu's MMPBSA rank, (B) experimental k_cat where available, (C) PM hand-binned activity class? Without this answer, the entire L2/L3 label contract stays blocked.

**Highest leverage** (Codex priority): Q4 burn-in, Q5 build with `genslm_embed=null`, Q7 reweighting estimator, Q11 activity proxy. **Lowest leverage / can be defaulted**: Q1 (default Polars), Q2 (default kcal/mol), Q8 (default 301×141 grid until variants exist).

---

## Errata — Codex independent audit 2026-04-25 (CCB task `20260425-123133`)

Three load-bearing schema bugs caught and fixed in this revision:

1. **`z_path_A2` / `z_path_A` range inversion** (§3.1, §5): had `z_path_A2 ∈ [0, 7.84] Å²` and `z_path_A ∈ [0, 2.8] Å`. The `7.84` came from incorrectly squaring `2.8`. Actual PLUMED grid max is `2.8 Å²` (per `--max 15.5,2.8`), so `z_path_A` max is `√2.8 = 1.673 Å`, not `2.8 Å`. Fixed both rows in §3.1 and §5.

2. **GenSLM token-vs-nucleotide unit confusion** (§4): had "918–1263 codon tokens (306–421 AA × 3 nt / 3 nt-per-token)". The arithmetic 306×3 = 918 / 421×3 = 1263 produces nucleotides, not codon tokens. Each codon token represents 3 nt, so codon-token count = AA count = 306–421. Fixed §4.

3. **`convergence_grade` insufficient structure** (§3.2, §5): was a bare `str` scalar `{PASS, PROVISIONAL, FAIL}`. A status alone cannot let a downstream consumer decide whether a borderline gate is acceptable for their use. Now structured as `{status, reason, ess_min, block_ci_max, max_weight_frac}`. Fixed §3.2; cross-referenced from §5 row.

Other changes (Codex secondary recommendations applied):
- `state_pseudo` enum dropped `pre_O`; replaced with separate `state_reason` provenance string (Codex §1).
- `collect_metad_run` `burn_in_ns=10` silent default → required `burn_in_policy` parameter (Codex §2).
- `reweight_to_unbiased` ESS gate split into PROVISIONAL (`> 0.05*N`) and TRAIN (`per-state > 0.10*N_state` + block CI bound) tiers (Codex §2).
- `attach_genslm_embeddings` `pool='mean'` silent default → required `pool` argument (Codex §2).
- §7 added Q11 (activity proxy) — Codex §5 missing-question.
- §7 added "highest leverage" / "lowest leverage" annotation per Codex §4.

Codex verdict (§8): "block on two fixes before sending to PM: fix the `z_path_A2`/`z_path_A` range inconsistency, and replace '918–1263 codon tokens' with '306–421 codon tokens / 918–1263 nt.' Also change `convergence_grade` from scalar string to structured gate fields. After those edits, STATE+INTERFACE are fit to send as a design draft, with L2/L3 still clearly blocked." — All three fixes applied above; document is now in **fit-to-send** state.
