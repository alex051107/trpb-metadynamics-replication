Raswanth  [上午 10:13]
[@Anima](https://ramanathan-lab.slack.com/team/U04RBNXFSJK) What I am working on? - building **RF-Diffusion-3 → MPNN → RF3** pipeline to generate protein sequences that can scaffold theozyme provided by [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U). This theozyme represents the  **transition state of D-serine → D-tryptophan reaction** ;  **D-external aldimine ** (Plan A), not related to** L-serine** (Plan B).
⸻
From here (from my POV), there are currently  **2 directions for Plan A** , and these are the issues with each:-

**Direction 1: SFT Using RFD3 Data for Fine-Tuning**
*(Implementation CLEAR, Motivation UNCLEAR)*

1. Need to generate ~10,000 backbones for ~100 good sequences. Too little data for SFT => overfitting (Or) sufficient data generated, but lot of time needed to generate it.
2. Reward (Docking) and RFD3 (Motif RMSD) success metrics are Geometric. Catalysis-based metrics NOT a part of the pipeline (SFT and GRPO). How will this pipeline increase the odds of catalysis of generated sequences?

**Direction 2: Analysis of RFD3 Outputs to upgrade current GRPO Reward **
*(Motivation CLEAR, Implementation UNCLEAR)*

1. The goal here is to incorporate both **Catalytic** and **Geometric** metrics/constraints into the reward function by Yu’s MD analysis and RFD3 sequences. On Jan 5th 2026 [@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) suggested analyzing both results trying to come up with sequence based measures + multi level reward (not sure if this refers to the design document or something else). How to do?Not clear. (Discussion can happen after RFD3 seqs are generated, how many required for analysis, not sure ~100 should be a decent amount?)
   ⸻
   **Analysis of Mutation at 104… 298.**
   This part of the work I am an unfamiliar. I haven't been a part of the recent discussions. [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) and Yu know better. （已编辑）

Raswanth  [上午 9:57]
[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) —I was finally able to get the script running cleanly across multiple nodes. I tested it today on the debug queue and it scales nearly ~2× across two nodes (8 gpus). Based on this, running on the prod queue (which is quite small compared to preemptable) with ~10 nodes (40 GPU) for ~3 hours should yield ~2k backbones (hopefully >100 good designs) for the analysis. Before I proceed, I wanted to confirm if it’s okay to run this on the prod with these resources. The alternative is using a preemptible queue, but that's too crowded.

Arvind Ramanathan  [上午 9:58]
yes go for it. Both queues are going to be crowded.

[上午 9:58]

But that's okay

[上午 9:58]

once you submit let me know and i will see if i can boost it

Raswanth  [下午 3:38]
回复了一个消息列:

[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) I was able to generate a 100 good sequences from rfd3. Now we can meet to dicuss it alongside Yu's analyses. Please let me what I need to prep for the discussion.

Yu Zhang  [凌晨 12:47]
Hi all, here is the weekly update:

1. I have finished the remaining MD calculations and analysis using the modified external aldimine geometry, which keeps the H atom unchanged, and swaps the the carboxylate and CH2OH group. After 500 ns, 4 out of 5 replicas flip back to the configuration we have been working with. This suggests that the current working geometry is likely the evolutionarily preferred configuration.
2. I generate two input theozyme geometries for RFD3 calculations. Converting the DFT optimized theozyme model into an RFD3 input PDB file is somewhat time-consuming because the formats differ and we have to manually label residues and atom types. I'm looking into whether there is an existing tool or workflow to streamline this conversion.

* The small theozyme model includes residues within 3Å of PLS and those that form hydrogen bonding interactions with PLS. No constraints were applied during DFT optimization. This model should provide more flexibility for RFD3 runs.
* The other larger theozyme model includes all resiudes within 3Å of PLS, including those without direct hydrogen bonding interactions to better represent the full active site pocket. In DFT optimization, alpha C atoms of all residues were frozen to preserve the MD-derived residue positions, and the H atoms attached to alpha C were fixed to maintain side-chain orientations consistent with the MD simulation. This model can capture the key active site interactions more comprehensively for RFD3.

3. I reviewed the RFD3 code and settings, everything looks good so far.
   Plan for next week:
4. Theozyme model design is essentially complete. Once Raswanth's pipeline is completed, we will proceed with stability and foldability analyses.
5. As discussed earlier this week, Amin is working on mutations at sites 104...298. After docking is finished, we will rank candidates by binding affinity and run MD for the top candidates.

Amin  [晚上 9:09]
Hi Everyone,

As Yu mentioned, the docking is still going on. I had to redo it with the new exhaustiveness parameter to ensure proper docking.
Currently it is at 7091 out of 8000 docking processes. I will have a complete update once it is finished.

I am also adding the XPO to the pipeline (it's a quick addition). Attached is the formula of the XPO. It adds a summation terms of all the samples form the reference policy to the model. It is theoretically proven that XPO encourage more exploration than DPO. （已编辑）

Arvind Ramanathan  [晚上 10:20]
What would be good for the analyses of the generated sequences is how does it fold w/ the D/ L-serine (it shouldn[t recognize L-serine and should recognize D-serine - the score difference will tell us if we are in the right direction). For the sequences we also need to see how the placement of the product may look like after the reaction. For the 100 sequences, I am also interested to see the differences in the diversity of residues seen, and the number of folds exolored.

Anima  [晚上 10:25]
回复了一个消息列:

really good progress. regarding "Converting the DFT optimized theozyme model into an RFD3 input PDB file is somewhat time-consuming" this is where Gemini or Claude can be very effective. can u or [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) give me some prompts and I can see if advanced models I have access to can generate

Arvind Ramanathan  [晚上 10:36]
With Yu's set up, i'd like to see whether we can cluster the sequences into similar active sites and see if the chemistry lines up for catalysis

Raswanth  [下午 1:48]
**Weekly Update**

**1) RF Diffusion 3 – Scaling and Results**
The main bottleneck last week was compute. Generating ~100 *good* backbones requires generating 1000s of candidates, which on a single A100 node would min 1–2 days. The *preempt queue* on Polaris is extremely congested, so waiting on that queue itself could take days.

I worked on scaling the RFD3 pipeline script code to run across multiple nodes because  *prod queue * (multi-node queue) was small. After some initial issues with poor scaling, I was able to see optimal parallelization: on 2 nodes, I observed ~2× backbones processed in same wall time. Based on pilot runs, I estimated that **20 nodes × ~1.5 hours** would be sufficient.

I was able to run this setup for **Both theozymes** Yu shared:

* D-serine external aldimine theozyme
* D-serine external aldimine theozyme + 301 mutation

For each, I now have **123 &106 viable sequences **passing both RMSD thresholds. This brings the effective inference time down from >1 day to ~1.5 hours, which is pretty cool. I also confirmed with the RFD3 author regarding my implementation of **Theozyme-Backbone RMSD** (no implementation on git repo). The filtering criterion aligns with what’s used in the RFD2/RFD3. the **RFD3 pipeline is complete** for future theozyme iterations (I will push the latest updates to repo soon. )

**2) Next Steps**
The next focus will be  **analysis and interpretation to improve GRPO reward** . I will learn *basics* of protein structure analysis so I can independently filter and organize the generated designs, which should make the process faster rather than just dumping all the generated results.
next actions:

* This coming week to go through the RFD3 results and analyse and discuss the candidates based on Arvind's suggestions.
* **Add Theozyme-Backbone RMSD to GRPO reward function.** This metric is used to identify good enzyme designs in both RFD2 & RFD3, it could also be a useful & low-cost signal for GRPO. However, I am not sure if this carries any new information that Docking Scores does not. will dig deeper on this metric.

Amin  [晚上 8:16]
[https://x.com/biologyaidaily/status/2015434506766045498?s=46&amp;t=RwiU4Hc30zkv5s4-flUoUA](https://x.com/biologyaidaily/status/2015434506766045498?s=46&t=RwiU4Hc30zkv5s4-flUoUA)

[](https://x.com/biologyaidaily/status/2015434506766045498?s=46&t=RwiU4Hc30zkv5s4-flUoUA)[Biology+AI Daily (@BiologyAIDaily) on X](https://x.com/biologyaidaily/status/2015434506766045498?s=46&t=RwiU4Hc30zkv5s4-flUoUA)

Protein language models trained on biophysical dynamics inform mutation effects @PNASNews

1. Researchers have developed two novel protein language models, SeqDance and ESMDance, which integrate dynamic biophysical properties derived from molecular dynamics simulations and

X (formerly Twitter)

[https://x.com/biologyaidaily/status/2015434506766045498?s=46&amp;t=RwiU4Hc30zkv5s4-flUoUA](https://x.com/biologyaidaily/status/2015434506766045498?s=46&t=RwiU4Hc30zkv5s4-flUoUA "Biology+AI Daily (@BiologyAIDaily) on X")[](https://x.com/biologyaidaily/status/2015434506766045498?s=46&t=RwiU4Hc30zkv5s4-flUoUA)

Anima  [下午 3:34]
[https://pubs.acs.org/doi/10.1021/acs.jcim.5c02385](https://pubs.acs.org/doi/10.1021/acs.jcim.5c02385)

Anima  [晚上 9:19]
[https://www.pnas.org/doi/10.1073/pnas.2530466123](https://www.pnas.org/doi/10.1073/pnas.2530466123)

Amin  [凌晨 12:50]
The docking results are in.
here is the plot for the first order mutations. There are many strong candidates.
I am working on higher order mutations. I am using mutual information between mutations and binding affinities. Please let me know if you think of better ways to study higher orders.

Amin  [凌晨 12:51]
here is the full result btw

mutated_library_D-AEX2_best_affinities.csv

Receptor

AvgAffinity_kcal/mol

DASPTT

17.43

0CPI0Q

13.37

0RWEI0

30.8

0Q0IT0

4.37

T0FLA0

-3.62

YHYTKY

6.47

ARNHKV

8.8

YFSCNC

3.86

I0WSLY

-8.91

[凌晨 12:54]

the immediate conclusion is that 298 does not like many mutations. Only to D amino acid.

mutation_heatmap.png

[](https://files.slack.com/files-pri/T0105PFBYAZ-F0AC85Y8C72/mutation_heatmap.png)

Anima  [下午 3:22]
[https://arxiv.org/abs/2505.04823](https://arxiv.org/abs/2505.04823)

arXiv.org

[ProteinGuide: On-the-fly property guidance for protein sequence generative models](https://arxiv.org/abs/2505.04823)

Sequence generative models are transforming protein engineering. However, no principled framework exists for conditioning these models on auxiliary information, such as experimental data, without additional training of a generative model. Herein, we present ProteinGuide, a method for such "on-the-fly" conditioning, amenable to a broad class of protein generative models including Masked Language Models (e.g. ESM3), any-order auto-regressive models (e.g. ProteinMPNN) as well as diffusion and flow matching models (e.g. MultiFlow). ProteinGuide stems from our unifying view of these model classes under a single statistical framework. As proof of principle, we perform several in silico experiments…

Anima  [晚上 10:46]
[https://www.science.org/doi/10.1126/science.adv4503](https://www.science.org/doi/10.1126/science.adv4503)

Yu Zhang  [晚上 10:36]
Hi all, here is the weekly update:

1. I have been working with Amin on the mutations of 104-109 and 298 positions and analyzed the results from the mutated library. The mutations are sorted based on computed affinity. Several conclusion can be summarized: (1) Those mutations with extremely unfavorable affinity, typically have large functional groups,  which introduce significant steric repulsion to destabilize the geometry. (2) in the heapmap, we can observe that the mutations with similar score usually have similar geometry or length.
2. I have been running MD for the top 10 candidates (affinity from -9.73 to -9.16). 5 out of 10 have mutations on all 6 positions, 3 out of 10 have mutations on 5 positions, the remaining 2 have mutations on 4 positions.
3. I also found out that, with mutations on only 3 positions, the model can also achieve very good affinity (~ -8.77). Less mutations could possibly maintain similar stability to parent sequence. Therefore, I picked another 3 having 3 mutations and 2 having 4 mutations to run MD. So in total, I'm running 15 MD simulations and only 1 replica for each at this moment. Since there was a storage issue on Caltech HPC, the calculations were killed in error. But now, everything is running smoothly. I will analyze the results once they are done and we should be able to gain some insights about the 104-109 and 298 positions.
4. I have also working with Ranswanth on the filtering criteria for his RFD3 results.

Some random thoughts:
I feel the current model can work well if we only consider steric effect. The generated results can be explained well according to geometry or chain length. However, in some cases, the model increases or decreases the hydrogen bond acceptor or donor without a pattern, for example, all three H, L, N mutation on 108 can give -9.7 score but they all have different electronic property. I think the model either underestimates the electronic effect or maybe even doesn't consider it at all. This might be a potential direction we can pursue. I need to search more literatures.
Plan for next week:

1. I will focus on MD for 104-109 and 298 positions.
2. Keep working with Raswanth on the analysis of RFD3 results.

（已编辑）

Arvind Ramanathan  [凌晨 4:25]
Please analyze the rfd3 results

[凌晨 4:26]

I feel you will have to take into account the electronic effects on the step to assimilate the results better both for binding and catalysis

Anima  [下午 3:53]
[@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) when u say "I think the model either underestimates the electronic effect or maybe even doesn't consider it at all." which model are u referring to? what are some solutions for that

Anima  [下午 4:26]
[https://arxiv.org/abs/2511.22311](https://arxiv.org/abs/2511.22311)

arXiv.org

[Swarms of Large Language Model Agents for Protein Sequence Design with Experimental Validation](https://arxiv.org/abs/2511.22311)

Designing proteins de novo with tailored structural, physicochemical, and functional properties remains a grand challenge in biotechnology, medicine, and materials science, due to the vastness of sequence space and the complex coupling between sequence, structure, and function. Current state-of-the-art generative methods, such as protein language models (PLMs) and diffusion-based architectures, often require extensive fine-tuning, task-specific data, or model reconfiguration to support objective-directed design, thereby limiting their flexibility and scalability. To overcome these limitations, we present a decentralized, agent-based framework inspired by swarm intelligence for de novo protei…

Raswanth  [下午 4:47]
**Last Week Update**
All results were done on 2 Theozymes -
*D-serine Theozyme (T1) & 301 mutated D-serine Theozy*me (T2)

**1) Motif RMSD threshold (1.5 Å)**

* I tried to find the **origin/basis** for the **catalytic-motif RMSD < 1.5 Å** cutoff.
* I checked the RFD2 + RFD3 papers, but couldn’t find an explicit rationale (seems empirical).
* I pinged the authors asking for the basis; no response yet.

**2) RFD3 design setup**

* I discussed with Yu to get an idea of where to start with the analysis

pLDDT Filter:

* All filtered sequences show  **RF3 pLDDT ~0.79–0.8+** , i.e., in the “good confidence” regime. For T1 & T2.

**3) Structural diversity (global)**
I computed **pairwise TM-align** across all filtered designs (TM-score is length-normalized, unlike RMSD), then did  **PCA + clustering** .

* Main observation:  **most clusters are singletons** , suggesting **high global global topology diversity** in generated sequences (both T1 & T2).
* PCA plots + cluster counts are included in the attached PDF. **(Pg - 1) **

**4) Active-site / binding-site analysis (local)**
*Definition:* active site = residues with any non-hyd atom  **within 4 Å of the ligand atoms** .
**A. Do theozyme residues appear in the active site? (Pg - 2,3)**
I measured overlap between:
Theozyme residue-set (A) vs. active-site residue-set (B) (How similar are the types of residues in Theozyme & residues in the active-site? Any theozyme residues key to the active site?)

* Theozyme residues positions (A) vs. active-site residue *positions (B) (How many of the theozyme residues are actually being used in the active site?)*
* Using Jaccard (|A∩B| / |A∪B|):
* **Identity overlap is highly variable** - The type of residues used by RFD3 in binding pocket showed NO relation to with the type of residues in Theozyme (except Lysine which was enforced).
* **Positional overlap is high** : in T1 - 12/13 **residues end up forming the 4 Å active site** even if their identities have changed. In T2 only 9/14 were used. 5 residues were almost never a part of the active site (**Pg - 3** to which residues were not useful).

**B. What residue substitutions does RFD3 use for each Theozyme residue? (Pg - 4-14)**
For each Theozyme residue position (except fixed Lys), I looked at what residue it becomes across all designs filtered & unfiltered.
Strong trend:  **Glycine dominates** , then  **Ser/Thr/Ala** .

* Interpretation: these are  **small/flexible residues** , so they’re the easiest “fit”. other people have observed this overuse of Glycine in RFD3 as well.

**5) Conclusions**

1. RFD3 designs have high global structural diversity.
2. Analysis confirms that the Theozyme is being properly scaffolded by the designs.
3. While NO insights were found regarding which residues were useful, insights on which residues in the Theozyme were NOT useful was found.
4. High frequency of GLy >> Ser > Thr > Ala and nearly no exploration of other residue substitutions by RFD3 in the active - suggests that designs prioritize geometry first and not so much chemstry? Not sure how to interpret this.

**6) What’s missing / limitations**

* NO analysis of chemistry/catalysis - Binding Affinity etc.

**7) **Questions/guidance

1. **Next analyses:** beyond TM-align diversity + 4 Å site overlap + substitution statistics, what other analyses would be interesting? Please comment.
2. **Catalytic motif RMSD cutoff:** Is there a known rationale for  **1.5 Å** , or do we treat it as purely empirical? (side quest)
   Any questions or comments on the analysis are welcome.

PDF

[ANALYSIS.pdfPDF](https://ramanathan-lab.slack.com/files/U0AQRESK99R/F0ACMNDURC4/analysis.pdf?origin_team=T0105PFBYAZ&origin_channel=C068HL4259P)

Raswanth  [下午 4:54]
回复了一个消息列:

[@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) a doubt. Shouldnt we also consider the Binding Affinities of L-serine? Aren't good candidates those that are selective toward D-serine but also show low affinity to L-serine ? Or can it have high affinity for both L & D?

Arvind Ramanathan  [下午 4:41]
[https://arxiv.org/pdf/2601.19205](https://arxiv.org/pdf/2601.19205)

Anima  [中午 11:17]
[@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) given that [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) is remote I think you should have a weekly meeting with him and make sure there are no confusions. Ideally [@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) can also join

Anima  [下午 1:30]
[@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) where are your weekly updates?

Amin  [晚上 6:21]
Hi Everyone,

Last week, Yu and I noticed a small but impactful bug in the docking experiment. I fixed it and redo the docking with a slightly shifted center (Suggested by Yu).
The docking are finished now. I am attaching the results for [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) and [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM).
My first observation after fixing the bug, is that 298 is actually a site with most enthusiasm for mutation to let D-serine in. 104 is the least likely one to mutate. Here are the top 20 (0 means no mutation):
`0TW0Y0E`
`0K0000W`
`000CW0W`
`0SH0W0Q`
`0ETSYFR`
`NK0GN0W`
`00Y0LFH`
`LD00R0W`
`0T0000Y`
`0M0G00H`
`TFM0WHS`
`0000NHR`
`00M0I0R`
`0H00Q0R`
`TTLAF0P`
`0WQ000R`
`FNG00TF`
`00A0M0R`
`0C00Q0H`
`VC0000W`

mutated_library_2_D-AEX2_best_affinities.csv

Receptor

AvgAffinity_kcal/mol

HP0G0Q0

-9.94

F0NW00R

-7.54

SI0AAI0

-10.61

000000C

-9.0

0C0W00M

-7.84

SH0TDLQ

-8.67

VA0R0Y0

-9.78

KMVR0DY

-9.13

K00W0R0

-9.04

Anima  [凌晨 12:17]
[https://arxiv.org/abs/2602.03779](https://arxiv.org/abs/2602.03779)

arXiv.org

[Generative AI for Enzyme Design and Biocatalysis](https://arxiv.org/abs/2602.03779)

Sparked by innovations in generative artificial intelligence (AI), the field of protein design has undergone a paradigm shift with an explosion of new models for optimizing existing enzymes or creating them from scratch. After more than one decade of low success rates for computationally designed enzymes, generative AI models are now frequently used for designing proficient enzymes. Here, we provide a comprehensive overview and classification of generative AI models for enzyme design, highlighting models with experimental validation relevant to real-world settings and outlining their respective limitations. We argue that generative AI models now have the maturity to create and optimize enzym…

Anima  [凌晨 12:14]
[https://newscenter.lbl.gov/2026/02/02/foundational-ai-models-to-accelerate-biological-discovery/](https://newscenter.lbl.gov/2026/02/02/foundational-ai-models-to-accelerate-biological-discovery/)

Berkeley Lab News Center

[Foundational AI Models to Accelerate Biological Discovery](https://newscenter.lbl.gov/2026/02/02/foundational-ai-models-to-accelerate-biological-discovery/)

Berkeley Lab is helping build AI models for autonomous research that will enable prediction and precise design of biological systems.

Written by

akovner

Est. reading time

1 minute

2 月 2 日

[https://newscenter.lbl.gov/2026/02/02/foundational-ai-models-to-accelerate-biological-discovery/](https://newscenter.lbl.gov/2026/02/02/foundational-ai-models-to-accelerate-biological-discovery/ "Foundational AI Models to Accelerate Biological Discovery")[](https://newscenter.lbl.gov/2026/02/02/foundational-ai-models-to-accelerate-biological-discovery/)

Yu Zhang  [凌晨 1:13]
Hi all, here is the weekly update:

* The MD calculations for Amin's 104-109 and 298 mutation set from last week have been completed. We identified 15 potential candidates with high binding affinity. Among them, four show strong MMPBSA binding energies (better than -104 kcal/mol). The rest candidates also show negative binding energies, with generally favorable MMPBSA values (-36 to -97 kcal/mol)

Mutations	MMPBSA binding energy
00FII00	        -139.1143
0VYVMTI	-129.0583
0TPEKHP	-106.6961
0PHRKQH	-104.317
0EQLM0V	-97.1188
0N0AYR0	-84.6497
0000KIP	        -83.1355
000EKAS	-63.0316
0TPL00N	-61.8938
000W0ID	-56.7848
0Y0KENC	-55.9584
0FQEKNV	-54.8125
0FK0RIH	-47.5576
0VFVMLI	-36.9903

* I inspected the geometries one by one. A consistent trend is that the newly generated mutations improve binding affinity by strengthening stabilizing interactions. For example, adding additional hydrogen bonds and C-H..π interactions. However, with the current mutation set, the next proton transfer step may be less favorable due to the lack of suitable proton-accepting residues. After discussion with Amin, we think a good next step is to incorporate the Y301K mutation into the 104-109 and 298 mutation pipeline. This approach should help both improve binding affinity and better support the subsequent proton transfer process.
* The MD calculations for the mutations generated this Wednesday are still running. These designs may or may not include residues that can serve as proton acceptors. I will inspect the geometries once the calculations finish.

Plan for next week:

* Finish the current running MD calculations and analyze the results.
* Work with Amin to update the mutation pipeline by incorporating Y301K mutation and inspect geometries prior to MD. If the structures look promising, then proceed with MD for verification.

Amin  [晚上 10:53]
Hi Everyone,

most importantly, I have a added 301 and remove 104 to my docking calculation as 301 mutations need to provide protein-accepting sites. The docking is running for ~6000 variants.

I have calculated the mutual information between mutations at each site and the binding affinities. The results are not obvious to interpret and I am still looking for metrics that might provide insights on the ideal D-handed theozyme.

XPO is added locally and I ran some sanity checks. I will incorporate it to the pipeline now. （已编辑）

Raswanth  [下午 3:23]
**Weekly Update**
I’ve wrapped up the RF diffusion analysis for the theozymes I currently have and I am focusing on the GRPO reward function.

The issue is that incorporating chemistry-aware terms (e.g., QM/MM calculations, activation energy) directly into the GRPO loop is extremely expensive because it can take hours to days. The direction I’m exploring is whether we can  **trade generalizability for compute** —i.e., reduce reliance on heavy calculations by using **tryptophan-synthase–specific mechanistic knowledge** from the literature as lower-cost reward signals.

The way I’m approaching this is **state by state** along the L reaction pathway. There are four key stages (Cα–H deprotonation, OH elimination, indole attack, reprotonation), and I’m trying to understand, for each stage,  *what features of the enzyme/substrate/active site enable the reaction to move to the next stage* , and whether those features can be expressed as low-cost constraints in the GRPO reward.

**Few interesting things I’ve learned:**

* ** Cα–H deprot. step  - Dunathan hypothesis for PLP enzymes (PNAS, +500):** The active site geometry enforces an ~90° angle between the Cα–H bond and the PLP π-system, facilitating Cα–H cleavage via resonance. This step is critical for forming the quinonoid intermediate and seems like a concrete, geometry-based constraint that could potentially be encoded in the reward.
* **OH elimination - Loss of chirality at the planar intermediate:** After Cα–H abstraction, the substrate becomes planar at Cα, meaning the original L/D information is lost. Implying that even if D-serine external aldimine is stabilized as in our theozyme, without controlling the orientation of the planar intermediate quinonoid and the indole attack, the reaction might yield L-tryptophan in the active site instead of D-tryptophan.

**Next steps:**
I am still have quite bit of reading to do and understand to consolidate these ideas, then summarize them (likely as slides) and run them by others with biochemistry expertise to sanity-check the reasoning before attempting any implementation.

Anima  [晚上 6:09]
[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) any thoughts on the updates? Regarding the earlier RFD3 results, [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) did we run with all the mutations that [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) were looking at? what is the output we have now? trying to put all that together before GRPO. I m worried that GRPO on wrong rewards can yield a lot of false positives

Yu Zhang  [凌晨 2:49]
Hi all, here is the weekly update:

1. I have finished all the MD calculations as well as their analysis using Amin generated mutations. We identified 20 potential candidates with high binding affinity. Among them, four show strong MMPBSA binding energies (better than -100 kcal/mol). Seven candidates also show negative binding energies, with generally favorable MMPBSA values (-53 to -90 kcal/mol). The remaining nine candidates show very unfavorable binding preference in MD calculation.
2. For those with unfavorable binding preference, the external aldimine just fly out of active pocket during free MD simulation. Therefore, no binding energy is computed. The steric repulsion is quite obvious during MD. We can definitely add some geometric constrains to enforce external aldimine to stay in the active pocket but I wouldn't expect the results would be good.
3. I have been spending time on analyzing Raswanth's RFD3 results. I looped through all geometries for both basic dserine design and 301K mut designs. Since the residue number has been changed, I looked at all residues within 4Å to the external aldimine. By just analyzing the geometry, although H atoms are not added yet, it looks like the hydrogen bond acceptor and donor have been considered to stabilize the geometry. One concern from me is that although there are several sequences have lysine near the H atom being extracted in the next step, however, most sequences do not have such lysine but rather other amino acids, or lysine is simply not in the correct position.

Plan for next week:

1. All current MD calculations have been finished. I was discussing with Amin on incorporating Y301K mutation into his 104-109/298 mutation generation. We will decide whether MD is needed or not for this set. If so, I will start to work on it.
2. [@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) Do you have any thoughts about the geometries in Raswanth's movie? If you think the lysine position is an issue, we should find a way to enforce its position in RFD3. One possible solution is to constrain the distance (and maybe also dihedral to constrain its direction) between lysine and the H atom being extracted in the next step.
3. I also need to spend some time on SURF proposal.

| **TFM0WHS**`` | **-132.3695**`` |
| -------------------------- | ---------------------------- |
| FNG00TF                    | -126.5061                    |
| 000CW0W                    | -124.5152                    |
| 00Y0LFH                    | -100.7972                    |
| 0T0000Y                    | -90.4526                     |
| 0K0000W                    | -77.2543                     |
| TTLAF0P                    | -59.9833                     |
| NK0GN0W                    | -58.2028                     |
| LD00R0W                    | -56.1474                     |
| 00A0M0R                    | -56.0587                     |

Anima  [下午 1:28]
[@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) where is your weekly update

Arvind Ramanathan  [下午 1:30]
There are quite a few things to discuss

Arvind Ramanathan  [下午 1:30]
Can we
Meet sometime next week say Fri?

Arvind Ramanathan  [下午 1:30]
Am
Traveling the following week and have a couple f meetings at the lab that prevent me from meeting earlier

Amin  [凌晨 12:32]
Hi everyone,

This week, I have added 301 site to the calculations. During structure prediction, I noticed that 301 seems to be a highly sensitive residue. Considering the pLDDT as the property,  301 generates highly epistatic mutations with the other sites leading to super uncertain structures. This is a serious source of noise in our calculations. However, I have filtered out the good ones and the docking is still running for ~9000 variants. I was hoping to get the results to Yu by yesterday, however, I need to wait more for the docking.
Besides that, I have been preparing my job talk (presentation) during the week and will ask everyone for feedback soon.

Raswanth  [下午 3:24]
Weekly Update,

As discussed last week, the focus is to make the  **current GRPO reward more reliable** . Proposed terms (MD-based fold stability, binding free energy, catalytic barrier/QM) in Arvind's design document capture catalysis but are expensive to place directly inside the GRPO loop. The approach I am exploring is to trade generalizability for compute: instead of relying primarily on generic, high-cost physics terms, can we use well-established mechanistic knowledge of TrpB to design cheaper, stage-specific signals that approximate catalysis signals? QM/MM/MD terms could then be reserved for late-stage filtering before wet lab.

Over the past week, I’ve been reviewing literature stage-by-stage for the L-serine → L-tryptophan pathway, identifying what structurally or mechanistically enables each transition, and whether any of those constraints can be translated into low-cost, reliable, quantifiable reward terms. A compiled draft of these candidate signals is attached in the PDF below (first draft). I plan to prepare slides and discuss with everyone on Friday.

**Two questions/insights from the Literature Review:**

**1. Our Theozyme scope and reaction progression**
Current theozyme modeling focuses only on D-serine external, is that enough? the reaction we want is:
**D-serine → D-serine external aldimine → quinonoid → aminoacrylate → D-tryptophan **

A) If we scaffold only the external aldimine TS via DFT-derived theozyme using RFD3, what guarantees that the designed enzymes push the substrate to proceed to quinonoid and aminoacrylate rather than being over-stabilized at the external aldimine state?
B) After deprotonation (D-serine external aldimine → quinonoid), the C-alpha becomes planar (sp2), meaning L/D information in Aldmine is effectively lost. Literature suggests that the face of reprotonation at the tryphtohpan stage determines final stereochemistry. This implies that stabilizing D-serine external aldimine alone does not guarantee D-tryptophan output; orientation control in the other stages is important. [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) is this correct?

2. relevance of Y301
   Interestingly, A UCSB paper on engineered TrpB reports Y301H as a key mutation that prevent the flipping of D to L at the final step. If this position was identified independently, then this might be more support to focus on this 301 mutation? Paper link - [https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2025-32vjk](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2025-32vjk)

PDF

[Stage-wise_proposed reward function design.pdfPDF](https://ramanathan-lab.slack.com/files/U0AQRESK99R/F0AG5GR2KKJ/stage-wise_proposed_reward_function_design.pdf?origin_team=T0105PFBYAZ&origin_channel=C068HL4259P)

Raswanth  [下午 3:32]
回复了一个消息列:

Yes friday works for me.

Arvind Ramanathan  [下午 3:32]
I don;t know how many of you saw the movies that [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) generated. There is quite a bit to unparse there IMO.

Amin  [晚上 7:09]
the new docking results are in with 301 mutated.

mutated_library_3_D-AEX2_best_affinities.csv

Receptor

AvgAffinity_kcal/mol

YY00000

-11.35

00KGQ00

-9.17

RLPTEMT

-9.16

000000C

-11.23

CLT0E0K

-9.17

Q00L0W0

-12.25

IDM0A00

-9.11

0WYTYGS

-9.11

K0QGMLL

-9.55

Yu Zhang  [晚上 11:48]
Hi all, here is the weekly update:
I didn't start any new calculation this week. I mainly focused on analyzing existing results, reading papers and talking with people on projects
I got a chance to talk to Lei Cheng, who is the first author of the paper shared by Raswanth. He recently published another very relevant paper ([https://pubs.acs.org/doi/full/10.1021/jacs.5c16304](https://pubs.acs.org/doi/full/10.1021/jacs.5c16304)). Both papers can prove that our strategy is reasonable that designing a proton donor from the (Re)-face (near 301 position as we identified) should be able to provide D-handness. Their experiment shows that PLP enzyme binding with D-external aldimine should not be a problem.
Another very interesting experimental observation is that by only E104P mutation, they can achieve D-handness but with a very very low selectivity (L:D = 97:3). This is really counterintuitive since to our knowledge, 104 position is only useful in the indole addition step, which should not introduce any chirality. Good news is Amin incorporate 104 position in his mutation generation. Bad news is I built up the E104P mutation geometry but can not identify how it affects the chirality. I think MD is needed here to answer the question. Figuring out this should help us better understand the reaction and our design.
Some unpublished experimental data: single mutations itself on 101-110 positions and 290-300 positions do not have an effect on chirality, which are consistent with our observation from MD, showing those positions only form stabilizing hydrogen bonding interactions to stabilize the whole geometry. Amin's newest docking results could be valuable since we are considering multiple mutations including Y301K mutation. It worths to run MD for the top candidates.
Another useful but may not be important in our project is the substrate tunnel, which delivers the substrate to the active site. Lei identified multiple important positions in his paper but I figured out most of them are mutating substrate tunnel as his reaction needs. Since we are still working on Tryptophan synthase, the substrate tunnel should not be a problem. We are ignoring it all the time but it may be good to point out at this moment.
Other than this, I have been working with SURF student Alex Liu and Amin on NeuralPlexer proposal. I think we already have a complete version of it. Alex is improving it based on our comments. Another SURF proposal is to incorporate electronic effect from OrbitAll in enzymatic generative model as we discussed earlier. Me, Amin and SRUF student Yiyan Liao are currently working on the proposal.
Plan for next week:

1. MD for E104P mutation. The mechanism here is interesting.
2. MD for top candidates from Amin's newest docking results.
3. SURF proposal.

Arvind Ramanathan  [上午 9:15]
Let’s get chatting about this on Monday evening

Amin  [早上 6:36]
This week I’ve done the docking simulations with 301 included. After observing the results, I can see that 301 is highly impactful on the enantio selectivity. Most likely the sequences must have mutations at 301.
Currently, we have this problem of RFD3 generated sequences where the active sites are usually far from the active sites in trpBs (in sequence space).
I’m still thinking of how we can solve this …
We should definitely discuss this during our Monday meeting.
Besides that, Yu and I discussed possible data curation only with MD and not RFD3.
We are also working on the SURF proposals.
I have been also working on preparing my job talk.

Raswanth  [下午 3:59]
回复了一个消息列:

**Weekly Update**
I’m continuing my work on increasing the reliability of the  **GRPO reward** .
Previously, I raised two concerns:

1. **Incomplete pathway modeling.** Neither the current reward nor the theozyme incentivizes designs to follow the full reaction sequence: D-serine → external aldimine → quinonoid → aminoacrylate → product. The theozyme focuses only on the external aldimine, so there are no incentives to produce quinonoid and aminoacrylate, without which getting tryptophan, let alone L/D, is difficult. One reassurance here is that the original TrpB GenSLM's embeddings could remain helpful, because quinonoid → aminoacrylate step is same, irrespective of L or D-serine. But still D-external aldimine → quinonoid and aminoacrylate → D-tryphtophan needs some enforcing.
2. **Reprotonation determines stereochemistry.** Even if we start with D-serine, once the intermediate becomes planar. If the pocket allows sufficient flexibility (e.g., flipping of the planar Cα intermediate), reprotonation could still yield the L-product. With no penalties for L products, a larger pocket is likely favoured and gives no guarantees on output D/L.

Both concerns were validated in discussion with Yu, and analysis of 301 addresses 2 to some extent. 1, however, it still needs to be addressed.

Last to Last week’s design document was entirely based on  **TrpB-specific literature and mechanism analysis** . Last week, I extended the survey to **relatives of TrpB** (EC similarity, overlapping reaction pathways, fold-type similarities, and other PLP-dependent enzymes). The primary motivation is to prevent the model from overfitting to the specific heuristics of TrpB. Instead, the goal is to include only **necessary** **signals to fulfill reaction** (using existing literature/research on TrpB as an alternative to generalizable heavy terms from MD/QM/MM) into GRPO.

Amin  [下午 4:57]
[https://www.arxiv.org/pdf/2602.16634](https://www.arxiv.org/pdf/2602.16634)

Amin  [下午 5:46]
[@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) find the scripts for structural alignment under `/Theozyme/strcutural_alignment` .
Let me know if you get permission errors to my compiled TMAligned. （已编辑）

Anima  [晚上 6:17]
[@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) do you know when precisely Ziqi will be done at Caltech

Arvind Ramanathan  [晚上 9:20]
[https://www.nature.com/articles/s41929-026-01478-y](https://www.nature.com/articles/s41929-026-01478-y)

Nature

[A geometric foundation model for enzyme retrieval with evolutionary insights](https://www.nature.com/articles/s41929-026-01478-y)

Nature Catalysis - Predicting the function of enzymes remains difficult and current computational methods require improvement. Now EnzymeCAGE, a geometric deep learning model, has been developed to...

[https://www.nature.com/articles/s41929-026-01478-y](https://www.nature.com/articles/s41929-026-01478-y "A geometric foundation model for enzyme retrieval with evolutionary insights")[](https://www.nature.com/articles/s41929-026-01478-y)

Anima  [下午 1:04]
Is there a writeup being maintained for ongoing work

Amin  [凌晨 12:16]
Hi Everyone,

This week I've been mainly occupied with my job talk preparation which is almost done. I will share it with you for feedback.
Besides that, Yu and I are discussing the possibilities of identifying and using the most viable candidates generated by RFD3. There are several technical (and minor) issue for data clean up which Yu is handling. Once we can do it automatically, we should run high throughput batches of RFD3. But this only can be done once we identify the most viable Theozyme model -- which is what we are doing now.

Yu Zhang  [凌晨 12:24]
Hi All, here is the weekly update:

1. As we discussed on Monday, I'm running MD for E104P mutation with both L- and D-external aldimine. Then I will compare their electronic structures around active site to investigate the factors affecting the chirality.
2. I have focused on the geometries generated by RFD3. As Arvind suggested, I was trying to identify good candidates and set up MD for them. The strategy I'm using is that (1) having stabilizing interactions between external aldimine and residues (2) no significant steric repulsion anywhere (3) having potential proton acceptor around active site in an appropriate direction to allow the first proton transfer happen. However, here are several hidden errors happening in (almost all) geometries.

* There are duplicate residue numbers in the sequence. All of them are from the theozyme model. For example, there are two 82 in the sequence. One is from theozyme 82 lysine, the other one is generated by RFD3. The 82 lysine from theozyme is overlapping and forming significant steric repulsion with other residues. Such observation happens in all generated sequences. After discussing with Amin, one possible explanation is RFD3 is suggesting a better mutation for those positions and for some reason, the original one is kept in the generated sequence. This should be an easy fix. As long as we delete those duplicate residues, the steric issue should be solved. My concern in this part is whether we really take into account the residues in theozyme model, or just simply fix the geometry/coordinates there. [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) Can you verify it?
* Another error is that heavy atoms are missing. For example, one C is missing in alanine, 5-membered ring is missing in histidine. Basically, side chain of amino acid is missing. This is also an easy fix. Tleap can help to add missing atoms.

The two points mentioned above are happening in almost all sequences. The following two are more specific and I need suggestions:

* In several cases, the atoms in one residue break into different parts and they are super far away from each other. My strategy here is to look at the active site first. If reasonable, then I will try to fix the geometry, otherwise I will just consider it as a bad candidate.
* I also found several geometries having longer than usual (> 2Å) protein bond. Should I just consider it as bad candidate or set up MD for it to hope geometry can be fixed during simulation?

[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) Can you give me some suggestions?
I have also finished the two SURF proposals with students.
Plan for next week:

1. Finish E104P calculation and analyze it
2. Solve the problems for geometries generated by RFD3 asap and set up calculations for good candidates.

Anima  [凌晨 1:53]
[https://x.com/biospace9/status/2028301770770858326?s=46](https://x.com/biospace9/status/2028301770770858326?s=46)

[](https://x.com/biospace9/status/2028301770770858326?s=46)[しんしあ@バイオテクコミュニティ「BioSpace」モデレーター (@BioSpace9) on X](https://x.com/biospace9/status/2028301770770858326?s=46)

Rapid directed evolution guided by protein language models and epistatic interactions

[https://t.co/iBdKXaAdWC](https://t.co/iBdKXaAdWC)

X (formerly Twitter)

Raswanth  [下午 2:05]
**Weekly Update**
Based on last week’s discussion. As suggested, I ran pairwise structural alignment on the two sets of generated CIF files for both the theozymes. The results are attached below. [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U), these should at least help reduce the search space. I have also put the alignment scores in the csv file. I’m also working on using FoldSeek, DALI, and RCSB structural searches to identify structurally similar natural proteins, but I’m currently debugging CIF format issues. Most of this week was spent continuing the literature survey. Not just reading more papers, but trying to answer a more specific question: how far can geometric proxies alone capture catalysis, and when do we necessarily need QM/MM-level calculations? One conceptual shift is recognizing that many of the constraints are likely *necessary* conditions, but not *sufficient *conditions. It is quite difficult to identify sufficient catalytic conditions purely from the literature. I’m also increasingly suspecting that satisfying geometric constraints does not guarantee a valid electronic configuration in quite a few of the cases. So the current line of thinking is: which geometric rules, when enforced in the reward, strongly imply electronically permissible states, and which ones are only weak proxies?

Zip

[struct_aligned_cif.zipZip](https://files.slack.com/files-pri/T0105PFBYAZ-F0AJ5UFFTPE/download/struct_aligned_cif.zip?origin_team=T0105PFBYAZ)

Amin  [下午 4:08]
[@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) do you have the structure of the 3:97 trpB?

Raswanth  [下午 4:53]
回复了一个消息列:

Hi [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) & [@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883),
Following up on the file issues. I’ve addressed the main ones and attached the updated files.
**Updates & Fixes**

* **Residue & NaN errors:** The previous structures were RFD3 backbone-only outputs. I’ve swapped them for RosettaFold3 outputs, which are properly refolded with all side chains. This automatically resolved the last NaN atom issue, but I am still not sure about the starting residue problem.
* **Structure overlap errors:** This was happening because the original Theozyme contents got appended to main pdb file while making the movie. I am fairly sure of it now.

**Missing Gaps (To Monitor)**

* Adding the side chains might naturally resolve the gaps Yu noticed in the structure.
* If gaps persist, it’s the shortcoming of the diffusion model because they are not forced to generate C and N atoms  1.6 Å apart so maybe thats why ?

**Attached Files**

* **ZIP file:** All generated structures for both Theozymes.
* **JSON file:** Mappings of the original Theozyme residues onto the sequence so you can easily locate the catalytic lysine and other key residues, their position in the sequence, and structure for the analysis.

I haven’t visualized these updated structures myself yet. Could you take a look and let me know if this deal addresses the issues you faced earlier? The files are individual, not in movie format, though.

Zip

[fixed_cif_files.zipZip](https://files.slack.com/files-pri/T0105PFBYAZ-F0AJ8P04PLM/download/fixed_cif_files.zip?origin_team=T0105PFBYAZ)

Arvind Ramanathan  [晚上 8:29]
Good

Anima  [晚上 7:57]
[https://research.ibm.com/blog/half-mobius-molecule](https://research.ibm.com/blog/half-mobius-molecule)

IBM Research

[Quantum simulates properties of the first-ever half-Möbius molecule, designed by IBM and researchers](https://research.ibm.com/blog/half-mobius-molecule)

University scientists team up with IBM to engineer the new molecule atom-by-atom in quantum-centric study.

Written by

Peter Hess

Est. reading time

5 minutes

[https://research.ibm.com/blog/half-mobius-molecule](https://research.ibm.com/blog/half-mobius-molecule "Quantum simulates properties of the first-ever half-Möbius molecule, designed by IBM and researchers")[](https://research.ibm.com/blog/half-mobius-molecule)

Raswanth  [上午 10:02]
[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) "qsub: Request rejected.  Reason: No active allocation found for project FoundEpidem and resource polaris." Could I be assigned to a new project so I can access Polaris? I know you're away, so let me know who to reach out to.

Arvind Ramanathan  [上午 10:03]
yeah - i thought i had mentioned earlier can you please request acccess to FRAME-IDP project?

Arvind Ramanathan  [上午 10:03]
i will approve as soon as i see it

Amin  [晚上 7:13]
[@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) I canot see the updated GitHub for RFD3. （已编辑）

Yu Zhang  [凌晨 12:57]
Hi all, here is the weekly update:

1. I have finished the MD for original PLP enzyme with E104P mutation for both L- and D-external aldimine. I have run for 500 ns. The geometries in the last 200 frames are quite stable. There are no significant geometric flipping or bond rotating happening. The only residue that can serve as proton acceptor is 82 lysine, which is consistent with original PLP enzyme. Therefore, the following steps can only  proceed on L-external aldimine since the position of 82 lysine matches the position of proton being extracted on L-external aldimine. The following reaction in the catalytic cycle is not predicted to happen with D-external aldimine.
2. The reason why there is trace amount of D product (L : D = 97 : 3) is postulated as the presence of water molecule as an alternative proton donor. Such assumption is indeed captured in the MD simulation with L-external aldimine. Water molecules are forming a bridge between PLP cofactor and Y301 residue, which can serve as the proton donor to finally lead to D product. I didn't run DFT to calculate the energy barrier since water typically is not a good proton donor as it would generate a hydroxide ion, which is usually not favorable if free ions are generated in a chemical transformation. I think this is where our Y301K could potentially work since we are introducing a mutation which can serve as both proton donor to trigger the first proton transfer step and serve as a good proton donor in the chirality determining step.
3. I have also investigated the other mutations mentioned in the experimental paper in case we miss something important. The MD simulation indicates that other positions are all far away from active site and I can not observe any interaction happening between those residues with external aldimine in our case. Therefore, I think they are not important in our case.
4. I have worked with [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) on editing RFD3 outputs. Most of the issues have been solved. There are still several issues remaining but all easy fix. Currently, I have to manually clean up the geometry individually by adding missing side chains and H atoms. Fixing the protonation state of PLP cofactor. After those, we can run MD with our MD pipeline. I'm working on the sequences generated by RFD3 with Y301K mutation. Hopefully I can finish them by the end of next week.

Plan for next week:

1. Finish the remaining work in #4
2. There are actually several other amino acids can potentially serve for the same purpose of lysine. For example, Arginine, asparagine, maybe glutamine as well. I probably can create a model reaction as simple as possible to test the energy barrier using DFT. The calculation should not take a long time and the computed values are definitely not accurate but the relative trend of energy barrier can provide some meaningful information. This is not the priority but can be an interesting thing to test.
3. We should start the writeup asap [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B)

（已编辑）

Anima  [晚上 6:08]
[https://x.com/avapamini/status/2031106186347741212?s=46](https://x.com/avapamini/status/2031106186347741212?s=46)

[](https://x.com/avapamini/status/2031106186347741212?s=46)[Ava Amini (@avapamini) on X](https://x.com/avapamini/status/2031106186347741212?s=46)

designing substrates for enzymes like proteases is a combinatorial problem.

tackling this, we built CleaveNet: a deep learning pipeline that designs peptide substrates with targeted efficiency & selectivity, validated end-to-end in the lab.

[https://t.co/K7zirl7Llm](https://t.co/K7zirl7Llm) @NatureComms

X (formerly Twitter)

[https://x.com/avapamini/status/2031106186347741212?s=46](https://x.com/avapamini/status/2031106186347741212?s=46 "Ava Amini (@avapamini) on X")[](https://x.com/avapamini/status/2031106186347741212?s=46)

Anima  [晚上 8:15]
[https://x.com/slavov_n/status/2031366493229711556?s=46](https://x.com/slavov_n/status/2031366493229711556?s=46)

[](https://x.com/slavov_n/status/2031366493229711556?s=46)[Prof. Nikolai Slavov (@slavov_n) on X](https://x.com/slavov_n/status/2031366493229711556?s=46)

AI protein design is rapidly progressing ![:火箭:](https://a.slack-edge.com/production-standard-emoji-assets/15.0/apple-medium/1f680@2x.png)

This study benchmarks de novo nanobody design by leading models, such as AlphaFold3, Boltz-2, and Chai-1. The study tested 106 true complexes and over 11,000 shuffled mismatches.

Key result:
High confidence scores often reflect

X (formerly Twitter)

[https://x.com/slavov_n/status/2031366493229711556?s=46](https://x.com/slavov_n/status/2031366493229711556?s=46 "Prof. Nikolai Slavov (@slavov_n) on X")[](https://x.com/slavov_n/status/2031366493229711556?s=46)

Arvind Ramanathan  [早上 7:58]
i generally agree w/ the assessment ... thisis also our experience. This is why the multi-fidelity models should do better hopefully

Anima  [晚上 10:02]
[https://x.com/biologyaidaily/status/2031730724609708141?s=46](https://x.com/biologyaidaily/status/2031730724609708141?s=46)

[](https://x.com/biologyaidaily/status/2031730724609708141?s=46)[Biology+AI Daily (@BiologyAIDaily) on X](https://x.com/biologyaidaily/status/2031730724609708141?s=46)

Ligand-guided Sequence–structure Co-design of De Novo Functional Enzymes

1. A new AI foundation model called ProteinNet achieves what was once considered exceptionally difficult: designing entirely novel enzymes from scratch that actually work in the lab, with catalytic

X (formerly Twitter)

[https://x.com/biologyaidaily/status/2031730724609708141?s=46](https://x.com/biologyaidaily/status/2031730724609708141?s=46 "Biology+AI Daily (@BiologyAIDaily) on X")[](https://x.com/biologyaidaily/status/2031730724609708141?s=46)

Arvind Ramanathan  [晚上 10:45]
Lei Li is a good friend, the work here is sort of old tho

Yu Zhang  [凌晨 12:18]
Hi all, here is the weekly update:

1. I have finished the MD calculations for 23 sequences generated by RFD3 with Y301K mutation earlier today. 17 out of 23 are successfully completed. The remaining 6 are either killed in the middle of simulation or ending with broken geometry. I think this is because the bad initial input geometry. They all have slightly longer peptide bond distance, which results in broken geometry.
2. I have gone through each final geometry for all 17 candidates, and their geometries all look good to me. External aldimine is located in the active site. There is no dissociation or significant flipping or rotating. All necessary interactions around external aldimine are there to stabilize the geometry. Therefore, I'm running MMPBSA calculation to estimate the binding energy.
3. [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) and I have been meeting with surf students and working on proposals. We have talked to Zhenpeng and he is willing to modifying the proposal and helping us with metadynamics. I believe both of them have sent the commitment confirmation email.

Plan for next week:

1. Finish the MMPBSA analysis.
2. Set up a meeting with Ziqi to update the current progress and figure out the following wet-lab procedures.
3. Set up a meeting with surf students to refine the proposal.

Amin  [凌晨 12:55]
Hi Team,

This week, I have been focusing on updating the RLHF reward function. Currently, we find the catalytic lysine by aligning the generated sequences with pfTrpB and perform all the deckings. Given that the RFD3 sequences may have binding pocket anywhere on the sequence, we should expect the model to generate sequences that do not align well with pfTrpB. so the reward must be independent of the alignment.
I implemented the idea of distributed binding pockets across generated sequences. it makes the reward model much slower for previous batch of generated sequences. I am going to test it on the RFD3 sequences this week.

besides, that I am planning to polish the SURF projects and provide the students with the resources they need before the start date.

Most importantly, we will meet Ziqi this week and will update everyone. （已编辑）

Raswanth  [早上 7:15]
**Weekly Update**
Last week I was travelling, so I couldn't share the weekly update. Over the last two weeks, I focused on one question: can reaction-specific geometry‑based proxies capture catalysis for our reaction, by extension, be a cheap but effective signal for GRPO**?** I wanted a clear answer before continuing in that direction. Most literature on enzyme study mainly describes **necessary conditions** for catalysis (geometric arrangements, residue positioning), not  **sufficient conditions** . Because of this, purely geometry‑based reward signals from literature may not reliably guarantee catalysis.

I got the answer I was looking for in Arieh Warshel's work (Nobel Prize in Chemistry). His seminal work argues that electrostatics within the active site is the dominant factor governing enzyme catalysis, and that favorable geometry (e.g., near‑attack conformations) does not guarantee a reaction will occur and actually arises from the electrostatics. Moreover, the number of possible catalytically unfavourable electronic configurations for a given geometry is so large that it seems even if one manages to get the substrates/residues in the right orientations, it's unlikely catalysis will proceed.

Warshel’s group also developed **Empirical Valence Bond (EVB)** methods. EVB is **much faster than QM/MM** (also created by Warshel) and can still estimate activation energies very well, though it requires careful parameterization, which can be tricky. EVB is still expensive for direct use inside the GRPO loop (to calculate the activation energy), so I looked at further approximations within the EVB framework: **LRA (Linear Response Approximation)** and  **PDLD electrostatic models** , which can further reduce runtime and thereby make it possible to calculate activation energy in a reasonable time and scale. The key question now is whether these approximations converge to the correct Activation Energy calculations under conditions that our system satisfies. Preliminary literature suggests this might be possible because:

* Standalone TrpB appears structurally rigid (reported in Francis’s directed evolution work).
* Fold‑type II PLP enzymes are generally considered relatively rigid systems.

Rigidity seems to a positive signal to use LRA as it tends to approximate activation energy under such conditions.

I do not yet have a definitive answer, so this week I will focus on verifying:

1. When LRA/PDLD approximations converge to EVB.
2. Whether our reaction and TrpB system fit into those assumptions.

Arvind Ramanathan  [早上 7:54]
Lots of things to unpack here [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) -

[早上 7:54]

I doubt if EVB will converge to LRA/ PDLD really...

Arvind Ramanathan  [早上 7:54]
esp given that TrpB will not fit into these assumptions.

Anima  [晚上 8:20]
[https://x.com/sacdallago/status/2033684125270278384?s=20](https://x.com/sacdallago/status/2033684125270278384?s=20)

[](https://x.com/sacdallago/status/2033684125270278384?s=20)[Christian Dallago (@sacdallago) on X](https://x.com/sacdallago/status/2033684125270278384?s=20)

![:消息列:](https://a.slack-edge.com/production-standard-emoji-assets/15.0/apple-medium/1f9f5@2x.png) We predicted 31 million protein complex structures across thousands of proteomes — and deposited 1.8M high-confidence ones into the AlphaFold Database.

Here's what that means and why it matters. ![:向下:](https://a.slack-edge.com/production-standard-emoji-assets/15.0/apple-medium/1f447@2x.png)

X (formerly Twitter)

Anima  [下午 1:00]
[https://www.biorxiv.org/content/10.64898/2026.03.02.708991v2](https://www.biorxiv.org/content/10.64898/2026.03.02.708991v2)

bioRxiv

[Rigidity-Aware Geometric Pretraining for Protein Design and Conformational Ensembles](https://www.biorxiv.org/content/10.64898/2026.03.02.708991v2)

Generative models have recently advanced de novo protein design by learning the statistical regularities of natural structures. However, current approaches face three key limitations: (1) Existing methods cannot jointly learn protein geometry and design tasks, where pretraining can be a solution; (2) Current pretraining methods mostly rely on local, non-rigid atomic representations for property prediction downstream tasks, limiting global geometric understanding for protein generation tasks; and (3) Existing approaches have yet to effectively model the rich dynamic and conformational information of protein structures. To overcome these issues, we introduce RigidSSL ( Rigidity-Aware Self-Supe…

3 月 6 日

Amin  [下午 3:08]
Hi team;

[@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) and I met with Ziqi today. Here are the most important updates:

1. Ziqi estimates that the wet lab experiments would take around one week. This is from the day that she delivers plasmid to finding the enzyme activity.
2. The other factor which is unknown, is the process of ordering plate(s) and how long would it take.
   1. We worked with Elegen last time. They added two co-authors to the paper for some form of discount. It took three weeks to one month for them to synthesize the genes and send us the plates
   2. Ziqi works with Twist before and she said it would take one month to get the plasmid.
3. The cost of one plate (comes in plasmid) is around $10k. of course this is without any discount. We will get more accurate numbers if we decide on the vendor.
4. Ziqi can work on two plates at the same time within the estimated time frame.
5. Frances knows that we are working on this project and we will send her an update before ordering the sequecnes.
6. We also discussed some technical details of involved in the assay.

[@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) feel free to add if I am missing something.

Anima  [下午 3:09]
ok, great. this is promising. We should ask her to contact Elegen and reduce uncertainty on that part. the rest is fine

[下午 3:10]

and we should get more accurate cost estimates in the process

Arvind Ramanathan  [下午 3:30]
did you guys discuss the fact the proteins may be different in fold than the TrpB?

Arvind Ramanathan  [下午 3:30]
Or are we only focused on testing things that look like TrpB?

Anima  [下午 1:34]
[https://x.com/arcinstitute/status/2035013002244866547?s=20](https://x.com/arcinstitute/status/2035013002244866547?s=20)

[](https://x.com/arcinstitute/status/2035013002244866547?s=20)[Arc Institute (@arcinstitute) on X](https://x.com/arcinstitute/status/2035013002244866547?s=20)

Over 250 million protein sequences are known, but fewer than 0.1% have confirmed functions. Today, @genophoria, @BoWang87 & team introduce BioReason-Pro, a multimodal reasoning model that predicts protein function and explains its reasoning like an expert would.

X (formerly Twitter)

[https://x.com/arcinstitute/status/2035013002244866547?s=20](https://x.com/arcinstitute/status/2035013002244866547?s=20 "Arc Institute (@arcinstitute) on X")[](https://x.com/arcinstitute/status/2035013002244866547?s=20)

Arvind Ramanathan  [下午 1:48]
I knew these folks were working on this.

Arvind Ramanathan  [下午 1:48]
Although i have my own critique on it

Yu Zhang  [凌晨 3:15]
Hi all, here is the weekly update:

* I have been working on the geometric analysis of MD results for RFD3 generated sequences with Y301K mutation. I have gone through each final geometry along with their binding energy calculated by MMPBSA. Those geometries are not similar to natural enzyme.
* According to the computational results, the sequence #1106 looks quite promising. It's binding energy is -114.7 kcal/mol and has necessary stabilizing interactions to stabilize the external aldimine. Another very promising one is #1082 with a -84.6 kcal/mol binding energy.
* Several sequences generated by RFD3 are not stable. The RMSD values of those structures keep increasing (at least > 3.5Å) along the MD trajectory. For example, sequence 0002, 0366, 1379 and 1788. The external aldimine in 1986 is even dissociated from the active pocket.
* Overall, in addition to promising meaningful results, I think RFD3 can also give us unreasonable results. We should always perform extra validations, for example, MD calculation, to valid those results.
* Amin, Raswanth and I have discussed current progress with Ziqi as Amin updated earlier this week.
* Amin and I have discussed the SURF projects with students. Since we are set for the proposal, we will start to push forward the two projects. We have required them to report weekly update from next week in the corresponding channel.

Plan for next week:

* Work with Amin on constructing the reward model
* Push forward SURF projects.

[凌晨 3:15]

| **sequence**`` | **binding energy**`` |
| --------------------------- | --------------------------------- |
| 0002                        | NA                                |
| 0089                        | -33.4857                          |
| 0256                        | -38.5687                          |
| 0366                        | -11.5947                          |
| 0382                        | -15.4004                          |
| 0569                        | -45.4139                          |
| 0785                        | -2.0942                           |
| 0959                        | NA                                |
| 1082                        | -84.5986                          |

Arvind Ramanathan  [早上 7:47]
This is very good IMO, [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U)

[早上 7:47]

I am curious how many more sequences can you take a look at?

Arvind Ramanathan  [早上 7:59]
Can you share the folds of these sequences?

Arvind Ramanathan  [早上 8:00]
( mean as a PDB file)

Anima  [晚上 9:08]
[https://zhanghanni.github.io/RigidSSL/](https://zhanghanni.github.io/RigidSSL/)

Raswanth  [晚上 7:05]
Weekly Update,
I’ve been extending my research from last week, specifically diving deeper into EVB, LRA, and some de novo enzyme design pipelines.
Here’s a breakdown of where things stand:

1. **EVB & LRA (Addressing Last Week's Questions)**
   a.  **Multi-step EVB** : [@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883), to answer your question on whether we can do EVB for a multi-step reaction, seems yes. There are two main approaches:

* Multi-MS-EVB: This uses a larger Hamiltonian (e.g., 5x5), where diagonal terms are MM and off-diagonal terms are QM. Distant off-diagonal terms are zeroed out (assuming far-away reaction coordinates aren't related) to make computation easier.
* Single-Step Breakdown: This is the more common approach. You break the reaction down into multiple single-step reactions, dealing with independent 2x2 Hamiltonians for all stages.

b.  **EVB Drawbacks** : One tricky part is that EVB requires heavy upfront parameterization. However, it is faster than QM/MM because it leverages a well-defined reaction pathway, which we fortunately have. And it seems if we get out hands on L-serine reaction parametrization, we can directly use that to run EVB on the D reaction.
c.  **LRA (Linear Response Approximation)** : It seems unlikely that LRA will work for our system (just a preliminary guess). The change in hybridization from sp3 to sp2 and the entering of the indole indicate non-linear responses.

2. The PLACER Model (seems quite interesting and a shortcut)
   I was looking into de novo enzyme design success stories and read up on Baker Lab’s work on **serine hydrolase** using the RFD+PLACER pipeline.

* How it works? - PLACER takes a backbone and a substrate (which could be reactants, intermediates, or a transition state) as input. It outputs multiple conformations of how the substrate might sit within the active site of the backbone.
* Overall General Pipeline: For each important reaction coordinate, they run PLACER with the specific substrate and RFD generated backbone. For example, if there are 5 reaction coordinates of interest, they generate 50 ensembles for each substrate, resulting in 250 total ensembles.
* From there, they compute two things:

  a. Intra-RMSD: Calculated for each substrate across its 50 generated ensembles. This seems very similar to computing ΔS (entropy).
  b. Inter-RMSD: Calculated between the DFT theozyme of that particular substrate and the PLACER-generated ensemble. This is very similar to computing ΔH (enthalpy).
* Selection & Speed: If both RMSDs are below thresholds (by reducing both, they seem to be reducing ΔS & ΔH), the backbone is selected and is considered "pre-organized". This objective seems acts as a crude proxy for reducing ΔG (my interpretation, they don't explicitly say this). Since it's an NN, it's a cheap and fast proxy for activation energy calculations in the GRPO pipeline.
* Bypassing MD: Because it generates ensembles, a very interesting idea I was thinking was using these ensembles as snapshots for MD. With some processing, we could potentially use these to compute binding affinity via MM/GBSA or MM/PBSA. This would significantly reduce the need for full MD simulations, which is typically the hardest part of computing binding affinity. Ofc this needs more insights and testing. Could be interesting, as it will make calculating binding affinity and D/L selectivity mentioned in the MF-BO document possible to implement and run faster.

3. Questions ([@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883), [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) , [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B), [@Anima](https://ramanathan-lab.slack.com/team/U04RBNXFSJK)) & Notes
4. (EVB vs. PLACER): A major drawback of the Baker Lab's pipeline is that they don't factor in second-shell interactions. Their final designed enzyme doesn't have great catalytic rates and reportedly stops functioning after about 10 uses. Because we need something that really captures electrostatic preorganization, I think EVB is still highly relevant and should be used at our final/highest fidelity level (while using PLACER for earlier stages). Any thoughts on this?
5. (NNP/MM):  What are your thoughts on NNP/MM or ML/MM (Neural Network Potentials + MM + ELME )? They seem to be gaining traction as a faster substitute for QM/MM while yielding similar accuracies at MM speeds. Is it worth considering instead of EVB and QM/MM?
6. (PLACER Experience): Any experience using PLACER? It sounds great, but I’d like to know how it fares in practice. Should we explore PLACER further?

Yu Zhang  [凌晨 1:11]
Hi all, here is the weekly update:
I focused on editing the RFD3 generated geometries and preparing the MD inputs. Sequences showing clearly unfavorable interactions were excluded. At this point,  all filtered RFD3 generated sequences have been evaluated computationally. Once the MD simulations are complete, I will carry out geometric and energetic analyses.
I also reviewed the current results and generated sequences with [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B). Based on the promising candidates identified through binding energy and geometric analyses, I will generate new theozymes for Amin's next step.
Next step:
Finish remaining MD calculations and their analysis
Generate new theozymes based on the MD results
Explore PLACER
[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) Can we set up a meeting next week to catch up?

Amin  [晚上 7:40]
Hi,

This week I have been working on two main things:

1. To generate new theozyme models (other than 301). There are four strong candidates based on the 104, 106, and 298 sites. [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) will run MDs to make sure the theozyme models are sane. Then we will run them through RFD3.
2. Set up the protein dynamic benchmark for the SURF student. There is a nice work on long horizon prediction of dynamics using SE3 diffusion models: [https://arxiv.org/html/2602.02128v2](https://arxiv.org/html/2602.02128v2). I created a working version of it and will share with the SURF student.

I think once we created the new theozyme models, we can meet and check them. Then [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) should run the large scale RFD3.

Arvind Ramanathan  [晚上 10:11]
Let's meet on Tue am or pm… I am free after 2
PM CT

Raswanth  [下午 5:45]
Weekly update,
This week's update is short because I've been quite sick for the better part of the week. I spent my time focusing on the big picture of how all these components coalesce together.

In discussions regarding the design doc, I was under the impression that the proposed fidelities were notes on how the GRPO reward system was to be designed. I wasn't part of the discussion on the design doc with Frances, probably missed it there, and didn't really come up in meetings, so I misinterpreted it. Reading up about MFBO (which I didn't know how it worked) cleared things up. I see they are complementary approaches, which I believe some of you already knew. Thankfully, it doesn't change a lot, and a lot of my research from the past few weeks is still useful.

The MFBO+LigandMPNN is very much in the spirit of how directed evolution works in the lab to date, just computationally. So GRPO's strength is what directed evolution lacks : A good start, the ability to make large-scale epistemic changes that help cross valleys in the fitness landscape. Putting the two together counters the limitation and helps us find our golden eggs.

Here is the implementation plan of how we get there:

1. F1 and F2 will be exclusively part of MFBO, not GRPO. The time it takes for meaningful signals update the GenSLM from them is high and not feasible.
2. F0 (quick signals like PLACER) will be used as part of the GRPO reward and most likely reused for MFBO.
3. The theozymes and key mutations fit into the SFT part with the RF diffusion designs, PLACER mutations, or MFBO F0-screening methods to remove obvious candidates/or fix certain mutations.
4. The EVB vs. QM/MM vs X debate can wait now that I understand MFBO better. I still stand by the fact that we absolutely need to capture electrostatic preorganization in the pipeline (as part of F2) becasue is one of the only extablished ***sufficient*** conditions for catalysis. But the execution is a trade-off: QM/MM is easier to setup but takes time; EVB is hard to execute but takes lesser time. Since it's the final stage, based on how many sequences come through the final pipeline. But a decision in the coming weeks will be needed.

There is a non-trivial amount of implementation ahead. I think iterating fast is the way to go, hoping to get it right isnt as practical. I'm hopeful because now there are a few LLM agents to help as well. That's for this week.

Yu Zhang  [晚上 11:47]
Hi all, here is my weekly update:
I have finished half of the MD simulations for the RFD3-generated sequences without the Y301K mutation (30 total), along with the corresponding geometric analyses and binding energy calculations. So far, 4 of the 14 completed sequences show promising geometries and excellent binding energies. The remaining simulations are running normally, and I am monitoring them regularly.
For the previous 20 MD simulations of [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) generated sequences containing mutations at positions 104–109 and 298, I selected the top 12 sequences and generated the corresponding theozyme models for Amin’s next step. Their binding energies range from -132.4 to -53.5.
The approach I used to generate the theozyme models was as follows:
 First, I selected all residues within 4 Å of the external aldimine. I then visualized the full enzyme structure and removed residues that do not make meaningful interactions with the external aldimine, such as hydrogen-bonding or π–π interactions. Serine near the pyridine ring was always retained, even when its distance was slightly greater than 4 Å, because it has been identified as important in the literature. Positions 104–109 and 298 were also always included. Backbones and hydrogen atoms involved in hydrogen-bonding interactions with the external aldimine were retained as well.
Next week:
The remaining MD simulations should be completed soon. I will update the results as soon as I get them.
Based on the results of binding energy calculation, I will generate theozyme model for Amin's use.

Zip

[theozyme.zipZip](https://files.slack.com/files-pri/T0105PFBYAZ-F0ARAFHR40H/download/theozyme.zip?origin_team=T0105PFBYAZ)

| **RFD3-generated sequences without Y301K**`` |                |
| --------------------------------------------------------- | -------------- |
| sequence                                                  | binding energy |
| 0350                                                      | -113.0019      |
| 0457                                                      | -112.7921      |
| 0029                                                      | -107.791       |
| 0342                                                      | -68.8312       |
| 0591                                                      | -43.3643       |
| 0461                                                      | -25.266        |
| 0343                                                      | -22.5921       |
| 0427                                                      | -8.854         |

Zhenpeng Liu  [凌晨 2:14]
已由  添加至 genslm-trpb。

Raswanth  [上午 10:43]
Weekly Update,
This week I've moved ahead with the F0 (Fidelity 0) implementation, specifically focusing on the selectivity function using a docking approach.

1. F0 Selectivity Implementation
   The process I built is:

- Check if the catalytic lysine is accessible and present in the generated protein.
- Form the Schiff's base with the catalytic lysine.
- Perform a local relaxation of the Schiff's base.
- Dock both D- and L-serine.
- Report the difference in their docking scores.

2. Rationale for the Docking Score Difference
   Because D- and L-serine are stereoisomers, their changes in entropy and solvation are identical. While MMGBSA calculates enthalpy, entropy, and solvation (which is more accurate and expensive), and Autodock Vina is essentially just an empirical guess at enthalpy. By taking the difference of the Vina scores, the systematic errors (like entropy and solvation) cancel out, giving us a result comparable to what we would get from MMGBSA and also reduces time.
3. Next Steps: PLACER Implementation
   The repository structure is now set, and my next big focus is implementing PLACER. I have two main questions to resolve first:
   a. What are the exact important reaction coordinates in our reaction for PLACER? Based on Arvind's suggestion, I'm also going to try and catch a current or former Frances Arnold lab member who fully understands the mechanism so we can nail down those reaction coordinates before I implement them. Yu I will probably start with you to get insights when I have a better undertsanding.
   b. How do we model the theozymes for these reaction coordinates and mainly compare them with the PLACER ensembles (since a simple RMSD won't work)?
4. Code Review (Yu & Amin)
   [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B) & [@Yu Zhang](https://ramanathan-lab.slack.com/team/U09M3JE3Q2U) I created a new branch (grpo_mfbo) for this part before I merge. If you can have a look at this file alone and verify if the logic and implementation are executed properly, that will be great - [https://github.com/RaswanthMurugan20/GenSLM_DPO/blob/grpo_mfbo/fidelity/f0/tier2_docking.py](https://github.com/RaswanthMurugan20/GenSLM_DPO/blob/grpo_mfbo/fidelity/f0/tier2_docking.py)
   Whenever you have the time, could you take 30-45 minutes to review the code? It's just a single script for this part. More code is going to pile up, so if we can fix any issues as they come, it will make things easier and make testing the other modules much easier.

Anima  [中午 12:40]
[https://x.com/kevinkaichuang/status/2041253741437857883?s=46](https://x.com/kevinkaichuang/status/2041253741437857883?s=46)

[](https://x.com/kevinkaichuang/status/2041253741437857883?s=46)[Kevin K. Yang 楊凱筌 (@KevinKaichuang) on X](https://x.com/kevinkaichuang/status/2041253741437857883?s=46)

[https://t.co/Usy2Fk0Jxd](https://t.co/Usy2Fk0Jxd)

X (formerly Twitter)

Arvind Ramanathan  [下午 1:12]
cool\

Arvind Ramanathan  [下午 4:27]
Were you aware of this work: [https://arxiv.org/pdf/2604.05181](https://arxiv.org/pdf/2604.05181)?

Amin  [晚上 7:56]
[@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) did you submit the sequence generations? If so, for how many theozymes?

Yu Zhang  [晚上 8:38]
Hi all, here is the weekly update:

1. I have completed all MD simulations for RFD3 generated sequences without Y301K mutation. The binding energy of a complete sequence set is attached. The best value is -113.0 kcal/mol. There are 7 promising candidates we could test in web lab if the binding energy threshold is set to be -50 kcal/mol.
2. Sequence generation using theozyme models generated from [@Amin](https://ramanathan-lab.slack.com/team/U05M1827L5B)’s 104-109/298 mutations is ongoing. [@Raswanth](https://ramanathan-lab.slack.com/team/U0907ADBGEM) could update more progress on this task.
3. I have worked with [@Zhenpeng Liu](https://ramanathan-lab.slack.com/team/U0AQRESK99R) on metadynamics setup. In the literature, metadynamics is most commonly performed using PLUMED with GROMACS or AMBER. Since this project already uses OpenMM for MD, and OpenMM can support metadynamics either through its built-in API or through the openmm-plumed plugin, we plan to run a quick test of these approaches. The goal is to determine whether OpenMM can reproduce results similar to those in Osuna's paper. If so, we can modify our current MD code to strengthen the existing pipeline.

Plan for next week:

1. Based on Raswanth generated sequences, I will work with Amin on his model fine-tuning. We should determine how to evaluate the generated sequences and any potential filterings to be done.
2. I have not used OpenMM to run metadynamics before. Me and Zhenpeng will spend some time exploring the settings and do the method benchmark.
3. For the electronic informed enzyme design, I plan to read papers about TargetDiff and NucleusDiff.

Also, [@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883) am I able to get an account on Argonne HPC. I also wanted to test Raswanth's calculation with RFD3. I'm not sure whether there is a security clearance issue for Chinese or not. Thanks for checking it in advance!

Yu Zhang  [晚上 8:38]

| **sequence**`` | **binding energy**`` |
| --------------------------- | --------------------------------- |
| 0350                        | -113.0019                         |
| 0457                        | -112.7921                         |
| 0029                        | -107.791                          |
| 1890                        | -98.3296                          |
| 1766                        | -88.8855                          |
| 0342                        | -68.8312                          |
| 1235                        | -60.77                            |
| 1005                        | -45.6986                          |
| 1301                        | -44.2283                          |

Amin  [晚上 9:20]
Hi Team,

This week, Yu and I finalized the set of the best theozyme models (12 new and 1 301k). After refining the model and exclusion of H atoms (as we did not do it for 301k),  Raswanth has submitted the RFD3 sequence generation for all 12 new theozymes. We decided to generate between 300 and 350 sequence per theozyme, so the final dataset will be around 5k sequences and will be used for SFT of the model.
I also worked on a pathway verification pipeline using xTB and CREST as a separate tool, so we can thermodynamically verify a reaction pathway by finding the free energy profile of the intermediates. This can be useful for both SURF projects and enzymatic reactions.
Finally, for the protein dynamic project (SURF), I learned that protein dynamics are not Markovian if the protein representation is not all-atom (coarse grain). This is related to [Mori-Zwanzig formalism](https://en.wikipedia.org/wiki/Mori%E2%80%93Zwanzig_formalism) (attached is the mathematical form of it).
This was raised in a very recent paper that published last month. It is a very important consideration. I am trying to study more and potentially find efficient ways to model this. （已编辑）

Screenshot 2026-04-11 at 6.26.43 PM.png

[](https://files.slack.com/files-pri/T0105PFBYAZ-F0ASPPU1B0R/screenshot_2026-04-11_at_6.26.43_pm.png)

[](https://en.wikipedia.org/)[Wikipedia](https://en.wikipedia.org/)

[Mori–Zwanzig formalism](https://en.wikipedia.org/wiki/Mori%E2%80%93Zwanzig_formalism)

The Mori–Zwanzig formalism, named after the physicists Hajime Mori and Robert Zwanzig, is a method of statistical physics. It allows the splitting of the dynamics of a system into a relevant and an irrelevant part using projection operators, which helps to find closed equations of motion for the relevant part. It is used e.g. in fluid mechanics or condensed matter physics.

Raswanth  [下午 3:53]
Weekly update,
There are multiple things in the works this week, so here is a quick breakdown of where everything stands:

1. PLACER Research
   I have been looking into PLACER setup, also specifically trying to define which states we need to consider and how exactly we will compare them.
2. Theozyme Scheduling
   I ran into some pdb format issues, which have been resolved. I have successfully scheduled 12 theozymes. All of their mutation 104-109 298 identities and the catalytic lysine 82 identity have been explicitly fixed (even though their exact positions in sequence can change). As of my last check, they are still in the queue.
3. DISCO Model Exploration
   We are evaluating RF diffusion + LigandMPNN, it makes sense to also see what kind of outputs the DISCO model can produce, it claims to produce catalytically active enzymes without a theozyme.

- The Tricky Part: It only requires one intermediate, which is confusing for our reaction since our rate-determining step is an Indole+AA compound. Because of this, there's no clear way to steer the model towards D rather than L because this intermediate is planar.
- FKC-Selectivity for Diffusion model : One takeaway from their paper is the Feynman-Kac Corrector (FKC). Specifically, the selectivity FKC, which enforces the selectivity of the substrate (even though it's just one) to the protein key for success.

Raswanth  [下午 3:22]
[@Arvind Ramanathan](https://ramanathan-lab.slack.com/team/UV8955883), the job I scheduled is on the prod queue. There are 2 jobs above my job and one of them is on Hold, it's been 4 days any way to speed the process up?

Ozan Gokdemir  [下午 4:18]
Arvind is in Italy. I am trying to get the job boosted.

Ozan Gokdemir  [下午 4:19]
It's strange that there are brackets next to your job ID on Polaris's qstat printout. Did you submit an array of jobs?

`qstat -f`  is not printing anything with your job ID. I think there must've been an issue with your PBS submission script. （已编辑）

Anima  [晚上 7:30]
[https://www.nature.com/articles/s41587-026-03081-9](https://www.nature.com/articles/s41587-026-03081-9)

Nature

[Artificial allosteric protein switches with machine-learning-designed receptors](https://www.nature.com/articles/s41587-026-03081-9)

Nature Biotechnology - Allosteric biosensors are constructed by combining reporter proteins with machine-learning-designed receptor domains.
