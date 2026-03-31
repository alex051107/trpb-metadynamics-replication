# ACS Catal 2021 Reading Notes
> Maria-Solano et al., ACS Catal 2021, 11(21), 13733-13743
> DOI: 10.1021/acscatal.1c03950 | Zotero key: 57U7HRRN

## 这篇讲了什么（3 句话）

JACS 2019 证明了 SPM 能从 PfTrpS 的 MetaDynamics 轨迹里找到影响 COMM domain 动力学的关键位点。这篇把 SPM 和祖先序列重建（ASR）结合，在一个更古老的 TrpB 体系（LBCA → ANC3）上直接预测增强 stand-alone 活性的远端突变，然后用实验验证了。核心结论：SPM 从动力学信息出发，能设计出和多轮定向进化相当的活性提升——这正是"动力学 → 序列设计"这条路可行的直接证据。

## 关键方法和数字

**体系：**
- LBCA TrpB: Last Bacterial Common Ancestor TrpB，天然有一定 stand-alone 活性
- ANC3 TrpB: 更晚的祖先节点，已经依赖 TrpA 别构激活（活性低）
- 目标：用 SPM 预测突变，把 ANC3 TrpB 从低活性恢复到 stand-alone

**SPM + ASR 组合策略：**
1. 对 LBCA TrpB 做 MetaDynamics → 重建 COMM domain O-to-C FEL
2. 对 LBCA TrpB MetaDynamics 轨迹做 SPM → 识别 68/413 残基（18%）为动力学热点
3. 对比 LBCA 和 ANC3 序列 → 在 SPM 热点位置上找氨基酸差异
4. 得到 6 个突变：A56E, D62E, S73T, T207S, N299A, R300M
5. 命名 SPM6 TrpB = ANC3 + 这 6 个突变

**关键结果：**
- 6 个突变都不在 COMM domain 内
- 5/6 远离活性位点（18-29 Å），只有 S73T 在活性位点附近
- N299A 和 R300M 靠近 TrpA-TrpB 界面
- 实验验证：SPM6 TrpB stand-alone 活性显著提升，可比多轮 DE 的效果

**LBCA TrpB 构象动力学：**
- LBCA TrpB(Ain): 主要访问 PC 状态（和 PfTrpB 不同——PfTrpB 的 Ain 主要是 O）
- LBCA TrpB(Q2): 能访问 productive C 状态，H6 helix 正确关闭
- 有一个 deviated C* 状态（类似 PfTrpB 的 unproductive closure）
- TrpA 的存在反而把 LBCA TrpB 推向 PC，阻碍 productive C → 这是 ANC3 活性低的原因

## 对我的项目意味着什么

1. **验证了"MetaDynamics → 序列设计"这条路径。** JACS 2019 只是观察到 SPM 能回溯性解释 DE 结果；这篇是前瞻性的——先预测再验证。对我们的 pipeline 来说，这证明了动力学信息确实能指导序列选择。

2. **SPM 的具体局限性。** SPM 识别了 68 个位点（18% 的序列），需要和 ASR 组合才能缩减到 6 个可操作的突变。单独的 SPM 信息密度太低，不能直接当 filter 用——需要叠加序列层面的约束。

3. **不同物种/祖先的 TrpB 有不同的构象基态。** LBCA 的 Ain 是 PC 而不是 O（PfTrpB 是 O）。这意味着如果我要把 JACS 2019 的 path CV 直接搬到 GenSLM-230 上，参考路径可能需要调整——不能假设所有 TrpB 的构象基态相同。

4. **对 GenSLM-230 vs NdTrpB 的启示。** GenSLM-230 和 NdTrpB backbone RMSD 只有 0.36 Å，但活性不同。这篇论文表明，静态结构几乎一样的序列可以有完全不同的构象动力学。这正是我们要用 MetaDynamics 去解释的。

## 还不确定的地方

- 具体的 MetaDynamics 参数在 SI，还没看到（和 JACS 2019 一样的问题）
- LBCA 和 PfTrpB 的 MetaDynamics 是否用完全相同的 path CV 参考结构？论文提到"reference O-to-C path generated from X-ray structures"但没说是不是同一条路径
- SPM 的 correlation 计算具体用的是什么矩阵（互相关？动态网络？）——原方法在 2017 ACS Catal 论文里
- 68 个 SPM 热点是怎么确定阈值的（前 18%？还是有统计判据？）

## 复刻优先级

这篇 **不是** 复刻的第一优先级。JACS 2019 才是（因为它有完整的 PfTrpB 体系和 benchmark 数据）。但这篇提供了关键的方法论延伸：

- 如果 benchmark 成功了，SPM + ASR 的组合策略可以直接应用到 GenSLM-230 的分析上
- 具体来说：对 GenSLM-230 做 MetaDynamics → SPM → 和 NdTrpB 做序列层面的对比 → 找到决定活性差异的残基

## Zotero 里的状态
- PDF: ✅ 有（key: N6IQVNFX）
- SI: ❓ 需要确认
- 深度标注 HTML: ✅ 有（papers/annotations/ACSCatal2021_DeepAnnotation.html）
