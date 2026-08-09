# 边界测试用例

> 用途：验证边界条件下的输出完整性。逐项在平台验证。

## 用例 1：首次建账（空库存 -> 初始化）

**输入**：新对话开始，玩家首次点击 WSK

**预期**：
- [ ] WSK 输出完整 `[State Update]`（非 `[Commit Rejected]`）
- [ ] Party Condition 包含 5 轨压力状态级（首次必出）
- [ ] Inventory State 有初始随身物品（非空）
- [ ] 近五日主要事件有 D1 条目
- [ ] Day = D1-T1，Season = Autumn

## 用例 2：跨日推进

**输入**：WM 叙事中明确写到"第二天"/"天亮"/过夜后醒来

**预期**：
- [ ] WM [主要状态] Day +1
- [ ] Turn 继续累计（不归零）
- [ ] 时间设为合理时刻（06:00-08:00）
- [ ] WSK 第一行 Day 与 WM 一致
- [ ] WSK Season 与 WM [主要状态] 一致（如 D62 = Winter）
- [ ] 近五日主要事件新增当日条目

## 用例 3：死亡事件

**输入**：WM 叙事中 NPC 死亡

**预期**：
- [ ] WM 死亡叙事标注 `[知情范围: <level>]`
- [ ] 默认 知情范围 = hidden
- [ ] WSK 在 Relationship 或 Party Condition 中记录死亡
- [ ] WSK 不自行判断公开性

## 用例 4：地图外地点

**输入**：玩家到达地图外地点（如西郊石基农舍）

**预期**：
- [ ] WM 叙事中给出 Boundary Anchor / External Site / Access Route / Reachability
- [ ] WSK 第一行位置写 `地图外·{地点名}`
- [ ] WSK 完整视图中保留 External Location State
- [ ] WSK 不把地图外地点当作新九宫格分区

## 用例 5：交易场景

**输入**：玩家与 NPC 交易（如用弹药换食物）

**预期**：
- [ ] WM 叙事中写明谁付出什么、谁得到什么
- [ ] WSK Inventory Delta 记录获得/消耗
- [ ] WSK 弹药按口径记录（9mm×67发），不按武器类别
- [ ] WSK Relationship 记录 Trust 变化（数值格式 Trust=XX）
- [ ] 轻交易不展开担保/押货条款

## 用例 6：无可提取变化

**输入**：WM 叙事仅有对话/观察，无已成立状态变化；用户点击 WSK

**预期**：
- [ ] WSK 输出 `[Commit Rejected] (无可提取变化)`
- [ ] 仅一行，不附完整视图
- [ ] 保持上一份官方状态不变

## 用例 7：概率检查触发

**输入**：玩家在拾荒者活动频繁区域搜刮，WM 判定需要第三方目击检查

**预期**：
- [ ] WM 输出 `[Probability Check]` 块
- [ ] 包含 Trigger / Event Class / Base Probability / Modifiers / Final Probability / Day ID / Turn ID / Event Offset / Seed / Threshold / Result / Outcome
- [ ] Seed = (Day ID × 7 + Turn ID × 3 + Event Offset) mod 100
- [ ] 未触发时不在叙事中渲染该事件
- [ ] WSK 不因概率块而生成新账本（概率块仅供用户阅读）
