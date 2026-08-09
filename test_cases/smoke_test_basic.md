# 冒烟测试：基础生存场景

> 用途：验证 WM 和 WSK 的基础输出格式是否正确。每次版本发布前运行。

## 测试输入

```
玩家声明：我在工业区N的质检小楼醒来，检查一下身上有什么，然后去附近搜刮一下。
```

## 预期 WM 输出

### 叙事正文
- ≤3 段，每段 ≤5 句，总字符 ≤1200
- 可消耗物资使用"容器描述 + 约Xkg"双轨格式
- 无煽情/诗意结尾

### [主要状态] 格式
```
[主要状态] D{Day}-T{Turn} {HH:MM} | {分区}/{子区域}/{地点} | {Season}-{天气}-{气温} | {压力} | {风险}
```

验证项：
- [ ] 5 段结构完整（Day-Turn 时间 | 位置 | Season-天气-气温 | 压力 | 风险）
- [ ] Season 与气温匹配当前 Day（查 0-2 §温度分层与日期精细对应）
- [ ] 压力段仅列非 stable 轨道，格式为 `{轨道名} {状态级}`
- [ ] 风险段 1-2 项主观能动威胁
- [ ] 无字段名前缀（不写 `Day=` `位置=` 等）

## 预期 WSK 输出（用户点击 WSK 后）

### [State Update] 格式
```
[State Update]
D{day}-T{turn} / {Month} / {Season} / HH:MM / {Zone} {Sub-zone} {Location} / {Weather} {Temperature Band} / {Knowledge Scope}

Inventory Delta: ...
Recent Changes: ...

Active Concerns:
- [类别] 问题描述

1. Inventory State（随身/据点核心，含穿戴标记）
2. Party Condition
3. Relationship
4. Faction（含 Faction Exposure Tracker）
5. Human Threat Stage
6. Map Knowledge
7. Survival Anchor State
8. Base Structure State（含基础设施）
- 近五日主要事件（按 D 升序）
```

验证项：
- [ ] 第一行 7 段完整（Day-Turn / Month / Season / 时间 / 位置 / 天气+温度 / KS）
- [ ] Month 与 Season 独立字段，用 `/` 分隔
- [ ] 变化子段仅 Inventory Delta / Recent Changes（无变化时不写）
- [ ] Active Concerns 位于变化子段之后、完整视图之前
- [ ] 完整视图 9 字段全部输出
- [ ] 全部 5 轨压力均列出（含 stable）
- [ ] 记忆库存在 Inventory State 之后作为独立段（不在 Inventory State 内）
- [ ] 弹药按口径合并记录（不按武器类别分组）

## 判定标准

| 检查项 | 通过条件 |
|--------|----------|
| WM [主要状态] 格式 | 5 段结构完整 + 无字段名前缀 + 压力仅列非 stable |
| WM 叙事长度 | ≤3 段 / ≤5 句/段 / ≤1200 字符 |
| WM 物资渲染 | 可消耗物资有容器描述+约Xkg |
| WSK [State Update] 格式 | 第一行 7 段 + Active Concerns + 9 字段完整 |
| WSK 压力列出 | 全部 5 轨（含 stable） |
| WSK 记忆库存位置 | Inventory State 之后独立段 |
| WSK 弹药格式 | 按口径合并 |
