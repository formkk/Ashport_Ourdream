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
import json
from pathlib import Path

# 格式规则 SSOT：output_rules.json（改格式只改 json，不改本脚本）
RULES_PATH = Path(__file__).parent / 'output_rules.json'
RULES = json.loads(RULES_PATH.read_text(encoding='utf-8'))

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

[Move] 工业区/N -> 工业区/C -> 工业区/E | Steps: 2 | Travel Time: 60min
[Probability Check] Trigger: third-party-sighting: 穿越工业区开阔地带是否被第三方远距目击；Base: 15（白天开阔地人流低）；Modifiers: 开阔地+10，白天人流低-5；Final: 20；Seed: 42；Threshold: 20；Result: 未触发；Outcome: 疑似跟踪者放弃，未升级接触
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

    # 8. json SSOT 格式校验：用 output_rules.json 的 format_pattern 校验全部结构块行
    for block_name, line in [('[Move]', move_line), ('[Probability Check]', prob_line),
                             ('[判定]', res_line), ('[主要状态]', state_line)]:
        rule = RULES['wm']['block_rules'].get(block_name)
        if rule is None:
            continue
        import re as _re
        if _re.match(rule['format_pattern'], line.strip()):
            checks.append(f"  ✅ {block_name} json SSOT 格式合规")
        else:
            errors.append(f"  ❌ {block_name} json SSOT 格式违规（期望: {rule['format_desc']}；实际: '{line.strip()[:60]}'）")

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


def check_regex_negative_cases():
    """反例自测：真实违规样本必须被 json SSOT 正则拒绝"""
    print(f"\n{'='*60}")
    print("反例自测：真实违规样本应被拒绝")
    print(f"{'='*60}")

    pc_pattern = RULES['wm']['block_rules']['[Probability Check]']['format_pattern']

    # 4 个真实 WM 输出样本（用户提供，2026-08 采集；末尾 * 已去除以隔离单一变量）
    real_samples = [
        "[Probability Check] Trigger: 江在护林员小屋内搜刮，屋外左侧再次出现明显擦碰声，附近是否有人正接近或已发现小屋被入；Base: 30（雨林地带声近且透）；Modifiers: 江入屋后动作收敛-5，小屋半塌有回风干扰+5，异响极近且无风+15；Final: 45；Seed: 33；Threshold: 45；Result: 触发；Outcome: 屋外有声源，但未冲门，也未现形。江判断不可再搜，风险转为即时不安；未与之照面，仅一瞬后复静。",
        "[Probability Check] Trigger: 从游客中心前往护林员小屋的短暂林路，是否被林内其他人先看到或跟上；Base: 15（林中遮掩多，江一路压步子）；Modifiers: 鸟群惊飞后江警觉+5，林间腐叶厚难避免细微响动-5，天阴能见度差但声音反传清晰-0；Final: 15；Seed: 58；Threshold: 15；Result: 未触发；Outcome: 江抵达小屋外，暂无人现身，但林路上确有来源不明的细响，需谨慎进屋。",
        "[Probability Check] Trigger: 进入游客中心搜索并传出轻微翻找声，同时鸟群惊飞，是否有人或兽已察觉江并朝建筑靠近；Base: 25（游客中心为显眼地标，附近已现异动）；Modifiers: 江动作轻-5，树林遮蔽与天色阴-5，鸟群惊飞说明近处已有扰动+15；Final: 30；Seed: 48；Threshold: 30；Result: 未触发；Outcome: 未发现人影与生物逼近，但鸟群惊飞方向正对所搜房间东侧，现场紧张感陡增。",
        "[Probability Check] Trigger: 江从北区住宅带前往森林公园边缘，经过林缘锈栏时，林内是否有人先发现他；Base: 20（林缘开阔段+北区近郊偶有流民）；Modifiers: 江单人轻装-5，昼间林鸟未惊-5，天阴多影+5；Final: 15；Seed: 76；Threshold: 15；Result: 未触发；Outcome: 未发现林中人迹，仅一声枯枝响，来源不明；但森林公园整体气压低，落叶腐味像有活物在深处。",
    ]

    all_pass = True
    for i, sample in enumerate(real_samples, 1):
        matched = re.match(pc_pattern, sample)
        if matched:
            print(f"  ❌ 样本{i} 未被拒绝（违规样本通过了校验）")
            all_pass = False
        else:
            print(f"  ✅ 样本{i} 被正确拒绝（缺类名等违规）")

    # 合规形态必须通过
    valid_cases = [
        "[Probability Check] 无概率事件",
        "[Probability Check] Dase-1",
        "[Probability Check] Dase-1；Dase-2",
        "[Probability Check] Dase-2",
        "[Probability Check] Dase-2；Dase-3",
        "[Probability Check] Dase-1；Dase-4",
        "[Probability Check] wear-weather: 未触发",
        "[Probability Check] wear-weather: 未触发；wear-sabotage: 未触发",
        "[Probability Check] Trigger: hostile-contact: 江在护林员小屋内搜刮，屋外左侧再次出现明显擦碰声，是否有人接近或已发现小屋被入；Base: 30（雨林地带声近且透）；Modifiers: 江入屋后动作收敛-5，小屋半塌有回风干扰+5，异响极近且无风+15；Final: 45；Seed: 33；Threshold: 45；Result: 触发；Outcome: 屋外确认有声源，未冲门，未现形，一瞬后复静，江未与之照面",
        "[Probability Check] Trigger: hostile-contact#2: 同轮第二次独立敌对接触检查；Base: 20；Modifiers: 夜间+10；Final: 30；Seed: 55；Threshold: 30；Result: 未触发；Outcome: 无接触",
        "[Probability Check] Trigger: custom: 自定义事件检查；Base: 10；Modifiers: 无关紧要+5；Final: 15；Seed: 22；Threshold: 15；Result: 未触发；Outcome: 无事发生",
    ]
    for i, sample in enumerate(valid_cases, 1):
        if re.match(pc_pattern, sample):
            print(f"  ✅ 合规形态{i} 通过")
        else:
            print(f"  ❌ 合规形态{i} 被误拒: '{sample[:60]}'")
            all_pass = False

    return all_pass


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

    # 反例自测：真实违规样本应被 json SSOT 正则拒绝
    all_pass &= check_regex_negative_cases()

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
    # Windows 管道/GBK 终端下强制 UTF-8 输出，避免 ✅/❌ 触发 UnicodeEncodeError
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    exit(main())
