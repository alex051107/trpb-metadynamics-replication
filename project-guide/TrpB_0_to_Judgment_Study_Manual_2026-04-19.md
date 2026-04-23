# TrpB 项目 0→判断力 学习手册

> **文档定位**: 这不是普通 glossary，也不是论文综述。
> 这是给我自己（Zhenpeng）的“补课总纲”。
> 目标不是把名词背下来，而是尽快获得三种能力：
> 1. **听懂项目**: 知道组里每条线在干什么，方法之间如何衔接。
> 2. **听懂术语**: 知道每个方法能回答什么问题、不能回答什么问题。
> 3. **形成判断力**: 能独立判断一个 proposed direction 是真问题、伪创新、好 benchmark、坏 proxy，还是 scope 爆炸。
>
> **最低完成标准**:
> - 能用自己的话解释项目主线和支线
> - 能解释 RFD3 / ProteinMPNN / docking / MD / MMPBSA / MetaDynamics / STAR-MD 各自做什么
> - 能说出每种方法的强项、弱项、最常见误用
> - 能在和 Amin 开会时，不把“改模型”当唯一问题
>
> **材料来源规则**:
> - 项目事实优先看 [PROJECT_OVERVIEW.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/PROJECT_OVERVIEW.md)、[workflow-map.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/workflow-map.md)、[slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md)
> - MetaDynamics/TrpB benchmark 优先看 [JACS2019_ReadingNotes.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/papers/reading-notes/JACS2019_ReadingNotes.md) 和 [TrpB_MetaDynamics_Complete_Workflow.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/TrpB_MetaDynamics_Complete_Workflow.md)
> - STAR-MD 与 dynamics ML 优先看本地 paper 和 review
> - 外部补课资料尽量用官方文档、官方教程、原始论文

---

## 目录

1. [先给结论：你到底缺什么](#先给结论你到底缺什么)
2. [第 0 层：项目地图](#第-0-层项目地图)
3. [第 1 层：TrpB 生物化学核心](#第-1-层trpb-生物化学核心)
4. [第 2 层：模拟栈与力场栈](#第-2-层模拟栈与力场栈)
5. [第 3 层：增强采样与 MetaDynamics](#第-3-层增强采样与-metadynamics)
6. [第 4 层：生成式设计与当前 ML 主线](#第-4-层生成式设计与当前-ml-主线)
7. [第 5 层：protein dynamics / STAR-MD 支线](#第-5-层protein-dynamics--star-md-支线)
8. [方法审美：每种方法到底好在哪里，烂在哪里](#方法审美每种方法到底好在哪里烂在哪里)
9. [独立判断框架：以后怎么判断一个新方案值不值得做](#独立判断框架以后怎么判断一个新方案值不值得做)
10. [最快补课路径：7 天冲刺版](#最快补课路径7-天冲刺版)
11. [官方教程 / 视频 / 文档清单](#官方教程--视频--文档清单)
12. [开会最低门槛：见 Amin 前必须已经会的东西](#开会最低门槛见-amin-前必须已经会的东西)

---

## 先给结论：你到底缺什么

你现在最大的缺口，不是“缺几个好 idea”，而是缺下面四种东西：

1. **项目地图**
   你能看到局部任务，但还不总能稳定地看见主线、支线和 owner 边界。
2. **方法边界感**
   你知道很多方法名字，但不总能马上说出“它解决什么 / 不解决什么 / 容易怎么骗人”。
3. **跨层翻译能力**
   你现在卡在 chemistry 和 ML 之间：一边知道 MetaDynamics 很重要，一边不确定它怎么变成 ML 侧真正能用的东西。
4. **判断模板**
   你还没有一套稳定问题框架，去判断一个方案到底是好 benchmark、好 proxy、好故事，还是 scope trap。

所以这份手册不是“多学点背景知识”，而是帮你建立一套**稳定判断模板**。

---

## 第 0 层：项目地图

### 0.1 这个项目真正的主线是什么

用一句话说：

> **主线是 TrpB 生成式设计闭环，不是 protein dynamics 本身。**

这一点在本地项目总览里写得很清楚：项目是在生成式 pipeline 下，用 MetaDynamics 作为物理层来解释和筛选 TrpB 候选序列。[PROJECT_OVERVIEW.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/PROJECT_OVERVIEW.md:8)

更展开地说：

1. 先有一个目标：设计能做出目标反应/立体选择性的 TrpB 变体。
2. 然后需要一个设计入口：`theozyme` 或活性位点几何模板。
3. 再通过结构生成和序列设计工具产生候选。
4. 用 docking / MD / MMPBSA / 几何检查去筛。
5. 再把有信息量的信号往 reward / fine-tuning / 下一轮设计回流。

### 0.2 protein dynamics 线是什么

它不是主线起点，而是后面为了 SURF 和 dynamics benchmark 长出来的支线。

只看 Slack，Amin 后来明确说过自己在做两件事，其中一件是：

> `Set up the protein dynamic benchmark for the SURF student`

也就是：protein dynamics 线是后来被单独拉出来的一条研究/benchmark 支线，不是一开始就定义好的唯一主任务。

### 0.3 你在图里哪里

最稳的说法是：

> 你被明确放进去的位置，是 `proposal + metadynamics + method benchmark support`。

这和“直接 owner Amin 的模型”不是一回事。

你现在真正最自然的位置，其实是：

> **chemistry-to-ML bridge / benchmark-facing role**

也就是：把 MetaDynamics 这条线从“只是跑模拟”变成“ML 侧可消费的 benchmark / evaluation truth”。

### 0.4 你现在的 confusion 为什么合理

因为你同时踩中了三个结构性问题：

1. 你主要跟 Yu 沟通，所以看到的是 chemistry / MetaDynamics 视角。
2. Amin 那边的 protein-dynamics 线本身也在变化，尤其是 STAR-MD 出来之后。
3. 组里没有一句始终稳定、明确的 “Zhenpeng owns X”。

所以你现在不是单纯没努力，而是**owner 定义本来就不够硬**。

---

## 第 1 层：TrpB 生物化学核心

这一层的目标不是让你变成 enzymology 专家，而是让你知道：

> **为什么这个项目不能只看静态结构，而必须关心构象动力学。**

### 1.1 TrpB 到底是什么

TrpB 是 tryptophan synthase 的 β 亚基，参与 PLP 依赖的反应过程。你项目里的关键点不是“TrpB 是一个酶”这么简单，而是：

- 它有多个反应中间体
- 不同中间体偏好不同构象
- COMM domain 的 open/partially closed/closed 切换和功能直接相关

这就是为什么只拿一个 AlphaFold 结构看一眼，根本不够。

### 1.2 你最低要会的几个生物化学对象

- `PLP`
  - 最简单理解：一个辅酶，反应是围着它转的
  - 重要性：没有它，TrpB 的化学本体就没法表达
- `Ain / Aex1 / A-A / Q2`
  - 最简单理解：反应过程中几个不同的化学状态
  - 重要性：不同状态可能对应不同构象偏好
- `COMM domain`
  - 最简单理解：TrpB 里和开合运动强相关的一段结构域
  - 重要性：它是 JACS 2019 Path CV 的核心对象，也是你 MetaDynamics 主要在盯的东西

### 1.3 为什么“静态结构像”不够

因为这个项目里最关键的问题之一恰恰是：

> 两个序列/结构可能静态上看起来差不多，但构象地形完全不同。

这也是 [PROJECT_OVERVIEW.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/PROJECT_OVERVIEW.md:12) 强调的点：GenSLM-230 和 NdTrpB 静态 backbone 很像，但功能不同，说明光看结构不够。

### 1.4 这一层你需要学到什么程度

最低要求：

- 知道 TrpB 不是“一个结构”，而是“多个中间体 + 多个功能相关构象”
- 知道 COMM domain transition 是你项目里最重要的动力学对象之一
- 知道 productive closure / non-productive closure 的差别有功能意义

你暂时**不需要**：

- 把整个 PLP 反应机理每一步量子化学细节都背熟
- 一开始就理解所有催化电子效应

---

## 第 2 层：模拟栈与力场栈

这一层的目标是：

> 知道“模拟”不是一个按钮，而是一整套假设链。

### 2.1 Conventional MD 是什么

最简单的人话：

> 给系统一个力场，然后按时间一步一步积分，看原子怎么动。

它的优点：

- 物理含义清楚
- 是很多更高级方法的基础
- 用来做稳定性检查、局部几何 sanity check 很好

它的缺点：

- 对慢过程、稀有事件很不友好
- 你关心的 O→PC→C 这种跨 barrier 事件，普通 MD 可能很久都不出来

**结论**：MD 很重要，但不是万能。

### 2.2 力场是什么

最简单的人话：

> 力场就是“你允许系统按什么规则相互作用”的近似物理模型。

在这个项目里你至少会遇到：

- `ff14SB`：蛋白主力场
- `GAFF`：小分子/辅酶参数
- `RESP`：电荷拟合
- `TIP3P`：水模型

**独立判断点**：
如果你看到有人只说“我们做了 MD”，你要立刻追问：

1. 用的什么 force field？
2. 辅酶/小分子参数怎么来的？
3. 电荷是 RESP、AM1-BCC，还是别的？
4. 这些选择会不会影响你真正关心的结论？

### 2.3 OpenMM / GROMACS / PLUMED 各是什么

#### GROMACS
- 最简单理解：高性能 MD 引擎
- 好处：成熟、快、MetaDynamics + PLUMED 社区经验丰富
- 坏处：有些工作流集成不如 OpenMM 灵活

#### OpenMM
- 最简单理解：更可编程的 MD engine，Python 生态很好
- 官方文档把它定义为一个既能跑常规模拟，也支持 enhanced sampling/add-on packages 的模拟工具包。[OpenMM User Guide](https://docs.openmm.org/development/userguide/)
- 好处：可编程、容易接 Python/ML pipeline
- 坏处：如果你想严格照搬一篇 GROMACS+PLUMED 文献，细节兼容性要更谨慎

#### PLUMED
- 最简单理解：给 MD 引擎加 collective variables 和 enhanced sampling 的外挂
- 官方主页明确说它可以和 GROMACS、AMBER、OpenMM 等常见 MD engines 配合使用。[PLUMED 官网](https://www.plumed.org/)
- 好处：增强采样和 CV 生态非常成熟
- 坏处：配置一错，经常“看起来跑了，实际上科学上没跑对”

#### openmm-plumed
- 最简单理解：让 OpenMM 能直接挂 PLUMED 脚本的插件
- 官方 GitHub 说明也很直接：创建 `PlumedForce`，把 PLUMED 控制脚本加进 `System` 即可。[openmm-plumed GitHub](https://github.com/openmm/openmm-plumed)
- 好处：更容易往现有 Python/ML pipeline 接
- 坏处：兼容和安装问题、restart 语义、环境问题更容易踩坑

### 2.4 这一层你需要学到什么程度

最低要求：

- 知道 MD engine、force field、enhanced sampling plugin 是三层不同东西
- 知道 OpenMM 和 GROMACS 不是“一个比一个高级”，而是工程取向不同
- 知道辅酶参数和电荷选择是会影响结果的，不是琐事

---

## 第 3 层：增强采样与 MetaDynamics

这一层是你当前最重要的一层。

### 3.1 MetaDynamics 到底是什么

最简单的人话：

> 当普通 MD 老是在一个坑里打转时，MetaDynamics 就不断往已经去过的地方填小土包，逼系统去探索别的地方。

OpenMM 官方 Metadynamics API 也给出了同样的核心逻辑：周期性地在当前 CV 位置加 Gaussian “bumps”，把系统推离已经探索过的区域，最后 bias 可用来重构自由能。[OpenMM Metadynamics API](https://docs.openmm.org/7.6.0/api-python/generated/openmm.app.metadynamics.Metadynamics.html)

PLUMED 官方 Masterclass 21.4 也把目标写得很清楚：训练用户写 metadynamics input、重构 free energy、做 unbiasing、判断 CV 好坏。[PLUMED Masterclass 21.4](https://www.plumed-tutorials.org/lessons/21/004/data/INSTRUCTIONS.html)

### 3.2 为什么 MetaDynamics 比普通 MD 更适合你这个问题

因为你关心的是：

- rare events
- slow conformational transitions
- basin structure
- free-energy landscape

这些事情普通 MD 可能很久都不给你。

MetaDynamics 的价值在于它不是只给“轨迹”，而是给你：

- 哪些状态是 basin
- basin 之间隔着多高的 barrier
- 系统更偏爱哪里

### 3.3 FES / FEL 为什么比单条 trajectory 更像真值

因为单条 trajectory 只告诉你：

> “它走过哪里”

而 FES/FEL 更像告诉你：

> “整个地形长什么样，哪些地方是低谷，哪些地方难过去”

这就是为什么对 ML 侧来说，FES/FEL 往往比一条“好看的轨迹”更有价值。

### 3.4 你最低要掌握的 MetaDynamics 子概念

#### CV（collective variable）
- 最简单理解：你拿来描述慢过程的低维坐标
- 在 TrpB 里：核心是 path CV 的 `s(R)` 和 `z(R)`

#### path CV
- `s(R)`：沿参考路径走到哪里
- `z(R)`：离这条路径偏多远

#### well-tempered metadynamics
- 最简单理解：不是永远加一样高的 Gaussian，而是随着模拟推进逐渐降温式地加 bias
- 好处：更容易收敛

#### multiple walkers
- 最简单理解：多条轨迹一起探索并共享 bias
- 好处：更快铺地形
- 坏处：如果 seed 或 bias 管理有问题，也会一起把错误放大

### 3.5 MetaDynamics 最常见的误用

这是你必须有“审美”的地方。

#### 误用 1：CV 选错
后果：模拟看起来很忙，但你 bias 的不是你真正关心的慢过程。

#### 误用 2：参数看起来来自文献，其实没确认
后果：复现过程失真，结论不可信。

#### 误用 3：只看轨迹有没有跑开，不看 FES 是否合理
后果：把“有动作”误当“有科学意义”。

#### 误用 4：把 MetaD 结果直接当 kinetics truth
后果：过度解释。

### 3.6 这一层你需要学到什么程度

最低要求：

- 能解释 MetaDynamics 和普通 MD 的差别
- 能解释 CV/path CV/FES/FEL 是什么
- 能说出 MetaDynamics 对项目的价值不仅是“跑出图”，而是提供 benchmark / evaluation truth

---

## 第 4 层：生成式设计与当前 ML 主线

这一层的目标是：

> 知道组里现在 ML 主线上的方法分别在干什么，它们不是一坨“AI 模型”。

### 4.1 RFD3 / RFdiffusion 做什么

最简单理解：

> 先生成能容纳某个 motif / active-site 约束的 backbone 或结构草图。

官方 RFdiffusion 仓库本身就是这么定位的：它是用来做 protein backbone generation / motif scaffolding 的，提供 Colab 和 Docker，强调 inference 时的 contig map、motif scaffolding、对称设计等。[RFdiffusion GitHub](https://github.com/RosettaCommons/RFdiffusion)

#### 好处
- 结构生成能力强
- 对 motif scaffolding 很有用
- 在 de novo design 里非常强势

#### 坏处
- 生成“看起来合理的 backbone”不等于生成“会催化的 enzyme”
- 对真正的 chemistry / electrostatics / long-timescale dynamics 没直接保证

#### 最容易误用
- 把“结构生成成功”误当“功能设计成功”

### 4.2 ProteinMPNN 做什么

最简单理解：

> 给定 backbone，设计 sequence。

官方仓库描述也很明确：它是 sequence design/inverse folding 工具，给定 backbone，可以用 full backbone 或 CA-only 模型来生成序列。[ProteinMPNN GitHub](https://github.com/dauparas/ProteinMPNN)

#### 好处
- 对 backbone → sequence 这一跳很强
- 工具成熟，使用门槛相对可控

#### 坏处
- 前提是 backbone 本身得靠谱
- 它擅长的是 compatibility，不等于天然会优化功能

#### 最容易误用
- 把 sequence compatibility 误当 catalytic correctness

### 4.3 RF3 / RoseTTAFold 做什么

最简单理解：

> 更像结构预测/验证或 refold 检查工具，而不是你项目里真正的 physics layer。

官方 RoseTTAFold 仓库定义自己是 structure prediction / interaction modeling 的实现。[RoseTTAFold GitHub](https://github.com/RosettaCommons/RoseTTAFold)

#### 好处
- 适合做结构 plausibility 检查
- 可以做快速结构 sanity

#### 坏处
- 不是功能动力学真值
- 更不是 rare-state sampling

### 4.4 docking / binding energy / MMPBSA 各自是什么

#### docking
- 最简单理解：先把配体塞到 pocket 里，看 pose 和打分
- 好处：快、便宜、适合粗筛
- 坏处：容易假阳性，和真正 catalysis 差得远

#### binding energy / MMPBSA
- 最简单理解：比 docking 更物理一点的 end-point 近似
- 好处：比单纯 docking 更强一些
- 坏处：还是 proxy，不是反应能垒，也不是完整功能指标

### 4.5 reward / GRPO / SFT / MFBO 这一组

这组是最容易把你绕晕的，因为名字都像“优化”。

#### reward
- 本质：模型到底被鼓励什么
- 核心判断：reward 错了，后面优化越努力越糟

#### GRPO / RL-style optimization
- 本质：给定 reward，往 reward 高的方向更新
- 好处：能直接把某些目标写进优化
- 坏处：如果 reward 是伪信号，会系统性放大伪信号

#### SFT
- 本质：拿现成样本做监督式微调
- 好处：稳定
- 坏处：数据质量和覆盖面极关键

#### MFBO
- 本质：多保真度优化/筛选思想
- 最重要的直觉：先便宜筛，再贵验证

### 4.6 这一层你要形成的判断

看到任何一个 ML 方法时，你都应该立刻问：

1. 它是在管 backbone、sequence、structure plausibility，还是 dynamics？
2. 它对 catalysis / rare state / allostery 有直接约束吗？
3. 它是不是只是某一层 proxy？
4. 它输出的结果需要什么物理层来兜底？

---

## 第 5 层：protein dynamics / STAR-MD 支线

### 5.1 STAR-MD 到底干了什么

最简单的人话：

> 它把“generic long-horizon coarse-grained protein dynamics generation”这层故事做得很强。

它的核心卖点包括：

- joint spatio-temporal attention
- 用 Mori-Zwanzig 给 coarse-grained + temporal history 讲理论故事
- 在 ATLAS benchmark 上做 100 ns / 240 ns / 1 μs 级别的 rollout

### 5.2 它为什么会让你们原来的 story 变弱

因为如果原来的 pitch 是：

> “我们也来做一个 generic long-horizon protein dynamics model”

那 STAR-MD 已经把这层 narrative 占掉很多了。

所以 Amin 才会出现那种反应：不是这个方向完全没戏了，而是“最宽的那层故事不够新了”。

### 5.3 它没做完什么

你最该记住的是这句：

> 它压掉的是 generic story，不是 TrpB-specific story。

尤其它没有真正替你们做完这些东西：

- TrpB mutant-specific dynamics
- ligand / cofactor-aware dynamics
- metadynamics-grounded evaluation
- O/PC/C / productive closure 这种 task-specific state truth
- chemistry-to-ML translation layer

### 5.4 这一层你需要会到什么程度

最低要求：

- 能解释 STAR-MD 为何强
- 能解释它为什么让 Amin 改变判断
- 能解释它没有把你们所有问题都做完
- 能用它来区分“generic dynamics”与“TrpB-specific dynamics benchmark”

---

## 方法审美：每种方法到底好在哪里，烂在哪里

下面这张表是你形成判断力最重要的部分。

| 方法 | 它最擅长什么 | 它最不擅长什么 | 最常见误用 | 你该怎么评价它 |
|---|---|---|---|---|
| RFD3 / RFdiffusion | backbone / motif scaffolding | 不能直接保证 catalysis | 把结构生成当功能设计 | 先问 motif/scaffold 成功，再问 chemistry 怎么兜底 |
| ProteinMPNN | backbone → sequence | 不直接管功能动态 | 把 sequence compatibility 当功能真值 | 看它是工具层，不是 physics truth |
| RF3 / RoseTTAFold | 结构 plausibility / refold | 不提供功能地形 | 把结构预测稳定当功能稳定 | 当 sanity check，不当终点 |
| Docking | 快速粗筛 | 假阳性高、忽视动力学 | 把 docking score 当功能好坏 | 只能当 cheap proxy |
| MMPBSA / MMGBSA | 比 docking 更物理的 end-point ranking | 仍然不是反应能垒 | 过度解释 binding 为 catalysis | 适合 ranking，不适合单独下最终结论 |
| Conventional MD | 稳定性和局部动力学检查 | rare events 差 | 跑了一条轨迹就讲自由能故事 | 适合 sanity / stability，不适合跨 barrier 真值 |
| MetaDynamics | rare events、FES、basin structure | 强依赖 CV/参数 | 以为“跑开了”就算成功 | 核心看 CV、FES、state interpretability |
| EVB/QM-like chemistry layer | 更接近 catalytic truth | 重、慢、难参数化 | 范围太早放太大 | 留给高保真阶段，不是起手式 |
| STAR-MD / generic dynamics model | generic long-horizon dynamics generation | 不自动解决 ligand-aware / mutant-specific / metad-grounded任务 | 看到长轨迹就以为学会功能态 | 问它 benchmark 问的是什么，不是只看模型炫不炫 |

---

## 独立判断框架：以后怎么判断一个新方案值不值得做

以后无论是 Amin 提一个方向，还是你自己想到一个方向，都先过下面 8 个问题。

### 1. 它到底回答的是哪个层级的问题？

- 结构生成？
- sequence design？
- docking proxy？
- dynamics truth？
- rare-state evaluation？
- reward design？

如果一个方案连层级都说不清，先不要激动。

### 2. 它的真值是什么？

任何方案都要问：

> 你最后拿什么当 ground truth？

如果是 TrpB 项目，最常见的真值层包括：

- 实验功能
- MD/MetaD 物理结果
- state labels / FES
- chemistry-informed descriptors

### 3. 它最强的 baseline 是谁？

如果一个方案提出来时没有清楚 baseline，通常说明它还不成熟。

### 4. 它是不是只是“换一层说法”

这是判断伪创新最重要的问题。

例如：
- 把“generic long-horizon protein dynamics”换成“memory-aware dynamics”不一定就真新
- 把“多起点评估”说成“rare-state intelligence”也不一定就新

### 5. 它需要的数据和算力现实吗

你现在必须有这个下意识：

> 一个 idea 如果需要你拿不到的数据、拿不到的 model code、或者超出你能承担的 compute，它再漂亮也可能不现实。

### 6. 它适合本科生吗

不是说本科生不能做难题，而是：

> 你应该优先做“高信息密度、强接口价值、低 scope 爆炸概率”的事。

### 7. 它的 failure mode 是什么

你以后必须强迫自己反着想：

- 它怎么会失败？
- 它会不会只剩形式感？
- 它会不会最后没人真正用？

### 8. 它和当前 owner 结构相容吗

再好的 idea，如果它天然跨了 Amin / Yu 两边而没人认领，也会出事。

---

## 最快补课路径：7 天冲刺版

### Day 1：先补项目地图

读：
- [PROJECT_OVERVIEW.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/PROJECT_OVERVIEW.md)
- [workflow-map.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/workflow-map.md)
- [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md)

目标：
- 自己画出主线/支线
- 写出每个人的 role

### Day 2：补 TrpB + MetaDynamics 核心

读：
- [JACS2019_ReadingNotes.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/papers/reading-notes/JACS2019_ReadingNotes.md)
- [TrpB_MetaDynamics_Complete_Workflow.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/TrpB_MetaDynamics_Complete_Workflow.md)
- [GLOSSARY.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/GLOSSARY.md)

目标：
- 讲清楚 path CV、FES、O/PC/C、productive closure

### Day 3：补官方 MetaD / OpenMM

看：
- [PLUMED Masterclass 21.4: Metadynamics](https://www.plumed-tutorials.org/lessons/21/004/data/INSTRUCTIONS.html)
- [PLUMED Masterclass 总入口（含视频）](https://www.plumed.org/masterclass)
- [OpenMM User Guide](https://docs.openmm.org/development/userguide/)
- [OpenMM Metadynamics API](https://docs.openmm.org/7.6.0/api-python/generated/openmm.app.metadynamics.Metadynamics.html)
- [openmm-plumed 官方仓库](https://github.com/openmm/openmm-plumed)

目标：
- 把 MetaDynamics 的软件层理解补稳

### Day 4：补当前 ML 主线

看：
- [RFdiffusion GitHub](https://github.com/RosettaCommons/RFdiffusion)
- [ProteinMPNN GitHub](https://github.com/dauparas/ProteinMPNN)
- [RoseTTAFold GitHub](https://github.com/RosettaCommons/RoseTTAFold)
- 本地相关 reading notes

目标：
- 分清 backbone generation / sequence design / structure verification

### Day 5：补 STAR-MD

看：
- 本地 STAR-MD paper
- 本地 STAR-MD review notes

目标：
- 自己写出“STAR-MD 压掉了哪层 story，没压掉哪层 story”

### Day 6：做方法优劣表

任务：
- 自己重新写一版“每种方法擅长什么 / 不擅长什么 / 最常见误用”

### Day 7：准备 meeting 版本

任务：
- 写出 30 秒项目解释
- 写出 30 秒你角色的解释
- 写出 7 个要问 Amin 的问题

---

## 官方教程 / 视频 / 文档清单

### 最优先

1. PLUMED Metadynamics Masterclass
   - 官方：PLUMED 教程体系
   - 用途：把 MetaDynamics 从“知道名字”变成“知道怎么判断好坏”
   - 链接：[Metadynamics Masterclass](https://www.plumed-tutorials.org/lessons/21/004/data/INSTRUCTIONS.html)

2. PLUMED Masterclass 总入口（含公开视频）
   - 链接：[PLUMED Masterclass](https://www.plumed.org/masterclass)
   - 说明：这里最适合当视频补课入口；比零散 YouTube 搜索靠谱得多

3. OpenMM User Guide
   - 链接：[OpenMM User Guide](https://docs.openmm.org/development/userguide/)

4. OpenMM Metadynamics API
   - 链接：[OpenMM Metadynamics](https://docs.openmm.org/7.6.0/api-python/generated/openmm.app.metadynamics.Metadynamics.html)

5. openmm-plumed 官方仓库
   - 链接：[openmm-plumed GitHub](https://github.com/openmm/openmm-plumed)

### 设计模型最优先

6. RFdiffusion 官方仓库
   - 链接：[RFdiffusion GitHub](https://github.com/RosettaCommons/RFdiffusion)

7. ProteinMPNN 官方仓库
   - 链接：[ProteinMPNN GitHub](https://github.com/dauparas/ProteinMPNN)

8. RoseTTAFold 官方仓库
   - 链接：[RoseTTAFold GitHub](https://github.com/RosettaCommons/RoseTTAFold)

### 用来理解 RFdiffusion 为什么强

9. RFdiffusion 原始论文页面
   - 链接：[Nature paper](https://www.nature.com/articles/s41586-023-06415-8)

### 用来理解“为什么不是所有事情都该交给 generic dynamics model”

10. STAR-MD 本地论文 + 本地 review
   - 用途：理解 generic long-horizon dynamics 的上限和边界

---

## 开会最低门槛：见 Amin 前必须已经会的东西

在和 Amin 开会前，你至少要能稳定说出下面 6 句话。

### 1. 项目主线是什么

> 主线是 TrpB 生成式设计闭环，protein dynamics 是后面为 SURF 拉出来的一条支线。

### 2. 你现在手上的线是什么

> 我现在最直接在做的是 metadynamics / method benchmark 这条线，它的价值在于把 chemistry truth 变成 ML 侧可用的 benchmark/evaluation asset。

### 3. MetaDynamics 为什么重要

> 因为普通 MD 很难给出 rare-state 和自由能地形，而 TrpB 的关键差异恰恰可能在构象地形而不是单一静态结构上。

### 4. STAR-MD 为什么重要

> 它把 generic long-horizon coarse-grained protein dynamics 这层故事做得很强，所以 generic narrative 变弱了。

### 5. STAR-MD 没做完什么

> 它没有把 TrpB-specific、ligand-aware、mutant-specific、metadynamics-grounded 这一层任务做完。

### 6. 你现在最该确认的不是“我要不要改模型”

> 而是 before summer 你到底 owner 哪一个明确 deliverable：benchmark pack、evaluation layer，还是一个被明确 scope 的 model-side task。

---

## 最后一条提醒

你现在最该建立的不是“我会不会某个模型”，而是这种反射：

> 每听到一个方法，我都能立刻问：
> 1. 它解决什么问题？
> 2. 它不解决什么问题？
> 3. 它在哪一层？
> 4. 它的真值是什么？
> 5. 它最容易怎么骗人？
> 6. 它和 TrpB 这个项目的真正接口在哪里？

只要你把这个反射练出来，你就开始有独立审美了。

