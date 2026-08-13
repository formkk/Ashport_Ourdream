# edge_cases - 边界场景测试

## 场景 1：无变化可提取
WM 本轮无 Day 推进、无库存变化、无结构变化。WSK 被点击但无已成立变化可提取。

## WSK 正确输出（无变化）

```
-
```

## 场景 2：Day 推进消耗行提取
D5->D6 据点过夜。WM 在 [判定] 中写消耗行：`消耗（D5->D6）: 随身 干粮×0.5kg / 据点 大米×1kg + 木柴×2kg`

## WSK 正确输出（消耗行提取）

```
[State Update] D6-T58

Inventory Delta: 消耗 干粮×0.5kg（随身）；消耗 大米×1kg（据点）；消耗 木柴×2kg（据点）

1. Inventory State: 随身: 食品: 干粮×1.0kg；据点核心: 食品: 大米×4kg；燃料动力: 木柴×8kg
2. Party Condition: 1人；疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable
3. Relationship & Threat: 无正式关系记录
4. Map Knowledge: 工业区/N 已探索
5. Base Structure State: 质检小楼：完好
6. 近五日主要事件:
D5: 到达工业区/N/质检小楼
D6: 据点过夜消耗
```

## WSK 错误输出（- 输出但有多行内容）

```
-

Inventory State: 随身: 武器: 猎枪×1
```

## WSK 错误输出（缺少必出字段）

```
[State Update] D6-T58

Inventory Delta: 消耗 干粮×0.5kg

1. Inventory State: 随身: 食品: 干粮×1.0kg
2. Party Condition: 1人；疲劳 stable
3. Relationship & Threat: 无正式关系记录
```

验证点：
- 正例 1：`-` 输出只有一行 -> 应通过
- 正例 2：消耗行拆分为逐条 Delta，6 字段完整 -> 应通过
- 反例 1：`-` 输出但有多行 -> R6 应检出
- 反例 2：缺少 Map Knowledge / Base Structure State / 近五日主要事件 -> R4 应检出
