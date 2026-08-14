#!/usr/bin/env python3
"""提取孤立章节列表（定义了但无引用）"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"d:\Mycode\AshHarbor_OD_Trae\Ashport_Ourdream")
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

# 收集所有定义的 section 和所有引用
all_sections = {}  # section_name -> [files]
all_refs = set()

REF_PATTERN = re.compile(r'§\[{1,2}([^\]]+)\]')

for filename, short in FILE_SHORT.items():
    filepath = PROMPT_DIR / filename
    if not filepath.exists():
        continue
    content = filepath.read_text(encoding='utf-8')
    
    # 提取定义
    for match in re.finditer(r'^\[([^\]]+)\]', content, re.MULTILINE):
        sec = match.group(1)
        if sec not in all_sections:
            all_sections[sec] = []
        all_sections[sec].append(short)
    
    # 提取引用
    for match in REF_PATTERN.finditer(content):
        sec = match.group(1).strip('`').lstrip('[').rstrip('`')
        all_refs.add(sec)

# 孤立章节 = 定义了但未被引用
orphans = []
for sec, files in sorted(all_sections.items()):
    if sec not in all_refs:
        orphans.append((sec, files))

print(f"孤立章节总数: {len(orphans)}\n")
print(f"{'#':<4} {'Section':<55} {'File':<8} {'类型'}")
print("-" * 100)
for i, (sec, files) in enumerate(orphans, 1):
    files_str = "/".join(files)
    print(f"{i:<4} {sec:<55} {files_str:<8}")
