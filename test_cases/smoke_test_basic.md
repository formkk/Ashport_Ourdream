# smoke_test_basic - 基础输出格式测试

## 场景
D5，玩家首次到达工业区质检小楼，搜刮获得物资。WSK 首次建账。

## WM 输出
WM 叙事正文：玩家进入质检小楼，在架上找到半袋大米（约 2.5kg），抽屉里有 12 发 9mm 弹药。消耗随身干粮 0.5kg。
[Resolution] 消耗（D5->D5）: 随身 干粮×0.5kg
[主要状态] D5-T55 14:00 | 工业区/N/质检小楼 | Autumn-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 无

## WSK 正确输出

```
[State Update] D5-T55

Inventory Delta: 获得 大米×2.5kg；获得 9mm×12发；消耗 干粮×0.5kg

1. Inventory State: 随身: 武器: 猎枪×1；弹药: 9mm×42发；食品: 大米×2.5kg, 干粮×1.5kg, 罐头×3；饮水: 净水×1.5kg
2. Party Condition: 1人；疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable
3. Relationship & Threat: 无正式关系记录
4. Map Knowledge: 工业区/N 已探索；质检小楼已确认
5. Base Structure State: 无据点
6. 近五日主要事件:
D5: 到达工业区/N/质检小楼，搜刮获得大米×2.5kg + 9mm×12发
```

## WSK 错误输出

```
[State Update] D5-T55

1. Inventory State: 随身: 武器: 猎枪×1；弹药: 9mm×42发
2. Party Condition: 1人；疲劳 stable
3. Relationship & Threat: 无正式关系记录
4. Map Knowledge: 工业区/N 已探索
5. Base Structure State: 无据点
6. 近五日主要事件:
D5: 到达工业区
```

验证点：
- 正例：完整 6 字段 + Inventory Delta 标签 + 正确开头 -> 应通过全部规则
- 反例：缺少 Inventory Delta: 标签 -> R3 应检出
