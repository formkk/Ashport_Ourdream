---
name: "output-format-validator"
description: "Validates WM/WSK output format against project rules. Invoke when user pastes WM or WSK output for format compliance checking, or after prompt file changes to verify format consistency."
---

# Output Format Validator

Validates Ash Harbor WM (World Master) and WSK (World State Keeper) output against the project's format rules.

## When to Invoke

- User pastes WM or WSK output text and asks to check/validate format
- User wants to verify output compliance after prompt file changes
- User asks to run a "smoke test" or "format check" on actual platform output
- User mentions "输出格式", "format validation", "格式验证", "冒烟测试"

## How to Use

### Step 1: Identify Output Type

Determine if the pasted text is WM or WSK output:
- **WM output**: Contains `[移动]`, `[掷骰]`, `[判定]`, `[主要状态]` blocks
- **WSK output**: Contains `[State Update]` tag

### Step 2: Run Validation Script

Save the user's output text to a temporary file, then run:

```bash
# For WM output
C:\ProgramData\anaconda3\python.exe tools/validate_output.py --type wm --file <temp_file>

# For WSK output
C:\ProgramData\anaconda3\python.exe tools/validate_output.py --type wsk --file <temp_file>
```

Or pipe directly:
```bash
echo "<output text>" | C:\ProgramData\anaconda3\python.exe tools/validate_output.py --type wm
```

### Step 3: Report Results

Present the validation results to the user:
- List all passed checks (✅)
- List all failed checks (❌) with expected format vs actual content
- Provide specific fix suggestions for failures

## What It Checks

### WM Output

| Check | Description |
|-------|-------------|
| Block presence | All 4 blocks present: [移动], [掷骰], [判定], [主要状态] |
| Block order | Order: 正文 -> [移动] -> [掷骰] -> [判定] -> [主要状态] |
| Label no newline | Label and content on same line (no `\n` after label) |
| Empty format | [移动] 无 / [掷骰] 无概率事件 / [判定] 无 |
| [移动] format | {原地点所在子区域} -> {中间子区域 Route} -> {目标地点所在子区域} \| Steps: N \| Travel Time: Nmin（链只写 Zone/Sub-zone，不写 Location） |
| [掷骰] format | Trigger: {类名}: {...}；Base: {N}（理由可省）；Modifiers: {...}；Final/Seed/Threshold: {N}；Result: {触发/未触发}；Outcome: {...} 或 Dase-N / wear-*: 未触发 / 无概率事件 |
| [判定] format | 消耗（D{prev}->D{curr}）: {物品}；{类别}: {结果}；代价与后果: {一句} |
| [主要状态] format | D{Day}-T{Turn} {HH:MM} \| {位置} \| {Season}-{天气}-{气温} \| {压力} \| {风险} |
| Terminator | Output ends with [主要状态] |

### WSK Output

| Check | Description |
|-------|-------------|
| [State Update] tag (R1) | Present at start（`-` 空白标记已废除，2026-08-15 起） |
| Header format (R2) | 第一行含 `D{day}-T{turn}`（D-T 从 WM `[主要状态]` 提取） |
| Inventory Delta（字段 0，R3） | `Inventory Delta:` 标签必出；无变化时内容留空，其余字段照抄基线原文 |
| Full view 7 fields (R4) | Inventory Delta（字段 0）/ Inventory State / Party Condition / Relationship & Threat / Map Knowledge / Base Structure State / 近五日主要事件 |
| No ## titles (R5) | 不含 markdown 标题行 |
| Field order (R7) | Inventory Delta 在其余 6 字段之前 |

> v1.70 起完整视图按 7 字段计法（`Inventory Delta` 为字段 0）；`validate_output.py` 内部仍以"Delta 标签 + 6 正文字段"实现，字段集合一致。

## Rules Configuration

Format rules are externalized in `tools/output_rules.json`. When prompt file format changes:
1. Update `tools/output_rules.json` with new patterns
2. No need to modify the validation script

## Example Usage

User pastes:
```
你站在窗边观察街道。

[移动] 无
[掷骰] 无概率事件
[判定] 无
[主要状态] D6-T178 08:15 | 工业区/N/质检小楼 | Winter-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 无
```

AI should:
1. Identify as WM output
2. Save to temp file
3. Run: `python tools/validate_output.py --type wm --file <temp_file>`
4. Report: "✅ 全部通过 (14 项)"
