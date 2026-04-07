# GenSLM Reading Notes: Foundation Model and TrpB Application

> 本文件覆盖两篇论文：
> 1. GenSLM 基础模型论文（Zvyagin et al., IJHPCA 2023）
> 2. GenSLM TrpB 应用论文（Lambert et al., Nat Commun 2026）
>
> NatCommun2026 的完整项目操作清单见 `NatCommun2026_ReadingNotes.md`。本文件重点：基础模型机制 + 两篇论文的连接逻辑。

---

## Paper 1: GenSLM Foundation Model

### Bibliographic Information

| Field | Value |
|-------|-------|
| **Title** | GenSLMs: Genome-scale language models reveal SARS-CoV-2 evolutionary dynamics |
| **Authors** | Zvyagin MT, Brace A, Hippe K, Deng Y, Zhang B, ... Ramanathan A |
| **Venue** | International Journal of High Performance Computing Applications (IJHPCA) |
| **Year** | 2023 (Vol. 37, No. 6) |
| **DOI** | 10.1177/10943420231201154 |
| **bioRxiv preprint** | 10.1101/2022.10.10.511571 |
| **PubMed ID** | 36451881 |
| **Lab** | Ramanathan Lab, Argonne National Laboratory + Caltech (Anandkumar) |

---

### What Problem It Solves

Traditional genome surveillance for pandemic viruses (SARS-CoV-2) relies on phylogenetic methods that compare sequences to known reference trees. These approaches are reactive: they classify variants only after sufficient sequences have accumulated and after human experts define lineage criteria (e.g., Pango nomenclature). They cannot anticipate which mutations will prove functionally important or predict whether a new variant has pandemic potential before it spreads.

GenSLM reframes this as a representation-learning problem: if a language model is pretrained on the evolutionary logic of biological sequences at the DNA/codon level, its learned latent space should reflect functional relationships, evolutionary pressures, and fitness constraints — not just sequence similarity. The goal is a foundation model that can, without explicit supervision, separate variants of concern from neutral background variation.

---

### Method Summary

**Core architecture:**
- Tokenization: codon-level (3 nucleotides = 1 token; 64 codons cover the 20 standard amino acids + stop codons). This is a critical design choice — it preserves the reading frame and genetic code structure, unlike nucleotide-level or amino-acid-level tokenization.
- Base model: GPT-style autoregressive transformer (GPT-NeoX family). Multiple model scales were trained: 25M → 2.5B → 25B parameters.
- Hierarchical extension: for whole-genome sequences (SARS-CoV-2 genome ~30 kb = ~10,000 codons), a diffusion model was added at the top level to handle long-range genome context, while the bottom-level transformer operates on individual gene subsequences.

**Pretraining:**
- Dataset: >110 million prokaryotic gene sequences from BV-BRC (Bacterial and Viral Bioinformatics Resource Center)
- Maximum sequence length: 2,048 tokens (prokaryotic pretraining), extended to 10,240 tokens for SARS-CoV-2 fine-tuning
- Compute: training runs utilized 1.63 Zettaflops; sustained 121 PFLOPS (mixed precision), peak 850 PFLOPS on GPU supercomputers and AI accelerators (Argonne ALCF Polaris, Cerebras)

**Fine-tuning:**
- Dataset: 1.5 million SARS-CoV-2 whole-genome sequences
- Objective: causal language modeling (next-codon prediction); no explicit variant labels used during fine-tuning

**Downstream evaluation:**
- Task: predict whether a new variant is a variant of concern (VOC) before it is formally classified
- Method: extract embeddings from the fine-tuned model, cluster in latent space
- Key test: train on variants observed Dec 2019 – Dec 2020 (Alpha, Beta), then evaluate on unseen variants from Jan 2021 – Apr 2022 (Delta, Omicron, Iota)

---

### Key Results

| Result | Detail |
|--------|--------|
| **Prospective VOC identification** | GenSLM correctly separated Delta, Omicron, and Iota from background variants using only embeddings from a model trained on pre-2021 data — without explicit VOC labels |
| **Latent space structure** | UMAP projections of genome embeddings show biologically meaningful clustering: lineages (Alpha/Beta/Delta/Omicron) separate cleanly |
| **Generalization** | Model trained on early pandemic data identifies future variants it has never seen — the latent space captures evolutionary fitness landscape, not memorized sequences |
| **Scale** | Largest biologically-trained codon LLM at time of publication: 25B parameters |
| **Computational achievement** | Training runs at 1.63 Zettaflops; one of the first genome-scale foundation models demonstrated on supercomputing infrastructure |

---

### Connection to TrpB Pipeline

GenSLM was primarily developed for viral genomics, but its architecture has a key property that transfers to protein engineering: it operates at the **DNA/codon level, not the amino-acid level**. This distinction matters:

1. Codon bias encodes expression efficiency in the host organism (E. coli vs. thermophiles)
2. Synonymous codon variation captures population-level sequence diversity not visible in protein sequences
3. The model learns correlations across the full reading frame, not just within the protein fold

In the Ramanathan/Anandkumar pipeline, GenSLM is the **sequence generator**:

```
GenSLM (DNA-level PLM)
  → generates novel TrpB nucleotide sequences
  → filter (length, start codon, ESMFold pLDDT, sequence identity)
  → express in E. coli, measure activity
  → MetaDynamics FEL analysis [← this project]
  → reward signal back to model (future direction)
```

The model's pretraining on 110M prokaryotic genes means it has implicitly learned what a "valid gene" looks like in terms of codon usage, open reading frame structure, and sequence constraints — before ever seeing a TrpB sequence. Fine-tuning on ~30,000 trpB DNA sequences then specializes it.

---

## Paper 2: GenSLM TrpB Application

### Bibliographic Information

| Field | Value |
|-------|-------|
| **Title** | Sequence-based generative AI design of versatile tryptophan synthases |
| **Authors** | Lambert T, Tavakoli A, Dharuman G, Yang J, Bhethanabotla V, Kaur S, Hill M, Ramanathan A, Anandkumar A, Arnold FH |
| **Venue** | Nature Communications |
| **Year** | 2026 (Vol. 17, Article 1680) |
| **DOI** | 10.1038/s41467-026-68384-6 |
| **bioRxiv preprint** | 10.1101/2025.08.30.673177 |
| **Corresponding author** | Frances H. Arnold (Caltech) |
| **Key institutions** | Caltech, Argonne National Laboratory (Ramanathan Lab / Anima Lab) |

---

### What Problem It Solves

Directed evolution (DE) — the gold standard for enzyme engineering — requires a starting enzyme with measurable activity on the target substrate. For novel desired reactions, no such starting point exists. Discovering functional enzymes from scratch requires either exhaustive screening of natural diversity or rational design, both of which are slow.

This paper asks: can a generative language model trained on DNA sequences produce novel TrpB enzymes that are **functional out of the box**, with no DE rounds required? And can those enzymes exceed the performance of an enzyme that required multiple rounds of laboratory evolution (PfTrpB-0B2)?

---

### Method Summary

**GenSLM fine-tuning on TrpB:**
- Base model: 25M parameter GenSLM (the prokaryote-pretrained checkpoint)
- Fine-tuning dataset: ~30,000 unique trpB nucleotide sequences (corresponding to ~22,800 unique amino acid sequences) sourced from natural sequence databases
- Model size choice: 25M parameters (not the 2.5B or 25B variants) — sufficient for the TrpB task and computationally tractable

**Generation:**
- 60,000 TrpB sequences generated by the fine-tuned model
- Autoregressive sampling starting from ATG codon (start-token filter applied first)

**Multi-stage filtering pipeline (applied hierarchically, cheap filters first):**

| Filter Step | Criterion | Rationale |
|------------|-----------|-----------|
| Start-token filter | Must begin with ATG (Met) | Autoregressive models; first token governs downstream quality |
| Length filter | Within 2 standard deviations of natural TrpB mean (363.6 ± 57.9 AA) | Exclude truncated/extended sequences |
| Sequence identity filter | Balance novelty vs. functionality; exclude trivial copies of training data | Design goal: access unexplored sequence space |
| ESMFold pLDDT filter | Average pLDDT ≥ 80 | Structural confidence; only keep sequences with well-predicted folds |

After filtering: a small set of candidates synthesized by gene synthesis (Twist Bioscience) and expressed in E. coli.

**Experimental validation:**
- Expression in E. coli (soluble protein)
- Activity assays: L-serine + indole → L-tryptophan (native reaction, stand-alone, no TrpA)
- Substrate promiscuity panel: non-canonical nucleophiles and electrophiles
- Temperature range: room temperature and 75°C (thermophilic enzyme benchmark)
- Comparison benchmarks: wild-type PfTrpB, PfTrpB-0B2 (Arnold lab's 6-mutation DE variant), NdTrpB (closest natural homolog to best generated enzyme)

---

### Key Results

| Result | Quantitative Detail |
|--------|---------------------|
| **Activity exceeding DE standard** | GenSLM-230 (the most active generated TrpB) activity exceeds PfTrpB-0B2 — a variant that required multiple directed evolution rounds |
| **Stand-alone activity without TrpA** | Generated TrpBs active without TrpA partner subunit activation — recapitulating the property that required DE to achieve in natural TrpBs |
| **Substrate promiscuity** | Many GenSLM-TrpBs accepted non-canonical substrates; some outperformed wild-type TrpBs on non-native substrates |
| **Thermostability** | 7+ generated enzymes retained substantial activity at 75°C, despite thermostability not being an explicit design target |
| **Sequence novelty** | Most active variants at 80–90% sequence identity to closest natural TrpB; some at 70–80% identity — genuinely novel, not trivial mutations |
| **NdTrpB comparison** | GenSLM-230 shares ~80.5% identity with NdTrpB (*Neobacillus drentensis*); comparison confirms GenSLM-230's enhanced versatility is absent from this natural homolog |
| **Creative potential** | The model generates properties (substrate promiscuity, stand-alone activity) not present in the closest natural sequences — the model is not just interpolating known sequences |

---

### Connection to TrpB Pipeline

This paper is the **direct upstream source** for the MD simulation work:

```
Lambert et al. 2026 (this paper)
  output: GenSLM-TrpB sequences (especially GenSLM-230)
  
→ Zhenpeng's project:
  input: GenSLM-230 sequence
  task: homology model → system build → MetaDynamics
  question: does GenSLM-230 spontaneously access the COMM-closed conformation
            that Osuna 2019 showed is required for stand-alone TrpB activity?
  
→ Downstream (future work):
  output: FEL reward signals → retrain GenSLM
```

The paper explicitly does **not** explain the conformational dynamics basis for GenSLM-230's activity. That gap is precisely what MetaDynamics can fill.

---

## Pipeline Integration: How GenSLM Fits the Ramanathan/Anima Lab Workflow

The Ramanathan Lab (Argonne / Caltech) appears to be building a full AI-driven enzyme design pipeline. Based on these two papers and related work, the pipeline looks like:

```
Stage 1: Generation (sequence space)
  GenSLM (DNA-level PLM, codon tokenization)
  Fine-tuned on target enzyme family (e.g., trpB sequences)
  Generates: novel nucleotide sequences
  
Stage 2: Filtering (in silico screening)
  Start-token, length, sequence-identity filters (cheap)
  ESMFold / AlphaFold2 structure prediction + pLDDT threshold (expensive)
  Output: ~50–200 candidates for synthesis
  
Stage 3: Experimental validation
  Gene synthesis (Twist Bioscience)
  E. coli expression
  Activity + substrate promiscuity assays
  Output: hit rate, ranked candidates

Stage 4: Structural/dynamics analysis [← this project's role]
  Homology modeling of active variants (vs. crystal structures 5DVZ, 5DW0, 5DW3)
  MetaDynamics with path CV (COMM domain O→C)
  Free energy landscape: which variants recover the allosteric-driven ensemble?
  Output: FEL reward signals (ΔG_closed, barrier height, K82-Q2 distance)

Stage 5: Reward-guided generation (future)
  RL or fine-tuning of GenSLM with FEL-derived reward
  GRPO / MFBO for multi-objective optimization
  Iterate: better sequences → lower MD barrier → higher activity
```

**What GenSLM adds vs. standard amino-acid PLMs (ESM-2, ProtTrans):**

| Feature | GenSLM | ESM-2 / ProtTrans |
|---------|--------|-------------------|
| Tokenization level | DNA / codon | Amino acid |
| Codon bias (expression) | Captured implicitly | Not captured |
| Training data | Prokaryotic genomes | Protein sequences (UniRef) |
| Generation target | Nucleotide sequence | Protein sequence |
| Generative model | Autoregressive GPT | Masked LM (ESM) or autoregressive (some) |
| Genome-scale context | Hierarchical diffusion + transformer | Not applicable |

The codon-level training is the key innovation for TrpB enzyme design: it gives GenSLM information about expression efficiency (codon usage) that amino-acid-level PLMs cannot access.

---

## Open Questions for This Project

1. **Does GenSLM-230's conformation match the active ensemble?**
   - Osuna 2019 shows that COMM-closed conformation is required for stand-alone TrpB activity
   - GenSLM-230 is active without TrpA → does it spontaneously close?
   - This is the core MetaDynamics question

2. **What's the FEL difference between GenSLM-230 and NdTrpB?**
   - NdTrpB shares 80.5% identity but lacks GenSLM-230's enhanced versatility
   - Side-by-side MetaDynamics would quantify whether the FEL difference explains activity difference

3. **Why does codon-level training outperform AA-level PLMs for this task?**
   - Lambert et al. 2026 doesn't show a formal ablation comparing GenSLM to ESM-2 at the same scale
   - For the TrpB project: is the advantage from codon bias, longer-range correlations, or pretraining data diversity?

4. **What filter contributes most to hit rate?**
   - The multi-stage filtering pipeline is described qualitatively
   - No breakdown of how many sequences survive each filter stage or hit rate per filter level is reported in public summaries

---

## Cross-Paper Summary Table

| Dimension | Zvyagin et al. 2023 (GenSLM) | Lambert et al. 2026 (GenSLM TrpB) |
|-----------|------------------------------|-------------------------------------|
| **Primary goal** | Pandemic variant surveillance | Novel enzyme design |
| **Model size used** | 2.5B / 25B (full-genome tasks) | 25M (TrpB fine-tuning) |
| **Training data** | 110M prokaryotic genes + 1.5M SARS-CoV-2 genomes | 30,000 trpB nucleotide sequences |
| **Key technical innovation** | Codon tokenization + hierarchical genome-scale architecture | Fine-tuning GPT on DNA for protein generation + multi-stage filter |
| **Demonstrated result** | Prospective VOC identification before formal classification | Generated TrpBs exceeding directed-evolution standard |
| **Relevance to this project** | Architecture and pretraining that makes Paper 2 possible | Provides the GenSLM-TrpB sequences to simulate |

---

**Last updated: 2026-04-05**

**Sources:**
- GenSLM (Zvyagin 2023): https://pmc.ncbi.nlm.nih.gov/articles/PMC9709791/
- GenSLM TrpB (Lambert 2026): https://www.nature.com/articles/s41467-026-68384-6
- Lambert et al. bioRxiv preprint: https://www.biorxiv.org/content/10.1101/2025.08.30.673177v1
- GenSLM GitHub: https://github.com/ramanathanlab/genslm
