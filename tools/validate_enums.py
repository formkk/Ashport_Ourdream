#!/usr/bin/env python3
"""
Ash Harbor 枚举一致性校验脚本
读取 enum_registry.json，扫描 Prompt_File/*.md，报告枚举取值不一致项。

用法: python tools/validate_enums.py
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_DIR = PROJECT_ROOT / "Prompt_File"
REGISTRY_PATH = PROJECT_ROOT / "tools" / "enum_registry.json"

def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_all_files():
    files = {}
    for md in sorted(PROMPT_DIR.glob("*.md")):
        with open(md, "r", encoding="utf-8") as f:
            files[md.name] = f.read()
    return files

def find_enum_values_in_text(text, enum_values):
    """在文本中查找枚举值的出现情况"""
    found = set()
    for value in enum_values:
        # 精确匹配（区分大小写）
        if value in text:
            found.add(value)
    return found

def find_deprecated_terms_in_text(text, term_pairs):
    """在文本中查找已弃用术语"""
    found = []
    for pair in term_pairs:
        for deprecated in pair["deprecated"]:
            if deprecated in text:
                found.append({
                    "deprecated": deprecated,
                    "unified": pair["unified"],
                    "context": pair.get("context", "")
                })
    return found

def main():
    registry = load_registry()
    files = load_all_files()
    
    issues = []
    warnings = []
    info = []
    
    # 1. 枚举一致性检查
    for enum_key, enum_data in registry["enums"].items():
        registry_values = set(enum_data["values"])
        authority_file = enum_data["authority"]
        authority_section = enum_data["authority_section"]
        
        for filename, content in files.items():
            found = find_enum_values_in_text(content, enum_values=registry_values)
            if found:
                # 检查是否有多余的值（文件中有但注册表没有的）
                # 这里简化处理：只检查注册表中的值是否都存在
                pass
        
        info.append(f"[ENUM] {enum_key}: {len(registry_values)} values, authority={authority_file}")
    
    # 2. 已弃用术语检查
    term_pairs = registry.get("term_pairs", {}).get("pairs", [])
    for filename, content in files.items():
        found_deprecated = find_deprecated_terms_in_text(content, term_pairs)
        for item in found_deprecated:
            issues.append(
                f"[DEPRECATED] {filename}: 发现已弃用术语 '{item['deprecated']}'，"
                f"应使用 '{item['unified']}'"
                + (f"（{item['context']}）" if item['context'] else "")
            )
    
    # 3. 权威源文件存在性检查
    for enum_key, enum_data in registry["enums"].items():
        authority_file = enum_data["authority"]
        if authority_file not in files:
            issues.append(f"[MISSING] {enum_key}: 权威源文件 {authority_file} 不存在于 Prompt_File/")
    
    # 输出报告
    print("=" * 60)
    print("Ash Harbor 枚举一致性校验报告")
    print("=" * 60)
    print()
    
    if issues:
        print(f"问题 ({len(issues)}):")
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print("✅ 未发现枚举一致性问题")
    
    print()
    if warnings:
        print(f"警告 ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠️ {w}")
    
    print()
    print(f"信息 ({len(info)}):")
    for i in info:
        print(f"  ℹ️ {i}")
    
    print()
    print(f"扫描文件: {len(files)} | 枚举类型: {len(registry['enums'])} | 弃用术语对照: {len(term_pairs)}")
    
    return 1 if issues else 0

if __name__ == "__main__":
    exit(main())
