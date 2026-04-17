# SSH 分析 Checklist — single walker MetaD 作业监控

本文档给出 SSH 进入 Longleaf 后应该看哪些数据的完整清单。
针对当前 Job 44008381，但结构同样适用于将来的 10-walker。

## 前置: 建立 SSH 连接

```
ssh longleaf
cd /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker
```

若 Duo 重新认证: 走 `ssh longleaf` 一次建立 ControlMaster, 后续命令免重试。

## 第 1 步: 作业状态

(每 step 同样结构: 命令 → 解读健康/异常)

### 1A. 作业是否还在跑?
```
squeue -u liualex -j 44008381
```
- ST=R: 运行中
- ST=PD: 在排队 (应该立刻查 START_TIME; 若超预期晚, 看分区负载)
- ST=CG: 清理中, 快完成
- 不在列表: 已结束 (检查 sacct)

### 1B. 精确状态 + 运行时间
```
sacct -j 44008381 --format=JobID,State,Elapsed,MaxRSS,ReqTRES
```
- State=RUNNING/COMPLETED/FAILED/TIMEOUT
- Elapsed 超过 wall time → 已被 kill, 看 .err 确认

## 第 2 步: 物理进度 — s(R) 和 z(R)

### 2A. 最新几行 COLVAR
```
tail -5 COLVAR
```
列: `time(ps)  path.sss(s)  path.zzz(z)  metad.bias(kJ/mol)`

健康:
- time 单调递增 (没有 restart 重置)
- s 在 [1, 15] 内
- z 在 [-0.1, 0.1] 内 (我们的 SIGMA_MAX_z=0.05, 略超是正常的热涨落)
- bias 随时间累积 (单调非负, 但可局部下降因 well-temper 饱和)

病:
- time 回跳 → restart 没处理对 (FP-026 复发)
- s > 20 → walker 跑出 path 外 (z 应也大; 检查 path.pdb 对齐)
- bias = 0 → METAD action 没激活 (plumed.dat 出错)

### 2B. s(R) 窗口统计 — 这是最关键的一步
```
python3 - <<EOF
import numpy as np
d = np.loadtxt('COLVAR', comments='#')
t, s, z = d[:,0], d[:,1], d[:,2]
print(f'已跑 {t.max()/1000:.1f} ns, n_rows={len(t)}')
print(f's range: [{s.min():.3f}, {s.max():.3f}]')
print(f'z range: [{z.min():.4f}, {z.max():.4f}]')
print('max s per 5 ns window:')
for tw in [5,10,15,20,25,30,35,40,45,50]:
    m = t <= tw*1000
    if m.any(): print(f'  t<={tw:2d} ns: max s = {s[m].max():.3f}')
from scipy.stats import pearsonr
if len(t) > 1000:
    last2ns = t >= (t.max() - 2000)
    if last2ns.sum() > 10:
        r, _ = pearsonr(s[last2ns], z[last2ns])
        print(f'Last 2 ns s-z Pearson: {r:+.2f}')
        print(f"  Interpretation: {'活化越过 barrier 信号' if r > 0.3 else '正交' if abs(r) < 0.3 else '反向, 后退'}")
EOF
```

解读:
- max s 单调递增 → walker 在移动, 好
- max s 三个连续窗口不变 → 卡死 (要怀疑 FP-024 复发 或 barrier 太高)
- 末 2 ns Pearson s-z > +0.3 → walker 正在从 O 往 C 跃迁 (活化 barrier 特征)
- Pearson < -0.3 → walker 在回退
- |Pearson| < 0.3 → s 和 z 解耦, walker 在平面上游走

## 第 3 步: HILLS 沉积健康 — FP-024 复发侦测

```
tail -3 HILLS
wc -l HILLS
```
列: `time  path.sss  path.zzz  sigma_s  sigma_z  height  biasf`

健康:
- sigma_s 在 **[0.3, 1.0]** (SIGMA_MIN_s=0.3 / SIGMA_MAX_s=1.0 强制, 应看到刚好触底 0.3 的情况也有 0.3~0.6 之间)
- sigma_z 在 **[0.005, 0.05]**
- height 恒定 = 0.628 (单位 kJ/mol)
- wc -l 每秒增加约 0.5 行 (PACE=1000 steps × dt=2 fs = 2 ps/高斯 → 1 行/2ps)

病:
- sigma_s < 0.3 → SIGMA_MIN 没生效 → plumed.dat 出错 / FP-024 复发
- sigma_s > 1.0 → SIGMA_MAX 没生效 (同理)
- height ≠ 0.628 → 读错 plumed.dat, 立刻检查挂载版本
- wc -l 停止增长 → PLUMED 挂了 (看 .err)

## 第 4 步: 有没有意外备份 — FP-026 复发侦测

```
ls -la bck.*.HILLS 2>/dev/null
ls -la bck.*.COLVAR 2>/dev/null
```

健康: 空输出 (没有这些文件)

病: 一旦出现 bck.0.HILLS → PLUMED restart 没生效, 之前的 bias 丢了, 必须 kill 并重新从 checkpoint 重启 (FP-026 protocol).

## 第 5 步: GROMACS/GPU 性能

```
tail -20 metad.log | grep -E "Performance|ns/day|Time"
```

健康: Hov 分区 200–280 ns/day; GPU 分区 150–200 ns/day.

病:
- < 50 ns/day → GPU 没拿到 (检查 Slurm 资源, nvidia-smi)
- 剧降 → 节点邻居压缩资源 (考虑 requeue)

## 第 6 步: NaN / 崩溃排查

```
grep -iE "nan|inf|segmentation|cannot|fatal" metad.log md.err | head -20
```

健康: 空

病:
- nan → 数值炸了 (过温, dt 太大, bias 炸开) — 查前一个 checkpoint
- segmentation → MPI/GPU 层崩溃, 查 Slurm .err

## 第 7 步: 决策门速查 (25 ns / 50 ns 时)

在 metad.log 里找当前 ns:
```
grep "Step " metad.log | tail -3
```

结合 **第 2B 步**的 max s(R), 应用决策表:

| 25 ns max s | 动作 |
|-------------|------|
| ≥ 5 | ALERT — Phase 2 go, 停 Job 44008381, 运行 multi_walker/setup_walkers.sh |
| 3 ≤ s < 5 | 继续 50 ns 观察 |
| < 3 | 严格是 Phase 3 触发, 但看趋势 (三连升 → 等 50 ns) |

## 第 8 步: 收尾 — 50 ns 完成后

Job 结束出 squeue 后, 确认:
```
tail -5 metad.log   # 找 "Finished mdrun" 字样
md5sum HILLS COLVAR   # Linux 用 md5sum (不是 Mac 的 md5)
sacct -j 44008381 --format=State,Exitcode
```

然后 scp HILLS COLVAR 到本地做 sum_hills FES 重建:
```
plumed sum_hills --hills HILLS --kt 2.908 --bin 200,200 --outfile fes.dat
```

kT 单位: `--kt 2.908` 对 350 K 在 kJ/mol 单位 (FP-021 修正过).

---

## 作为对 Yu Zhang 的 demo

组会时若 Yu 问"你是怎么确认 walker 在动的", 按 1 → 2B → 3 的顺序走三步,
用截图/粘贴终端输出给他看。重点: max s per 5 ns window + HILLS sigma_s 在 0.3~1.0 之间。
