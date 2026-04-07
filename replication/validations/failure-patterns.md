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

## FP-020: conda-forge PLUMED 2.9.2 的 libplumedKernel.so 模块残缺

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-04-04 |
| 发现者 | Claude Code Terminal |
| 受影响文件 | conda-forge plumed 2.9.2 包 |
| 错误描述 | plumed driver（独立二进制）能用 PATHMSD/METAD，但 libplumedKernel.so 缺少 colvar/mapping/function 模块。PATHMSD 在 mdrun 中报 "number of atoms in a frame should be more than zero" |
| 根因 | conda-forge 编译只把完整功能编进 plumed 二进制，没编进 .so |
| 防范措施 | 从源码编译 PLUMED（--enable-rpath），用自编译的 libplumedKernel.so。同时发现 PATHMSD 在 mdrun 中只认连续编号 PDB，改用 FUNCPATHMSD 绕过 |
| 已修复 | ✅ 源码编译 PLUMED 2.9.2 + FUNCPATHMSD |

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
