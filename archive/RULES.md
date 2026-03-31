# 工作规则（适用于所有 AI Agent）

> **⚠️ 这是详细参考文件。核心强制规则已搬到 `CLAUDE.md` 的"强制规则"部分。**
> 本文件包含工作风格、工具分工、错误处理的完整说明。`CLAUDE.md` 里放的是精简版。

---

## 我是谁

Zhenpeng Liu，UNC Chapel Hill 本科生。正在准备 Caltech aNima Lab 暑期研究职位，用这个 TrpB MetaDynamics 复刻项目展示计算生物学能力。

之前在 KU Miao Lab 做过 HSP90 LiGaMD3 蛋白-配体解离模拟，熟悉 AMBER/pmemd.cuda、CHARMM-GUI、Slurm、增强采样基本概念。

---

## 工作风格

1. **中英文混用**：中文写说明和解释，英文写技术术语和命令。不要全英文。
2. **不要 overwhelming**：每次给一个清晰的 entry point，不要一次倒出 20 个文件让我看。
3. **每一步都要有"为什么"**：用 `> blockquote` 格式解释每个操作的理由，参考 HSP90 workflow 的风格。
4. **参数变化必须标注**：如果换了体系（比如从 PfTrpS 到 PfTrpB），哪些参数需要重新算、哪些不变，用表格说清楚。
5. **代码块直接给命令**：不要描述"你需要运行一个命令来做 X"，直接给 `bash` 代码块。
6. **文件要 portable**：不锁定在某个 AI vendor。YAML frontmatter 可以有，但核心内容必须是 plain markdown。
7. **不要给我虚假的进度**：如果某个步骤还没做，就标 NOT STARTED，不要提前写"已完成"。

---

## 文件结构约定

```
TrpB_project/
├── CLAUDE.md            ← **唯一 entry point**（Cowork + Claude Code 都读这个）
├── NEXT_ACTIONS.md      ← 共享任务队列
├── RULES.md             ← 本文件。详细参考（核心规则在 CLAUDE.md）
├── PROTOCOL.md          ← 6-stage pipeline 详细参考
├── GLOSSARY.md          ← 名词解释（所有缩写 + 专有名词）
├── CHANGELOG.md         ← 每天的进展 / 遇到的问题 / 决策记录
├── project-guide/       ← 概念性文档（逻辑链、overview、stage 描述）
├── papers/              ← 论文 PDF + 阅读笔记 + 深度标注 HTML
├── replication/         ← 实际复刻工作
│   ├── parameters/      ← 从 SI 提取的参数
│   ├── manifests/       ← campaign manifest（冻结的科学决策）
│   ├── structures/      ← PDB 文件
│   ├── scripts/         ← Slurm 脚本、PLUMED 输入文件等
│   ├── validations/     ← **Skeptic 输出：failure-patterns.md + validation notes**
│   └── campaign-reports/← Journalist 输出
├── reports/             ← 周报
└── memory/              ← 深度记忆（glossary 全量、人物、项目上下文）
```

---

## 工具分工

| 场景 | 用什么 |
|------|--------|
| 查论文、搜 Zotero/PubMed、读 PDF、planning、写文档 | **Cowork**（桌面 app） |
| SSH 到 Longleaf、装软件、写脚本、提交 Slurm 作业 | **Claude Code Terminal** |
| 两边都要做的事 | 先在 Cowork 规划，再到 Terminal 执行 |

**状态同步方式**：两边都读写 `CLAUDE.md`。做完一个步骤就更新 Project Status 表。

---

## 严格复刻原则

**MetaDynamics 必须用 GROMACS + PLUMED2**，不用 AMBER 做 MetaD。原因：原文用的 GROMACS 5.1.2 + PLUMED2，严格复刻。

**常规 MD 可以用 AMBER 24p3**（pmemd.cuda），这和原文的 AMBER16 在力场层面等价（同样的 ff14SB）。

---

## 错误处理规则（Skeptic 强制触发）

> **任何时候发现事实错误、脚本 bug、参数不匹配，必须做以下三件事，缺一不可：**

1. **修源文件**：在出错的文件里直接修正
2. **追加 failure-patterns.md**：在 `replication/validations/failure-patterns.md` 追加一条新的 FP-XXX 条目，包含：首次发现时间、发现者、错误描述、正确事实、根因、防范措施
3. **写 validation note**：在 `replication/validations/` 创建 `YYYY-MM-DD_[context].md`，记录这次验证的 pass/fail 结果

**光改 CHANGELOG.md 不算完成。** CHANGELOG 记录"发生了什么"，failure-patterns 记录"怎么防止再发"，validation note 记录"验证结论是什么"。三个文件各有用途。

**生成新文档/脚本前**：先读 `replication/validations/failure-patterns.md`，检查自己是否在重复已知错误。

---

## 周报规则

- 去 AI 化：禁用 "delve", "landscape", "cutting-edge", "groundbreaking" 等词
- 完整 banned phrases 列表见 `.claude/skills/weekly-report/SKILL.md`
- 用朴素语言写：做了什么、遇到什么问题、下周计划做什么
