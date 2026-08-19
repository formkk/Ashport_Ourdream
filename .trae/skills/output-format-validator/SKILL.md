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
- **WM output**: Contains `[Move]`, `[Probability Check]`, `[判定]`, `[主要状态]` blocks
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
| Block presence | All 4 blocks present: [Move], [Probability Check], [判定], [主要状态] |
| Block order | Order: 正文 -> [Move] -> [Probability Check] -> [判定] -> [主要状态] |
| Label no newline | Label and content on same line (no `\n` after label) |
| Empty format | [Move] 无 / [Probability Check] 无概率事件 / [判定] 无 |
| [Move] format | {原地点所在子区域} -> {中间子区域 Route} -> {目标地点所在子区域} \| Steps: N \| Travel Time: Nmin（链只写 Zone/Sub-zone，不写 Location） |
| [Probability Check] format | Trigger: {类名}: {...}；Base: {N}（理由可省）；Modifiers: {...}；Final/Seed/Threshold: {N}；Result: {触发/未触发}；Outcome: {...} 或 Dase-N / wear-*: 未触发 / 无概率事件 |
| [判定] format | 消耗（D{prev}->D{curr}）: {物品}；{类别}: {结果}；代价与后果: {一句} |
| [主要状态] format | D{Day}-T{Turn} {HH:MM} \| {位置} \| {Season}-{天气}-{气温} \| {压力} \| {风险} |
| Terminator | Output ends with [主要状态] |

### WSK Output

| Check | Description |
|-------|-------------|
| [State Update] tag | Present at start |
| Header format | D{day}-T{turn} / {Season} / HH:MM / {位置} / {天气} {温度} / {知情范围} |
| Inventory Delta | Present (or empty marker `-` if no changes) |
| Active Concerns | Present with valid categories ([生存]/[人际]/[环境]/[据点]) |
| Full view 6 fields | Inventory State, Party Condition, Relationship & Threat, Map Knowledge, Base Structure State, 近五日主要事件 |

## Rules Configuration

Format rules are externalized in `tools/output_rules.json`. When prompt file format changes:
1. Update `tools/output_rules.json` with new patterns
2. No need to modify the validation script

## Example Usage

User pastes:
```
你站在窗边观察街道。

[Move] 无
[Probability Check] 无概率事件
[判定] 无
[主要状态] D6-T178 08:15 | 工业区/N/质检小楼 | Winter-Overcast-Cool | 疲劳 stable；体温 stable；脱水 stable；饥饿 stable；伤病 stable | 无
```

AI should:
1. Identify as WM output
2. Save to temp file
3. Run: `python tools/validate_output.py --type wm --file <temp_file>`
4. Report: "✅ 全部通过 (14 项)"
