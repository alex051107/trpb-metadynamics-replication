# Reading Notes: GRPO / ProtRL + MFBO for Protein Engineering

> **Purpose**: These notes connect two methodological pillars of the Ramanathan Lab's next-generation TrpB pipeline:
> 1. **GRPO** — RL-based fine-tuning of the sequence generator (GenSLM)
> 2. **MFBO** — Coordinating cheap vs. expensive fitness evaluations across F0/F1/F2 tiers

---

## Paper 1: GRPO Applied to Protein Language Models

### Bibliographic Info

| Field | Value |
|-------|-------|
| **Title** | From Supervision to Exploration: What Does Protein Language Model Learn During Reinforcement Learning? |
| **arXiv** | 2510.01571 |
| **Year** | 2025 (submitted October 2025) |
| **Authors** | Hanqun Cao, Hongrui Zhang, Junde Xu, Zhou Zhang, Lingdong Shen, Minghao Sun, Ge Liu, Jinbo Xu, Wu-Jun Li, Jinren Ni, Cesar de la Fuente-Nunez, Tianfan Fu, Yejin Choi, Pheng-Ann Heng, Fang Wu |
| **Venue** | arXiv preprint |

### What Problem Does It Solve?

Protein language models (PLMs) learn from supervised pretraining on natural sequences. This confines their output to distributions seen in evolution. The core question: **can RL push PLMs beyond their pretraining priors** to discover sequence-structure-function rules not encoded in natural sequence databases?

The problem is practically urgent for engineering: directed evolution explores a tiny neighborhood; PLMs can sample broadly but without fitness guidance. RL provides that guidance.

### Method: GRPO for Protein Design

#### GRPO Algorithm (Group Relative Policy Optimization)

GRPO was originally proposed by DeepSeekMath for LLM reasoning. The key innovation over PPO is **elimination of the critic/value model**.

**Core algorithm:**

```
For each prompt (protein context):
  1. Sample G completions (sequences) from current policy π_θ
  2. Score each with reward function r_i
  3. Compute group advantage:
       A_i = (r_i - mean(r)) / (std(r) + ε)
  4. Update policy with clipped surrogate loss:
       L = min(A_i × π_θ/π_ref, A_i × clip(π_θ/π_ref, 1-ε, 1+ε))
     + β × KL(π_θ || π_ref)
```

**Key differences from PPO:**
- No separate value network → reduces GPU memory by ~50%
- Advantage is computed relative to the group mean, not a learned baseline
- KL divergence is added as a penalty term (not subtracted from reward)
- Typically requires 8–64 samples per prompt (group size G)

**Key differences from DPO:**
- DPO requires preference pairs (winner/loser); GRPO only needs scalar rewards
- GRPO is more flexible: works with any scoring function (classifier, physics oracle, etc.)
- GRPO showed superior exploration via its "group loss mechanism, which emphasizes high-reward samples"

#### Reward Functions Tested

| Task | Reward Signal |
|------|--------------|
| Antimicrobial peptide (AMP) | `R(s) = 2·(f_MIC(s) − 0.4)` where f_MIC is ApexMIC binary classifier |
| Kinase variant optimization | Experimentally measured fitness values from dataset |
| Antibody engineering | ΔΔG binding affinity (ProtAttBA model) |
| Inverse folding | TM-score vs. native structure |

#### Multi-Round Iterative Refinement

RL fine-tuning is not one-shot. Reference weights are refreshed progressively across rounds. This prevents mode collapse and keeps exploration active.

### Key Results

**Central finding — three-factor interaction:**
> Task headroom × Reward fidelity × Policy capacity → jointly determine RL gains

| Factor | Meaning | Impact |
|--------|---------|--------|
| Task headroom | How much better can you get beyond supervised baseline? | High headroom → large RL gains |
| Reward fidelity | Is the reward signal accurate / low-noise? | Noisy rewards cap improvements regardless of headroom |
| Policy capacity | Is the model large enough to learn new patterns? | Small models hit capacity ceilings |

**GRPO-specific results:**
- In AMP design: GRPO outperformed PPO and DPO; ESR (Expansion-Shrinkage Ratio) = 0.14, indicating focused, targeted exploration
- In kinase mutation: ESR = 0.08 (very tight focus on high-fitness regions; less diversity)
- In antibody: ESR = 0.50 (mixed results; some knowledge loss)
- General: "RL reliably improves sampling efficiency across domains"

**ESR metric (Expansion-Shrinkage Ratio):**
- ESR > 0: model expanded into new sequence regions
- ESR < 1: model focused/contracted relative to pretraining
- GRPO's low ESR in AMP/kinase = surgical focus on high-reward regions, not random exploration

### Connection to TrpB Pipeline

This paper is **directly applicable** to Raswanth's plan to train GenSLM with RL rewards:

1. **GRPO is the right algorithm**: No critic model needed → practical for large genome-scale PLMs like GenSLM. The group-relative advantage is memory-efficient.

2. **Reward design is the critical bottleneck**: The paper's central finding maps directly to the F0/F1/F2 evaluation tiers:
   - Low-fidelity rewards (F0: PLACER sequence scoring) → fast but potentially noisy → risk of capping RL gains
   - High-fidelity rewards (F1: MD + binding energy) → accurate but expensive → ideal for reward signal, but slow
   - The GRPO training loop should use F1 rewards where possible; F0 rewards only for initial coarse exploration

3. **Three-factor framework as pipeline design guide**:
   - *Task headroom*: TrpB non-native substrate activity is far from natural sequences → high headroom expected
   - *Reward fidelity*: Our F1 MetaDynamics + binding energy is high-fidelity → favorable
   - *Policy capacity*: GenSLM is genome-scale → sufficient capacity

4. **ESR as diversity monitor**: Track ESR during GRPO training to ensure GenSLM doesn't collapse to a narrow high-fitness mode. The paper's antibody case (ESR=0.50) shows knowledge loss is a real risk.

### What We Can Use

- Use GRPO (not PPO/DPO) for GenSLM RL fine-tuning: memory-efficient, no critic model, works with scalar fitness rewards
- Reward function design: `R(s) = normalize(fitness_score - baseline)` following their AMP formulation
- Monitor ESR to detect if GenSLM is losing diversity during RL training
- Expect: 3-factor interaction means reward fidelity matters more than algorithm choice → prioritize F1 (MD-derived) rewards over F0 (PLACER-only) rewards for the RL signal

---

## Paper 2: Multi-Fidelity Bayesian Optimization for Protein Engineering

### Bibliographic Info

| Field | Value |
|-------|-------|
| **Title** | Protein engineering via Bayesian optimization-guided evolutionary algorithm and robotic experiments |
| **Journal** | Briefings in Bioinformatics |
| **Volume/Issue** | 24(1), January 2023 |
| **DOI** | 10.1093/bib/bbac570 |
| **PubMed** | 36562723 |
| **Authors** | Ruyun Hu, Lihao Fu, Yongcan Chen, Junyu Chen, Yu Qiao, Tong Si |

> **Note on scope**: This paper is the primary 2023 *Briefings in Bioinformatics* MFBO-adjacent paper. It focuses on **Bayesian optimization guided by evolutionary algorithm** (BO-EVO) with robotic experiments, rather than a full multi-fidelity stack (F0/F1/F2). The F0/F1/F2 multi-fidelity framework described in the task context represents the **Ramanathan Lab's own pipeline design** informed by MFBO best practices. See supplementary notes below for the broader MFBO theory.

### What Problem Does It Solve?

Directed evolution requires exhaustive experimental screening — infeasible for large combinatorial libraries. The core challenge: how to find high-fitness protein variants in a vast sequence space (e.g., 160,000 possible variants) using only ~1% of experimental budget?

**BO-EVO answer**: Use Gaussian process surrogate model to predict fitness across the landscape, then use evolutionary algorithm to generate candidate sequences biased toward predicted high-fitness regions.

### Method: BO-EVO Framework

#### Surrogate Model

- **Gaussian Process Regression (GPR)** as the probabilistic surrogate
- Input features: protein sequences encoded with **ESM-1v** embeddings
- Output: predicted fitness score + uncertainty estimate
- GPR provides both prediction and confidence interval → enables principled exploration-exploitation tradeoff

#### Acquisition Function

Upper Confidence Bound (UCB):
```
UCB(x) = μ(x) + κ·σ(x)
```
where:
- μ(x) = GP mean prediction (exploitation)
- σ(x) = GP uncertainty (exploration)
- κ = tradeoff parameter

UCB is "optimistic in the face of uncertainty" — it prioritizes sequences with high predicted fitness OR high uncertainty.

#### Evolutionary Algorithm Integration

Rather than exhaustive enumeration, the method generates candidates via single-point mutation on parent sequences. This:
- Restricts search to evolutionary-plausible neighbors
- Avoids non-functional sequence combinations
- Enables batched evaluation (384 variants per round)

#### Experimental Loop

```
Round 1: Initial library → robotic assay → GPR training
Round 2-4: UCB-guided mutation → batch eval → GPR update
```

Four rounds, 384 variants/round = 1,536 total evaluated (< 1% of 160,000 possible)

### Key Results

| Metric | Value |
|--------|-------|
| Success rate on test landscapes | 75% reaching global optima |
| RhlA enzyme improvement | 4.8× improvement in rhamnolipid production specificity |
| Campaign duration | ~1 month |
| Sequence space explored | < 1% of theoretical library |

The approach is validated on:
- GB1 domain (benchmark fitness landscape)
- PhoQ kinase (benchmark)
- NK landscapes (mathematical model)
- RhlA (real enzyme application)

### Multi-Fidelity Extension: How MFBO Works in Theory

> The following draws on MFBO literature that informs the Ramanathan Lab F0/F1/F2 design.

Standard BO evaluates all candidates at the same (expensive) fidelity. **Multi-fidelity BO** introduces a hierarchy of evaluators:

#### Fidelity Levels

| Level | Evaluator | Cost | Accuracy |
|-------|-----------|------|----------|
| l₀ (low) | Fast sequence-level predictor | Seconds | Coarse |
| l₁ (medium) | Physics-based simulation | Hours | Moderate |
| l₂ (high) | Expensive quantum/FEP calculation | Days | High |

#### Multi-Fidelity GP Surrogate

The GP kernel is extended to include a fidelity dimension:
```
k((x,l), (x',l')) = k_input(x,x') × k_fidelity(l,l')
```

This allows information from cheap (l₀) evaluations to inform predictions at expensive (l₂) fidelity.

#### Multi-Fidelity Acquisition Function

```
acqf_MF(x, l) = acqf_standard(x) / cost(l)
```

This normalizes the expected improvement by evaluation cost — so a medium-fidelity evaluation that gives 80% of the information at 10% of the cost is preferred until high-fidelity data is truly needed.

**Key insight**: The acquisition function decides *both* which sequence to evaluate AND at which fidelity level.

#### Practical Coordination Strategy

```
Stage 1: Evaluate many sequences at l₀ (PLACER/sequence scoring)
         → identify top-N candidates cheaply

Stage 2: Evaluate top-N at l₁ (MD + binding energy)
         → refine predictions with physics

Stage 3: Evaluate top-k at l₂ (EVB/QM-MM)
         → high-confidence fitness for final candidates
```

This "funnel" approach reduces expensive l₂ evaluations by 10–100× compared to flat evaluation.

### Connection to TrpB Pipeline

The F0/F1/F2 pipeline in the Ramanathan Lab maps directly to MFBO theory:

| Lab Tier | Tool | MFBO Level | Role in BO |
|----------|------|-----------|------------|
| F0 | PLACER (sequence scoring) | l₀ | Cheap acquisition: screen thousands of GenSLM sequences |
| F1 | MetaDynamics + binding energy | l₁ | Medium acquisition: validate conformational fitness |
| F2 | EVB / QM-MM | l₂ | Expensive acquisition: confirm catalytic barrier |

**Our MetaDynamics work feeds F1**: The conformational dynamics from well-tempered MetaD (current job 41514529) provides the COMM domain O→C transition probability — a key component of F1 fitness scoring.

**What MFBO adds over naive filtering:**
- Instead of simply discarding F0 rejects, MFBO uses l₀ data to update the GP surrogate
- F0 near-misses inform where in sequence space to explore next
- Uncertainty from F0 scores can justify sending borderline sequences to F1 for disambiguation

**Acquisition function implication for GenSLM training:**
- GRPO reward at F0: fast but should be weighted by uncertainty (high-variance F0 predictions → worth F1 evaluation)
- GRPO reward at F1: authoritative → use as primary training signal
- MFBO and GRPO are complementary: MFBO decides *what to evaluate*; GRPO decides *how to update the generator*

### What We Can Use

- Adopt BO-EVO batched evaluation strategy: generate 200–500 GenSLM sequences per round, evaluate at F0, select top ~50 for F1
- Use UCB acquisition: prefer sequences with high predicted fitness OR high uncertainty (unexplored regions of sequence space)
- Track per-round F1 fitness distribution to monitor BO convergence
- The ESM-1v encoding used in BO-EVO should be compatible with GenSLM output analysis
- Cost-normalized acquisition (`acqf / cost(l)`) justifies our current single-walker MetaD as a cost-efficient F1 evaluator before committing to multi-walker or EVB campaigns

---

## Cross-Paper Synthesis: How GRPO + MFBO Work Together

```
GenSLM (sequence generator)
    │
    ▼ sample G sequences per prompt (GRPO group)
    │
    ├─── F0 eval (PLACER) ──→ fast scalar reward r_i^F0
    │         │
    │         ▼ MFBO: select uncertain/promising subset
    │
    ├─── F1 eval (MetaD + ΔΔG) ──→ physics-based reward r_i^F1
    │         │
    │         ▼ MFBO: select top candidates
    │
    └─── F2 eval (EVB) ──→ high-fidelity reward r_i^F2
                │
                ▼
GRPO update: A_i = (r_i - mean(r)) / std(r)
             → reinforce sequences with above-average fitness
             → update GenSLM policy weights
```

**Key tension to manage**: GRPO + MFBO interact through reward fidelity. If GRPO is trained primarily on F0 rewards (noisy), the three-factor model predicts gains will be capped. F1 rewards are more accurate but expensive — MFBO's job is to make F1 evaluations as strategically targeted as possible.

**Practical recommendation for Raswanth's RL training**:
1. Pre-screen with F0 (PLACER) for feasibility
2. Use F1 (MetaD-derived conformational fitness) as the GRPO reward signal
3. Run MFBO to decide which sequences get elevated to F2 (EVB)
4. Monitor ESR to ensure GenSLM doesn't collapse to narrow mode

---

## Open Questions / What Still Needs Work

1. **Reward normalization**: GRPO requires scalar rewards. How to combine F0 + F1 into a single reward `r_i = α·r_F0 + (1-α)·r_F1`? What is the right α?

2. **ESR measurement protocol**: ESR is defined in the paper but implementation details are not given. Need to operationalize this metric for GenSLM's codon-level token space.

3. **MFBO with GP on protein sequences**: Standard GPs scale as O(N³) in data points. With thousands of F0 evaluations, this may require sparse GP approximations.

4. **F0 noise characterization**: How accurate is PLACER for TrpB sequences outside the natural distribution? If F0 reward is highly noisy for GenSLM-generated sequences, consider using it only for hard filtering (not as RL reward).

5. **Multi-walker MetaD as F1**: Our current single-walker MetaD (job 41514529) produces one FEL. Is one walker sufficient for F1 fitness signal, or is the FEL too noisy for GRPO reward calculation?

---

## Sources

- [arXiv 2510.01571 — From Supervision to Exploration (GRPO/ProtRL)](https://arxiv.org/abs/2510.01571)
- [arXiv 2510.01571 HTML full text](https://arxiv.org/html/2510.01571)
- [adaptyvbio.com — ProtRL Designer Spotlight](https://www.adaptyvbio.com/blog/protrl/)
- [Cameron Wolfe — GRPO Algorithm Explained](https://cameronrwolfe.substack.com/p/grpo)
- [Briefings in Bioinformatics 2023 — BO-EVO (Hu et al.)](https://academic.oup.com/bib/article/24/1/bbac570/6958505)
- [PubMed 36562723 — BO-EVO abstract](https://pubmed.ncbi.nlm.nih.gov/36562723/)
- [arXiv 2410.00544 — Best Practices for MFBO in Materials/Molecular Research](https://arxiv.org/html/2410.00544v1)
- [arXiv 2311.13050 — Multi-Fidelity Bayesian Optimization: A Review](https://arxiv.org/abs/2311.13050)
- [ACS Central Science — MFBO for drug discovery](https://pubs.acs.org/doi/10.1021/acscentsci.4c01991)
- [arXiv 2512.09329 — Self Distillation Fine-Tuning of PLMs (Tavakoli, Murugan, Ramanathan et al.)](https://arxiv.org/abs/2512.09329)
- [Nature Communications 2026 — GenSLM TrpB (Lambert, Tavakoli et al.)](https://www.nature.com/articles/s41467-026-68384-6)
