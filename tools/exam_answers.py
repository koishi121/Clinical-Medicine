#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam_answers.py (v2) — 「对照 txt 回填答案」管线工具(支持 OCR 同题号多块:题号+出现序号)。
命令:
  python exam_answers.py --dump 卷=一 单元=二
      → 导出该单元「待核对」题(题干/选项,带 {no}#{occ})到 tools/_tbd/… 并打印
  python exam_answers.py --apply <答案表.tsv>
      → 表列: 卷<TAB>单元<TAB>题号<TAB>出现序号(0起)<TAB>答案<TAB>备注
        回填 汇总答案行 + 核对清单「参考答案」列
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


def parse_blocks():
    """返回 [(set, unit, no, occ, q, ops, a, ok, start_idx)] 保持文件顺序。"""
    lines = open(SUM, encoding="utf-8").read().split("\n")
    blocks = []
    cur = None
    cnt = {}
    for i, ln in enumerate(lines):
        m = REQ.match(ln)
        if m:
            k = (m.group("set"), m.group("unit"), int(m.group("no")))
            occ = cnt.get(k, 0)
            cnt[k] = occ + 1
            cur = dict(st=m.group("set"), un=m.group("unit"), no=int(m.group("no")),
                       occ=occ, q="", ops="", a="", ok=False, line=i)
            blocks.append(cur)
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
    return blocks


def dump(setn, unitn):
    blocks = [b for b in parse_blocks() if b["st"] == setn and b["un"] == unitn]
    pend = [b for b in blocks if not b["ok"]]
    os.makedirs(TBD, exist_ok=True)
    outp = os.path.join(TBD, f"卷{setn}·第{unitn}单元.md")
    with open(outp, "w", encoding="utf-8") as f:
        f.write(f"# 卷{setn} 第{unitn}单元 待核对题({len(pend)})\n")
        for b in pend:
            f.write(f"--- T{b['no']}#{b['occ']} ---\n题干: {b['q']}\n选项: {b['ops']}\n")
    print(f"待核 {len(pend)}/{len(blocks)} 块 -> {outp}")
    for b in pend:
        print(f"T{b['no']}#{b['occ']}: {b['q'][:50]}")


def apply(tsv):
    rows = []
    for line in open(tsv, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) < 5:
            continue
        rows.append((p[0].strip(), p[1].strip(), int(p[2].strip()), int(p[3].strip()),
                     p[4].strip().upper(), p[5].strip() if len(p) > 5 else ""))
    blocks = parse_blocks()
    key = {(b["st"], b["un"], b["no"], b["occ"]): b for b in blocks}
    # 1) 汇总答案行
    lines = open(SUM, encoding="utf-8").read().split("\n")
    apply_map = {}
    for r in rows:
        k = (r[0], r[1], r[2], r[3])
        if k in key:
            b = key[k]
            if not b["ok"]:
                apply_map[k] = r[4] + (f"({r[5]})" if r[5] else "(教材推断)")
            else:
                print(f"[跳过已答] {k}")
    changes = 0
    for i, ln in enumerate(lines):
        m = REQ.match(ln)
        if not m:
            continue
        k = (m.group("set"), m.group("unit"), int(m.group("no")))
        # 找到该题第 occ 次出现 → 需要统计
    # 重新按出现序定位
    cnt = {}
    for i, ln in enumerate(lines):
        m = REQ.match(ln)
        if not m:
            continue
        k = (m.group("set"), m.group("unit"), int(m.group("no")))
        occ = cnt.get(k, 0)
        cnt[k] = occ + 1
        ak = (k[0], k[1], k[2], occ)
        if ak in apply_map:
            for j in range(i + 1, min(i + 14, len(lines))):
                am = RLA.match(lines[j].strip())
                if am and am.group("a").startswith("⚠️"):
                    lines[j] = f"- **答案**:{apply_map[ak]}"
                    changes += 1
                    break
    with open(SUM, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    # 2) 核对清单填列(按 题号+occ 可能重复;清单行以 卷·单元·题号 唯一,多条取第一条命中)
    clines = open(CK, encoding="utf-8").read().split("\n")
    filled = 0
    for i, ln in enumerate(clines):
        if not ln.startswith("| 卷"):
            continue
        for r in rows:
            key2 = f"卷{r[0]}·第{r[1]}·{r[2]}"
            if ln.startswith("| " + key2 + " |"):
                parts = ln.split("|")
                if len(parts) >= 5 and parts[4].strip() == "":
                    parts[4] = f" {r[4]} "
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
        dump(d.get("卷", "一"), d.get("单元", "二"))
    elif "--apply" in sys.argv:
        apply(sys.argv[sys.argv.index("--apply") + 1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()