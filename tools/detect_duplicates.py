#!/usr/bin/env python3
"""
Ash Harbor 重复检测脚本（PAM v1.2 Phase 1.3）

功能：
  1.3 SSOT 重复检测：提取所有 [section] 内容块，检测跨文件/跨节的重复内容
    - 逐字重复：行级精确匹配
    - 疑似重复：Jaccard 相似度 > 阈值

注意：语义等价（陷阱 #19，文字不同但意思相同）仍需人工判断，本脚本只做文本级检测。

用法: python tools/detect_duplicates.py
"""

import re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_DIR = PROJECT_ROOT / "Prompt_File"

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

SIMILARITY_THRESHOLD = 0.7
MIN_BLOCK_LINES = 3  # 最少行数才参与比对（过滤过短的节）

def short_name(filename):
    return FILE_SHORT.get(filename, filename)

def is_chatroom(filename):
    """判断文件是否为聊天室级字段（0-x）"""
    short = short_name(filename)
    return short.startswith("0-")

def is_role_card(filename):
    """判断文件是否为角色卡字段（1-x / 2-x）"""
    short = short_name(filename)
    return short.startswith("1-") or short.startswith("2-")

def is_intentional_inline(file_a, file_b):
    """
    判断重复是否为角色卡从聊天室字段有意内联（PAM v1.2 2026-08-10 例外）。
    角色卡（1-x/2-x）从聊天室（0-x）内联 = 有意，不计为重复。
    """
    return (is_role_card(file_a) and is_chatroom(file_b)) or \
           (is_role_card(file_b) and is_chatroom(file_a))


def extract_sections(filename, content):
    """
    提取文件中所有 [section] 及其内容块。
    返回 [(section_name, [lines])]
    """
    sections = []
    lines = content.split('\n')

    current_section = None
    current_lines = []

    for line in lines:
        match = re.match(r'^\[([^\]]+)\]', line)
        if match:
            # 保存上一个 section
            if current_section is not None:
                sections.append((current_section, current_lines))
            current_section = match.group(1)
            current_lines = []
        else:
            if current_section is not None:
                current_lines.append(line)

    # 保存最后一个 section
    if current_section is not None:
        sections.append((current_section, current_lines))

    return sections


def normalize_lines(lines):
    """标准化行：去首尾空格、去空行、转小写"""
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            result.append(stripped)
    return result


def jaccard_similarity(set_a, set_b):
    """计算两个集合的 Jaccard 相似度"""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def main():
    # 加载所有文件的 section 块
    all_blocks = []  # [(file, section_name, normalized_line_set, line_count)]

    for md in sorted(PROMPT_DIR.glob("*.md")):
        with open(md, "r", encoding="utf-8") as f:
            content = f.read()
        sections = extract_sections(md.name, content)
        for section_name, raw_lines in sections:
            norm_lines = normalize_lines(raw_lines)
            if len(norm_lines) >= MIN_BLOCK_LINES:
                line_set = set(norm_lines)
                all_blocks.append((md.name, section_name, line_set, len(norm_lines)))

    print("=" * 60)
    print("1.3 SSOT 重复检测")
    print("=" * 60)
    print()
    print(f"扫描文件: {len(set(b[0] for b in all_blocks))}")
    print(f"提取 section 块: {len(all_blocks)}")
    print(f"相似度阈值: {SIMILARITY_THRESHOLD}")
    print(f"最小块行数: {MIN_BLOCK_LINES}")
    print()

    # 1. 逐字重复检测：完全相同的行集
    exact_dupes = []
    skipped_inlines = []
    for i, (file_a, sec_a, lines_a, count_a) in enumerate(all_blocks):
        for j, (file_b, sec_b, lines_b, count_b) in enumerate(all_blocks):
            if j <= i:
                continue
            if lines_a == lines_b and count_a >= MIN_BLOCK_LINES:
                if is_intentional_inline(file_a, file_b):
                    skipped_inlines.append((file_a, sec_a, file_b, sec_b, count_a))
                else:
                    exact_dupes.append((file_a, sec_a, file_b, sec_b, count_a))

    print(f"逐字重复（行集完全相同）: {len(exact_dupes)} 对")
    for file_a, sec_a, file_b, sec_b, count in exact_dupes:
        print(f"  ❌ [{short_name(file_a)}] [{sec_a}] <-> [{short_name(file_b)}] [{sec_b}] ({count} lines)")

    if skipped_inlines:
        print(f"\n有意内联（角色卡 <- 聊天室，PAM 例外，不计违规）: {len(skipped_inlines)} 对")
        for file_a, sec_a, file_b, sec_b, count in skipped_inlines:
            print(f"  ✅ [{short_name(file_a)}] [{sec_a}] <-> [{short_name(file_b)}] [{sec_b}] ({count} lines)")

    # 2. 疑似重复：Jaccard 相似度 > 阈值（排除完全相同的）
    similar_pairs = []
    for i, (file_a, sec_a, lines_a, count_a) in enumerate(all_blocks):
        for j, (file_b, sec_b, lines_b, count_b) in enumerate(all_blocks):
            if j <= i:
                continue
            if lines_a == lines_b:
                continue  # 已在逐字重复中报告
            sim = jaccard_similarity(lines_a, lines_b)
            if sim >= SIMILARITY_THRESHOLD:
                if is_intentional_inline(file_a, file_b):
                    continue  # 有意内联，跳过
                similar_pairs.append((file_a, sec_a, file_b, sec_b, sim, min(count_a, count_b)))

    # 按相似度降序
    similar_pairs.sort(key=lambda x: -x[4])

    print()
    print(f"疑似重复（Jaccard > {SIMILARITY_THRESHOLD}）: {len(similar_pairs)} 对")
    for file_a, sec_a, file_b, sec_b, sim, count in similar_pairs:
        print(f"  ⚠️ [{short_name(file_a)}] [{sec_a}] <-> [{short_name(file_b)}] [{sec_b}] sim={sim:.2f} ({count} lines)")

    total = len(exact_dupes) + len(similar_pairs)
    print()
    if total == 0:
        inline_count = len(skipped_inlines)
        print(f"✅ 1.3 重复检测: 0 issues (scanned {len(all_blocks)} blocks, threshold={SIMILARITY_THRESHOLD}, {inline_count} intentional inlines skipped)")
    else:
        print(f"⚠️ 1.3 重复检测: {total} pairs (exact={len(exact_dupes)}, similar={len(similar_pairs)}, skipped={len(skipped_inlines)} intentional inlines)")
    print()
    print("注：语义等价（陷阱 #19，文字不同但意思相同）仍需人工判断。")

    return 1 if total else 0


if __name__ == "__main__":
    exit(main())
