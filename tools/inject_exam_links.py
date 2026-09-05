#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_exam_links.py — 第2步:把《模拟试卷汇总》里已关联的真题,反链写入 272 张正库卡。
位置:每张卡 `## 考点提示` 标题正下方,以 blockquote 呈现,幂等(已有标记则跳过)。
用法: python inject_exam_links.py
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"D:\Clinical Medicine"
SUM = os.path.join(ROOT, "资料", "模拟试卷", "汇总", "模拟试卷汇总.md")
C03 = os.path.join(ROOT, "考试", "03_临床医学综合")
MARK = "📝 **2026模拟卷真题**"

BLOCK_HEAD = re.compile(r"^### 卷(?P<set>[一二三])·第(?P<unit>[一二三四])单元·第(?P<no>\d+)题")
LINE_Q = re.compile(r"^- \*\*题干\*\*:(?P<q>.+)$")
LINE_A = re.compile(r"^- \*\*答案\*\*:(?P<a>.+)$")
LINE_C = re.compile(r"^- \*\*关联卡\*\*:\[(?P<name>[^\]]+)\]\((?P<link>[^)]+)\)$")


def shorten(s, n=42):
    s = s.strip()
    return s if len(s) <= n else s[:n] + "…"


def main():
    txt = open(SUM, encoding="utf-8").read().split("\n")
    # 按题块聚合
    by_card = {}
    cur = None
    for ln in txt:
        b = BLOCK_HEAD.match(ln)
        if b:
            cur = {
                "set": b.group("set"), "unit": b.group("unit"), "no": int(b.group("no")),
                "q": "", "a": "", "card": None, "link": None,
            }
            continue
        if cur is None:
            continue
        m = LINE_Q.match(ln)
        if m:
            cur["q"] = m.group("q").strip()
            continue
        m = LINE_A.match(ln)
        if m:
            cur["a"] = m.group("a").strip()
            continue
        m = LINE_C.match(ln)
        if m:
            cur["card"] = m.group("name")
            cur["link"] = m.group("link")
            if cur["card"]:
                by_card.setdefault(cur["card"], []).append(dict(cur))
            cur = None  # 一块结束

    print(f"聚合到 {len(by_card)} 张卡,共 {sum(len(v) for v in by_card.values())} 条反链")

    # 卡名 → 文件路径
    card_file = {}
    for dirpath, _, files in os.walk(C03):
        for f in files:
            if f.lower().endswith(".md") and f.lower() != "readme.md":
                card_file.setdefault(os.path.splitext(f)[0], os.path.join(dirpath, f))

    injected = skipped = missing = 0
    total_items = 0
    changes = []
    for card, items in sorted(by_card.items()):
        path = card_file.get(card)
        if not path:
            missing += 1
            continue
        content = open(path, encoding="utf-8").read()
        if MARK in content and "## 考点提示" in content:
            skipped += 1
            continue
        lines = []
        lines.append(MARK + f"(共 {len(items)} 题,详见 `资料/模拟试卷/汇总/模拟试卷汇总.md`):")
        for it in sorted(items, key=lambda x: (x["set"], "一二三四".index(x["unit"]), x["no"])):
            a = it["a"]
            if a.startswith("⚠️"):
                a_short = "待核"
            else:
                a_short = a.split("(")[0].strip()
            lines.append(f"- 卷{it['set']}·U{('一二三四'.index(it['unit']) + 1)}·#{it['no']} {shorten(it['q'])} · 答案 {a_short}")
        block = "\n".join("> " + s for s in lines)
        # 插入到 `## 考点提示` 标题之后(其下一行即列表首项之前)
        m = re.search(r"^## 考点提示\s*\n", content, re.M)
        if not m:
            missing += 1
            continue
        pos = m.end()
        content = content[:pos] + block + "\n\n" + content[pos:]
        open(path, "w", encoding="utf-8").write(content)
        injected += 1
        total_items += len(items)
        changes.append((card, len(items), path))

    print(f"注入卡数={injected}, 注入条目={total_items}, 跳过(已注入)={skipped}, 找不到卡={missing}")
    # 抽查最多题的一张卡
    if changes:
        top = max(changes, key=lambda x: x[1])
        print(f"题最多卡: {top[0]} ({top[1]} 题) -> {top[2]}")


if __name__ == "__main__":
    main()