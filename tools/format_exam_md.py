#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_exam_md.py — 优化《模拟试卷汇总.md》目录格式(幂等,重复运行安全)。
1) 顶部:单份 📑 目录(卷×单元锚点 + 题数/已答/待核)。
2) 单元标题稳定格式:## 卷X · 第Y单元 — N 题
   下一行:> ✅已答 A ⏳待核 B
用法: python format_exam_md.py
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\Clinical Medicine\资料\模拟试卷\汇总\模拟试卷汇总.md"
REQ = re.compile(r"^### 卷(?P<set>[一二三])·第(?P<unit>[一二三四])单元·第(?P<no>\d+)题")
RU = re.compile(r"^## 卷(?P<set>[一二三]) · 第(?P<unit>[一二三四])单元")
STAT = re.compile(r"^> ✅已答")
RLA = re.compile(r"^- \*\*答案\*\*:(?P<a>.+)$")


def main():
    lines = open(P, encoding="utf-8").read().split("\n")
    unit_idx = []
    for i, ln in enumerate(lines):
        if RU.match(ln):
            unit_idx.append(i)
    stats = {}
    for k, i in enumerate(unit_idx):
        s = RU.match(lines[i]).group("set")
        u = RU.match(lines[i]).group("unit")
        end = unit_idx[k + 1] if k + 1 < len(unit_idx) else len(lines)
        tot = ok = 0
        blk = None
        for j in range(i + 1, end):
            if REQ.match(lines[j].strip()):
                tot += 1
                blk = j
                continue
            if blk is not None:
                am = RLA.match(lines[j].strip())
                if am:
                    ok += int(not am.group("a").startswith("⚠️"))
                    blk = None
        stats[(s, u)] = (tot, ok)
    toc = ["", "## 📑 目录", "", "| 卷/单元 | 题数 | 已回填 | 待核 |", "| --- | --- | --- | --- |"]
    for s in "一二三":
        for u in "一二三四":
            tot, ok = stats.get((s, u), (0, 0))
            toc.append(f"| [卷{s}·第{u}单元](#卷{s}-·-第{u}单元--{tot}-题) | {tot} | {ok} | {tot - ok} |")
    toc.append("")
    out = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        if ln.startswith("## 📑 目录"):
            while i < n and not RU.match(lines[i]) and not lines[i].startswith("## 📊") and not lines[i].startswith("## 📖"):
                i += 1
            continue
        if ln.startswith("# 模拟试卷汇总"):
            out.append(ln)
            out.extend(toc)
            i += 1
            continue
        m = RU.match(ln)
        if m:
            s, u = m.group("set"), m.group("unit")
            tot, ok = stats.get((s, u), (0, 0))
            out.append(f"## 卷{s} · 第{u}单元 — {tot} 题")
            out.append(f"> ✅已答 {ok} ⏳待核 {tot - ok}")
            i += 1
            continue
        if STAT.match(ln):
            i += 1
            continue
        out.append(ln)
        i += 1
    with open(P, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    tot = sum(v[0] for v in stats.values())
    ok = sum(v[1] for v in stats.values())
    print(f"单元={len(unit_idx)} 题块={tot} 已回填={ok} 待核={tot - ok}")


if __name__ == "__main__":
    main()