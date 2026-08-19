#!/usr/bin/env python3
"""
Ash Harbor 引用关系图 + 引用活性检查脚本（PAM v1.2 Phase 1.1 + 1.5）

功能：
  1.1 引用活性：扫描 §[章节名] 断链 + 口语化引用（陷阱 #14）
  1.5 节名引用链：孤立章节检测
  附带输出 Mermaid 格式引用关系图 -> tools/ref_graph.mmd

用法: python tools/gen_ref_graph.py
"""

import re
import os
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_DIR = PROJECT_ROOT / "Prompt_File"
OUTPUT_PATH = PROJECT_ROOT / "tools" / "ref_graph.mmd"

# 匹配 §[章节名] 和 §[[章节名]]（双括号形式）
REF_PATTERN_BRACKET = re.compile(r'§\[{1,2}([^\]]+)\]')

# 匹配 §章节名（非括号形式）-- 排除 [ ] ` 防止重复匹配括号引用和反引号侵入
REF_PATTERN_PLAIN = re.compile(r'§([^\s,，。；;（）\(\)\[\]`]+)')

# 匹配聊天室字段引用
CHATROOM_REF_PATTERN = re.compile(r'聊天室\s*(?:Scenario|Private Details|自定义指令)?\s*字段\s*§\[?([^\]），\s]+)')

# --- 陷阱 #14：口语化引用模式（未使用 § 前缀） ---
# "按 X 条" / "按 X 律" / "按 X 规则" -- 不含 §
COLLOQUIAL_REF_PATTERN_1 = re.compile(r'按\s*([^\s§`]{2,12})\s*[条律规则]')
# "见 X 规则" / "见 X 机制" / "见 X 表" / "见 X 协议" -- 不含 §
COLLOQUIAL_REF_PATTERN_2 = re.compile(r'见\s*([^\s§`]{2,15})\s*(?:规则|机制|表|协议|矩阵)')
# "参照 X" -- 不含 §
COLLOQUIAL_REF_PATTERN_3 = re.compile(r'参照\s*([^\s§`]{2,15})')

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

def extract_sections(filename, content):
    """提取文件中定义的所有 [章节名]"""
    sections = set()
    for match in re.finditer(r'^\[([^\]]+)\]', content, re.MULTILINE):
        sections.add(match.group(1))
    return sections

def extract_references(filename, content):
    """提取文件中的所有 § 引用"""
    refs = []
    seen = set()  # 去重：(filename, section)
    
    # §[章节名] 形式（含 §[[章节名]] 双括号）
    for match in REF_PATTERN_BRACKET.finditer(content):
        section = match.group(1)
        # 清理：去除反引号和前导 [
        section = section.strip('`').lstrip('[').rstrip('`')
        if section and (filename, section) not in seen:
            seen.add((filename, section))
            refs.append(("bracket", section, match.start()))
    
    # §章节名 形式（排除括号引用）
    for match in REF_PATTERN_PLAIN.finditer(content):
        section = match.group(1)
        # 清理：去除反引号
        section = section.strip('`')
        if section and (filename, section) not in seen:
            seen.add((filename, section))
            refs.append(("plain", section, match.start()))
    
    return refs

def extract_colloquial_refs(filename, content):
    """
    提取口语化引用（陷阱 #14）：未使用 § 前缀的引用模式。
    返回 [(pattern_type, matched_text, captured_ref, line_number)]
    """
    # 常见非引用词，匹配到这些的跳过（减少误报）
    FALSE_POSITIVE_WORDS = {
        '混合', '口径', '时钟', '暴露', '自包含原', '需', 'step', '实际',
        '上一轮', '场景', '消耗', '优先', '行', '区', '基', '步',
    }

    results = []
    patterns = [
        ("按X条/律/规则", COLLOQUIAL_REF_PATTERN_1),
        ("见X规则/机制/表", COLLOQUIAL_REF_PATTERN_2),
        ("参照X", COLLOQUIAL_REF_PATTERN_3),
    ]
    for ptype, pattern in patterns:
        for match in pattern.finditer(content):
            # 排除：已含 § 的行段（在同一行中如果附近有 § 则跳过）
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.end())
            if line_end == -1:
                line_end = len(content)
            line_text = content[line_start:line_end]
            if '§' in line_text:
                continue

            # 排除："见" 前一个字与 "见" 构成常见词（如 意见/发现/看见/遇见/听见）
            match_start = match.start()
            if ptype == "见X规则/机制/表" and match_start > 0:
                prev_char = content[match_start - 1]
                if prev_char in '意发看遇听见':
                    continue

            captured = match.group(1)

            # 排除：匹配到的后缀字符是更长词的一部分
            # 如 "条目" 中的 "条"、"规格" 中的 "规"
            match_end = match.end()
            if match_end < len(content):
                next_char = content[match_end]
                # "条" 后接 "目" = 条目（非引用）
                if match.group(0).endswith('条') and next_char == '目':
                    continue
                # "规" 后接 "格" = 规格（非引用）
                if match.group(0).endswith('规') and next_char == '格':
                    continue

            # 排除常见非引用词
            if any(fp in captured for fp in FALSE_POSITIVE_WORDS):
                continue

            # 参照X 模式：要求 X 以规则/机制/表/协议等结尾或包含节名关键词
            if ptype == "参照X":
                if not any(kw in captured for kw in ['规则', '机制', '表', '协议', '矩阵', '节', '段']):
                    # 检查 captured 是否匹配某个已定义 section 名
                    continue

            line_num = get_line_number(content, match.start())
            results.append((ptype, match.group(0), captured, line_num))
    return results

def get_line_number(content, pos):
    """根据字符位置获取行号"""
    return content[:pos].count('\n') + 1

def main():
    files = {}
    all_sections = {}  # filename -> set of section names
    all_refs = []      # (source_file, ref_type, section_name, line_number)
    
    # 加载所有文件
    for md in sorted(PROMPT_DIR.glob("*.md")):
        with open(md, "r", encoding="utf-8") as f:
            content = f.read()
            files[md.name] = content
            all_sections[md.name] = extract_sections(md.name, content)
            
            for ref_type, section, pos in extract_references(md.name, content):
                line_num = get_line_number(content, pos)
                all_refs.append((md.name, ref_type, section, line_num))
    
    # 收集口语化引用
    all_colloquial_refs = []  # (source_file, pattern_type, matched_text, captured_ref, line)
    for md_name, content in files.items():
        for ptype, matched, captured, line in extract_colloquial_refs(md_name, content):
            all_colloquial_refs.append((md_name, ptype, matched, captured, line))
    
    # 构建引用图
    # edges: source_file -> [(target_file, section, line)]
    edges = defaultdict(list)
    broken_refs = []
    
    for source_file, ref_type, section, line in all_refs:
        # 查找哪个文件定义了这个 section
        target_file = None
        for fname, sections in all_sections.items():
            if section in sections:
                target_file = fname
                break
        
        if target_file:
            edges[source_file].append((target_file, section, line))
        else:
            broken_refs.append((source_file, section, line))
    
    # 查找孤立章节（定义了但无任何文件引用）
    all_defined_sections = set()
    for sections in all_sections.values():
        all_defined_sections.update(sections)
    
    all_referenced_sections = set()
    for _, _, section, _ in all_refs:
        all_referenced_sections.add(section)
    
    orphan_sections = all_defined_sections - all_referenced_sections
    
    # 生成 Mermaid 图
    lines = ["graph LR"]
    
    # 节点定义
    for fname in sorted(files.keys()):
        short = FILE_SHORT.get(fname, fname)
        lines.append(f'    {short}["{short}"]')
    
    lines.append("")
    
    # 边定义（按源文件分组）
    for source in sorted(edges.keys()):
        short_source = FILE_SHORT.get(source, source)
        seen_targets = set()
        for target, section, line in edges[source]:
            short_target = FILE_SHORT.get(target, target)
            edge_key = (short_source, short_target)
            if edge_key not in seen_targets:
                lines.append(f'    {short_source} --> {short_target}')
                seen_targets.add(edge_key)
    
    # 输出断链
    lines.append("")
    lines.append("%% 断链引用")
    for source, section, line in broken_refs:
        short = FILE_SHORT.get(source, source)
        lines.append(f'    %% {short} L{line}: §[{section}] -> 未找到目标')
    
    # 写入文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    # 控制台报告
    print("=" * 60)
    print("1.1 引用活性 + 1.5 节名引用链 检查报告")
    print("=" * 60)
    print()
    print(f"扫描文件: {len(files)}")
    print(f"定义章节: {len(all_defined_sections)}")
    print(f"§引用总数: {len(all_refs)}")
    print(f"有效引用: {sum(len(v) for v in edges.values())}")
    print(f"断链引用: {len(broken_refs)}")
    print(f"孤立章节: {len(orphan_sections)}")
    print(f"口语化引用: {len(all_colloquial_refs)}")
    print()
    
    if broken_refs:
        print("断链引用:")
        for source, section, line in broken_refs:
            short = FILE_SHORT.get(source, source)
            print(f"  ❌ {short} L{line}: §[{section}]")
    
    if all_colloquial_refs:
        print()
        print(f"口语化引用（陷阱 #14，未使用 § 前缀）({len(all_colloquial_refs)}):")
        for source, ptype, matched, captured, line in all_colloquial_refs:
            short = FILE_SHORT.get(source, source)
            print(f"  ⚠️ [{short} L{line}] [{ptype}] '{matched}' -> captured: '{captured}'")
    else:
        print(f"✅ 1.1 口语化引用: 0 issues (scanned {len(files)} files)")
    
    if orphan_sections:
        print()
        print("孤立章节（定义了但无引用）:")
        for section in sorted(orphan_sections):
            print(f"  ⚠️ [{section}]")
    
    print()
    print(f"引用图已输出: {OUTPUT_PATH}")
    
    return 1 if broken_refs else 0

if __name__ == "__main__":
    import sys
    # Windows 管道/GBK 终端下强制 UTF-8 输出，避免 ✅/❌ 触发 UnicodeEncodeError
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    exit(main())
