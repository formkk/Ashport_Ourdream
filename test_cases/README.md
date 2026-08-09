# 回归测试用例集

> 本目录承载 Ash Harbor 项目的回归测试场景。每次版本发布前，用相同输入跑一遍，对比输出是否漂移。

## 用途

| 用例类型 | 文件 | 场景 | 验证目标 |
|----------|------|------|----------|
| 冒烟测试 | `smoke_test_basic.md` | 基础生存场景 | WM [主要状态] 格式 + WSK [State Update] 完整视图 |
| 边界测试 | `edge_cases.md` | 首次建账/跨日/死亡/地图外 | 边界条件下的输出完整性 |
| 一致性快照 | `consistency_snapshot.md` | 版本发布前全库审计 | 跨文件枚举/引用/术语一致性 |

## 使用方法

1. **冒烟测试**：在 OurDream.ai 平台用指定输入跑一轮，对比 WM 输出是否符合 `smoke_test_basic.md` 中的预期格式
2. **边界测试**：逐项在平台验证，记录实际输出与预期的偏差
3. **一致性快照**：在 Trae 中对全库运行一致性审计 Skill，对比上次快照是否有新问题

## 快照记录

每次测试后在 `snapshots/` 目录下记录：
```
snapshots/
  YYYY-MM-DD_vX.XX/
    smoke_result.md
    edge_result.md
    audit_result.md
```
