---
name: "prompt-consistency-audit"
description: "Audits prompt engineering files for cross-reference integrity, enum consistency, authority source uniqueness, output structure alignment, and inline completeness. Invoke when user asks for consistency check, audit, or alignment of Prompt_Files."
---

# Prompt Consistency Audit

This skill performs a systematic consistency audit across all prompt engineering files in the `Prompt_File/` directory. It is designed for the Ash Harbor (灰港) LLM chatroom RPG project.

## When to Invoke
- User asks for "一致性检查", "审计", "对齐", "consistency check", "audit"
- User asks to check "全库" or "所有文件" for consistency
- After making changes to any `Prompt_File/*.md` file, user wants to verify no new inconsistencies were introduced

## Audit Steps (Execute in Order)

### Step 1: Cross-Reference Resolution
Scan all `§[章节名]` and `§章节名` references across all files:
1. Grep for `§\[.*\]` and `§[^\s]+` patterns in all `Prompt_File/*.md` files
2. For each reference, extract: source file, source line, referenced file, referenced section name
3. Verify the referenced section actually exists in the target file
4. Flag any broken references (target section does not exist)
5. Flag any misdirected references (reference says "Scene 字段" but data is actually in "Extra Details 字段")

**Key check**: When file A says "see file B's §[X]", verify §[X] exists in file B AND contains the data being referenced.

### Step 2: Enum Consistency
Extract and cross-compare all enum definitions:
1. Search for each known enum (see list below) in all files
2. Compare the value lists across all files where each enum appears
3. Flag any mismatched values (missing, extra, or different spelling)

**Enums to check**:
- 知情范围: `hidden / party-known / local-only / publicly-known`
- Survival state levels: `stable / strained / weakened / critical / dying / dead`
- Weather: `Clear / Overcast / Light Rain / Heavy Rain / Fog / Windy / Sleet / Snow / Storm`
- Temperature Band: `Mild / Cool / Cold / Bitter Cold / Heat`
- Current Season: `Winter / Spring / Summer / Autumn`
- Memory Inventory Availability: `confirmed-intact / uncertain / likely-moved / likely-looted / likely-damaged / unreachable`
- Human Threat Stage: `none / signs / observed / followed / probed / blocked / robbed / violent / lethal`
- Ammunition calibers: `9mm / .45 ACP / .380 ACP / .22 LR / 霰弹 / 7.62 / 5.45 / 其他口径`
- Base categories: `主据点 / 物资点 / 安全屋 / 地图外据点`
- Exposure response levels: `L0 未暴露 / L1 怀疑 / L2 暴露 / L3 追查 / L4 清算`

### Step 3: Authority Source Uniqueness & Inline Copy Consistency
Verify each data table / enum / rule has exactly ONE authoritative source in 0-1/0-2, AND that role cards (1-x/2-x) have corresponding inline "execution copies":
1. Identify all data tables and mechanical rules
2. For each, verify only 0-1/0-2 defines the authoritative data
3. Verify role cards have inline execution copies (full text, not just `§聊天室` references)
4. Cross-compare: inline copy values match authority source values
5. Flag: role card has only `§聊天室` reference without inline text -> P1

**Authority source -> execution copy mapping**:
| Data / Rule | Authority (0-1/0-2) | WM copy | WSK copy |
|------------|---------------------|---------|----------|
| 弹药口径换算表 | 0-2 §[弹药口径换算表] | 1-3 | 2-3 |
| 可消耗物资渲染协议 | 0-1 §[可消耗物资渲染与记录协议] | 1-3 | 2-3 |
| 资源消耗基准 | 0-2 §[资源消耗基准] | 1-3 | 2-3 |
| 物资重量校准锚点 | 0-2 §[可消耗物资重量校准锚点] | 1-3 | 2-3 |
| 5 轨压力系统 | 0-2 §[环境生存压力系统] | 1-2/1-3 | 2-2/2-3 |
| 温度分层与季节 | 0-2 §[温度分层与 5 轨道联动] / §[季节锚点] | 1-3 | 2-3 §[固定取值] |
| 天气枚举与影响 | 0-2 §[轻量天气系统] | 1-3 | 2-3 §[固定取值] |
| 知情范围 | 0-1 §[跨层转移与 知情范围 协议] | 1-2 | 2-2 |
| 跨层转移规则 | 0-1 §[跨层转移与 知情范围 协议] | 1-2 | 2-2 |
| NPC 知识边界 | 0-2 §[NPC 反全知 / 反顾问化机制] | 1-2 | -- |
| 移动与路由规则 | 0-2 §[地图调用规则] | 1-3 | 2-2 |
| 死亡/抢救规则 | 0-2 §[死亡 / 抢救 / 遗物规则] | 1-2 | -- |
| [主要状态] 格式 | 0-1 §[主要状态栏硬约束] | 1-1 | -- |
| 压力/风险栏规则 | 0-1 §[压力/风险栏规则与正反示例] | 1-1 | -- |

### Step 4: Output Structure Completeness
For each role (WM / WSK), compare all output structure descriptions:
1. Find all places that describe output structure (输出白名单, 使用原则, 完整视图, 正式提交顺序, etc.)
2. Verify they all describe the same steps/fields in the same order
3. Flag any step/field present in one description but missing in another

**Key checks**:
- WSK: Active Concerns appears in 输出结构(使用原则), 正式提交顺序, AND 完整视图 definition
- WSK: 完整视图 9 字段 count matches actual field list
- WM: [主要状态] 5 段 structure matches 0-1 §[主要状态栏硬约束] definition
- Memory inventory position: consistent across §压缩规则, §完整视图, §正式提交顺序

### Step 5: Terminology Consistency (with Regression Checks)
Check that the same concept uses the same name across all files:
1. Grep for known ambiguous term pairs
2. Flag any file using a different name for the same concept

**Known term pairs (all historically fixed, check for regression)**:
- "沉默协议" vs "静默协议"（已统一为"沉默协议"）
- "Human Contact Status" vs "Human Threat Stage"（已统一为"Human Threat Stage"）
- "据点核心库存" vs "据点库存" vs "据点储备"（已统一为"据点核心库存"）
- ".45" vs ".45 ACP"（已统一为全名）
- "Inventory State 末尾" vs "Inventory State 之后"（记忆库存位置，已统一为"之后"）
- "由 WSK 归档到 Pinned Memory" vs "由 WSK 产出素材、由用户手动复制"（已统一为后者）

### Step 6: Process Description Consistency
Verify the same process is described consistently:
1. Pinned Memory flow: Who produces? Who copies? (WSK produces -> user manually copies)
2. Cross-layer transfer: Source decreases, target increases (both sides recorded)
3. Death event: Default 知情范围 = hidden
4. Off-screen evolution: Time threshold definition exists
5. Pressure listing: WM lists only non-stable; WSK lists all 5

### Step 7: Inline Completeness & Reference Failure Audit
This step checks that role cards are self-contained and don't have execution-dependent references to 0-1/0-2:
1. Cross-reference with `prompt-engineering.mdr` "WM/WSK 自包含要求" table
2. For each required inline item, verify the role card field contains the actual rule text (not just a `§聊天室` reference)
3. Scan 1-x / 2-x for all `§聊天室` / `聊天室 XX 字段` references:
   - Execution dependency (tables/mechanical rules/system protocols) without inline text -> **P1**
   - World consensus background references (faction positioning, geography) -> acceptable
4. Check inline copies have `（与 0-X §XX 一致）` annotation for traceability

## Report Format

Output the audit report in this structure:

```
## 一致性检查结果：{文件范围}

### 严重矛盾（直接冲突）
**P0-1: {问题标题}**
- 位置：[文件名](file:///path#L行号) 第X行
- 问题：{描述}
- 建议：{修复方案}

### 重大遗漏（结构性缺失）
**P1-1: {问题标题}**
...

### 命名不一致（术语/格式）
**P2-1: {问题标题}**
...

### 缺口（内容缺失但不矛盾）
**P3-1: {问题标题}**
...

### 建议修复优先级
| 优先级 | 问题 | 建议 |
|--------|------|------|
| P0 | ... | ... |
```

## Important Notes
- Always read the actual file content before reporting an issue (don't rely on Grep alone)
- Use `file:///` links with line numbers for clickable references
- Check both the referencing file AND the referenced file when verifying cross-references
- When comparing enums, check spelling exactly (including spaces, capitalization, Chinese vs English)
- Report what you actually find, not what you expect to find based on previous audits
- For Step 7: the "自包含要求" table in `prompt-engineering.mdr` is the authoritative checklist; always read it before auditing
