#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
annotate_cards.py — 给正库病种卡头部自动插入「> 大纲要求:」标注行。
- 高频病种(README「高频卡片」节)→ 🔷 掌握(高频重点)
- 小众骨架(README「小众骨架」节)→ ◽ 熟悉(小众)
- 未归入任一卷 → ◽ 熟悉(待确认)
依据:2024 修订大纲以高频/小众归类作掌握度代理(OCR 未含要求列,精确细目要求以人卫 2026 大纲原文为准)。
幂等:已含「大纲要求:」的卡跳过。
用法: python annotate_cards.py [<03 系统目录>]
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                       os.path.join(os.path.dirname(__file__), "..", "考试", "03_临床医学综合"))
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")


def read_sections(readme_path):
    """返回 (high_list, niche_list):各卡文件名(去 .md)。"""
    high, niche = [], []
    try:
        with open(readme_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return high, niche
    mh = re.search(r"## 高频卡片.*?(?=\n## |\Z)", text, re.S)
    mn = re.search(r"## 小众骨架.*?(?=\n## |\Z)", text, re.S)
    if mh:
        high = [os.path.basename(p) for p in LINK_RE.findall(mh.group(0))]
    if mn:
        niche = [os.path.basename(p) for p in LINK_RE.findall(mn.group(0))]
    return high, niche


def annotate_file(path, badge):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("> 大纲要求:"):
            return False  # 已标注
    target = None
    for i, ln in enumerate(lines):
        if ln.startswith("> 来源:"):
            target = i
            break
    if target is None:
        return False
    lines.insert(target + 1, f"> 大纲要求:{badge}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True


def main():
    if not os.path.isdir(ROOT):
        print("不存在:", ROOT)
        sys.exit(1)
    total = changed = 0
    for sysname in sorted(os.listdir(ROOT)):
        sroot = os.path.join(ROOT, sysname)
        if not os.path.isdir(sroot):
            continue
        readme = os.path.join(sroot, "README.md")
        if not os.path.isfile(readme):
            continue
        high, niche = read_sections(readme)
        high_ok = {os.path.splitext(x)[0] for x in high}
        niche_ok = {os.path.splitext(x)[0] for x in niche}
        for f in sorted(os.listdir(sroot)):
            if not f.lower().endswith(".md") or f.lower() == "readme.md":
                continue
            base = os.path.splitext(f)[0]
            if base in high_ok:
                badge = "🔷 掌握(高频重点)"
            elif base in niche_ok:
                badge = "◽ 熟悉(小众)"
            else:
                badge = "◽ 熟悉(待确认)"
            total += 1
            if annotate_file(os.path.join(sroot, f), badge):
                changed += 1
                print(f"  [{sysname}] {f}  ←  {badge}")
    print(f"共 {total} 卡,新增标注 {changed} 张")


if __name__ == "__main__":
    main()