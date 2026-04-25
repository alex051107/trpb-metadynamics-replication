# TrpB 锚定的序列条件动力学贡献设计书

## 研究边界与总判断

本报告不是文献综述，而是基于你给定的硬约束与固定先验，逆向设计“在 2026 年这个时间点，什么东西既足够新、又足够能在 10 周内做出 v0、还能真正卡住提案验证链条”的研究角度。我的总判断是：**最强的 SURF 贡献不应是再造一个模型，而应是做出一个让现有与未来模型都无法回避的、TrpB 锚定的“任务—指标—基准—诊断”组合包。**原因很清楚：现有生成式蛋白动力学工作主要还是围绕广谱结构分布恢复、ATLAS/快折叠蛋白上的 JS/TIC/RMSF 等通用指标；PLaTITO 已经把“pLM 条件化 operator”空间占掉了大头，MEMnets 已经把“显式记忆核最小化找慢 CV”占掉了，ConfRover 与 STAR-MD 也已经把“更长时间滚动、更强时空架构”这条线推得很远。与此同时，公开数据层面，ATLAS 与 mdCATH 提供的是大规模蛋白 MD 资源，但都不是面向“酶、突变、催化相关亚稳态、增强采样真值”这一组合；后 AlphaFold 时代的综述也明确把**数据不足与缺乏标准化评价协议**列为核心瓶颈。citeturn18view0turn35search0turn19view1turn19view3turn21view0turn21view1turn34view0

因此，真正 defensible 的路线不是“把某个通用模型再搬到 TrpB 上”，而是把 Maria-Solano 2019 的 TrpB COMM O/PC/C 体系和后续 TrpB 变体工作，变成一个**可公开、可打分、可反驳、可复用**的验证装置：一方面验证“sequence-conditioned surrogate 能否恢复与 MetaD 一致的亚稳态与路径分布”，另一方面直接回答 Amin 提出的 Mori–Zwanzig 张力：在 coarse-grained 表示上，究竟什么时候显式记忆是必需的，什么时候只是表示不充分的替代物。Maria-Solano 等展示了 PfTrpB 的 COMM 开/部分闭/闭构象景观与进化相关的群体重排；Duran 等进一步把这些状态与 TrpB 催化循环阶段、SPM 路径以及 tAF2+MD / MetaD 对照联系起来；但这些工作并没有把它们封装成一个可供序列条件 surrogate 统一检验的 benchmark/task/metric 体系。citeturn7search7turn8view0

下面我按你要求的五个轴来做：每轴先给候选池，再保留通过 novelty + feasibility 双重筛选的前两项；每个保留项都给完整 idea card。凡是我把置信度降到 MEDIUM/LOW 的地方，都会明确指出最强攻击面。citeturn34view0turn33view0

## 任务定义创新

候选池共有三项。保留两项：**突变诱导亚稳态偏移预测任务**、**路径进度分布匹配任务**。淘汰一项：**反应阶段条件化集合准确率**，理由是它需要跨多个化学中间体的可靠参数化与公开结构准备，十周内最容易被“化学态准备没做稳”拖死；同时，TrpB 相关高分辨率主动位点化学信息虽然存在，但跨阶段对齐成本明显高于纯构象态任务。citeturn8view0turn14search8turn14search14

**IDEA A1: Mutation-conditioned substate shift prediction**  
**AXIS:** A  
**ONE-LINE CLAIM:** 把 TrpB 变体的 MetaD 景观重构为一个“预测突变会把 O/PC/C 哪个亚稳态推高或推低”的监督任务，并用置信区间而不是点估计来定义标签。

**NEAREST PRIOR ART:**  
- Maria-Solano 等，2019，JACS——给出 PfTrpS/PfTrpB 相关的 COMM O/PC/C 构象景观与进化驱动的群体重排，但它是机制论文，不是可复用任务定义，更没有“变体间 signed shift label + uncertainty”的公开评测对象。citeturn7search7turn8view0  
- Monteiro da Silva 等，2024，Nature Communications——用 subsampled AF2 预测不同构象相对群体，并在 Abl1/GMCSF 上对突变导致的构象分布变化给出定性预测，但它不是增强采样真值，也不是酶催化亚稳态任务。citeturn10view1  
- Medaparambath 等，2026，预印本——研究小肽突变如何改变 FES，并用 HLDA 特征与稳定性变化相关联；但对象是 10 aa 小肽，不是酶，也没有公共的、MetaD-grounded 的亚稳态 shift benchmark。citeturn32view0

**THE GAP THIS CLOSES:**  
现有工作要么研究“某个系统会不会出现某些构象”，要么研究“某个方法能不能粗略预测群体变化”，但**没有一个公共任务把 TrpB 这类酶的序列扰动，映射成增强采样支持的、状态对齐的、带统计显著性的亚稳态偏移标签**。这件事并不等于“把 population prediction 搬到 TrpB”，因为这里的核心不是一个预测器，而是一个**评测问题的形式化**：标签来自对齐后的 MetaD FES 与 block CI，输出既区分方向也区分不确定性。citeturn10view1turn32view0turn8view0

**LOAD-BEARING TEST:**  
如果没有这个任务，提案里“recover conformational substates consistent with metadynamics ground truth”这句话在**序列扰动条件下**就没有可验证含义：模型只要生成出看上去多样的构象就能自称“恢复亚稳态”，但你无法问它一个更尖锐的问题——**这个突变是否把闭态群体往上推了，而不是只是把分布变宽了？** 这会直接卡住提案对“sequence-conditioned dynamics contribution”的可证伪性。  

**CONCRETE APPROACH:**  
- **Inputs required:** PfTrpB WT 与公开变体序列；公开结构或可重建结构；按 Maria-Solano / Duran 路线建立的 PATHMSD 参考路径；GROMACS+PLUMED 生成的 WT-MetaD 与 2–3 个公开变体 MetaD；状态划分规则与 block 分析脚本。citeturn7search7turn8view0turn3view6turn23search4  
- **Algorithm / protocol steps:**  
  1. 选 2–3 个公开可得的 PfTrpB 变体，优先 WT 与 0B2，再加一个公开工程/文献变体。  
  2. 用统一 PATHMSD 坐标系得到所有变体在同一 \(s,z\) 网格上的 reweighted FES。  
  3. 定义 O/PC/C 区域掩码，并对每个变体做 block-reweighted 亚稳态群体估计。  
  4. 对每个变体对生成 signed label：\(\mathrm{sign}(\Delta p_O), \mathrm{sign}(\Delta p_{PC}), \mathrm{sign}(\Delta p_C)\)，当 95% CI 跨零时标记为 ambiguous。  
  5. 发布一个小而干净的 benchmark：输入是变体 ID/序列与统一坐标系，输出是三态 signed shift label + magnitude bin + ambiguity flag。  
- **Compute budget:** 约 60–120 GPU-hours 等价的 GROMACS GPU 预算，或 2–5k CPU-core-hours；4–6 周可拿到 v0 地景，余下时间做重加权与文档。  
- **Ground truth / reference data source + license:** 上游序列与结构来自 PDB/文献公开数据；PDB 原始结构文件按 CC0 可自由使用；发布数据集本体建议 CC-BY-4.0，代码 MIT。citeturn22search0turn22search1  
- **v0 success criterion:** 至少形成 8–12 个“方向稳定”的 state-shift label（95% CI 不跨零），且至少 80% 的 pairwise shift instance 有明确非歧义标签。  
- **What the released artifact looks like:** `landscape_pairs.parquet`（variant_a, variant_b, state, delta_pop, ci_low, ci_high, sign_label, ambiguity）；`fes_grid.npz`（shared s,z grid）；`splits.yaml`；`score.py`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `mutation-conditioned substate population shift prediction metadynamics benchmark enzyme`、`direction of population shift metric conformational ensemble benchmark protein`、`mutation-matched free energy surface pair dataset protein metadynamics benchmark`。返回的是一般性酶动力学综述、AF2 population-prediction、FES 工程与通用 free-energy benchmarking，而**没有**“TrpB/酶增强采样真值 + 变体亚稳态 signed shift benchmark”的现成工作。citeturn25search0turn25search7turn26search0turn32view0  
- **Non-triviality:** 一个合格博士生当然会想到“比较 WT 和 mutant 的景观”，但不会天然把它做成**可跨模型复用、对齐状态空间、带歧义标签、对 surrogate 直接可打分**的 benchmark 任务；难点在于状态对齐、CI 设计、以及让“方向”比“绝对误差”更 load-bearing。  
- **Load-bearing:** 没有它，提案无法在“sequence perturbation leads to substate redistribution”这个层面被严格验证。  
- **Reviewer attack surface:** 最强批评会是“这不就是把 Monteiro 2024 的 population shift 思路搬到 TrpB？”；我的反驳是：Monteiro 2024 的对象是结构预测输出与实验/NMR 已知状态比例，**不是**增强采样真值、不是统一 PATHMSD 状态空间、也不是酶催化相关三态 signed shift benchmark。citeturn10view1turn3view6turn8view0  

**FEASIBILITY:**  
- **Time to v0:** 5–7 周。  
- **Hardest step + mitigation:** 最难的是统一参考路径与变体对齐；缓解办法是 v0 只做同一 PfTrpB 路线上的 2–3 个公开变体，避免跨物种路径失配。  
- **What could block:** 某个变体公开结构不足；MetaD 对某一变体收敛太慢；状态边界对小样本敏感。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** indirectly。  
- **(b) cross-family substate recovery:** indirectly；它先把“序列扰动下的 substate recovery”定义清楚。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 提供这些模型都必须面对的 enzyme-specific、mutation-conditioned 评测对象，而不是再造新模型。citeturn18view0turn19view1turn19view3  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是。因为任务规范、标签协议、数据工件和 scoring script 都是明确的一作式产物。  
- **1-sentence interview pitch:** 我把 TrpB 的公开 MetaD 景观变成了一个能检验“序列扰动是否真的改变催化相关亚稳态群体”的 benchmark，而不是再给已有模型加一个 case study。  

**CONFIDENCE ON NOVELTY:** HIGH（相邻工作很多，但“MetaD-grounded enzyme substate signed-shift benchmark”这一组合我没有搜到确证先例）。

**IDEA A2: Path-progress distribution matching**  
**AXIS:** A  
**ONE-LINE CLAIM:** 不再只问模型能否恢复 O/PC/C 群体，而是问它能否恢复沿 PATHMSD 参考路径的完整 \(p(s,z)\) 分布与 barrier occupancy。

**NEAREST PRIOR ART:**  
- PLUMED PATHMSD 文档——提供 path progress `sss` 与 off-path distance `zzz` 的定义，但它只是 CV 工具，不是评测任务。citeturn3view6  
- PNAS Nexus 2024 的 metadynamics of paths + ML CV 工作——证明路径空间数据对学习 CV 很重要，但目标是训练更好的 CV，不是给 surrogate 模型定义统一的 path-distribution benchmark。citeturn17view0  
- ConfRover / Mac-Diff——在 ATLAS 或快折叠蛋白上主要用 JS-PwD、JS-Rg、JS-TIC、RMSF 等通用指标评估，仍然没有 enzyme-specific 的 path-progress distribution matching。citeturn19view1turn33view0

**THE GAP THIS CLOSES:**  
仅看 O/PC/C 群体会把很多错误藏起来：两个模型可能给出几乎相同的三态占比，但一个沿物理可接受路径推进，另一个靠 off-path 塌陷或错误 barrier 穿越得到同样占比。这个任务补上的，正是“**亚稳态恢复**”与“**路径动力学逼真度**”之间的空白地带。citeturn3view6turn17view0turn33view0

**LOAD-BEARING TEST:**  
如果没有这个任务，提案中“recover conformational substates consistent with metadynamics ground truth”只能被解释成 basin occupancy matching，而不能验证**路径层面的物理一致性**；这会让“recover substates”沦为一个过宽松说法。  

**CONCRETE APPROACH:**  
- **Inputs required:** 统一的 15-frame PATHMSD 参考路径；WT 与公开变体 MetaD 轨迹；重加权脚本；状态掩码与 transition-window 定义。citeturn3view6turn8view0turn23search2  
- **Algorithm / protocol steps:**  
  1. 在统一参考路径上对所有轨迹投影得到 \(s\) 与 \(z\)。  
  2. 用 reweighting 得到参考 \(p(s,z)\)；对 generated trajectory 或 baseline MD 也做同样投影。  
  3. 定义三类子任务：全局 \(p(s,z)\) 匹配；barrier window occupancy；state-conditioned \(p(s\mid \text{state})\)。  
  4. 提供标准 scorer：2D EMD、state-conditional JS、rare-barrier recall。  
  5. 用 split-half MetaD 作为“oracle 下界”，用随机重排或 basin-only 重采样作为“坏基线”。  
- **Compute budget:** 轨迹投影与评分耗时低；重头戏与 A1 共享 MetaD，额外 <10 GPU-hours 的分析即可。  
- **Ground truth / reference data source + license:** 同 A1；路径与评分脚本由本项目发布，代码 MIT。  
- **v0 success criterion:** split-half reference 的 scorer 显著优于随机/只匹配 basin 占比的基线，且 block 重采样下排序稳定。  
- **What the released artifact looks like:** `path_reference.pdb`；`p_sz_reference.nc`；`score_path.py`；`barrier_masks.json`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `path-progress distribution matching PATHMSD benchmark protein dynamics`、`pathway entropy metric protein transition path ensemble paper`、`path-progress distribution matching PATHMSD benchmark protein dynamics` 与 `PATHMSD` 相关查询。返回的是 PATHMSD 工具、transition/path sampling、path-like CV 学习，而不是“把 \(p(s,z)\) 当作 surrogate evaluation task”的 benchmark。citeturn25search1turn25search5turn11search1turn25search37  
- **Non-triviality:** 这不是“把 PATHMSD 拿来再算一遍”；真正新的是把路径坐标从**模拟工具**变成**模型验证协议**。  
- **Load-bearing:** 没有它，路径层面的真值缺席。  
- **Reviewer attack surface:** “路径分布过于依赖你选的参考路径。” 反驳：v0 可以公开 path file、path sensitivity 分析与 alternative reference test；而且这一攻击本身正说明需要 benchmark 化。  

**FEASIBILITY:**  
- **Time to v0:** 4–6 周，且与 A1 共享大部分基础设施。  
- **Hardest step + mitigation:** 参考路径的稳健性；缓解办法是只做同一系统内比较，并加一份 path perturbation 敏感性分析。  
- **What could block:** 参考路径文件无法从公开材料完整重建；某些变体需要重新聚类定义 barrier。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** directly tests。  
- **(b) cross-family substate recovery:** indirectly。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 把“长时间滚动是否看起来稳定”升级为“沿催化相关路径是否分布正确”。citeturn18view0turn19view3turn33view0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是。因为它产出的是 benchmark protocol 与 scorer，而不是“协助某模型跑结果”。  
- **1-sentence interview pitch:** 我把 TrpB 的 PATHMSD 从增强采样坐标，改造成了检验生成轨迹是否沿正确催化路径前进的标准任务。  

**CONFIDENCE ON NOVELTY:** HIGH（PATHMSD 与路径采样很多，但“PATHMSD-distribution benchmark for surrogate validation”我没有搜到现成实现）。

## 评价指标创新

候选池共有三项。保留两项：**方向正确率加不确定性惩罚**、**化学锚定催化就绪度分数**。淘汰一项：**committor distribution matching**，不是因为它不重要，而是因为在十周内对 TrpB 做高质量 committor 估计很可能把项目重心拖进 transition-path sampling，本末倒置；现有转变态/committor 工作反而证明了这部分计算和方法学门槛并不轻。citeturn30view0turn11search4

**IDEA B1: Sign-of-shift with uncertainty penalty**  
**AXIS:** B  
**ONE-LINE CLAIM:** 用“方向是否对”替代单纯的 population error，并显式惩罚 CI 过宽或跨零的预测，从而让评价更贴近酶工程决策。

**NEAREST PRIOR ART:**  
- Monteiro da Silva 等，2024——对突变导致的相对状态群体变化做定性预测，并报告 >80% 的正确率，但没有一个标准化指标把“方向正确、幅度不确定、歧义样本处理”打包起来。citeturn10view1  
- Mac-Diff，2026——用 JS-PwD、JS-Rg、JS-TIC、EMD、diversity/fidelity 等评估 ensemble；这些指标衡量分布接近性，但不会直接回答“这个突变把闭态推高还是推低”。citeturn33view0  
- SHAPES，2025——评估生成模型的结构覆盖与层次相似性，也不是 mutation-induced dynamical direction metric。citeturn11search2

**THE GAP THIS CLOSES:**  
酶工程里的很多判断并不需要你把所有分布都拟合得很精细，先要回答的是**方向**：某个变体到底把催化相关态推向有利还是不利。现有通用评分在这件事上太钝，因为一个模型可以拿到不错的 JS/EMD，却把最关键的效应方向搞反。citeturn33view0turn10view1

**LOAD-BEARING TEST:**  
没有这个指标，sequence-conditioned surrogate 在酶工程语境里就缺少一个“最小可用”判据。换句话说，模型可能“分布上不差”，但对实验设计者而言完全没用，因为它连变体效应方向都不能可靠给出。  

**CONCRETE APPROACH:**  
- **Inputs required:** 由 A1/C1 产生的亚稳态 signed labels、CI、paired FES。  
- **Algorithm / protocol steps:**  
  1. 定义每个变体对、每个状态的 signed ground truth。  
  2. 对候选模型输出的 \(\Delta p\) 计算 sign agreement。  
  3. 增加 uncertainty penalty：若预测或真值 CI 跨零，则按 ambiguity weight 降权。  
  4. 输出三个分数：plain sign accuracy、confidence-weighted sign accuracy、wrong-way penalty。  
- **Compute budget:** 纯分析，无额外 MD 预算。  
- **Ground truth / reference data source + license:** 依赖 C1；评分脚本 MIT。  
- **v0 success criterion:** 评分能把“只匹配总分布、但方向经常错”的基线与真正恢复方向的模型清晰分开；随机/翻符号基线接近 0.5 或更差。  
- **What the released artifact looks like:** `metric_signshift.py`、`metric_card.md`、`examples.ipynb`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `direction of population shift metric conformational ensemble benchmark protein`、`mutation-conditioned substate population shift prediction metadynamics benchmark enzyme`。返回的是 population prediction 与通用分布指标，没有“direction + CI penalty”这种专门为动力学变体效应设计的 scorer。citeturn25search7turn25search0turn33view0  
- **Non-triviality:** 这不是把 accuracy 改个名字；它要求把 boosted/reweighted ensemble 的统计不确定性引入评分协议。  
- **Load-bearing:** 它把“模型对酶工程决策是否有用”这个问题压缩成一个更锋利的指标。  
- **Reviewer attack surface:** “方向指标太粗，丢了幅度信息。” 反驳：不是替代幅度，而是补上一个在工程决策里更高优先级的维度；可以与 magnitude bin 一起报告。  

**FEASIBILITY:**  
- **Time to v0:** 1–2 周。  
- **Hardest step + mitigation:** 歧义样本处理；缓解办法是把 ambiguity 公开为标签之一，而不是强行二值化。  
- **What could block:** 若 C1 的 CI 过宽，标签量会变少。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** indirectly。  
- **(b) cross-family substate recovery:** indirectly。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 这些模型的通用高分不再足够，必须经受“方向对不对”的检验。citeturn19view3turn33view0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，且极适合作为方法学小而硬的输出。  
- **1-sentence interview pitch:** 我设计了一个专门衡量“模型是否把突变引起的功能相关态往正确方向推”的指标，而不是继续停留在通用 JS 分数。  

**CONFIDENCE ON NOVELTY:** HIGH（很像“显然应该有”的指标，但我没有搜到已标准化发表的版本）。

**IDEA B2: Chemistry-anchored catalytic readiness score**  
**AXIS:** B  
**ONE-LINE CLAIM:** 在 O/PC/C 状态之外，再看主动位点上真正与 PLP 化学相关的几何分布是否对，从而区分“只是闭了”与“闭得可催化”。

**NEAREST PRIOR ART:**  
- Mac-Diff，2026——主要用 JS-PwD、JS-Rg、JS-TIC、RMSF、EMD 等全局/中尺度指标，完全不触及 TrpB/PLP 主动位点化学几何。citeturn33view0  
- Holmes 等，2022，PNAS / NMR crystallography——给出 tryptophan synthase α-aminoacrylate 中间体的高分辨率化学与质子化信息，说明主动位点精细几何与化学态是 mechanistically load-bearing 的。citeturn14search8turn14search14  
- 对 PLP 酶的一系列评述与结构化学工作——反复强调 Dunathan 取向、Schiff base 几何、PLP 取向与反应特异性/催化相关；但这些知识还没有被转写为 ML-MD surrogate 的标准评分项。citeturn15search8turn15search1turn15search9turn15search14

**THE GAP THIS CLOSES:**  
TrpB 的闭态不是充分条件。Duran 2024 与相关 TrpB 工作已经说明，COMM 关闭与更高活性有关，但“闭了”不等于“活性位几何也正确”。当前 generative-dynamics 论文几乎都把评价停在结构分布和 slow-mode 投影上，导致“看起来对、但化学不对”的失败模式没有被捕捉。citeturn8view0turn33view0

**LOAD-BEARING TEST:**  
没有这个指标，提案即使在 MetaD substate 层面过关，仍然无法支持“对酶功能相关动力学有贡献”的更强说法，因为模型可能只是学会 COMM 开合，而没有学到与催化化学相容的集合。  

**CONCRETE APPROACH:**  
- **Inputs required:** TrpB MetaD/MD 帧；PLP 与关键残基坐标；公开高分辨率 TS 主动位点化学结构作为 descriptor 依据；状态标签。citeturn14search8turn15search9turn8view0  
- **Algorithm / protocol steps:**  
  1. 定义一组 state-conditional chemistry descriptors：PLP–Lys 键联几何代理、Schiff-base 平面扭转代理、PLP 环取向、隧道门控距离、必要时加入可从公开中间体结构映射的 Dunathan-like 角度。  
  2. 在每个状态内计算参考分布 \(p(d\mid O), p(d\mid PC), p(d\mid C)\)。  
  3. 对模型输出集合计算同样分布，并以 state-weighted JS/EMD 求分。  
  4. 把最终分数定义为“状态恢复 × 化学几何恢复”的乘性或双报告协议。  
- **Compute budget:** 纯分析，<5 GPU-hours；若需补充短 MD 验证，再加 10–20 GPU-hours。  
- **Ground truth / reference data source + license:** 上游结构来自公开 tryptophan synthase / PLP 酶文献与 PDB；评分脚本 MIT。citeturn22search0turn14search8turn15search9  
- **v0 success criterion:** 该指标能把“COMM 关闭但活性位几何偏离”的集合与真正更接近文献活性态几何的集合区分开，并且与已知高活性/低活性变体排序一致。  
- **What the released artifact looks like:** `chemistry_metric.yaml`（descriptor 定义）；`score_catalytic_readiness.py`；`descriptor_reference.parquet`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `chemistry-aware catalytic readiness metric Dunathan angle protein dynamics benchmark`、`catalytic readiness metric Dunathan angle Schiff base geometry generative protein dynamics evaluation`。返回的是 PLP 化学与酶学文献、以及通用生成模型评价，并没有“把这些 descriptor 转成 surrogate benchmark metric”的论文。citeturn25search2turn15search8turn15search9turn33view0  
- **Non-triviality:** 难点不在于挑几个距离，而在于把 descriptor 设计成**状态条件化**的，否则会把“开态本来就不该像闭态主动位几何”误判成错误。  
- **Load-bearing:** 它把“只是构象学对”与“功能意义上对”分开。  
- **Reviewer attack surface:** “经典 MD 上的主动位点化学代理太粗。” 反驳：正因为粗，所以更适合做 surrogate evaluation 的第一道筛子；v0 不碰 QM/MM，只做坐标几何代理与 state conditioning。  

**FEASIBILITY:**  
- **Time to v0:** 2–3 周。  
- **Hardest step + mitigation:** descriptor 集合不能太贪；缓解办法是先发布 4–6 个最稳健的几何代理，Dunathan-like 角做可选项。  
- **What could block:** 不同 TrpB 化学态坐标系难直接对齐；部分 descriptor 对 ff14SB/TIP3P 敏感。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** indirectly。  
- **(b) cross-family substate recovery:** indirectly。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 引入在通用 benchmark 中完全缺席的“催化可用性”判据。citeturn33view0turn34view0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，而且很像“undergrad 也能一眼说清的 sharp contribution”。  
- **1-sentence interview pitch:** 我把 TrpB 评价从“像不像 MD”推进到“像不像一个化学上准备好催化的 TrpB 集合”。  

**CONFIDENCE ON NOVELTY:** HIGH（邻近知识很多，但作为标准评分协议的形式化缺失非常明显）。

## 数据与基准工件

候选池共有三项。保留两项：**突变配对自由能地形库**、**带 block 误差条的罕见态重加权集合包**。淘汰一项：**跨酶家族 PATHMSD 参考路径库**，因为在 10 周内它会从“好想法”变成“结构同源映射的大泥潭”；这不是没有价值，而是 v0 最容易死于跨家族路径对齐与状态同构假设。ATLAS/mdCATH 的规模与价值说明了公开动态数据库的重要性，但它们也说明“大而广”不是这个 SURF 的正确落点。citeturn21view0turn21view1turn34view0

**IDEA C1: Mutation-matched FES pair corpus**  
**AXIS:** C  
**ONE-LINE CLAIM:** 发布一个不是“单个 FES 图”，而是**同一坐标系里成对对齐**的 TrpB 变体 FES 语料，直接提供 \(\Delta F(s,z)\) 与 state-shift 标签。

**NEAREST PRIOR ART:**  
- Maria-Solano 2019 与 Duran 2024——都展示了 TrpB 变体间的 FEL/FES 比较，但没有把它们做成可下载、可对齐、可评分的数据工件。citeturn7search7turn8view0  
- ATLAS，2024——提供 1390 蛋白链标准化 all-atom MD，但不是 mutation-matched enzyme FES pair 数据库。citeturn21view0  
- mdCATH，2024——提供 5398 域、5 温度、5 重复的大规模 all-atom MD 与力信息，但同样不是酶突变配对自由能景观数据。citeturn21view1turn22search3

**THE GAP THIS CLOSES:**  
公开动态数据库已经证明“大规模轨迹”可以做到，但 surrogate validation 这里真正缺的并不是再来一个 ATLAS，而是一个**小而带强语义的 benchmark artifact**：同一路径、同一网格、同一状态掩码下，不同变体如何改写地景。没有这个工件，A1/B1 只能停留在 proposal 文本层。citeturn21view0turn21view1

**LOAD-BEARING TEST:**  
没有这个语料，sequence-conditioned surrogate 的“跨序列地景迁移”只能拿通用 MD 数据去测，无法在 TrpB 这种目标酶上以增强采样真值做 sequence-aware 验证。  

**CONCRETE APPROACH:**  
- **Inputs required:** 统一参考路径；WT 与 2–3 个公开变体的 MetaD 轨迹；重加权与 block 分析工具。citeturn3view6turn23search0turn23search4  
- **Algorithm / protocol steps:**  
  1. 统一网格化所有变体的 \(F(s,z)\)。  
  2. 生成每对变体的 \(\Delta F(s,z)\)、dominant basin masks、barrier masks。  
  3. 对每个网格点给出 block mean 与 CI。  
  4. 派生 state-shift labels 与 path-distribution reference，供 A1/A2/B1 直接复用。  
- **Compute budget:** 与 A1/A2 共用；额外分析成本低。  
- **Ground truth / reference data source + license:** PDB 上游 CC0；本语料 CC-BY-4.0；评分代码 MIT。citeturn22search0  
- **v0 success criterion:** 至少 2 个变体对的共享网格 FES 可重复；dominant basin 区域 split-half correlation >0.9，且 major basin 的 \(\Delta F\) 方向在 block CI 下稳定。  
- **What the released artifact looks like:** `pairs/{wt__0b2}.zarr`（F, dF, CI, masks）；`metadata.csv`；`LICENSE`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `mutation-matched free energy surface pair dataset protein metadynamics benchmark`。返回的是通用 free-energy benchmarking、reweighting 与小肽 FES 工程，并没有公开的 mutation-matched protein FES pair corpus。citeturn26search0turn26search4turn26search5turn32view0  
- **Non-triviality:** 重点不是“把图片存下来”，而是把多变体景观对齐到同一个 scoring 空间，并附带不确定性。  
- **Load-bearing:** 它是所有上层 task 与 metric 的地基。  
- **Reviewer attack surface:** “样本量太小，不像数据库。” 反驳：这个工件追求的是 load-bearing，不是规模；small-and-sharp 恰恰符合 SURF。  

**FEASIBILITY:**  
- **Time to v0:** 4–6 周。  
- **Hardest step + mitigation:** 变体数过多会拖垮收敛；缓解办法是 v0 只做 2–3 个变体、2 个 pair。  
- **What could block:** 某个变体 landscape 收敛慢；不同变体需要稍微调整 state mask。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** indirectly。  
- **(b) cross-family substate recovery:** indirectly。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 提供酶特异、突变配对、增强采样真值的数据工件，而非再收集一个大规模通用轨迹库。citeturn18view0turn19view3turn21view0turn21view1  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，数据工件本身就可作为独立贡献。  
- **1-sentence interview pitch:** 我没有去追求百万轨迹，而是把最能卡住模型真实性的一小批 TrpB 变体地景做成了可对齐、可打分、可复用的数据集。  

**CONFIDENCE ON NOVELTY:** HIGH。

**IDEA C2: Rare-state reweighted ensemble pack**  
**AXIS:** C  
**ONE-LINE CLAIM:** 从 MetaD 中提取不是“全体轨迹”，而是带重加权与 block 误差条的 rare/barrier state ensemble，专门服务于 surrogate 的 hardest-case 验证。

**NEAREST PRIOR ART:**  
- PLUMED 教程与相关最佳实践——强调 metadynamics 可以做重加权、block analysis、误差估计，但没有把 rare-state ensemble 发布成本体 benchmark artifact。citeturn23search0turn23search4turn23search9  
- 2024 JCTC 关于 FES convergence 的工作——研究如何估计不同偏置模拟合并得到的 FES 收敛，但也没发布“rare-state pack”。citeturn26search5  
- Borthakur 等，2025——把 IDP 的 reweighted ensemble 做成公开资源，但对象不是酶的罕见构象态，也不是为了 generative-dynamics surrogate benchmark。citeturn17view3

**THE GAP THIS CLOSES:**  
现在的 generative-dynamics 评价太容易被 dominant basin 主导。rare state 才是 surrogate 最容易露馅的地方，也是提案里“recover substates consistent with metadynamics ground truth”最难的部分。这个工件的价值，不在于包全轨迹，而在于**只把最难的部分抽出来，并且明确告诉别人这里的统计置信度是多少**。citeturn23search4turn17view3

**LOAD-BEARING TEST:**  
如果没有它，模型可以靠 dominant basin 拿到还不错的通用分数，却在 rare/barrier 区域完全失败而不被看见；这会直接削弱对“recover substates”的检验强度。  

**CONCRETE APPROACH:**  
- **Inputs required:** MetaD 重加权帧、state masks、barrier masks、active-site descriptors。  
- **Algorithm / protocol steps:**  
  1. 基于 \(p(s,z)\) 选出 low-population but converged bins。  
  2. 导出这些 bin 中的帧与重加权权重。  
  3. 记录 block ID、effective sample size、CI、state label、descriptor。  
  4. 提供最小下载包，方便别人不必重跑 MetaD 就能直接做 rare-state validation。  
- **Compute budget:** 分析级，<10 GPU-hours。  
- **Ground truth / reference data source + license:** 来自本项目生成的 MetaD/reweighting；数据包 CC-BY-4.0。  
- **v0 success criterion:** 至少 3 个 rare/barrier 区域拥有可接受 ESS 与可报告 CI；导出的 rare-state pack 可被 scorer 稳定调用。  
- **What the released artifact looks like:** `rare_frames.parquet`（frame_id, weight, block, s, z, state, descriptor...）；`states.md`；`how_to_use.ipynb`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `rare-state ensemble benchmark metadynamics block convergence error bars protein`、`reweighted rare-state ensemble with uncertainty metadynamics benchmark protein`。返回的是 block analysis、IDP 重加权、误差估计和 FES 收敛方法，而没有酶动力学 rare-state ensemble benchmark artifact。citeturn23search0turn23search4turn26search5turn17view3  
- **Non-triviality:** 真正新的是把 rare-state support、ESS、block uncertainty 一起打包；这不是常规 supplementary table。  
- **Load-bearing:** 它显式把 hardest-case evaluation 暴露出来。  
- **Reviewer attack surface:** “rare-state 定义主观。” 反驳：可以把 bin 频率阈值、ESS 阈值、CI 阈值都公开成数据文档的一部分。  

**FEASIBILITY:**  
- **Time to v0:** 1–2 周，依赖 C1 基础设施。  
- **Hardest step + mitigation:** 定义“rare but converged”；缓解办法是采用 frequency + ESS + CI 三条件。  
- **What could block:** 如果某些 barrier 区域 ESS 太低，rare pack 会很小。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** directly tests hardest cases。  
- **(b) cross-family substate recovery:** indirectly。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 给未来任何长时生成模型一个“别只在 dominant basin 好看”的压力测试。citeturn19view3turn33view0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，而且与 C1 形成明显 compound value。  
- **1-sentence interview pitch:** 我把最容易被 generative model 伪装过去的 rare states 单独抽出来，做成了一个有不确定性说明的压力测试包。  

**CONFIDENCE ON NOVELTY:** MEDIUM-HIGH（许多文章会报告 rare states，但我没有搜到把它做成公开 benchmark pack 的规范化实现）。

## 理论与诊断

候选池共有三项。保留两项：**滞后分层的记忆必要性判决**、**FDT 闭合审计**。淘汰一项：**“PLM embedding 是否吸收 K 的 state dependence”直接证伪试验**，理由是它太容易滑向架构/representation ownership，而且题设已经给了“没有公开 family-diverse enzyme corpus”这个硬限制，十周内做不出让人信服的跨家族统计。citeturn21view0turn21view1

**IDEA D1: Lag-stratified memory necessity test**  
**AXIS:** D  
**ONE-LINE CLAIM:** 用同一套 TrpB 粗粒/低维表示，同时比较 historyless 与 history-aware 基线，明确判定“这个表示下显式记忆到底是不是必需的”。

**NEAREST PRIOR ART:**  
- Ayaz 等，2021，PNAS——证明蛋白折叠的非马尔可夫模型与 memory friction 可以改善再现，但它告诉你“memory 可能重要”，不提供针对某个酶 coarse-grained 表示的**判决协议**。citeturn26search10  
- qMSM / IGME 教程与后续比较论文——系统介绍如何构建非马尔可夫动力学模型，也比较了 qMSM、macrostate projection 等方法的优缺点，但对象仍是“如何建模”，不是“如何在一个给定表示下裁决是否真的需要 memory”。citeturn36search1turn36search6turn36search11  
- MEMnets，2025——通过最小化时间积分记忆核来找慢 CV，本质是在“表示学习”层面处理 non-Markovianity，不是一个 benchmark-style diagnostic。citeturn35search0turn35search24

**THE GAP THIS CLOSES:**  
Amin 的质疑不是“有没有 non-Markovian 方法”，而是“**在 coarse-grained protein dynamics 上，non-Markovianity 是物理必需，还是因为表示太粗？**” D1 的新意就在于，它不再比“谁更 fancy”，而是比“在同一 observables 集合下，history-aware 模型是否显著改善 hold-out 动力学预测”。这把理论争论压缩成可实验判别的 benchmark。citeturn36search1turn35search0turn29view0

**LOAD-BEARING TEST:**  
如果没有这个诊断，提案里关于 memory kernel 的部分就会悬空：无论模型用了显式 memory 还是没用，你都无法回答“这个系统/表示下 memory 是否真的必要”。这是 Arvind–Amin 张力的正中央。  

**CONCRETE APPROACH:**  
- **Inputs required:** TrpB 轨迹在三套 observables 上的投影：COMM-only；COMM+PATHMSD；COMM+PATHMSD+少量 active-site descriptors。  
- **Algorithm / protocol steps:**  
  1. 对每套 observables 构建统一时间序列。  
  2. 拟合 historyless baseline：MSM 或一阶 Markov/AR。  
  3. 拟合 history-aware baseline：qMSM 或有限历史 AR/Volterra baseline，不涉及新深度架构。  
  4. 在 hold-out 轨迹上比较三个量：Chapman–Kolmogorov 误差、亚稳态 occupancy rollout 误差、MFPT / substate transition 误差。  
  5. 定义 **Memory Necessity Index**：当 history-aware 相对 historyless 在至少两项指标上获得统计显著改善时，判该表示“needs memory”；若加入更丰富 observables 后改进消失，则说明 earlier memory demand partly came from under-resolution。  
- **Compute budget:** 分析主导，<20 GPU-hours；若需补短无偏轨迹，再加 20–40 GPU-hours。  
- **Ground truth / reference data source + license:** 公共文献与本项目轨迹；诊断代码 MIT。  
- **v0 success criterion:** 至少找到一套表示使 MNI 明显 >0，且一套 richer 表示使 MNI 显著下降，从而形成**可证伪**结果。  
- **What the released artifact looks like:** `mni_results.csv`、`diagnostic_notebook.ipynb`、`ck_tests/`、`mfpt_curves/`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `Markov versus non-Markov coarse-grained protein dynamics benchmark memory kernel`、`qMSM tutorial 2024 protein dynamics memory kernel`、`Markov-Type State Models to Describe Non-Markovian Dynamics`。返回的是 non-Markovian 建模、教程与比较论文，但没有“same observables, same system, benchmark-style necessity decision”的公开协议。citeturn26search2turn26search10turn36search1turn36search6  
- **Non-triviality:** 这不是把 qMSM 跑一遍；关键是把“need memory?”从建模选择，变成可重复的模型诊断。  
- **Load-bearing:** 它直接回答 Amin 的核心质疑。  
- **Reviewer attack surface:** “这只是一个系统上的 case study。” 反驳：对提案验证来说，一个有代表性的 enzyme-anchored falsifiable test 已经足够有价值；外推到所有系统不是 v0 目标。  

**FEASIBILITY:**  
- **Time to v0:** 3–4 周。  
- **Hardest step + mitigation:** time-lag 选择与统计功效；缓解办法是只报告 few-lag regime，并配合 bootstrap CI。  
- **What could block:** 无偏长轨迹不足以稳定 MFPT；某些 observables 的 discretization 太噪。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** directly tests。  
- **(b) cross-family substate recovery:** NA 但极其 load-bearing。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 不是再比一个分数，而是定义了“为什么需要 memory/不需要”的裁决标准。citeturn18view0turn19view3turn35search0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，而且非常像一个独立、强逻辑的 methods note。  
- **1-sentence interview pitch:** 我没有主张应该用 memory，我先设计了一个能把“是否需要 memory”在 TrpB 上裁决出来的实验。  

**CONFIDENCE ON NOVELTY:** HIGH。

**IDEA D2: FDT-consistency audit for CG observables**  
**AXIS:** D  
**ONE-LINE CLAIM:** 在 TrpB 的 coarse observables 上显式估计 \(M\)、\(K(t)\) 与 orthogonal noise，检查 generalized FDT 是否闭合，并以此审计任何“只学 drift / 不管 noise”的 surrogate 是否物理自洽。

**NEAREST PRIOR ART:**  
- Lin 等，2021，data-driven Mori–Zwanzig——提出可从时间序列中提取 Markov term、memory kernel 与 orthogonal dynamics，并用 generalized fluctuation-dissipation relation 做自洽性验证；但案例是 Lorenz-96 等，不是酶 coarse observables。citeturn29view0turn31view1  
- PRL 2023 的 non-Markovian CGMD——强调 state-dependent memory 与 coherent noise 一起出现，说明“只加 memory、不管 noise”在物理上是不完整的；但它不是 enzyme-focused audit。citeturn26search34turn26search38  
- qMSM/IGME 相关教程——强调 memory kernel 的提取和难点，但没有围绕 surrogate claims 做 FDT audit。citeturn36search1turn36search17

**THE GAP THIS CLOSES:**  
题设里已经指出提案没有指定 fluctuation-dissipation noise model。D2 不是要重写理论，而是做一个特别硬的检查：**在你实际用于 surrogate 评测的 coarse observables 上，若提取到非零 memory kernel，那么对应噪声是否呈 colored/noise closure；如果没有，这个 reduced model 物理上就是不闭合。** 这把“memory/noise hand-waving”直接堵死。citeturn29view0turn31view1turn26search34

**LOAD-BEARING TEST:**  
没有这个审计，提案中的 memory-kernel component 可以一直停留在“加了一个更复杂 temporal module”，却没有回答 reduced dynamics 的噪声一致性问题。对于 coarse-grained protein dynamics，这会让物理解释处于半悬空状态。  

**CONCRETE APPROACH:**  
- **Inputs required:** TrpB projected observables 的长时间序列；两时间相关函数；Lin 2021 风格的 operator extraction 代码；白噪声 Markov 对照。  
- **Algorithm / protocol steps:**  
  1. 从 TrpB observables 估计两时间相关函数。  
  2. 用离散 Mori–Zwanzig / GLE 方法提取 \(M\)、\(K(t)\)。  
  3. 由残差重建 orthogonal noise \(F(t)\)，并计算 generalized FDT closure residual。  
  4. 对比 white-noise Markov null 与 colored-noise closure：看谁能更好再现 auto-correlation、cross-correlation 与 state occupancy decay。  
  5. 发布一个 **FDT closure scorecard**，可供未来任何 surrogate 结果对照。  
- **Compute budget:** 基本为分析；<15 GPU-hours。  
- **Ground truth / reference data source + license:** 来自公开数据与本项目轨迹；代码 MIT。  
- **v0 success criterion:** 在至少一套 coarse observables 上，white-noise null 明显无法再现相关函数，而 FDT-consistent closure 可以；closure residual 可重复。  
- **What the released artifact looks like:** `fdt_audit.ipynb`、`closure_score.csv`、`correlation_functions.npz`。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `fluctuation dissipation audit machine learning molecular dynamics surrogate protein`、`generalized Langevin equation protein coarse-grained memory kernel estimation fluctuation dissipation`。返回的是 GLE/MZ 理论文献与材料体系/一般系统，而没有 TrpB/酶 coarse observables 上的 surrogate-oriented FDT audit。citeturn12search1turn12search5turn12search10turn26search34  
- **Non-triviality:** 困难在于把抽象的 GFD 变成“任何人都能看懂的 closure residual + null comparison”，而不是停留在公式。  
- **Load-bearing:** 它直接处理了题设里点名的 noise-term 缺位。  
- **Reviewer attack surface:** “这仍然是 linear/GLE-based audit，未必适配复杂蛋白观测。” 反驳：正因为它是 audit，不是 final model，所以其价值恰在于给出一个最低物理一致性门槛。  

**FEASIBILITY:**  
- **Time to v0:** 2–3 周。  
- **Hardest step + mitigation:** 相关函数估计噪声；缓解办法是先在低维 observables 上做，避免高维爆炸。  
- **What could block:** 采样长度不足；closure residual 对 block 分割敏感。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** directly tests physical consistency。  
- **(b) cross-family substate recovery:** NA。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 把“是否物理上闭合”引入讨论，而不是只报 rollout quality。citeturn18view0turn19view3turn29view0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，而且尤其利于面试时体现“我抓住了 proposal 的最薄弱物理环节”。  
- **1-sentence interview pitch:** 我把提案里没有写清的 noise closure 问题，变成了一个能在 TrpB coarse observables 上直接审计的 FDT 测试。  

**CONFIDENCE ON NOVELTY:** HIGH。

## 综合叙事方案

候选池共有三项。保留两项：**ShiftBench-TrpB** 与 **Catalytic Path Fidelity Suite**。淘汰一项：**跨家族记忆核图谱**，理由同前——在“公开数据不足 + 不碰架构 ownership”的限制下，十周内很难做出真正可信的跨家族统计。citeturn21view0turn21view1

**IDEA E1: ShiftBench-TrpB**  
**AXIS:** E  
**ONE-LINE CLAIM:** 把 A1 + B1 + C1 + D1 组合成一个完整故事：既能评估序列扰动下的亚稳态偏移，又能裁决 coarse 表示下 memory 是否必要。

**NEAREST PRIOR ART:**  
- PLaTITO，2026——展示 pLM embeddings 改善 transferable implicit transfer operators 的 OOD equilibrium benchmarks，但不是 enzyme-specific mutation benchmark。citeturn18view0  
- STAR-MD，2026 / ConfRover，2025——把蛋白动态生成推向更长时间或同时建模 conformation+dynamics，但仍建立在通用 benchmark 与通用指标之上。citeturn19view1turn19view3  
- Monteiro da Silva，2024——做 mutation-induced conformational population prediction，但不是 MetaD-grounded、TrpB-anchored benchmark 套件。citeturn10view1

**THE GAP THIS CLOSES:**  
单个 idea 的价值都存在，但 E1 的组合价值更大：A1 定义任务，B1 给 sharp scorer，C1 给 ground-truth corpus，D1 则回答“如果模型失败，到底是没有学到 sequence-to-landscape，还是因为 coarse representation 需要 explicit memory”。这让结果不仅是“跑了一个 benchmark”，而是能解释 benchmark 失败的**因果诊断框架**。citeturn18view0turn19view3turn36search1

**LOAD-BEARING TEST:**  
如果没有 E1 这种组合，项目很容易散成几块：有数据没指标，或有指标没诊断，最后只能做“这里有个 TrpB case study”。E1 的作用就是把它变成一个完整 contribution story。  

**CONCRETE APPROACH:**  
- **Inputs required:** C1 语料；B1 scorer；D1 diagnostic；简易 baseline（不自创架构）。  
- **Algorithm / protocol steps:**  
  1. 先完成 C1 paired FES。  
  2. 从 C1 自动派生 A1 任务标签与 B1 scorer。  
  3. 用同一 observables 在 D1 上做 memory necessity diagnosis。  
  4. 发布 benchmark leaderboard skeleton：oracle split、random baseline、state-only baseline、history-aware classical baseline。  
- **Compute budget:** 基本等于 C1 + D1。  
- **Ground truth / reference data source + license:** 同 C1；整体仓库可 CC-BY/MIT 混合。  
- **v0 success criterion:** 形成一个外部组可直接下载运行的 benchmark package，且基线排序稳定、诊断结果可复现。  
- **What the released artifact looks like:** `shiftbench-trpb/` 仓库，包含数据、scorer、baseline、docs、paper-style benchmark card。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我搜到的是通用 protein dynamics benchmark、通用结构/动力学评估、以及单点 mutation population papers，但没有“enzyme mutation shift benchmark + memory necessity diagnostic”这一成套包。citeturn18view0turn19view3turn34view0turn10view1  
- **Non-triviality:** 这里的新意在 story architecture，而不是叠词缀；它把 benchmark 和 falsification glue 在一起。  
- **Load-bearing:** 它是最接近 proposal validation 的 SURF 完整交付。  
- **Reviewer attack surface:** “看起来像很多小想法的打包。” 反驳：正因为它们共享同一 TrpB MetaD 基础设施，组合后才产生解释力。  

**FEASIBILITY:**  
- **Time to v0:** 7–9 周。  
- **Hardest step + mitigation:** C1 地景先行，D1 诊断后置；避免并行摊太大。  
- **What could block:** C1 收敛慢会拖延所有上层模块。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** directly tests through path/state rollout baselines。  
- **(b) cross-family substate recovery:** indirectly，但先把 family-internal sequence conditioning 评测打牢。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 任何这些模型若想声称在酶上有效，都必须过这一关。citeturn18view0turn19view3  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是；它最像一篇独立的一作 benchmark/diagnostic paper。  
- **1-sentence interview pitch:** 我不是做了一个 TrpB case study，而是做了一个能验证并解释 sequence-conditioned enzyme dynamics claims 的完整 benchmark。  

**CONFIDENCE ON NOVELTY:** HIGH。

**IDEA E2: Catalytic Path Fidelity Suite**  
**AXIS:** E  
**ONE-LINE CLAIM:** 把 A2 + B2 + C2 + D2 组合成“路径是否对、rare state 是否对、化学是否对、noise closure 是否对”的四维评价套件。

**NEAREST PRIOR ART:**  
- Mac-Diff / 近年的 ensemble generators——评价以结构分布、TIC、RMSF、EMD 为主。citeturn33view0  
- metadynamics of paths / TS-DAR——分别提供 path-space data 与 transition-state identification，但都不是面向酶 surrogate 的统一 fidelity suite。citeturn17view0turn30view0  
- PLP/TrpB 化学文献——教会我们哪些主动位几何重要，但没有转成 surrogate 的标准评分协议。citeturn14search8turn15search8

**THE GAP THIS CLOSES:**  
E2 解决的是另一类“假阳性”：模型在通用结构指标和 basin 指标上都不差，但它的路径推进、barrier 支持、活性位几何甚至 reduced noise closure 任何一项都可能出错。E2 让“是不是像一个会催化的 TrpB 动力学集合”成为一个可量化问题，而不是审稿人口头直觉。citeturn33view0turn30view0

**LOAD-BEARING TEST:**  
没有 E2，proposal 的“recover substates consistent with metadynamics ground truth”就仍然偏弱，因为“consistent”只在构象统计层面，而没到催化相关 fidelity。  

**CONCRETE APPROACH:**  
- **Inputs required:** A2 的 \(p(s,z)\) 参考；B2 descriptor 参考；C2 rare-state pack；D2 FDT scorecard。  
- **Algorithm / protocol steps:**  
  1. 建立四个子分数：path fidelity、rare-state fidelity、catalytic readiness、FDT closure。  
  2. 对任意 generation result 输出单项分数与总雷达图。  
  3. 公开两种聚合方式：均权与“对酶更保守”的 min-operator。  
- **Compute budget:** 主要为分析。  
- **Ground truth / reference data source + license:** 来自项目内部公开数据工件；代码 MIT。  
- **v0 success criterion:** 该 suite 对至少两个明显不同的 baseline 给出一致且可解释的区分：例如某基线 path fidelity 尚可但 chemistry/FDT 差。  
- **What the released artifact looks like:** `cpf_suite/`，含四个 scorer、aggregate report、示例输出。  

**NOVELTY DEFENSE:**  
- **Existence gap:** 我运行了 `chemistry-aware catalytic readiness metric...`、`path-progress distribution matching PATHMSD benchmark...`、`fluctuation dissipation audit...` 等查询，返回的是分散在不同子领域的单块工作，没有四维组合 suite。citeturn25search2turn25search5turn12search10turn33view0  
- **Non-triviality:** 它不是指标堆砌；四项正好对应四种常见假阳性。  
- **Load-bearing:** 这是“更强版本的 proposal validation”。  
- **Reviewer attack surface:** “总分会掩盖单项解释。” 反驳：默认必须同时报告单项分数，aggregate 只做摘要。  

**FEASIBILITY:**  
- **Time to v0:** 7–9 周，依赖 A2/B2/C2/D2 共用基础设施。  
- **Hardest step + mitigation:** B2 与 D2 需要好好控规模；缓解办法是 v0 descriptor limited、closure 只在低维 observables 上做。  
- **What could block:** 某个子分数不稳定导致总 suite 过于噪声。  
- **Public-data-only check:** ✅  

**ALIGNMENT WITH ARVIND'S 3 TARGETS:**  
- **(a) long-horizon validity:** directly tests。  
- **(b) cross-family substate recovery:** indirectly。  
- **Additional value to Ramanathan+Anima beyond PLaTITO/STAR-MD/ConfRover:** 把“模型长得像 MD”推进到“模型像酶学上可信的 MD”。citeturn19view3turn33view0  

**ALIGNMENT WITH CALTECH/ANIMA JUDGMENT:**  
- **Is this defensibly a SURF-owned contribution:** 是，但比 E1 更依赖多模块全部站稳。  
- **1-sentence interview pitch:** 我把通用蛋白动力学评价升级成了一个面向 TrpB 催化语境的 fidelity suite。  

**CONFIDENCE ON NOVELTY:** MEDIUM-HIGH（单块都能找到邻近工作，但作为成套 suite 仍然新）。

## 对抗性红队结果

下面按你要求，对所有通过初筛的想法做 red team。这里不再重复文献事实，只给最强对抗论点与我对其的判断。

**A1**  
- **Skeptic steelman:** “这只是把已知 population-shift 预测换了个酶系统。”  
- **Competitor steelman:** 六个月内 entity["company","ByteDance","Beijing, China"] 或更新后的 PLaTITO 完全可以拿这个 benchmark 作为补实验；**但这恰恰证明 benchmark 值得做**，因为工具方最怕没有新 benchmark。  
- **Ablation test:** 去掉“signed shift”后，只剩普通 FES 数据集，贡献会明显变弱；**是单点风险，但还能退化为 C1**。  
- **Mori–Zwanzig / FDT consistency test:** 不直接碰 memory/noise，因此不手挥；安全。  

**A2**  
- **Skeptic steelman:** “PATHMSD 只是你选的一条坐标，任务可能 path-biased。”  
- **Competitor steelman:** 任何生成模型都能加一个投影头去报这个分数；六个月内很容易跟上。  
- **Ablation test:** 去掉 barrier occupancy 与 off-path \(z\)，任务价值会大幅下滑；**仍值得做，但必须保住二维分布而不是退成一维 s**。  
- **Mori–Zwanzig / FDT consistency test:** 不直接碰 memory，但可与 D1/D2 组合。  

**B1**  
- **Skeptic steelman:** “方向指标过粗，信息量不足。”  
- **Competitor steelman:** 很容易在半年内被别人补上。  
- **Ablation test:** 去掉 CI penalty 后，剩下只是 sign accuracy，贡献明显降级；**不是单点致命，但需要 uncertainty 才成立**。  
- **Mori–Zwanzig / FDT consistency test:** 不涉及。  

**B2**  
- **Skeptic steelman:** “经典 MD 上的化学几何代理不够接近真实催化。”  
- **Competitor steelman:** 竞争者可以很快补一个更 fancy 的活性位指标。  
- **Ablation test:** 去掉 state-conditional 只剩一堆距离统计，会失去核心新意；**这是单点风险，必须保住“状态条件化”**。  
- **Mori–Zwanzig / FDT consistency test:** 与 memory 无关，不手挥。  

**C1**  
- **Skeptic steelman:** “只有两个或三个变体，太小。”  
- **Competitor steelman:** 大组半年内可直接扩容。  
- **Ablation test:** 即使只剩 2 个 pair，它仍然是可用 benchmark；**不是单点赌注**。  
- **Mori–Zwanzig / FDT consistency test:** 可为 D1/D2 提供数据，不涉及噪声手挥。  

**C2**  
- **Skeptic steelman:** “rare-state 阈值是人为的。”  
- **Competitor steelman:** 竞争者很容易照着做一个近似版本。  
- **Ablation test:** 即使去掉总分，只保留 rare-state pack 也仍有价值；**不是单点赌注**。  
- **Mori–Zwanzig / FDT consistency test:** 不直接涉及。  

**D1**  
- **Skeptic steelman:** “一个系统上的 necessity test 不能推广到所有蛋白。”  
- **Competitor steelman:** 竞争者可以在半年内对更多系统复制。  
- **Ablation test:** 哪怕最后结论是“在 richer observables 下 memory 不再必要”，依然是贡献，因为它回答了题设张力；**不是单点赌注**。  
- **Mori–Zwanzig / FDT consistency test:** 触及 memory，但不回避 noise；因此最好与 D2 配套，避免只谈 kernel 不谈 noise。  

**D2**  
- **Skeptic steelman:** “FDT audit 太理论化，离生成模型实用评价太远。”  
- **Competitor steelman:** 先进组半年内可以做更高维、更漂亮的 audit。  
- **Ablation test:** 就算不把它接到 generative model，上交一个 enzyme-observable FDT audit 也仍具论文价值；**不是单点赌注**。  
- **Mori–Zwanzig / FDT consistency test:** 这是唯一一个**正面处理** noise closure 的想法，因此在 memory 相关 ideas 里最稳。  

**E1**  
- **Skeptic steelman:** “这是把几件小事捆一起，不是一个新 idea。”  
- **Competitor steelman:** 大组六个月后当然能吃掉，但 benchmark-first 的先发优势仍然值钱。  
- **Ablation test:** 去掉 D1 后它仍是强 benchmark；去掉 C1 则整体崩掉；**核心依赖 C1**。  
- **Mori–Zwanzig / FDT consistency test:** 通过 D1 接触 memory，最好在 paper 里把 D2 作为 future/appendix 补上。  

**E2**  
- **Skeptic steelman:** “四维 suite 太重，undergrad 容易做到每块都半成品。”  
- **Competitor steelman:** 一旦 community 接受这个方向，别人很快能做更全版本。  
- **Ablation test:** 去掉 FDT 或 chemistry 其中一项仍可成立，但会从“suite”退化成“metric bundle”；**不是单点赌注**。  
- **Mori–Zwanzig / FDT consistency test:** 已显式纳入 D2，因此一致性最好。  

总体红队结论很明确：**真正稳的不是单个 fancy metric，而是 C1 / D1 / E1 这条线。** B2 与 E2 很有辨识度，但它们更依赖主动位 descriptor 设计得足够克制。  

## 排名、组合与不做清单

**A. Top 3 ideas ranked on load-bearing × feasibility × defensibility**

我用 5 分制打分，乘积逻辑等价于你要求的三维排序。

- **E1 — ShiftBench-TrpB**：load-bearing 5，feasibility 4，defensibility 5，**总分 14/15**。它最接近“一个完整小论文/独立贡献”的形状，而且直接服务于提案验证。  
- **D1 — Lag-stratified memory necessity test**：load-bearing 5，feasibility 5，defensibility 4，**总分 14/15**。它最锋利地回应 Amin 提出的核心张力，而且不要求你造新架构。  
- **C1 — Mutation-matched FES pair corpus**：load-bearing 5，feasibility 4，defensibility 4，**总分 13/15**。它是所有上层想法的地基，最不容易被审稿人说成“只是帮别人跑模型”。  

如果你更重视“面试辨识度”而不是最稳妥的主线，我会把 **B2** 作为 honorable mention，因为它最像一句话就能说清楚的 sharp innovation。citeturn18view0turn19view3turn34view0

**B. One portfolio combination**

我建议的组合是：**C1 + D1 + B2**。  
理由很直接。C1 给你共享的 TrpB MetaD 基础设施与 paired landscape；D1 用同一批轨迹回答“memory 到底需不需要”；B2 把评价从“像不像 MD”推进到“像不像一个化学上准备好催化的 TrpB 集合”。这三者一起做，有三个优点：  
其一，同一套轨迹和统一坐标系，复用率最高；  
其二，既有 benchmark artifact，也有 diagnosis，也有 enzyme-specific metric，不会显得单薄；  
其三，避免最重的 E2 套件化风险，又比单做 C1 更有故事。citeturn8view0turn33view0turn29view0

**C. Named contribution story**

> “In 2026 the field of enzyme-focused sequence-conditioned protein dynamics has a specific limitation: models are evaluated mostly on generic structural-distribution metrics and broad MD datasets, so mutation-induced catalytic substate shifts in enzymes remain weakly testable. This work contributes a TrpB-anchored benchmark-and-diagnostic package for sequence-conditioned dynamics. It does so by releasing mutation-matched free-energy landscape pairs, defining shift-sensitive and chemistry-aware metrics, and adding a falsifiable memory-necessity diagnostic on the same coarse observables. This is novel because prior art can predict broad conformational populations, learn slow CVs, or generate long trajectories, but does not provide a MetaD-grounded enzyme benchmark that simultaneously tests substate shifts, path fidelity, catalytic readiness, and whether explicit memory is actually needed. This matters because without such a package, key claims about long-horizon validity and metadynamics-consistent substate recovery in enzyme dynamics remain only loosely verifiable.” citeturn10view1turn18view0turn19view3turn35search0turn34view0

**D. What I would NOT do and why**

我明确不会做下面三件事：

- **“在 TrpB 上微调或扩展 STAR-MD / ConfRover”**。这直接违反你的硬规则：它会变成别人架构论文的补实验，而且 novelty 太弱。现有长时蛋白动力学模型已经在 ATLAS/通用指标上卷得很深。citeturn19view1turn19view3  
- **“自己做一个 sequence-conditioned operator / RNO 新架构”**。这会撞上 PLaTITO 已占领的空间，也违反“no architecture ownership”的边界；而且公开酶数据的 family-diverse 缺口使得你很难在十周内做出可信的跨家族 generalization claim。citeturn18view0turn21view0turn21view1  
- **“直接做跨家族 learnable memory-kernel transfer 的实证论文”**。这在 field-level 很诱人，但题设已经告诉你公开数据不够、而且从系统设计到统计功效都会把项目拖进不可控区；对 SURF 来说，这是高风险低完成度路线。citeturn21view0turn21view1turn34view0

最后给出一句最实用的选择建议：如果你只选一条主线，选 **E1/其精简版 = C1 + D1**；如果你想再加一个最有辨识度的小而硬创新，补 **B2**。这套组合最符合你当前身份、时间、算力和“不能抢架构 ownership”的真实边界，同时也最容易在 entity["organization","Caltech","Pasadena, CA, US"] / summer placement / proposal owner 三方眼里被看成“这不是我帮别人做实验，而是我自己定义了验证问题”。