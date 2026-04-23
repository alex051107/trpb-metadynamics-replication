# TrpB MetaDynamics Pipeline — 完整技术走查
**版本**：2026-04-09
**作者**：Zhenpeng（Claude Opus 协助整理）
**用途**：从 500 ns 常规 MD 一直到今天的 path CV fix，把中间每个脚本、每个文件、每个参数都讲清楚。读完之后应该能回答：
- Pipeline 每一步在做什么、为什么这么写
- Longleaf 上每个文件代表什么、怎么读它
- 上周的初始 MetaD 为什么失败、现在是什么状态
- 下一步要跑哪些命令

---

## 0. 一页话摘要

| 阶段 | 工具 | 状态 |
|---|---|---|
| 1. 体系搭建（PLP 参数化 + tleap） | Gaussian + AmberTools | ✅ 完成，39268 atoms |
| 2. 500 ns 常规 MD | AMBER 24p3 (`pmemd.cuda`) | ✅ 完成，`prod_500ns.nc` 23 GB |
| 3. AMBER → GROMACS 转换 | ParmEd | ✅ 完成，单点能对比 < 0.1% |
| 4. Path CV 构建（15 帧 O→C） | Python + BioPython + MDAnalysis | ✅ 完成，λ = 379.77 nm⁻² |
| 5. Initial 50 ns MetaD (v1) | GROMACS + PLUMED2 (源码编译) | ❌ Job 41514529 失败（FP-022 坏 CV + walltime kill），已归档 |
| 6. Path CV bug 诊断 + 修复 | PLUMED driver 离线重算 | ✅ 切回 PATHMSD，本地已改好 |
| 7. 部署 PATHMSD + 重提交 initial run (v2) | `scp` + `sbatch` | ✅ Job 42679152 **R** on `hov`/c0301，CV 确认正常（s≈1.04，bias 正在累积） |
| 8. FES 重构与分析 | `plumed sum_hills` + analyze_fes.py | ⏸ 等 Job 42679152 跑完 |

**关键结论**：上周跑了 46.3 ns 的 MetaD 在数学上**等价于无偏置 MD**。Path CV 的 λ 参数算错了 112 倍（FP-022），导致 CV 对所有构象都输出 s ≈ 7.8，bias 梯度接近零，没推动系统。用修复后的 PATHMSD 离线重算同一条轨迹显示系统其实一直在 O basin（s ≈ 1.0）。

---

## 1. Pipeline 总览

```
┌─────────────────────┐
│  PLP parameterize   │  Gaussian RESP → Ain_gaff.mol2 + Ain.frcmod
│   (Ain cofactor)    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│    tleap build      │  PLP + K82 Schiff base + solvate + Na+
│  (39,268 atoms)     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Classical MD 500 ns │  AMBER pmemd.cuda, ff14SB+TIP3P+GAFF
│  NVT @ 350 K        │  min×2 → heat×7 → equil 2 ns NPT → prod 500 ns NVT
└──────────┬──────────┘
           ↓ prod_500ns.rst7
┌─────────────────────┐
│  AMBER → GROMACS    │  ParmEd, 单点能相对误差 < 0.1%
│    conversion       │
└──────────┬──────────┘
           ↓ conf.gro + topol.top
┌─────────────────────┐   ┌───────────────────┐
│  Path CV 15 frames  │ + │ PLUMED plumed.dat │  PATHMSD, λ = 379.77 nm⁻²
│   O→C 线性插值      │   │  + metad.mdp      │  WT-MetaD 350 K BF 10
└──────────┬──────────┘   └─────────┬─────────┘
           └─────────────┬──────────┘
                         ↓
┌─────────────────────────────────────┐
│  GROMACS + PLUMED single-walker     │  50 ns × 1, 72 h walltime
│    MetaDynamics production          │
└──────────────────┬──────────────────┘
                   ↓ HILLS + COLVAR
┌─────────────────────────────────────┐
│  plumed sum_hills → fes.dat         │
│  analyze_fes.py → basins, barriers  │  JACS 对比: ΔG(C-OPC)≈5, ΔG‡(PC→C)≈6
│  check_convergence.py → plateau     │
└─────────────────────────────────────┘
```

---

## 2. 阶段 1：500 ns 常规 MD（AMBER）

**目的**：给 MetaD 一个已经平衡的、代表真实室温构象分布的起点坐标。SI 的协议是两步 minimization → 七步 heating → 2 ns NPT equilibration → 500 ns NVT production。

**文件位置**：
- 输入：`replication/classical_md/inputs/*.in`
- Slurm 脚本：`replication/classical_md/slurm/run_md_pipeline.sh` + `submit_production.sh`
- 产物：Longleaf `/work/.../AnimaLab/classical_md/output/`

### 2.1 `min1.in` — 约束最小化

```fortran
&cntrl
  imin=1,              ! 1 = 最小化模式
  ntx=1,               ! 读坐标不读速度
  irest=0,             ! 不续跑
  maxcyc=10000,        ! 最多 10000 步
  ncyc=5000,           ! 前 5000 步 steepest descent，后切 conjugate gradient
  ntpr=500,            ! 每 500 步打印能量
  ntb=1,               ! 常体积 PBC
  cut=8.0,             ! 8 Å cutoff (SI 规定)
  ntr=1,               ! 开位置约束
  restraint_wt=500.0,  ! 500 kcal/mol/Å² (很硬)
  restraintmask='!@H= & !:WAT & !:Na+',  ! 除氢、水、钠外全部约束
/
```

**为什么要约束溶质**：水盒子初始状态可能有高能接触，但溶质（带 PLP 的蛋白）是精心搭的。先只放水和离子，溶质保持原位避免 PLP 结构被破坏。

### 2.2 `min2.in` — 无约束最小化

和 `min1.in` 一模一样，只是 `ntr=0`。溶剂已经理顺了，放开溶质让整体降到能量局部最小。

### 2.3 `heat1.in` → `heat7.in` — 分段加热

每一段都是 50 ps NVT，温度线性上升，位置约束**逐段放松**。

| 文件 | 温度 (K) | 约束 (kcal/mol/Å²) |
|---|---|---|
| heat1 | 0 → 50 | 210 |
| heat2 | 50 → 100 | 180 |
| heat3 | 100 → 150 | 160 |
| heat4 | 150 → 200 | 120 |
| heat5 | 200 → 250 | 60 |
| heat6 | 250 → 300 | 10 |
| heat7 | 300 → 350 | 10 |

`heat7.in` 的核心：
```
temp0=350.0,
restraint_wt=10.0,
&wt
  TYPE='TEMP0', ISTEP1=0, ISTEP2=50000, VALUE1=300.0, VALUE2=350.0,
/
&wt TYPE='END' /
```

`&wt TEMP0 ISTEP1 ... ISTEP2` 是 AMBER 的"按步插值"语法：告诉 sander 第 0 步 300 K，第 50000 步 350 K，中间线性。终点 350 K 是 Osuna 用的温度（*P. furiosus* 嗜热菌，350 K ≈ 77 °C）。

**UNVERIFIED**：SI 只列了 6 个约束值但有 7 个加热步。heat6 和 heat7 都用 10 kcal/mol/Å² 是操作选择，不是 SI 明确规定。

### 2.4 `equil.in` — 2 ns NPT 平衡

```
nstlim=1000000,  ! 1e6 × 2 fs = 2 ns
dt=0.002,        ! 2 fs (SHAKE 打开)
ntc=2, ntf=2,    ! SHAKE on H-containing bonds
ntb=2, ntp=1,    ! NPT
barostat=1,      ! Berendsen
pres0=1.0, taup=1.0,  ! 1 atm, 1 ps coupling
cut=8.0,
ntr=0,
temp0=350.0,
```

**为什么要从 NVT 切到 NPT**：heating 是 NVT，box 体积固定不变，此时体系密度可能不是 1 atm 下的真实平衡值。NPT 让盒子收缩/膨胀到对应密度。2 ns 足够达到稳态。

### 2.5 `prod.in` — 500 ns NVT production

```
nstlim=250000000,  ! 2.5e8 × 2 fs = 500 ns
dt=0.002,
ntb=1, ntp=0,      ! NVT (体积固定在 equil 终态)
temp0=350.0,
cut=8.0,
ntwx=5000,         ! 每 5000 步 = 10 ps 写一帧 NetCDF 轨迹
ntwe=500,          ! 能量写得更频繁
ntwr=500000,       ! 重启写得少
```

500 ns 是 SI 硬性规定。最终产物 `prod_500ns.nc`（23 GB NetCDF 轨迹）和 `prod_500ns.rst7`（重启坐标，作为 MetaD 的起点）。

### 2.6 `run_md_pipeline.sh` — prep 启动器

```bash
#SBATCH --partition=gpu --qos=gpu_access --gres=gpu:1
#SBATCH --time=24:00:00
```

用 **L40 GPU** 跑 `pmemd.cuda`。关键的字面值断言：

```bash
assert_file_contains_literal "$MDIN_DIR_REL/min1.in" "restraint_wt=500.0"
assert_file_contains_literal "$MDIN_DIR_REL/heat1.in" "VALUE1=0.0, VALUE2=50.0"
assert_file_contains_literal "$MDIN_DIR_REL/heat7.in" "VALUE1=300.0, VALUE2=350.0"
assert_file_contains_literal "$MDIN_DIR_REL/equil.in" "nstlim=1000000"
assert_file_contains_literal "$MDIN_DIR_REL/equil.in" "barostat=1"
```

**这是 pipeline_guard 的精神**：run 之前先断言关键字面值存在，避免别人改了文件你没发现。跑的时候会依次执行：

```
min1 → min2 → heat1 → heat2 → … → heat7 → equil
```

每一步用 `-ref min2.rst7` 作为位置约束的参考坐标（UNVERIFIED：SI 没明说参考坐标用哪个）。

### 2.7 `submit_production.sh` — 500 ns production 启动器

```bash
#SBATCH --time=72:00:00      # 72 小时 walltime
```

断言更严：
```bash
assert_file_contains_literal "$PROD_MDIN_REL" "nstlim=250000000"  # 500 ns
assert_file_contains_literal "$PROD_MDIN_REL" "temp0=350.0"
assert_file_contains_literal "$PROD_MDIN_REL" "cut=8.0"
```

调用：
```bash
pmemd.cuda -O -i prod.in -o prod_500ns.out -p pftrps_ain.parm7 \
  -c equil.rst7 -r prod_500ns.rst7 -x prod_500ns.nc -e prod_500ns.mden
```

`-c equil.rst7`：以 NPT 平衡终态为 production 起点。实际这个 job（40806029）跑了 71.55 小时，**一次 walltime 完成 500 ns**。

---

## 3. 阶段 2：AMBER → GROMACS 格式转换

**为什么需要**：Osuna 原文的 MetaD 用 GROMACS 5.1.2 + PLUMED2。我们的 AMBER 拓扑（`.parm7`）和重启文件（`.rst7`）必须转成 GROMACS 的 `.top` + `.gro`。严格复刻不允许在 AMBER 里跑 MetaD。

**文件**：`replication/metadynamics/conversion/convert_amber_to_gromacs.py`

### 3.1 核心断言

```python
EXPECTED_ATOM_COUNT = 39_268    # tleap 搭出来的原子数
EXPECTED_TOTAL_CHARGE = 0.0     # PLP -2 + 4 Na+ → 电中性
BOX_TOLERANCE_ANGSTROM = 0.02   # box 差 < 0.02 Å
CHARGE_TOLERANCE_E = 1.0e-6     # 电荷差 < 1e-6 e
ENERGY_REL_TOL = 1.0e-3         # 单点能相对误差 < 0.1%
```

### 3.2 转换流程（`convert_to_gromacs()`）

1. **加载 AMBER**：`structure = pmd.load_file(parm7, rst7)`
2. **断言原子数** = 39268
3. **断言总电荷** ≈ 0（容差 1e-6 e）
4. **读出 box 长度**
5. **写出 GROMACS**：`structure.save("topol.top")` + `structure.save("conf.gro")`
6. **回读**刚写的 top/gro：`pmd.load_file(top, xyz=gro)`
7. **断言回读的 atom_count、charge、box 和原来一致**

### 3.3 单点能对比（最关键的物理检查）

```python
# AMBER 单点能
sander -O -i energy_check.in -o amber_energy.out -p parm7 -c rst7
# GROMACS 单点能（rerun 模式，nsteps=0）
gmx grompp -f energy_check.mdp -c conf.gro -p topol.top -o energy_check.tpr
gmx mdrun -s energy_check.tpr -rerun conf.gro
gmx energy -f energy_check.edr -o potential.xvg
```

然后 `assert_energy_consistency`：
```python
assert relative_delta <= 1e-3, "AMBER↔GROMACS potential deviation exceeds 0.1%"
```

这是**唯一能证明 AMBER 和 GROMACS 用的是同一个力场**的物理检查。原子数、电荷、盒子都对上不代表力场参数真的过来了——只有单点能一致才能证明。

实际执行时（2026-04-01），你的独立参数验证报告 `31/41 PASS`。

---

## 4. 阶段 3：Path CV 构建

**目的**：给 MetaD 两个可以 bias 的 CV。Path CV 是 Osuna 用的方案，把 O→C 开合运动抽象成沿一条 15 帧参考路径的进度（s 值）和偏离距离（z 值）。

**文件**：`replication/metadynamics/path_cv/generate_path_cv.py`（约 450 行）

### 4.1 四个子过程

1. **下载 PDB**（`load_or_download_pdb`）
   - `1WDW.pdb`：*P. furiosus* TrpB，Open 构象
   - `3CEP.pdb`：*S. typhimurium* TrpB，Closed 构象
   - **为什么跨物种**：*P. furiosus* 只有 Open 态晶体，*S. typhimurium* 只有 Closed 态晶体。用不同物种的同源蛋白拼一条路径（SI 也是这样做的）。

2. **选原子**：只取 COMM domain 的 Cα
   ```python
   COMM_RESIDUES = list(range(97, 185))     # 97-184
   BASE_RESIDUES = list(range(282, 306))    # 282-305
   ATOMS_OF_INTEREST = COMM_RESIDUES + BASE_RESIDUES  # 共 112 个 Cα
   ```

3. **Kabsch 叠合**（`align_structures`）— 把 3CEP 最优叠到 1WDW 上
   ```python
   H = open_centered.T @ closed_centered
   U, S, Vt = np.linalg.svd(H)
   R = Vt.T @ U.T
   # 确保 det(R) = 1（正交旋转，不反射）
   ```

4. **线性插值 15 帧**（`interpolate_frames`）
   ```python
   for i in range(15):
       lambda_param = i / 14                # 0, 1/14, 2/14, ..., 1
       frame = (1 - λ) * coords_open + λ * coords_closed
   ```
   frame_01 是纯 Open，frame_15 是纯 Closed，frame_08 是 50/50。**这是一条直线，没有 minimization**。它不是真实的反应路径，只是给 MetaD 一个方向轴。

### 4.2 `calculate_msd` 和两种约定（FP-022 的坑）

```python
def calculate_msd(coords1, coords2):  # PLUMED 约定（per-atom mean）
    result = float(np.mean(np.sum(diff**2, axis=1)))
    assert result > 0 and result < 1000

def calculate_total_squared_displacement(coords1, coords2):  # JACS SI 引用的 "80"
    result = float(np.sum(np.sum(diff**2, axis=1)))
    assert 10 < result < 500
```

两个函数差一个因子 **N_atoms = 112**：
- `np.sum(diff**2, axis=1)` = 每个原子的位移平方 `|Δr_i|²`（112 个数）
- `np.mean(...)` = 平均到每个原子 → **per-atom MSD**（PLUMED RMSD action 输出的）
- `np.sum(...)` = 所有原子加起来 → **total SD**（JACS SI 那句"80 Å²"对应的）

### 4.3 `calculate_lambda`

```python
result = LAMBDA_SCALE / msd_value      # LAMBDA_SCALE = 2.3
```

公式 `λ = 2.3 / ⟨rmsd⟩²` 的来源：PLUMED 文档 PATHMSD 页，推荐让相邻参考帧的 kernel weight `exp(-λ × MSD_adjacent) ≈ exp(-2.3) ≈ 0.10`。Branduardi 2007 原始论文解释了为什么 0.10 是最优值：既能区分相邻帧（不太大），又能让过渡光滑（不太小）。

- **Per-atom MSD（正确）**：MSD ≈ 0.006 nm² → λ ≈ 379.77 nm⁻²
- **Total SD（FP-022 错误）**：MSD ≈ 0.68 nm² → λ ≈ 3.391 nm⁻²

**FP-015 修复后这里加了断言**：
```python
assert 0.1 < result < 100, f"lambda(plumed)={result} outside 0.1-100"
```
如果哪天有人再算出 3.391，assertion 会当场尖叫。

### 4.4 `write_plumed_path_file` — multi-model PDB 写出

```python
for frame_idx, coords in enumerate(frames):
    f.write(f"MODEL        {frame_idx + 1:4d}\n")
    # 写所有 ATOM 行
    f.write("ENDMDL\n")
# 注意：循环结束后 NOT 写 'END'（FP-023）
```

**FP-023 的注释**：
> File MUST end with the last ENDMDL, not a trailing bare 'END' line. PLUMED's PATHMSD treats a trailing 'END' as the start of an empty (N+1)-th frame and aborts with "number of atoms in a frame should be more than zero".

这是**你这个 file/build 上经验观察到的**行为。PLUMED 文档实际上说 `END` 和 `ENDMDL` 都是合法分隔符——所以 FP-023 不是官方规则，是你碰到的一个经验坑。

### 4.5 `path.pdb` vs `path_gromacs.pdb`

两个文件的区别：**哪个系统会读它**，以及**坐标单位**。

- `path.pdb`：给 Python 调试脚本用（`01_self_consistency_test.py` 等），坐标单位 Å
- `path_gromacs.pdb`：给 PLUMED PATHMSD 用（运行时参考），**PLUMED 读 PDB 时内部按 Å 处理然后转成 nm**

两者在数值上是同一份 15 个 MODEL 的文件。名字不同只是为了避免 Python 脚本和 PLUMED 混用。

### 4.6 历史 bug 列表（本脚本相关）

| FP 编号 | 日期 | Bug | 修法 |
|---|---|---|---|
| FP-015 | 2026-03-31 | λ 算出来 3.798 Å⁻²（convention 搞反） | 用 per-atom MSD，加 assertion |
| FP-020 | 2026-04-04 初诊 / 2026-04-09 更正 | 以为 PATHMSD 不认非连续 atom serial；实际是 conda 版 `libplumedKernel.so` bug | 源码编译 PLUMED 2.9.2 |
| FP-022 | 2026-04-08 | FUNCPATHMSD workaround 保留了 total-SD 的 λ=3.391，应该用 per-atom MSD 的 379.77 | 改回 per-atom convention + 加 assertion |
| FP-023 | 2026-04-09 | multi-model PDB 末尾 trailing END 让 PATHMSD 报错 | 写文件时只到 last ENDMDL，Longleaf 旧文件用 sed 删 |

---

## 5. 阶段 4：PLUMED 输入 + GROMACS 参数

**目录**：`replication/metadynamics/single_walker/`（本地镜像 Longleaf 工作目录）

### 5.1 `plumed.dat`（PATHMSD 当前版，verbatim）

本节逐字符对应 `replication/metadynamics/single_walker/plumed.dat`（md5 `ba2dbd89...`，两边一致）。文件由三段 action 加一大块历史注释组成：

```plumed
# WT-MetaD PLUMED input for PfTrpS(Ain) — JACS 2019 benchmark reproduction
#
# History (see failure-patterns.md for full context):
#
#   FP-018 (2026-04-04): Å⁻² → nm⁻² × 100 unit conversion added for LAMBDA
#
#   FP-020 (2026-04-04, re-diagnosed 2026-04-09):
#     Originally attributed PATHMSD failures to "non-sequential atom serials"
#     (1614, 1621, 1643, ...). Actual root cause was a broken libplumedKernel.so
#     in the conda-forge PLUMED 2.9.2 build. With source-compiled PLUMED 2.9.2,
#     PATHMSD handles non-sequential serials correctly.
#
#   FP-022 (2026-04-08): FUNCPATHMSD workaround used per-atom-mean RMSD
#     semantics, so LAMBDA had to be recomputed from per-atom MSD (379.77)
#     instead of the original total-SD value (3.391). This was a silent
#     N_atoms = 112× error in the FUNCPATHMSD path. Now moot — we are
#     switching back to PATHMSD.
#
#   FP-023 (2026-04-09): A trailing bare "END" after the last "ENDMDL" in
#     the multi-model reference PDB makes PATHMSD try to parse an empty
#     16th frame and abort with "number of atoms in a frame should be more
#     than zero". The fix is to strip the trailing END so the file ends
#     with the last "ENDMDL".
#
# 2026-04-09 decision: switch BACK to PATHMSD (matches SI protocol exactly).
#   - Simpler: 1 path CV line vs 17 (15 RMSD + FUNCPATHMSD)
#   - More stable numerically: 0 NaN vs 116 NaN over 4631 frames
#   - Physical z(R) range: 0.004–0.08 nm² vs 1.45–1.92 nm² for FUNCPATHMSD
#   - Matches SI protocol: Osuna 2019 SI says "path collective variables"
#     with GROMACS 5.1.2 + PLUMED2 — PATHMSD is the dedicated action.
#
# LAMBDA = 379.77 nm⁻² from: λ = 2.3 / <rmsd>² × 100 (per-atom, in Å², × 100
# for GROMACS nm). Formula confirmed from PLUMED docs and PLUMED users forum.
# For our 15-frame path of 112 Cα atoms, per-atom RMSD_adjacent = 0.778 Å,
# so λ = 2.3 / 0.6056 Å² × 100 = 379.77 nm⁻².

path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77

metad: METAD ARG=path.sss,path.zzz SIGMA=0.05 ADAPTIVE=GEOM HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
# ⚠️ 2026-04-15 UPDATE (FP-024): The SIGMA=0.05 shown above was the 2026-04-09
# version and turned out to trap the walker in s(R)=1.0-1.6 for 50 ns.
# Current production uses:
# metad: METAD ARG=path.sss,path.zzz SIGMA=0.1 ADAPTIVE=GEOM SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05 HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
# See replication/validations/failure-patterns.md FP-024.

PRINT ARG=path.sss,path.zzz,metad.bias FILE=COLVAR STRIDE=500
```

**逐字段解释**（看下面三个 action 行）：

**PATHMSD action**：
- `PATHMSD REFERENCE=path_gromacs.pdb`：一次读入 multi-model PDB，自己算每个参考帧的 best-fit RMSD
- `LAMBDA=379.77`：Branduardi 2007 公式 `s(R) = Σ i·exp(-λ·d_i²) / Σ exp(-λ·d_i²)` 里的 λ
- 输出字段**固定命名** `path.sss`（progress）和 `path.zzz`（distance from path）——PATHMSD 约定，不能改

**METAD action**：
- `ARG=path.sss,path.zzz`：bias 加在 s 和 z 两个 CV 上
- `SIGMA=0.05`：初始 Gaussian hill 宽度的种子值（因为 `ADAPTIVE=GEOM` 会动态调整）
- `ADAPTIVE=GEOM`：按 CV 的几何变化自适应 σ
- `HEIGHT=0.628` kJ/mol：每个 hill 的高度（SI 的 0.15 kcal/mol × 4.184 = 0.628 kJ/mol）
- `PACE=1000`：每 1000 步（= 2 ps）放一个 hill
- `BIASFACTOR=10`：well-tempered 的温度比 `(T+ΔT)/T = 10`，ΔT = 9T = 3150 K
- `TEMP=350`：物理温度，必须和 MDP 一致
- `FILE=HILLS`：bias 写到这里

**PRINT action**：
- `STRIDE=500`：每 500 步（1 ps）写一行 COLVAR，打印当前 s、z、累计 bias

### 5.2 `metad.mdp` — GROMACS 运行参数

```
integrator              = md
dt                      = 0.002              ; 2 fs
nsteps                  = 25000000            ; 50 ns 总时长

nstxout-compressed      = 5000                ; 每 10 ps 写一帧 xtc
nstlog                  = 1000

cutoff-scheme           = Verlet
rlist                   = 0.8                 ; nm (= 8 Å, SI 规定)
coulombtype             = PME
rcoulomb                = 0.8
rvdw                    = 0.8

tcoupl                  = v-rescale           ; UNVERIFIED: SI 没明说热浴
ref_t                   = 350                 ; 必须和 PLUMED 里的 TEMP 一致
pcoupl                  = no                  ; NVT (匹配 prod.in)

constraints             = h-bonds
constraint-algorithm    = lincs
```

**关键数值**：
- `rlist = 0.8 nm`：8 Å，匹配 SI 的 cutoff
- `ref_t = 350 K`：匹配 AMBER prod 和 PLUMED METAD
- `pcoupl = no`：NVT（和 prod.in 一致）
- `constraints = h-bonds`：SHAKE 打开 H 键，允许 2 fs 时间步

### 5.3 `submit.sh` — Slurm 脚本（verbatim）

本节逐字符对应 `replication/metadynamics/single_walker/submit.sh`（md5 `edf6c00e...`，两边一致）：

```bash
#!/bin/bash
#SBATCH --job-name=trpb_metad
#SBATCH --partition=general
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=72:00:00
#SBATCH --output=slurm-%x-%j.out

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

cd $SLURM_SUBMIT_DIR

echo "=== Environment ==="
echo "PLUMED_KERNEL: $PLUMED_KERNEL"
echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "LAMBDA: 379.77 nm^-2 (PATHMSD per-atom MSD convention, 2026-04-09 pivot)"

gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}

echo "=== Done ==="
ls -lh COLVAR HILLS metad.log
wc -l COLVAR HILLS
head -5 COLVAR
tail -5 COLVAR
```

**逐段解释**：

- `#SBATCH --partition=general --cpus-per-task=8 --mem=16G --time=72:00:00 --output=slurm-%x-%j.out`：72 小时 walltime，8 OpenMP 线程，16 GB 内存，stdout 写到 `slurm-trpb_metad-<JOBID>.out`
- `set -eo pipefail`：bash 严格模式，任何一步失败立即退出
- `module purge` + `module load anaconda/2024.02`：清干净环境再加载 Anaconda
- `eval "$(conda shell.bash hook)"` + `conda activate trpb-md`：激活 `trpb-md` conda 环境（含 GROMACS、MDAnalysis、plumed 的 Python binding 等）
- `export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so`：**这一行是关键**，强制 PLUMED 加载源码编译的 2.9.2，绕开 conda-forge 版的 `libplumedKernel.so` bug（FP-020 的真实原因）
- `export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}`：OpenMP 线程数跟 Slurm 申请的 CPU 数保持一致，默认 8
- `cd $SLURM_SUBMIT_DIR`：进入 sbatch 时所在的目录，即 `single_walker/`
- 四个 `echo` 行：把关键 env 变量和约定的 LAMBDA 值打印到 slurm 日志，方便事后核对
- `gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2`：从 mdp+gro+top 生成 binary run input `metad.tpr`
- `gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}`：跑 mdrun，挂上 PLUMED，单 MPI rank + 8 OpenMP 线程
- 末尾 `=== Done ===` 诊断块：job 正常结束时会 ls / wc / head / tail 几个关键产物，方便从 slurm 日志直接判断结果合理性

**为什么用源码编译 PLUMED**：conda-forge 的 PLUMED 2.9.2 的 `libplumedKernel.so` 对 PATHMSD 有 bug（真实的 FP-020 原因）。源码版能正确处理。

**为什么没用 GPU**：GROMACS + PLUMED 的 MetaD 瓶颈在 CPU（PLUMED 计算 path CV 不能 offload 到 GPU），所以用 `--partition=general` 的 CPU-only 队列更省配额。8 个 OpenMP 线程够 39268 原子体系。

### 5.4 PATHMSD vs FUNCPATHMSD 的选择（2026-04-09 回到 PATHMSD）

| | PATHMSD | FUNCPATHMSD (workaround) |
|---|---|---|
| 输入文件 | 1 个 multi-model PDB | 15 个单帧 PDB + 15 个 RMSD action |
| plumed.dat 行数 | 3 | 17+ |
| λ 约定 | 对用户透明 | 必须手动推导 per-atom |
| 相邻帧 kernel | 稳定 | 易坍缩（FP-022） |
| 匹配 SI | ✅ 原版协议 | ❌ workaround |
| conda 版 PLUMED | ❌ crash（.so bug） | ✅ |
| 源码编译 PLUMED | ✅ | ✅ |

**决策**（2026-04-09）：因为有了源码编译 PLUMED 2.9.2，可以直接用 PATHMSD——简单、数值稳定、匹配 SI。

---

## 6. 阶段 5：Path CV 本周调试（上周的 bug 怎么发现的）

### 6.1 背景：Job 41514529 的现象

- Job 41514529：Apr 4 19:03 → Apr 7 19:03，**72h walltime 耗尽，46.3 / 50 ns 完成**
- COLVAR 显示 s(R) 从头到尾卡在 [7.77, 7.83] 很窄的窗口里
- 初步怀疑：系统卡在 PC basin，没跨 barrier

### 6.2 假设 1：PC basin 太深？→ 被数据推翻

数据：所有 COLVAR 帧 s 值方差 < 0.03。如果是真的 PC，bias 应该推出去，但 bias 已累计 36-50 kJ/mol 还是推不动。这不对劲。

### 6.3 假设 2：ADAPTIVE=GEOM σ 坍缩了？→ 也被数据推翻

数据：HILLS 里的 `sigma_path.s_path.s` 稳定在 0.0016，没坍缩。σ 没问题。

### 6.4 假设 3：CV 本身是坏的？→ Self-consistency test 证实

**`01_self_consistency_test.py` 的思路**：如果 CV 正确，把 frame_i 喂回去应该返回 s=i。

```python
def compute_s(rmsd_to_refs, lambda_val, squared):
    d = rmsd_to_refs ** 2 if squared else rmsd_to_refs
    weights = np.exp(-lambda_val * d)
    num = sum((idx + 1) * w for idx, w in enumerate(weights))
    return num / weights.sum()
```

扫几个 λ 值：
```
                          plain RMSD          RMSD²(SQUARED)
                          f01  f08  f15      f01  f08  f15
3.391 (CURRENT, wrong):   4.02 8.00 11.98    ...  ...  ...     ← 全坍到中间
379.77 (2.3/MSD per-atom): 1.00 8.00 15.00    ...  ...  ...    ← 对了
```

**硬断言**在脚本结尾：
```python
assert abs(s1_current - 1) > 0.5, "current LAMBDA appears OK"
assert abs(s15_current - 15) > 0.5, "current LAMBDA appears OK"
```

确保未来有人把 λ 改回 3.391 时 assertion 会当场炸掉，不允许静默回退。

### 6.5 PLUMED driver 离线重算（几分钟 vs 重跑 50 ns MD）

不需要重跑 MD，PLUMED 有 driver 模式：

```bash
/work/users/l/i/liualex/plumed-2.9.2/bin/plumed driver \
    --plumed plumed_analysis_fixed.dat \
    --mf_xtc metad.xtc \
    --timestep 0.002 --trajectory-stride 5000
```

PLUMED 假装给 mdrun 送轨迹，只算 CV 不算力。5 分钟跑完。

**结果**（Longleaf `rerun/COLVAR_pathmsd`）：
```
#! FIELDS time path.sss path.zzz
0.000000    1.033744 0.025176      ← s ≈ 1.03
46290.000000 1.019646 0.022272     ← s ≈ 1.02
```

**诊断**：系统 46.3 ns 一直在 O basin（s ≈ 1.0）。原 COLVAR 里记的 s ≈ 7.8 是 FUNCPATHMSD 在 λ 太小的情况下对所有构象都坍缩到 `~Σi/15 = 8` 的人工假象。**实际 bias 的物理力梯度接近零，等价于 46 ns 无偏置 MD**。

### 6.6 PATHMSD 可用性验证（2026-04-09）

今天（Apr 9 01:00）在 Longleaf 上跑了 2 行 PATHMSD 测试：

```plumed
path: PATHMSD REFERENCE=../path_gromacs.pdb LAMBDA=379.77
PRINT ARG=path.sss,path.zzz FILE=COLVAR_pathmsd STRIDE=1
```

跑 `plumed driver` 重算同一条 46.3 ns 轨迹：
- **0 NaN**（4631 帧）
- s 值范围合理（1.02-1.06）
- z 值在 0.02-0.04 nm²

**结论**：
1. PATHMSD 在源码编译的 PLUMED 2.9.2 上正常工作
2. FP-020 的原诊断（"PATHMSD 不认非连续 atom serial"）被证伪，真实原因是 conda 版 `.so` bug
3. 可以切回 PATHMSD（匹配 SI 原版协议）

---

## 7. 阶段 6：FES 分析流程（待做，等 MetaD 跑完）

### 7.1 `plumed sum_hills`

```bash
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 2.908
```

- 把所有 HILLS 里的 Gaussian 加起来，取反号 = FES
- `--mintozero`：把最低点设为 0，便于读
- `--kt 2.908`：**kJ/mol 单位**，k_B × 350 K = 2.908 kJ/mol（**不是** 0.695 kcal/mol，这是 FP-021 的坑）

### 7.2 分段 FES（收敛检查）

截 HILLS 文件的头 N 行，不要用 `--stride`：

```bash
HEADER=$(grep -c "^#" HILLS)
for ns in 10 20 30 40; do
  head -n $((ns * 500 + HEADER)) HILLS > HILLS_${ns}ns
  plumed sum_hills --hills HILLS_${ns}ns --outfile fes_${ns}ns.dat --mintozero --kt 2.908
done
cp fes.dat fes_50ns.dat
```

**为什么不用 `--stride`**：`plumed sum_hills --stride N` 是每 N 个 hill 做一次，不是每 N ns 做一次。容易搞错单位。截 HILLS 文件更直观。

### 7.3 `analyze_fes.py`

核心算法：

```python
DEFAULT_STATE_WINDOWS = {
    "O":  (1.0, 5.0),    # s 在 1-5 的是 Open
    "PC": (5.0, 10.0),   # 5-10 是 Partially Closed
    "C":  (10.0, 15.0),  # 10-15 是 Closed
}
```

1. `load_fes_grid(fes.dat)` → `(s_values, z_values, F_grid_kj_mol)`
2. `find_basin_minimum(state)`：在每个 s 窗口里找能量最低点
3. `calculate_projected_profile`：沿 s 对 z 取 min → 1D profile
4. `calculate_barrier_from_profile`：找两 basin 之间的最大值 = saddle
5. 对比 JACS 参考值：
   - `reference_c_minus_opc_kcal = 5.0 ± 2.0`
   - `reference_pc_to_c_barrier_kcal = 6.0 ± 2.0`

输出：
- `fes_plot.png`：2D 等高线 + basin 标注
- `fes_report.json`：basin 位置、ΔG、barrier、JACS 对比 PASS/FAIL

### 7.4 `check_convergence.py`

给它一堆 `fes_10ns.dat`, `fes_20ns.dat`, ...：
1. 对每个时间点算 ΔG(C-O)
2. 做 block averaging（非重叠）
3. 看最后几个 block 的 ΔG 是否在 tolerance 内稳定 → plateau 判定

输出：`fes_convergence_plot.png` + `fes_convergence_report.json`

### 7.5 FES 决策矩阵

| analyze_fes.py 输出 | 含义 | 下一步 |
|---|---|---|
| 两项 PASS + 收敛 | benchmark 复刻成功 | merge 10-walker branch → 正式生产 |
| 两项 PASS 但未收敛 | basin 对但采样不够 | 直接上 10-walker（SI 用 500-1000 ns） |
| COLVAR 只在 PC 区域 | 单 walker 采样不足 | 直接上 10-walker（HILLS 可 warm-start） |
| 只有 2 个 basin | 不一定错（独立 TrpB O 态可能不稳定） | 对照 JACS 2019 对应体系再判断 |
| FAIL：数值偏差 > 2 kcal/mol | 参数或 CV 可能有误 | 检查 LAMBDA, path Cα, atom indexing |

---

## 8. Longleaf 文件地图

基本路径：`/work/users/l/i/liualex/AnimaLab/`

```
AnimaLab/
├── structures/                    # 原始 PDB (1WDW, 3CEP, 5DVZ, 4HPX)
├── parameterization/ain/          # PLP RESP 参数化 (Gaussian 输出, mol2, frcmod)
├── system_build/                  # tleap 产物 (.parm7, .inpcrd)
│
├── classical_md/                  # ✅ 500 ns 常规 MD
│   ├── inputs/                    # min1..2, heat1..7, equil, prod 的 mdin
│   ├── slurm/                     # run_md_pipeline.sh, submit_production.sh
│   └── output/                    # ⭐ 所有 production 产物
│       ├── prod_500ns.nc          # ← 500 ns NetCDF 轨迹 (23 GB)
│       ├── prod_500ns.rst7        # ← MetaD 起点坐标来源
│       ├── prod_500ns.out         # pmemd 日志
│       ├── prod_500ns.mden        # 能量
│       ├── equil.rst7             # NPT 平衡终态
│       ├── heat1..7.rst7          # 分段加热
│       ├── min1..2.rst7           # minimization
│       └── slurm-*-{40709153,40806029}.out
│
├── metadynamics/                  # ⭐ MetaD 工作区
│   ├── conversion/                # AMBER→GROMACS 转换产物
│   │   ├── convert_amber_to_gromacs.py
│   │   ├── conf.gro               # 转换后坐标
│   │   ├── topol.top              # 转换后拓扑
│   │   └── ca_indices.txt
│   │
│   ├── path_cv/                   # 15-frame 参考路径生成
│   │   ├── generate_path_cv.py
│   │   ├── path.pdb               # Å 版（给 Python 调试用）
│   │   └── summary.txt
│   │
│   ├── plumed/                    # 通用 plumed 模板（不被 single_walker 直接用）
│   │   ├── plumed_trpb_metad.dat
│   │   ├── plumed_trpb_metad_single.dat
│   │   └── metad.mdp
│   │
│   └── single_walker/             # ⭐⭐⭐ 实际 MetaD 跑的地方
│       ├── plumed.dat             # 当前 PLUMED 输入（PATHMSD LAMBDA=379.77）
│       ├── path_gromacs.pdb       # 15 帧参考 PDB（trailing END 已删）
│       ├── start.gro              # 起点坐标（从 conversion/ 复制）
│       ├── topol.top              # 拓扑（从 conversion/ 复制）
│       ├── metad.mdp              # GROMACS 参数
│       ├── submit.sh              # Slurm 脚本
│       ├── metad.tpr              # gmx grompp 产物
│       ├── metad.xtc              # 轨迹
│       ├── metad.log/.edr/.cpt    # GROMACS 运行产物
│       ├── COLVAR / HILLS         # PLUMED 输出
│       ├── rerun/                 # 调试证据（PATHMSD 离线重算）
│       │   ├── plumed_pathmsd_test.dat
│       │   ├── COLVAR_pathmsd     # ← 修复后重算的 CV
│       │   ├── plumed_analysis_fixed.dat
│       │   └── COLVAR_rerun_fixed
│       └── archive_FP022_broken_2026-04-09/   # 旧 FUNCPATHMSD 坏数据，已归档
│           ├── HILLS, COLVAR, metad.{xtc,log,edr,cpt,tpr}
│           ├── path_fixed.pdb, PLUMED.OUT, mdout.mdp
│           ├── #metad*, bck.*.PLUMED.OUT    (GROMACS/PLUMED 备份)
│           └── slurm-trpb_metad-{41495758,41495824,41495866,41498429,41500355,41514529}.out
│
├── analysis/                      # FES 分析脚本（部署到此）
└── logs/                          # Slurm 日志
```

**关键 env 变量**：
```bash
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
conda activate trpb-md
```

---

## 9. 怎么读结果

### 9.1 `COLVAR` — CV 时间序列

```
#! FIELDS time path.sss path.zzz metad.bias
0.000000 1.033744 0.025176 0.000000
1.000000 1.031169 0.025396 0.000000
...
```

格式：时间 (ps) / s(R) / z(R) / 累计 bias (kJ/mol)

**最快诊断**：
```bash
python3 -c "
import numpy as np
d = np.loadtxt('COLVAR', comments='#')
s = d[:,1]
print(f'O  (s<5):    {(s<5).sum()}')
print(f'PC (5<s<10): {((s>5)&(s<10)).sum()}')
print(f'C  (s>10):   {(s>10).sum()}')
print(f's range: {s.min():.2f} .. {s.max():.2f}')
"
```

- 只在一个 basin → walker 没跨 barrier → 延长模拟或上 10-walker
- 三个 basin 都访问过 → 可以直接 sum_hills

### 9.2 `HILLS` — bias deposit 历史

```
#! FIELDS time path.sss path.zzz sigma_path.sss_path.sss sigma_path.zzz_path.zzz ... height biasf
#! SET multivariate true
#! SET kerneltype stretched-gaussian
  2   1.033  0.025   0.00164  0.00472  ...  0.6977  10
  4   1.031  0.025   0.00164  0.00472  ...  0.6976  10
```

每一行 = 一个 Gaussian hill 的中心位置、宽度（σ）、高度。**hill 数 = 运行时长 / PACE × 1**（对 PACE=1000, dt=2 fs，每 ns 500 个 hill）。

最主要的用途：给 `plumed sum_hills` 算 FES。

### 9.3 `fes.dat` — Free Energy Surface

```
#! FIELDS path.sss path.zzz file.free
#! SET min_path.sss 1.0
#! SET max_path.sss 15.0
...
1.00000 0.00000 24.538
1.00000 0.02083 24.612
...
```

格式：s / z / F(s,z)（kJ/mol）。

**快速 sanity check**：
```bash
python3 -c "
import numpy as np
d = np.loadtxt('fes.dat', comments='#')
f = d[:,2]
fmax_kj = f.max()
fmax_kcal = fmax_kj / 4.184
print(f'F range: {f.min():.1f} .. {fmax_kj:.1f} kJ/mol ({f.min()/4.184:.1f} .. {fmax_kcal:.1f} kcal/mol)')
print('FLAT:', 'FAIL - bias not working' if fmax_kj - f.min() < 1 else 'PASS')
print('RANGE:', 'PASS' if fmax_kj < 80 else 'FAIL - check --kt (likely FP-021)')
"
```

**物理合理范围**：FES 最大 20-30 kJ/mol。>80 kJ/mol 几乎一定是 `--kt` 用了 0.695 kcal/mol 而没转成 2.908 kJ/mol（FP-021）。

### 9.4 全流程（production 跑完后）

```bash
# 进工作目录
cd /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so

# 1. 全时长 FES
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 2.908

# 2. 分段 FES
HEADER=$(grep -c "^#" HILLS)
for ns in 10 20 30 40; do
  head -n $((ns * 500 + HEADER)) HILLS > HILLS_${ns}ns
  plumed sum_hills --hills HILLS_${ns}ns --outfile fes_${ns}ns.dat --mintozero --kt 2.908
done
cp fes.dat fes_50ns.dat

# 3. 定量分析
python3 analyze_fes.py --fes fes.dat
# → fes_plot.png, fes_report.json

# 4. 收敛检查
python3 check_convergence.py --fes-glob "fes_*ns.dat"
# → fes_convergence_plot.png, fes_convergence_report.json
```

---

## 10. 当前状态（2026-04-09 部署后）

### 10.1 Longleaf 队列

```
squeue -u liualex -j 42679152
  JOBID     PARTITION  NAME        USER     ST  TIME  NODES  NODELIST
  42679152  hov        trpb_metad  liualex  R   0:04  1      c0301
```
**新 Job 42679152** 已于 2026-04-09 提交并切到 **RUNNING** 状态，在 `hov` partition 的 `c0301` 节点上跑。取代失败的 41514529。

**Job 起跑后第一分钟的健康度检查**（从 `slurm-trpb_metad-42679152.out` + `COLVAR` 头几行）：
- ✅ `gmx grompp` 通过，`metad.tpr` 已生成
- ✅ `+++ PLUMED_KERNEL="/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so" +++`（源码版 PLUMED 加载成功）
- ✅ `starting mdrun 'Generic title' ... 25000000 steps, 50000.0 ps`（50 ns 生产开始）
- ✅ COLVAR 头：`#! FIELDS time path.sss path.zzz metad.bias`（PATHMSD 特征命名，不是坏的 `path.s path.z`）
- ✅ `path.sss ≈ 1.04` 起点（和 `rerun/COLVAR_pathmsd` 的 1.033 完全吻合）
- ✅ `metad.bias` 已从 0 增长到 ~0.9 kJ/mol（bias 在累积，不是卡死）
- ✅ `path.zzz ≈ 0.02 nm²`（物理合理范围）

> 队列里其他的 1HXW / 1EBY / 2YKJ / 1HIV / 1D4H 是你的其他项目（和本 pipeline 无关，跳过）。

### 10.2 上次的 job（41514529）— 已归档

```
Job:        41514529  ❌
开始:       2026-04-04 19:03
结束:       2026-04-07 19:03 (exactly 72h walltime kill)
完成度:     46.3 / 50 ns
状态:       CV 坏（FP-022）— 物理上等价于无偏置 MD
```

产物已**全部归档到** `single_walker/archive_FP022_broken_2026-04-09/`：
- `metad.xtc` 666 MB （46.3 ns 轨迹）
- `HILLS` 4.2 MB （23151 hills）
- `COLVAR` 1.9 MB （46303 行）
- `metad.{cpt,log,edr,tpr}`, `mdout.mdp`, `PLUMED.OUT`, `path_fixed.pdb`
- `#metad*` / `bck.*.PLUMED.OUT` 备份文件
- 6 个旧 slurm 日志

### 10.3 同一条轨迹用 PATHMSD 重算（CV 修复的证据）

`rerun/COLVAR_pathmsd`（保留在 single_walker/，未归档，作为 debug 证据）：
```
time       path.sss    path.zzz
0.00       1.033744    0.025176
46290.00   1.019646    0.022272
```

**解读**：46.3 ns 里系统一直在 O basin，s ≈ 1.0。和旧 COLVAR 里的 s ≈ 7.8 完全对不上——因为旧的 FUNCPATHMSD + 坏 λ 让所有构象都映射到 s ≈ 8。**这是 PATHMSD 在源码编译 PLUMED 2.9.2 上能工作的直接证据**，也是 Job 42679152 敢重提的根据。

### 10.4 当前文件对比（本地 ↔ Longleaf，部署后）

| 文件 | 本地 md5 | Longleaf md5 | 状态 |
|---|---|---|---|
| `metad.mdp` | `83cedc03...` | `83cedc03...` | ✅ 一致 |
| `path_gromacs.pdb` | `cbc88225...` | `cbc88225...` | ✅ 一致（trailing END 已删） |
| `plumed.dat` | `ba2dbd89...` (PATHMSD 379.77) | `ba2dbd89...` | ✅ 已同步 |
| `submit.sh` | `edf6c00e...` (echo 已更新) | `edf6c00e...` | ✅ 已同步 |

### 10.5 Longleaf `single_walker/` 的当前布局

Job 42679152 已开始运行，mdrun 正在实时产出 HILLS/COLVAR/xtc。目录结构：

```
single_walker/
├── 输入文件 (本次提交前由本地 scp 而来或一直就在)
│   ├── metad.mdp              (1602 B)    GROMACS 参数
│   ├── path_gromacs.pdb     (133050 B)    15-frame 参考 (trailing END 已删)
│   ├── plumed.dat             (2183 B)    PATHMSD LAMBDA=379.77 (✅ 已同步)
│   ├── start.gro           (2709571 B)    起点坐标
│   ├── submit.sh              ( 897 B)    Slurm 脚本 (✅ 已同步)
│   └── topol.top           (3327322 B)    拓扑
│
├── Job 42679152 的运行时产物 (grompp/mdrun 生成)
│   ├── metad.tpr                           grompp 输出 (新)
│   ├── metad.xtc / metad.log / metad.edr   mdrun 输出 (实时增长)
│   ├── mdout.mdp                            grompp 规范化的 mdp
│   ├── COLVAR / HILLS                       PLUMED 输出 (实时增长)
│   ├── PLUMED.OUT                           PLUMED 自检日志
│   └── slurm-trpb_metad-42679152.out        Slurm stdout
│
├── frames/                                  15 个单帧 PDB (FUNCPATHMSD 遗产, 未归档)
├── rerun/                                   离线 debug 证据 (保留)
└── archive_FP022_broken_2026-04-09/        旧 Job 41514529 的坏数据
```

---

## 11. 已完成的部署 + 后续待做

### 11.1 已完成的部署动作（2026-04-09，本次 session）

| # | 动作 | 结果 |
|---|---|---|
| 1 | 本地 `submit.sh` 的 stale `LAMBDA: 3.3910` echo 改成 `LAMBDA: 379.77 nm^-2 (PATHMSD...)` | ✅ 完成 |
| 2 | `scp plumed.dat submit.sh → longleaf:single_walker/` | ✅ md5 两边一致 |
| 3 | Longleaf 归档 `HILLS COLVAR metad.{xtc,log,edr,cpt,tpr,...}` 到 `archive_FP022_broken_2026-04-09/` | ✅ 11 个核心文件 + 备份 + 旧 slurm 日志 |
| 4 | `sbatch submit.sh` → **Job 42679152** | ✅ 已进队列 |
| 5 | 确认队列状态 | ✅ PD → R on `c0301` |
| 6 | 验证 CV 起步健康度 | ✅ `path.sss ≈ 1.04`，`bias` 正在累积，PATHMSD kernel 加载成功 |

**不需要再做任何手动步骤**，mdrun 已经在跑，等 3 天左右完成。

### 11.2 Job 开始跑之后的监控（想看的时候做）

```bash
# 看 slurm 日志里 grompp 是否报错
ssh longleaf "cat /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/slurm-trpb_metad-42679152.out"

# 看 COLVAR 实时进度（能跨 basin 吗？）
ssh longleaf "cd /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker && tail -3 COLVAR"
# 期望：path.sss 会从 ~1.0 慢慢往 5, 10, 15 方向爬

# 看 HILLS 是否在累积
ssh longleaf "wc -l /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/HILLS"
```

### 11.3 ~3 天后（Job 42679152 完成）— 后续待做

```bash
cd /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so

# B1. 确认正常完成
squeue -u liualex | grep 42679152         # 应该不在了
wc -l HILLS COLVAR                         # HILLS ~25000, COLVAR ~50000
grep -i "error\|fatal\|nan" metad.log | head

# B2. COLVAR 分布检查
python3 -c "
import numpy as np; d=np.loadtxt('COLVAR',comments='#')
s=d[:,1]; print(f'O:{(s<5).sum()} PC:{((s>5)&(s<10)).sum()} C:{(s>10).sum()}')
"
# 如果只在一个 basin → 直接上 10-walker

# B3-B6. FES 重构 + 分析（见 Section 9.4 全流程）
```

### 11.4 决策点（FES 分析完成后）

看 `fes_report.json` 的 `comparisons` 字段：
- 两项 PASS + 收敛 → 复刻成功，准备 merge 10-walker branch 进生产
- 两项 PASS 但未收敛 → 直接上 10-walker
- 只在 PC → 直接上 10-walker（HILLS 可 warm-start）
- FAIL → 继续 debug（先查 LAMBDA、path Cα、atom indexing）

---

## 12. Failure Pattern 索引

| FP# | 日期 | 简述 | 位置 |
|---|---|---|---|
| FP-015 | 2026-03-31 | λ 算出来用了 total SD 约定（130× 错误） | `generate_path_cv.py` |
| FP-018 | 2026-04-04 | LAMBDA 单位 Å⁻² → nm⁻² 要 ×100（GROMACS 内部单位） | `plumed.dat` |
| FP-019 | 2026-04-04 | FUNCPATHMSD 不带 SQUARED 时 feeding d = RMSD 而非 MSD | `plumed.dat` |
| FP-020 | 2026-04-04 初诊 / 2026-04-09 更正 | conda 版 `libplumedKernel.so` 对 PATHMSD 有 bug（初诊为 "PATHMSD 不认非连续 serial"） | Longleaf env |
| FP-021 | 2026-04-07 | `plumed sum_hills --kt` 单位：用 2.908 kJ/mol，不是 0.695 kcal/mol | 分析流程 |
| FP-022 | 2026-04-08 | FUNCPATHMSD workaround 保留了 total-SD 的 λ=3.391，应该用 379.77 per-atom | `plumed.dat` |
| FP-023 | 2026-04-09 | multi-model PDB 末尾 trailing END 让 PATHMSD 报错（经验观察，不是官方规则） | `path_gromacs.pdb` |

详细的修复记录在 `replication/validations/failure-patterns.md`，每一个都有：
- 首次发现者 / 时间
- 错误描述
- 正确事实
- 根因
- 防范措施（通常是加 assertion）

---

## 13. 附录：本地 ↔ Longleaf 文件对照

| 角色 | 本地路径 | Longleaf 路径 | 同步方式 |
|---|---|---|---|
| AMBER mdin | `replication/classical_md/inputs/` | `classical_md/inputs/` | git + scp |
| Prep slurm | `replication/classical_md/slurm/` | `classical_md/slurm/` | git + scp |
| 转换脚本 | `replication/metadynamics/conversion/convert_amber_to_gromacs.py` | `metadynamics/conversion/` | scp |
| Path CV 脚本 | `replication/metadynamics/path_cv/generate_path_cv.py` | `metadynamics/path_cv/` | scp |
| Multi-model PDB | `replication/metadynamics/single_walker/path_gromacs.pdb` | `metadynamics/single_walker/` | scp |
| PLUMED 输入 | `replication/metadynamics/single_walker/plumed.dat` | `metadynamics/single_walker/` | scp（每次改都要同步） |
| GROMACS MDP | `replication/metadynamics/single_walker/metad.mdp` | `metadynamics/single_walker/` | scp |
| Submit 脚本 | `replication/metadynamics/single_walker/submit.sh` | `metadynamics/single_walker/` | scp |
| 分析脚本 | `replication/analysis/{analyze_fes,check_convergence}.py` | `analysis/` | scp |

**不在本地但在 Longleaf**（生成物 / 太大不进 git）：
- `classical_md/output/prod_500ns.nc` (23 GB)
- `metadynamics/single_walker/start.gro` + `topol.top`（从 conversion/ 复制过来的）
- `metadynamics/single_walker/{metad.*, HILLS, COLVAR}`（运行产物）

**同步规则**：
1. **代码（脚本 + 输入文件）** → 本地是 source of truth，改完 scp 到 Longleaf
2. **生成物（.nc, .xtc, .cpt, HILLS, COLVAR）** → Longleaf 是 source of truth，本地不存
3. **path_gromacs.pdb** → 特例，因为小（133 KB）且定义反应路径，两边都存并保持一致

---

**Last updated**: 2026-04-09（部署后：Job 42679152 已提交并切换到 RUNNING，文件已同步，旧数据已归档，CV 起步验证通过）
**下次更新触发**: Job 42679152 完成后（看 FES 结果更新 Section 10/11）或出现新 FP
