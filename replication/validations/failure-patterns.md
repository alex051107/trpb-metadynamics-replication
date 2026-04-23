# Failure Patterns（反复出现的验证失败）

> **用途**：记录项目中反复出现的错误模式，防止再犯。
> 每次 Skeptic 验证发现新错误时，追加到对应类别。
> AI Agent 在生成新文档/脚本时，**必须先读这个文件**，检查自己是否在重复已知错误。

---

## FP-001: 混淆 "biased CV" 和 "monitoring metric"

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (fact-check agent) |
| 受影响文件 | `papers/reading-notes/JACS2019_ReadingNotes.md` |
| 错误描述 | 阅读笔记把 K82-Q₂ distance 和 E104-Q₂ distance 列为 MetaDynamics 偏置的 CV |
| 正确事实 | MetaD 只偏置 **2 个 Path CV**: s(R) = progress along O→C path, z(R) = deviation from path。K82-Q₂ 和 E104-Q₂ 是**监测指标**，不参与偏置 |
| 根因 | AI 在生成阅读笔记时，没有区分 "we monitor X" 和 "we bias along X" |
| 防范措施 | 写 MetaD 相关文档时，明确区分：(1) biased CVs (PLUMED METAD 里的 ARG)，(2) monitored metrics (PRINT 里的 ARG) |
| 已修复 | ✅ JACS2019_ReadingNotes.md line 102-103 |

---

## FP-002: SHAKE/SETTLE 约束描述不精确

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (fact-check agent) + Cowork (SI fact-check) |
| 受影响文件 | `replication/parameters/JACS2019_MetaDynamics_Parameters.md` |
| 错误描述 | 参数表写 SHAKE "fix hydrogen bond angles" |
| 正确事实 | SHAKE/SETTLE 约束**水分子几何**（H-O-H angle + O-H bonds），不是泛指"氢键角" |
| 根因 | AI 用了不精确的 shorthand，没有查 AMBER manual 对 SHAKE 的定义 |
| 防范措施 | 涉及 MD 约束算法时，写全：SHAKE constrains bonds involving hydrogen; SETTLE constrains water geometry (3-site rigid model) |
| 已修复 | ✅ JACS2019_MetaDynamics_Parameters.md |

---

## FP-003: PDB 原子名不匹配力场定义

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (Longleaf 执行) |
| 受影响文件 | `replication/scripts/toy-alanine/setup_alanine.sh` |
| 错误描述 | Cowork 生成的 alanine dipeptide PDB 里 ACE 残基有 'N' 原子 |
| 正确事实 | AMBER ff14SB 的 ACE capping group 只有 CH3, C, O（没有 N）。pdb2gmx 报错 "Atom N in residue ACE not found in rtp entry" |
| 根因 | AI 凭记忆写 PDB 坐标，没有查 AMBER force field rtp 文件中 ACE 的原子列表 |
| 防范措施 | **永远不要凭记忆写 PDB 原子名**。要么：(1) 从已有 PDB 提取，(2) 查 `aminoacids.rtp` 确认，(3) 用 `gmx pdb2gmx` 先做 dry run 验证 |
| 已修复 | ✅ Claude Code Terminal 在 Longleaf 上重写了 PDB |

---

## FP-004: PLUMED 原子索引与实际拓扑不匹配

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (Longleaf 执行) |
| 受影响文件 | `replication/scripts/toy-alanine/plumed_metad.dat` |
| 错误描述 | Cowork 写的 PLUMED 文件用原子索引 4,5,6,7 定义 φ/ψ 二面角 |
| 正确事实 | pdb2gmx 重排原子后，正确索引是 5,7,9,15（从 .gro 文件确认） |
| 根因 | AI 基于原始 PDB 的原子顺序写索引，没有考虑 pdb2gmx 会重排原子（加氢、重命名）|
| 防范措施 | **PLUMED 原子索引必须从 pdb2gmx 输出的 .gro 文件确定**，不能从输入 PDB 推断。流程：先跑 pdb2gmx → 看 .gro → 再写 PLUMED |
| 已修复 | ✅ Claude Code Terminal 在 Longleaf 上修正了索引 |

---

## FP-005: 体系-中间体分配错误

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (fact-check agent) |
| 受影响文件 | `replication/parameters/JACS2019_MetaDynamics_Parameters.md` |
| 错误描述 | PfTrpA-PfTrpB0B2 复合体被标注为 "Q₂ + Ain"，实际该复合体只模拟了 "Q₂ only" |
| 正确事实 | SI Table S2 明确：PfTrpA-PfTrpB0B2 只做了 Q₂ 中间体；PfTrpB₂ 只做了 Ain 中间体 |
| 根因 | AI 在提取参数时混淆了不同体系的中间体分配 |
| 防范措施 | 参数表中每行必须对应唯一的 (system, intermediate) pair，不要合并 |
| 已修复 | ✅ JACS2019_MetaDynamics_Parameters.md |

---

## FP-006: Slurm OMP_NUM_THREADS 与 GROMACS -ntomp 冲突

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (Longleaf 执行) |
| 受影响 Jobs | 39960167 (OMP=1 vs ntomp=4), 39960248 (OMP=garbage) |
| 错误描述 | Longleaf Slurm 默认 `OMP_NUM_THREADS=1`。GROMACS `-ntomp 4` 要求 OMP=4，不一致时直接 fatal error |
| 根因 | Slurm 脚本没有显式设置 OMP_NUM_THREADS |
| 防范措施 | **所有 Slurm 脚本模板必须包含** `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK`（或硬编码核数），放在 conda activate 之后、gmx mdrun 之前 |
| 已修复 | ✅ Job 39960327 用硬编码 `export OMP_NUM_THREADS=4` 解决 |

---

## FP-007: Longleaf conda 激活路径硬编码错误

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Claude Code Terminal (Longleaf 执行) |
| 受影响文件 | `setup_alanine.sh`, `submit_metad.slurm` |
| 错误描述 | 脚本用 `/opt/conda/` 或 `~/anaconda3/` 作为 conda 路径 |
| 正确做法 | Longleaf 用 `module load anaconda/2024.02` |
| 根因 | Cowork 不知道 Longleaf 的 conda 加载方式 |
| 防范措施 | Longleaf 脚本统一用 `module load anaconda/2024.02 && conda activate trpb-md`。**Cowork 生成的 Slurm 脚本顶部应加注释：`# NOTE: conda path will be fixed by Claude Code Terminal for Longleaf`** |
| 已修复 | ✅ 手动替换 |

---

## FP-008: 报告温度标注与实际运行温度不符

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Cowork (Skeptic 独立复审) |
| 受影响文件 | `replication/validations/2026-03-28_toytst_alanine_final.md`, `replication/analysis/toy-alanine/fes_alanine.png` |
| 错误描述 | Final validation note 和 FES 图标题写 "350 K"，但 MDP `ref_t=300`，PLUMED `TEMP=300`。实际模拟温度是 **300 K** |
| 根因 | Claude Code Terminal 用了项目级别的温度设定（350 K, for TrpB）覆盖了 toy test 的实际参数 |
| 防范措施 | **报告中的参数必须从实际运行文件（MDP / PLUMED input）读取，不能从项目级别的 Key Decisions 表推断。验证时必须 `grep ref_t *.mdp` 和 `grep TEMP plumed*.dat` 确认** |
| 已修复 | ✅ Claude Code Terminal 修正了 validation note (300 K)、FES 图标题 (300 K)、generate_week2.py、generate_week3.py |

---

## FP-009: antechamber BCC (AM1-BCC) SCF 不收敛于 PLP 分子

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-30, Claude Code Terminal |
| 错误描述 | 对 LLP (PLP-K82 Schiff base, 42 atoms with H) 运行 `antechamber -c bcc` 时，SQM AM1 计算 SCF 不收敛（1000 steps 后 DeltaE = -10.5, DeltaP = 0.21）。charge=0 和 charge=-2 都不收敛 |
| 根因 | PLP 含磷酸基团（高电荷密度）+ 吡啶环 + Schiff base 共轭体系，AM1 半经验方法处理这类分子容易 SCF 发散 |
| 防范措施 | **PLP 类分子不要用 BCC 电荷。必须走 RESP 路径（Gaussian HF/6-31G(d) → antechamber -c resp）。** 这也正好是 SI 指定的方法 |
| 已修复 | ✅ 已生成 Gaussian RESP 输入文件 `LLP_ain_resp.gcrt`，待提交计算 |

## FP-010: antechamber 对无氢 PDB 的 atom typing 错误

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-30, Claude Code Terminal |
| 错误描述 | 对仅含重原子的 `LLP_chainA.pdb`（24 atoms, no H）运行 antechamber 时，吡啶环原子被错误分配为 `c1`（sp, triple bond）/ `c2`（sp2）而非 `ca`（aromatic）/ `nb`（aromatic N）。导致 parmchk2 生成的 frcmod 全是 empirical 估算参数 |
| 根因 | antechamber 需要氢原子来正确判断键级和芳香性。无氢 PDB 的 HETATM 记录不含 CONECT 信息，antechamber 只能猜测键级 |
| 防范措施 | **提取非标准残基后，必须先用 `reduce` 加氢再运行 antechamber。** 命令：`reduce input.pdb > input_H.pdb` |
| 已修复 | ✅ 已用 reduce 生成 `LLP_chainA_H.pdb`（42 atoms），供 Gaussian/RESP 使用 |

## FP-011: 跳过 pipeline stage 直接执行

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-30, Claude Code Terminal |
| 错误描述 | 在 Librarian 阶段未完成（resource_inventory.md 仍标记多项为 "Unknown"/"Critical"）的情况下，直接跳到 Runner 阶段在 Longleaf 上执行 antechamber，导致使用了错误的 charge 和未验证的参数 |
| 根因 | Agent 急于推进进度，忽略了 CLAUDE.md 中明确的 6-stage pipeline 顺序 |
| 防范措施 | **执行任何 Runner 操作前，先检查 PROTOCOL.md 中的 campaign status，确认当前 stage。Librarian → Janitor → Runner 不能跳过** |
| 已修复 | ✅ 回退并完成 Librarian 阶段（更新 resource_inventory.md），记录 FP-009/010 |

---

## FP-012: 自动生成的 Gaussian 输入有奇数电子（singlet 不可能）

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-31, Claude (review of Codex output) |
| 受影响文件 | `replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt` |
| 错误描述 | Codex 的 `build_llp_ain_capped_resp.py` 生成了 55 原子的 ACE-LLP-NME 片段，Z_total=227（奇数）。charge=-2 → 229 electrons（奇数）→ singlet (multiplicity=1) 不可能。Gaussian 报错："The combination of multiplicity 1 and 229 electrons is impossible" |
| 根因 | 脚本在芳香环 C5 上错误添加了 1 个氢。PLP 吡啶环的 C5 有三个取代基（C4, C6 在环内 + C5' 连磷酸臂），是全取代 sp2 碳，不应该有 H。这将 H 总数从正确的 25 变成了 26，Z 从偶变奇 |
| **原理** | **Pauli exclusion principle**：singlet state 要求所有电子配对 → 总电子数必须为偶数。电子数 = Z_total - charge。如果 Z 为奇且 charge 为偶（如 -2），电子数为奇，singlet 不可能 |
| 正确做法 | 54 原子（17C, 4N, 7O, 1P, 25H），Z=226（偶），charge=-2 → 228 electrons（偶）→ singlet ✓ |
| 防范措施 | **自动生成 Gaussian 输入后，必须验证电子数奇偶性**：`assert (Z_total - charge) % 2 == 0`。已在脚本中添加此 assertion |
| 已修复 | ✅ 移除 HC5，加电子数 assertion，重新生成并提交 Job 40533504 |

## FP-013: Gaussian `iop(6/50=1)` GESP 文件名格式错误

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-31, Claude (Longleaf 执行) |
| 受影响文件 | `LLP_ain_resp_capped.gcrt` (Longleaf) |
| 错误描述 | Gaussian 16 在 SCF 收敛后报 "Blank file name read" 并终止于 l602.exe。`iop(6/50=1)` 指示 Gaussian 输出 ESP 到 `.gesp` 文件，但文件名 section 格式不被 Gaussian 16c02 接受 |
| 根因 | `iop(6/50=1)` 的 GESP 文件名格式在 Gaussian 16 中可能需要特定的空行和换行模式，与 Gaussian 09 不同。或者 `opt` 关键字和 `iop(6/50=1)` 的组合在多步计算中需要 `--Link1--` 分隔 |
| 防范措施 | **不使用 `iop(6/50=1)`**。antechamber 可以直接从 Gaussian `.log` 文件读取 MK ESP 数据（使用 `-fi gout` flag），不需要独立的 `.gesp` 文件。简化 route section 为 `#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt` |
| 已修复 | ✅ 移除 `iop(6/50=1)` 和 GESP section，重新提交 Job 40533504 |

## FP-014: 生成脚本与实际运行文件不同步

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-31, Codex code review |
| 受影响文件 | `scripts/build_llp_ain_capped_resp.py` (line 314), `replication/scripts/parameterize_plp.sh` (lines 413/432/440) |
| 错误描述 | Python 生成脚本的 Gaussian route line 仍包含 `iop(6/50=1)`（FP-013 已修复的 bug），但实际运行的 `.gcrt` 文件已手动修正。如果重跑脚本，会覆盖正确文件为错误版本。同时 `parameterize_plp.sh` 的 3 处 route section 也有同样残留。Slurm 脚本缺 `OMP_NUM_THREADS`（违反 FP-006） |
| 根因 | 手动修复 live file 后没有同步更新生成脚本。修复分散在多个文件中，没有统一检查 |
| 防范措施 | **修复 live file 后，必须 grep 整个仓库检查同样的错误是否存在于其他文件**。命令：`grep -r 'iop(6/50=1)' --include='*.py' --include='*.sh' --include='*.gcrt'`。生成脚本和 live file 必须保持一致——最好只有一个 source of truth |
| 已修复 | ✅ Codex 修复了 `build_llp_ain_capped_resp.py`、`parameterize_plp.sh`、`submit_gaussian_capped.slurm` 及 4 个 stale 文档（2026-03-31） |

## FP-015: calculate_msd() 返回 RMSD 而非 MSD，导致 lambda 错 130x

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-31, Independent skeptic agent (Stage 4 validation) |
| 受影响文件 | `replication/scripts/generate_path_cv.py` (line 280), `replication/structures/path_frames/summary.txt` |
| 错误描述 | `calculate_msd()` 函数在计算 `np.mean(np.sum(diff**2, axis=1))` 后多做了一步 `np.sqrt()`，返回的是 RMSD (0.606 A) 而非 MSD (0.367 A^2)。`calculate_lambda()` 用这个 RMSD 做 `2.3 / 0.606 = 3.798`，而正确的 lambda 应为 ~0.029 (JACS 2019) |
| 正确事实 | PLUMED PATHMSD 的 lambda 定义要求 `lambda * <d> ~ 2.3`，其中 `<d>` 是相邻帧之间的 MSD（不是 RMSD）。JACS 2019 报告 MSD ~80 A^2、lambda ~0.029。即使修正 sqrt bug，per-atom MSD = 0.367 A^2 仍与 80 有显著差距，需要核实 PLUMED 用的是 per-atom mean 还是 total sum convention |
| 根因 | 函数命名为 `calculate_msd` 但实际返回 `sqrt(msd)` = RMSD。下游使用者不知道返回值的语义已变 |
| 防范措施 | **数值函数的返回值必须与函数名语义一致**。如果函数名叫 `calculate_msd`，返回值必须是 MSD（平方量，单位 A^2），不能悄悄加 sqrt 变成 RMSD（线性量，单位 A）。**生成 PLUMED lambda 参数前，必须查 PLUMED 官方文档确认 MSD 的定义（per-atom mean vs total sum）** |
| 已修复 | 未修复 — 需要在 Runner stage 回退修正脚本并重新生成 summary.txt |

## FP-016: Lambert 2026 候选序列数写成 100,000，而不是 60,000

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-01, Independent Skeptic Agent + cross-review synthesis |
| 受影响文件 | `project-guide/FULL_LOGIC_CHAIN.md` |
| 错误描述 | 文档把 Lambert et al. 2026 生成的 TrpB 候选数写成 `100,000`（至少 5 处），而论文实际数字是 **`60,000` generated sequences**，其中 `105` 条进入实验验证。这个错误把 dataset scale 高估了约 67%。 |
| 根因 | 复述上游论文时复用了未经核对的 shorthand，没有把 headline 数字与 primary source 和仓库其他文档（如 `MASTER_TECHNICAL_GUIDE.md`）做一致性检查。 |
| 防范措施 | **所有来自主论文的 headline 数字（样本数、筛选数、命中数、参数规模）都必须逐项对 primary source 核对，并在跨文档复用前做一致性检查。** 如果仓库不同文件出现冲突数字，必须先 resolve，再继续写新文档。 |
| 已修复 | ✅ `FULL_LOGIC_CHAIN.md` 已于 2026-04-01 全文改为 `60,000`，并同步软化由该数字支撑的 screening-scale 叙事 |

---

## FP-017: antechamber `-rn` 参数被文件名覆盖，LLP→AIN 静默改名

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-02, Claude Code (组会 fact-check 时发现) |
| 受影响文件 | `replication/parameters/mol2/Ain_gaff.mol2`, `replication/scripts/parameterize_plp.sh` |
| 错误描述 | `parameterize_plp.sh` 调用 antechamber 时指定 `-rn "LLP"`（PDB 官方残基名），但输出 mol2 里的残基名是 **AIN**（从输出文件名 `Ain_gaff.mol2` 自动提取并大写化）。antechamber 静默忽略了 `-rn` 参数。 |
| 后果 | `prepare_5dvz.py` 用 LLP→AIN 重命名做了补偿（line 286-290），tleap 建系统时两边一致（都是 AIN），所以 **不影响计算结果**。但命名链断裂：PDB(LLP) → script intent(LLP) → actual mol2(AIN) → prepared PDB(AIN) → tleap(AIN)。 |
| 根因 | antechamber 某些版本/调用方式下，`-rn` 不生效，改从输出文件名推断残基名。这是 antechamber 的已知行为，非脚本 bug。 |
| 防范措施 | antechamber 输出后，**必须验证 mol2 内部残基名**（`grep SUBSTRUCTURE -A1 *.mol2`）与预期一致。如不一致，用 `sed` 或在 mol2 中手动修正。不要假设 `-rn` 一定生效。 |
| 已修复 | ⚠️ 不影响结果，暂不修改。记录备查。 |

---

## FP-018: LAMBDA 单位未从 Å⁻² 转换为 nm⁻²

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-04 |
| 发现者 | 3 个并行 subagent（rmsd-checker + units-checker + fes-figure-reader） |
| 受影响文件 | `replication/scripts/plumed_trpb_metad.dat`, `replication/scripts/plumed_trpb_metad_single.dat` |
| 错误描述 | SI 报告 λ=0.029 Å⁻²，直接写进 PLUMED 文件。但 GROMACS+PLUMED 用 nm，LAMBDA 应为 ×100。导致 z(R) 爆炸到 -78（应为 ~0.5） |
| 根因 | 没做 Å→nm 单位转换 |
| 防范措施 | 所有 GROMACS 参数必须检查单位。Checklist: Å→nm (÷10), Å²→nm² (÷100), Å⁻²→nm⁻² (×100), kcal→kJ (×4.184) |
| 已修复 | ✅ LAMBDA=3.3910 nm⁻² |

---

## FP-019: GROMACS 2026 mdrun 接口不支持 PLUMED 反斜杠续行

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-04 |
| 发现者 | Claude Code Terminal |
| 受影响文件 | 所有 plumed.dat 模板 |
| 错误描述 | PLUMED 标准语法允许 `\` 续行，plumed driver 能解析，但 GROMACS 2026 mdrun -plumed 接口截断 `\` 后的行，导致 METAD 报 "SIGMA is compulsory"。这导致之前误以为 ADAPTIVE=GEOM 不可用，使用了固定 SIGMA=0.2,0.1 作为替代。实际上单行格式下 ADAPTIVE=GEOM 可以正常工作。 |
| 根因 | GROMACS 2026 的 PLUMED 接口重新解析输入文件时不处理反斜杠 |
| 防范措施 | 所有 PLUMED 参数写在一行，不使用 `\` 续行 |
| 已修复 | ✅ 所有参数写在一行。ADAPTIVE=GEOM 在单行格式下可正常使用（之前误以为不可用）。 |

---

## FP-020: conda-forge PLUMED 2.9.2 的 libplumedKernel.so 模块残缺（+ 2026-04-09 更正）

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-04 |
| 发现者 | Claude Code Terminal |
| 受影响文件 | conda-forge plumed 2.9.2 包 |
| 错误描述 | plumed driver（独立二进制）能用 PATHMSD/METAD，但 libplumedKernel.so 缺少 colvar/mapping/function 模块。PATHMSD 在 mdrun 中报 "number of atoms in a frame should be more than zero" |
| 根因 | conda-forge 编译只把完整功能编进 plumed 二进制，没编进 .so |
| 防范措施 | 从源码编译 PLUMED（--enable-rpath），用自编译的 libplumedKernel.so |
| 已修复 | ✅ 源码编译 PLUMED 2.9.2 |
| **⚠️ 2026-04-09 更正** | 当时的诊断还包含第二条："PATHMSD 在 mdrun 中只认连续编号 PDB，改用 FUNCPATHMSD 绕过"——**这条是错的**。2026-04-09 在源码编译版 PLUMED 2.9.2 上用 plumed driver + `path_gromacs.pdb`（non-sequential serial 1614, 1621, 1643, ...）直接测试 PATHMSD，完美工作。原本的 "number of atoms in a frame should be more than zero" 错误有两个原因：(a) conda 版 .so 残缺，(b) path PDB 尾部多余的 `END` 行（见 FP-023）。**FP-020 只和 conda 版本有关**，与 atom serial 连续性无关。因为这个误诊，FP-022（FUNCPATHMSD LAMBDA 约定错误）本来是可以避免的——如果当时直接用源码版 + PATHMSD，整个 FP-022 不会发生。 |

---

## FP-021: `plumed sum_hills --kt` 单位必须匹配模拟引擎

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-07 |
| 发现者 | Codex (via /codex:rescue plan review) |
| 受影响文件 | FES 后处理命令、`replication/parameters/JACS2019_MetaDynamics_Parameters.md`（写了 --kt 0.695 kcal/mol） |
| 错误描述 | `plumed sum_hills` 需要 `--kt` 参数才能正确重构 well-tempered MetaD 的 FES。(1) 不加 `--kt` → 输出的是 raw bias potential，不是自由能。(2) 参数文件写 kT=0.695 kcal/mol，但 GROMACS+PLUMED 用 kJ/mol，正确值是 2.908 kJ/mol (= 0.695 × 4.184)。用 0.695 会导致 FES 能量缩放错 ×4.184（30 kJ/mol 变成 ~125 kJ/mol）。 |
| 根因 | kcal/mol vs kJ/mol 单位混淆，与 FP-018 (Å⁻² vs nm⁻²) 属同一类错误 |
| 防范措施 | (1) `sum_hills` 必须加 `--kt`。(2) GROMACS 用 kJ/mol → `--kt 2.908`；AMBER 用 kcal/mol → `--kt 0.695`。(3) B5 sanity check：FES max > 80 kJ/mol → 几乎肯定是 --kt 单位错。 |
| 已修复 | ⚠️ 预防性修复（MetaD 尚未完成，命令已更正在 NEXT_ACTIONS.md） |

---

## FP-022: FUNCPATHMSD LAMBDA 用了 total-SD 约定，差 N_atoms = 112 倍

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-08 |
| 发现者 | Claude + Codex 联合（先 Codex 在 /codex:rescue 第二轮 review 中怀疑 FUNCPATHMSD 语义不对，后 Claude 用本地 Python 数值实验确认 LAMBDA=3.391 给不出自洽结果，最后 PLUMED driver 在 Longleaf 上的实际重跑证实修复有效） |
| 受影响文件 | `replication/metadynamics/path_cv/generate_path_cv.py` (`calculate_lambda` 默认 convention)、`replication/metadynamics/single_walker/plumed.dat` (LAMBDA=3.3910 + 缺 SQUARED)、`replication/metadynamics/plumed/plumed_trpb_metad.dat`、`plumed_trpb_metad_single.dat` 等所有 plumed 模板、`replication/parameters/JACS2019_MetaDynamics_Parameters.md` (Path CV 表)、Job 41514529 的 46.3 ns HILLS/COLVAR（无法用于 FES 重构） |
| 错误描述 | `FUNCPATHMSD` 内部公式是 `s = Σ i × exp(-λ × d_i) / Σ exp(-λ × d_i)`，PLUMED 2.9.2 源码 (`FuncPathMSD.cpp`) 把 ARG 输入直接喂进 exp，**不会内部平方**。我们的 plumed.dat 用 `RMSD ... TYPE=OPTIMAL`（不带 SQUARED），PLUMED 输出的是 per-atom RMSD（nm）。但 LAMBDA=3.3910 是按 "λ = 2.3 / total_SD" 算出来的（其中 total_SD = 0.6783 nm² 是 112 个原子位移平方的总和）。"per-atom MSD = 0.006056 nm²" 才是和 PLUMED 输出兼容的量；正确的 LAMBDA 应该是 2.3/0.006056 = **379.77 nm⁻²**，不是 3.391。**两者差正好 N_atoms = 112 倍。** 症状：相邻 frame 的 kernel weight 是 exp(-3.391 × 0.0778) = 0.77（应该是 exp(-2.3) = 0.10），CV 完全没法分辨 frame，所有构象都被压缩到 s ≈ 4-12（不是 1-15）。Job 41514529 的 46.3 ns COLVAR 显示 s 一直在 7.77-7.83，被误以为是"系统卡在 PC basin"，实际上是"坏 CV 数学伪影 + 系统其实在 O basin（s≈1.05 经修复后重算确认）"。同时因为坏 CV 的梯度 ds/dx 几乎为零，bias 转回原子的物理力极弱，46 ns 等价于无偏置 MD，没有任何增强采样发生。 |
| 根因 | (1) `generate_path_cv.py` 里 `calculate_lambda` 默认 `convention="total_sd"`，main 流程用 `calculate_lambda(total_sd)`，得到 λ ≈ 0.0339 Å⁻²。(2) FP-018 修复时把 0.0339 Å⁻² × 100 = 3.391 nm⁻² 作为最终 LAMBDA 写入 plumed.dat，但没有同时切换 RMSD action 到 SQUARED。(3) FP-020 之前我们用过 PATHMSD（PATHMSD 内部可能用 total-SD 兼容公式），切换到 FUNCPATHMSD 时没意识到约定不同。(4) 没有做 self-consistency test（喂参考帧给 CV 公式，看 frame_i 是否输出 s=i），所以 bug 没被早期发现。(5) PLUMED 自己在 driver 启动时会打印 "Consistency check completed!"，但这条消息只在 driver 模式可见，mdrun 模式下没有，bug 悄悄通过。 |
| 防范措施 | **三层保护**：(1) `generate_path_cv.py` 默认 convention 已改为 `"plumed"`，同时加 assertion 检查 λ ∈ [0.1, 100] Å⁻²（旧的 0.0339 现在会立即报错）；(2) 脚本自动生成 `plumed_path_cv.dat` snippet，包含正确的 SQUARED 关键字 + LAMBDA 数值，**不要再手动从 summary.txt 复制 λ**；(3) 任何新的 plumed.dat 提交前必须跑 self-consistency test (`replication/validations/path_cv_debug_2026-04-08/01_self_consistency_test.py`)，确认 s(frame_i) ≈ i。**通用规则**：path CV 修改后必须用 PLUMED driver 短跑一段已有轨迹（不需要新 MD），看 PLUMED 是否打印 "Your path cvs look good!" 消息，并人工检查 COLVAR 输出范围是否合理。 |
| 已修复 | ✅ 2026-04-08 FUNCPATHMSD + SQUARED + LAMBDA=379.77；**2026-04-09 更优方案**：直接回到 PATHMSD（见 FP-020 更正和 FP-023）。FP-022 的根源是错误地切换到 FUNCPATHMSD，如果当时用源码版 PLUMED + PATHMSD，FP-022 本来就不会出现。 |
| 2026-04-23 corrigendum | Miguel 邮件 (FP-031/032) 触发重新审视 λ。Codex 独立核对（2026-04-23）确认：在我们 15-frame 路径 + PATHMSD 默认 per-atom MSD 约定下，`λ=379.77 nm⁻²` 就是 Branduardi 2007 教科书值（相邻帧权重 ≈ exp(-2.3) ≈ 0.10）。Miguel 的 `80 Å⁻²` 是他**4.6× 更密路径**的对应值，不可直接转移（见 FP-032）。新 plumed 模板把 λ 写成 Å⁻² 下的 `3.77`（= 379.77 nm⁻²），并配 `UNITS LENGTH=A ENERGY=kcal/mol`，物理含义与 FP-022 的结论完全一致。 |

---

## FP-023: PATHMSD reference PDB 尾部多余的 `END` 行导致误读空帧

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-09 |
| 发现者 | Claude (via Longleaf plumed driver test) |
| 受影响文件 | `replication/metadynamics/structures/path_frames/path_fixed.pdb`、`path_gromacs.pdb` 等所有多 MODEL 的 path reference PDB |
| 错误描述 | PLUMED PATHMSD 读多 MODEL PDB 时，每个 `ENDMDL` 或 `END` 之间的内容被当作一个 reference frame。我们的 path_gromacs.pdb 结构是：`MODEL 1 ... ENDMDL MODEL 2 ... ENDMDL ... MODEL 15 ... ENDMDL END`——最后一个 `END` 被 PATHMSD 当作第 16 帧的开始，然后发现第 16 帧没有 ATOM 行，报错 `ERROR in input to action PATHMSD with label path : number of atoms in a frame should be more than zero`。 |
| 根因 | PATHMSD 的多 MODEL 解析对 `END` 和 `ENDMDL` 一视同仁，trailing `END` 被误判为第 N+1 帧的 marker |
| 防范措施 | path reference PDB 必须以 `ENDMDL` 结尾，**不要**有 trailing `END`。应急修复命令：`sed -i "/^END$/d" path_gromacs.pdb`。`generate_path_cv.py` 的 `write_plumed_path_file` 函数已加三重防护（详见下面"已修复"行）。 |
| 已修复 | ✅ 2026-04-09 三层修复都完成：**(1) Longleaf 上**手动 `sed -i "/^END$/d" path_gromacs.pdb` 删除 trailing END，PATHMSD 驱动测试通过（15 帧全部正确读取）；**(2) `generate_path_cv.py` 的 `write_plumed_path_file()` 已更新**——docstring 显式注明 FP-023 (L394-399)；writing loop 只输出 `MODEL/ENDMDL` 不追加 `END` (L401-436)；write 之后加了主动 strip 保护 (L438-445)；最终 `assert lines[-1].strip() == "ENDMDL"` (L446-448)——三重防护；**(3) 同步验证**：本地和 Longleaf 的 `path_gromacs.pdb` md5 一致 (`cbc88225f516d11f07b78d312c9cdfdb`)；Job 42679152 (PATHMSD) 2026-04-09 ~17:25 已在 Longleaf c0301 起跑，PATHMSD kernel 加载成功、`path.sss ≈ 1.04`、0 NaN——实地确认 FP-023 不再触发。 |

---

## FP-024: ADAPTIVE=GEOM 下 SIGMA=0.05 让 Gaussian 塌缩成针尖，bias 堆在 s=1 推不出 O basin

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-15 |
| 发现者 | Claude + Codex + 3 路并行 agent（physics / literature / longleaf forensics）联合诊断，primary-source 验证来自 PLUMED 2.9 官方 METAD 文档 |
| 受影响文件 | `replication/metadynamics/single_walker/plumed.dat`、`replication/metadynamics/annotated/plumed_annotated.dat`、Longleaf 上 Job 42679152 的 50 ns HILLS/COLVAR（可复用做 baseline 对比但无法用于 FES 重构） |
| 错误描述 | Job 42679152（2026-04-09 起跑、2026-04-12 正常结束的 50 ns PATHMSD 单 walker）在修复了 FP-020/022/023 之后物理上正常运行：25,000 个 Gaussian 正常沉积，metad.bias 累积到 48 kJ/mol（≈12 kcal/mol），height 按 well-tempered 规律衰减到 ~0。**但 walker 整个 50 ns 卡在 s(R)=1.00-1.63（74.6% 时间在 s=1.0-1.1，0% 时间在 PC 或 C 区域）**。直接后果：SI 要求"initial run 扫过 s=1..15 然后从 trajectory 抽 10 帧做 10-walker 起点"这一步完全失败，整个 10-walker 阶段卡住。|
| 根因 | PLUMED 2.9 官方 METAD 文档原话："Sigma is one number that has distance units or time step dimensions"（对 ADAPTIVE 模式），即 `SIGMA=0.05` 在 `ADAPTIVE=GEOM` 下表示"Gaussian 应该覆盖 0.05 nm 的 Cartesian 空间"，**是单一标量，不是 CV 单位**。PLUMED 反投影到 s 方向后，实测 sigma_s 从 0.011 长到 0.072（path 轴 1-15 的 0.5-0.7%）；sigma_z 从 0.001 长到 0.003 nm²（针尖）。25,000 个这么窄的 Gaussian 全挤在 s=1.0-1.6，堆成一个深而窄的"尖刺"bias，但 bias 力梯度在 s≈1.6 边界处**不足以匹配真实 FES 的回拉梯度**，walker 每次尝试 s>1.6 都被拉回 s=1，进入振荡死循环。 Osuna SI **只写了"adaptive Gaussian width scheme was used"**（引 Branduardi 2012），从头到尾没给 SIGMA 数值（Agent-B 文献审计确认：2021 ACS Catal follow-up、2024 Faraday Discuss、PLUMED-NEST 全部 defer 到同一个 SI），所以"照 SI"只能照到 HEIGHT/PACE/BIASFACTOR/TEMP/ADAPTIVE=GEOM 这五个明确参数，SIGMA 必须我们自己做 informed choice。 |
| 正确做法 | 保留 `ADAPTIVE=GEOM`，加 `SIGMA_MIN` 和 `SIGMA_MAX`——PLUMED 2.9 文档原话："the lower bounds for the sigmas (in CV units) when using adaptive hills"——即 SIGMA_MIN/MAX 是 **per-CV，在 CV 单位**的 floor/ceiling。我们的选择：`SIGMA_MIN=0.3,0.005`（s 方向至少覆盖 path 2%，z 方向至少 0.005 nm²）+ `SIGMA_MAX=1.0,0.05`（s 方向最多 path 7%，z 方向最多 0.05 nm²）。同时把 `SIGMA` 从 0.05 nm 调到 0.1 nm（Cartesian 几何种子翻倍）。 |
| 防范措施 | (1) **任何 ADAPTIVE=GEOM 的 MetaD 输入必须同时写 SIGMA_MIN 和 SIGMA_MAX**，这两个 key 是 per-CV in CV units（与 SIGMA 本身的单位不同）；(2) **新跑 MetaD 前，先跑 5-10 ns 探针**检查 COLVAR 有没有突破起始 basin，不要一上来就跑 50+ ns；(3) **HILLS 文件第一行的 sigma 列是诊断金标准**——如果 sigma 只有 path 轴 1% 或更小，Gaussian 一定不够宽，99% 会卡住；(4) **写 campaign report 时必须注明哪些参数"SI 明示"、哪些"我们选的默认"**，不要笼统写"follow SI"。 |
| 已修复 | ✅ 2026-04-15 本地 `single_walker/plumed.dat` 和 `annotated/plumed_annotated.dat` 都改到新参数，带 SIGMA_MIN/MAX + FP-024 注释。Longleaf 待部署 + 探针验证。 |

---

## FP-025: Tutorial 里 `[SI p.S3]` 引用的 SIGMA=0.2,0.1 是假的，SI 根本没写

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-15 |
| 发现者 | Claude（在 FP-024 primary-source 验证过程中顺手 grep 发现仓库里 5 个互相冲突的 SIGMA 数值，其中 tutorial 版本带 SI 引用最可疑） |
| 受影响文件 | `project-guide/TrpB_Replication_Tutorial_EN.md` L2028 和 L2087-2088；`project-guide/TrpB_Replication_Tutorial_CN.md` L2089 和 L2148, L2241 |
| 错误描述 | Tutorial 把 `SIGMA=0.2,0.1` 写进 plumed.dat 示例，并在参数解释表注明来源为 `[SI p.S3]`。但我本人用 Zotero MCP + pdf extraction 完整读过 Osuna 2019 SI p.S1-S10，**SI 从头到尾没有任何数值形式的 SIGMA**，只在 p.S3 写了 "The adaptive Gaussian width scheme, in which hills variance adapt to local properties of the free-energy surface, was used"（引 Branduardi 2012）。这个 `[SI p.S3]` 引用是早期写 tutorial 的 AI（大概率 cowork 那轮）凭印象编出来的。| 
| 根因 | 早期文档阶段没有 primary-source 验证要求，AI 写 tutorial 时把"应该有的数字"当作"SI 有的数字"写进表里。同类型问题比 FP-016（Lambert 60k vs 100k）更隐蔽，因为它藏在看起来很权威的参数表里。 |
| 下游影响 | 2026-04-04 debug note 也用了 `SIGMA=0.2,0.1`（没有引用，但显然受 tutorial 影响）；当前生产版又独立改回 `SIGMA=0.05`（也没引用）。仓库里总共 5 个冲突的 SIGMA 数值（见 plan file 表格），都没有明确的 primary source。 |
| 防范措施 | (1) **任何 `[SI p.SX]` 引用必须逐字在原 PDF 里找到匹配段落，不能推断**；(2) **数值参数表的每一行都要有可追溯来源**，来源类型分三种：SI 明示（引用原文页+句）、PLUMED 默认（引官方文档页）、我们选的默认（说明理由）；(3) **Tutorial 和 production 脚本的数值必须 md5 关联同步**，或者 Tutorial 明确标"示例，实际跑用 live 文件"。 |
| 已修复 | ⚠️ FP-025 本身未修：Tutorial 两个版本的 `[SI p.S3]` 假引用还在，参数表和代码块都还是 `SIGMA=0.2,0.1`。计划：下次 Tutorial 大改时一起清理（非 blocking，不影响当前 production 跑）。 |

---

## FP-026: Checkpoint restart of a completed MetaD run silently loses 10 ns of bias without `convert-tpr -extend` + `RESTART`

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-16 |
| 发现者 | Codex stop-time adversarial review on branch `feature/probe-extension-50ns` v1 script |
| 受影响文件 | `.worktrees/probe-extension/replication/metadynamics/single_walker/extend_to_50ns.sh` v1（未部署即被拦） |
| 错误描述 | 为把 Job 43813633 的 10 ns 探针续跑到 50 ns，v1 脚本用的是 `gmx mdrun -cpi metad.cpt -nsteps 25000000 -plumed plumed.dat`。两个独立 bug 叠加会 silently 把 10 ns 成果清零：(1) `metad.tpr` 的 `nsteps=5,000,000`，`metad.cpt` 停在 step 5,000,000（完成状态），mdrun 读完 checkpoint 就判定"simulation already complete" **先于** `-nsteps` override 生效而退出，实际新增步数为 0。(2) `plumed.dat` 没有 `RESTART` 指令，PLUMED 看到 HILLS 已存在，按 no-restart 语义把旧 HILLS 备份到 `bck.0.HILLS` 然后从头沉积，等于丢掉 10 ns 72 kJ/mol bias。|
| 根因 | 对 GROMACS + PLUMED restart 协议的经验依赖写代码，没查 primary source 就声称"safe resume"。PLUMED 2.9 RESTART 官方文档原话（plumed.org/doc-v2.9/user-doc/html/_r_e_s_t_a_r_t.html）：**"not all the MD code send to PLUMED information about restarts. If you are not sure, always put RESTART when you are restarting"**。GROMACS 这边 `-cpi` + `-nsteps` 组合在完成状态 tpr 上的边缘行为官方也没明说，社区标准做法是 `gmx convert-tpr -extend <ps>` 先改 tpr。|
| 正确做法 | 一次续跑拆成两步：(1) `gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr` 生成新 tpr；(2) `gmx mdrun -s metad_ext.tpr -cpi metad.cpt -plumed plumed_restart.dat -deffnm metad ...`，其中 `plumed_restart.dat` 第一行是 `RESTART`，后面 byte-identical 到 plumed.dat。sbatch 带 pre-flight 硬 assert（`grep '^RESTART' plumed_restart.dat`）+ post-flight 硬 assert（`wc -l HILLS` 增加、没有 `bck.*.HILLS`）。|
| 防范措施 | (1) **任何 GROMACS+PLUMED MetaD 续跑**都必须 "convert-tpr -extend → mdrun -cpi with plumed_restart.dat (RESTART 指令)" 两步；(2) 续跑脚本必须有 pre-flight + post-flight 硬 assert；(3) 声称 "safe resume" 之前查两边引擎的 restart 文档；(4) 所有新 sbatch 脚本在部署前 **应该 Codex adversarial review**，不靠经验。|
| 已修复 | ✅ 2026-04-16 v2 `extend_to_50ns.sh` + `plumed_restart.dat` 已部署到 Longleaf；Job 44008381 PD on hov。|

---

## FP-027: 重新诠释 SI "80" 为 λ（本仓 summary.txt 早已解释为 total SD Å²），导致 3+ 小时错误诊断方向

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-16 |
| 发现者 | Codex adversarial review（原话："your new 'SI `80` vs our `379.77` differs 4.75x' diagnosis is comparing different quantities, so the core premise is not sound"）；用户当场确认 "lambda 是我们计算出来的"；仓库 `replication/metadynamics/path_cv/summary.txt` line 23-25 自己早写了 "Reported MSD: ~80 Å² (interpreted as total SD) / Our total SD: 67.826 Å² (ratio 0.85x)" |
| 受影响文件 | 本次 session 内 Claude 的诊断推理（未污染任何 commit 文件）；`.worktrees/alignment-diag/test_alignments.py`（诊断脚本，保留作后续警示，不 merge） |
| 错误描述 | Claude 在 2026-04-16 下午重读 Osuna 2019 SI page S3 原文 "The λ parameter was computed as 2.3 multiplied by the inverse of the mean square displacement between successive frames, 80"，**把末尾的 "80" 解读为 λ 值**（nm⁻² 单位隐含），推出 SI λ=80 vs 我们 379.77 差 4.75×，据此花 3+ 小时追查 "alignment method 不同" 假设：跨物种 sequence alignment 诊断、4 种 Kabsch alignment 变体对比、写完整诊断脚本。最后被 Codex 打穿：这个 "80" 在项目 `summary.txt` line 23-25 早已注明是 total SD Å²（67.826 vs 80 = 0.85× 近乎匹配），不需要重新诠释。|
| 根因 | (1) **没有先读仓库里既有注释就自行重新诠释 SI 数值**；(2) **单位/语义不明时凭语法推断代替 primary-source**（SI "80" 无显式单位；summary.txt 已做 judgment call，应 trust 直到有反证）；(3) **用户在 session 早些时候已说过 "单位问题 i 也说过了"**，Claude 没吃进这个 prior。|
| 正确做法 | (1) **SI 数值在仓库内已有注释的，重新诠释前必须读该注释**并判定"保留原注释"vs"推翻原注释+反证"；(2) **单位/语义歧义时给至少两种读法的数字对照表**，跟用户确认选哪种，不单方面定性；(3) **用户说过的话吃进 prior**，要推翻必须显式说 "I'm pushing back because X"。|
| 下游影响 | 创建 `.worktrees/alignment-diag/` worktree + branch `diag/path-cv-alignment`（保留警示，不 merge）。没有污染生产。Offline CV audit（Codex 推荐）证明 path CV 物理上正确（1WDW→s=1.09, 3CEP→s=14.91, 4HPX→s=14.91）。|
| 防范措施 | (1) **SI 数值诠释必须先读仓库既有注释**；(2) **用户确认过的事实 = prior**；(3) **任何"重大诊断方向切换"前跑一次 Codex adversarial review**；(4) 在 `PARAMETER_PROVENANCE.md` 显式记每个 SI 数值的 current interpretation + alternatives + 选理由。|
| 已修复 | ✅ 2026-04-16 Claude 承认错误、session 内立即停止 alignment 方向、切到 Codex 推荐的 offline CV audit 验证 path CV 物理正确、FP-027 作为永久警示记入。worktree `.worktrees/alignment-diag/` 保留但不 merge。|

---

## 通用规则（从以上模式提炼）

1. **写任何文件前，先读 failure-patterns.md**，检查是否在重复已知错误
2. **区分"看到的"和"确认的"**：AI 从论文提取信息时，必须标注信息来源（main text / SI / Figure / Table），不要混合推断
3. **不要凭记忆写结构数据**（PDB 坐标、原子名、力场参数）。必须从权威来源（rtp 文件、PDB 数据库、SI）复制
4. **索引类数据必须从实际输出确认**：PLUMED 原子索引、残基编号等，必须从工具链的实际输出中读取，不能从输入文件推断
5. **修复错误后，必须在此文件追加新条目**，并更新 CHANGELOG.md
6. **报告中的参数必须从运行文件读取**：验证 note 和图的标题里的温度、力场、时长等数字，必须从 MDP/PLUMED 输入文件确认，不能从 CLAUDE.md 的 Key Decisions 表推断
7. **自动生成的 Gaussian 输入必须验证电子数奇偶性**：`(Z_total - charge) % 2 == 0`。不验证 = 白白浪费 HPC 时间
8. **不要假设 Gaussian 09 和 16 的输入格式完全兼容**：iop 选项、GESP 文件名 section 等可能有格式差异
9. **修复 live file 后，grep 全仓库检查同样错误是否残留在生成脚本或其他文件中**。生成脚本和 live file 必须保持一致
10. **数值函数的返回值必须与函数名语义一致**：`calculate_msd` 必须返回 MSD (A^2)，不能偷偷返回 RMSD (A)。生成 PLUMED 参数时，必须查官方文档确认量的定义
11. **GROMACS 用 nm，AMBER 用 Å**：所有参数跨引擎迁移时必须检查单位。Checklist: Å→nm (÷10), Å²→nm² (÷100), Å⁻²→nm⁻² (×100), kcal→kJ (×4.184)
12. **PLUMED .dat 文件不使用 `\` 续行**：GROMACS 2026 mdrun 接口不正确处理反斜杠，所有参数写在一行
13. **不要信任 conda-forge 的 PLUMED .so 模块完整性**：生产环境必须从源码编译 PLUMED，验证 `plumed info --components` 输出包含所需模块
14. **`plumed sum_hills --kt` 单位必须匹配模拟引擎**：GROMACS 用 kJ/mol → `--kt 2.908`；AMBER 用 kcal/mol → `--kt 0.695`。不加 `--kt` 输出的是 bias potential 不是 FES；用错单位 FES 能量缩放错 ×4.184。（FP-021, Codex review 2026-04-07 发现）
15. **`FUNCPATHMSD` 必须配合 `RMSD ... SQUARED` 使用，且 LAMBDA 用 per-atom MSD 算**：`FUNCPATHMSD` 把 ARG 输入直接喂进 `exp(-λ × d)`，不会内部平方。如果 ARG 是 plain RMSD（nm），那 LAMBDA 单位是 nm⁻¹；如果 ARG 是 SQUARED RMSD = per-atom MSD（nm²），那 LAMBDA 单位是 nm⁻²。**SI 论文里 "λ = 2.3 / MSD" 公式中的 MSD 必须是 per-atom 平均，不是所有原子的 sum**。错用 sum 会让 LAMBDA 小 N_atoms 倍，CV 完全失效。**修改 path CV 必须做 self-consistency test：把每个参考 frame 喂回 CV，frame_i 应该输出 s=i。**（FP-022, Claude+Codex 2026-04-08 发现）
16. **path CV 任何修改后必须用 PLUMED driver 离线验证一段已有轨迹**：`plumed driver --plumed plumed.dat --mf_xtc some.xtc` 启动时会打印 "Your path cvs look good!" 或类似检查消息。这是发现 path CV bug 的最快方式，比重跑 50 ns MetaD 快 100 倍。验证 COLVAR 输出范围是否物理合理。
17. **ADAPTIVE=GEOM 的 MetaD 必须同时写 SIGMA_MIN 和 SIGMA_MAX**：SIGMA 本身是 Cartesian nm 单一标量（PLUMED docs 原话: "Sigma is one number that has distance units"），但反投影到 CV 后的 per-CV sigma 可以任意塌缩到 < 1% path 范围。SIGMA_MIN/MAX 是 per-CV in CV units（docs 原话: "in CV units when using adaptive hills"），必须显式给 floor/ceiling。不加的症状：walker 卡在起始 basin 的一个指甲盖大小窗口里，bias 累积到 10+ kcal/mol 也推不动（FP-024, 2026-04-15）。
18. **新跑 MetaD 前必须先跑 5-10 ns 探针**：HILLS 文件第一行的 sigma 列 + COLVAR 前 2000 行的 s(R) 分布，就能告诉你 Gaussian 宽度合理不合理、walker 有没有从起始 basin 爬出来。不要一上来就投 50-100 ns 长 job 等三天回来才发现卡住（FP-024 教训）。
19. **`[SI p.SX]` 引用必须逐字在原 PDF 里找到匹配**：数值参数表里任何引用 "SI" 的数字，都必须能指向 PDF 里一段包含该数字或直接推导它的原文。推断、"按理应该是"、"follow SI spirit" 都不算；引用类型分三种：SI 明示、PLUMED/软件默认（附官方文档链接）、我们选的默认（说明理由）。防范 FP-016 / FP-025 类"权威感假引用"。
20. **GROMACS+PLUMED MetaD 续跑必须两步 + 两重 assert**：(a) `gmx convert-tpr -s X.tpr -extend <ps> -o X_ext.tpr`；(b) `gmx mdrun -s X_ext.tpr -cpi X.cpt -plumed plumed_restart.dat`，其中 plumed_restart.dat 第一行 `RESTART`；pre-flight `grep '^RESTART' plumed_restart.dat` + post-flight `wc -l < HILLS` 增长且无 `bck.*.HILLS` 生成。声称 "safe resume" 之前查两边官方 restart 文档，不靠经验。（FP-026, 2026-04-16, Codex stop-hook 发现）
21. **SI 数值重新诠释前必须读本仓库对该数值的既有注释**：summary.txt / failure-patterns.md / parameter 表里已经 interpret 过的 SI 数字，重新诠释前必须读注释并判定"保留"或"推翻+反证"，不能单方面换读法然后据此推理。单位/语义不明时给双读对照表跟用户确认。用户确认过的事实作为 prior，要推翻必须显式说。（FP-027, 2026-04-16, Codex adversarial review 发现）

---

## FP-028: conda-forge openmm 8.4 build 的 CUDA PTX 版本高于 Longleaf A100 驱动

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-18 |
| 发现者 | Claude Code Terminal (OpenMM toy Job 44295894 / 44296042 连续 fail) |
| 受影响 env | `/work/users/l/i/liualex/conda/envs/md_setup_trpb` |
| 错误描述 | `Platform.getPlatformByName("CUDA")` → `Context` 构造时抛 `CUDA_ERROR_UNSUPPORTED_PTX_VERSION (222)`。尝试 `module load cuda/12.2` 和 `cuda/13.0` 都不能救。|
| 正确事实 | `mamba install -c conda-forge openmm-plumed` 把 openmm 升到 8.4，并拉 `cuda-nvrtc 13.2.78`。openmm 8.4 conda-forge build 的 PTX 针对 CUDA ≥13.2 driver，Longleaf A100 节点驱动最高对应 `cuda/13.0` module → driver 不认 PTX。module load CUDA 工具链不会改驱动版本。|
| 根因 | 装 openmm-plugin 包时没显式 pin CUDA build。conda-forge 默认给最新 CUDA build，生产集群驱动往往滞后。|
| 防范措施 | 任何新 env 装 openmm 必须 `mamba install 'openmm=*=*cuda12*' 'openmm-plumed=*=*cuda12*' 'cuda-version=12.*'` 显式钉 CUDA 12 build。`nvidia-smi --query-gpu=driver_version` 在 GPU 节点上查实际驱动版本，和 conda-forge openmm build 的 run-constraint `__cuda >=X` 对比。|
| Cross-check | PTX error 和 module load 的 CUDA 版本无关——module load 只改 nvcc/cuBLAS/等工具链，不改内核驱动。排查 GPU 问题先 `cat /proc/driver/nvidia/version` 看真实驱动。|
| 已修复 | ⚠️ 未 — toy 用 `OPENMM_PLATFORM=CPU` 跳过 CUDA 证明链路；生产 TrpB 40k 原子前必须重装 CUDA 12 build 或等 Longleaf 升驱动 |

---

## FP-029: 把 ADAPTIVE=GEOM 误讲成 time-window 语义，并把 well-tempered γ 冷却方向说反

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-21 |
| 发现者 | ChatGPT Pro review 2026-04-21 |
| 受影响文件 | 本次 session 内关于 probe sweep saturation 的口头诊断（未写入生产参数文件） |
| 错误描述 | 我们在解释 probe sweep 的 floor saturation 时，把 `ADAPTIVE=GEOM` 说成了“walker 不动 → time-window / local-diffusion 估计变小 → σ 自然塌缩”的语义；同时又把 well-tempered metadynamics 的 bias factor `γ` 讲成“γ 越大越 aggressive / 冷得更快”。这两句都不对，会把后续诊断带偏到错误的控制轴。 |
| 正确事实 | (1) `ADAPTIVE=GEOM` 是 **geometry-based**：Gaussian 宽度来自 CV 对 Cartesian 坐标的局部几何/Jacobian 映射，不是 DIFF 模式那种 time-window / local-diffusion 语义。不能用“walker 没动，所以 GEOM 自然缩小”来解释 floor saturation。(2) well-tempered metaD 中 **γ 越大，bias tempering 越慢，系统越不‘冷’**；`γ=10` 是 Osuna 2019 SI 的锁定值，不应该被说成“过于 aggressive 导致太快冷却”。 |
| 根因 | (1) 把 Branduardi 2012 里 `GEOM` 和 `DIFF` 两种 adaptive 方案的物理意义混在一起；(2) 对 well-tempered metadynamics 的 `γ = (T+ΔT)/T` 温度关系记反了符号方向，只记住了“有 tempering”而没记住 γ 的单调性；(3) probe sweep 压力下先用直觉解释 saturation，没有先回到一手定义。 |
| 防范措施 | (1) **解释 ADAPTIVE 失败模式前，先明确是 GEOM 还是 DIFF**，不要跨语义借词；(2) **讨论 well-tempered `γ` 时写出单调关系**：γ 大 = slower cooling，γ 小 = faster cooling；(3) 任何“为什么 sigma 会塌缩”的口头诊断，先对照 PLUMED METAD 官方文档里的 scheme 定义，再决定是改 `SIGMA_MIN/MAX`、改 adaptive scheme，还是回到 CV/path audit。 |
| 已修复 | ✅ 2026-04-21 在 Option A dispatch 中明确锁住 `γ=10`，不再把它作为调参方向；并把 probe sweep 解释改成“GEOM saturation 是局部几何映射 + floor/ceiling 约束的问题”，不再套用 DIFF 的 time-window 叙述。 |
| 2026-04-23 corrigendum | Miguel 邮件 (FP-031) 证明 **Osuna 2019 用的是 `ADAPTIVE=DIFF`，不是 GEOM**。本 FP 的 GEOM-vs-DIFF 判别核心仍然成立（两种语义不可互换），但方向搞反了：我们以为 SI 是 GEOM，实为 DIFF。`probe_sweep` 所有 P1–P5 全在 GEOM 下做的 σ-floor/ceiling 扫描，因此对 Osuna 协议不具参考性，需整体标记 deprecated。 |

---

## FP-030: `plumed driver --mf_pdb` 自投影时把 multi-model PATH 参考文件当成 112 原子系统，导致高 atom serial 越界；生产 GROMACS 运行不受影响

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-21 |
| 发现者 | Codex executor diagnostic on Longleaf (`00_self_projection.sh` / `00b_self_projection_renumbered.sh`) |
| 受影响文件 | `/tmp/00_self_projection.sh`（Longleaf 临时诊断脚本，失败）；`replication/metadynamics/path_cv/diagnostics/00b_self_projection_renumbered.sh`（driver-only 修复脚本） |
| 错误描述 | 用 `plumed driver --mf_pdb path_gromacs.pdb` 对 production `PATHMSD` 做自投影时，PLUMED 2.9.2 报 `ERROR in input to action PATHMSD with label path : atom 1614 out of range`。原因是 `path_gromacs.pdb` 中 112 个 Cα 的 ATOM serial 继承自完整 ff14SB/GROMACS 系统（例如 1614 ... 4723），而 `driver --mf_pdb` 只把该 multi-model PDB 本身读成一个 **112 原子** 轨迹；PATHMSD 随后用参考文件里的高 serial 作为索引访问当前系统，超出 112 即报错。 |
| 正确事实 | 这是 **driver-vs-GROMACS 语义差异**，不是生产 PATHMSD bug。Longleaf 生产坐标 `start.gro` / `metad.gro` 的原子数都是 `39268`，因此在 GROMACS+PLUMED 联动时，`path_gromacs.pdb` 里的 serial `1614...4723` 能映射到真实系统原子；但在 standalone `plumed driver --mf_pdb` 诊断里，当前系统只有 112 个原子，必须把参考/轨迹文件临时重编号成 `1..112` 才能自投影。 |
| 正确做法 | 诊断时新建 driver-local 副本 `/tmp/path_driver.pdb`，对 **每个 MODEL 内** 的 `ATOM` serial 依次重编号为 `1..112`，其余 `MODEL/ENDMDL/TER` 原样保留；然后运行 `plumed driver --plumed plumed_self.dat --mf_pdb /tmp/path_driver.pdb`，其中 `REFERENCE=/tmp/path_driver.pdb`、`LAMBDA=379.77` 不变。验证通过后得到 15 行 `ref_selfproj.dat`，`s` 单调且端点约 `1.091 / 14.909`。 |
| 根因 | 把 production 参考 PDB 的 **atom serial 语义** 和 standalone driver 的 **local trajectory indexing 语义** 混为一谈。`PATHMSD` 在生产里依赖 MD 引擎传入的完整系统坐标；`driver --mf_pdb` 只知道自己手上的 112 原子 multi-model PDB。 |
| 防范措施 | (1) **任何用 `plumed driver` 直接读取 production PATH 参考文件的自检**，先检查 `ATOM` serial 是否连续 `1..N`；若不是，先生成 driver-local renumbered copy；(2) 报 `atom XXXX out of range` 时优先检查“参考 serial vs 当前系统 atom count”而不是怀疑 `LAMBDA` 或 atom order；(3) 生产 `plumed.dat` 不要因为 driver 诊断失败而改动，只在诊断脚本里做局部 renumber。 |
| 已修复 | ✅ 2026-04-21 `00b_self_projection_renumbered.sh` 在 Longleaf 上通过：原始 `path_gromacs.pdb` 自投影报 `atom 1614 out of range`，renumbered `/tmp/path_driver.pdb` 成功输出 15 行 `ref_selfproj.dat`（`s`: 1.091318 → 14.908700，`z` 近 0）。 |

---

## FP-031: 把 SI "adaptive Gaussian width scheme" 读成 `ADAPTIVE=GEOM`，实为 `ADAPTIVE=DIFF`

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-23 |
| 发现者 | Miguel Iglesias-Fernández（Osuna 2019 原作者）email 回复 Zhenpeng Liu |
| 受影响文件 | `replication/metadynamics/single_walker/plumed.dat`（旧）；`replication/metadynamics/probe_sweep/**`；`replication/metadynamics/pilot_matrix/**`；`replication/validations/failure-patterns.md` FP-029；`project-guide/TrpB_Replication_Tutorial_{EN,CN}.md` |
| 错误描述 | Osuna 2019 SI 只写 "adaptive Gaussian width scheme to reach a better sampling"，我们读成了 `ADAPTIVE=GEOM`（Branduardi 2012 几何缩放方案），进而围绕 SIGMA/SIGMA_MIN/SIGMA_MAX 做了大量探针扫描（probe_sweep P1–P5 和 pilot_matrix 2×2 设计）。 |
| 正确事实 | Miguel 2026-04-23 邮件给出作者示例 plumed.dat：`METAD ... ADAPTIVE=DIFF SIGMA=1000 ...`。`DIFF` 是 time-window / local-diffusion 方案，`SIGMA=1000` 是**步数**（1000 × 2 fs = 2 ps 局部时间窗），不是 Gaussian 宽度。PLUMED 内部用 walker 近期轨迹估计局部扩散张量，据此自动确定 Gaussian 形状。 |
| 根因 | "adaptive Gaussian width" 在 PLUMED 里有两种独立实现（GEOM, DIFF），SI 未指明；我们没有去查原作者或读 2007/2012 两篇方法论，直接按 PLUMED 文档头条 `GEOM` 的描述推断。 |
| 防范措施 | (1) SI 若对某关键字**只给描述不给语法**，必须找作者确认或在 PR 里明标 `UNVERIFIED`；(2) `ADAPTIVE` 的两个取值语义差异巨大（SIGMA 一个是长度一个是步数），未来遇到同类关键字先列举所有可能再缩小；(3) 涉及 MetaD 复刻的探针/扫描前必须 email 作者一次。 |
| 已修复 | ✅ 2026-04-23 新契约 `replication/metadynamics/miguel_2026-04-23/`：`ADAPTIVE=DIFF SIGMA=1000` 全面替换。`probe_sweep/` 和 `pilot_matrix/` 将标记 DEPRECATED（任务 #36）。FP-029 corrigendum 见其条目新增段落。 |

---

## FP-032: PATHMSD λ 跨 UNITS/nm-vs-Å 不能直接换算，必须 per-path 推导；Miguel 的 λ=80 Å⁻² 不可转移到我们系统

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-23 |
| 发现者 | Codex peer review (2026-04-23) on a user-posed question |
| 受影响文件 | `replication/metadynamics/miguel_2026-04-23/plumed_template.dat`（第一版草稿）；临时 SLURM 作业 `45312786`（已 scancel） |
| 错误描述 | 初读 Miguel 邮件时，把他提供的 `LAMBDA=80` + `UNITS LENGTH=A` 当作"权威值"直接拷进我们的 `plumed_template.dat`，并提交了 10-walker 作业 `45312786`。忽略了 λ 同时依赖**单位**和**路径密度**两个变量。 |
| 正确事实 | λ 的 Branduardi 2007 启发式选法是 `λ ≈ 2.3 / ⟨MSD_adjacent⟩`。Miguel 的 `80 Å⁻²` 反推 ⟨MSD_adj⟩ ≈ 0.029 Å² → 相邻帧 Cα-RMSD ≈ 0.17 Å（他的路径比我们密 ~4.6×）。我们 15 帧路径相邻 Cα-RMSD ≈ 0.78 Å → MSD ≈ 0.61 Å² → λ 应为 `2.3/0.61 = 3.77 Å⁻²`（= 379.77 nm⁻²）。两者即使做单位换算后仍差 ~21×，完全来自路径密度差异。 |
| 根因 | λ 不是一个"作者给的固定常数"，而是**路径相关**的校准量。不同作者的路径（帧数、帧间结构距离、构象跨度）不同，λ 就不同。单位换算（1 Å⁻² = 100 nm⁻²）只是纯尺度；路径密度是物理内容。 |
| 防范措施 | (1) 任何从外部作者拿到的 PATHMSD λ，先用 `plumed driver` 做 self-projection + 核对 `exp(-λ·⟨MSD_adj⟩)` 是否接近 0.1（Branduardi 启发式）；(2) "好看的 self-projection 整数 snap" 不是 validation——过 sharp 核也会给整数投影，需看帧间梯度是否连续；(3) 移植作者脚本时，单位和 λ 要**同时**核对，不要假设换算后就通用。 |
| FP-022 / Miguel email corrigendum | 本项目原先在 FP-022 将 λ 锁定在 `379.77 nm⁻²`（per-atom MSD 约定），该值在当前 15-frame 路径下经 Codex 独立核对确认为 Branduardi 2007 教科书值。Miguel 的 `80 Å⁻²` 是**他系统**的正确值，但不能直接转移。重提交作业 `45320189` 使用 `λ=3.77 Å⁻²`（= 379.77 nm⁻² 换单位版），其余参数 100% Miguel contract。 |
| 已修复 | ✅ 2026-04-23 `plumed_template.dat` / `plumed_single.dat` / `single_walker/plumed.dat` 全部更新为 `LAMBDA=3.77`（Å⁻² 下）；`materialize_walkers.py` 断言也同步更新（`LAMBDA_LITERAL = "LAMBDA=3.77"`）。自投影 gate 通过：`s` 从 1.092 → 14.907 单调，`z ≈ -0.05 Å²`（非零但小，符合 kernel-average 边界效应）。 |
