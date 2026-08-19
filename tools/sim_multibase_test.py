#!/usr/bin/env python3
"""
多据点分桶输出 静态格式测试（依据：多据点分桶输出决议.md，决议 1=A 统一限定符，决议 2=A 全量无上限）

验证对象：模拟 WSK 完整视图（3 据点：主据点/安全屋/地图外据点）+ 模拟 WM 输入上下文（[Move]/[判定] 消耗行）。

检查组：
  R1-R7   现行结构规则（同 tools/validate_output.py：头部/Delta 标签/6 字段/顺序/无##标题）
  B1      Inventory State 分桶段头格式：据点核心/{据点名}（{锚点}，{4 分类枚举}）: ...
  B2      分桶行锚点与 Base Structure State 锚点行一致（同名同锚点同分类）
  B3      Base Structure State 多据点块：锚点行 + `组件名` = 状态（历史）组件行 / 结构节点未确认；块间空行
  B4      Delta 存储位限定符：随身 或 据点核心/{据点名}；跨位/跨据点为 全限定符->全限定符
  B5      Delta 引用的据点名 ⊆ 分桶行据点名集合（防幻觉据点）
  B6      WM 消耗行（输入侧）：据点({据点名}) 限定符写法
  B7      空块分隔：Base Structure State 内不得用 ； 合并多据点；不得用单行式多据点
  B8      边界①：同口径弹药不跨桶合并（随身/各据点桶独立条目，无全局合计值）
  B9      边界②：定性标记组发生具体数量变化后升级为具体计数（不再 具备/充足）
"""

import re
import sys

if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")

# ---------- 模拟 WM 输入上下文（提取源） ----------
WM_MOVE = "[Move] 工业区/N -> 工业区/W -> 西区/S | Steps: 2 | Travel Time: 70min"
WM_JUDGE = "[判定] 消耗（D8->D9）: 随身 干粮×0.5kg + 净水×1kg / 据点(河边安全屋) 净水×1kg；获得: 罐头×3（泵房储物架）；代价与后果: 转运木柴耗力，午后疲劳上升"

# ---------- 模拟 WSK 完整视图（决议格式） ----------
SIM_OUTPUT = """[State Update] D9-T195

Inventory Delta: 转移 木柴×5kg（据点核心/质检小楼->随身）；转移 木柴×5kg（随身->据点核心/河边安全屋）；获得 罐头×3（据点核心/河边安全屋）；消耗 干粮×0.5kg（随身）；消耗 净水×1kg（随身）；消耗 净水×1kg（据点核心/河边安全屋）

1. Inventory State: 随身: 武器: 猎枪×1；弹药: 9mm×42发；食品: 干粮×1.0kg；饮水: 净水×1.5kg
据点核心/质检小楼（工业区/N/质检小楼，主据点）: 食品: 罐头×6, 大米×10kg；水储备: 净水×7kg；建材储备: 木柴×8kg（估）, 金属件 具备
据点核心/河边安全屋（西区/S/泵房，安全屋）: 弹药: 9mm×20发；食品: 罐头×3；水储备: 净水×2kg；燃料动力: 木柴×5kg
据点核心/林场木屋（北闸口->林场护林站，地图外据点）: 食品: 罐头×2, 压缩饼干×1kg
2. Party Condition: 1人；疲劳 strained；体温 stable；脱水 stable；饥饿 stable；伤病 stable
3. Relationship & Threat: 谢尔盖: 存活 / 市政厅 / 追债；Human Threat Stage: observed（D8 拾荒者远距目击）
4. Map Knowledge: 工业区/N 已探索；西区/S 已探索；质检小楼已确认（主据点）；泵房已确认（安全屋）；北闸口->林场护林站 已确认（外部路线，Reachability: 可达）
5. Base Structure State:
质检小楼（工业区/N/质检小楼，主据点）
- `正门钢架` = 完好，可上闩（D6 新建）
- `二楼储物间` = 干燥，货架2排（D6 新建；D8 清点）
- `天台瞭望位` = 完好，视野开阔（D8 新建）

河边安全屋（西区/S/泵房，安全屋）
- `泵房铁门` = 完好，内侧加闩（D8 新建）

林场木屋（北闸口->林场护林站，地图外据点）
- 结构节点未确认
6. 近五日主要事件:
D5: 到达工业区/N/质检小楼，搜刮获得大米×2.5kg + 9mm×12发
D6: 建立质检小楼主据点，物资转入据点核心
D7: 经北闸口抵达林场护林站，建立林场木屋物资点，留下罐头×2 + 压缩饼干×1kg
D8: 建立河边安全屋（西区/S/泵房）；被拾荒者远距看到
D9: 质检小楼装载木柴×5kg转移至河边安全屋；搜刮泵房获得罐头×3"""

# ---------- 检查实现 ----------
BASE_CAT = r"(主据点|安全屋|物资点|地图外据点)"
RE_BUCKET = re.compile(r"^据点核心/[^（）/]+（[^（）]+，%s）: .+$" % BASE_CAT)
RE_ANCHOR = re.compile(r"^[^（）/]+（[^（）]+，%s）$" % BASE_CAT)
RE_COMP = re.compile(r"^- `[^`]+` = .+（.+）$")
RE_UNCONF = re.compile(r"^- 结构节点未确认$")
RE_QUAL = r"(随身|据点核心/[^（）/；]+)"
RE_DELTA_ITEM = re.compile(r"^(获得|消耗|丢失|转移) [^（]+（%s->%s）$" % (RE_QUAL, RE_QUAL))
RE_DELTA_ITEM1 = re.compile(r"^(获得|消耗|丢失|转移) [^（]+（%s）$" % RE_QUAL)

results = []
def test(tid, name, ok, detail=""):
    results.append((tid, name, ok, detail))

out = SIM_OUTPUT
lines = out.split("\n")

# R1-R7（对齐 validate_output.py）
first = lines[0]
test("R1", "输出以 [State Update] 开头", first.startswith("[State Update]"))
test("R2", "头部 D{N}-T{N}", bool(re.match(r"^\[State Update\] D\d+-T\d+$", first)))
test("R3", "Inventory Delta 标签必出", any(l.startswith("Inventory Delta:") for l in lines))
req = ["Inventory State", "Party Condition", "Relationship & Threat", "Map Knowledge", "Base Structure State", "近五日主要事件"]
pos = [out.find(f) for f in req]
test("R4", "6 字段必出", all(p >= 0 for p in pos))
test("R5", "无 ## 标题行", not any(re.match(r"^#{2,3} ", l) for l in lines))
test("R6", "非 - 开头输出", not first.startswith("-"))
test("R7", "Delta 在 6 字段之前", out.find("Inventory Delta:") < min(p for p in pos if p >= 0))

# B1 分桶段头
bucket_lines = [l for l in lines if l.startswith("据点核心/")]
test("B1", "分桶段头格式（3 行）", len(bucket_lines) == 3 and all(RE_BUCKET.match(l) for l in bucket_lines),
     f"{len(bucket_lines)} 行")

# B3 Base Structure State 块结构
i5 = next(i for i, l in enumerate(lines) if l.startswith("5. Base Structure State:"))
seg = lines[i5 + 1:]
end = next((j for j, l in enumerate(seg) if l.startswith("6.")), len(seg))
seg = seg[:end]
blocks, cur = [], None
for l in seg:
    if not l.strip():
        cur = None
        continue
    if RE_ANCHOR.match(l):
        cur = [l]
        blocks.append(cur)
    elif cur is not None:
        cur.append(l)
ok_b3 = len(blocks) == 3 and all(
    len(b) >= 2 and all(RE_COMP.match(x) or RE_UNCONF.match(x) for x in b[1:]) for b in blocks)
test("B3", "结构块 = 锚点行 + 组件行/未确认（3 块）", ok_b3, f"{len(blocks)} 块")

# B2 分桶行与结构块锚点一致
def anchor_of(line):  # "名（锚，分类）" 或 "据点核心/名（锚，分类）: ..." -> (名, 锚, 分类)
    line = re.sub(r"^据点核心/", "", line)
    m = re.match(r"^([^（）/]+)（([^（）]+)，%s）" % BASE_CAT, line)
    return m.groups() if m else None
bucket_anchors = {anchor_of(l) for l in bucket_lines}
block_anchors = {anchor_of(b[0]) for b in blocks}
test("B2", "分桶行与结构块锚点一致", bucket_anchors == block_anchors and len(bucket_anchors) == 3,
     f"桶{len(bucket_anchors)}/块{len(block_anchors)}")

# B4/B5 Delta 限定符与据点名闭包
delta = next(l for l in lines if l.startswith("Inventory Delta:"))
items = [x.strip() for x in delta[len("Inventory Delta:"):].split("；") if x.strip()]
ok_b4 = all(RE_DELTA_ITEM.match(x) or RE_DELTA_ITEM1.match(x) for x in items)
test("B4", "Delta 条目全限定符", ok_b4,
     "; ".join(x for x in items if not (RE_DELTA_ITEM.match(x) or RE_DELTA_ITEM1.match(x))))
names_in_delta = set(re.findall(r"据点核心/([^（）/；>\-]+)", delta))
names_in_buckets = {a[0] for a in bucket_anchors}
test("B5", "Delta 据点名 ⊆ 分桶据点名", names_in_delta <= names_in_buckets, str(names_in_delta))

# B6 WM 消耗行限定符（输入侧）
m = re.search(r"消耗（D8->D9）: ([^；]+)", WM_JUDGE)
cons = m.group(1)
pos_items = [p.strip() for p in cons.split("/")]
ok_b6 = all(re.match(r"^(随身|据点\([^（）/]+\)) .+(\+ .+)*$", p) for p in pos_items) and \
    all(n in names_in_buckets for n in re.findall(r"据点\(([^（）/]+)\)", cons))
test("B6", "WM 消耗行 据点(名) 限定符", ok_b6, cons)

# B7 块间不混用 ； 或单行式
test("B7", "结构块为多行块（非单行；合并）", not re.search(r"Base Structure State: .+；.+", out))

# B8 边界①：同口径弹药不跨桶合并（各存储位独立条目，无全局合计值）
nine_lines = [l for l in lines if "9mm×" in l]
ok_b8 = (any("9mm×42发" in l and l.startswith("1. Inventory State") for l in nine_lines)
         and any("9mm×20发" in l and l.startswith("据点核心/") for l in nine_lines)
         and not any("9mm×62发" in l for l in lines))
test("B8", "边界①：同口径弹药不跨桶合并", ok_b8,
     "存在全局合计值 9mm×62发" if any("9mm×62发" in l for l in lines) else "")

# B9 边界②：定性标记组发生具体数量变化后升级为具体计数
bad9 = []
for x in items:
    m = re.match(r"^(?:获得|消耗|丢失|转移) (.+?)×", x)
    if not m:
        continue
    item_name = m.group(1)
    for b in re.findall(r"据点核心/([^（）/；>\-]+)", x):
        bl = next((l for l in bucket_lines if l.startswith("据点核心/" + b)), None)
        if bl and re.search(re.escape(item_name) + r"\s*(具备|充足)", bl):
            bad9.append(f"{b}:{item_name} 仍为定性标记")
test("B9", "边界②：定性组发生具体数量变化已升级计数", not bad9, "; ".join(bad9))

# ---------- 输出 ----------
print("=" * 62)
print("多据点分桶输出 静态格式测试（依据：多据点分桶输出决议.md）")
print("=" * 62)
for tid, name, ok, detail in results:
    mark = "✅" if ok else "❌"
    extra = f"  [{detail}]" if detail and not ok else ""
    print(f"  {mark} {tid} {name}{extra}")
n_fail = sum(1 for r in results if not r[2])
print("-" * 62)
print(f"总计: {len(results)} 项，通过 {len(results) - n_fail}，失败 {n_fail}")
print()
print("【模拟输入 · WM [Move]】")
print(WM_MOVE)
print()
print("【模拟输入 · WM [判定]】")
print(WM_JUDGE)
print()
print("【模拟输出 · WSK 完整视图】")
print(SIM_OUTPUT)
sys.exit(0 if n_fail == 0 else 1)
