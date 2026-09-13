#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remove_old_notes.py — 删除旧笔记文件夹并清理所有 md 中的旧笔记失效引用。
- 删除 资料/旧笔记 整个文件夹
- 遍历仓库 md(排除 docs/项目日志.md 历史记录):
  - 删除含「旧笔记」且含链接语法 ]( 的行(失效链接)
  - 删除「## 旧笔记联动」等小节标题行
  - 清理残留空行
"""
import os
import re
import shutil

ROOT = r"D:\Clinical Medicine"
OLD = os.path.join(ROOT, "资料", "旧笔记")
KEEP = {"docs", "项目日志.md"}  # 项目日志保留历史

# 删除旧笔记文件夹
if os.path.isdir(OLD):
    shutil.rmtree(OLD)
    print(f"已删除: {OLD}")

# 清理 md 引用
removed_lines = 0
for dirpath, dirs, files in os.walk(ROOT):
    # 跳过 .git / .venv
    dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__")]
    for f in files:
        if not f.lower().endswith(".md"):
            continue
        p = os.path.join(dirpath, f)
        rel = os.path.relpath(p, ROOT)
        if rel.startswith("docs" + os.sep) and f == "项目日志.md":
            continue  # 项目日志保留历史
        with open(p, encoding="utf-8") as fh:
            lines = fh.readlines()
        out = []
        changed = False
        for ln in lines:
            # 删除:含「旧笔记」且含链接 ]( 的行(失效链接)
            if "旧笔记" in ln and "](" in ln:
                removed_lines += 1
                changed = True
                continue
            # 删除「## 旧笔记联动」等小节标题
            if re.match(r"^#+\s*.*旧笔记", ln):
                removed_lines += 1
                changed = True
                continue
            out.append(ln)
        if changed:
            # 清理连续空行(最多保留1个)
            cleaned = []
            blank = 0
            for ln in out:
                if ln.strip() == "":
                    blank += 1
                    if blank > 1:
                        continue
                else:
                    blank = 0
                cleaned.append(ln)
            with open(p, "w", encoding="utf-8") as fh:
                fh.writelines(cleaned)
            print(f"清理: {rel}")
print(f"共删除引用行: {removed_lines}")