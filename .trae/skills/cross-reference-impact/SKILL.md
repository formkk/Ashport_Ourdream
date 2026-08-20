---
name: "cross-reference-impact"
description: "Analyzes cross-reference impact when modifying prompt rules, enums, or sections. Invoke when user wants to modify a rule and needs to know what else will be affected, or before making changes to Prompt_Files."
---

# Cross-Reference Impact Analysis

This skill identifies all locations in the project that reference a specific file, section, enum, or rule -- before the user makes changes. It prevents "change one place, forget to sync others" errors.

## When to Invoke
- User says "我想修改 X" / "我要改 X 规则" / "X 需要调整" and wants to know impact
- User wants to rename a section, change an enum value, or modify a rule
- Before executing any change to `Prompt_File/*.md`

## Analysis Steps

### Step 1: Identify the Modification Target
Determine what the user wants to modify:
- A **section** (e.g., `§[掷骰 块]`)
- An **enum value** (e.g., adding a new Weather type)
- A **rule** (e.g., changing step calculation)
- A **file** (e.g., restructuring 1-3)

### Step 2: Grep All Reference Patterns
Scan ALL files in `Prompt_File/` for references to the target:

1. **Formal references**: Grep `§[章节名]` and `§章节名` patterns
2. **Oral references**: Grep patterns like `按 X 条` / `见 X 规则` / `按 X 律` / `按 X 机制` / `按 X 协议`
3. **Enum mentions**: If modifying an enum, Grep each enum value across all files
4. **Inline copies**: If modifying 0-1/0-2, check if role cards (1-x/2-x) have inline copies that need sync (see `prompt-engineering.mdr` 自包含要求 table)
5. **Section name mentions**: Grep the section name itself (without `§` prefix) to catch informal mentions

### Step 3: Categorize Each Reference
For each found reference, classify:

| Category | Description | Action Required |
|----------|-------------|-----------------|
| **Direct reference** | `§[章节名]` pointing to modified section | Update if section renamed; sync if content changed |
| **Inline copy** | Role card has inlined copy of the rule/table | Must sync content changes |
| **Enum usage** | File uses the enum value being modified | Must sync value changes |
| **Oral reference** | Informal mention like "按 X 规则" | Update if rule name changed |
| **Authority source** | The file IS the authority source for this data | All other references depend on this; changes propagate everywhere |

### Step 4: Check Inline Dependency
If modifying 0-1/0-2:
- Cross-reference with `prompt-engineering.mdr` "WM/WSK 自包含要求" table
- List all role card fields that have inline copies of the modified content
- Mark each as "needs sync"

If modifying 1-x/2-x:
- Check if the modified content is an inline copy of 0-1/0-2
- If so, note the authority source for consistency verification

### Step 5: Generate Impact Report

Output format:

```
## 影响范围分析：{修改目标描述}

### 修改目标
- 文件：{文件名}
- 位置：{章节/行号}
- 修改类型：{section rename / enum change / rule modification / file restructure}

### 受影响位置清单
| # | 文件 | 行号 | 引用类型 | 当前内容 | 需要操作 |
|---|------|------|----------|----------|----------|
| 1 | 1-2_WorldMaster_... | L20 | §[章节名] | `§[掷骰 块]` | 更新章节名 |
| 2 | 2-3_WorldState... | L87 | 枚举使用 | `9mm / .45 ACP / ...` | 同步取值 |
| 3 | 1-3_WorldMaster_... | L178 | 内联副本 | 容器描述+约kg格式 | 同步内容 |

### 内联同步清单（若修改 0-1/0-2）
| 内联目标 | 一致性源 | 同步状态 |
|----------|----------|----------|
| 1-3 (弹药换算表) | 1-3 §[弹药口径换算表] | 需同步 |
| 2-3 (弹药换算表) | 1-3 §[弹药口径换算表] | 需同步 |

### 建议操作顺序
1. 修改权威源（0-1/0-2 中的原始定义）
2. 同步所有内联副本（1-x/2-x）
3. 更新所有引用位置（§[章节名] / 口语化引用）
4. 更新枚举注册表（若涉及枚举）
5. 验证一致性（运行审计 Skill）
```

## Important Notes
- Always Grep BOTH formal (`§[...]`) and informal (`按 X 条`) reference patterns
- For enum changes, search for EACH individual value, not just the enum name
- Inline copies are the highest-risk sync items -- they're easy to miss because they don't have `§` markers
- If the modification target is in 0-1/0-2, ALWAYS check the 自包含要求 table for inline copies
- Report file paths with line numbers as `file:///` links for clickability
