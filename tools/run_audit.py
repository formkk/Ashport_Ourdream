#!/usr/bin/env python3
"""
Ash Harbor 审计统一入口（PAM v1.2 Phase 1/2 机械核验）

串联所有检查脚本，输出标准化执行证据模板。
审计者运行后将输出复制到审计报告头部，然后进入 Phase 3-7 人工审查。

用法: python tools/run_audit.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent

SCRIPTS = [
    ("1.1 引用活性 + 1.5 节名引用链", "gen_ref_graph.py"),
    ("1.2 术语一致性 + 1.6 跨文件枚举一致性", "validate_enums.py"),
    ("1.3 SSOT 重复检测", "detect_duplicates.py"),
    ("1.4 格式合规 + 2.8/2.9/2.10 形态黑名单", "format_lint.py"),
]


def run_script(script_name):
    """运行单个脚本，返回 (return_code, stdout)"""
    script_path = TOOLS_DIR / script_name
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode, result.stdout, result.stderr


def main():
    print("=" * 60)
    print("PAM v1.2 Phase 1/2 机械核验 - 统一执行证据")
    print("=" * 60)
    print()

    all_exit_codes = []

    for label, script in SCRIPTS:
        print("-" * 60)
        print(f">>> {label}")
        print(f"    工具: python tools/{script}")
        print("-" * 60)
        print()

        exit_code, stdout, stderr = run_script(script)
        all_exit_codes.append(exit_code)

        if stdout:
            print(stdout)
        if stderr:
            print(f"[stderr] {stderr}")
        print()

    # 汇总
    print("=" * 60)
    print("执行证据汇总")
    print("=" * 60)
    print()

    for (label, script), exit_code in zip(SCRIPTS, all_exit_codes):
        status = "❌ 有发现" if exit_code != 0 else "✅ 无发现"
        print(f"  {label}: {status} (exit={exit_code})")

    print()
    print("下一步: 将以上输出复制到审计报告 'Phase 1/2 机械核验执行证据' 节，")
    print("       然后进入 Phase 3-7 人工审查（节级漏斗 / 机制闭环 / 行级审计 / 组织预算 / 汇总处置）。")

    return 1 if any(c != 0 for c in all_exit_codes) else 0


if __name__ == "__main__":
    exit(main())
