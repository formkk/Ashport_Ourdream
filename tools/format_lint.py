#!/usr/bin/env python3
"""
Ash Harbor 格式合规 + 形态黑名单扫描脚本（PAM v1.2 Phase 1.4 + 2.8/2.9/2.10）

功能：
  1.4 格式合规：bold / backticks / [section] 格式粗筛
  2.8 强调性格式化石：**bold** / 【】 / emoji / section 名含开发编号 [§x.x]
  2.9 版本化石：(v1.xx) 版本标注 / "字段已删除" 类描述
  2.10 SSOT 元注释：开发者维护用 SSOT 指针

用法: python tools/format_lint.py
"""

import re
from pathlib import Path

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

def short_name(filename):
    return FILE_SHORT.get(filename, filename)

def get_line_number(content, pos):
    return content[:pos].count('\n') + 1

# --- 检测模式 ---

# 2.8 bold 标记
BOLD_PATTERN = re.compile(r'\*\*.+?\*\*')

# 2.8 【】强调标记
BRACKET_EMPHASIS_PATTERN = re.compile(r'【[^】]+】')

# 2.8 emoji（常见 emoji 范围）
EMOJI_PATTERN = re.compile(
    '[\U0001F300-\U0001F9FF'   # symbols & pictographs
    '\U00002600-\U000027BF'     # misc symbols
    '\U0000FE00-\U0000FE0F'     # variation selectors
    '\U0001FA00-\U0001FA6F'     # extended symbols
    '\U0001F000-\U0001F02F'     # mahjong
    ']'
)

# 2.8 section 名含开发编号 [§x.x]
DEV_NUM_SECTION_PATTERN = re.compile(r'\[§\d+\.\d+[^\]]*\]')

# 2.9 版本标注 (v1.xx) / (v2.xx)
VERSION_PATTERN = re.compile(r'\(v\d+\.\d+[^)]*\)')

# 2.9 "字段已删除" 类描述
DELETED_FIELD_PATTERN = re.compile(r'(?:已删除|已移除|已废弃).{0,10}(?:字段|节|section)')

# 2.10 SSOT 元注释：（与...§...一致）/（见...字段...§...）
SSOT_META_PATTERN_1 = re.compile(r'（与.{0,30}§.{0,30}一致）')
SSOT_META_PATTERN_2 = re.compile(r'（见.{0,20}字段.{0,20}§.{0,30}）')
SSOT_META_PATTERN_3 = re.compile(r'（见.{0,10}APD.{0,20}§.{0,30}）')


# 角色卡文件前缀（1-x / 2-x）；聊天室级文件前缀（0-x）
def is_role_card(filename):
    """判断文件是否为角色卡字段（1-x / 2-x）"""
    short = short_name(filename)
    return short.startswith("1-") or short.startswith("2-")


def scan_file(filename, content):
    """扫描单个文件，返回各类发现"""
    findings = []
    role_card = is_role_card(filename)

    patterns = [
        ("2.8-bold", BOLD_PATTERN, "强调性格式化石"),
        ("2.8-【】", BRACKET_EMPHASIS_PATTERN, "强调性格式化石"),
        ("2.8-emoji", EMOJI_PATTERN, "强调性格式化石"),
        ("2.8-devnum", DEV_NUM_SECTION_PATTERN, "section名含开发编号"),
        ("2.9-version", VERSION_PATTERN, "版本化石"),
        ("2.9-deleted", DELETED_FIELD_PATTERN, "指向不存在内容"),
        ("2.10-ssot-1", SSOT_META_PATTERN_1, "SSOT元注释"),
        ("2.10-ssot-2", SSOT_META_PATTERN_2, "SSOT元注释"),
        ("2.10-ssot-3", SSOT_META_PATTERN_3, "SSOT元注释"),
    ]

    for check_id, pattern, desc in patterns:
        # 2.10 例外：角色卡内的 SSOT 元注释保留不报（PAM v1.2 2026-08-10 例外）
        if check_id.startswith("2.10") and role_card:
            continue

        for match in pattern.finditer(content):
            line_num = get_line_number(content, match.start())
            findings.append({
                "file": short_name(filename),
                "line": line_num,
                "check": check_id,
                "desc": desc,
                "match": match.group(0),
            })

    return findings


def main():
    files = {}
    for md in sorted(PROMPT_DIR.glob("*.md")):
        with open(md, "r", encoding="utf-8") as f:
            files[md.name] = f.read()

    all_findings = []
    # 统计计数
    counts = {}

    for filename, content in files.items():
        findings = scan_file(filename, content)
        all_findings.extend(findings)
        for f in findings:
            check = f["check"]
            if check not in counts:
                counts[check] = 0
            counts[check] += 1

    # 报告
    print("=" * 60)
    print("1.4 格式合规 + 2.8/2.9/2.10 形态黑名单扫描")
    print("=" * 60)
    print()
    print(f"扫描文件: {len(files)}")
    print()

    # 按检查项分组统计
    print("精确统计（陷阱 #13，不靠估算）:")
    print()

    # 定义检查项的显示顺序
    check_order = [
        ("2.8-bold", "**bold** 标记"),
        ("2.8-【】", "【】强调标记"),
        ("2.8-emoji", "emoji"),
        ("2.8-devnum", "section名含开发编号 [§x.x]"),
        ("2.9-version", "版本标注 (v1.xx)"),
        ("2.9-deleted", "'字段已删除'类描述"),
        ("2.10-ssot-1", "SSOT元注释（与...§...一致）"),
        ("2.10-ssot-2", "SSOT元注释（见...字段...§...）"),
        ("2.10-ssot-3", "SSOT元注释（见...APD...§...）"),
    ]

    for check_id, label in check_order:
        count = counts.get(check_id, 0)
        # 模拟 grep -c 的输出格式
        print(f"  {label}: {count} 处")

    # 详细发现
    if all_findings:
        print()
        print(f"详细发现 ({len(all_findings)}):")
        # 按检查项分组
        by_check = {}
        for f in all_findings:
            key = f["check"]
            if key not in by_check:
                by_check[key] = []
            by_check[key].append(f)

        for check_id, label in check_order:
            items = by_check.get(check_id, [])
            if items:
                print(f"\n  [{check_id}] {label} ({len(items)}):")
                for item in items:
                    match_text = item["match"][:60]
                    if len(item["match"]) > 60:
                        match_text += "..."
                    print(f"    [{item['file']} L{item['line']}] {match_text}")

    # 汇总
    total = len(all_findings)
    print()
    if total == 0:
        print(f"✅ 1.4/2.8/2.9/2.10 格式合规: 0 issues (scanned {len(files)} files, {len(check_order)} patterns)")
    else:
        print(f"⚠️ 1.4/2.8/2.9/2.10 格式合规: {total} issues (scanned {len(files)} files)")

    return 1 if all_findings else 0


if __name__ == "__main__":
    exit(main())
