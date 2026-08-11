# consistency_snapshot - 一致性快照测试

## 场景
D10，玩家已在质检小楼建立据点，经过多轮交互。WSK 输出应体现自包含原则：6 字段各自输出当前实际值，不依赖历史轮次推算。

## WM 输出
WM 叙事正文：你在质检小楼整理物资，清点库存。与水源商会谢尔盖有过一次接触，他用 20 发 9mm 换了你 5 个罐头。今天消耗了 1kg 大米和 2kg 木柴。
[Resolution] 消耗（D9->D10）: 据点 大米×1kg + 木柴×2kg；Trade: 9mm×20发 <-> 罐头×5
[主要状态] D10-T120 08:00 | 工业区/N/质检小楼 | Autumn-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 无

## WSK 正确输出

```
[State Update] D10-T120

Inventory Delta: 消耗 大米×1kg（据点）；消耗 木柴×2kg（据点）；获得 9mm×20发；丢失 罐头×5

1. Inventory State: 随身: 武器: 猎枪×1；弹药: 9mm×62发；据点核心: 食品: 大米×8kg；燃料动力: 木柴×15kg
2. Party Condition: 1人；疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable
3. Relationship & Threat: 谢尔盖: 存活 / 市政厅 / 追债
4. Map Knowledge: 工业区/N 已探索；质检小楼已确认；中心区/C 已探索
5. Base Structure State: 质检小楼: 大门 完好；屋顶 完好
6. 近五日主要事件:
D6: 据点过夜消耗
D8: 与水源商会初次接触
D9: 交易 9mm×20发换取 罐头×5
D10: 据点过夜消耗
```

## WSK 错误输出（字段顺序错误）

```
[State Update] D10-T120

1. Inventory State: 随身: 武器: 猎枪×1
2. Party Condition: 1人；疲劳 stable
3. Relationship & Threat: 无正式关系记录
4. Map Knowledge: 工业区/N 已探索
5. Base Structure State: 无据点
6. 近五日主要事件:

Inventory Delta: 消耗 大米×1kg
```

验证点：
- 正例：自包含完整视图，6 字段各有当前实际值，Inventory Delta 在 6 字段之前 -> 应通过
- 反例：Inventory Delta 在 6 字段之后 -> R7 应检出
