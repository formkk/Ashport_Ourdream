# wsk_narrative_drift_test - 叙事漂移防护测试

## 场景
WM 输出了大量叙事文本。WSK 的本能是"也用叙事风格回复"，但必须压制--输出必须是结构化账本，不是故事。

## WM 输出
WM 叙事正文：寒风从破碎的窗框灌入，你缩了缩脖子。架子上落满灰尘的罐头在手电光下泛着冷光，你伸手取下三罐，金属的凉意透过手套传来。远处似乎有什么东西倒塌了，声音在空旷的街道间回荡。
[Resolution] 无
[主要状态] D5-T55 14:00 | 工业区/N/质检小楼 | Autumn-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 远处坍塌声

## WSK 正确输出

```
[State Update] D5-T55

Inventory Delta: 获得 罐头×3

1. Inventory State: 随身: 食品: 罐头×3
2. Party Condition: 1人；疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable
3. Relationship & Threat: 无正式关系记录
4. Map Knowledge: 工业区/N 已探索
5. Base Structure State: 无据点
6. 近五日主要事件:
D5: 搜刮获得罐头×3
```

## WSK 错误输出（以叙事文本开头）

```
你走进质检小楼，架子上还有半袋大米。你把它塞进背包，又找到几发子弹。外面的风越来越冷了...

Inventory Delta: 获得 大米×2.5kg；获得 9mm×12发
```

## WSK 错误输出（包含 ## 标题）

```
[State Update] D5-T55

## Inventory Delta
获得 罐头×3

## Inventory State
随身: 食品: 罐头×3
```

验证点：
- 正例：标准账本输出，无叙事文本 -> 应通过
- 反例 1：以叙事文本开头，不以 [State Update] 或 - 开头 -> R1 应检出
- 反例 2：包含 ## 标题 -> R5 应检出
