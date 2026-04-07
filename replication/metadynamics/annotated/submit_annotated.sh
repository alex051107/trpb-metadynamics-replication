#!/bin/bash
# ===========================================================================
# Slurm 提交脚本：PfTrpS(Ain) 单 walker WT-MetaD 模拟
# 集群：UNC Longleaf (RHEL 8, Slurm 23.x)
# ===========================================================================
#
# 这个脚本做什么？
#   1. 向 Slurm 调度系统申请计算资源（CPU、内存、时间）
#   2. 加载所需软件环境（GROMACS + PLUMED）
#   3. 运行 gmx grompp（预处理：合并参数+坐标+拓扑 → 生成 .tpr）
#   4. 运行 gmx mdrun（生产运行：读取 .tpr + plumed.dat → 输出轨迹+能量+CV）
#   5. 打印诊断信息（文件大小、行数、CV 值范围）
#
# 预计运行时间：
#   50 ns MetaD 在 8 个 CPU 核心（无 GPU）上：约 24-48 小时
#   72 小时的墙钟时间提供了安全余量，防止因节点慢或队列等待而超时
#   如果 wall time 不够，作业会被 Slurm 杀掉，但可以用检查点续跑
#
# 提交方式：
#   cd /work/users/l/i/liualex/AnimaLab/runs/metad_benchmark/
#   sbatch submit_metad.sh
#
# 查看状态：
#   squeue -u liualex                    # 看作业在跑没
#   tail -f slurm-trpb_metad-*.out       # 实时看输出日志
#   tail -5 COLVAR                       # 看最新的 CV 值
#
# 续跑（如果超时）：
#   gmx mdrun -deffnm metad -plumed plumed.dat -cpi metad.cpt -ntmpi 1 -ntomp 8
#
# 输入文件（提交前必须都在 $SLURM_SUBMIT_DIR 中）：
#   metad.mdp       - GROMACS 参数文件（见 metad_annotated.mdp 的详细注释）
#   start.gro       - 平衡后的坐标（从 AMBER 准备 → 转换到 GROMACS 格式）
#   topol.top       - 系统拓扑文件（ff14SB + TIP3P + PLP 的 GAFF 参数）
#   plumed.dat      - PLUMED MetaD 输入文件（见 plumed_annotated.dat 的详细注释）
#   frames/         - 包含 frame_01.pdb ... frame_15.pdb（Path CV 的 15 个参考结构）
#
# 输出文件：
#   metad.tpr       - 便携运行文件（gmx grompp 生成），包含运行所需的一切信息
#   metad.xtc       - 压缩轨迹文件（每 10 ps 一帧），用于后续构象分析
#   metad.edr       - 能量文件（每 2 ps 一个数据点），用 gmx energy 读取
#   metad.log       - MD 引擎日志，包含性能数据（ns/day）和 PLUMED 计时信息
#   metad.cpt       - 检查点文件（用于续跑，Slurm 自动定期更新）
#   COLVAR          - Path CV 值 + 偏置势（PLUMED 输出，每 500 步 = 1 ps 一行）
#   HILLS           - 沉积的高斯山丘（PLUMED 输出，每 1000 步 = 2 ps 一行）
#   slurm-*.out     - Slurm 的标准输出/错误日志（包含诊断信息和报错）
#
# ===========================================================================

# --- Slurm 资源申请 ---
# 每个 #SBATCH 行告诉 Slurm 调度器这个作业需要什么资源
# Slurm 会根据这些参数把作业分配到合适的节点上

#SBATCH --job-name=trpb_metad         # 作业名称：在 squeue 输出中显示，方便识别
                                       # 也用于输出文件名（见 --output）

#SBATCH --partition=general           # 分区（队列）：general 是 Longleaf 的通用分区
                                       # 为什么用 general（CPU）而不是 gpu 分区？
                                       # 因为 PLUMED 的 Path CV 计算不支持 GPU 加速。
                                       # PLUMED 在每一步都要算 15 次 RMSD + 路径函数，
                                       # 这些计算在 CPU 上运行。如果用 GPU 跑 GROMACS，
                                       # 每一步都需要 GPU→CPU→GPU 的数据传输（PCIe 瓶颈），
                                       # 反而可能比纯 CPU 更慢。
                                       # general 分区最长可跑 7 天 (168 小时)

#SBATCH --ntasks=1                    # MPI 进程数 = 1（只用一个 MPI rank）
                                       # MetaD 单 walker 不需要多 MPI 进程
                                       # PLUMED 在 thread-parallel 模式下工作，不需要 MPI
                                       # 如果做多 walker MetaD，需要 --ntasks=4（每个 walker 一个 rank）

#SBATCH --cpus-per-task=8             # 每个 MPI 进程分配 8 个 CPU 核心
                                       # 这些核心用于 OpenMP 线程并行（GROMACS 的 -ntomp 参数）
                                       # 8 核是单 walker MetaD 的甜蜜点：
                                       # 太少（如 2）→ 力计算太慢
                                       # 太多（如 32）→ 线程同步开销大于收益

#SBATCH --mem=16G                     # 申请 16 GB 内存
                                       # PfTrpS 体系约 7 万个原子，需要约 4-8 GB 内存
                                       # 16 GB 提供充足余量，包括：
                                       #   - GROMACS 邻居列表 (~2 GB)
                                       #   - PME FFT 网格 (~1 GB)
                                       #   - PLUMED 的 15 个参考帧 + RMSD 计算 (~0.5 GB)
                                       #   - 系统开销 (~2 GB)

#SBATCH --time=72:00:00               # 墙钟时间限制：72 小时 = 3 天
                                       # 超过这个时间 Slurm 会强制杀掉作业
                                       # 50 ns 在 8 核上预计 24-48 小时，72 小时是安全余量
                                       # 如果真的超时了，用检查点文件续跑即可

#SBATCH --output=slurm-%x-%j.out     # 输出日志的文件名模板
                                       # %x = 作业名称 (trpb_metad)
                                       # %j = 作业 ID（Slurm 分配的唯一数字）
                                       # 例如：slurm-trpb_metad-1234567.out
                                       # 标准输出和标准错误都写到这个文件里

# --- 遇到错误立即退出 ---
# set -e：任何命令返回非零退出码时，脚本立即停止（不继续执行后续命令）
# set -o pipefail：管道中任何命令失败时，整个管道返回失败
# 这很重要：如果 grompp 失败了（比如参数错误），不应该继续跑 mdrun
set -eo pipefail

# --- 加载软件环境 ---
module purge                           # 清除所有已加载的模块（从干净状态开始）
                                       # 防止不同模块之间的库冲突（比如两个不同版本的 libfftw）

module load anaconda/2024.02           # 加载 Anaconda 发行版（提供 conda 命令）
                                       # Longleaf 上 conda 不是默认可用的，需要先加载模块

eval "$(conda shell.bash hook)"        # 初始化 conda 环境（让 conda activate 命令可用）
                                       # 这一行是 conda 4.x+ 的标准初始化方式
                                       # 没有它，conda activate 会报错

conda activate trpb-md                 # 激活我们的 conda 环境
                                       # 这个环境包含：
                                       #   - GROMACS 2026.0（conda-forge 版，编译时启用了 -plumed 支持）
                                       #   - PLUMED 2.9 的 Python wrapper
                                       # 为什么用 conda 版 GROMACS 而不是 module load gromacs？
                                       # 因为系统模块的 GROMACS（module load gromacs/2026.0）
                                       # 编译时没有启用 PLUMED 支持，无法运行 gmx mdrun -plumed

# --- PLUMED 内核路径 ---
# 为什么需要这个环境变量？
# conda-forge 的 GROMACS 在编译时开启了 PLUMED 支持（-plumed 标志），
# 但它不捆绑 PLUMED 的动态库（libplumedKernel.so）。
# 运行时，GROMACS 会通过 dlopen() 动态加载 PLUMED_KERNEL 指向的 .so 文件。
# 如果这个变量没有设置或路径错误，gmx mdrun -plumed 会报错：
#   "PLUMED is not available. Check that PLUMED_KERNEL is set correctly."
#
# 为什么指向源码编译版本（/work/.../plumed-2.9.2/）而不是 conda 安装的？
# 因为源码编译版本可以精确控制 PLUMED 版本和编译选项，
# 确保与 conda GROMACS 的 ABI（应用二进制接口）兼容。
# conda 环境中的 PLUMED 版本可能与 GROMACS 不匹配，导致段错误。
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so

# --- OpenMP 线程数 ---
# 告诉 GROMACS 使用多少个 OpenMP 线程做并行计算
# ${SLURM_CPUS_PER_TASK:-8} 的含义：
#   如果 SLURM_CPUS_PER_TASK 变量存在（正常 Slurm 作业中），使用它的值（= 8）
#   如果不存在（比如交互式测试时直接 bash submit.sh），回退到默认值 8
# 线程数必须与申请的 CPU 核心数匹配！
# 如果 OMP > 实际核心数，线程会争抢 CPU，性能反而下降
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

# --- 切换到提交目录 ---
# Slurm 默认在用户的 $HOME 目录启动作业
# 但输入文件在提交 sbatch 的那个目录（$SLURM_SUBMIT_DIR）中
# 所以需要 cd 过去。如果不 cd，grompp 找不到 metad.mdp 等文件
cd $SLURM_SUBMIT_DIR

# --- 诊断输出（打印到 slurm-*.out 日志）---
# 这些 echo 帮助后续排错：如果作业出了问题，可以从日志中确认环境是否正确
echo "=== Environment ==="
echo "PLUMED_KERNEL: $PLUMED_KERNEL"
echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "LAMBDA: 3.3910 nm^-2 (= 0.033910 A^-2 x 100)"

# --- GROMACS 预处理（gmx grompp）---
# grompp = GROmacs PreProcessor
# 它做什么：把三个文件合并成一个便携运行文件 .tpr
#   输入：metad.mdp（参数）+ start.gro（坐标）+ topol.top（拓扑）
#   输出：metad.tpr（二进制，包含运行所需的全部信息）
#
# -maxwarn 2：最多允许 2 个警告（否则 grompp 拒绝生成 .tpr）
# 已知的预期警告：
#   警告 1：原子名称不匹配（AMBER→GROMACS 转换时原子命名惯例不同，如 HB2 vs HB1）
#   警告 2：DispCorr=no 与 cutoff VdW 一起使用（我们是故意的，因为 NVT 不需要色散校正）
# 注意：不要随意增大 -maxwarn！意外的警告可能指示真正的参数错误
gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2

# --- 生产 MetaD 运行（gmx mdrun）---
# 这是实际跑分子动力学的命令，是整个脚本最耗时的部分（24-48 小时）
#
# -deffnm metad     所有输出文件统一命名为 metad.*（metad.xtc, metad.edr, metad.log, metad.cpt）
#                    方便管理，不用为每个输出单独指定文件名
#
# -plumed plumed.dat PLUMED 输入文件的路径
#                    GROMACS 在每一步调用 PLUMED：
#                    1. 传递当前坐标给 PLUMED
#                    2. PLUMED 计算 RMSD → Path CV → 偏置力
#                    3. PLUMED 把偏置力加到 GROMACS 的力上
#                    4. GROMACS 用总力（物理力+偏置力）更新原子位置
#
# -ntmpi 1           只用 1 个 MPI rank
#                    单 walker MetaD 不需要多 MPI 进程
#                    PLUMED 的 thread-parallel 模式要求 ntmpi=1
#                    如果设成 >1，PLUMED 会因为 domain decomposition 出错
#
# -ntomp N           使用 N 个 OpenMP 线程（从上面的 OMP_NUM_THREADS 取值 = 8）
#                    GROMACS 的力计算（PME + 非键 + 键）在这 8 个线程间并行
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}

# --- 运行后诊断 ---
# 作业完成后自动打印一些信息到 Slurm 日志，方便快速检查是否正常完成
echo "=== Done ==="

# 显示输出文件大小：COLVAR 应约 50 MB，HILLS 应约 5 MB，metad.log 应约 1-10 MB
# 如果文件太小（如 <1 MB），说明模拟提前中断了
ls -lh COLVAR HILLS metad.log

# 显示行数：COLVAR 应约 50000 行（50 ns / 1 ps），HILLS 应约 25000 行（50 ns / 2 ps）
# 如果行数远少于预期，说明模拟没有跑完
wc -l COLVAR HILLS

# 显示 COLVAR 的前 5 行：path.s 应该从约 1 开始（如果初始构象是 Open）
# 如果 s 从 15 开始，说明初始构象是 Closed（需要检查是否正确）
head -5 COLVAR

# 显示 COLVAR 的最后 5 行：检查最终采样范围
# 如果 s 一直停在 1-3 附近没动过，说明偏置势不够强或模拟时间太短
# 理想情况下应该看到 s 在 1-15 之间有来回的波动
tail -5 COLVAR
