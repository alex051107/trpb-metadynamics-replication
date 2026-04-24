# 组会速查卡 (2026-04-24)

> 上场前 5 分钟瞄一眼。站稳、不 overclaim、承认 limitation。

---

## 1 句话总结本周（开场第一句）

**"这周发现真正卡住项目的不是 MetaD 参数，是 path 定义本身的一个跨物种 residue mapping bug (FP-034)。修完之后 pilot 在 sim 6 ns 时 transient cross s=12 gate，端到端通路 confirm。10-walker primary production 正在启动。"**

**更新时间 2026-04-24 06:17**: GATE CLEARED — pilot 45515869 @ t=6085 ps, max_s=12.867（single transient ~120 ps, fraction(s>12)=0.05%, 未 sustained）。

---

## 核心数字（背下来）

| 量 | 数值 | 来源 |
|---|---|---|
| Bug 性质 | 跨物种 residue mapping，1WDW(Pf)/3CEP(St) 偏差 +5 | FP-034, summary.txt |
| Sequence identity 修正 | 6.2% → **59.0%** | VERIFICATION_REPORT |
| O↔C RMSD 修正 | 10.89 Å → **2.115 Å** | VERIFICATION_REPORT |
| ⟨MSD_adj⟩ | 0.606 → **0.0228 Å²** | summary.txt |
| Branduardi λ | 3.80 → **100.79 Å⁻²** | summary.txt |
| Miguel 邮件 λ=80 | 比值 **1.26×** = 自洽 | summary.txt L54 |
| Pilot max_s 当前 | **12.867 @ 6085 ps**（GATE CLEARED, transient ~120 ps）| Longleaf 45515869 |
| Pilot plateau 段 | 437 ps → 6085 ps = 4.3 ns at max_s=10.92 | COLVAR |
| fraction(s > 12) | 0.05%（单次 transient, 未 sustained）| COLVAR full scan |
| 老 path 对照 max_s | 1.75 @ 7.7 ns | 45324928 |
| PC 独立 projection | 5DW0→s=9.46, 5DW3→s=8.51, 5DVZ→s=5.37, 4HPX→s=14.90 | Codex VERIFICATION |
| Kill-switch 日期 | **2026-05-01** | memo A.5 |

---

## 3 个最可能的 killer questions（一句话答）

### Q1: "500× speedup 不是你的 MetaD 变快，是 coordinate rescaling，不算真加速"
**答**: 同意。slide 1 和 slide 9 已经改过，没说 500×，改成"coord-system 修正后 walker 能 access s=5-11 region"。真 exploration speedup 数字要等 10-walker 出。

### Q2: "zero neighbor_msd_cv = linear interp = 没 physical intermediate。你 s=8 凭什么代表 PC？"
**答**: 两句话，不合并。(1) path 本身是 geometric reference，s=8 **不 define** PC。(2) 5DW0/5DW3 是**独立** biological PC 晶体，它们 projection **恰好**落在 s=8-9，这是事后 validation 不是 prior。真 mechanistic path 需要 string method / TMD，在 future work（memo 方向 2/F/G）。

### Q3: "+5 offset 是 alignment finding 还是 PDB 编号惯例差？"
**答**: 诚实答——大部分是**编号惯例差**（1WDW 和 3CEP N 端 signal peptide 处理不同）。NW 的 value-add 不是"发现 offset"，是**证明 selected 112 个 residue 内无 indel**。如果有 indel，uniform offset 就数学上不可能，bug 会错得更彻底。

### Q4（备用）: "500 ns cMD 之前分析是不是也污染了？"
**答**: cMD trajectory 本身 **没污染**（unbiased Cartesian，没用 path CV）。污染的只是**用老 path 做过的 project_to_path.py 产出**，TechDoc Ch 3.4 列了 3 条 downstream 要重跑：(a) path_piecewise audit retracted, (b) probe_sweep/45324928 stall 重解释, (c) FP-032 21× 纠正到 1.26×。

### Q5（备用）: "MNG 需要 qMSM，你会吗？"
**答**: **坦白不会**。这是下个月关键技术风险。mitigation: Huang lab 教程 + PyEMMA/Deeptime 现成实现。1 个月判断学不动就 drop 给未来 grad student。

---

## 绝不能说的话

- ❌ "MetaD replication 做完了" / "复现成功"
- ❌ "Miguel's λ=80 is universal"
- ❌ "500× 加速"（已从所有材料删除）
- ❌ "STAR-MD 不好，cartridge 更好"
- ❌ "我 owns TrpB MetaD"

## 必须说的话

- ✅ "D1 path 层做完，D2 API 草图 + D3 demo 还欠"
- ✅ "Miguel 80 和我们 101 同一量级（ratio 1.26×）"
- ✅ "Coordinate system 修正后，walker 能 access s=5-11 新 region"
- ✅ "STAR-MD upstream 生成，cartridge downstream 评估"
- ✅ "2026-05-01 hard kill-switch，WT FES 不过 sanity 就全停"

---

## Slide 流程记忆钩子

1-3 **Strategic**（5 min）: 定位 pivot → cartridge 7 组件 → lab 生态位
4-10 **D1 MetaD 实质进展**（12 min）: Miguel → A/B/C/D → **FP-034** (slow down) → NW 修复 → bio sanity → pilot → 10-walker ready
11-12 **探索路线树**（4 min）: what tried, what rejected, why rejections 有价值
13-15 **ML audit + STAR-MD**（6 min）: 5 方向 → 1 alive/2 weakened/2 dead → ByteDance upstream
16-17 **Next + kill-switch**（3 min）: D2/D3 + 5-1 gate → Q&A

**时长**: ~30 min talk + 10-15 min Q&A。讲到 pilot 那张 slide（9）**必须 pause 2 秒**强调 t=0 s=7 的 re-interpretation —— 这是全场信息量最大的一点。

---

## 讲完最后一句

"**FP-034 给我的教训是 cross-species PATH-CV 必须做 sequence identity > 50% 的硬 gate；这条我已经写进 failure-patterns.md FP-034 防范措施，所有 future path-builder 脚本头必须 assert 这个条件。**"

这句话把"修一个 bug"拔高到"建了一条规则"，Yu 最买这种 takeaway。

---

## 如果 Yu 追问太多 details → 临时降级话术

"这个我 hot-path 答不对可能犯错。**TechDoc 第 X 章** / **REVERSE_SANITY_CHECK** / **VERIFICATION_REPORT** 都写了完整溯源，我们会后过一遍。"

---

## 最终心态

你这周的真实贡献是：(1) 发现一个 2 个月没人发现的 silent bug，(2) 独立 + Codex 双实现交叉验证，(3) 把 replication 升级成 cartridge owner 的战略定位。Yu 的 pressure 是保护你，不是针对你。**稳住、诚实、承认 limitation，就赢了**。
