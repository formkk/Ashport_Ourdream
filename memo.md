# 优化方案 memo：v1.55（已收尾）+ v1.56（已收尾）+ v2.01（待审）

> **范围**：v1.55 = 2-2 为主；v1.56 = WSK 三文件 + WM 三文件 + 0-2 + PB + enum_registry + test_cases
> **日期**：2026-08-09
> **前置**：v1.54（WSK 越界内容清理已完成）
> **原则**：v1.55 只做已明确结论的修复；需机制设计讨论的项排入 v2
> **状态**：v1.55 ✅ 已收尾；v1.56 ✅ 已收尾（WSK 反应模型简化 + 字段合并 + Relationship 统一关系轴 + D1 保暖机制落地 + Condition 全库移除）；v2.01 📋 方案待审（T2 废弃）

---

## v1.55 执行完成报告

| Task | 文件 | 状态 | 执行结果 |
|------|------|------|----------|
| Task 1 | 2-2 L7 | ✅ | DO 表时间推进句精简为"记录 WM 在 `[主要状态]` 中输出的 Day / Turn / Time（时间由 WM 唯一决定，WSK 仅记录）" |
| Task 2 | 2-2 L61 | ✅ | 删除 Elapsed，改为"1. 时间：Day、Time" |
| Task 3 | 2-2 L64 + [物资状态规则] L91-96 | ✅ | 装备属性精简为 Condition / Insulation；删除 Wetness / Attachment / Repair State；[物资状态规则] 合并精简为 3+1 条 |
| Task 4 | 2-2 L76 | ✅ | 删除 1d（Day→Month 映射）；原 1e 升为 1d"跨日与一致性：Day/Turn/Season 信任 WM，均非拒收场景" |
| Task 5 | 2-2 [据点与庇护记录规则] item 4 | ✅ | 降级规则改为"风险因素→降级状态记录，非二元否定庇护身份；仅失守/被占领/无法抵达才否定" |
| Task 6 | 2-2 [据点与庇护记录规则] item 5 | ✅ | 持续代价 + 长期驻留字段合并为单条 5 字段（Occupancy / Supply-Sanitation / Maintenance / Security-Exposure / Heat-Dryness） |
| Task 7 | 0-2 / 1-3 / 2-2 / 2-3 / enum_registry.json | ✅ | Month 全面去除（含扩展清理，见下） |

### Task 7 扩展清理（验证阶段发现的遗漏）

原 Task 7 计划只列了 [季节锚点] / [月份推进规则] / [固定取值] 等显式 Month 字段。验证阶段全库 grep 发现两类遗漏，已一并清理：

1. **[温度分层与 5 轨压力联动] 季节温度参考**（0-2 L270-273 / 1-3 L777-780）：
   `冬（12-2 月）` → `冬`；`春（3-5 月）` → `春`；`夏（6-8 月）` → `夏`；`秋（9-11 月）` → `秋`
   （[温度分层与日期精细对应] 表已提供权威 Day→Season→温度层 映射，日历月份属冗余气候注释，与 Task 0"真实月份无意义"决议冲突）

2. **[天气-季节可用性矩阵]**（0-2 L284-285）：
   `Heavy Rain 与 Storm 集中于 7-8 月` → `集中于盛夏`；`Sleet 从 11 月开始混入` → `从深秋开始混入`

3. **enum_registry.json 陈旧条目**：
   删除 `current_month` 枚举（authority 指向已删除的 §月份推进规则，12 个英文月份值，derivation_rule 为已删除的 Day→Month 映射）。清理后枚举总数 11→10。

---

## Task 0：Day→Month→Season 链条验证（前置讨论）

### 验证问题

WM 是时间决定者和推进者，WSK 只是记录者。WM [主要状态] 只输出 Day-Season，不输出 Month。已知 Day 决定 Month、Month 决定 Season、Season 影响天气系统。需验证：
1. Season 是否能由 Day 推断出来？
2. Season 的转变如何触发？
3. WM 有没有根据 Day 判断 Month 的表格？

### 验证结果

**1. Day → Season：✅ WM 有内联表**

1-3 L788-801 有 [温度分层与日期精细对应（D1 锚定）] 表（标记"与 0-2 §[温度分层与日期精细对应（D1 锚定）] 一致"），内联完整：

| Day 范围 | Season | 默认温度层 |
|---------|--------|----------|
| D1-D15 | Autumn | Cool |
| D16-D31 | Autumn | Cool ~ Cold |
| D32-D45 | Autumn | Cold |
| D46-D61 | Autumn | Cold ~ Bitter Cold |
| D62-D92 | Winter | Bitter Cold |
| D93-D120 | Winter | Bitter Cold |
| D121-D151 | Winter | Cold ~ Bitter Cold |
| D152-D181 | Spring | Cold ~ Cool |

Season 是 Day 的确定性查表函数，WM 可从自身字段直接推导。

**2. Season 转换触发机制：Day 跨越表中边界**

- Autumn → Winter：Day 从 D61 → D62（对应 11月→12月，即 0-2 [月份推进规则] 的 `D62-D92 = 12月（冬开始）`）
- Winter → Spring：Day 从 D151 → D152（对应 2月→3月，即 `D152-D181 = 3月（春开始）`）
- 1-3 L768 明确："季节按灾变后第 3 年的自然年度推进，与官方 Day 推进保持一致；季节转换由 WM 在 [主要状态] 中直接体现"
- Day 推进触发条件（1-3 L22）：用户明确"第二天/次日/天亮"→ Day+1；角色夜间睡眠并醒来 → Day+1；WM 自然叙事跨日 → Day+1
- **结论**：Season 转换不是 WM 独立决定，而是 Day 推进的自动结果。WM 推进 Day → Day 跨越表中边界 → Season 自动切换 → WM 在 [主要状态] 中体现新 Season

**3. WM 有没有 Day→Month 表：❌ 1-3 未内联**

- 0-2 L253-255 有 [月份推进规则]：`D1-D31=10月；D32-D61=11月；D62-D92=12月；D93-D120=1月；D121-D151=2月；D152-D181=3月`
- 1-3 L790 引用了 `§月份推进规则`（"Day->月份推导以 `§月份推进规则` 为唯一权威"），但 **1-3 没有内联该节**
- 1-3 有 Month→Season 对应（L770：`冬=12-2月；春=3-5月；夏=6-8月；秋=9-11月`），但这只给出月份范围，不能从 Day 精确推导到具体月份
- **结论**：WM 有 Day→Season 表（内联），但无 Day→Month 表（引用 0-2 但未内联）。这是 WM 侧的自包含缺口

**4. WM [主要状态] 不输出 Month**

[主要状态] 格式（1-1 L22）：`D{Day}-T{Turn} {时间} | {位置} | {Season}-{天气}-{气温} | {压力} | {风险}`

WM 输出：Day、Turn、Time、Season、Weather、Temperature。**不输出 Month**。

**5. 三表一致性验证：✅ 对齐**

| Day 边界 | 月份推进规则（0-2） | 温度分层表（1-3） | 季节-月份对应（1-3 L770） |
|---------|-------------------|------------------|------------------------|
| D61→D62 | 11月→12月 | Autumn→Winter | 12月=冬 ✅ |
| D151→D152 | 2月→3月 | Winter→Spring | 3月=春 ✅ |

三表在关键边界点对齐，无矛盾。

### 完整链条

```
WM 推进 Day（叙事触发：睡眠/"次日"/自然跨日）
  → WM 查 1-3 内联 [温度分层与日期精细对应] 表 → 确定 Season + 温度层
  → WM 输出 [主要状态]：Day / Turn / Time / Season / Weather / Temperature（无 Month）
  → WSK 读取 WM 的 Day + Season
  → WSK 查 2-2 L76 内联 Day→Month 映射 → 推导 Month
  → WSK 输出 [State Update]：Day / Turn / Month / Season / Time / ...（含 Month）
```

### 验证结论

1. **Season 能由 Day 推断**：✅ WM 有 1-3 内联表，Season 是 Day 的确定性函数
2. **Season 转换由 Day 推进自动触发**：不是 WM 独立裁定，而是 Day 跨越表中边界的结果
3. **WM 无 Day→Month 表**：1-3 引用 0-2 §月份推进规则 但未内联——自包含缺口
4. **WM 不输出 Month**：[主要状态] 格式只有 Day/Turn/Time/Season/Weather/Temperature
5. **Month 零机制依赖**：天气/温度/5 轨/消耗投影/时间推进/据点代价/势力追踪均不读取 Month

### Task 0 决议：全面去除 Month

经 Task 0 验证，Month 在系统中是典型的"零价值复杂度"：

- **WM 不输出 Month**，Month 只存在于 WSK [State Update] 输出格式
- **零游戏机制依赖 Month** — Day 决定时间点，Day 通过 [温度分层与日期精细对应] 表决定 Season，Season 决定天气系统。Month 是纯传递链中的冗余环节
- **后末日设定中真实月份无意义** — 幸存者关心"第几天"和"什么季节"，不关心"几月"
- **Month 制造了自包含缺口** — 1-3 引用 §月份推进规则 但未内联，去除 Month 后此缺口自动消失

**去除后的时间链**：
```
WM 推进 Day（叙事触发：睡眠/"次日"/自然跨日）
  → WM 查 1-3 内联 [温度分层与日期精细对应] 表 → 确定 Season + 温度层
  → WM 输出 [主要状态]：Day / Turn / Time / Season / Weather / Temperature
  → WSK 读取 WM 的 Day + Season
  → WSK 输出 [State Update]：Day / Turn / Season / Time / ...（无 Month）
```

**去除范围**（详见 Task 7）：
- 0-2：删除 [月份推进规则]；季节-月份对应删除月份只留 Season 定义；"10月1日"→"秋季开局"
- 1-3：同步 0-2 处理；删除 §月份推进规则 引用
- 2-2：删除 L76（1d）Day→Month 映射；L77（1e）简化为不含 Month
- 2-3：第一行格式删除 `{Month} /`；[固定取值] 删除 Current Month 枚举；示例删除 "October"

**对方案的影响**：
- v2-1（Month 推导 WM 侧自包含缺口）→ **消除**，不再需要讨论
- Task 4（跨日一致性重写）→ 简化，不再需要提 Month
- Task 0 验证结论 4（"WSK 侧设计正确"）→ 修订为"WSK 的 Month 推导不必要，应去除"

---

## v1.55 执行项（7 项）

### Task 1：DO 表时间推进句精简（memo 1）

**文件**：2-2 L7

**问题**：DO 表第 1 行"作为唯一硬状态源，记录 WM 已决定的时间推进（时间由 WM 唯一决定，WSK 不验证）"——"作为唯一硬状态源"在 [身份] 已声明；"已决定的时间推进"语义模糊；括号约束在 2-1 L9 和 2-2 L74 已重复。

**改为**：
```
记录 WM 在 `[主要状态]` 中输出的 Day / Turn / Time（时间由 WM 唯一决定，WSK 仅记录）
```

---

### Task 2：删除 Elapsed（memo 2）

**文件**：2-2 L61

**问题**：`Elapsed` 无定义、无输出格式、无枚举值、无引用。是遗留死字段。

**改为**：`1. 时间：Day、Time`

---

### Task 3：装备属性精简 + [物资状态规则] 合并（memo 3 + memo 6 合并）

**文件**：2-2 L64 + [物资状态规则] L91-96

**问题**：
- L64 声明 5 个装备属性（Condition / Wetness / Insulation / Attachment / Repair State），但多数无清晰枚举或实际效用
- Wetness：逐物品湿度追踪粒度过细，LLM 难以持续维护；体表湿度是 5 轨（体温轨）的事 → **删除**
- Insulation：静态属性，与体温轨有潜在联动，但是否应由 WSK 追踪需讨论 → **保留，排入 v2-4 讨论**
- Attachment：战术配置，属 WM 决策领域 → **删除**
- Repair State：与 Condition 完全重叠（修复 = Condition 改善）→ **删除**
- L64 与 [物资状态规则] 两处定义不一致（L64 有 Repair State 无 Filter Remaining；[物资状态规则] 反之）
- [物资状态规则] L4"枪械价值应受弹药、弹匣、附件和维护状态影响"是 WM 交易裁定逻辑，不是 WSK 记账规则

**改动**：
1. L64 改为：`库存：弹药、食物、水、药品、工具、燃料、过滤器、建材，以及随身 / 据点核心 / 记忆库存（装备 Condition / Insulation 作为物品条目属性记录在 Inventory 内）`
2. [物资状态规则] 精简为：
   ```
   [物资状态规则]
   1. 关键物资应尽量记录 Condition：Pristine / Worn / Damaged / Badly Damaged / Ruined
   2. 衣物和装备应尽量记录 Insulation
   3. 污染区相关物资应记录 Filter Remaining 或防护状态
   3a. 若本轮已明确形成污染暴露、防护损耗、滤材剩余变化、防护失效、脱离污染环境或相关恢复窗口,应写入 Recent Changes；不要在完整视图里单列污染字段。
   ```
3. 删除原 L2 中的 Wetness（保留 Insulation）、原 L4（枪械价值/附件/维护状态）

---

### Task 4：跨日与一致性重写（memo 5，按 Task 0 决议修订）

**文件**：2-2 L76-77（1d + 1e）

**问题**：1d 整条是 Day→Month 映射（按 Task 0 决议去除 Month，整条删除）；1e 表述混乱且含 Month 引用。

**改动**：
1. 删除 1d 整条（Day→Month 映射 + 推导规则）
2. 1e 改为（原 1d 删除后，1e 顺升为 1d）：
```
1d. 跨日与一致性：Day / Turn / Season 信任 WM `[主要状态]` 输出，WSK 不判定冲突、不验证跨日。Day / Turn / Season 均非拒收场景。
```

---

### Task 5：庇护点降级规则修正（memo 7）

**文件**：2-2 [据点与庇护记录规则] L106（item 4）

**问题**：当前规则把所有负面条件（漏雨/潮湿/霉菌/单出口/火光暴露/尸体污染/被盯梢/临时封锁/失守/无法持续补给）都当作二元否定条件——出现任何一个就否定"稳定庇护点"身份。但现实中大多数是风险因素（应降级状态），只有"失守/被占领/无法抵达"才真正否定庇护身份。

**改为**：
```
4. 若地点出现漏雨、潮湿、霉菌、单出口、火光暴露、尸体污染、被盯梢、临时封锁或无法持续补给等已成立风险,应在 Base / Shelter State 中降级记录（Security / Exposure 或 Maintenance Pressure 恶化），但不自动否定庇护身份。仅当地点失守、被正式占领或彻底无法抵达时，才不再按庇护点沿用。
```

**注**：降级状态的记录规则在 v1.55 完成；降级后与游戏机制的联动（WM 叙事响应/Active Concerns 触发/5 轨压力影响/消耗投影修正）排入 v2-5 讨论。

---

### Task 6：持续代价 + 长期驻留字段合并（memo 8 + memo 9 合并）

**文件**：2-2 [据点与庇护记录规则] L107-108（item 5 + item 6）

**问题**：L107 说"要记持续代价"但没说记什么/记到哪/怎么联动；L108 定义字段但与 L107 分离。两者是同一主题的两面，应合并。完整的机制联动设计（消耗投影/Inventory/5 轨/Active Concerns 联动）排入 v2。

**改为**（合并 item 5 + item 6）：
```
5. 长期驻留据点持续代价：若 WM Scene 叙事明确形成长期驻留 / 多人共住 / 夜间烧火 / 伤员收容 / 稳定囤货 / 固定守点等持续消耗资源的据点结果,应在 Base / Shelter State 中记录以下字段,不只记"可住"：
   - `Occupancy / Residency Load`（人数 → 喂入消耗投影 `{N}人`，见 Extra Details §[压缩规则] 消耗投影）
   - `Supply / Sanitation Strain`（补给 / 卫生压力）
   - `Maintenance Pressure`（维护负担：夜间烧火 / 固定守点增加燃料消耗与暴露风险）
   - `Security / Exposure`（安全 / 暴露：火光 / 固定守点 / 被盯梢导致暴露上升）
   - `Heat / Dryness`（保暖 / 干燥：多人共住影响湿气与温度）
```

---

### Task 7：全面去除 Month（Task 0 决议执行）

**文件**：0-2、1-3、2-2、2-3（4 文件跨文件改动）

**依据**：Task 0 验证确认 Month 零机制依赖、WM 不输出 Month、后末日设定中真实月份无意义。

**改动明细**：

**0-2_Scenario.md**：
1. 删除 [月份推进规则] L253-255 整节（3 行）
2. L249 `季节与月份对应：冬 = 12-2 月；春 = 3-5 月；夏 = 6-8 月；秋 = 9-11 月` → 删除（Season 已由 [温度分层与日期精细对应] 表从 Day 直接确定，无需月份中转）
3. L250 `D1 锚定日期 = 10月1日（灾变后第 3 年的开局日）` → `D1 锚定 = 灾变后第 3 年秋季开局日`
4. L251 `"10月初、秋初、灾变后第 3 年开局"` → `"秋初、灾变后第 3 年开局"`
5. L293 `Day→月份推导以 §月份推进规则 为唯一权威` → 删除该句

**1-3_WorldMaster_Extra_Details.md**：
1. L771 同 0-2 L249 处理（删除季节-月份对应）
2. L772-773 同 0-2 L250-251 处理
3. L790 `Day->月份推导以 §月份推进规则 为唯一权威` → 删除该句

**2-2_WorldStateKeeper_Additional_Personality_Details.md**：
1. 删除 L76（1d）整条（Day→Month 映射 + 推导规则）— 与 Task 4 合并执行
2. L77（1e）简化 — 与 Task 4 合并执行

**2-3_WorldStateKeeper_Extra_Details.md**：
1. L18 第一行格式：`D{day}-T{turn} / {Month} / {Season} / HH:MM / ...` → `D{day}-T{turn} / {Season} / HH:MM / ...`
2. L18 删除 `Month 与 Season 是独立字段，必须用 / 分隔（October / Autumn），不允许省略分隔符` 句
3. L18 删除 `Month/Season 推导规则见...§[环境记录规则]` 句，改为 `Day/Turn/时间/Season 以 WM [主要状态] 输出为准`
4. L26 示例：`D5-T55 / October / Autumn / 10:55 / ...` → `D5-T55 / Autumn / 10:55 / ...`
5. L113 [固定取值]：删除 `Current Month: January / February / ... / December` 整行
6. L127 [正式提交顺序] 第一行格式：同步删除 `{Month} /`

---

## v1.55 验证清单

- [x] 7 项改动完成后运行 `gen_ref_graph.py`（无悬挂引用）— ✅ 断链引用 0；孤立章节 77（属正常，多为内联使用未 §引用）
- [x] 运行 `validate_enums.py`（枚举一致）— ✅ 未发现枚举一致性问题；枚举总数 11→10（current_month 已删）
- [x] 检查 [物资状态规则] 删除项无外部 §引用 — ✅ ref graph 0 断链，Wetness/Attachment/Repair State 无外部引用
- [x] 检查 Elapsed 删除后无残留引用 — ✅ 全库 grep `Elapsed` 无匹配
- [x] 全库搜索 `Month|month|月份|October|November|December|January|February|March` 确认无残留 — ✅ 无残留（含扩展清理：`\d+\s*月` / `月）` 模式亦清零）
- [x] 检查 0-2/1-3 [温度分层与日期精细对应] 表未受影响（Day→Season 映射保留）— ✅ 0-2 L287-299 / 1-3 L788-800 完整保留 8 行 Day 范围映射
- [x] git diff 确认净减行数 — 0-2(±23) / 1-3(±15) / 2-2(±34) / 2-3(±7) / enum_registry.json(-11)；注：`real_output.md` 的 422 行变动属无关运行日志，非 v1.55 范围

### 全库扫描遗留（v1.55 Task 7 范围外，运行时不影响）

Prompt_File/ 运行时文件已 100% 清零。全库扫描在以下非运行时文件发现 Month 引用，按性质分类：

**A. 需更新（设计文档与测试，描述已失效的 Month 机制）— ✅ 已清理**：
- `PROJECT_BLUEPRINT.md` L78（原则③ 示例 Month→Season 查表）/ L81（实证加注 v1.55 去除）/ L1378（常见错误加注 v1.55）/ L1561（changelog 加注废弃）— 已更新；L914 "2 合 9mm/月" 是月费成本，保留
- `PROJECT_BLUEPRINT.md` 头部 L10 "最后更新" v1.54→v1.55；§20.2 新增 v1.55 变更日志条目 — 已更新
- `OURDREAM_PLATFORM_REFERENCE.md` L84 — 引用示例 §月份推进规则 → §季节锚点，已更新
- `test_cases/edge_cases.md` L14/L25、`test_cases/smoke_test_basic.md` L35/L55-56 — 测试用例 Month 校验已删除/改为 Season 校验

**B. 历史记录（point-in-time 审计快照，不应回改）— 保留原貌**：
- `审计历史记录.md` L250/L413/L423、`全库对齐审计报告_20260806.md`、`全库对齐审计报告_第三轮_20260807.md`、`OPTIMIZATION_ROADMAP_v1.md` — 记录历史状态/决策，保留

**C. 无关（自然语言/平台通用说明）— 保留**：
- `MrGeekStar State Trackers Definitive Guide.docx.md` L366（平台通用 date tracking 说明）、`The Unnecessarily In-Depth OurDream Character Creation Guide.md` L1969（"in months" 自然语言）

---

## v1.55 收尾

v1.55（Month 去除 + WSK 记账层精简）已全部完成并验证：
- 7 项任务 + Task 7 扩展清理（气候注释 / enum_registry）+ A 类文档同步（PB / test / platform）+ PB §20.2 变更日志
- 验证：ref_graph 0 断链 / enum 通过（10）/ Prompt_File Month 100% 清零
- v1.54 历史缺口：v1.54（WSK 越界清理，commit 4491fe5）未入 PB §20.2，保留缺口不回补（避免改写已提交历史）

---

## v1.56 执行完成报告

> **日期**：2026-08-09
> **来源**：2-3 审计 + 用户讨论中确认的 WSK 系统简化 + D1 保暖机制设计
> **范围**：WSK 三文件（2-1/2-2/2-3）+ WM 三文件（1-1/1-2/1-3）+ 0-2 + PB + enum_registry + test_cases

### 改动总览

| 改动 | 说明 |
|------|------|
| WSK 反应模型 5->2 | 删除 [Commit Rejected] 及 4 种拒绝原因；有变化输出完整视图，无变化输出空白标记 `-`；缺失字段标 `未确认` 沿用，不拒绝 |
| Recent Changes 移除 | 变化子段从 2 个（Inventory Delta + Recent Changes）缩减为 1 个（仅 Inventory Delta）；标注迁移到对应字段 |
| 完整视图 8->6 字段 | 旧 3（Relationship）+ 4（Faction）+ 5（Human Threat Stage）合并为 3（Relationship & Threat） |
| Relationship 统一关系轴 | Trust 0-100 + Hostility 0-100 -> Relationship 7 档定性（依恋/完全信任 / 亲密/信任 / 好感 / 中立 / 冷漠 / 敌意 / 仇恨）；适用于所有个体与势力；WSK 语义升降档，不做数值记录 |
| Faction Exposure Tracker 移除 | 删除 [势力暴露追踪规则] 整节；Suspicion Level L0-L4 / Last Exposed Day / Last Trigger Type 全部移除 |
| PAM v1.1->v1.2 | 增加 Phase 1 执行证据约束 + 1.6 跨文件枚举一致性检查 + 形态黑名单 2.10 + 陷阱 #21/#22 |
| D1 保暖机制落地 | 1-3 新增 [保暖修正] 子节（保暖值 5 档优/良/中/弱/差修正有效温度层）+ 1-2 新增 [保暖裁定] 节（WM 每轮实时裁定，不持久化） |
| Condition 全库移除 + Component 生命周期简化 | Condition 枚举（Pristine/Worn/Damaged/Badly Damaged/Ruined）全库删除；Component 生命周期简化为"组件名 + Type + Role + 状态描述（自然语言）" |
| T1 据点消耗机制 | 1-1 Resolution 每轮必出 + Day 推进消耗行 / 1-2 据点消耗规则 / 1-3 Resolution 格式更新 |
| D2 据点损耗机制最终版 | 三级状态+统一Day触发+天气/人为Probability Check+二级后果映射+MP指示器 |
| D3 Relationship升降档指引 | 1-2升降档触发表+跨档跳跃+势力差异 / 2-2初始档中立->冷漠+单向记录 |
| D4 据点暴露机制 | 1-2暴露来源+后果联动 / 2-3 Exposure三档定义 / 2-3固定取值加枚举 |

### 受影响文件

| 文件 | 改动 |
|------|------|
| 2-1 Scene | 沉默协议简化 / 输出白名单 / LLM 心理预设 |
| 2-2 APD | 决策表 3->2（删 REJECT）/ 关系规则重写 / 删势力暴露追踪规则整节 / 合并记录内容 / 删除物品 Condition 枚举 + Component 生命周期简化 / D3 初始档中立->冷漠+单向记录 |
| 2-3 Extra | 输出白名单 / 模板声明 / 提取纪律 / 最低提交标准 / 完整视图字段合并 / 固定取值增加 Relationship / 2-3 审计修复 28 项 / 删除结构 Condition 引用 / D4 Exposure三档定义+固定取值加枚举 |
| 1-1 Scene | 关系追踪核心 三轴->两轴 / [Resolution] 每轮必出 + Day 推进消耗行 |
| 1-2 APD | Trust/Hostility -> Relationship / NPC 行为阈值表引用更新 / 新增 [保暖裁定] 节 / 新增 [据点消耗规则] / [据点损耗机制]最终版：三级状态+统一Day触发+OR关系+二级后果映射 / D3 升降档触发表+跨档跳跃+势力差异 / D4 暴露来源+后果联动 |
| 1-3 Extra | [NPC Trust 行为阈值表] -> [NPC Relationship 行为阈值表] 5 档->7 档 / 常驻角色状态引用更新 / 新增 [保暖修正] 子节 / 锚点表删除 Condition + Delta 改为状态描述 / [Resolution 块] 格式增加消耗行 |
| 0-2 Scenario | 人际与信息条 Trust -> Relationship |
| PROJECT_BLUEPRINT.md | 9 处更新 / 头部 changelog v1.56 / PAM v1.2 |
| enum_registry.json | 删除 exposure_response_level / 新增 relationship / 新增 warmth_level（保暖值） |
| test_cases/ | smoke_test_basic + edge_cases 适配新 WSK 模型 |

### 遗留项

- ~~**1-3 §[身份暴露风险]**（L610-621）：WM 侧的劫掠者伪装暴露 L0-L4 响应机制仍存在。用户已指示"去除暴露机制"，但该节涉及 WM 叙事机制设计（伪装交易/采购/灰色接触的后果连锁），需用户确认是否一并删除或保留伪装机制但去除 L0-L4 框架。~~ ✅ 已处理：保留伪装触发机制（Probability Check），删除 L0-L4 分级响应，改为"暴露后 Relationship 降为敌意/仇恨 + 自然后果"。

---

## v1.56 补充：PAM v1.2 工具化 + 规则更新

> **日期**：2026-08-10
> **来源**：PAM v1.2 工具化实施 + 首次全库机械核验发现
> **范围**：PROJECT_BLUEPRINT.md PAM 节 + tools/ 全部脚本 + 2-3 L157 + 1-2 bold 清除

### 改动总览

| 改动 | 说明 |
|------|------|
| PAM 2.10 角色卡 SSOT 例外 | 角色卡字段（1-x/2-x）中指向聊天室级字段（0-x）的 SSOT 指针保留不删--WM 运行时不反查聊天室字段，角色卡必须内联数据（陷阱 #20 对策），SSOT 指针供维护追溯。仅聊天室级字段中的 SSOT 指针判定为违规 |
| PAM 1.3 角色卡内联例外 | 角色卡从聊天室级字段内联的数据节不计为重复--同理陷阱 #20 对策 |
| P0 死链修复 | 2-3 L157 `§[据点组件锚点表]` 改为 `§[据点结构基线]`（正确节名）+ 举例改用中文（大门/暗道/瞭望点） |
| 1-2 bold 清除 | [据点消耗规则] + [据点损耗机制] 14 处 `**bold**` 子标题标记全部清除（PAM 2.8 格式化石） |
| validate_enums.py 重写 | 1.6 跨文件枚举比对核心逻辑重写：子串搜索代替 `/` 分割，消除 75% 误报 |
| format_lint.py 新建 | 1.4 格式合规 + 2.8/2.9/2.10 形态黑名单扫描；SSOT 扫描区分角色卡 vs 聊天室级 |
| detect_duplicates.py 新建 | 1.3 SSOT 重复检测；角色卡 <- 聊天室内联自动跳过 |
| gen_ref_graph.py 增强 | 1.1 口语化引用检测（陷阱 #14）+ 误报过滤 |
| run_audit.py 新建 | 统一入口，串联全部脚本，输出标准化执行证据模板 |

### 首次全库机械核验结果

| 检查项 | 发现 | 状态 |
|--------|------|------|
| 1.1 断链引用 | 0（已修复 1 处） | ✅ |
| 1.1 口语化引用 | 0 | ✅ |
| 1.2 弃用术语 | 0 | ✅ |
| 1.3 重复检测 | 0 违规（8 对有意内联已跳过） | ✅ |
| 1.4 bold | 1（0-3 误报） | ✅ |
| 2.10 SSOT | 0 违规（12 处角色卡内已跳过） | ✅ |
| 1.6 枚举一致性 | 0 真实问题（5 项上下文引用误报） | ✅ |
| 1.5 孤立章节 | 77（P2 信息性，待人工确认） | ⚠️ |

---

## v2.01 优化方案

> **来源**：v1.55 遗留的 5 项 v2 排期项转化为可执行方案
> **边界原则**：WSK = 账本记录者（记会变化的状态），WM = 裁定者（推演机制效果）。联动设计按此边界划分——WSK 只提供数据与投影，机制推演与叙事响应归 WM。
> **状态**：📋 方案待审（2026-08-09）

### v2.01-T1：持续代价 + 庇护降级 联动职责澄清（v2-1 + v2-5 合并）

**问题**：v1.55 Task 5/6 完成了字段定义，但联动职责未划清。

**决议（基于 WSK=账本 / WM=裁定 边界）**：
1. **消耗联动**：持续代价字段（Occupancy / Strain / Pressure 等）是消耗投影的 **INPUT**，不是独立计算。WSK 已通过 `{N}人` 喂入消耗投影（2-3 [压缩规则]）。日常驻留增量消耗（多人共住 / 伤员收容 / 固定守点）由 WM 在叙事中体现，WSK 不量化、不自动扣减 Inventory。
2. **Inventory 联动**：消耗投影是估算值（≈X 天），**≠ Inventory 实际扣减**。Inventory 只接受 WM 叙事中明确写出的消耗 / 转移。需明确此区分，防止 WSK 误把投影当扣减。
3. **5 轨联动**：纯 WM 裁定（多人共住 / 卫生恶化 → 精神 / 感染轨）。WSK 不介入。已由 v1.53 5 轨权威迁移确立。
4. **Active Concerns**：现有规则已覆盖——WSK 扫描全部字段，[据点] 类别捕获降级 / 持续代价恶化（"正在活跃、需 WM 优先处理"）。无需新增阈值。
5. **WM 联动**：WM 读取 WSK 持续代价 + 降级状态 + 消耗投影，自行叙事响应（物资紧缺 / 被盯梢 / 设施故障）。属 WM 侧，不需 WSK 改动。

**改动**（2-2 [据点与庇护记录规则] item 5 末尾 + 2-3 [压缩规则] 消耗投影段）：
- 2-2 item 5 末尾加注：`以上字段为消耗投影输入与降级状态记录；实际 Inventory 扣减与 5 轨推进由 WM 裁定，WSK 不自动结算。`
- 2-3 消耗投影段加注：`消耗投影为估算值，不等于 Inventory 实际扣减；Inventory 只接受 WM 叙事中明确写出的消耗/转移。`

**状态**：✅ 可执行（纯职责澄清，无机制变更，无枚举/引用影响）

---

### v2.01-T2：势力暴露升级标准迁移到 WM（v2-3 部分）

**问题**：升级定性标准（"单一异常→L1 / 多指标叠加→L2 / 异常反复→L3"）当前写在 2-2 [势力暴露追踪规则]，但这是 WM 裁定标准，WSK 只记录。违反 WSK=记录 / WM=裁定 边界。

**决议**：标准迁移到 WM 侧；WSK 只保留"依据 WM 叙事事实记录"的职责声明。

**改动**：
- 2-2 [势力暴露追踪规则]：删除升级定性标准句，改为 `WSK 依据 WM Scene 叙事的识别/升级/反水事实记录，不自行判定升级（升级定性标准见 WM 字段 §[身份暴露风险]）`
- 1-3 [身份暴露风险]：补入升级定性标准（单一异常→L1 / 多指标叠加→L2 / 异常反复累积→L3）+ 触发类型扩展（被目击犯罪 / 被辨认 / 情报泄露 / 阵营反水）
- 后果联动（L3→巡逻 / L4→袭击）：**defer 到 v2.02**（需 WM 叙事指令设计）
- 多势力扩展（码头帮 / 商会等）：**defer**（需用户决定 scope）

**状态**：❌ 废弃（v1.56 已整体移除 Faction Exposure Tracker / Suspicion Level，本任务前提不复存在）

---

### v2.01-T3：Insulation 从 WSK 移除（v2-4 账本侧）

**问题**：v1.55 Task 3 保留 Insulation 在 WSK，但 WSK 不应持有静态属性。

**决议（用户确认）**：Insulation 是衣物**静态属性**（一件冬衣保暖值不变），WSK 定位 = "记会变化的状态"（PB §0.5 原则③），静态属性不属 WSK 账本。从 WSK 移除。

**改动**（仅 WSK 账本侧，不涉及机制设计）：
- 2-2 L64：`（装备 Condition / Insulation 作为物品条目属性记录在 Inventory 内）` → `（装备 Condition 作为物品条目属性记录在 Inventory 内）`
- 2-2 [物资状态规则] item 2：删除 `衣物和装备应尽量记录 Insulation`

**注**：Insulation 作为**游戏机制**（如何修正体温轨映射、Condition 降级联动、枚举化等）不在本任务范围，排入 v2.02+ 讨论（见下）。移除后 Insulation 暂时从提示词消失——当前 WM [温度分层与 5 轨压力联动] 本就未引用 Insulation，故运行时无影响；v2 机制设计完成后再补入 WM 侧。

**状态**：✅ 可执行（用户已确认移除）

---

### v2.01-T4：库存规则梳理评估（v2-2）

**问题**：库存规则 ~50 条分布在 2-2（6 节）+ 2-3（3 节），职责交叉。

**评估结论**：**不建议大重构**
- 当前结构已通过 v1.53 / v1.54 / v1.55 三轮验证，运行时合规
- 大规模条目移动（2-2 ↔ 2-3）风险高，收益是结构整洁而非运行时改善
- 用户原则"prioritizes runtime effectiveness over documentation" → 重构属文档整洁，非运行时价值

**可执行小项**：
- Filter Remaining：评估后建议**保留在 [物资状态规则]**（它是物品属性，与 Condition 同层，不是污染规则）
- 审计职责：当前 2-2 [库存分类与精简原则] 9b 已有审计条款，无需再迁移

**状态**：✅ 评估完成，结论 = 不大重构；Filter Remaining 保留原位

---

### v2.02+ 延期项

- **Insulation 游戏机制设计**（用户指定排入 v2 讨论）：衣物保暖值如何修正 [温度分层与 5 轨压力联动] 的温度档→体温压力映射（如 `Cool` 档 + 无保暖衣物 → strained；`Cool` 档 + 冬衣 → stable）；Condition 降级（Worn→Damaged）是否降低保暖效果；Insulation 枚举化（Light/Medium/Heavy/Extreme 还是自然语言）。属 WM 侧机制，设计完成后补入 1-3。
- ~~势力暴露后果联动（L3->巡逻 / L4->袭击的 WM 叙事指令设计）~~ ❌ 废弃（v1.56 移除 Suspicion Level）
- ~~势力暴露多势力扩展（码头帮 / 商会等是否建立追踪，需 scope 决定）~~ ❌ 废弃（v1.56 移除 Faction Exposure Tracker）
- 库存规则大重构（如未来规则膨胀到影响运行时再议）

---

### v2.01 执行优先级建议

| Task | 状态 | 建议 |
|------|------|------|
| T1 联动职责澄清 | ✅ 可执行 | 纯澄清，低风险，可立即做 |
| T2 升级标准迁移 | ✅ 部分可执行 | 标准迁移+触发扩展可做；后果联动 defer |
| T3 Insulation 移除 | ✅ 可执行 | 用户已确认；机制设计 defer v2.02+ |
| T4 库存梳理评估 | ✅ 已结题 | 结论=不重构，无后续动作 |
