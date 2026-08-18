#!/usr/bin/env python3
"""
Ash Harbor 据点损耗机制触发链路测试脚本

场景：模拟"建立据点并推进一天"（D5 -> D6, Storm 天气, 暴露事件成立），
按 prompt 规则推演 WSK 的预期输出日志，重点检查 Security/Exposure 等据点状态字段是否存在。

测试对象：
  1. 规则源检查：2-2 §[据点与庇护记录规则] L102 的 4 字段要求仍在位
  2. 正例推演：规则完整形态的 WSK 输出（LLM 完全遵守规则时应输出什么）-> 应全 PASS
  3. 反例：模拟早期实际输出（只有组件清单，无状态字段）-> 应检出缺失
  4. 真实输出校验：若 tools/wsk_real_output.txt 存在（用户从平台实测粘贴），对其做同样检查

字段存在性依据（2-2 §[据点与庇护记录规则]）：
  - L102: "对据点/庇护状态,至少应保留：Rest / Shelter Availability、Security / Exposure、Heat / Dryness、Maintenance Pressure"
  - L103a: Security/Exposure 三档 hidden / local-only / publicly-known
  - L105: 长期驻留时应有 Occupancy / Residency Load
  - L111: 每轮统一输出组件名 + 状态描述

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
  3. 暴露事件成立：白天搬运物资时被附近拾荒者远距看到（据点暴露 hidden -> local-only）
  4. Day 推进 D5->D6，天气 Storm（恶劣天气，天气损耗检查 Base 40）

[WM 侧输出]（供 WSK 提取的输入）
  [Move] ...
  [Probability Check] Trigger: 天气损耗（Storm 跨日）; Base: 40; Modifiers: 无加固组件+0; Final: 40; Seed: 12; Threshold: 40; Result: 未触发; Outcome: 组件暂时撑住
  [判定] 消耗（D5->D6）: 压缩饼干x0.5kg+净水x1kg; 据点建立: 化工厂质检小楼（主据点）; 代价与后果: 夜间 Storm，屋顶渗水未触发
  [主要状态] D6-T58 21:00 | 工业区/N/化工厂质检小楼 | Winter-Storm-零下12度 | 疲劳 strained；体温 strained；脱水 stable；饥饿 stable；伤病 stable |
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
Rest / Shelter Availability: 可住（起居室可过夜）
Security / Exposure: local-only（白天搬运被附近拾荒者远距看到）
Heat / Dryness: 有壁炉可取暖；地面偶有湿印
Maintenance Pressure: 低（新据点，组件完好）
Occupancy / Residency Load: 1人
大门: 门锁铁片翘起，内以木杠别住
起居室（旧会议室）: 可住，有壁炉
壁炉: 烟道通畅，可用
食品储藏室: 北墙铁架，已分类存放
天台集水器: 滤网已清，可用

6. 近五日主要事件:
D5: 进入工业区，搜刮获得罐头与大米
D6: 建立化工厂质检小楼主据点，物资转入据点核心；被附近拾荒者远距看到（暴露 local-only）"""

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

SECURITY_ENUM = ["hidden", "local-only", "publicly-known"]

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
         "2-2 L111 要求每轮统一输出组件名+状态描述")

    # BD-4: Security/Exposure 字段存在（核心检查）
    test(f"{prefix}-4", "Security/Exposure 字段存在",
         bool(re.search(r'Security\s*/\s*Exposure', base_sec)),
         "2-2 L102 要求至少保留 Security / Exposure；缺失则 1-2 L91 人为破坏检查无输入")

    # BD-5: Security/Exposure 取值合法
    sec_m = re.search(r'Security\s*/\s*Exposure\s*[:：]\s*(\S+)', base_sec)
    test(f"{prefix}-5", "Security/Exposure 取值合法枚举",
         bool(sec_m and any(e in sec_m.group(1) for e in SECURITY_ENUM)),
         f"合法值: {SECURITY_ENUM}" + (f"；实际值: {sec_m.group(1)}" if sec_m else "；未找到取值"))

    # BD-6: Maintenance Pressure 字段存在
    test(f"{prefix}-6", "Maintenance Pressure 字段存在",
         bool(re.search(r'Maintenance\s*Pressure', base_sec)),
         "2-2 L102 要求至少保留 Maintenance Pressure")

    # BD-7: Rest/Shelter Availability 字段存在
    test(f"{prefix}-7", "Rest/Shelter Availability 字段存在",
         bool(re.search(r'Rest\s*/\s*Shelter\s*Availability', base_sec)),
         "2-2 L102 要求至少保留 Rest / Shelter Availability")

    # BD-8: Heat/Dryness 字段存在
    test(f"{prefix}-8", "Heat/Dryness 字段存在",
         bool(re.search(r'Heat\s*/\s*Dryness', base_sec)),
         "2-2 L102 要求至少保留 Heat / Dryness")

    # BD-9: 长期驻留时 Occupancy / Residency Load 存在
    test(f"{prefix}-9", "长期驻留时 Occupancy / Residency Load 存在",
         bool(re.search(r'Occupancy\s*/\s*Residency\s*Load', base_sec)),
         "2-2 L105 要求长期驻留据点更新此字段")


# ============================================================
# Part 1: 规则源检查（确认 prompt 规则仍在位）
# ============================================================

def test_rule_sources():
    print("\n--- Part 1: 规则源检查（prompt 规则仍在位）---")
    f_22 = read_prompt("2-2_WorldStateKeeper_Additional_Personality_Details.md")

    # RS-1: 2-2 L102 四字段要求存在
    test("RS-1", "2-2 L102 四字段保留要求仍在位",
         "至少应保留" in f_22 and "Security / Exposure" in f_22 and "Maintenance Pressure" in f_22,
         "若被删，WSK 无义务输出状态字段，人为破坏检查断链")

    # RS-2: 2-2 L103a 三档定义存在
    test("RS-2", "2-2 L103a Security/Exposure 三档定义仍在位",
         "hidden" in f_22 and "local-only" in f_22 and "publicly-known" in f_22)

    # RS-3: 2-2 L105 长期驻留字段存在
    test("RS-3", "2-2 L105 长期驻留 Occupancy 字段仍在位",
         "Occupancy / Residency Load" in f_22)

    # RS-4: 1-2 人为破坏检查指令存在（消费端）
    f_12 = read_prompt("1-2_WorldMaster_Additional_Personality_Details.md")
    test("RS-4", "1-2 L91 人为破坏检查输入指令仍在位",
         "检查上一轮 WSK State Update 中的 Security/Exposure 档位" in f_12,
         "若被删，WM 不会去读该字段")

    # RS-5: 2-3 L132 枚举定义存在
    f_23 = read_prompt("2-3_WorldStateKeeper_Extra_Details.md")
    test("RS-5", "2-3 L132 Security/Exposure 枚举仍在位",
         bool(re.search(r'Security/Exposure:\s*hidden\s*/\s*local-only\s*/\s*publicly-known', f_23)))


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
