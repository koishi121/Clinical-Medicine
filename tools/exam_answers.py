#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam_answers.py — 「对照 txt 回填答案」管线工具。
命令:
  python exam_answers.py --dump 卷=一 单元=一
      → 导出该单元「待核对」题(题干/选项)到 tools/_tbd/卷一·第一单元.md 并打印
  python exam_answers.py --apply <答案表.tsv>
      → 按表(卷\t单元\t题号\t答案\t备注)回填:
        · 模拟试卷汇总.md 的答案行(待核对→ X (教材推断))
        · 答案核对清单.md 的「参考答案」列
用法: 先 dump 看题 → 人工(我)判答写 tsv → apply
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\Clinical Medicine"
SUM = os.path.join(ROOT, "资料", "模拟试卷", "汇总", "模拟试卷汇总.md")
CK = os.path.join(ROOT, "资料", "模拟试卷", "汇总", "答案核对清单.md")
TBD = os.path.join(ROOT, "tools", "_tbd")

REQ = re.compile(r"^### 卷(?P<set>[一二三])·第(?P<unit>[一二三四])单元·第(?P<no>\d+)题")
RLQ = re.compile(r"^- \*\*题干\*\*:(?P<q>.+)$")
RLOP = re.compile(r"^- \*\*选项\*\*:(?P<o>.+)$")
RLA = re.compile(r"^- \*\*答案\*\*:(?P<a>.+)$")


def cn(x):
    return "一二三四五六七八九十".index(x) + 1


def parse_sections():
    lines = open(SUM, encoding="utf-8").read().split("\n")
    items = []
    cur = None
    for ln in lines:
        m = REQ.match(ln)
        if m:
            cur = dict(st=m.group("set"), un=m.group("unit"), no=int(m.group("no")),
                       q="", ops="", a="", ok=False)
            items.append(cur)
            continue
        if cur is None:
            continue
        m = RLQ.match(ln)
        if m:
            cur["q"] = m.group("q").strip()
            continue
        m = RLOP.match(ln)
        if m:
            cur["ops"] = m.group("o").strip()
            continue
        m = RLA.match(ln)
        if m:
            cur["a"] = m.group("a").strip()
            cur["ok"] = not cur["a"].startswith("⚠️")
    return items


def dump(setn, unitn):
    items = parse_sections()
    sel = [it for it in items if it["st"] == setn and it["un"] == unitn]
    pend = [it for it in sel if not it["ok"]]
    pend.sort(key=lambda x: x["no"])
    os.makedirs(TBD, exist_ok=True)
    outp = os.path.join(TBD, f"卷{setn}·第{unitn}单元.md")
    with open(outp, "w", encoding="utf-8") as f:
        f.write(f"# 卷{setn} 第{unitn}单元 待核对题({len(pend)})\n")
        f.write("字段: T=题号 | 题干 | 选项 | (请在答案列补充)\n")
        for i, it in enumerate(pend, 1):
            f.write(f"--- T{it['no']} ---\n题干: {it['q']}\n选项: {it['ops']}\n")
    print(f"待核 {len(pend)}/{len(sel)} 题 -> {outp}")
    for it in pend:
        print(f"T{it['no']}: {it['q'][:52]}")


def apply(tsv):
    rows = []
    for line in open(tsv, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) < 4:
            continue
        rows.append((p[0].strip(), p[1].strip(), int(p[2].strip()), p[3].strip().upper(),
                     p[4].strip() if len(p) > 4 else ""))
    # 1) 汇总答案行
    items = parse_sections()
    by_key = {(it["st"], it["un"], it["no"]): it for it in items}
    n_ok = [r for r in rows if (r[0], r[1], r[2]) in by_key and not by_key[(r[0], r[1], r[2])]["ok"]]
    changes = 0
    lines = open(SUM, encoding="utf-8").read().split("\n")
    map_a = {}
    for r in rows:
        map_a[(r[0], r[1], r[2])] = r[3] + (f"({r[4]})" if r[4] else "(教材推断)")
    for i, ln in enumerate(lines):
        m = REQ.match(ln)
        if not m:
            continue
        k = (m.group("set"), m.group("unit"), int(m.group("no")))
        if k in map_a:
            # 找到下一个「答案」行
            for j in range(i + 1, min(i + 12, len(lines))):
                am = RLA.match(lines[j].strip())
                if am and am.group("a").startswith("⚠️"):
                    lines[j] = f"- **答案**:{map_a[k]}"
                    changes += 1
                    break
    with open(SUM, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    # 2) 核对清单填列
    clines = open(CK, encoding="utf-8").read().split("\n")
    filled = 0
    for i, ln in enumerate(clines):
        if not ln.startswith("| 卷"):
            continue
        for r in rows:
            key = f"卷{r[0]}·第{r[1]}·{r[2]}"
            if ln.startswith("| " + key + " |"):
                parts = ln.split("|")
                if len(parts) >= 5 and parts[4].strip() == "":
                    parts[4] = f" {r[3]} "
                    clines[i] = "|".join(parts)
                    filled += 1
                break
    with open(CK, "w", encoding="utf-8") as f:
        f.write("\n".join(clines))
    print(f"回填汇总答案行: {changes}  | 核对清单填列: {filled}  | 表内有效行: {len(rows)}")


def main():
    if "--dump" in sys.argv:
        i = sys.argv.index("--dump")
        d = dict(x.split("=", 1) for x in sys.argv[i + 1:i + 3])
        dump(d.get("卷", "一"), d.get("单元", "一"))
    elif "--apply" in sys.argv:
        apply(sys.argv[sys.argv.index("--apply") + 1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()