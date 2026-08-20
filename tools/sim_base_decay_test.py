#!/usr/bin/env python3
"""
Ash Harbor 据点损耗机制触发链路测试脚本

场景：模拟"建立据点并推进一天"（D5 -> D6, Storm 天气, 暴露事件成立），
按 prompt 规则推演 WSK 的预期输出日志，检查据点状态字段存在性与已删字段不回归。

测试对象：
  1. 规则源检查：2-2 §[据点与庇护记录规则] 三字段要求在位 + Security/Exposure 已删（v1.67）
  2. 正例推演：规则完整形态的 WSK 输出（LLM 完全遵守规则时应输出什么）-> 应全 PASS
  3. 反例：模拟早期实际输出（只有组件清单，无状态字段）-> 应检出缺失
  4. 真实输出校验：若 tools/wsk_real_output.txt 存在（用户从平台实测粘贴），对其做同样检查

字段存在性依据（2-2 §[据点与庇护记录规则]）：
  - 据点状态唯一记录载体 = 组件名 + 状态描述（自然语言，每轮统一输出）
  - v1.67 删除全部据点状态字段（均为无触发依赖的纯记录字段）：
    Security/Exposure、Maintenance Pressure、Rest/Shelter Availability、
    Heat/Dryness、Occupancy/Residency Load、Supply/Sanitation Strain

用法: python tools/sim_base_decay_test.py
真实校验: 把平台实测的 WSK 输出粘贴到 tools/wsk_real_output.txt 后重新运行
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_DIR = PROJECT_ROOT / "Prompt_File"
REAL_OUTPUT_FILE = Path(__file__).parent / "wsk_real_output.txt"

# Windows GBK 终端兼容
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def read_prompt(filename):
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


# ============================================================
# Mock 场景定义（模拟建据点并推进一天）
# ============================================================

MOCK_SCENARIO = """
=== Mock 场景：D5 -> D6 建据点 + Day 推进 ===

[上轮 State Update 摘要] (D5-T55)
  - 位置: 工业区/N 化工厂质检小楼外
  - Base Structure State: 无据点
  - Inventory: 罐头x6, 大米x10kg, 净水x8kg, 压缩饼干x1kg, 火柴x半盒（随身）

[本轮 WM 叙事要点]
  1. 玩家进入质检小楼定居，清理大门（门锁铁片翘起，内以木杠别住），
     确认起居室（旧会议室，有壁炉，烟道通畅）、食品储藏室（北墙铁架）、天台集水器（滤网已清）
  2. 建立据点核心：转移 罐头x6 + 大米x10kg + 净水x8kg 随身->据点核心
  3. 暴露事件成立：白天搬运物资时被附近拾荒者远距看到（据点暴露信号，写入风险栏）
  4. Day 推进 D5->D6，天气 Storm（恶劣天气，天气损耗检查 Base 55）

[WM 侧输出]（供 WSK 提取的输入）
  [移动] ...
  [掷骰] wear-sabotage: 未触发（按信号驱动简化规则，上轮风险栏有暴露信号）
  [判定] 消耗（D5->D6）: 压缩饼干x0.5kg+净水x1kg; 据点建立: 化工厂质检小楼（主据点）; 代价与后果: 夜间 Storm，屋顶渗水未触发
  [主要状态] D6-T58 21:00 | 工业区/N/化工厂质检小楼 | Winter-Storm-零下12度 | 疲劳 strained；体温 strained；脱水 stable；饥饿 stable；伤病 stable | 据点白天被拾荒者远距观察到
"""

# 正例：规则完整形态的 WSK 预期输出（LLM 完全遵守 2-2 L102/L103a/L105/L111 时）
WSK_EXPECTED_OUTPUT = """[State Update] D6-T58

Inventory Delta: 转移 罐头x6+大米x10kg+净水x8kg 随身->据点核心；消耗（D5->D6）: 压缩饼干x0.5kg+净水x1kg

1. Inventory State:
随身: 压缩饼干x0.5kg, 火柴x半盒
据点核心: 食品: 罐头x6, 大米x10kg；饮水: 净水x7kg
消耗估算（1人）：食物约16.5天 / 饮水约3.5天 / 燃料约0天

2. Party Condition: 1人；疲劳 strained；体温 strained；脱水 stable；饥饿 stable；伤病 stable

3. Relationship & Threat: 无正式关系记录
Human Threat Stage: none
知情范围: local-only

4. Map Knowledge: 工业区/N 已探索；质检小楼已确认（主据点）

5. Base Structure State: 工业区/N/化工厂质检小楼（主据点）
大门: 门锁铁片翘起，内以木杠别住
起居室（旧会议室）: 可住，有壁炉
壁炉: 烟道通畅，可用
食品储藏室: 北墙铁架，已分类存放
天台集水器: 滤网已清，可用

6. 近五日主要事件:
D5: 进入工业区，搜刮获得罐头与大米
D6: 建立化工厂质检小楼主据点，物资转入据点核心；被附近拾荒者远距看到"""

# 反例：模拟早期实际输出形态（只有组件清单，无状态字段）
WSK_REGRESS_OUTPUT = """[State Update] D6-T58

Inventory Delta: 转移 罐头x6+大米x10kg+净水x8kg 随身->据点核心；消耗（D5->D6）: 压缩饼干x0.5kg+净水x1kg

1. Inventory State:
随身: 压缩饼干x0.5kg, 火柴x半盒
据点核心: 食品: 罐头x6, 大米x10kg；饮水: 净水x7kg

2. Party Condition: 1人；疲劳 strained；体温 strained；脱水 stable；饥饿 stable；伤病 stable

3. Relationship & Threat: 无正式关系记录
Human Threat Stage: none
知情范围: local-only

4. Map Knowledge: 工业区/N 已探索；质检小楼已确认（主据点）

5. Base Structure State: 工业区/N/化工厂质检小楼（主据点）
大门: 门锁铁片翘起，内以木杠别住
起居室（旧会议室）: 可住，有壁炉
壁炉: 烟道通畅，可用
食品储藏室: 北墙铁架，已分类存放
天台集水器: 滤网已清，可用

6. 近五日主要事件:
D6: 建立化工厂质检小楼主据点，物资转入据点核心"""


# ============================================================
# 检查规则
# ============================================================

passed = 0
failed = 0
fail_list = []


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
        fail_list.append({"id": test_id, "desc": description, "detail": detail})


def check_wsk_output(output, prefix):
    """对一份 WSK 输出做据点状态字段存在性检查"""
    print(f"\n--- 字段存在性检查（{prefix}）---")

    # 提取 Base Structure State 段（到下一个编号字段或文末）
    m = re.search(r'5\. Base Structure State:(.*?)(?=\n6\. |\Z)', output, re.DOTALL)
    base_sec = m.group(1) if m else ""

    # BD-1: Base Structure State 字段存在
    test(f"{prefix}-1", "Base Structure State 字段存在", "5. Base Structure State:" in output)

    # BD-2: 据点有位置锚点（Zone/Sub-zone/Location）
    test(f"{prefix}-2", "据点条目绑定位置锚点（Zone/Sub-zone/Location）",
         bool(re.search(r'Base Structure State:.*[/\\].*[/\\]', output)),
         "应含 形如 工业区/N/化工厂质检小楼 的锚点")

    # BD-3: 组件条目存在（组件名 + 状态描述）
    test(f"{prefix}-3", "组件条目存在（组件名+状态描述）",
         ("大门:" in base_sec or "大门：" in base_sec) and ("壁炉" in base_sec),
         "2-2 要求每轮统一输出组件名+状态描述")

    # BD-4: 已删字段不应出现（v1.67 起据点状态字段全部删除）
    # 被删字段：Security/Exposure、Maintenance Pressure、Rest/Shelter Availability、
    #          Heat/Dryness、Occupancy/Residency Load、Supply/Sanitation Strain
    removed_fields = [
        (r'Security\s*/\s*Exposure', "Security/Exposure"),
        (r'Maintenance\s*Pressure', "Maintenance Pressure"),
        (r'Rest\s*/\s*Shelter\s*Availability', "Rest/Shelter Availability"),
        (r'Heat\s*/\s*Dryness', "Heat/Dryness"),
        (r'Occupancy\s*/\s*Residency\s*Load', "Occupancy/Residency Load"),
        (r'Supply\s*/\s*Sanitation', "Supply/Sanitation Strain"),
    ]
    for pattern, name in removed_fields:
        test(f"{prefix}-4", f"已删字段不再出现：{name}",
             not re.search(pattern, output),
             "v1.67 删除该字段；若出现说明 WSK 按旧规则输出")


# ============================================================
# Part 1: 规则源检查（确认 prompt 规则仍在位）
# ============================================================

def test_rule_sources():
    print("\n--- Part 1: 规则源检查（prompt 规则仍在位）---")
    f_22 = read_prompt("2-2_WorldStateKeeper_Additional_Personality_Details.md")

    # RS-1: 2-2 据点状态字段要求已整体删除（v1.67）
    test("RS-1", "2-2 据点状态字段要求已删除（无'至少应保留'行）",
         "至少应保留" not in f_22,
         "v1.67 删除全部据点状态字段；若回归说明旧规则复活")

    # RS-2: 2-2 六个状态字段全部清除
    for keyword in ["Maintenance Pressure", "Rest / Shelter Availability",
                    "Heat / Dryness", "Occupancy / Residency Load",
                    "Supply / Sanitation Strain", "Security / Exposure"]:
        test("RS-2", f"2-2 已删字段清除：{keyword}",
             keyword not in f_22,
             "v1.67 删除该字段；若回归说明旧规则复活")

    # RS-3: 2-2 组件状态描述输出规则仍在位（据点状态的唯一记录载体）
    test("RS-3", "2-2 组件状态描述输出规则仍在位",
         "每轮统一输出组件名" in f_22,
         "组件状态描述是据点状态唯一记录载体，若被删据点状态断链")

    # RS-4: 1-2 人为破坏触发指令存在（信号驱动版）
    f_12 = read_prompt("1-2_WorldMaster_Additional_Personality_Details.md")
    test("RS-4", "1-2 人为破坏信号驱动触发指令仍在位（风险栏暴露信号）",
         "风险栏出现据点暴露信号" in f_12 and "wear-sabotage" in f_12,
         "若被删，人为破坏线断链")

    # RS-5: 2-3 Security/Exposure 枚举已删除
    f_23 = read_prompt("2-3_WorldStateKeeper_Extra_Details.md")
    test("RS-5", "2-3 Security/Exposure 枚举已删除",
         "Security/Exposure" not in f_23,
         "v1.67 删除该枚举行；若回归说明旧规则复活")

    # RS-6: 1-2 Maintenance Pressure 引用已清除
    test("RS-6", "1-2 Maintenance Pressure 引用已清除",
         "Maintenance Pressure" not in f_12,
         "v1.67 删除 MP；若回归说明旧规则复活")


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("据点损耗机制触发链路测试（模拟建据点 + Day 推进）")
    print("=" * 60)

    # Part 1: 规则源
    test_rule_sources()

    # Part 2: Mock 场景 + 正例推演
    print("\n--- Part 2: Mock 场景与 WSK 预期输出日志 ---")
    print(MOCK_SCENARIO)
    print("\n--- 推演的 WSK 输出日志（规则完整形态，正例）---")
    print(WSK_EXPECTED_OUTPUT)
    check_wsk_output(WSK_EXPECTED_OUTPUT, "POS")

    # Part 3: 反例（模拟早期实际输出）
    print("\n--- Part 3: 反例日志（模拟早期实际输出：只有组件清单，无状态字段）---")
    print(WSK_REGRESS_OUTPUT)
    check_wsk_output(WSK_REGRESS_OUTPUT, "REG")

    # Part 4: 真实输出校验
    print("\n--- Part 4: 真实输出校验 ---")
    if REAL_OUTPUT_FILE.exists():
        real = REAL_OUTPUT_FILE.read_text(encoding="utf-8").strip()
        if real:
            print("检测到 wsk_real_output.txt，开始校验：")
            print(real)
            check_wsk_output(real, "REAL")
        else:
            print("[SKIP] wsk_real_output.txt 为空，跳过真实校验")
    else:
        print("[SKIP] 未找到 wsk_real_output.txt")
        print("       实测方法：在平台建据点并跨日后，把 WSK 的 [State Update] 全文")
        print("       粘贴到 tools/wsk_real_output.txt，重新运行本脚本即可自动校验")

    # 汇总
    print("\n" + "=" * 60)
    print(f"总计: {passed} passed, {failed} failed")
    if fail_list:
        print("\n失败项汇总:")
        for item in fail_list:
            print(f"  - {item['id']}: {item['desc']}" + (f" -- {item['detail']}" if item["detail"] else ""))
        print("\n[解读] POS 失败 = prompt 规则与推演不符（规则源问题）；")
        print("       REG 失败 = 正常（反例本就应检出缺失）；")
        print("       REAL 失败 = 平台实测输出缺失字段（LLM 执行问题，风险点1成立）")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
