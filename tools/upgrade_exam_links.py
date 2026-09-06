#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upgrade_exam_links.py — 卡 ↔ 题双向互通:把卡内 `## 考点提示` 下的真题反链
(第2步 inject_exam_links.py 生成的纯文本)升级为可点击链接,跳回
《模拟试卷汇总.md》中对应题块(标题锚点),并刷新最新判答答案。

设计:
- 幂等:每次从汇总全量重算并整体替换每卡的真题 blockquote。
- 链接:目标 = 资料/模拟试卷/汇总/模拟试卷汇总.md#<题块标题slug>
  slug 用 VS Code / github-slugger 兼容算法(小写、去 ()'"!: 等、空格转 -);
  同卷单元题号有多个 OCR 重复块时,VS Code 预览锚点会追加 -1/-2…
  → 目标块 occ≥1 时链接 slug 追加 -{occ},并在题干后加 〔块k/m〕 标注。
用法: python upgrade_exam_links.py
"""
import os
import re
import sys
from collections import OrderedDict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"D:\Clinical Medicine"
SUM = os.path.join(ROOT, "资料", "模拟试卷", "汇总", "模拟试卷汇总.md")
C03 = os.path.join(ROOT, "考试", "03_临床医学综合")
MARK = "📝 **2026模拟卷真题**"
UNIT_NO = "一二三四"

BLOCK_HEAD = re.compile(r"^### 卷(?P<set>[一二三])·第(?P<unit>[一二三四])单元·第(?P<no>\d+)题(?P<tail>.*)$")
LINE_Q = re.compile(r"^- \*\*题干\*\*:(?P<q>.+)$")
LINE_A = re.compile(r"^- \*\*答案\*\*:(?P<a>.+)$")
LINE_C = re.compile(r"^- \*\*关联卡\*\*:\[(?P<name>[^\]]+)\]\((?P<link>[^)]+)\)$")


def slugify(h):
    """对齐 VS Code githubSlugifier(fromHeading)。
    流程: trim → lower → 剔除一切非 [字母/数字/_/空格/-] 的字符(中文间隔号·、括号等全删)
          → 空白替换为 -
    """
    s = h.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)   # \w 在 py3 含中文与数字下划线;删除 ·() 等
    s = re.sub(r"\s+", "-", s)
    return s


def shorten(s, n=38):
    s = s.strip()
    return s if len(s) <= n else s[:n] + "…"


def parse_blocks():
    """返回 [(set,unit,no,occ,total,title,slug,q,a,ok,name)] name=关联卡名(可为None)。"""
    lines = open(SUM, encoding="utf-8").read().split("\n")
    cnt = {}
    blocks = []
    cur = None
    for ln in lines:
        m = BLOCK_HEAD.match(ln)
        if m:
            k = (m.group("set"), m.group("unit"), int(m.group("no")))
            occ = cnt.get(k, 0)
            cnt[k] = occ + 1
            title = ln[len("### "):].strip()
            cur = dict(st=m.group("set"), un=m.group("unit"), no=int(m.group("no")),
                       occ=occ, title=title, slug=slugify(title),
                       q="", a="", ok=False, name=None, link=None)
            blocks.append(cur)
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
            cur["ok"] = not cur["a"].startswith("⚠️")
            continue
        m = LINE_C.match(ln)
        if m:
            cur["name"] = m.group("name")
            cur["link"] = m.group("link")
            cur = None
    # 回填每题号总块数(仅用于卡片〔块k/m〕提示)
    tot = {}
    for b in blocks:
        k = (b["st"], b["un"], b["no"])
        tot[k] = tot.get(k, 0) + 1
    for b in blocks:
        b["total"] = tot[(b["st"], b["un"], b["no"])]
    # 模拟 VS Code githubSlugifier.createBuilder():同标题 slug 第二次起追加 -1/-2…
    # (blocks 按文档顺序 append,顺序即文件顺序)
    seen = {}
    for b in blocks:
        base = b["slug"]
        if base not in seen:
            seen[base] = 0
        else:
            seen[base] += 1
            b["slug"] = f"{base}-{seen[base]}"
    return blocks


def main():
    allb = parse_blocks()
    doc_slugs = {b["slug"] for b in allb}          # 汇总全部题目标题的真实锚点(VS Code slug)
    blocks = [b for b in allb if b["name"]]
    # 卡名 → 题目
    by_card = OrderedDict()
    for b in sorted(blocks, key=lambda x: (x["st"], UNIT_NO.index(x["un"]), x["no"], x["occ"])):
        by_card.setdefault(b["name"], []).append(b)
    # 卡名 → 文件
    card_file = {}
    for dirpath, _, files in os.walk(C03):
        for f in files:
            if f.lower().endswith(".md") and f.lower() != "readme.md":
                card_file.setdefault(os.path.splitext(f)[0], os.path.join(dirpath, f))

    updated = inserted = skipped = missing = 0
    total_links = 0
    frags = []
    for card, items in by_card.items():
        path = card_file.get(card)
        if not path:
            missing += 1
            continue
        content = open(path, encoding="utf-8").read()
        m = re.search(r"^## 考点提示\s*\n", content, re.M)
        if not m:
            skipped += 1
            continue
        pos = m.end()  # 插入点:考点提示标题行之后
        rel = os.path.relpath(SUM, os.path.dirname(path)).replace("\\", "/")
        new_lines = [MARK + f"(共 {len(items)} 题,点击题号跳转题目·全表 `资料/模拟试卷/汇总/模拟试卷汇总.md`):"]
        for it in items:
            a_short = "待核" if not it["ok"] else it["a"].split("(")[0].strip()
            seg = f"卷{it['st']}·U{UNIT_NO.index(it['un']) + 1}·#{it['no']}"
            dup = f"〔块{it['occ'] + 1}/{it['total']}〕" if it["total"] > 1 else ""
            text = f"{shorten(it['q'])} · 答案 {a_short}"
            new_lines.append(f"- [{seg}]({rel}#{it['slug']}){dup} {text}")
            frags.append(it["slug"])
        block = "\n".join("> " + s for s in new_lines)

        lines = content.split("\n")
        # 找旧 blockquote(MARK 行起,连续 > 行止)
        js = next((i for i, l in enumerate(lines) if MARK in l), None)
        if js is not None:
            ke = js
            while ke < len(lines) and lines[ke].lstrip().startswith(">"):
                ke += 1
            del lines[js:ke]
            # pos 可能因删除前移;重定位插入索引=考点提示标题后的首个空/原位置
            inserted_at = js
        else:
            # 计算在 lines 中的插入行号:标题所在行之后
            hi = next(i for i, l in enumerate(lines) if l.startswith("## 考点提示"))
            inserted_at = hi + 1
        lines[inserted_at:inserted_at] = block.split("\n")
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        total_links += len(items)
        if js is not None:
            updated += 1
        else:
            inserted += 1

    print(f"卡(升级/新插)={updated}/{inserted}, 链接条目={total_links}, 缺卡={missing}, 无考点提示跳过={skipped}")
    # 自检:每个链接 fragment 都必须命中汇总标题的 slug 集合
    miss = sorted({f for f in frags if f not in doc_slugs})
    print(f"自检: 链接 fragment {len(frags)} 个, 未命中汇总锚点 {len(miss)} 个")
    for x in miss:
        print("  未命中:", x)
    if not miss:
        print("✓ 全部链接可精确定位到对应题目标题")


if __name__ == "__main__":
    main()
