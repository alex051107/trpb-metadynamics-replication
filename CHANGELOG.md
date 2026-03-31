# Changelog

> 每次工作后记录：日期、做了什么、遇到什么问题、做了什么决策。
> Cowork 和 Claude Code Terminal 都应该往这里追加。

---

## 2026-03-31 (Claude — 文献调研 + Codex 协作 + Critical Thinking 框架)

### PLP 参数化文献调研（4 篇论文）

通过 Zotero MCP + Web Search 查了 4 篇论文，解决了 SI 没写清楚的两个问题：

**问题 1：PLP 总电荷是多少？**
- JACS 2019 SI 只说了"用 RESP 算电荷"，没给具体数字
- 找到 Caulkins et al. (JACS 2014, DOI: 10.1021/ja506267d) — 固态 NMR 实验
- NMR 直接测量了 4 个基团的质子化状态 → 推导出总电荷 = **-2**
- 用 Huang 2016 (ProtSci) 和 Kinateder 2025 (ProtSci, Osuna 组最新) 交叉验证

**问题 2：需要 ACE/NME capping 吗？**
- dispatch 给 Codex 分析
- 结论：**需要**。LLP 是 polymer-linked 残基，不是 free ligand。不加帽会在断口处产生错误电荷
- ACE 从 HIS81 CA/C/O 取坐标，NME 从 THR83 N/CA 取坐标
- 来源：AMBER advanced tutorial §1 + basic tutorial A26

### Gaussian Job 提交

- Job **40364008** on Longleaf
- 55-atom ACE-LLP-NME fragment, HF/6-31G(d), charge=-2, multiplicity=1
- 预计几小时完成

### 文件变更

| 文件 | 变更 |
|------|------|
| `replication/validations/2026-03-30_plp_protonation_literature_review.md` | **新建** — 4 篇论文调研记录 |
| `replication/validations/2026-03-30_capping_analysis.md` | **新建** — Codex 的 capping 分析报告 |
| `replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt` | **新建** — 加帽后的 Gaussian 输入 |
| `replication/parameters/resp_charges/ain/submit_gaussian_capped.slurm` | **新建** — 提交脚本 |
| `scripts/build_llp_ain_capped_resp.py` | **新建** — 从 5DVZ 自动生成加帽 Gaussian 输入 |
| `PROTOCOL.md` | **更新** — 新增 PLP Parameterization Sources 章节（DOI + 原文引用） |
| `NEXT_ACTIONS.md` | **更新** — 质子化态确认、PI 反馈、reading tasks 加入思考提示 |
| `project-guide/CRITICAL_THINKING_PROMPTS.md` | **新建** — 论文阅读 5 层拆解框架 + 本项目思考题 |

### Claude+Codex 协作记录

| 任务 | 谁做的 | 结果 |
|------|--------|------|
| 文献调研（4 sources） | Claude (Zotero + Web) | charge=-2 confirmed |
| Capping 分析 | Codex | 必须 cap，写了完整报告 |
| Gaussian 输入生成 | Codex (脚本) + Claude (review + GESP fix) | 55-atom ACE-LLP-NME |
| 上传 + 提交 | Claude (SSH) | Job 40364008 |

---

## 2026-03-30 (Claude Code Terminal — PI 反馈响应 + 全面追赶)

### PI 反馈（周报回复）

- 复刻 Osuna 组 SI 中的 TrpB 搭建流程
- PLP 参数化用 Gaussian 生成电荷 → 构建力场参数
- PI 会找 PLP 参数化 tutorial
- 搞清楚完整流程后安排 meeting review

### 完成的事

- **SI Protocol 完整提取**（3 个 parallel agent）:
  - 从 JACS 2019 SI 提取了 5-phase 系统搭建 protocol
  - 标注了 10 个 SI gap（含严重度评级）
  - 最关键 gap：PLP 共价键处理、质子化状态、AMBER→GROMACS 转换

- **PDB 残基名验证**（从实际 PDB 文件 + RCSB 查询）:
  - 5DVZ (Ain): **LLP** — 24 heavy atoms（PLP-K82 Schiff base 共价体）
  - 5DW0 (Aex1): **PLS** — 22 heavy atoms（PLP-Serine 外部亚胺）
  - 4HPX (A-A): **0JO** — PLP-aminoacrylate（S. typhimurium，仅作结构模板）
  - Q2: 无晶体结构（需从 MD snapshot 或建模获得）

- **`parameterize_plp.sh` 重写**（501 → 754 行）:
  - 修复 3 个 HIGH 级 bug：残基名 PLP→LLP/PLS/0JO、`head -1` → 全原子提取、添加 ACE/NME capping
  - 添加：chain 选择逻辑、atom count 验证、charge/multiplicity 表、Gaussian 16 更新
  - 所有需要人工决策的地方标注 `[HUMAN DECISION]`

- **PLP + 体系搭建 Logic Chain 文档**（1248 行，12 章）:
  - `project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md`
  - 从 PDB 到 MetaDynamics-ready 的完整逻辑链
  - 包含 PI meeting 议题清单和 SI gap 严重度表
  - 风格与 FULL_LOGIC_CHAIN.md 一致

- **JACS 2019 速读 Brief**:
  - `papers/reading-notes/JACS2019_SpeedBrief.md`
  - 30 分钟读完版本，含 PI 可能问的 5 个问题 + 答案

- **Coordinator Agent 创建**:
  - `.claude/agents/trpb-coordinator.md`
  - 内置 review 三道门（pre-execution / post-execution / cross-check）
  - 调度现有 Runner/Skeptic skill

- **项目状态文件更新**：CLAUDE.md, NEXT_ACTIONS.md, CHANGELOG.md

### 关键发现

| 发现 | 影响 |
|------|------|
| 现有脚本 grep "PLP" 匹配不到任何残基 | 如果直接跑会静默失败 |
| LLP 已包含 K82 backbone 原子 | 不需要额外提取 K82，但需要 capping |
| 4HPX 是 S. typhimurium 不是 P. furiosus | 只能用作结构模板，不能直接参数化 |
| Gaussian 16c02 可用（非 09） | 兼容，无需担心 |

### 决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Agent 架构 | Coordinator + 现有 skills（非 team） | 单线程关键路径，team 过重 |
| PLP 优先级 | Ain (LLP) 先做，其他中间体后续 | Phase 1 目标只需 Ain |
| 脚本状态 | REFERENCE/TEMPLATE，标注 HUMAN DECISION 点 | 质子化等科学决策需要人工确认 |

---

## 2026-03-28 (Claude Code Terminal 第三轮 — Agent Team)

### 完成的事

- **全项目 Fact-Check (5 parallel agents)**:
  - MetaDynamics 参数 vs SI: 95-97% 准确，修正了 PfTrpA-PfTrpB0B2 系统分配错误 (Q2 only, not Q2+Ain)
  - FULL_LOGIC_CHAIN: HIGH reliability，无 AI 幻觉，kcat 数据需对照原文确认
  - Glossary/PDB: 7 个 PDB 全部验证正确，修正 H6 helix 残基顺序 (174-164→164-174)，补充 COMM 域编号说明
  - 阅读笔记: 修正了 JACS2019 笔记中把 K82-Q2 distance 误标为 MetaD CV 的错误（实际 CV 是 s(R)/z(R)）
  - 项目状态: CLAUDE.md 路径错误修正，缺失里程碑补充，论文计数更新 (4→5)
  - NatComm 2026 论文 + GenSLM-230: Zotero 验证确认真实存在

- **Alanine Dipeptide Toy Test (任务 1)**:
  - 修了 Cowork 脚本 3 个 bug: ACE PDB 原子名、PLUMED 原子索引 (4,5,6,7→5,7,9,15)、conda 路径
  - 完成: pdb2gmx → solvate → minimize → NVT heating → NPT equilibration
  - MetaDynamics Job 39960327 正在运行 (HILLS + COLVAR 正在生成)

- **PDB 下载 (任务 2 + 额外)**:
  - 1WDW (2.4MB), 3CEP (469KB) → path CV 端点
  - 4HPX (1.1MB), 5IXJ (2.1MB) → CAVER 参考 + 底物结合几何

- **Gaussian 可用性 (任务 4)**:
  - Gaussian 16c02 ✓, ORCA 6.0/6.1 ✓ → PLP RESP 参数化可行

### 修正的文档

| 文件 | 修正内容 |
|------|---------|
| replication/parameters/JACS2019_MetaDynamics_Parameters.md | PfTrpA-PfTrpB0B2 = Q2 only; SHAKE 描述修正 |
| CLAUDE.md | PDF 路径修正 (根目录→papers/)，缺失里程碑补充，论文计数 4→5 |
| papers/reading-notes/JACS2019_ReadingNotes.md | CV 误标修正: 3个CV→2个Path CV (s(R),z(R)) |
| GLOSSARY.md | H6 helix 164-174; COMM domain 编号说明 (PfTrpB vs StTrpB) |
| CLAUDE_CODE_TODO.md | 任务 1/2/4 完成标记 |

### 遇到的问题

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| pdb2gmx "Atom N in residue ACE not found" | Cowork 写的 PDB 原子名不符合 AMBER 力场 ACE 定义 | 重写 PDB (CH3/C/O, 无 N) |
| PLUMED 原子索引全错 | Cowork 用了旧 PDB 的索引，未考虑 pdb2gmx 重排 | 从 .gro 文件确认正确索引 |
| OMP_NUM_THREADS 冲突 | Slurm 设 OMP=1 但 -ntomp=4 | 重写 submit 脚本，显式 export OMP_NUM_THREADS=4 |

### 待完成

| 项目 | 状态 |
|------|------|
| MetaD Job 39960327 分析 (analyze_fes.py) | 等 job 完成 |
| Path CV 生成 (任务 3) | PDB 已就位，可以开始 |
| PLP 参数化 (任务 5) | Gaussian 可用，可以开始 |

---

## 2026-03-28 (Cowork 深夜 - 脚本批量生成)

### 完成的事

- **SI 参数 fact-check**：逐项对照 SI PDF 图片和参数表，所有 10+ 个关键参数全部匹配
  - SHAKE 描述修正：约束的是水分子几何（H-O-H 角 + O-H 键），不只是氢键角
  - 注意到加热步骤有 7 步但只列了 6 个 restraint 值（最后一步可能无约束）
- **Toy alanine 全套脚本**（10 文件）：`replication/scripts/toy-alanine/`
  - setup_alanine.sh, plumed_metad.dat, run_metad.mdp, submit_metad.slurm, analyze_fes.py
  - 4 份文档（README, QUICKSTART, INDEX, MANIFEST）+ validate_setup.sh
- **O→C 参考路径生成脚本**：`replication/scripts/generate_path_cv.py`（750+ 行）
  - 自动下载 1WDW/3CEP，序列比对，结构对齐，15 帧线性插值，PLUMED PATH 格式输出
  - 附 README + QUICKSTART
- **PLUMED MetaD 输入模板**：
  - `plumed_trpb_metad.dat`（多 walker 版，249 行）
  - `plumed_trpb_metad_single.dat`（单 walker 版，138 行）
  - 所有参数直接来自 SI：HEIGHT=0.628 kJ/mol, PACE=1000, BIASFACTOR=10, TEMP=350
- **PLP 参数化工作流**：`parameterize_plp.sh`（500 行）+ README（482 行）
  - 支持 BCC（快速）和 RESP（精确）两种电荷方案
  - 覆盖 4 个中间体：Ain, Aex1, A-A, Q₂
- **CLAUDE_CODE_TODO.md**：给 Claude Code Terminal 的完整执行指令
  - 5 个任务，按优先级排序，每个任务有完成标准
- **NEXT_ACTIONS.md**：创建了 Cowork ↔ Claude Code Terminal 共享任务队列
- **Full Logic Chain 文档**：12 章从零开始的项目全景（`project-guide/FULL_LOGIC_CHAIN.md`）

### 关键架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Cowork ↔ Claude Code 协作方式 | 通过共享文件（NEXT_ACTIONS.md, CLAUDE_CODE_TODO.md）| Cowork 没有 SSH，写好脚本让 Terminal 执行 |
| Toy test 用 alanine dipeptide | 标准 MetaD benchmark，2700 原子，1 小时跑完 | 验证工具链，不浪费计算资源 |

---

## 2026-03-28 (Claude Code Terminal 晚 - 第二轮)

### 完成的事

- **GROMACS 安装成功**：conda-forge gmx 2026.0 in trpb-md env，`-plumed` flag ✓
- **项目文件夹整理**：
  - 根目录从 ~25 个文件精简到 12 个
  - 重复 PDF、旧 dashboard、repro-workflow-old 等移到 archive/
  - paper-annotation skill 移到 .claude/skills/
- **Peer review 生成**：`papers/reviews/JACS2019_PeerReview.md` — peer-review skill demo
  - 关键发现：原文没有 error bar，复刻成功标准建议放宽到 ±1.5 kcal/mol
- **小红书 MCP 安装**：rednote-mcp 已添加到 Claude Code + Claude Desktop
- **Status bar 配置**：`cs` (claude-statusbar) 添加到 settings.json

### 新增 MCP

| MCP | 用途 | 配置位置 |
|-----|------|---------|
| Zotero | 文献管理（166 篇已索引） | user scope |
| 小红书 (rednote-mcp) | 搜索/读取小红书帖子 | user scope + Claude Desktop |

---

## 2026-03-28 (Cowork 晚上)

### 完成的事

- **NatCommun2026 深度标注 HTML**：从 Zotero 拉全文 → 生成 50KB 双栏标注 HTML（之前是 0 字节空文件）
- **NatCommun2026 阅读笔记**：`papers/reading-notes/NatCommun2026_ReadingNotes.md`（9.3KB）
- **ProtSci2025 阅读笔记**：`papers/reading-notes/ProtSci2025_ReadingNotes.md`（8.3KB）
- **paper-annotation-skill.skill 解析**：提取了 SKILL.md + styles.css，确认了标注格式规范
- **Paper 阅读体系完善**：现在 4 篇核心论文都有 reading notes + deep annotation HTML

### 关键讨论

- **MetaDynamics 作为 Reward Function**：确认了 FEL 特征（ΔG(closed), barrier height, K82-Q₂ distance）可以组合成 scalar score 反馈给 GenSLM 设计循环
- **FEL 为什么是筛选工具**：Osuna 发现 TrpB 活性 ∝ Closed 构象稳定性，所以 FEL 上 Closed 态深度 = 活性预测器

---

## 2026-03-28 (Claude Code Terminal)

### 完成的事

- **AnimaLab 目录创建**：在 Longleaf `/work/users/l/i/liualex/AnimaLab/` 创建项目目录
  - 子目录：structures/ parameters/ scripts/ runs/ logs/ analysis/
  - 以后所有 Longleaf 上的工作文件都放这里
- **SSH ControlMaster 配置**：`~/.ssh/config` 配好 ControlMaster，Mac Terminal 保持一个 SSH 连接，Claude Code 可以免密复用
  - Socket: `~/.ssh/sockets/liualex@longleaf.unc.edu:22`
- **Longleaf .bashrc 修复**：添加 `module load anaconda/2024.02`，清理重复 PLUMED_KERNEL 行
- **Claude Code 工具安装**：
  - `ccusage`：token 用量监控（`npx ccusage@latest`）
  - `claude-statusbar (cs)`：底部状态栏实时显示用量
  - Zotero MCP (54yyyu)：文献管理 MCP，166 篇已索引
  - K-Dense 科学技能包：8 个技能（molecular-dynamics, scientific-writing, literature-review, pdb-database, scientific-visualization, docx, research-lookup, peer-review）
- **weekly-report skill 路径修复**：Cowork session 硬编码路径 → Mac 本地路径
- **环境验证**：
  - AMBER 24p3: `module load amber/24p3` → pmemd.cuda ✓
  - PLUMED 2.9: `conda activate trpb-md` → plumed info --version ✓
  - GROMACS 系统模块 (2021.5/2025.2/2026.0): 可用但**无 PLUMED 支持**

### 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Longleaf 项目路径 | `/work/users/l/i/liualex/AnimaLab/` | 统一管理，Home 目录空间不够 |
| GROMACS 安装方式 | conda-forge（在 trpb-md 环境内） | 系统模块无 PLUMED patch |

### 遇到的问题

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| SSH socket 为空 | 用户在 sockets 目录创建前就连接了 | 重新用 `ssh longleaf` 连接 |
| conda: command not found (非交互 SSH) | .bashrc 缺少 module load anaconda | 添加到 .bashrc |
| 系统 GROMACS 无 PLUMED | 预编译版本没有 PLUMED patch | 改用 conda-forge 安装 |

---

## 2026-03-27

### 完成的事

- **SI 参数提取**：从 `ja9b03646_si_001.pdf`（JACS 2019 SI）提取了完整的 MetaDynamics 参数
  - 写入 `replication/parameters/JACS2019_MetaDynamics_Parameters.md`
  - 更新了 campaign manifest 状态为 `parameters-confirmed`
- **CLAUDE.md 创建**：在项目根目录创建了共享状态文件，Cowork 和 Claude Code Terminal 都读这个
- **RULES.md 创建**：工作风格规则文件
- **GLOSSARY.md 创建**：名词解释表
- **MetaDynamics 逻辑链文档**：写了 `project-guide/MetaDynamics_Logic_Chain.md`，解释 MetaD 在 TrpB 项目中的完整逻辑链

### 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| MetaD 引擎 | GROMACS + PLUMED2（严格复刻） | 原文用 GROMACS 5.1.2 + PLUMED2 |
| 常规 MD 引擎 | AMBER 24p3 (pmemd.cuda) | 力场层面与 AMBER16 等价 |

### 遇到的问题

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| `maria-solano2019.pdf` 是正文不是 SI | ACS 期刊正文和 SI 是分开的 PDF | 用户手动从 ACS 网站下载了 SI |
| ACS Catal 2021 的计算方法也在 SI 里 | 两篇论文的 main text 都不写具体参数 | 最终从 JACS 2019 SI 提取了全部参数 |

### 发现的重要事实

- 原文的 **conventional MD 用 AMBER16**，但 **MetaDynamics 用 GROMACS 5.1.2 + PLUMED2**（两个不同的引擎）
- 温度是 **350 K**（不是 300 K），因为 *P. furiosus* 是嗜热古菌
- PLP 参数化方法确认为 **GAFF + RESP at HF/6-31G(d)**，但 SI 没有提供实际的 mol2/frcmod 文件

---

## 2026-03-26

### 完成的事

- **Longleaf PLUMED 安装**：在 /work 下用 conda-forge 安装了 PLUMED 2.9
  - 环境名：trpb-md
  - `conda activate trpb-md` → `plumed info --version` → 2.9 ✓
- **Disk quota 问题解决**：Home 目录满了（76GB/50GB），把 conda pkgs_dirs 和 envs_dirs 移到 /work
- **PLUMED runtime 验证**：`plumed driver` 可以运行
- **项目文件夹重组**：创建了 project-guide/、papers/reading-notes/、replication/ 等目录

### 遇到的问题

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| `conda create` Disk quota exceeded | Home 目录 50GB 已满 | 把 conda 存储移到 /work（10TB）|
| `plumed --version` 报错 | 正确命令是 `plumed info --version` | 查了 PLUMED 文档 |
| `module avail plumed` 没有结果 | Longleaf 没有预装 PLUMED 模块 | 用 conda-forge 安装 |

---

## 2026-03-25（及之前）

### 完成的事

- 论文阅读笔记框架创建（JACS 2019 + ACS Catal 2021）
- PDB 结构下载（5DVZ, 5DW0, 5DW3）并验证
- Campaign manifest 初版
- 项目 overview 文档
- PROTOCOL.md 创建
- Weekly report skill 创建
