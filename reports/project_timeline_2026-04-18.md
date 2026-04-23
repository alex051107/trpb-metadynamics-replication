# Ramanathan / Anandkumar Lab 项目时间线（基于 Slack history 重建）

**作者**: 给用户（Zhenpeng）自用，理清进入 lab 之前 + 这段时间发生了什么
**数据源**: `reports/tools/slack_history.md` (1197 行, 涵盖 2026-01 → 2026-04-11) + `papers/reading-notes/` + STAR-MD paper + 4/17 Yu meeting notes
**更新**: 2026-04-18

---

## 一、项目核心使命（多人反复确认，可信度高）

**把 L-serine + indole → L-tryptophan 的 TrpB（色氨酸合酶 β 亚基）通过 de novo 重设计，变成 D-serine + indole → D-tryptophan 的酶。**

- 核心反应: D-serine external aldimine（D-外部醛亚胺，D-AEX）= TS proxy
- 关键难点 — Raswanth 4 月底指出: Cα-H 被夺去之后，中间体变成**平面 quinonoid**，手性信息丢失。即使 D-serine 被稳定进活性位点，若不控制 indole 进攻方向和 reprotonation 几何，产物可能还是 L-Trp。
- Dunathan hypothesis（PLP 酶通用原理）: Cα-H 与 PLP π-system 呈 ~90°，促进 Cα-H cleavage。

## 二、谁在干什么（Slack 证据）

| 人 | 负责 | 关键 artifact |
|----|------|--------------|
| **Raswanth Murugan** (remote, Anima 学生) | RFD3 → MPNN → RF3 pipeline；GRPO reward function | 12 个 theozymes × 300–350 sequences = ~5k 序列（4/4 完成）；GRPO F0 `tier2_docking.py` |
| **Yu Zhang** (张瑜，章鱼) | MD calculations；MMPBSA binding energy；theozyme 模型生成 | 100+ MD 模拟；12 theozymes + 301K theozyme；4/11 推出 #1106 (BE=-114.7) 和 #1082 (-84.6) |
| **Amin Tavakoli** | Docking pipeline (AutoDock Vina)；XPO 探索项；104-109/298 mutation library；**protein dynamics benchmark (SURF)**；GenSLM ML 模型本体 | 8000-variant docking；XPO in pipeline；STAR-MD working version (3/6) |
| **Arvind Ramanathan** (advisor, Argonne) | Strategic direction；HPC access；review | 反复要求"cluster seqs by active site / see chemistry lining up" |
| **Anima Anandkumar** (PI, Caltech) | 定方向；论文分享；进度催促 | 每周在 Slack 发新 papers；反复催 updates |
| **Ziqi** (wet-lab collaborator) | 湿实验验证 (~1 week/plate, ~$10k/plate) | Elegen / Twist vendor 讨论 (3/6) |
| **章鱼 (Yu) + Amin**: 两个 SURF 提案的 co-advisors | | |
| **Zhenpeng (我)** | **SURF student — 两条线混淆** | |

## 三、两条 SURF 线的分裂（这是问题的根源）

### 线 A: Amin 带的 "Protein Dynamics Benchmark" SURF 项目

**3/6 Slack line 1023** (Amin 的 weekly update):
> "Set up the protein dynamic benchmark for the SURF student. There is a nice work on long horizon prediction of dynamics using SE3 diffusion models: https://arxiv.org/html/2602.02128v2. **I created a working version of it and will share with the SURF student.**"

**关键事实**:
- Amin 在 group channel 公告了这个任务，**没有在 1-on-1 里直接 handoff 给 Zhenpeng**
- "I created a working version" — 说明 Amin 已经有可跑的 codebase（可能是 STAR-MD 作者 repo 的 fork，或自己复现）
- **4/11 Amin follow-up (line 1152)**:
  > "for the protein dynamic project (SURF), I learned that protein dynamics are not Markovian if the protein representation is not all-atom (coarse grain). This is related to **Mori-Zwanzig formalism**… I am trying to study more and potentially find efficient ways to model this."
- 这说明 Amin 仍在持续思考这条线 + 期望 SURF student 参与

### 线 B: Yu Zhang 带的 "OpenMM MetaDynamics Osuna 复刻" SURF 项目

**3/21 Slack line 1123** (Yu 的 weekly update):
> "I have worked with **Zhenpeng Liu** on metadynamics setup. In the literature, metadynamics is most commonly performed using PLUMED with GROMACS or AMBER. Since this project already uses OpenMM for MD, and OpenMM can support metadynamics either through its built-in API or through the openmm-plumed plugin, **we plan to run a quick test of these approaches. The goal is to determine whether OpenMM can reproduce results similar to those in Osuna's paper**. If so, we can modify our current MD code to strengthen the existing pipeline."

**关键事实**:
- Yu 主动拉 Zhenpeng 进 MetaD 方向
- 工具链定为 OpenMM（lab 现有 MD 代码是 OpenMM），但 Osuna 2019 是 GROMACS + PLUMED
- Plan 是 "quick test" → "modify our current MD code to strengthen the existing pipeline"
- 我这 6 周一直在做这条，因为 Yu 是我日常沟通的人

### 为什么 Zhenpeng 不知道线 A 存在

1. Amin 从未在 1-on-1 / 邮件 / 直接消息里跟 Zhenpeng 沟通
2. Zhenpeng 此前**看不到 Slack 历史**（今天才补上）
3. Zhenpeng 的日常 1-on-1 是跟 Yu 做的（Yu 每周 4/17 式会议跟进 MetaD 进度）

**这不是 Zhenpeng 的单方面 "我没跟进 Amin" 失误**，是三方沟通漏洞:
- Amin 公告没点名 → Zhenpeng 不认为那是自己的任务
- Yu 拉人进 MetaD → Zhenpeng 把 Yu 当主带人
- Slack 历史不可见 → 无法 cross-check

## 四、项目时间线（按月）

### 2026 Jan（上月）
- Raswanth 在 Polaris 上把 RFD3 multi-node scaling 搞通
- Amin 跑 104/298 mutation docking (8000 variants)
- Yu 做 MD top-10 候选 + MMPBSA

### 2026 Feb
- Amin 修了 docking bug (wrong center) + 重新跑；XPO 加进 pipeline
- Yu 发现 "electronic effect" 可能被模型低估（Anima 质疑，Yu 没回答清楚）
- Anima: "weekly meeting with Raswanth (remote)" 指令；反复催 Amin updates
- Raswanth 开始 GRPO reward function 设计，走 Dunathan + quinonoid + reprotonation 路线

### 2026 Mar
- **3/6**: Amin 建 STAR-MD SURF working version（**key missed handoff**）
- Yu + Amin 敲定 12 个新 theozyme（104-109, 298, 301 sites）
- Raswanth 跑 RFD3 for 12 theozymes → ~5k 序列
- Ziqi 进来谈 wet lab (1 plate/week, $10k/plate)
- **3/21**: Yu 在 weekly update 宣布和 Zhenpeng 做 OpenMM MetaD（**SURF 线 B 正式开始**）

### 2026 Apr (至 4/17)
- 4/4: Raswanth 改方向 — F1/F2 不进 GRPO, 只走 MFBO; F0 (PLACER-like) 进 GRPO
- 4/9 (我的视角): 发现 PATHMSD 问题，修好 path CV 生成
- **4/11 Amin**: 提 Mori-Zwanzig 作为 SURF 项目关键考量
- 4/15 (我): 修 SIGMA collapse (FP-024)，Job 44008381 开跑
- 4/17 (我): Yu 1-on-1 确认 SIGMA fix + 给出 Phase 2 decision gate
- 4/17 (我): 发 Maria-Solano 邮件问 SIGMA + alignment（Osuna 没回）

## 五、关键推断（需要跟 Amin 确认）

1. **Amin 可能认为 Zhenpeng 同时做线 A 和线 B** — 因为他在 3/6 公告后，没有 Zhenpeng 的线 A 进展，可能以为 Zhenpeng 偷懒或能力不够
2. **Amin 的 4/11 Mori-Zwanzig 评论** 是他期望 SURF student 深入的方向 — 他不是想要 benchmark engineer，是想要能跟他讨论 non-Markovian 动力学的人
3. **章鱼/Yu 可能没把线 B 的优先级跟 Amin 对齐** — 所以 Amin 不知道 Zhenpeng 其实在 Yu 的指令下
4. **"partially being solved" 的意思**: STAR-MD 论文自己在 p.11 Conclusion 明说:
   > "a promising direction for future work is to extend the model's capabilities to **simulate the dynamics of protein complexes or their interactions with small molecules**, which are crucial for understanding biological processes and drug design."
   - 翻译: STAR-MD 解决了**无配体蛋白的平衡采样 + microsecond 稳定性**，但**没解决配体结合动力学（PLP + 底物）和蛋白复合体动力学** — 恰好是 TrpB 需要的
   - 也没解决: rare-event 采样（MetaD 的本职），sequence-conditioned engineered variants（突变扫描），实验动力学验证（NMR / rate）

## 六、作为本科生，实际能做什么（初步想法，待跟 Amin 讨论）

**不能做的**: 改 STAR-MD 的网络架构、重新训练、证明 Mori-Zwanzig → 这是 PhD-ML 级工作

**可以做的**（按可行性排序）:

### 1. Benchmark STAR-MD 在 TrpB 上的 failure modes（最可行）
- 拿 Amin 的 STAR-MD working version，在 TrpB-apo + TrpB-PLP-AEX (有配体) 上跑
- 对比: STAR-MD 的 tICA / JSD / AA% 在 "无配体" vs "有配体" 上有多大差
- 预期: 有配体会崩，因为 STAR-MD 训练数据 ATLAS 不含 ligand
- **Output**: 一张实验图 + 一段话，说"这就是 paper Conclusion 里承认的 gap，我在 TrpB 上量化了它"

### 2. 用 MetaDynamics 生成 STAR-MD 够不着的 ground truth（配合线 B 已有工作）
- 我现在的 O→C MetaD 跑完就是一份 biased FES
- 跑在 ~3-5 个 GenSLM-designed 突变体（Yu 已经有候选）上
- **Output**: 突变体的 COMM 域 O→PC→C 自由能面 — 给 GenSLM / GRPO reward 用，或给 STAR-MD 当 test set

### 3. 测试 TrpB 的 O→C 是不是 Markovian（对接 Amin 的 4/11 思考）
- MetaD + reweighting 可以算 rate constants
- 同样的起点用短 unbiased MD 跑多轨 → 算 MSM Markovian assumption 有多强
- 对比: 如果 MSM 能复现 MetaD rates → Markovian 没问题；否则需要 memory kernel → 呼应 Amin 思考方向
- **Output**: 一个定量答案 "TrpB O→C 需不需要 memory kernel correction"

### 4. 读 Ayaz/Dalton PNAS 2021/2023 memory kernel 论文 + 跟 Amin 讨论应用到 TrpB
- 纯 reading + discussion，不写代码
- 可以作为 "intellectual contribution" 展示

这四条中，(1) + (2) 是最"本科生可交付"的；(3) 有一点难但值得尝试；(4) 让 Amin 觉得我在跟他同一个频道思考。

## 七、风险与担忧

- **期末周 (4/25 前)**: 实际每周可用时间 ~15-20 小时，不能同时开四条
- **Osuna 没回信**: 影响线 B 可信度；若 4/22 前还没回，line A 优先级可以提高
- **章鱼视角 vs Amin 视角**: 我需要跟章鱼先 sync 一下，不能让他觉得我突然切线导致线 B 掉链子

---

**下一步**: 发邮件给 Amin 约 Wed 4/23 2-3pm CT, 承认我之前没看到 3/6 announcement, 提 (1)(2) 作为具体 proposal, 留 (3)(4) 当会议讨论点。**不 CC 章鱼**（避免他被动），发完后单独跟章鱼 Slack 说一声。
