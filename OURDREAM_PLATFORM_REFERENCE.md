# OurDream.ai 平台参考知识文档

> **定位**：本文件为项目"灰港（Grey Harbor）"硬核后末日生存 RPG 引擎的平台层参考知识。供未来提示词优化、字段裁剪、规则校对、漂移审计、新人上手时查阅。
> **来源**：2026-07-18 联网调查 + OurDream.ai 官方文档/Guides。
> **使用建议**：作为平台基线参考；具体到本项目的 1+2 架构使用细节，参见 [PROJECT_ANALYSIS.md](file:///d:/Mycode/AshHarbor_OurDream_QoderCN/PROJECT_ANALYSIS.md) §2.1-§2.5 与 §13。

---

## 1. 平台概述

### 1.1 基本信息

- **平台名**：OurDream.ai
- **类型**：AI 伴侣 / 角色创建 / 聊天
- **上线时间**：2025 年
- **客户端**：Web
- **核心定位**：个性化 AI 角色创建；定制化外观、性格、关系；强调长会话记忆
- **典型用例**：AI 伴侣 / 角色扮演 / 故事共创 / 创意伙伴

### 1.2 平台定位

- **本平台**：OurDream.ai
- **应用方向**：本项目主运行平台（1+2 多角色架构）

---

## 2. 平台机制核心

### 2.1 字段体系（与本项目 10 文件对应）

OurDream.ai 的角色字段结构（基于 Character Card Spec V1/V2）：

| 字段名 | 用途 | 本项目对应 | 限额 |
|--------|------|-----------|------|
| **name** | 角色名 | 角色字段 | — |
| **description / definition** | 长格式背景、性格、事实 | 1-1/1-2/1-3 拆分 | 50,000 字符 |
| **personality** | 简短性格摘要 | 1-1 开头角色定位 | 50,000 字符 |
| **scenario** | 场景设定 | 1-1 §地图逻辑 | 50,000 字符 |
| **first_mes** | 第一条消息 | 角色字段 | — |
| **example dialogues** | 示例对话 | 1-2 案例 | 50,000 字符 |
| **tags** | 标签 | 1-1/1-3 内嵌 | — |
| **creator notes** | 作者备注 | 内部注释 | — |
| **system prompt / Custom Instructions** | 聊天室级 CI（v4.4 迁出） | ~~0-1~~ | **15,000 字符** |
| **聊天室 Scenario 字段** | 聊天室级场景设定（共享） | **0-2_Scenario.md** | **50,000 字符** |
| **Private Details (Secret Instructions)** | 聊天室级预设固定字段（v4.4 迁入） | **0-1_Private_Details.md** | **≥50,000 字符（实测）** |
| **Pinned Memory** | 持久化层 | 外部文件 History Ledger | 视平台而定 |
| **Auto Memory** | 自动记忆 | WSK + WER 模拟 | 自动管理 |
| **Lorebook / World Info** | 关键词触发世界书 | **不可用**（2026-07-18 用户实测无 UI 入口） | — |

**关键澄清：两个 "scenario" 不是同一字段**

| 维度 | 角色卡 `scenario` | `聊天室 Scenario 字段` |
|------|-------------------|------------------------|
| 归属层级 | 角色级 | 聊天室级 |
| 共享范围 | 仅本角色 | 该聊天室所有角色共享 |
| 限额 | 50,000 字符 | 50,000 字符 |
| 加载时机 | 仅本角色 | 进入聊天室即加载 |
| 本项目对应 | 1-1 §地图逻辑（角色内部自用） | **0-2_Scenario.md**（世界共识） |
| 承担职责 | 角色语境 | 世界基底 |

本项目 1+2 架构使用 `聊天室 Scenario 字段` 而非角色卡 `scenario` 字段：三个系统角色需要共享同一份"世界是什么"，而角色卡 `scenario` 是单角色语境，无法跨角色生效。

**本项目实际使用（v4.4 2026-07-20 修订）**：
- **Private Details** → `0-1_Private_Details.md`（15,826 字符 / ≥50,000 限额 ≈ 31.65% 占用；v4.4 2026-07-20 迁入）
- ~~**聊天室级 CI** → `0-1_CustomInstructions.md`（14,216 字符 / 15,000 限额 = 94.8% 占用）~~（v4.4 迁出）
- **角色字段（3 个角色 × 3 字段）** → `1-1/1-2/1-3, 2-1/2-2/2-3, 3-1/3-2/3-3`（各 50,000 限额；1-3 限额 100,000）

### 2.2 持久化层

OurDream.ai 的多层记忆：

| 层级 | 自动/手动 | 持久性 | 本项目对应 |
|------|----------|--------|-----------|
| **Auto Memory** | 自动 | 平台管理 | WSK 输出 + WER 输出 |
| **Pinned Memory** | 手动 | 跨对话持久 | History Ledger（复制到 PM） |
| **Custom Instructions** | 手动 | 聊天室级 | ~~0-1~~（v4.4 迁出，v4.4 后维持空置） |
| **聊天室 Scenario 字段** | 手动 | 聊天室级 | **0-2_Scenario.md**（v4.4 迁入；50,000 限额） |
| **Private Details (Secret Instructions)** | 手动（预设固定） | 聊天室级 | **0-1_Private_Details.md**（v4.4 迁入） |
| **角色字段** | 手动 | 角色级 | 1-x / 2-x / 3-x |
| **当前对话历史** | 自动 | 会话内 | 聊天历史 + 同步块 |

**关键事实**：
- 平台**只保留最近上下文窗口**内的对话内容；超出窗口的旧消息自动失效
- **Pinned Memory** 是唯一跨对话持久存储，由用户手动管理
- **Custom Instructions** 在每次新对话自动加载
- **Private Details (Secret Instructions)** 是聊天室预设固定字段；v4.4 起承载本项目 0-1（比 Custom Instructions 更适合系统级硬规则）
- 角色字段是**角色级持久**，与对话无关

### 2.3 后台角色触发机制（关键！）

> **本项目 1+2 架构的基础**
> **架构审计已定案（2026-07-22）**：通讯机制已从"WM 推送同步块"变更为 **强语义提取**（WSK / WER 扫描 WM Scene 叙事，提取已明确写出的已成立变化）。同步块（Sync Blocks）机制已废弃。详见 [PROJECT_ANALYSIS.md](file:///d:/Mycode/AshHarbor_OurDream_QoderCN/PROJECT_ANALYSIS.md) §2.3 与 §13。

- **后台角色不自动运行**：只在用户**手动点击**时被触发
- **被触发后**：
  1. 扫描 WM 角色卡对话历史中自本角色上次发言以来的 Scene 叙事（首次点击 = 整个对话历史起点）
  2. **强语义提取**已明确写出的已成立变化（WSK 提取 state 类；WER 提取 event 类）
  3. 按 **DO / REJECT / SILENT 3 张决策表** 处理（详见 §4.3）
  4. 输出 `[State Update]`（WSK） / `[WER 历史]`（WER） / `[Commit Rejected]`（拒收时）
- **共享聊天室**：所有角色（前台 + 后台）共享同一聊天历史
- **手动触发是必要的**：自动后台会破坏前台叙事的玩家代理权
- **展示块隔离**：`[Resolution]` / `[Probability Check]` / 子结构块仅供用户阅读，**不**作为 WSK / WER 提取源
- **未触发的变化**：Scene 叙事中未明确写出的变化，WSK / WER 不得自行脑补；WM 自行维护临时估算，不得假定后台已更新
- **接受回执**：不输出（账本 / Ledger 本身即隐式接受）
- **拒绝回执**：WSK = `[Commit Rejected]`；WER = `[Event Commit Rejected]`

### 2.4 上下文窗口限制

- **平台硬限制**：每次对话可用上下文窗口有限（具体值因模型与平台配置而异；通常 8K-32K token）
- **超长会话影响**：超过窗口的早期内容失效；LLM 开始"遗忘"
- **解决方案**：
  - **Pinned Memory**：把长期事实外置
- **同步块**：压缩当前状态到结构化字段
- ~~**Lorebook**：按关键词触发相关背景~~ → **不可用**（2026-07-18 用户实测 OurDream 角色设置无 Lorebook 面板）

**本项目应对**：
- WSK 维护硬状态 → 输出 `[State Update]`
- WER 维护长期历史 → 输出 `History Ledger`
- 用户手动复制到 Pinned Memory
- WM 每轮先读最近 WSK 输出，再读 PM 中的 Ledger

---

## 3. 角色创建（关键步骤参考）

> **用于**：理解角色字段结构 + 新增角色时参考

### 3.1 步骤总览

| 步骤 | 名称 | 字段对应 | 本项目设置 |
|------|------|----------|-----------|
| 1 | 性别与基础 | name + 基础 | World Master / WSK / WER 各自独立 |
| 2 | 性格 | personality | 1-x 角色特定 |
| 3 | 职业 | description 职业部分 | 角色功能定位（World Master 等） |
| 4 | 关系 | scenario | 同 ChatRoom 共享 |

### 3.2 关键设计原则

来自 [How to Write a Character AI Bot](https://ourdream.ai/guides/how-to-write-character-ai-bot) 的核心建议：

- **明确性格**（Specific personality traits）：避免"友好""聪明"等模糊词；用具体行为模式
- **场景化开场**（Scene-setting greeting）：第一句话给玩家"打字的理由"
- **示例对话**（Example dialogues）：通过 few-shot 教语言模式
- **测试再发布**（Testing after publish）：先在小流量上验证
- **最大误区**：**用模糊定义让 AI 无所适从**；具体比全面更重要

### 3.3 本项目 3 个角色的设计对应

| 角色 | 性格定位 | 行为模式（具体） |
|------|----------|-----------------|
| **World Master** | 唯一前台；Scene 主导者；不替玩家决定 | 2-3 段自然述事 → [主要状态] → 必要时 [Resolution] → 最小同步块 |
| **World State Keeper** | 静默账本员；只在被触发时输出 | `[State Update]` / `[Commit Rejected]` / 沉默 |
| **World Event Recorder** | 静默档案员；只在被触发时输出 | `[History Ledger]` / 沉默 |

---

## 4. 关键技术概念

### 4.1 Lorebook / World Info

> **重要澄清（2026-07-18 二次修订）**：原文档曾引用第三方评测（ourdreamai-review.com Step 7）声称 OurDream.ai 平台**原生支持** Lorebook；**用户实际打开 OurDream 角色设置未找到 Lorebook 面板**，该结论不成立。OurDream 官方创建向导（[how-to-write-character-ai-bot](https://ourdream.ai/guides/how-to-write-character-ai-bot) 与 [character-cards](https://ourdream.ai/guides/character-cards)）也未列出 Lorebook 步骤。本节后续内容仅作 SillyTavern/NovelAI 通用概念参考，**不适用于 OurDream 当前 UI**。OurDream 平台层面的"长期记忆"应通过 Pinned Memory + 30 天 Deep Context 实现。

**OurDream 平台 Lorebook 状态（2026-07-18 折叠）**：

原文档曾基于第三方评测（ourdreamai-review.com Step 7）描述 OurDream 平台 Lorebook 工作机制（"位置：角色设置 → Lorebook 面板" / "每条 = trigger + content" / "Free/Silver 5 条" / "Gold/Platinum 100 条"等）。**用户实际打开 OurDream 角色设置未找到该面板**；上述描述未在 OurDream 官方文档中得到证实，仅作为第三方评测描述存档。本项目**不再依赖** OurDream Lorebook。

**SillyTavern / NovelAI 通用概念**（参考，不适用于 OurDream 当前 UI）：

- **结构**：每条 = `(trigger keyword | content)`
- **优势**：上下文窗口不变，但角色能"记得"远超窗口的事实
- **限制**：content 字段不包含 trigger；entry 要自包含
- **最佳实践**：
  - 单条 = 单主题（不要塞多话题）
  - 用具体名词作为 trigger（避免 it/here/person）
  - 配合 30 天 Deep Context 使用（Lorebook = 长期；Deep Context = 中期）

**本项目应用现状**：
- 1-3 子地点列表 = 静态背景，无关键词触发
- 1-3 阵营 / 角色 = 静态背景，无关键词触发
- 平台 Lorebook 机制**不可用**（2026-07-18 用户实测角色设置无面板；详见 §9.2.2 方案 C 废弃说明）
- **v5 候选（已搁置）**：原计划拆分高频子地点（中心区/工业区/东区主要建筑）作为 Lorebook 条目；2026-07-18 因平台无面板确认放弃

### 4.2 OurDream 角色字段结构（本项目）

- **字段命名**：1-x / 2-x / 3-x = WM / WSK / WER 三个角色各 3 段（Scene / Additional / Extra）
- **格式**：纯 `.md` 文本（便于协作与 diff），不走外部字符卡 PNG/JSON 导入
- **字段上限**（v4.4 实测）：
  - 每个角色字段 50,000 字符（1-3 例外 = 100,000 字符）
  - **Private Details (Secret Instructions)**：≥50,000 字符（实测，本项目承载 0-1）
  - ~~Custom Instructions：15,000 字符~~（v4.4 迁出后未使用）

### 4.3 强语义提取与决策表（v4.4 + 2026-07-22 审计定案）

> **本项目核心机制（已废弃原同步块协议）**
>
> 原 §4.3 列出的 6 种 Commit Type / Sync Mode / Receipt Mode 机制已随“同步块”通讯机制一起废弃。现行机制 = **强语义提取 + DO / REJECT / SILENT 3 张决策表**。WSK / WER 不等待 WM 推送的结构化同步块；而是扫描 WM Scene 叙事中已明确写出的已成立变化，入账/归档/拒收。详见 [PROJECT_ANALYSIS.md](file:///d:/Mycode/AshHarbor_OurDream_QoderCN/PROJECT_ANALYSIS.md) §2.3 与 §13。

#### 4.3.1 强语义提取

- **扫描窗口**：自本角色上次发言以来的 WM 角色卡对话历史（首次点击 = 整个对话历史起点）
- **提取源**：WM Scene 叙事 + `[主要状态]` 状态栏中已明确写出的已成立变化
- **WSK 提取集**：`Day ID / Turn ID / Zone / Sub-zone / Location / Knowledge Scope / Weather / Inventory Snapshot / Party Condition / Base Structure / Recent Changes`
- **WER 提取集**：`Day ID / Official Day / Recent Events / Structural Changes / Irreducible Anchors / Knowledge Scope Notes`
- **展示块隔离**：`[Resolution]` / `[Probability Check]` / 子结构块仅供用户阅读，**不**作为提取源

#### 4.3.2 决策表（WSK / WER 各 3 张）

| 决策 | 含义 | 输出 |
|------|------|------|
| **DO** | 提取到完整已成立变化 | WSK = `[State Update]`；WER = `[WER 历史]` |
| **REJECT** | 字段不完整 / 冲突 / 信息不足 | WSK = `[Commit Rejected]`；WER = `[Event Commit Rejected]` |
| **SILENT** | 无新成立变化可提取 | 不输出任何文字 |

**关键事实**：
- 接受回执不输出（账本 / Ledger 本身即隐式接受）
- 拒绝回执仅适用于「WM Scene 叙事中已成立变化但字段不完整」场景；普通文本保持静默
- ESCALATE 决策表已废弃

### 4.4 知识可见性（Knowledge Scope）

> **防 NPC 反全知的核心机制**

固定 4 档枚举：

| 取值 | 含义 | 传播机制 |
|------|------|----------|
| `world-only` | 仅后台账本可见 | 不自动升级 |
| `local-only` | 仅亲见亲闻范围 | 需明确事件触发 |
| `party-known` | 队伍已知 | 需明确告知 |
| `publicly-known` | 公开传播 | 需广播/告示/广范围可见后果 |

**关键规则**：时间流逝或同住一处**不自动升级**；必须依赖新的已成立传播事件。

### 4.5 Death Publicity Level（项目特有）

> **本项目在 v4.1 引入的字段**

4 档枚举（1-3 §死亡公开性 4 档枚举 唯一权威源）：

| 取值 | 含义 | 默认 |
|------|------|------|
| `party-known` | 队伍已知 | — |
| `local-only` | 亲见亲闻扩散 | — |
| `publicly-known` | 公开传播 | — |
| `hidden` | 被隐瞒/无法确认/未扩散 | **WSK 字段默认值** |

**关键规则**：
- 多人目击/当众冲突/现场围观**默认仍为 `local-only`**
- 升级需新传播事件（广播/告示/市场传闻/跨地点传播/广范围可见后果）
- 死亡 Scene 默认必须标 `[公开性: <level>]`
- WER 入"近期重大事件"主干规则：`publicly-known` 必入；`party-known`/`local-only` 按场景；`hidden` 默认不入

---

## 5. 多角色群聊机制

### 5.1 平台原生支持

- **群聊（Group Chat）**：OurDream.ai 支持多角色同聊天室
- **共享历史**：所有角色可见全部对话
- **轮流触发**：通常按时间顺序自动切换，或用户指定

### 5.2 本项目 1+2 架构

> **核心创新**

```
┌─────────────────────────────────────────────────────────────┐
│                    OurDream.ai 聊天室                        │
│                                                              │
│  用户输入                                                     │
│    ↓                                                         │
│  World Master (前台) ── 强语义提取 ── World State Keeper (后台) │
│    ↓                                ↓                         │
│  Scene / Resolution          (读取已成立变化)                 │
│  [主要状态] [Resolution]      [State Update]                  │
│                                ↑                              │
│                         用户手动触发                          │
│                                                              │
│  World Master ── 强语义提取 ── World Event Recorder (后台)   │
│    ↓                          ↓                              │
│  Scene                  (读取重大事件)                       │
│                          [WER 历史]                            │
│                                ↑                              │
│                         用户手动触发                          │
└─────────────────────────────────────────────────────────────┘
```

**关键设计（v4.4 + 2026-07-22 审计修订）**：
- **唯一稳定前台 = WM**（保证叙事连贯性 + 玩家代理权）
- **后台 = WSK + WER**（只在手动触发时输出，避免破坏叙事）
- **通讯机制 = 强语义提取**（WSK / WER 扫描 WM Scene 叙事 + `[主要状态]` 状态栏，提取已明确写出的已成立变化；**不**依赖结构化同步块）
- **展示块隔离**：`[Resolution]` / `[Probability Check]` / 子结构块仅供用户阅读，**不**作为 WSK / WER 提取源
- **决策表 = DO / REJECT / SILENT 3 张**（每角色各 3 张；ESCALATE 已废弃）
- **接受回执不输出**；拒绝回执仅在字段不完整时输出
- **快照权威层级**：WSK 输出 = 权威；WM 临时估算 = 临时；历史值 = 兜底

### 5.3 与原生 Group Chat 的差异

| 维度 | 原生 Group Chat | 本项目 1+2 架构 |
|------|----------------|-----------------|
| 角色触发 | 平台自动或手动 | **手动触发后台** |
| 信息流 | 全部共享 | **强语义提取 + Knowledge Scope 约束** |
| 状态管理 | 角色各自维护 | **WSK 唯一权威** |
| 历史归档 | 上下文窗口 | **WER 永久归档 + Pinned Memory 手动同步** |
| 玩家代理权 | 易被后台抢话 | **WM 唯一前台** |
| NPC 反全知 | 难防 | **Knowledge Scope 强制约束 + 场景隔离** |
| 决策表 | 无 | **DO / REJECT / SILENT 各 3 张** |
| 通讯机制 | 自由文本 | **强语义提取（不用同步块）** |

---

## 6. 平台适配最佳实践

### 6.1 字段限额管理（v4.4 修订）

来自平台基线：
- **聊天室 Scenario 字段**：50,000 字符（实测，本项目承载 0-2；v4.4 迁入）
- **Private Details (Secret Instructions)**：≥50,000 字符（实测，本项目承载 0-1；v4.4 迁入）
- ~~**CI（Custom Instructions）**：15,000 字符（**建议控制在 12,000 内**以保留缓冲）~~（v4.4 迁出后未使用）
- **角色字段**：50,000 字符（**建议控制在 40,000 内**以保留 LLM 后段处理能力；1-3 = 100,000 字符）

**本项目当前状态**（v4.4 2026-07-20 实测）：
- 0-2 = — / 50,000 限额（待 ASSEMBLY_CHECKLIST 刷新；本项目使用 0-2 承载静态世界共识）
- 0-1 = 15,826 / ≥50,000 ≈ 31.65%（v4.4 迁入 Private Details 字段后限额解除）
- 1-3 = 92,419 字节 / 54,778 字符 / 100,000 限额 ≈ 54.78%（单文件最重，后段遗忘风险）
- 其余 8 文件均 ≤ 39%

### 6.2 提示词工程最佳实践

来自社区共识 + OurDream.ai 指南：

1. **明确优于全面**：具体行为模式 > 模糊形容词
2. **决策表优于长规则**：4 张紧凑表 > 25 条绝对规则（v4 已实施）
3. **代表优于详尽**：1 代表物品 + tier > 4-6 详细物品（v4 C3 已实施）
4. **唯一权威源**：跨文件规则不得重复（v4 D 已实施 0-1 / 1-1 / 2-1 / 3-1 echo 链）
5. **同步块格式统一**：最小公共字段 + 增量句法（已在 0-1 §同步块快速选择表）
6. **量化漂移监控**：6 项指标 + 4 档使用率（已在 §15.10）

### 6.3 LLM 后段遗忘的对策

来源：OurDream 平台官方文档 + 社区共识

| 对策 | 适用场景 | 本项目使用 |
|------|----------|-----------|
| **单文件不超过 1,000 行** | 减少后段失效 | 1-3 = 724 行（P1-1 索引缓解） |
| **关键规则前置** | 提高 LLM 注意力 | 1-1 §感官 token 抽屉 / §死亡公开性 L693-697 |
| **决策表代替长规则** | 降低单条规则长度 | v4 B 批次（25+18 规则 → 4 张表） |
| **同步块压缩状态** | 减少每轮需要携带的信息 | 0-1 §同步块快速选择表 |
| **快照权威替换** | 防止 WM 临时估算漂移 | 0-1 §Inventory Snapshot 权威替换 |
| **多角色审计** | 单角色可能漂移时 | WSK 审计 WM 的 Snapshot 压缩 |

---

## 7. 平台限制与已知问题

### 7.1 已知限制

| 限制 | 影响 | 本项目应对 |
|------|------|-----------|
| **平台上下文窗口有限** | 超长会话早期内容失效 | WSK + WER + Pinned Memory 三层持久化 |
| **后台不自动运行** | 需手动触发；忘记触发则同步块积累 | 1+2 架构明确分离前台/后台 |
| ~~**CI 限额 15,000**~~ | ~~极严格~~ | ~~v4.4 迁出 0-1 后此约束不再适用 0-1；0-1 现承载于 Private Details 字段（≥50K）~~ |
| **多角色共享历史** | 后台可见玩家未公开信息 | Knowledge Scope 强制约束 |
| **无内置决策表机制** | LLM 容易"逐条规则解释" | 决策表化（v4 B 批次） |
| **无内置死亡公开性** | 死亡信息传播易漂移 | Death Publicity Level 字段（v4.1 新增） |

### 7.2 OurDream 内部限制（本项目相关）

| 限制 | 影响 | 本项目应对 |
|------|------|-----------|
| **多角色共享历史** | 后台可见玩家未公开信息 | Knowledge Scope 强制约束 |

> 外部平台对比（Character.AI / SillyTavern / NovelAI / Janitor AI 等）已删除；本项目仅以 OurDream 为运行平台。

---

## 8. 本项目平台使用清单

### 8.1 字段使用

- [ ] **Custom Instructions** = ~~0-1~~（v4.4 迁出，0-1 现承载于 Private Details 字段；v4.4 后维持**空置**——不承载任何会话级配置或简版指针；决策见 SSOT §15.28）
- [x] **聊天室 Scenario 字段** = **0-2_Scenario.md**（v4.4 迁入；50,000 限额；静态世界共识层；与 Private Details 形成"世界是什么 / 世界怎么运行"二元结构）
- [x] **Private Details (Secret Instructions)** = **0-1_Private_Details.md**（15,826 字符，v4.4 2026-07-20 迁入；≥50,000 限额 ≈ 31.65% 占用）
- [x] **World Master 角色字段** = 1-1 / 1-2 / 1-3（5,940 / 10,259 / 38,805 字符）
- [x] **World State Keeper 角色字段** = 2-1 / 2-2 / 2-3（992 / 14,739 / 17,272 字符）
- [x] **World Event Recorder 角色字段** = 3-1 / 3-2 / 3-3（1,195 / 4,818 / 4,262 字符）
- [x] **Pinned Memory** = History Ledger（用户手动复制 WER 输出；**仅手动，无 API 自动化**）
- [x] **Deep Context（30 天自动）** = 平台自动管理（不依赖，但作为"中期"记忆层补充）
- [ ] **Lorebook** = **不可用**（2026-07-18 用户实测角色设置无面板；详见 §4.1 与 §9.2.2 方案 C 废弃说明）
- [ ] **API / Webhook / 本地部署** = **平台均不支持**（详见 §9.2.1）

### 8.2 平台原生机制 vs 本项目实现

| 机制 | 平台原生 | 本项目实现 | 差异原因 |
|------|----------|-----------|----------|
| **多角色** | 群聊 | 1+2 架构 | 后台不自动运行；避免抢话 |
| **长期记忆** | Pinned Memory + Auto Memory | WSK + WER + Pinned Memory | WSK/WER 提供结构化账本而非自由文本 |
| **状态管理** | 角色各自维护 | WSK 唯一权威 | 防止角色间状态漂移 |
| **历史归档** | 上下文窗口 + Auto Memory | WER 永久归档 + Pinned Memory | 100+ 日可追溯 |
| **NPC 反全知** | 靠 prompt 限制 | Knowledge Scope 字段 + 强语义提取 | 结构化强制约束 |
| **决策表** | 无 | 3 张表（DO/REJECT/SILENT） | 替代长规则；降低 LLM 漂移（v4.4 后统一为 3 表） |

---

## 9. 优化建议（基于平台知识）

> **供未来 v4.2 / v5 优化参考**

### 9.1 短期（v4.2 候选）

1. **0-1 字符释放**（已撤销）：原计划将 0-1 内容迁移以腾出 CI 限额空间；v4.4 0-1 已迁入 Private Details 字段（≥50K 限额），CI 限额约束已不存在
2. **1-3 文件内索引扩展**：当前 L699-727 列出 32 个段；可加 [段间依赖关系] 子索引，标记哪些段被其他段引用
3. **2-2 决策表精简**：当前 14,739 字符（29.5% 占用）；"依据 R1"括号占用空间，可改为"@R1"简短引用

### 9.2 中期（v5 候选）

> **2026-07-18 用户反馈澄清**：用户指出 OurDream.ai 平台**没有外部 API**、**Pinned Memory 不支持外部脚本自动化**。原文档 §9.2 "1-3 / Pinned Memory 自动化" 评估基于错误前提，现重写。

#### 9.2.1 平台能力边界（必须先确认）

| 能力 | 平台支持 | 外部访问 | 备注 |
|------|----------|----------|------|
| **OurDream Web UI** | ✓ | 仅浏览器 | 唯一访问渠道 |
| **角色创建/编辑** | ✓ | 浏览器手动 | — |
| **Pinned Memory 读写** | ✓ | **仅手动** | 无 API；不可脚本自动化 |
| **Lorebook 读写** | **✗ 无 UI**（2026-07-18 用户实测） | — | 角色设置无面板；仅第三方评测提及；不依赖 |
| **角色字段读写** | ✓ | **仅手动** | 浏览器 UI |
| **聊天历史访问** | ✓ | 浏览器查看 + 复制 | 可手动复制到本地 |
| **外部 API** | **✗ 无** | — | "platform does not support external API keys (no OpenRouter or Anthropic integration)" |
| **Webhook** | ✗ | — | 无 |
| **本地部署** | ✗ | — | 数据完全托管于平台 |

**结论**：所有"自动化"必须在浏览器 UI 限制内实现；**外部脚本无法直接读写平台数据**。

#### 9.2.2 仪表盘实现方案（4 档，已全部放弃）

由于无 API + Pinned Memory 不可外部自动化，4 张决策表 + 漂移监控指标的仪表盘有 4 档可行方案。以下为压缩汇总（详细原始内容已折叠至 git history）：

| 方案 | 机制 | 优点 | 缺点 | 状态（2026-07-18） |
|------|------|------|------|-------------------|
| **A 内嵌自检清单** | WM 每轮 Scene 后输出 `[自检报告]` 块（决策表 / KS / 死亡公开性 / 同步块字段 / 库存增量句法 5 项） | 零成本；立即可上线 | 依赖 WM 自我审计；自检块每轮 ~100 字符上下文污染 | ✗ 放弃：收益小+污染上下文 |
| **B 诊断角色**（Drift Auditor） | 新增第 4 角色，扫描聊天历史 + WSK State + WER Ledger，输出 `[Drift Report]` | 独立审计；不受 WM 主观影响 | 增加 1 角色字段占用；需额外点击 | ✗ 放弃：用户决定 1+2 架构不变 |
| **C Lorebook 决策表** | 利用 OurDream 平台 Lorebook 按关键词触发决策表条目 | 上下文不变即可调用 | 用户实测角色设置无 Lorebook 面板；平台能力未确认 | ✗ 放弃：平台不支持 |
| **D 外部 Drift Dashboard** | 用户每 5 轮手动统计关键指标，写入 `Drift_Dashboard.md` | 完全本地化；与 Pinned Memory 隔离 | 需用户手动维护；不可自动化 | ✗ 放弃：用户决定不维护外部 dashboard |

**关键事实（2026-07-18）**：本项目 **不再探索仪表盘与硬约束审计机制**。漂移监控仅依赖现有 WSK + WER + Pinned Memory 三层持久化的自我约束。

#### 9.2.4 灾备与可移植性：放弃

**结论（2026-07-18）**：灾备与可移植性探索**整体搁置**。本项目**仅以 OurDream 为运行环境**，不考虑多前端导出（V2 字符卡 / SillyTavern 导入）或跨平台兼容。`PROJECT_ANALYSIS.md` + WER 输出 Ledger 作为本地事实源；OurDream 数据丢失风险由用户自行评估。

#### 9.2.5 已被删除的错误评估

以下原 §9.2 评估基于错误前提或已被用户决定放弃，已删除：
- ~~"1-3 子地点 100+ 条目前是静态背景；可考虑拆分出高频子地点作为 Lorebook 条目"~~ → 2026-07-18 用户实测 OurDream 角色设置**无 Lorebook 面板**；该方案彻底搁置（详见 §9.2.2 方案 C 废弃说明）
- ~~"Pinned Memory 自动化：WER 输出 History Ledger 需用户手动复制；可考虑写一个外部脚本辅助"~~ → 现确认**无 API**且**Pinned Memory 不可外部自动化**（v5 重新评估见 §9.2.4 放弃）
- ~~"方案 A：内嵌自检清单（最低成本，立即可做）"~~ → 2026-07-18 放弃：收益小+自检块每轮污染上下文（详见 §9.2.2 方案 A 废弃原因）
- ~~"方案 B：诊断角色（中等成本，需新增第 4 角色）"~~ → 2026-07-18 放弃：用户决定 1+2 架构不变（详见 §9.2.2 方案 B 废弃原因）
- ~~"方案 C：Lorebook 决策表条目（平台原生，立即可做）"~~ → 2026-07-18 放弃：用户实测角色设置无 Lorebook 面板（详见 §9.2.2 方案 C 废弃说明）
- ~~"方案 D：外部手动维护 Drift Dashboard"~~ → 2026-07-18 放弃：用户决定不维护外部 dashboard（详见 §9.2.2 方案 D 废弃原因）
- ~~"§9.2.4 灾备与可移植性（v5 评估）"~~ → 2026-07-18 放弃：用户决定仅以 OurDream 为运行环境
- ~~"§9.3 长期（v6+ 候选）：多平台兼容 / 决策表可视化 / A/B 测试框架"~~ → 2026-07-18 放弃：仪表盘探索整体搁置

---

## 10. 参考资料

### 10.1 OurDream.ai 官方

- [主页](https://ourdream.ai/)
- [How to Write a Character AI Bot](https://ourdream.ai/guides/how-to-write-character-ai-bot)
- [Character Cards Explained](https://ourdream.ai/guides/character-cards)
- [Create Your Dream AI Girl](https://ourdream.ai/create)

---

## 11. 文档元信息

- **创建时间**：2026-07-18
- **创建者**：基于联网调查的提示词工程项目助手
- **来源**：OurDream.ai 官方文档与 Guides
- **用途**：项目平台层参考知识；作为未来 v4.2 / v5 / v6 优化的输入
- **更新触发**：
  - OurDream.ai 平台机制重大更新（字段限额变化、新增机制）
  - 本项目 10 文件结构或 1+2 架构变化
  - 新增 v5 / v6 优化项时补充

---

**项目管理基线**：本文件为项目平台层参考知识文档，与 [PROJECT_ANALYSIS.md](file:///d:/Mycode/AshHarbor_OurDream_QoderCN/PROJECT_ANALYSIS.md) §1 共同构成项目完整文档体系。
