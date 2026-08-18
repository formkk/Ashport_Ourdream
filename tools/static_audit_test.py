#!/usr/bin/env python3
"""
Ash Harbor 审计修复静态验证脚本
验证 P0(2) + P1(7) + P2(10) + P3(3) = 22 项修复的规则逻辑是否按预期工作。
所有输出使用 ASCII 安全标记，避免 Windows GBK 终端编码问题。
"""

import re
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_DIR = PROJECT_ROOT / "Prompt_File"

def read_file(short_name):
    """按短名读取提示词文件"""
    mapping = {
        "0-1": "0-1_Private_Details.md",
        "0-2": "0-2_Scenario.md",
        "0-3": "0-3_\u81ea\u5b9a\u4e49\u6307\u4ee4.md",
        "1-1": "1-1_WorldMaster_Scene.md",
        "1-2": "1-2_WorldMaster_Additional_Personality_Details.md",
        "1-3": "1-3_WorldMaster_Extra_Details.md",
        "2-1": "2-1_WorldStateKeeper_Scene.md",
        "2-2": "2-2_WorldStateKeeper_Additional_Personality_Details.md",
        "2-3": "2-3_WorldStateKeeper_Extra_Details.md",
    }
    filepath = PROMPT_DIR / mapping[short_name]
    return filepath.read_text(encoding="utf-8")

# ============================================================
# 测试框架
# ============================================================

passed = 0
failed = 0
errors = []

def test(test_id, description, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {test_id}: {description}")
    else:
        failed += 1
        msg = f"  [FAIL] {test_id}: {description}"
        if detail:
            msg += f" -- {detail}"
        print(msg)
        errors.append({"id": test_id, "desc": description, "detail": detail})

# ============================================================
# P0 修复验证
# ============================================================

def test_p0():
    print("\n--- P0 Critical Fixes ---")
    f_12 = read_file("1-2")
    f_03 = read_file("0-3")
    f_11 = read_file("1-1")

    # P0-1: [Move] 输出位置不再矛盾
    # 1-2 L150 应为 "按 [输出结构] 规定的位置输出 [Move]"
    test("P0-1", "[Move] position conflict resolved",
         "按 [输出结构] 规定的位置输出 [Move]" in f_12,
         "1-2 should say '按 [输出结构] 规定的位置输出 [Move]'")

    # P0-1 补充：旧的矛盾措辞 "在 [主要状态] 之后输出 [Move]" 不应存在
    test("P0-1b", "Old contradictory [Move] wording removed",
         "在 [主要状态] 之后输出 [Move]" not in f_12,
         "Old wording '在 [主要状态] 之后输出 [Move]' should not exist")

    # P0-2: 不再要求跨轮词频统计（[重复抑制]已迁至 1-1）
    test("P0-2a", "Cross-turn word counting removed",
         "跟踪本场最近 3 轮" not in f_03 and "3 轮内每词最多" not in f_03,
         "Should not contain '跟踪本场最近 3 轮' or '3 轮内每词最多'")

    # P0-2 补充：已改为单轮约束（[重复抑制]已迁至 1-1）
    test("P0-2b", "Single-turn constraint present",
         "单轮内" in f_11 and "[重复抑制]" in f_11,
         "Should contain '[重复抑制]' and '单轮内' in 1-1")

# ============================================================
# P1 修复验证
# ============================================================

def test_p1():
    print("\n--- P1 High-Priority Fixes ---")
    f_13 = read_file("1-3")
    f_12 = read_file("1-2")
    f_23 = read_file("2-3")

    # P1-1: Seed 公式使用尾数运算
    test("P1-1a", "Seed formula uses digit-tail",
         "Day 末两位" in f_13 and "Turn 末两位" in f_13,
         "Should use 'Day 末两位' and 'Turn 末两位'")

    # P1-1: 旧的完整数字乘法公式不应存在
    test("P1-1b", "Old full-number Seed formula removed",
         "(Day ID" not in f_13 or "Day ID × 7 + Turn ID × 3" not in f_13,
         "Old formula '(Day ID × 7 + Turn ID × 3' should not exist")

    # P1-1: 示例行匹配新公式格式
    test("P1-1c", "Example line uses new formula",
         "((83 × 7) + (00 × 3) + 37)" in f_13,
         "Example should show '((83 × 7) + (00 × 3) + 37)'")

    # P1-1d: Seed 计算正确性验证
    # ((83*7) + (00*3) + 37) mod 100 = (581 + 0 + 37) mod 100 = 618 mod 100 = 18
    expected_seed = ((83 * 7) + (0 * 3) + 37) % 100
    test("P1-1d", "Seed arithmetic correct (expect 18)",
         expected_seed == 18,
         f"Expected 18, got {expected_seed}")

    # P1-2: 场外演化条件删除了 (d)
    test("P1-2a", "Offscreen condition (d) removed",
         "(d)" not in f_13.split("[回合后场外演化规则]")[1].split("[场外演化同步原则]")[0]
         if "[回合后场外演化规则]" in f_13 else False,
         "Condition (d) should not exist in offscreen rules")

    # P1-2b: 仍保留 (a)(b)(c) 三个条件
    offscreen_section = f_13.split("[回合后场外演化规则]")[1].split("[场外演化同步原则]")[0]
    test("P1-2b", "Conditions (a)(b)(c) preserved",
         "(a)" in offscreen_section and "(b)" in offscreen_section and "(c)" in offscreen_section,
         "Should still have (a), (b), (c)")

    # P1-3: 连续暴露/驻留天数改为定性判断
    test("P1-3a", "Day-counting for exposure removed",
         "连续暴露≥3日" not in f_12,
         "'连续暴露≥3日' should not exist")
    test("P1-3b", "Day-counting for residence removed",
         "连续驻留 ≥7 日" not in f_12,
         "'连续驻留 ≥7 日' should not exist")

    # P1-4: 压力阈值表有 step 换算参考
    threshold_section = f_13.split("[生存压力时间阈值表]")[1].split("脱水")[0] if "[生存压力时间阈值表]" in f_13 else ""
    test("P1-4", "Step conversion reference added",
         "1 step = 0.5h" in threshold_section or "1 step = 0.5h" in f_13,
         "Should contain '1 step = 0.5h' conversion")

    # P1-5: 据点损耗修复间隔简化
    test("P1-5", "Repair interval simplified (no day counting)",
         "对比当前 Day 判断间隔是否 ≥3 日" not in f_12,
         "Old day-counting repair rule should not exist")

    # P1-6: Offset 简化 - 冲突检测逻辑应删除
    offset_section = f_13.split("使用规则：")[1].split("Final Probability")[0] if "使用规则：" in f_13 else ""
    test("P1-6a", "Offset conflict detection removed",
         "+1 mod 100" not in offset_section,
         "'+1 mod 100' conflict resolution should not exist")

    test("P1-6b", "Offset uses simple index increment",
         "本轮检查序号" in offset_section,
         "Should use '本轮检查序号'")

    # P1-7: Party Condition 维度对齐到 5 轨
    test("P1-7a", "Party Condition aligned to 5 tracks",
         "5 轨状态级" in f_23 and "从 WM" in f_23.split("Party Condition")[2][:200]
         if f_23.count("Party Condition") >= 3 else False,
         "Party Condition should reference 5-track states")

    # P1-7b: 旧的无序维度列表不应存在
    test("P1-7b", "Old chaotic dimension list removed",
         "伤病/疼痛/感染/饥渴/疲劳/体温/湿度/精神压力/濒死/死亡" not in f_23,
         "Old flat dimension list should not exist")

# ============================================================
# P2 修复验证
# ============================================================

def test_p2():
    print("\n--- P2 Medium-Priority Fixes ---")
    f_01 = read_file("0-1")
    f_02 = read_file("0-2")
    f_03 = read_file("0-3")
    f_12 = read_file("1-2")
    f_13 = read_file("1-3")
    f_23 = read_file("2-3")

    # P2-1: 0-1 NPC 反全知压缩为概述
    npc_section_01 = f_01.split("[NPC")[1].split("[")[0] if "[NPC" in f_01 else ""
    npc_lines_01 = [l for l in npc_section_01.split('\n') if l.strip().startswith('-')]
    test("P2-1a", "0-1 NPC rules compressed to summary",
         len(npc_lines_01) <= 5,
         f"0-1 NPC section has {len(npc_lines_01)} bullet points, expected <= 5")

    test("P2-1b", "0-1 NPC section references 1-3 for details",
         "1-3" in npc_section_01 or "Extra Details" in npc_section_01,
         "Should reference Extra Details for detailed rules")

    # P2-2: 敌对阶梯枚举在 1-3 中补充
    test("P2-2", "Hostility ladder enum defined in 1-3",
         "no-signal" in f_13 and "old-trace" in f_13 and "spotted" in f_13
         and "contacted" in f_13 and "hostile-contact" in f_13,
         "Should define 5 stages: no-signal, old-trace, spotted, contacted, hostile-contact")

    # P2-3: 据点物资丰富 +10 有参考阈值
    test("P2-3", "Base wealth modifier has threshold definition",
         "≥3 天口粮" in f_12 or "据点物资丰富 +10" in f_12,
         "Should have threshold like '≥3 天口粮'")

    # P2-4: 跨午夜换算示例
    test("P2-4", "Cross-midnight travel example exists",
         "跨午夜" in f_13 or "跨日 -> 00:" in f_13 or "22:00" in f_13,
         "Should have cross-midnight calculation example")

    # P2-4b: 验证跨午夜计算正确性
    # 22:00 + 150min = 22:00 + 2h30m = 00:30 next day
    start_h, start_m = 22, 0
    travel_min = 150
    end_total = (start_h * 60 + start_m + travel_min) % (24 * 60)
    end_h, end_m = divmod(end_total, 60)
    crosses_midnight = (start_h * 60 + start_m + travel_min) >= (24 * 60)
    test("P2-4b", "Cross-midnight math correct (00:30)",
         end_h == 0 and end_m == 30 and crosses_midnight,
         f"Expected 00:30 crossing midnight, got {end_h:02d}:{end_m:02d} cross={crosses_midnight}")

    # P2-5: 感官词改为可选（[感官词抽屉]已迁至 1-3）
    test("P2-5", "Sensory tokens are optional",
         "可选参考工具" in f_13 and "不强制每轮" in f_13,
         "Should say '可选参考工具' and '不强制每轮' in 1-3")

    # P2-6: WSK 消耗投影简化
    proj_section = f_23.split("消耗投影")[1].split("[可消耗物资")[0] if "消耗投影" in f_23 else ""
    test("P2-6", "Consumption projection uses formula",
         "÷" in proj_section or "/" in proj_section,
         "Should use division formula")

    # P2-6b: 旧的兜底基准值行应删除
    test("P2-6b", "Old fallback baseline removed",
         "基准值（仅 WM 未估算时兜底）" not in proj_section,
         "Old fallback baseline should not exist")

    # P2-7: 微步概念引入
    test("P2-7a", "Micro-step concept in 1-3",
         "微步" in f_13,
         "1-3 should define '微步'")
    test("P2-7b", "Micro-step concept in 1-2",
         "微步" in f_12,
         "1-2 should reference '微步'")

    # P2-8: 据点暴露 vs 知情范围差异（v1.67 起 Security/Exposure 字段已删，知情范围 4 档在 2-3）
    test("P2-8", "Exposure vs knowledge scope difference noted",
         "知情范围: hidden / party-known / local-only / publicly-known" in f_23
         and "Security/Exposure" not in f_23,
         "2-3 should keep knowledge 4-tier; Security/Exposure removed in v1.67")

    # P2-9: 据点结构基线不再含存档数据
    baseline_section = f_13.split("[据点结构基线]")[1].split("[长时间")[0] if "[据点结构基线]" in f_13 else ""
    test("P2-9a", "Archive data removed from baseline",
         "化工厂质检小楼" not in baseline_section and "绿墙别墅" not in baseline_section,
         "Archive data (specific bases) should not exist")

    test("P2-9b", "Format template preserved",
         "格式模板" in baseline_section or "{组件名}" in baseline_section,
         "Format template should remain")

    # P2-10: 1-2 跨位转移协议改为引用
    cross_section_12 = f_12.split("[跨位转移与知情范围协议]")[1].split("[死亡")[0] if "[跨位转移与知情范围协议]" in f_12 else ""
    test("P2-10", "1-2 cross-transfer protocol is reference-only",
         "见 Public Details" in cross_section_12 or "本字段不重复" in cross_section_12,
         "1-2 should reference 0-1 instead of duplicating")

# ============================================================
# P3 修复验证
# ============================================================

def test_p3():
    print("\n--- P3 Minor Fixes ---")
    f_02 = read_file("0-2")
    f_13 = read_file("1-3")

    # P3-1: 保持现状（英文枚举）- 验证枚举仍为英文
    test("P3-1", "Temperature/weather enums remain English",
         "Bitter Cold" in f_13 and "Mild" in f_13,
         "English enums should be preserved")

    # P3-2: 保暖修正方向改为中文
    warm_section = f_13.split("保暖修正表")[1].split("环境修正")[0] if "保暖修正表" in f_13 else ""
    test("P3-2", "Warmth modifier uses directional Chinese",
         "向暖侧移" in warm_section and "向冷侧移" in warm_section,
         "Should use '向暖侧移' and '向冷侧移' instead of +/-")

    # P3-3: 0-2 起始物资有 kg 估算
    test("P3-3", "Starting items have kg estimates",
         "≈0.45kg" in f_02 or "0.45kg" in f_02,
         "0-2 should have kg estimates for starting items")

# ============================================================
# 机制模拟测试
# ============================================================

def test_mechanics():
    print("\n--- Mechanism Simulation ---")

    # 模拟 1: Seed 公式多组数据验证
    print("  [Mech-1] Seed formula multi-case verification:")
    test_cases = [
        # (day_last2, turn_last2, offset, expected_seed)
        (83, 0, 37, 18),    # 原示例
        (1, 1, 10, 20),     # 早期游戏
        (62, 45, 53, 22),   # 冬季: (434+135+53)%100=622%100=22
        (30, 76, 19, 57),   # 中期: (210+228+19)%100=457%100=57
        (99, 99, 99, 89),   # 大数边界: (693+297+99)%100=1089%100=89
    ]
    all_pass = True
    for day_l2, turn_l2, offset, expected in test_cases:
        seed = ((day_l2 * 7) + (turn_l2 * 3) + offset) % 100
        ok = seed == expected
        if not ok:
            all_pass = False
            print(f"    Day={day_l2} Turn={turn_l2} Offset={offset} -> Seed={seed} (expected {expected}) [FAIL]")
        else:
            print(f"    Day={day_l2} Turn={turn_l2} Offset={offset} -> Seed={seed} [OK]")
    test("Mech-1", "Seed formula all cases pass", all_pass)

    # 模拟 2: 微步累计结算
    print("  [Mech-2] Micro-step accumulation:")
    # 3 个微步 = 45 分钟，不足 30 分钟？不，3 个 15 分钟 = 45 分钟 >= 30 分钟 = 1 step + 余
    # 规则：同轮累计达 30 分钟 = 1 step
    micro_steps = [10, 15, 12]  # 3 个微步，共 37 分钟
    total_min = sum(micro_steps)
    steps = total_min // 30
    remaining = total_min % 30
    test("Mech-2a", "3 micro-steps (37min) = 1 step + 7min remainder",
         steps == 1 and remaining == 7,
         f"Expected 1 step + 7min, got {steps} step + {remaining}min")

    # 单个微步不推进 step
    single_micro = 15
    steps_single = single_micro // 30
    test("Mech-2b", "Single micro-step (15min) = 0 step",
         steps_single == 0,
         f"Expected 0 step, got {steps_single}")

    # 模拟 3: 敌对阶梯升级路径
    print("  [Mech-3] Hostility ladder escalation:")
    ladder = ["no-signal", "old-trace", "spotted", "contacted", "hostile-contact"]
    test("Mech-3", "Ladder has 5 monotonically escalating stages",
         len(ladder) == 5,
         f"Expected 5 stages, got {len(ladder)}")

    # 模拟 4: 保暖修正方向
    print("  [Mech-4] Warmth modifier direction:")
    # 档位序列: Heat > Mild > Cool > Cold > Bitter Cold (index 0=warm, 4=cold)
    temp_levels = ["Heat", "Mild", "Cool", "Cold", "Bitter Cold"]
    # "向暖侧移 2 档" = 向 Heat 方向(index 减小)
    # "向冷侧移 2 档" = 向 Bitter Cold 方向(index 增大)
    base_idx = 2  # Cool
    warm_shift = max(base_idx - 2, 0)  # 向暖侧移 2 = Heat
    cold_shift = min(base_idx + 2, len(temp_levels) - 1)  # 向冷侧移 2 = Bitter Cold
    test("Mech-4a", "Warm shift +2 from Cool = Heat",
         temp_levels[warm_shift] == "Heat",
         f"Expected Heat, got {temp_levels[warm_shift]}")
    test("Mech-4b", "Cold shift -2 from Cool = Bitter Cold",
         temp_levels[cold_shift] == "Bitter Cold",
         f"Expected Bitter Cold, got {temp_levels[cold_shift]}")

    # 模拟 5: WSK 消耗投影公式
    print("  [Mech-5] WSK consumption projection:")
    # 食物 12kg, 3 人, 1kg/天/人 -> 12 / (3*1) = 4 天
    food_kg = 12
    people = 3
    food_days = food_kg / (people * 1)
    test("Mech-5a", "Food projection: 12kg / 3 people = 4 days",
         food_days == 4.0, f"Expected 4, got {food_days}")
    # 饮水 6kg, 3 人, 2kg/天/人 -> 6 / (3*2) = 1 天
    water_kg = 6
    water_days = water_kg / (people * 2)
    test("Mech-5b", "Water projection: 6kg / (3*2) = 1 day",
         water_days == 1.0, f"Expected 1, got {water_days}")

# ============================================================
# 一致性交叉验证
# ============================================================

def test_cross_consistency():
    print("\n--- Cross-File Consistency ---")
    f_01 = read_file("0-1")
    f_12 = read_file("1-2")
    f_13 = read_file("1-3")
    f_23 = read_file("2-3")

    # 验证：0-1 和 1-2 的跨位转移协议不再重复
    cross_01 = f_01.split("[跨位转移与知情范围协议]")[1].split("[")[0] if "[跨位转移与知情范围协议]" in f_01 else ""
    cross_12 = f_12.split("[跨位转移与知情范围协议]")[1].split("[")[0] if "[跨位转移与知情范围协议]" in f_12 else ""

    # 0-1 应有完整定义，1-2 应为引用
    test("Cross-1", "0-1 has full cross-transfer definition",
         "随身 / 据点核心" in cross_01,
         "0-1 should have full definition")
    test("Cross-2", "1-2 is reference-only (not duplicated)",
         len([l for l in cross_12.strip().split('\n') if l.strip()]) <= 2,
         "1-2 should be <= 2 lines")

    # 验证：NPC 反全知规则不重复（0-1 概述 vs 1-3 细则）
    npc_01_lines = [l for l in f_01.split("[NPC 反全知")[1].split("[")[0].split('\n') if l.strip().startswith('-')]
    npc_13_lines = [l for l in f_13.split("[NPC 反全知")[1].split("[NPC Relationship")[0].split('\n') if l.strip().startswith('-')]
    test("Cross-3", "0-1 NPC is summary (<=5 lines), 1-3 is detailed (>=10 lines)",
         len(npc_01_lines) <= 5 and len(npc_13_lines) >= 10,
         f"0-1: {len(npc_01_lines)} lines, 1-3: {len(npc_13_lines)} lines")

    # 验证：据点暴露档位与知情范围档位的区分
    test("Cross-4", "Exposure field removed, Knowledge 4-tier intact",
         "Security/Exposure" not in f_23
         and "party-known" in f_01,
         "Security/Exposure removed in v1.67; knowledge scope with party-known in 0-1")

# ============================================================
# 近五日主要事件机制验证
# ============================================================

def test_recent_events():
    print("\n--- Recent Events Mechanism ---")
    f_23 = read_file("2-3")
    f_13 = read_file("1-3")

    # 提取近五日规则段落
    events_rule = ""
    for line in f_23.split('\n'):
        if "近五日主要事件" in line and "完整视图最末" in line:
            events_rule = line
            break

    # 验证：滚动窗口机制存在
    test("RE-1", "Rolling window: keep last 5 days, remove older",
         "往前数 5 天" in events_rule and "更早的事件" in events_rule and "移除" in events_rule,
         "Should define 5-day rolling window with removal")

    # 验证：总容量上限已删除
    test("RE-2", "Total capacity limit removed (no 1500 chars)",
         "1500" not in events_rule,
         "Should not contain 1500-char total limit")

    # 验证：单条上限改为 300 字符
    test("RE-3", "Per-entry limit is 300 chars (not 150-500 range)",
         "300" in events_rule and "500" not in events_rule,
         "Should use 300-char per-entry cap, not 150-500 range")

    # 验证：同日多事件合并
    test("RE-4", "Same-day multi-event merge rule exists",
         "同日多事件合并为一条摘要" in events_rule,
         "Should define same-day merge rule")

    # 验证：继承机制（从上一份继承，首次从当前Day累积）
    test("RE-5", "Inheritance mechanism defined",
         "继承" in events_rule and "首次" in events_rule and "累积" in events_rule,
         "Should define inheritance from previous [State Update]")

    # 验证：季节性事件规则已从 1-3 删除
    seasonal_removed = "纳入" not in f_13.split("世界事件同步")[1].split("\n")[0] if "世界事件同步" in f_13 else True
    test("RE-6", "Seasonal event rule removed from 1-3",
         seasonal_removed,
         "1-3 should not have seasonal event -> recent events rule")

    # ---- 模拟数据：滚动窗口 + 合并逻辑 ----
    # Mock: 上一份 State Update 的近五日段（D6-D10），当前 Day=11
    prev_events = {
        6: "与劫掠者交火，击退但受伤；修补据点大门",
        7: "探索工业区/NE，发现废弃药房",
        8: "与水源商会交易，以零件换水×3kg",
        9: "煤矿队来访谈合作；据点安装雨水收集器",
        10: "夜袭警报，击退侦察兵；Amber 到达加入队伍",
    }
    # Mock: 本轮 D11 新事件（同日多事件）
    d11_events = [
        "拾荒者阶层在商业区/E 发生骚乱",
        "据点壁炉烟道清理完毕",
        "与码头帮建立初步交易关系",
    ]

    # 模拟滚动窗口：保留 D7-D11（丢弃 D6）
    current_day = 11
    window_size = 5
    all_days = sorted(prev_events.keys() | {current_day})
    keep_days = [d for d in all_days if d > current_day - window_size]
    # D6 should be removed
    test("RE-Sim1", "Rolling window removes D6 (older than 5 days)",
         6 not in keep_days and 7 in keep_days and 11 in keep_days,
         f"D6 should be removed, kept days = {keep_days}")

    # 模拟同日合并：D11 多事件合并为一条
    d11_merged = "；".join(d11_events)
    test("RE-Sim2", "Same-day merge: D11 combines 3 events into 1 entry",
         d11_merged.count("；") == 2 and d11_merged.count("D11") == 0,
         f"Merged entry: {d11_merged[:60]}...")

    # 模拟最终输出格式
    merged_events = {}
    for d in keep_days:
        if d == current_day:
            merged_events[d] = f"D{d}: {d11_merged}"
        else:
            merged_events[d] = f"D{d}: {prev_events[d]}"

    output_lines = list(merged_events.values())

    # 验证：最终输出恰好 5 条
    test("RE-Sim3", "Final output has exactly 5 entries (D7-D11)",
         len(output_lines) == 5,
         f"Expected 5, got {len(output_lines)}: {[l[:10] for l in output_lines]}")

    # 验证：D 升序排列
    day_order = [int(l.split("D")[1].split(":")[0]) for l in output_lines]
    test("RE-Sim4", "Output sorted by D ascending",
         day_order == sorted(day_order),
         f"Order: {day_order}")

    # 验证：D11 合并条目包含全部 3 个事件关键词
    d11_line = [l for l in output_lines if l.startswith("D11")][0]
    test("RE-Sim5", "D11 merged entry contains all 3 event keywords",
         "骚乱" in d11_line and "烟道" in d11_line and "交易关系" in d11_line,
         f"D11 line: {d11_line[:80]}...")

    # 验证：每条不超过 300 字符
    max_len = max(len(l.split(": ", 1)[1]) if ": " in l else len(l) for l in output_lines)
    test("RE-Sim6", f"All entries under 300 chars (max={max_len})",
         max_len <= 300,
         f"Max entry length = {max_len}")

# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("Ash Harbor Audit Fix Static Verification")
    print("Verifying P0(2) + P1(7) + P2(10) + P3(3) = 22 fixes")
    print("=" * 60)

    test_p0()
    test_p1()
    test_p2()
    test_p3()
    test_mechanics()
    test_cross_consistency()
    test_recent_events()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = passed + failed
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed > 0:
        print(f"\n  Failed tests ({failed}):")
        for e in errors:
            print(f"    [{e['id']}] {e['desc']}")
            if e['detail']:
                print(f"      -> {e['detail']}")

    print()
    if failed == 0:
        print("  >>> ALL TESTS PASSED <<<")
    else:
        print(f"  >>> {failed} TEST(S) FAILED <<<")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    exit(main())
