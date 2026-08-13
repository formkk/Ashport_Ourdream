#!/usr/bin/env python3
"""
端到端测试：验证 WM 输出结构符合新规则
- 4 块每轮必出
- 因果顺序：正文 -> [Move] -> [Probability Check] -> [判定] -> [主要状态]
- 标签后不换行
- 空块格式正确
"""

import re
import sys

# 模拟 WM 输出（跨日推进 + 交易 + 无移动 + 无概率事件）
SIMULATED_OUTPUT_A = """你在质检小楼里翻找了一圈，架子上还有半袋大米和一桶柴油。你把这些塞进背包，准备回去。

天亮了。你简单吃了点东西，把昨晚找到的罐头跟路过的拾荒者换了些净水。

[Move] 无
[Probability Check] 无概率事件
[判定] 消耗（D5->D6）: 随身 干粮×0.5kg / 据点 大米×1kg + 木柴×2kg（留守）；Trade: 以罐头×2换得净水×3L；代价与后果: 暴露在拾荒者面前
[主要状态] D6-T177 08:00 | 工业区/N/质检小楼 | Winter-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 strained；伤病 stable | 食物还够4天"""

# 模拟 WM 输出（无事件 + 无 Day 推进）
SIMULATED_OUTPUT_B = """你站在窗边观察了一会儿街道。没什么动静，偶尔有风吹过废铁皮。

[Move] 无
[Probability Check] 无概率事件
[判定] 无
[主要状态] D6-T178 08:15 | 工业区/N/质检小楼 | Winter-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 无"""

# 模拟 WM 输出（移动 + 概率检查 + Day 推进）
SIMULATED_OUTPUT_C = """你决定离开质检小楼，向东穿过工业区。途中似乎有人远远跟了过来。

天黑前你到了加油站，这里比预想的荒凉。

[Move] 工业区/N/质检小楼 -> N-E-工业通道 -> 工业区/E/加油站 | Steps: 3 | Travel Time: 90min
[Probability Check] Trigger: third-party-sighting；Base: 15；Modifiers: 白天+0, 开阔地+10；Final: 25；Seed: 42；Threshold: 25；Result: 未触发；Outcome: 疑似跟踪者放弃
[判定] 消耗（D6->D7）: 随身 干粮×0.5kg + 净水×1L；Encounter: 远距目击疑似跟踪者，未升级
[主要状态] D7-T178 17:00 | 工业区/E/加油站 | Winter-Overcast-Cool | 疲劳 strained；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 弹药余9mm×12"""


def check_output(label, output):
    """验证 WM 输出是否符合新规则"""
    errors = []
    checks = []

    lines = output.strip().split('\n')

    # 1. 检查 4 个结构块存在
    blocks_found = {}
    for i, line in enumerate(lines):
        for block_name in ['[Move]', '[Probability Check]', '[判定]', '[主要状态]']:
            if line.startswith(block_name):
                blocks_found[block_name] = i

    for block_name in ['[Move]', '[Probability Check]', '[判定]', '[主要状态]']:
        if block_name in blocks_found:
            checks.append(f"  ✅ {block_name} 存在 (行 {blocks_found[block_name]})")
        else:
            errors.append(f"  ❌ {block_name} 缺失")

    # 2. 检查顺序
    expected_order = ['[Move]', '[Probability Check]', '[判定]', '[主要状态]']
    found_order = sorted(blocks_found.keys(), key=lambda k: blocks_found[k])
    if found_order == expected_order:
        checks.append(f"  ✅ 顺序正确: {' -> '.join(expected_order)}")
    else:
        errors.append(f"  ❌ 顺序错误: {' -> '.join(found_order)} (期望: {' -> '.join(expected_order)})")

    # 3. 检查标签后不换行（标签行不等于纯标签）
    for block_name, line_idx in blocks_found.items():
        line = lines[line_idx]
        if line.strip() == block_name:
            errors.append(f"  ❌ {block_name} 标签后换行（行 {line_idx}：'{line}'）")
        else:
            content = line[len(block_name):].strip()
            checks.append(f"  ✅ {block_name} 标签后不换行: '{content[:40]}...'")

    # 4. 检查空块格式
    move_line = lines[blocks_found.get('[Move]', -1)] if '[Move]' in blocks_found else ""
    if '[Move] 无' in move_line:
        checks.append("  ✅ [Move] 空格式正确: '[Move] 无'")

    prob_line = lines[blocks_found.get('[Probability Check]', -1)] if '[Probability Check]' in blocks_found else ""
    if '无概率事件' in prob_line:
        checks.append("  ✅ [Probability Check] 空格式正确: '无概率事件'")

    res_line = lines[blocks_found.get('[判定]', -1)] if '[判定]' in blocks_found else ""
    if re.match(r'\[判定\] 无$', res_line.strip()):
        checks.append("  ✅ [判定] 空格式正确: '[判定] 无'")
    elif '消耗' in res_line:
        checks.append(f"  ✅ [判定] 含消耗行")
        # 检查消耗行格式
        if re.search(r'消耗（D\d+->D\d+）:', res_line):
            checks.append("  ✅ 消耗行格式正确: 消耗（D{prev}->D{curr}）:")
        else:
            errors.append(f"  ❌ 消耗行格式错误: '{res_line[:60]}'")

    # 5. 检查 [主要状态] 格式
    state_line = lines[blocks_found.get('[主要状态]', -1)] if '[主要状态]' in blocks_found else ""
    state_pattern = r'\[主要状态\] D\d+-T\d+ \d{2}:\d{2} \| .+ \| .+-.+-.+ \| .+ \| .+'
    if re.match(state_pattern, state_line):
        checks.append("  ✅ [主要状态] 5段结构完整")
    else:
        errors.append(f"  ❌ [主要状态] 格式错误: '{state_line[:60]}'")

    # 6. 检查 [主要状态] 是否为最后一个块
    if '[主要状态]' in blocks_found:
        last_block_line = max(blocks_found.values())
        if blocks_found['[主要状态]'] == last_block_line:
            checks.append("  ✅ [主要状态] 为最后一个结构块")
        else:
            errors.append("  ❌ [主要状态] 不是最后一个结构块")

    # 7. 检查各项用 ；分隔（判定和 Probability Check）
    if '；' in res_line and '消耗' in res_line:
        checks.append("  ✅ [判定] 各项用 ；分隔")
    if '；' in prob_line and 'Trigger' in prob_line:
        checks.append("  ✅ [Probability Check] 各项用 ；分隔")

    # 输出结果
    print(f"\n{'='*60}")
    print(f"测试: {label}")
    print(f"{'='*60}")

    if checks:
        print("\n通过项:")
        for c in checks:
            print(c)

    if errors:
        print(f"\n失败项 ({len(errors)}):")
        for e in errors:
            print(e)
        return False
    else:
        print(f"\n✅ 全部通过 ({len(checks)} 项)")
        return True


def main():
    print("="*60)
    print("端到端测试：WM 输出结构验证")
    print("="*60)

    all_pass = True

    # 测试 A: 跨日 + 交易 + 无移动 + 无概率
    all_pass &= check_output("场景A: 跨日+交易+无移动+无概率", SIMULATED_OUTPUT_A)

    # 测试 B: 无事件 + 无 Day 推进
    all_pass &= check_output("场景B: 无事件+无Day推进", SIMULATED_OUTPUT_B)

    # 测试 C: 移动 + 概率检查 + Day 推进
    all_pass &= check_output("场景C: 移动+概率检查+Day推进", SIMULATED_OUTPUT_C)

    # 汇总
    print(f"\n{'='*60}")
    print("端到端测试汇总")
    print(f"{'='*60}")
    if all_pass:
        print("✅ 全部场景通过")
    else:
        print("❌ 有场景未通过")
    return 0 if all_pass else 1


if __name__ == "__main__":
    exit(main())
