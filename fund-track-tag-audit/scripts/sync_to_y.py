#!/usr/bin/env python3
"""将固定的本地缓冲文件 latest_report.md 同步到 Y 盘目标路径。

用法: python sync_to_y.py "<Y盘目标文件路径>"
源文件固定为脚本所在目录的父目录下的 latest_report.md。
"""

from __future__ import annotations

import os
import shutil
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python scripts/sync_to_y.py <Y盘目标文件路径>")
        return 1

    target_file = sys.argv[1]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(os.path.dirname(script_dir), "latest_report.md")

    if not os.path.exists(source_file):
        print(f"❌ 错误: 本地缓冲文件 {source_file} 不存在，请先让 Agent 写入。")
        return 1

    target_dir = os.path.dirname(target_file)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    try:
        shutil.copy2(source_file, target_file)
        if not os.path.exists(target_file):
            print(f"❌ 同步后未找到目标文件: {target_file}")
            return 1
        if os.path.getsize(source_file) != os.path.getsize(target_file):
            print("❌ 同步后文件大小不一致，请人工检查目标文件。")
            return 1
        print(f"✅ 同步成功: {target_file}")
        return 0
    except OSError as e:
        print(f"❌ 同步失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
