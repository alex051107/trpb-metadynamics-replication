# Single-Walker MetaD Timeline (2026-04-09 → 2026-04-17)

Last updated: 2026-04-17 15:32 (Job 44008381 at 27.68 ns, max s=3.494 — **首次越过 s=3 门槛**)

## 核心时间线

| # | Job ID | 起止日期 | 时长 | 类型 | 结果 | 原因/备注 |
|---|--------|---------|------|------|------|-----------|
| 1 | 42679152 | 2026-04-09 → 04-12 | 50 ns | 首次 single walker, post-PATHMSD 切换 | 卡死 O basin, s=[1.00,1.63], 25000 高斯 48 kJ/mol 全堆 s≈1 | **FP-024** SIGMA 崩塌 — ADAPTIVE=GEOM 无 SIGMA_MIN 下，σ_s 塌到 0.011 (<0.5% 路径轴) → 针状高斯 → 零梯度 → walker 感受不到 bias |
| 2 | 43813633 | 2026-04-16 | 10 ns probe, post-FP-024 fix | max s=1.393, 末 2 ns s↔z 相关 -0.31→+0.49 | walltime 到 — 10 ns 太短，但末期出现 "activated-barrier escape" 信号 (Branduardi 2007 描述的跃迁特征) |
| 3 | 44008381 | 2026-04-16 → 04-19 (est) | 10 → 50 ns checkpoint 延长 | **进行中** 当前 27.68 ns, max s=3.494 (1.41% 帧 s>3) | `gmx convert-tpr -extend 40000` + plumed_restart.dat 带 RESTART 指令 (FP-026 修复); HILLS append 正常, 无 bck.*.HILLS |

## Trend analysis (at 27.68 ns)

s(R) 在各个 5 ns 窗口的 max (单调爬升):
- t≤5 ns: max s = 1.182
- t≤10 ns: max s = 1.393 (probe boundary)
- t≤15 ns: max s = 1.455 (延长启动, 爬升缓慢)
- t≤20 ns: max s = 1.807
- t≤25 ns: max s = 2.794 (最近 5 ns 窗口跳升 ~1.0)
- **t≤30 ns: max s = 3.494** ✨ 首次越过 s=3 门槛, fraction s>3 = 1.41%

连续 6 个窗口都在爬 — walker 没平台, 正持续过 barrier. 如果 35/40 ns 继续保持 +0.5~+1.0 的增量, 50 ns 内有望触 Phase 2 门槛 (s≥5).

## 决策门 (2026-04-18 AM 或 50 ns 完成时)

| 25 ns max s | 50 ns max s | 决策 |
|-------------|-------------|------|
| ≥ 5 | N/A | **Phase 2** — 即刻 10-walker, 从 COLVAR 聚类出 10 帧 |
| 3 ≤ s < 5 | 看 50 ns | 等 50 ns 结果再决定 |
| < 3 | ≥ 5 | 依然 Phase 2 (50 ns 爬上来了) |
| < 3 | < 3 | **Phase 3** — 放弃 single-walker, 建 4HPX-seeded Ain-PLP 体系, 双 seed dual-walker |

截至 2026-04-17 15:32, max s=**3.494** (27.68 ns)，**已进入 3-5 观察区** — 按规则让 50 ns 跑完再决定。趋势单调向上，Phase 2 概率上升。

## 关联失败模式

- **FP-020** (FUNCPATHMSD→PATHMSD 切换): 2026-04-08 发现, fix 2026-04-09
- **FP-022** (LAMBDA per-atom MSD 校正 3.39→379.77): 2026-04-09 fix
- **FP-024** (SIGMA 崩塌): 2026-04-12 诊断, 2026-04-15 fix
- **FP-025** (伪造 SIGMA SI 引用): 2026-04-15 发现
- **FP-026** (checkpoint restart 两个 bug): 2026-04-16 fix
- **FP-027** (SI "80" 误读为 λ): 2026-04-16 发现并 Codex 纠正

## 相关工件

- 当前 plumed.dat: `replication/metadynamics/single_walker/plumed.dat`
- 教学版 (带 sensitivity 表): `replication/metadynamics/annotated/plumed_annotated.dat`
- 延长脚本: `.worktrees/probe-extension/replication/metadynamics/single_walker/extend_to_50ns.sh`
- CV audit: `.worktrees/cv-audit/project_structures.py` (运行得: 1WDW→1.09, 3CEP→14.91, 4HPX→14.91)
- SSH 分析 checklist: `replication/metadynamics/single_walker/SSH_INSPECTION_CHECKLIST.md`
