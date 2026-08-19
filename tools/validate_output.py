#!/usr/bin/env python3
"""
Ash Harbor WSK 输出格式验证脚本

功能：
  验证 test_cases/ 下的 WSK 输出样本是否符合 prompt 格式规则。
  - 正例（## WSK 正确输出）：应通过所有规则
  - 反例（## WSK 错误输出）：应检测到至少一个违规

验证规则（依据 2-1/2-3 prompt）：
  R1  输出开头：必须以 [State Update] 或 - 开头
  R2  第一行格式：[State Update] 行必须包含 D{数字}-T{数字}
  R3  Inventory Delta 标签必出：必须包含 "Inventory Delta:" 行
  R4  6 字段必出：Inventory State / Party Condition / Relationship & Threat / Map Knowledge / Base Structure State / 近五日主要事件
  R5  无 ## 标题：不应包含 ## 或 ### 开头的行
  R6  - 输出检查：以 - 开头时应只有一行
  R7  字段顺序：Inventory Delta 在 6 字段之前

用法: python tools/validate_output.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TEST_CASES_DIR = PROJECT_ROOT / "test_cases"

# 6 字段标签（按出场次序）
REQUIRED_FIELDS = [
    "Inventory State",
    "Party Condition",
    "Relationship & Threat",
    "Map Knowledge",
    "Base Structure State",
    "近五日主要事件",
]

# --- 解析测试用例 ---

def parse_test_case(filepath):
    """解析测试用例文件，提取正例和反例代码块"""
    content = filepath.read_text(encoding="utf-8")
    name = filepath.stem

    cases = []

    # 提取所有 ## 标题及其后的代码块
    sections = re.split(r'^## ', content, flags=re.MULTILINE)
    for section in sections[1:]:  # 跳过第一部分（文件头）
        lines = section.split('\n')
        header = lines[0].strip()
        body = '\n'.join(lines[1:])

        # 提取代码块
        code_blocks = re.findall(r'```\n(.*?)```', body, re.DOTALL)
        if not code_blocks:
            continue

        for block in code_blocks:
            block = block.strip()
            if not block:
                continue

            if header.startswith("WSK 正确输出"):
                cases.append({
                    "name": name,
                    "type": "positive",
                    "label": header,
                    "output": block,
                })
            elif header.startswith("WSK 错误输出"):
                cases.append({
                    "name": name,
                    "type": "negative",
                    "label": header,
                    "output": block,
                })

    return cases


# --- 验证规则 ---

def check_rules(output):
    """对 WSK 输出运行所有验证规则，返回违规列表"""
    violations = []
    lines = output.strip().split('\n')
    first_line = lines[0].strip() if lines else ""

    # R1: 输出开头
    if not (first_line.startswith("[State Update]") or first_line == "-"):
        violations.append({
            "rule": "R1",
            "desc": f"输出必须以 [State Update] 或 - 开头，实际开头: {first_line[:40]}",
        })

    # R6: - 输出应只有一行
    if first_line == "-" and len(lines) > 1:
        non_empty = [l for l in lines[1:] if l.strip()]
        if non_empty:
            violations.append({
                "rule": "R6",
                "desc": f"以 - 开头时应只有一行，实际有 {len(non_empty)} 行额外内容",
            })

    # 如果是 - 输出，后续规则不适用
    if first_line == "-":
        return violations

    # R2: 第一行格式
    if first_line.startswith("[State Update]"):
        if not re.search(r'D\d+-T\d+', first_line):
            violations.append({
                "rule": "R2",
                "desc": f"[State Update] 行必须包含 D{{数字}}-T{{数字}}，实际: {first_line}",
            })

    # R5: 无 ## 标题
    for i, line in enumerate(lines):
        if line.strip().startswith("##"):
            violations.append({
                "rule": "R5",
                "desc": f"不应包含 ## 标题（第 {i+1} 行: {line.strip()[:40]}）",
            })

    # R3: Inventory Delta 标签
    has_delta = any("Inventory Delta:" in line for line in lines)
    if not has_delta:
        violations.append({
            "rule": "R3",
            "desc": "缺少 Inventory Delta: 标签",
        })

    # R4: 6 字段必出
    full_text = '\n'.join(lines)
    for field in REQUIRED_FIELDS:
        # 字段可能以 "1. Inventory State:" 或 "Inventory State:" 形式出现
        if field not in full_text:
            violations.append({
                "rule": "R4",
                "desc": f"缺少必出字段: {field}",
            })

    # R7: 字段顺序（Inventory Delta 在 6 字段之前）
    delta_pos = -1
    first_field_pos = -1
    for i, line in enumerate(lines):
        if "Inventory Delta:" in line and delta_pos == -1:
            delta_pos = i
        for field in REQUIRED_FIELDS:
            if field in line and first_field_pos == -1:
                first_field_pos = i
                break

    if delta_pos != -1 and first_field_pos != -1 and delta_pos > first_field_pos:
        violations.append({
            "rule": "R7",
            "desc": f"Inventory Delta（行 {delta_pos+1}）应在 6 字段（首次出现行 {first_field_pos+1}）之前",
        })

    return violations


# --- 主流程 ---

def main():
    if not TEST_CASES_DIR.exists():
        print("=" * 60)
        print("WSK 输出格式验证")
        print("=" * 60)
        print()
        print(f"❌ 测试用例目录不存在: {TEST_CASES_DIR}")
        return 1

    # 收集所有测试用例
    all_cases = []
    for md in sorted(TEST_CASES_DIR.glob("*.md")):
        cases = parse_test_case(md)
        all_cases.extend(cases)

    if not all_cases:
        print("=" * 60)
        print("WSK 输出格式验证")
        print("=" * 60)
        print()
        print(f"⚠️ 未找到测试用例（扫描 {TEST_CASES_DIR}）")
        return 0

    print("=" * 60)
    print("WSK 输出格式验证 (validate_output)")
    print("=" * 60)
    print()
    print(f"测试用例文件: {len(list(TEST_CASES_DIR.glob('*.md')))}")
    print(f"测试样本总数: {len(all_cases)}")

    positives = [c for c in all_cases if c["type"] == "positive"]
    negatives = [c for c in all_cases if c["type"] == "negative"]
    print(f"  正例（应通过）: {len(positives)}")
    print(f"  反例（应检测到违规）: {len(negatives)}")
    print()

    # 验证正例
    pos_pass = 0
    pos_fail = 0
    for case in positives:
        violations = check_rules(case["output"])
        if not violations:
            pos_pass += 1
        else:
            pos_fail += 1
            print(f"  ❌ [正例失败] {case['name']} - {case['label']}")
            for v in violations:
                print(f"      [{v['rule']}] {v['desc']}")

    # 验证反例
    neg_pass = 0
    neg_fail = 0
    for case in negatives:
        violations = check_rules(case["output"])
        if violations:
            neg_pass += 1
        else:
            neg_fail += 1
            print(f"  ❌ [反例未检出] {case['name']} - {case['label']}")
            print(f"      期望检测到违规但未检出")

    # 汇总
    print()
    print("验证结果:")
    print(f"  正例通过: {pos_pass}/{len(positives)}")
    print(f"  反例检出: {neg_pass}/{len(negatives)}")
    total_fail = pos_fail + neg_fail
    if total_fail == 0:
        print(f"✅ validate_output: 全部通过 (scanned {len(all_cases)} cases)")
    else:
        print(f"⚠️ validate_output: {total_fail} failures (scanned {len(all_cases)} cases)")

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    # Windows 管道/GBK 终端下强制 UTF-8 输出，避免 ✅/❌ 触发 UnicodeEncodeError
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    exit(main())
