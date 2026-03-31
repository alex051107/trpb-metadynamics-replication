# Zotero MCP 配置指南 + 项目进展总结

---

## 第一部分：Zotero MCP 安装与配置

### 为什么用 Zotero MCP？

Zotero MCP 让你可以直接在 Claude 对话中：
- 语义检索你的 Zotero 文献库（"帮我找关于 COMM domain 的论文"）
- 提取 PDF 批注和笔记
- 自动生成引用格式
- 跨文献比较和分析

---

### 两种配置模式

#### 模式 A：本地模式（推荐，最简单，无需 API Key）

**前提条件**：
1. 电脑上已安装 **Zotero 7**（注意：必须是 Zotero 7，不是 Zotero 6）
2. Zotero 正在运行

**第一步：启用 Zotero 本地 API**

打开 Zotero → 偏好设置（Preferences）→ Advanced → 勾选：
> ✅ "Allow other applications on this computer to communicate with Zotero"

**第二步：安装 Zotero MCP**

在终端运行：

```bash
# 推荐方式（用 uv，更快）
pip install zotero-mcp-server

# 然后自动配置
zotero-mcp setup
```

**第三步：Claude Desktop 配置**

找到 `claude_desktop_config.json` 文件，位置：
- **macOS**：`~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**：`%APPDATA%\Claude\claude_desktop_config.json`

添加以下内容：

```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp",
      "env": {
        "ZOTERO_LOCAL": "true"
      }
    }
  }
}
```

**第四步：验证**

重启 Claude Desktop → 在对话框问 Claude："我的 Zotero 里有哪些关于 tryptophan 的论文？" → 如果返回结果就成功了。

---

#### 模式 B：云端模式（需要 Zotero API Key）

**适合**：不在本地用 Zotero，或者想从其他设备访问。

**第一步：获取 API Key**
1. 登录 [zotero.org](https://www.zotero.org)
2. 进入 Settings → Feeds/API → Create New Private Key
3. 勾选所有"Read"权限，保存 API Key

**第二步：获取 Library ID**

```bash
curl "https://api.zotero.org/users/verifyCredentials" \
  -H "Zotero-API-Key: YOUR_API_KEY"
```

返回 JSON 中的 `userID` 就是你的 Library ID。

**第三步：配置 claude_desktop_config.json**

```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp",
      "env": {
        "ZOTERO_API_KEY": "YOUR_API_KEY",
        "ZOTERO_LIBRARY_ID": "YOUR_USER_ID",
        "ZOTERO_LIBRARY_TYPE": "user"
      }
    }
  }
}
```

---

### 将本项目论文导入 Zotero 的最快方法

**方法一：通过 DOI 批量导入**

在 Zotero 工具栏点击魔法棒图标（"Add item(s) by Identifier"），粘贴以下 DOI，每行一个：

```
10.1002/cbic.202000379
10.1073/pnas.1516401112
10.1002/pro.4426
10.1021/jacs.9b03646
10.1021/acscatal.1c03950
10.1038/s41586-023-06415-8
10.1038/s41592-025-02975-x
10.1038/s42254-020-0153-0
10.3389/fmicb.2024.1455540
10.1007/s00018-009-0028-0
```

Zotero 会自动从网络获取完整元数据和 PDF（如果有开放访问版本）。

**方法二：手动从 Google Scholar 保存**

安装 [Zotero Connector 浏览器插件](https://www.zotero.org/download/connectors)，然后：
1. 在 Google Scholar 搜索每篇论文
2. 点击浏览器工具栏的 Zotero 图标
3. 自动保存到 Zotero

**推荐：创建一个"TrpB Project"集合（Collection）专门存放这些论文。**

---

### Zotero MCP 使用示例（配置成功后）

你可以这样与 Claude 对话：

```
你：帮我在 Zotero 里找所有关于 COMM domain 的论文
Claude：[通过 Zotero MCP 检索] 找到以下论文...

你：帮我总结这两篇论文的核心方法差异：[论文1] vs [论文2]
Claude：[读取 PDF 内容] 对比如下...

你：我想写一篇 weekly update，自动引用相关文献
Claude：[从 Zotero 提取引用格式] 以下是你的 update 草稿...
```

---

### 备选方案：如果 Zotero 有问题

另一个优质的免费文献管理 + MCP 集成方案：

**Notion + Notion MCP**：
- 在 Notion 里创建一个"论文数据库"表格（每行一篇论文）
- 用 Notion MCP 让 Claude 读写这个数据库
- 优点：更灵活，可以加自定义字段（进度、笔记等）

**简单替代（最快）**：
- 将本手册的"文献清单"保存为 Zotero 书签
- 直接将 PDF 上传给 Claude 进行对话

---

## 第二部分：你现在的进展在哪里？

### 2.1 你已经完成的事

| 内容 | 状态 |
|------|------|
| 参加了 onboarding 会议，了解了项目大方向 | ✅ 完成 |
| 知道了要做什么（TrpB de novo → D-Trp，MetaDynamics） | ✅ 完成 |
| 获得了导师 Google Scholar 链接（Osuna） | ✅ 完成 |
| 完成了本文档的研究和整理 | ✅ 通过本次调研完成 |

---

### 2.2 你还不知道（但很快需要弄清楚）的事

| 问题 | 如何解决 |
|------|---------|
| 具体有哪些 RFDiffusion 候选结构？在哪里？ | 加入 Stack channel 后问 JP |
| MetaDynamics 在哪个服务器上跑？有多少 GPU 时间？ | 问 JP，申请 HPC 账号 |
| 他们用的 MD force field 是什么？（AMBER? CHARMM?）| 看 Osuna 文章 SI，或问 JP |
| D-Trp 对应的过渡态结构是什么？有 QM 计算吗？ | 可能需要自己做或问组里 |
| "White Lab" 是谁？实验流程如何？ | 问 JP |

---

### 2.3 你理解这个项目的方式

**最简洁的框架**（建议你能随时用这句话解释项目）：

> 我们用生成式 AI（RFDiffusion2）从头设计一个能合成 D-型色氨酸的酶，这需要重新设计活性位点的立体化学几何。MetaDynamics 的作用是：（1）验证设计的酶是否具有正确的构象动力学，（2）为设计流程提供物理约束，让我们能用自由能景观信息指导更好的设计。

---

### 2.4 关键概念关系图

```
你的项目
    │
    ├── 生物学目标
    │       └── 合成 D-Trp（立体化学翻转）
    │                └── 需要：re-face 吲哚进攻
    │                         └── 需要：重新设计活性位点几何
    │
    ├── 计算工具链
    │       ├── RFDiffusion2 → 生成候选骨架（已做/正在做）
    │       ├── ProteinMPNN → 设计序列（已做）
    │       ├── AlphaFold2 → 筛选验证（已做）
    │       └── MetaDynamics → 你的工作（待开始）
    │
    ├── MetaDynamics 的具体角色（你需要想清楚的）
    │       ├── A. 筛选工具：对候选结构评估构象景观
    │       ├── B. Reward signal：FEL 信息 → reward function term
    │       └── C. 机制研究：理解为什么某些设计有效/无效
    │
    └── 你的独特价值
            ├── LiGaMD 经验 → 可以做 enhanced sampling 对比
            ├── ML 建模能力 → FEL 特征 → 活性预测模型
            └── HPC 自动化 → 大规模并行计算流程
```

---

### 2.5 你接下来应该怎么做（分阶段）

#### 🟥 本周内必须完成

1. **加入 Stack channel**（等 JP 今晚把你拉进去）
2. **第一篇 weekly update**（虽然刚入职，但可以写"加入了项目，读了 Osuna JACS 2019 和 TrpB Biocatalyst 综述，了解了..."）
3. **开始读 Paper 1**（TrpB Biocatalyst Extraordinaire，这是本周最重要的任务）

#### 🟨 未来两周

4. **安装 GROMACS + PLUMED**（验证软件栈，先跑 alanine dipeptide tutorial）
5. **精读 Osuna JACS 2019**（拿到文章后逐字读 Methods，理解他们的 CV 定义）
6. **下载所有 PDB 结构**（PfTrpB 相关：5DW3, 1K8Z, 5T5K）

#### 🟩 一个月内

7. **复现 COMM domain MetaDynamics**（LBCA-TrpB 的 FEL 重建）
8. **准备第一个具体技术提案**（如何把 MetaDynamics 接入 reward function）

---

### 2.6 理解这些事情的最佳思维框架

学术科研中 "快速上手" 的核心思路：

**不要从零开始理解每一件事，要从项目终点倒推。**

问自己：**"六周后，我应该能展示什么结果？"**

推荐的 6 周目标：
> 能展示一张 LBCA-TrpB 的 MetaDynamics FEL 图（哪怕是重复 Osuna 的结果），并用 2-3 句话解释它和 D-Trp 项目的关联。

有了这个目标之后，所有的读文献、装软件、跑模拟都有了方向感。

**读文献的诀窍**：每读一篇，问自己：
1. 这篇文章的核心 claim 是什么？（一句话）
2. 他们用什么 evidence 支持这个 claim？（实验/计算结果）
3. 如果我的项目要用这个方法，我需要改变什么？

---

*文档生成时间：2026年3月18日*
*文献来源：PubMed（DOI 链接均已注明）、Osuna Lab 官网、GitHub 开源资源*
