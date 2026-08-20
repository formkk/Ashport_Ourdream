#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B2 冲突探针（conflict probe）：检验 WM 推导温度层时是"查 1-3 A 区权威表"还是"复用历史最近 [主要状态]"。

假设：
  H-table   : 每轮从 Extra Details §[温度分层与日期精细对应] 推导（1-2 [必查表] 要求的行为）
  H-history : 直接复用对话历史中最近一条 [主要状态] 的温度层（近因位零查表成本）

判别原理：构造历史锚点与权威表冲突的场景，看输出跟随谁。
  P1: D33 锚点 Mild vs 权威表 Cold（同日中段，纯档位冲突）
  P2: D31 夜锚点 Cool → 过夜 → D32 晨权威表 Cold（跨日边界）
  P3: D20 锚点 Cool，与表（Cool~Cold）一致（对照组，只验基线有效性）

用法：
  干跑（默认，无 API）：py -3 tools/sim_b2_probe.py
    -> 在 tools/sim_b2_out/ 生成各探针完整提示词 txt（可整段贴到平台手动测）+ 评分指南
  API 模式（OpenAI 兼容端点）：
    set SIM_API_BASE=https://xxx/v1
    set SIM_API_KEY=sk-xxx
    set SIM_MODEL=模型名
    py -3 tools/sim_b2_probe.py --rounds 3
判定阈值：单一假设 ≥70% 判主导；30-70% 判混合；INVALID >20% 先查格式执行。
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT_DIR = os.path.join(ROOT, 'Prompt_File')
OUT_DIR = os.path.join(ROOT, 'tools', 'sim_b2_out')

# 平台装配顺序：0-1 -> 0-2 -> 0-3 -> 1-1 -> 1-2 -> 1-3
ASSEMBLY = [
    '0-1_Private_Details.md',
    '0-2_Scenario.md',
    '0-3_自定义指令.md',
    '1-1_WorldMaster_Scene.md',
    '1-2_WorldMaster_Additional_Personality_Details.md',
    '1-3_WorldMaster_Extra_Details.md',
]

LAYER_RE = re.compile(
    r'\[主要状态\][^\n]*?\|\s*(Autumn|Winter|Spring|Summer)-([^-|]+?)-(Mild|Cool|Cold|Bitter Cold|Heat)\s*\|'
)

PRESSURE_STABLE = '疲劳 stable；体温 stable；脱水 stable；饥饿 strained；伤病 stable'


def build_system():
    parts = []
    for f in ASSEMBLY:
        p = os.path.join(PROMPT_DIR, f)
        if not os.path.exists(p):
            print(f'[WARN] 缺文件，跳过: {f}')
            continue
        with open(p, encoding='utf-8') as fh:
            parts.append(fh.read().strip())
    return '\n\n'.join(parts)


def hist_asst(day, turn, clock, pos, season, weather, layer, narr):
    return (
        f'{narr}\n\n[移动] 无\n[掷骰] 无概率事件\n'
        f'[判定] 无\n[主要状态] D{day}-T{turn} {clock} | {pos} | '
        f'{season}-{weather}-{layer} | {PRESSURE_STABLE} | 风险: 无武器防御力低'
    )


PROBES = {
    # ---- P1 同日中段：D33 ∈ D32-D45 -> 权威 Cold；历史锚点 Mild（冲突） ----
    'P1': {
        'desc': '同日中段纯档位冲突（D33：锚点 Mild vs 表 Cold）',
        'table_layer': 'Cold', 'history_layer': 'Mild',
        'messages': [
            {'role': 'user', 'content': '我在高地公寓二楼把窗板重新钉牢，顺便看了看窗外的街口。'},
            {'role': 'assistant', 'content': hist_asst(
                33, 41, '14:20', '北区/S/高地公寓2号楼', 'Autumn', 'Clear', 'Mild',
                '你把最后一块窗板按回卡槽，钉子咬进湿木头。窗外的街口空着，风把一只塑料袋卷过路面。')},
            {'role': 'user', 'content': '我下楼到厨房翻找一下还剩什么能用的东西。'},
        ],
    },
    # ---- P2 跨日边界：D31 夜锚点 Cool -> 过夜 -> D32 晨表 Cold ----
    'P2': {
        'desc': '跨日边界（D31 夜锚点 Cool -> 过夜 -> D32 晨表 Cold）',
        'table_layer': 'Cold', 'history_layer': 'Cool',
        'messages': [
            {'role': 'user', 'content': '天黑透了，我把毯子裹紧，在火堆旁守着睡。'},
            {'role': 'assistant', 'content': hist_asst(
                31, 58, '22:10', '北区/S/高地公寓2号楼', 'Autumn', 'Clear', 'Cool',
                '火堆压低了苗头，你背靠墙角把毯子裹到下巴。楼下偶尔传来木板收缩的响动，你数着它们入睡。')},
            {'role': 'user', 'content': '我睡到天亮，收拾东西准备出门。'},
        ],
    },
    # ---- P3 对照：D20 ∈ D16-D31 -> Cool~Cold；锚点 Cool（一致，不判别） ----
    'P3': {
        'desc': '对照组（D20：锚点 Cool 与表 Cool~Cold 一致，只验基线）',
        'table_layer': 'Cool~Cold', 'history_layer': 'Cool',
        'messages': [
            {'role': 'user', 'content': '我把背包里的东西倒出来清点一遍。'},
            {'role': 'assistant', 'content': hist_asst(
                20, 30, '16:00', '北区/S/高地公寓2号楼', 'Autumn', 'Overcast', 'Cool',
                '你把装备摊在地板上逐件检查：火柴还剩半盒，水壶空了一半，小刀刃口卷了些。')},
            {'role': 'user', 'content': '清点完我把东西装回去，靠墙歇一会儿。'},
        ],
    },
}


def verdict(pid, layer):
    p = PROBES[pid]
    if pid == 'P3':
        return 'VALID' if layer in ('Cool', 'Cold') else 'INVALID'
    if layer == p['table_layer']:
        return 'TABLE'
    if layer == p['history_layer']:
        return 'HISTORY'
    return 'INVALID'


def call_api(base, key, model, system, messages, timeout=180):
    url = base.rstrip('/') + '/chat/completions'
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'system', 'content': system}] + messages,
        'temperature': 0.7,
        'max_tokens': 1500,
    }).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json', 'Authorization': f'Bearer {key}',
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode('utf-8'))
    return data['choices'][0]['message']['content']


def dump_prompt(pid, system):
    p = PROBES[pid]
    lines = [f'===== 探针 {pid}: {p["desc"]} =====\n']
    lines.append('--- [SYSTEM]（平台装配：0-1/0-2/0-3/1-1/1-2/1-3，共 %d 字符）---\n' % len(system))
    lines.append(system + '\n')
    for i, m in enumerate(p['messages']):
        tag = 'USER' if m['role'] == 'user' else 'ASSISTANT(历史)'
        lines.append(f'\n--- [{tag}] ---\n{m["content"]}\n')
    lines.append('\n--- [待补：以 USER 身份发送最后一条用户消息后，取 WM 回复判定] ---\n')
    lines.append(f'评分：P1/P2 输出 {p["table_layer"]} = TABLE(查表)；输出 {p["history_layer"]} = HISTORY(抄历史)；其他 = INVALID\n')
    return ''.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rounds', type=int, default=3)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--only', choices=list(PROBES), help='只跑指定探针')
    args = ap.parse_args()

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    system = build_system()
    print(f'装配完成：{len(system)} 字符（{len(ASSEMBLY)} 文件）')
    os.makedirs(OUT_DIR, exist_ok=True)

    base = os.environ.get('SIM_API_BASE', '')
    key = os.environ.get('SIM_API_KEY', '')
    model = os.environ.get('SIM_MODEL', '')

    # ---- dry-run：导出探针提示词 + 评分指南 ----
    pids = [args.only] if args.only else list(PROBES)
    for pid in pids:
        path = os.path.join(OUT_DIR, f'{pid}_prompt.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(dump_prompt(pid, system))
        print(f'  已导出 {path}')

    if args.dry_run or not (base and key and model):
        print('\n[dry-run] 未配置 API（SIM_API_BASE/SIM_API_KEY/SIM_MODEL），已导出提示词供平台手动测试。')
        print('评分指南：')
        for pid in pids:
            p = PROBES[pid]
            print(f"  {pid} {p['desc']}：TABLE={p['table_layer']} / HISTORY={p['history_layer']}")
        return

    # ---- API 模式 ----
    results = {pid: {'TABLE': 0, 'HISTORY': 0, 'INVALID': 0, 'raw': []} for pid in pids}
    for pid in pids:
        p = PROBES[pid]
        print(f'\n===== {pid}: {p["desc"]}（{args.rounds} 轮）=====')
        for i in range(args.rounds):
            try:
                out = call_api(base, key, model, system, p['messages'])
            except Exception as e:
                print(f'  round{i+1}: API 失败 {e}')
                results[pid]['INVALID'] += 1
                results[pid]['raw'].append({'error': str(e)})
                continue
            m = LAYER_RE.search(out)
            if not m:
                v = 'INVALID'
                print(f'  round{i+1}: INVALID（无 [主要状态] 温度层）')
            else:
                layer = m.group(3)
                v = verdict(pid, layer)
                print(f'  round{i+1}: {v}（输出 {m.group(1)}-{m.group(2).strip()}-{layer}）')
            results[pid][v] += 1
            results[pid]['raw'].append({'verdict': v, 'tail': out[-300:]})
            time.sleep(1)

    # ---- 汇总 ----
    print('\n===== 汇总 =====')
    n_total = {pid: sum(results[pid][k] for k in ('TABLE', 'HISTORY', 'INVALID')) for pid in pids}
    for pid in pids:
        r = results[pid]
        n = max(n_total[pid], 1)
        print(f"{pid}: TABLE {r['TABLE']}/{n}  HISTORY {r['HISTORY']}/{n}  INVALID {r['INVALID']}/{n}")
    p1p2 = [pid for pid in pids if pid != 'P3']
    if p1p2:
        t = sum(results[pid]['TABLE'] for pid in p1p2)
        h = sum(results[pid]['HISTORY'] for pid in p1p2)
        inv = sum(results[pid]['INVALID'] for pid in p1p2)
        n = max(t + h + inv, 1)
        print(f'P1+P2 合计: TABLE {t}/{n} ({t/n*100:.0f}%)  HISTORY {h}/{n} ({h/n*100:.0f}%)  INVALID {inv}/{n}')
        if inv / n > 0.2:
            print('-> INVALID >20%：先排查格式执行问题，本实验结论不可用')
        elif t / n >= 0.7:
            print('-> H-table 主导：WM 真查表，B2 为真问题，DEC-M 进入评估（§13.4）')
        elif h / n >= 0.7:
            print('-> H-history 主导：WM 从历史自服务，B2 为伪问题，DEC-M 关闭')
        else:
            print('-> 混合模式：档位冲突场景下行为不稳定，建议加大 rounds 复测')

    with open(os.path.join(OUT_DIR, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"原始结果已写入 {os.path.join(OUT_DIR, 'results.json')}")


if __name__ == '__main__':
    main()
