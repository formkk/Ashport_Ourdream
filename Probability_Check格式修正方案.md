# [Probability Check] 格式修正决议（已确认，已应用）

状态：**已应用**（v1.68）。7 处落点全部执行完毕：1-3 格式模板与三条定义句、触发流合并掷收紧、1-1 纯文本定义句、output_rules.json 权威正则、e2e_test.py（json SSOT 校验 + 4 真实样本反例自测）、SKILL.md 同步。验证 4 步全过（4 真实样本全拒、8 合规形态全过、e2e 三场景、static_audit 60/60、run_audit 无发现）。本文档保留为格式契约的历史依据与正则设计说明。

## 决议原则（用户给定）

- **P1 根因优先**：格式缺口 → 让格式定义吸收真实行为或补齐输入披露；规则空洞 → 补规则语义。不写"反例（禁止）"式补丁。
- **P2 正则优先**：可机器判定的约束全部落进 `tools/output_rules.json` 的 `format_pattern`（枚举、负向前瞻、字符类排除）；模板只留定义性表述。正则必须接入测试链（e2e 加载 json 校验），而非仅靠文字约束。

## 决议总表

| # | 决议 | 类型 | 落点 |
|---|------|------|------|
| 1 | Base 显式允许括号理由，理由内禁 `；`（字符类强制） | 格式+正则 | 1-3 / output_rules.json |
| 2 | 保留 `；` 分隔符；全部字段值用 `[^；]` 字符类强制 | 正则 | output_rules.json（+1-3 定义句） |
| 3 | Modifiers 禁 ±0（负向前瞻拦截） | 正则 | output_rules.json（+1-3 定义句） |
| 4 | 字段值排除 markdown 符号 `* # _`；`*` 来源问题作废 | 正则 | output_rules.json（+1-1 定义句） |
| 5 | Trigger 前缀枚举类名 + 同轮同类重复 `#序号`，Seed 全量可复算 | 格式+正则 | 1-3 / output_rules.json |
| 6 | 合并掷固定 world-event/npc-contact 名义，未触发压缩 Dase；情境掷为第二次独立掷 | 规则语义 | 1-3 触发流 |
| 7 | e2e_test.py 加载 output_rules.json 校验（json 成 SSOT）；顺带闭合 Dase/wear 压缩行既有缺口 | 工程 | e2e_test.py / output_rules.json |

---

## 修正 1：Base 理由入格式（方案 A 定案）

- 根因：取值理由有审计价值但无正式位置，WM 4/4 自发加括号。根因解法 = 给名分 + 字符类圈住。
- 决议：`Base: {N}（{理由，可省略}）` 为正式格式；理由内 `；` 由 `（[^；）*#_]*）` 字符类禁止。
- 1-3 L477 格式行相应更新（见"落点明细"）。
- 方案 B（反例禁令）违背 P1+P2，弃。

## 修正 2：保留 `；`，字段值 `[^；]` 强制（定案）

- 决议：不换分隔符（换 `|` 迁移成本高且与 [主要状态] 的 `|` 视觉混淆）。全部字段值在正则中用 `[^；...]` 字符类，域内出现 `；` 直接 FAIL。
- 1-3 加一句定义性分隔符纪律（见落点）。

## 修正 3：禁 ±0 修正（正则前瞻，定案）

- 决议：正则负向前瞻 `(?!...含 ±0...)` 拦截；模板一句定义"Modifiers 只列非零修正"。净零双向因素写进叙事正文，不进结构块。

## 修正 4：排除 markdown 符号（定案）

- 决议：Trigger / Base 理由 / Modifiers / Outcome 字段值字符类统一排除 `* # _`；[Move] / [判定] / [主要状态] 现有 `$` 锚定已天然拦截尾部残留，不动。
- `*` 是 WM 输出还是粘贴标记——因正则拦截而失去讨论价值，不再追究。
- 1-1 [输出结构] 加一句定义："结构块内容为纯文本，不含 markdown 标记"。

## 修正 5：Trigger 前缀类名 + `#序号`（定案）

- 决议：`Trigger: {Event Class}: {触发条件}`；类名 = [Probability Check 偏移表] 枚举（hostile-contact / npc-contact / 获得 / third-party-sighting / trade-complication / world-event / wear-weather / wear-sabotage / wear-usage / custom）。
- 同轮同类第 2 次起独立检查，类名后追加 `#2` `#3`（对应偏移表"基础偏移 + 本轮检查序号"规则），保证 Seed 全量可复算。
- Seed 复算材料闭合：类名（查偏移表）+ `#序号`（查修正偏移）+ [主要状态] 的 Day/Turn（查 Day 末两位与 Turn 个位）。缺类名 = 违规（正则直接 FAIL）。
- 不新增 `Offset: {N}` 字段（与偏移表 SSOT 重复）。

## 修正 6：合并掷收紧（定案）

- 决议：[Move] 轮的例行撞见掷不得被情境掷替代——合并掷 Trigger 类名固定 world-event 或 npc-contact；未触发压缩 Dase-1/2，触发输出完整算式（Dase-3/4）。
- 有独立触发依据的情境掷（搜刮噪音 / 追踪 / 目击等）不参与合并，作为第二次独立掷输出完整块，用情境类名 + 独立 Offset。
- 依此标准回看：样本 4 现状（单一无类名情境掷完整块、无 Dase）= 违规。正确输出 = `Dase-1`（例行掷未触发）+ 独立情境掷完整块（若 WM 判定需要）。

## 修正 7：正则接入测试链（定案）

- e2e_test.py 从 tools/output_rules.json 读取 `format_pattern`，对三个模拟场景的 [Move] / [Probability Check] / [判定] / [主要状态] 行做校验；json 成为格式 SSOT，改格式只改一处。
- 顺带闭合既有缺口：旧 PC 正则不认 Dase 压缩行与 wear 压缩行（两种合规形态），新正则补入合法分支。

---

## 权威正则（最终版，写入 output_rules.json）

```
^\[Probability Check\] (Trigger: (hostile-contact|npc-contact|获得|third-party-sighting|trade-complication|world-event|wear-weather|wear-sabotage|wear-usage|custom)(#\d+)?: [^；*#_]+；Base: \d+(（[^；）*#_]*）)?；Modifiers: (?![^；]*(?<![0-9])[+-]0(?![0-9]))[^；*#_]+；Final: \d+；Seed: \d+；Threshold: \d+；Result: (触发|未触发)；Outcome: [^；*#_]+|Dase-\d+(；Dase-\d+)*|wear-(weather|sabotage|usage): 未触发(；wear-(weather|sabotage|usage): 未触发)*|无概率事件)$
```

设计说明：
- 类名枚举 + `(#\d+)?`：修正 5；无类名 FAIL。
- `Base: \d+(（[^；）*#_]*）)?`：修正 1；理由可省略、禁 `；` 与 markdown 符号。
- Modifiers 负向前瞻 `(?![^；]*(?<![0-9])[+-]0(?![0-9]))`：修正 3；`-5` `+15` `+10` 等正常修正不受影响（`(?<![0-9])` 排除 `+10` 中的 `0`，`(?![0-9])` 排除 `-05` 中的 `0`）。
- 字段值 `[^；*#_]+`：修正 2 + 4；域内 `；` 与 markdown 符号同时拦截。
- 末尾四个合法分支：完整式 / Dase 压缩行（多个用 `；` 连）/ wear 压缩行（多个用 `；` 连）/ `无概率事件`。
- wear 触发时的完整算式块 Trigger 用 wear 类名，已被类名枚举覆盖。

---

## 落点明细（应用时逐条执行）

### 1. [Prompt_File/1-3_WorldMaster_Extra_Details.md](Prompt_File/1-3_WorldMaster_Extra_Details.md) §[Probability Check 格式模板]（L474-483）

L477 格式行：
- 原文：`` `[Probability Check] Trigger: {触发条件}；Base: {N}；Modifiers: {修正项}；Final: {N}；Seed: {N}；Threshold: {N}；Result: {触发/未触发}；Outcome: {结果描述}` ``
- 改后：`` `[Probability Check] Trigger: {Event Class}: {触发条件}；Base: {N}（{取值理由，可省略}）；Modifiers: {修正项}；Final: {N}；Seed: {N}；Threshold: {N}；Result: {触发/未触发}；Outcome: {结果描述}` ``

L477 后新增三条定义句（不写反例）：
```
- 分隔符纪律：`；` 仅为字段间分隔符；所有字段值内部一律用 `，` 或 `。`。
- Modifiers 只列非零修正；双向因素相抵为净零时不写入结构块（叙事正文可保留描写）。
- Trigger 必带 Event Class 前缀（取值 = §[Probability Check 偏移表] 类名）；同轮同类第 2 次起独立检查，类名后追加 `#序号`。Seed 复算材料 = 类名查偏移表 + `#序号` + [主要状态] 的 Day/Turn。
```

### 2. 同文件 §[势力行为档案] 触发流 item 1（L571）

- 原文：`[Move] 成立（跨 Zone/Sub-zone）或 Day 推进时触发；同轮多触发源合并为一次掷，以换区侧为准。`
- 改后：`[Move] 成立（跨 Zone/Sub-zone）或 Day 推进时触发；同轮多触发源合并为一次掷，以换区侧为准；合并掷 Trigger 类名固定 world-event 或 npc-contact，不得以情境类替代，未触发 -> 压缩为 Dase-1/2。有独立触发依据的情境掷（搜刮噪音/追踪/目击等）不参与合并，作为第二次独立掷输出完整块，用情境类名 + 独立 Offset。`

### 3. [Prompt_File/1-1_WorldMaster_Scene.md](Prompt_File/1-1_WorldMaster_Scene.md) §[输出结构]（L29-30 附近）

新增一条：`- 结构块内容（[Move] / [Probability Check] / [判定] / [主要状态]）为纯文本，不含 markdown 标记（* # _ 等）；叙事正文不受此限。`

### 4. [tools/output_rules.json](tools/output_rules.json)

`[Probability Check].format_pattern` 替换为上文权威正则（JSON 转义 `\` → `\\`）；`format_desc` 同步为：
`[Probability Check] Trigger: {类名}: {...}；Base: {N}（理由可省）；Modifiers: {...}；Final/Seed/Threshold: {N}；Result: {触发/未触发}；Outcome: {...} 或 Dase-N / wear-*: 未触发 / 无概率事件`

### 5. [tools/e2e_test.py](tools/e2e_test.py)

- 场景 C 的 PC 行改为新格式（修正 ±0 与类名）：
  `[Probability Check] Trigger: third-party-sighting: 穿越工业区开阔地带是否被第三方远距目击；Base: 15（白天开阔地人流低）；Modifiers: 开阔地+10，白天人流低-5；Final: 20；Seed: 42；Threshold: 20；Result: 未触发；Outcome: 疑似跟踪者放弃，未升级接触`
- 新增：加载 `tools/output_rules.json`，用各块 `format_pattern` 校验三个场景的全部结构块行（json 成 SSOT）。
- 新增反例自测（正则效果验证）：旧格式样例（无类名 / Base 外文本 / 域内`；` / ±0 / 尾部`*`）必须 FAIL。

### 6. [.trae/skills/output-format-validator/SKILL.md](.trae/skills/output-format-validator/SKILL.md)

L60 [Probability Check] format 行同步新格式描述。

### 7. static_audit_test.py

无直接断言涉及 PC 格式行字符串；应用后跑回归确认 60/60。

---

## 应用后回看 4 个真实样本（新规则判定）

| 样本 | 判定 | FAIL 项 |
|------|------|---------|
| 1 小屋搜刮 | FAIL | 缺类名；Outcome 域内`；`；尾部`*`（Base 括号 ✓ 合法） |
| 2 林路被跟 | FAIL | 缺类名；`-0` 修正；尾部`*` |
| 3 游客中心 | FAIL | 缺类名 |
| 4 林缘被发现 | FAIL | 缺类名；Outcome 域内`；`；尾部`*`；例行掷未以 Dase 压缩（修正 6） |

合规示范（样本 1 修正版，可直接用作模板示例）：

```
[Probability Check] Trigger: hostile-contact: 江在护林员小屋内搜刮，屋外左侧再次出现明显擦碰声，是否有人接近或已发现小屋被入；Base: 30（雨林地带声近且透）；Modifiers: 江入屋后动作收敛-5，小屋半塌有回风干扰+5，异响极近且无风+15；Final: 45；Seed: 33；Threshold: 45；Result: 触发；Outcome: 屋外确认有声源，未冲门，未现形，一瞬后复静，江未与之照面
```

## 验证计划（应用后执行）

1. 正则单测：权威正则 × {4 个真实样本（应 FAIL）、合规示范、Dase-1、wear-weather: 未触发、无概率事件（应 PASS）}
2. `python tools/e2e_test.py` — 含 json SSOT 校验与反例自测全过
3. `python tools/static_audit_test.py` — 60/60 无回归
4. `python tools/run_audit.py` — 聚合检查无新增发现
