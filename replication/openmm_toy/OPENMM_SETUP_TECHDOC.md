# OpenMM + PLUMED Toy Setup — Technical Documentation

**日期**: 2026-04-18
**目标**: 在 Longleaf 上验证 (1) OpenMM 能跑 cMD（CUDA）、(2) PLUMED 能作为
plugin 插入 OpenMM 跑 MetaD（因为 OpenMM 原生 metadynamics 不支持 path CV）。
**Env**: `/work/users/l/i/liualex/conda/envs/md_setup_trpb`

---

## 1. Why this matters

组会（2026-04-17）上 Yu 明确提醒：OpenMM 自带的 `openmm.app.metadynamics`
只支持 1-3 个**人工定义**的 CV，不支持 PATHMSD。TrpB 复刻依赖 15-frame
open→closed PATHMSD，所以必须走 **openmm + openmm-plumed plugin** 这条路，
plumed.dat 语法和我们现在 GROMACS+PLUMED2 版本完全一致 → 现有 plumed.dat 可以
直接复用。

这份文档记录从 0 开始把这条链路跑通的每一步、踩到的坑、以及为什么这样改。

---

## 2. 环境构建（改动清单）

### 2.1 基础 env（前序会话已完成）

Yu 给的 `md_setup`（hengma1001/md_setup）原始 `environment.yml` 针对 x86_64
Linux + CUDA 11.x。我按 Longleaf（RHEL9 + CUDA 12.2）做了以下改动，产出
`/work/users/l/i/liualex/AnimaLab/tools/md_setup/LONGLEAF_SETUP.md` 记录：

| 上游 | Longleaf 版 | 原因 |
|------|------------|------|
| `gromacs 4.6.5` | **去掉** | 我们 MetaD 用另外的 GROMACS+PLUMED 2.9.2 env，不需要重复装；且 4.6.5 和 cuda 12 不兼容 |
| `cudatoolkit 11.x` | `cudatoolkit 12.2` | 匹配 Longleaf `cuda/12.2` module |
| `ambertools 22` | `ambertools 23.3` | 22 在 py310 上 wheel 缺失 |
| `openmm 7.7` | `openmm 8.2` → 后升 8.4 | 装 openmm-plumed 时 mamba 自动升到 8.4 |
| `pdb4amber` 显式 pin | 去掉（走 ambertools 传递依赖） | 独立 pin 和 ambertools 23 冲突 |
| 所有版本 `==` | 改成 `>=` 宽 pin | solver 太严容易死锁 |

### 2.2 本次会话新加：openmm-plumed plugin

**命令**:
```bash
mamba install -n md_setup_trpb -c conda-forge openmm-plumed -y
```

**解决后 env 新增的包**:
- `openmm 8.2 → 8.4.0`（mamba 自动 upgrade，因为 openmm-plumed 2.1 要 ≥8.3）
- `plumed 2.9.2` (conda-forge 版，独立于 `trpb-md` env 里那份)
- `openmm-plumed 2.1`
- CUDA runtime libs (libcufft, nvrtc) 补齐到 12.2-13.2 系列

**验证**:
```python
from openmmplumed import PlumedForce
# → /work/users/l/i/liualex/conda/envs/md_setup_trpb/lib/python3.10/site-packages/openmmplumed.py
```

### 2.3 关键 env 分层（避免搞混）

| Env 路径 | 用途 | MetaD 引擎 |
|---------|------|-----------|
| `/work/.../envs/trpb-md` | 生产 MetaD 正在跑 Job 44008381 | GROMACS 2026 + PLUMED 2.9 |
| `/work/.../envs/md_setup_trpb` | OpenMM cMD 前端 + openmm-plumed MetaD 测试 | OpenMM 8.4 + PLUMED 2.9 (plugin) |

两条 PLUMED 是**独立的二进制**，plumed.dat 语法兼容。

---

## 3. Toy Project 代码

### 3.1 体系

Alanine dipeptide (Ace-Ala-Nme)，22 原子，vacuum 或 TIP3P box。
phi = atoms 5-7-9-15，psi = atoms 7-9-15-17（手工构造 PDB，坐标来自标准 α-螺旋
起始点）。

### 3.2 Toy 1 — 纯 OpenMM cMD (`toy_cmd.py`)

关键设定（对齐 TrpB campaign）：
- ff14SB + TIP3P（组会 parameter）
- 350 K, Langevin middle integrator, 2 fs, HBonds 约束
- MonteCarloBarostat 1 atm
- PME, 1.0 nm cutoff
- CUDA platform, mixed precision
- 25,000 步 = 50 ps

**输出**: DCD + 最终 PDB + 打印 `NS_PER_DAY`。
Pass 条件：无 NaN、`TOY_CMD_OK` 行出现、`NS_PER_DAY > 20`（A100 上的下限）。

### 3.3 Toy 2 — OpenMM + PLUMED MetaD (`toy_metad.py`)

```python
from openmmplumed import PlumedForce

PLUMED_SCRIPT = """
phi: TORSION ATOMS=5,7,9,15
psi: TORSION ATOMS=7,9,15,17
METAD ...
    ARG=phi,psi
    PACE=500        # 每 1 ps 放一个 hill
    HEIGHT=1.2      # kJ/mol
    SIGMA=0.35,0.35
    BIASFACTOR=10
    TEMP=350
    FILE=HILLS
    LABEL=metad
... METAD
PRINT ARG=phi,psi,metad.bias FILE=COLVAR STRIDE=500
"""

system.addForce(PlumedForce(PLUMED_SCRIPT))
```

Pass 条件：HILLS 行数 > 0、COLVAR 有 bias 列、无 NaN、`TOY_METAD_OK` 出现。

**为什么这个 toy 能证明 TrpB 链路可行**：`PlumedForce(script)` 接收的字符串和
我们 TrpB 生产的 `plumed.dat` **完全同语法**。如果 phi/psi 的 METAD 能跑通，把
脚本换成 PATHMSD s(R)/z(R) 只需改 `ARG=p.sss,p.zzz` 和 atom 列表——不需要动
Python 代码。

---

## 4. 踩过的坑 & 修法

### 坑 1 — Longleaf QoS 拒绝

**症状**: 第一次 sbatch → `Invalid qos specification`。
**根因**: `a100-gpu` 分区要求 `gpu_access` QoS，默认不带。
**修**: sbatch script 加 `#SBATCH --qos=gpu_access`。确认命令：
```bash
sacctmgr show assoc user=liualex format=account,qos
```
→ `normal,gpu_access`，有权限，只是没显式声明。

### 坑 2 — `set -u` + `/etc/bashrc` 冲突（Job 44295391 失败）

**症状**: job 1 秒 fail，stderr = `/etc/bashrc: line 12: BASHRCSOURCED: unbound variable`。
**根因**: sbatch 脚本开头 `set -euo pipefail`，然后 `source ~/.bashrc` 链到
`/etc/bashrc`，那里引用了未定义的 `BASHRCSOURCED` → `-u`（nounset）触发。
**修**: 两步都可以，选了第二个：
1. 去掉 `-u` → `set -eo pipefail`
2. 不再 `source ~/.bashrc`，改成直接 source conda 的 profile：
   ```bash
   source /nas/longleaf/rhel9/apps/anaconda/2024.02/etc/profile.d/conda.sh
   conda activate md_setup_trpb
   ```
   这条路径跳过用户 bashrc，不会碰到 BASHRCSOURCED。

**教训**: Longleaf 的 system-level bashrc 和 `set -u` 天然不兼容；cMD 相关
sbatch 脚本都不要用 `-u`。

### 坑 3 — NumPy 2.x ABI 警告（已知，非致命）

**症状**: OpenMM import 时 stderr 出现 numpy 2.x 兼容警告。
**状态**: 不致命，smoke test 仍输出 OK。生产体系变大后如果遇到 NaN，再考虑
`conda install 'numpy<2'`。现在先挂着。

### 坑 4 — OpenMM 8.2 → 8.4 静默升级

**症状**: 装 openmm-plumed 后 `openmm.__version__ = 8.4`，而 `LONGLEAF_SETUP.md`
写的是 8.2。
**根因**: openmm-plumed 2.1 在 conda-forge 上的 run-constraint 是 `openmm >=8.3`。
**影响**: 8.4 对我们用的 API（LangevinMiddleIntegrator, PME, MonteCarloBarostat）
向后兼容。已在本 doc 2.2 节标出真实版本号。

### 坑 5 — CUDA_ERROR_UNSUPPORTED_PTX_VERSION（toy 连跑 3 次 fail）

**症状**: `Platform.getPlatformByName("CUDA")` → `Context` 初始化时
`CUDA_ERROR_UNSUPPORTED_PTX_VERSION (222)`。试过 `cuda/12.2` 和 `cuda/13.0`
module，都不行。
**根因**: openmm-plumed 2.1 联动把 openmm 升到 8.4 + 拉了
`cuda-nvrtc 13.2.78`。OpenMM 8.4 conda-forge build 的 PTX 针对 CUDA 13.2+
driver，而 Longleaf A100 节点驱动最高只到 `cuda/13.0` module 对应版本 →
driver 不认 PTX。
**绕**: 改用 `OPENMM_PLATFORM=CPU` 环境变量，让 toy 在 general 分区的 CPU 上
跑；22 原子真空 NVT，CPU 也有 69 ns/day，足够验证。
**生产修**（待办）: 把 openmm 钉到 CUDA 12 build：
```bash
mamba install -n md_setup_trpb \
  'openmm=8.2.*=*cuda12*' 'openmm-plumed=*=*cuda12*' \
  'cudatoolkit>=12,<13'
```
或者等 Longleaf 把 A100 节点驱动升到支持 CUDA 13.2。Toy 证明链路逻辑通就够，
TrpB 40k 原子生产再处理 CUDA。

### 坑 6 — 溶剂化 + 小 box + barostat 崩

**症状**: OpenMM step 10 时 `The periodic box size has decreased to less than
twice the nonbonded cutoff`。
**根因**: 22 原子丙氨酸二肽 + 1 nm padding TIP3P + MonteCarloBarostat(1 atm,
350 K)，初始 box 太小，barostat 一缩就 < 2×cutoff。
**修**: toy 简化为 vacuum + NVT + `NoCutoff`（`toy_cmd.py` 当前版本）。真正的
TrpB 体系 39,268 原子 + 大 box，没这个问题；生产 md_setup 也有合理 padding。
Toy 只是证明 OpenMM+ff14SB+积分器工作。

---

## 5. 验证结果（Job 44296608 — COMPLETED 00:02:10）

```
=== ENV ===
openmm 8.4
openmm-plumed OK

=== Toy cMD (vacuum, NVT) ===
atoms = 22
platform = CPU
NS_PER_DAY = 69.2
TOY_CMD_OK

=== Toy MetaD (OpenMM + PLUMED plugin) ===
atoms = 22
platform = CPU
forces = ['HarmonicBondForce', 'PeriodicTorsionForce', 'NonbondedForce',
          'CMMotionRemover', 'HarmonicAngleForce', 'Force']  # <- PlumedForce
HILLS rows = 50 (one every 1 ps, PACE=500 steps × 2 fs)
NS_PER_DAY = 69.2
TOY_METAD_OK
```

**PLUMED banner 确认生效**：
- Action TORSION phi between atoms 5,7,9,15 ✓
- Action TORSION psi between atoms 7,9,15,17 ✓
- Action METAD: Gaussian width 0.35/0.35, height 1.2 kJ/mol, pace 500,
  bias factor 10, tau = 21.8 ps, KbT = 2.910 kJ/mol (350 K ✓) ✓
- Action PRINT: phi, psi, metad.bias → COLVAR every 500 steps ✓

**Artifacts** (`/work/users/l/i/liualex/AnimaLab/openmm_toy/`):
- `run_cmd/`: `toy_cmd.dcd`, `toy_cmd_final.pdb`
- `run_metad/`: `HILLS` (50 Gaussians), `COLVAR`, `toy_metad.dcd`

**结论**: OpenMM 能跑 ff14SB 体系；openmm-plumed plugin 接收和我们 TrpB
生产 plumed.dat 完全同语法的 PLUMED 脚本；HILLS/COLVAR 正常写出。OpenMM cMD
+ PLUMED MetaD 的链路在 Longleaf 的 `md_setup_trpb` env 里**在 CPU 上已验证
可用**。GPU 部分被 CUDA 版本问题卡住（见坑 5），不影响正确性证明。

---

## 6. 下一步往 TrpB 接

Toy 两个都绿 → 做两件事：

1. **cMD 接 md_setup**: `md_setup` 提供 PDB → OpenMM system 的自动构建链。
   给它 4HPX (pre-closed seed) 或 5DVZ 作为 PDB 输入，让它吐出
   `system.xml + integrator.xml + state.xml`，跑 100 ns cMD 做 Phase 3
   的种结构。

2. **MetaD 脚本化**: 把 TrpB 现有 `replication/metadynamics/single_walker/plumed.dat`
   原样传给 `PlumedForce(open('plumed.dat').read())`，system 换成 TrpB
   的 40k 原子 box → 跑一个 2 ns 短跑验证 path CV 在 openmm+plumed 下数值
   和 GROMACS+plumed 一致（diff COLVAR 第一列）。

只有**两者都对得齐**才能替换 GROMACS stack。否则 GROMACS 线继续跑，OpenMM
只做前处理和 Phase 3。

---

## 7. 文件清单

| 文件 | 位置 | 作用 |
|------|------|------|
| `toy_cmd.py` | `replication/openmm_toy/` | Toy 1 源码 |
| `toy_metad.py` | 同上 | Toy 2 源码 |
| `alanine_dipeptide.pdb` | 同上 | 22-atom 初始坐标 |
| `submit_toy.sbatch` | 同上 | Slurm 提交脚本 |
| `OPENMM_SETUP_TECHDOC.md` | 同上 | 本文件 |
| `LONGLEAF_SETUP.md` | `/work/.../tools/md_setup/` | env 改动记录（Longleaf 远端） |
