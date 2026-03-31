# 明天计划 (2026-03-29, Sunday)

> 基于 CLAUDE.md 和 CHANGELOG.md 的现状整理。

---

## 当前进度一句话总结

**基础设施全部就绪（HPC、AMBER、PLUMED、GROMACS），参数已提取，阅读材料已准备。但你还没读 paper，也还没跑过任何模拟。**

---

## 明天要做的事（按优先级）

### 1. 读 JACS 2019 正文（最高优先级，~1.5h）

打开 `papers/annotations/JACS2019_DeepAnnotation_v2.html`，配合 `papers/reading-notes/JACS2019_ReadingNotes.md` 一起看。

**读的时候重点关注：**
- Figure 2: FEL 的样子（O/PC/C 三个态在 s-z 平面上的分布）
- Figure 3: PfTrpB vs PfTrpB0B2 的 FEL 对比（这就是你要复现的核心结果）
- 为什么 PfTrpB 的 Closed 态是"非生产性"的（RMSD > 1.5 Å）
- K82-Q₂ 距离 3.6 Å 这个阈值是怎么来的

> 这篇读完后，你应该能回答："productive closure 和 unproductive closure 有什么区别？"

### 2. 读 GenSLM TrpB Nature Comms（第二优先级，~1h）

打开 `papers/annotations/NatCommun2026_DeepAnnotation.html`。

**重点关注：**
- GenSLM 怎么生成 TrpB 序列的
- 实验验证了什么（表达、折叠、催化活性、底物范围）
- D-serine 活性（这是跟你项目最相关的意外发现）

> 这篇读完后，你应该能回答："GenSLM 生成的序列为什么需要 MetaDynamics 来筛选？"

### 3. Alanine dipeptide toy test（如果还有时间，~30min）

这个需要在 **Claude Code Terminal** 里做。目的：验证 GROMACS + PLUMED2 的 conda 环境能正常跑 MetaDynamics。

```bash
ssh longleaf
conda activate trpb-md
cd /work/users/l/i/liualex/AnimaLab/runs/
mkdir toy-alanine && cd toy-alanine
```

让 Claude Code 帮你生成 alanine dipeptide 的 GROMACS 输入文件 + PLUMED MetaD input，提交一个短 job（~10 min），确认能出 HILLS 文件和 FES。

> 这步做完后，你的工具链就全部验证过了。

---

## 接下来一周的 Roadmap（供参考，不用明天全做）

| Step | Task | 在哪里做 | 依赖 |
|------|------|---------|------|
| A | PLP 参数化（antechamber + RESP） | Claude Code Terminal | 读完 JACS 2019 SI 的 PLP 部分 |
| B | 构建 15-frame O→C 参考路径 | Claude Code Terminal | 1WDW + 3CEP PDB |
| C | 准备 PfTrpS(Ain) 体系（solvate, minimize, heat） | Claude Code Terminal | PLP 参数 (Step A) |
| D | 500 ns conventional MD | Longleaf GPU job | Step C |
| E | Well-tempered MetaD (10 walkers) | Longleaf GPU job | Step B + Step D |

---

## 文件位置速查

| 要看什么 | 打开这个 |
|---------|---------|
| JACS 2019 逐段标注 | `papers/annotations/JACS2019_DeepAnnotation_v2.html` |
| JACS 2019 阅读笔记 | `papers/reading-notes/JACS2019_ReadingNotes.md` |
| GenSLM 逐段标注 | `papers/annotations/NatCommun2026_DeepAnnotation.html` |
| GenSLM 阅读笔记 | `papers/reading-notes/NatCommun2026_ReadingNotes.md` |
| MetaDynamics 参数总表 | `replication/parameters/JACS2019_MetaDynamics_Parameters.md` |
| 逻辑链（MetaD 在项目中的作用） | `project-guide/MetaDynamics_Logic_Chain.md` |
| 名词不认识 | `GLOSSARY.md` |

---

晚安 💤
