#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_tbd.py — 导出模拟试卷汇总中全部「待核对」题(答案行以 ⚠️ 开头)为翻书核对清单。
输出: 资料/模拟试卷/汇总/待核对题清单.md  (按 卷·单元·题号 分组;附题干/选项残文与缺失标记)
用法: python export_tbd.py
"""
import os
import re

ROOT = r"D:\Clinical Medicine"
SUM = os.path.join(ROOT, "资料", "模拟试卷", "汇总", "模拟试卷汇总.md")
OUT = os.path.join(ROOT, "资料", "模拟试卷", "汇总", "待核对题清单.md")

REQ = re.compile(r"^### 卷(?P<set>[一二三])·第(?P<unit>[一二三四])单元·第(?P<no>\d+)题")
RLQ = re.compile(r"^- \*\*题干\*\*:(?P<q>.+)$")
RLOP = re.compile(r"^- \*\*选项\*\*:(?P<o>.+)$")
RLA = re.compile(r"^- \*\*答案\*\*:(?P<a>.+)$")
RANS = re.compile(r"^- \*\*解析精要\*\*:")
UNIT_NAME = {"一": "第一单元", "二": "第二单元", "三": "第三单元", "四": "第四单元"}
SORD = {"一": 1, "二": 2, "三": 3, "四": 4}
SETNAME = {"一": "卷一", "二": "卷二", "三": "卷三"}


def parse_blocks():
    lines = open(SUM, encoding="utf-8").read().split("\n")
    blocks = []
    cur = None
    cnt = {}
    for ln in lines:
        m = REQ.match(ln)
        if m:
            k = (m.group("set"), m.group("unit"), int(m.group("no")))
            occ = cnt.get(k, 0)
            cnt[k] = occ + 1
            cur = dict(st=m.group("set"), un=m.group("unit"), no=int(m.group("no")),
                       occ=occ, q="", ops="", a="")
            blocks.append(cur)
            continue
        if cur is None:
            continue
        if RLQ.match(ln):
            cur["q"] = RLQ.match(ln).group("q").strip()
        elif RLOP.match(ln):
            cur["ops"] = RLOP.match(ln).group("o").strip()
        elif RLA.match(ln):
            cur["a"] = RLA.match(ln).group("a").strip()
    return blocks


def flag(q, ops):
    """判定残损类型标签。"""
    tags = []
    if not q:
        tags.append("题干缺失")
    elif re.search(r"(?:^|[，。；、])[A-E](?:[^A-Za-z]{0,6}|$)", q) or q.rstrip()[-1:].isalpha() is False:
        pass  # 复杂判定留给人工,此处不做噪音
    if not ops:
        tags.append("选项缺失")
    if not q and not ops:
        tags = ["题干+选项均缺失(整块OCR截断)"]
    # 题干尾部粘连 OCR 答案残片(如 "...是A胶质瘤" / "...的检查是AB超")
    if q and re.search(r"[A-E]$|[，。；、][A-E](?![A-Za-z])", q):
        tags.append("题干尾部疑混入答案/选项残片")
    return "；".join(tags) if tags else "题干完整"


def main():
    blocks = parse_blocks()
    pend = [b for b in blocks if b["a"].startswith("⚠️")]
    pend.sort(key=lambda b: (SORD[b["st"]], SORD[b["un"]], b["no"], b["occ"]))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# 模拟试卷 · 待核对题清单(翻书用)\n\n")
        f.write(f"> 汇总中答案仍为 ⚠️ 待核对 的题块共 **{len(pend)}** 个(按卷/单元分组)。"
                f"每题给出 OCR 残文,便于对照原书精析页补答。\n")
        f.write("> 生成: tools/export_tbd.py\n\n")
        # 概览小表(数字序)
        from collections import OrderedDict
        agg = OrderedDict()
        for b in pend:
            k = (SETNAME[b["st"]], UNIT_NAME[b["un"]])
            agg.setdefault(k, 0)
            agg[k] += 1
        f.write("| 卷/单元 | 待核数 |\n|---|---|\n")
        for k, n in agg.items():
            f.write(f"| {k[0]}·{k[1]} | {n} |\n")
        f.write("\n---\n\n")

        prev = None
        for b in pend:
            key = (SETNAME[b["st"]], UNIT_NAME[b["un"]])
            if key != prev:
                if prev is not None:
                    f.write("\n")
                f.write(f"\n## {key[0]} · {key[1]}\n\n")
                prev = key
            tag = flag(b["q"], b["ops"])
            f.write(f"### 第 {b['no']} 题  *(块#{b['occ']}·{tag})*\n")
            if b["q"]:
                f.write(f"- **题干残文**: {b['q']}\n")
            else:
                f.write(f"- **题干残文**: (缺失)\n")
            if b["ops"]:
                f.write(f"- **选项残文**: {b['ops']}\n")
            else:
                f.write(f"- **选项残文**: (缺失)\n")
            f.write(f"- **现答案行**: {b['a']}\n\n")

    print(f"待核块 {len(pend)} -> {OUT}")


if __name__ == "__main__":
    main()
