# Technical Reasoning Log — 原理思考记录

> **这个文件和 CHANGELOG 平行，但侧重"为什么"而不是"做了什么"。**
> 每个条目必须包含 6 个部分。如果你填不出某一项，说明你还没真正理解。
> AI agent 写的条目，人类必须读并标注 `[REVIEWED]` 或 `[QUESTION: ...]`。

---

## TR-001: 为什么 PLP 总电荷是 -2？

**做了什么**：确定 Ain 中间体（LLP 残基）的 RESP 计算总电荷为 -2。

**为什么这样做**：
Gaussian 做 RESP 电荷拟合时必须指定分子的总电荷和自旋多重度。电荷填错，算出来的每个原子的部分电荷就全部错误，后面的 MD 模拟从物理上就不成立。

PLP 的总电荷取决于 4 个可电离基团在酶活性位点内的质子化状态。这不是一个可以从 pKa 表简单查到的问题，因为：
- 酶活性位点的微环境 pH ≠ 溶液 pH
- 周围氨基酸的静电场会移动 pKa（所谓 pKa perturbation）
- PLP 的 4 个基团之间存在 intramolecular hydrogen bonding，互相影响

**它靠什么成立**：
不是靠计算推导，而是靠**实验测量**。

Caulkins et al. (JACS 2014, 136, 12824, DOI: 10.1021/ja506267d) 用**固态核磁共振 (ssNMR)** 直接测量了 TrpS 酶中 Ain 中间体的质子化态：

| 基团 | NMR 证据 | 质子化状态 | 电荷贡献 |
|------|----------|-----------|---------|
| Schiff base N (NZ) | ¹⁵N δ = 202.3 ppm（质子化 Schiff base 特征位移） | 带 H → NH⁺ | +1 |
| Pyridine N1 | ¹⁵N δ = 294.7 ppm（去质子化吡啶特征） | 不带 H | 0 |
| Phosphate | ³¹P 化学位移（dianionic 特征） | HPO₄²⁻ | -2 |
| Phenolate O3 | ¹³C shifts on C2, C3（去质子化酚 oxygen 特征） | O⁻ | -1 |

总计：+1 + 0 + (-2) + (-1) = **-2**

交叉验证：Huang et al. (Prot. Sci. 2016, 25, 166, PMID: 26013176) 用 MD 模拟测试了 17 种不同的质子化方案，NMR-consistent 的方案给出了与实验最一致的结构动力学。

**有没有更好的方法**：
- **QM/MM pKa 计算**：可以在不同 protonation states 下计算自由能，理论上更 rigorous。但计算量大，且依赖 QM 方法和 basis set 的选择。对于 TrpS，已有 NMR 实验数据，不需要从头计算。
- **PropKa / H++**：基于经验公式的 pKa 预测工具。速度快但精度低，对 PLP 这种非标准配体可能不可靠。
- **直接用 charge=-1 或 charge=0**：如果 phenolate O3 质子化（OH 而非 O⁻），charge 变为 -1。但 NMR 数据明确排除了这种可能（C2/C3 化学位移不符合质子化形式）。

**最可能错在哪**：
1. **pH 依赖**：Caulkins 的 NMR 实验是在特定 pH 下做的。如果模拟的 pH 条件与实验显著不同，质子化态可能变化。但 Osuna 的模拟没有改 pH（用的 standard TIP3P water），所以和 NMR 条件兼容。
2. **不同中间体不同**：charge=-2 只对 Ain 成立。Aex1 多了 serine，A-A 脱水，Q2 加了 indole——它们各自的 charge 不同，需要独立确定。
3. **动态质子化**：实际上质子可能在不同基团间跳跃（tautomerism）。Classical MD 不能模拟质子转移，用的是固定 charge。这是所有 classical MD 的根本限制。

**如果错了会怎样**：
如果 charge 错（比如用了 -1），RESP 拟合出的每个原子的部分电荷会系统性地偏移。影响链条：
- 原子电荷错 → 静电相互作用错 → 蛋白质-PLP 结合模式错 → COMM domain 构象动力学错 → FEL 形状错 → 所有科学结论不可靠
- 这是**不可通过后处理修复**的根本错误。必须从头跑。

---

## TR-002: 为什么必须加 ACE/NME capping？

**做了什么**：在 LLP 残基的 N 端加 ACE cap，C 端加 NME cap，然后再做 RESP 计算。

**为什么这样做**：
LLP（PLP-K82 Schiff base）在蛋白质中不是一个独立的分子。它通过两个**肽键 (peptide bonds)** 连接到前后的氨基酸：
- N 端 → HIS81 的 C=O（通过 HIS81-C—LLP82-N 肽键）
- C 端 → THR83 的 NH（通过 LLP82-C—THR83-N 肽键）

从 PDB 提取 LLP 时，这两个肽键被"剪断"了。剪断的位置暴露了不饱和的 N 和 C=O 原子，它们的电子分布是不物理的——在真实蛋白质中，这些原子参与肽键共振 (resonance)，电荷是被"分摊"的。

如果直接在这个断裂的片段上做 RESP，Gaussian 会把断口处理成真空中的自由端，算出来的电荷会反映这个不物理的边界——特别是 backbone N 和 C=O 处的电荷会严重失真。

ACE cap (CH₃-CO-) 模拟前一个残基的 C=O 端；NME cap (-NH-CH₃) 模拟后一个残基的 NH 端。加上它们后，肽键共振得以恢复，边界电荷变得物理合理。

RESP 拟合完成后，cap 原子的电荷会被丢弃——只保留 LLP 本身原子的电荷。最终在 tleap 中，LLP 作为一个自定义残基嵌入蛋白质链，它的 head 和 tail 连接到前后残基。

**它靠什么成立**：
- AMBER Advanced Tutorial §1 (https://ambermd.org/tutorials/advanced/tutorial1/section1.php)：明确说明 non-standard residue 的 RESP 计算需要 cap
- Bayly et al. (J. Phys. Chem. 1993, 97, 10269)：RESP 方法原始论文，讨论了分子边界对静电势的影响
- Codex 分析 (`replication/validations/2026-03-30_capping_analysis.md`)：从 5DVZ PDB 的 LINK 记录确认了 LLP 的 polymer-linked 性质

**有没有更好的方法**：
- **更大的 cap**：不只加 ACE/NME，而是保留 HIS81 和 THR83 的完整侧链。更准确但更贵，且增加了需要约束的原子数量。对于 RESP（只看静电势），ACE/NME 通常够用。
- **不用 cap，用 ONIOM/QM-MM**：在 QM 区域只放 LLP，MM 区域放蛋白质环境。理论上更 rigorous，但实现复杂且 Osuna 没有这样做。
- **不用 cap，直接拟合**：对于真正的自由配体（如药物小分子），这是合法的。但 LLP 不是自由配体——它共价连在蛋白质上。

**最可能错在哪**：
1. **Cap 的几何影响**：ACE/NME 的初始几何取自 HIS81/THR83 的晶体坐标。如果晶体结构在该区域有 disorder，cap 几何可能不理想。但 Gaussian 会做 geometry optimization，所以初始几何影响较小。
2. **Cap 电荷约束**：标准做法是将 ACE/NME 原子的电荷约束为 ff14SB 的标准值。如果 Codex 的脚本没有做这个约束（在 RESP 两阶段拟合中设置 IQOPT），cap 电荷可能"吸走"部分 LLP 的电荷。需要在 antechamber 步骤中检查。

**如果错了会怎样**：
如果不加 cap，backbone N 和 C=O 处的 RESP 电荷会偏离 ff14SB 的标准值。当 LLP 嵌入蛋白质链时，这些位置的电荷会和邻居残基不匹配，导致：
- 局部静电排斥/吸引异常
- K82-PLP Schiff base 区域的结构扭曲
- 可能影响 COMM domain 闭合的能垒 → FEL 形状变化

---

## TR-003: 为什么 Gaussian 报 "229 electrons" 错误？

**做了什么**：Gaussian job 40364008 失败。诊断原因并修复。

**为什么会出错**：
量子化学的基本规则：

**电子数 = 原子序数之和 - 净电荷**

| | 未加帽 (42 atoms) | 加帽 (55 atoms) |
|---|---|---|
| H | 18 × 1 = 18 | 26 × 1 = 26 |
| C | 14 × 6 = 84 | 17 × 6 = 102 |
| N | 3 × 7 = 21 | 4 × 7 = 28 |
| O | 6 × 8 = 48 | 7 × 8 = 56 |
| P | 1 × 15 = 15 | 1 × 15 = 15 |
| **Z_total** | **186 (偶数)** | **227 (奇数)** |
| charge = -2 | electrons = 188 (偶) ✅ | electrons = 229 (奇) ❌ |

**Singlet (multiplicity=1) 要求偶数电子**（所有电子配对）。229 是奇数 → 不可能是 singlet。

Cap 应该增加 ΔZ = 40 (偶数)：
- ACE: 2C+3H+1O = 12+3+8 = 23
- NME: 1N+1C+4H = 7+6+4 = 17
- 23 + 17 = 40 (偶数)

但实际增加了 41 → **脚本多加了 1 个 H**。

**它靠什么成立**：
这是量子力学的基础——Pauli exclusion principle 要求 singlet state 的电子总数为偶数。不是近似，是数学定理。

**有没有更好的方法**：
防止此类错误的正确做法：在生成 Gaussian 输入后、提交前，加一个自动 assertion：
```python
assert (Z_total - charge) % 2 == 0, f"Odd electron count: Z={Z_total}, charge={charge}"
```
这个检查应该加入 `build_llp_ain_capped_resp.py`。

**最可能错在哪**：
Codex 的脚本可能在以下位置多加了 H：
1. backbone N 上：提取时 reduce 给了 terminal NH₃⁺ (3H)，capping 后应该只保留 1H (peptide NH)
2. ACE methyl 上：不小心加了 4H 而不是 3H
3. NME methyl 上：同上

**如果错了会怎样**：
纯工程 bug，不涉及科学判断。但暴露了一个重要教训：
**自动生成的分子结构必须做数值校验**（原子数、电子数、键连接性）。这和 FP-003（不要凭记忆写 PDB）、FP-010（antechamber 需要 H）是同一类问题。

---

## TR-004: Path CV 的 λ 参数为什么是 2.3/MSD？

**做了什么**：按照 JACS 2019 SI 的描述，计算 λ = 2.3 × (1/MSD) ≈ 0.029。

**为什么这样做**：
Path CV 定义了一条从 Open (s=1) 到 Closed (s=15) 的参考路径。两个 CV：
- **s(R)**: 当前构象在路径上的位置（progress）
- **z(R)**: 当前构象到最近路径点的距离（deviation）

数学上：
```
s(R) = Σᵢ i × exp(-λ × |R - Rᵢ|²) / Σᵢ exp(-λ × |R - Rᵢ|²)
z(R) = -(1/λ) × ln(Σᵢ exp(-λ × |R - Rᵢ|²))
```

λ 是一个分辨率参数：
- **λ 太大**：只有最近的参考帧有贡献，s(R) 变成阶梯函数，MetaD bias 不平滑
- **λ 太小**：多个参考帧同时有贡献，不同位置的 s 值重叠，失去分辨率
- **最优**：λ ≈ 2.3 / MSD，使得相邻帧的 exp(-λ × MSD) ≈ exp(-2.3) ≈ 0.1，即相邻帧的贡献衰减到 10%

**它靠什么成立**：
- Branduardi et al. (J. Chem. Phys. 2007, 126, 054103)：Path CV 原始论文，推导了 λ 的最优范围
- JACS 2019 SI p.S3："The λ parameter was computed as 2.3 multiplied by the inverse of the mean square displacement between successive frames, 80."
- MSD = 80 Å² 是从 1WDW→3CEP 的 Cα 线性插值得到的帧间平均均方位移

**有没有更好的方法**：
- **λ = 1/MSD**：更保守，各帧贡献更均匀，但 s(R) 的分辨率降低。Branduardi 推荐 λ ∈ [1/MSD, 3/MSD]
- **自适应 λ**：根据局部 MSD 调整。更复杂，Osuna 没用
- **不用 Path CV，用 RMSD 做 CV**：更简单但不能区分 O/PC/C 三个状态——因为 RMSD 只给一个距离，不给路径上的位置。Path CV 的优势正是在于它能定义一条"轨道"
- **不用线性插值，用 targeted MD 生成路径**：可能更物理，但计算量大。线性插值对于 backbone Cα 足够好（骨架运动近似线性）

**最可能错在哪**：
1. **线性插值假设**：O→C 转变可能不是沿直线发生的。如果中间经过一个"弯曲"的路径（比如先向上再向右），线性插值会"抄近路"，导致中间帧不物理。但对于 backbone Cα 的缓慢构象变化，线性近似通常合理。
2. **参考结构来自不同物种**：1WDW 是 P. furiosus，3CEP 是 S. typhimurium。Osuna 在 SI 中说做了结构比对，但两个物种的 Closed 态可能有微小差异。
3. **15 帧是否足够**：帧数太少 → MSD 大 → λ 小 → 分辨率低。帧数太多 → MSD 小 → λ 大 → MetaD bias 不平滑。15 帧是 Osuna 的选择，可能是经验值。

**如果错了会怎样**：
如果 λ 不合适：
- 偏大：MetaD 的 Gaussian bias 只影响局部帧，能量面上出现锯齿状伪影
- 偏小：不同构象状态在 s(R) 上重叠，无法区分 O/PC/C → 整个分析框架失效
- 但由于 λ 的影响是连续的，±20% 的偏差通常不会导致定性错误
