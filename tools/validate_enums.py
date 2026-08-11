#!/usr/bin/env python3
"""
Ash Harbor 枚举一致性校验脚本（PAM v1.2 Phase 1.2 + 1.6）

功能：
  --enum-check : 跨文件枚举值集合比对（1.6，陷阱 #22）
  --term-check : 弃用术语扫描（1.2）
  不带参数时两项都执行

用法:
  python tools/validate_enums.py              # 全部检查
  python tools/validate_enums.py --enum-check  # 仅枚举一致性
  python tools/validate_enums.py --term-check  # 仅术语一致性
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_DIR = PROJECT_ROOT / "Prompt_File"
REGISTRY_PATH = PROJECT_ROOT / "tools" / "enum_registry.json"

# 文件简称映射
FILE_SHORT = {
    "0-1_Private_Details.md": "0-1",
    "0-2_Scenario.md": "0-2",
    "0-3_自定义指令.md": "0-3",
    "1-1_WorldMaster_Scene.md": "1-1",
    "1-2_WorldMaster_Additional_Personality_Details.md": "1-2",
    "1-3_WorldMaster_Extra_Details.md": "1-3",
    "2-1_WorldStateKeeper_Scene.md": "2-1",
    "2-2_WorldStateKeeper_Additional_Personality_Details.md": "2-2",
    "2-3_WorldStateKeeper_Extra_Details.md": "2-3",
}

# 反向映射：短名 -> 完整文件名
SHORT_TO_FULL = {v: k for k, v in FILE_SHORT.items()}


def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_files():
    files = {}
    for md in sorted(PROMPT_DIR.glob("*.md")):
        with open(md, "r", encoding="utf-8") as f:
            files[md.name] = f.read()
    return files


def get_line_number(content, pos):
    return content[:pos].count('\n') + 1


def short_name(filename):
    return FILE_SHORT.get(filename, filename)


# ============================================================
# 1.6 跨文件枚举一致性检查
# ============================================================

def extract_inline_enum_lists(text, enum_values):
    """
    在文本中查找包含多个枚举值的行，返回每行的匹配值集合。
    不按分隔符拆分，而是直接搜索每个枚举值是否在行中出现（子串匹配）。
    这样可以正确处理含 / 的值名（如 "依恋/完全信任"）和各种分隔符（/ 、 、 等）。
    """
    if not enum_values:
        return []

    lists_found = []

    for line in text.split('\n'):
        # 跳过太长的行
        if len(line) > 500:
            continue

        found_in_line = set()
        for val in enum_values:
            if val in line:
                found_in_line.add(val)

        if len(found_in_line) >= 2:
            lists_found.append(found_in_line)

    return lists_found


def check_enum_consistency(registry, files):
    """
    对每个枚举类型，检查各文件中的内联枚举列表与注册表声明值集合是否一致。
    报告 missing（注册表有/文件列表无）、extra（文件列表有/注册表无）。
    """
    issues = []
    info = []

    for enum_key, enum_data in registry["enums"].items():
        registry_values = set(enum_data["values"])
        authority_file = enum_data["authority"]
        referenced_in = enum_data.get("referenced_in", [])

        # 将短名解析为完整文件名
        if authority_file in SHORT_TO_FULL:
            authority_file = SHORT_TO_FULL[authority_file]

        info.append(f"[ENUM] {enum_key}: {len(registry_values)} values, authority={short_name(authority_file)}")

        # 检查权威源文件存在性
        if authority_file not in files:
            issues.append(
                f"  [MISSING] {enum_key}: 权威源文件 {authority_file} 不存在于 Prompt_File/"
            )
            continue

        # 在所有引用文件 + 权威源文件中查找内联枚举列表
        check_files = set()
        for ref in referenced_in + [authority_file]:
            if ref in SHORT_TO_FULL:
                check_files.add(SHORT_TO_FULL[ref])
            else:
                check_files.add(ref)
        for filename in sorted(check_files):
            if filename not in files:
                issues.append(
                    f"  [MISSING] {enum_key}: 文件 {filename} 不存在于 Prompt_File/"
                )
                continue

            content = files[filename]
            inline_lists = extract_inline_enum_lists(content, registry_values)

            if not inline_lists:
                continue

            # 取该文件中最大的值集合（最完整的列表）
            max_list = max(inline_lists, key=len)

            # 集合差运算
            missing = registry_values - max_list
            extra = max_list - registry_values

            # 权威源必须包含完整枚举（检查 missing + extra）
            # 非权威源只检查非法值（extra），不检查缺失（missing）——部分引用是正常的（SSOT 原则）
            is_authority = (filename == authority_file)
            short = short_name(filename)

            if is_authority:
                if missing:
                    issues.append(
                        f"  [MISMATCH] {enum_key} in {short} (authority): "
                        f"missing {sorted(missing)} (registry has {len(registry_values)}, file list has {len(max_list)})"
                    )
                if extra:
                    issues.append(
                        f"  [MISMATCH] {enum_key} in {short} (authority): "
                        f"extra {sorted(extra)} (file list has values not in registry)"
                    )
            else:
                if extra:
                    issues.append(
                        f"  [MISMATCH] {enum_key} in {short}: "
                        f"extra {sorted(extra)} (file list has values not in registry)"
                    )

    return issues, info


# ============================================================
# 1.2 术语一致性检查
# ============================================================

def check_deprecated_terms(registry, files):
    """扫描全库弃用术语"""
    issues = []
    term_pairs = registry.get("term_pairs", {}).get("pairs", [])

    for filename, content in files.items():
        for pair in term_pairs:
            for deprecated in pair["deprecated"]:
                pattern = re.escape(deprecated)
                for match in re.finditer(pattern, content):
                    line_num = get_line_number(content, match.start())
                    issues.append({
                        "file": short_name(filename),
                        "line": line_num,
                        "deprecated": deprecated,
                        "unified": pair["unified"],
                        "context": pair.get("context", "")
                    })

    return issues


# ============================================================
# 主函数
# ============================================================

def main():
    args = set(sys.argv[1:])
    run_enum = "--enum-check" in args or len(args) == 0
    run_term = "--term-check" in args or len(args) == 0

    registry = load_registry()
    files = load_all_files()

    all_issues = []
    all_info = []

    if run_enum:
        print("=" * 60)
        print("1.6 跨文件枚举一致性检查")
        print("=" * 60)
        issues, info = check_enum_consistency(registry, files)
        all_issues.extend(issues)
        all_info.extend(info)

        print(f"\n扫描枚举类型: {len(registry['enums'])} 个")
        print(f"扫描文件: {len(files)} 个")

        if issues:
            print(f"\n不一致项 ({len(issues)}):")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n✅ 1.6 跨文件枚举一致性: 0 issues (scanned {len(registry['enums'])} enums, {len(files)} files)")

        print(f"\n枚举信息 ({len(info)}):")
        for i in info:
            print(f"  {i}")

    if run_term:
        print("\n" + "=" * 60)
        print("1.2 术语一致性检查")
        print("=" * 60)
        term_issues = check_deprecated_terms(registry, files)

        print(f"\n执行: rg 弃用术语 -> {len(term_issues)} 处")
        if term_issues:
            print(f"\n弃用术语 ({len(term_issues)}):")
            for item in term_issues:
                ctx = f" ({item['context']})" if item['context'] else ""
                print(f"  [{item['file']} L{item['line']}] '{item['deprecated']}' -> 应使用 '{item['unified']}'{ctx}")
        else:
            print(f"\n✅ 1.2 术语一致性: 0 issues (scanned {len(files)} files, {len(registry.get('term_pairs', {}).get('pairs', []))} term pairs)")

    return 1 if all_issues else 0


if __name__ == "__main__":
    exit(main())
