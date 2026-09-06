#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
textbook_index.py — 阶段A:教材 txt 章节索引 + 卡内「教材出处」链接(零臃肿)。
1) 扫描 4 本教材 txt 的 篇/章/节 标题 → 生成 `资料\教材\教材索引.md`(书→篇→章→节→行号)。
2) 章/节标题 ↔ 正库卡名匹配 → 给卡注入 `> 教材出处:书·路径(行N)`,幂等。
用法: python textbook_index.py
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"D:\Clinical Medicine"
BOOK_DIR = os.path.join(ROOT, "资料", "教材")
OUT_INDEX = os.path.join(BOOK_DIR, "教材索引.md")
C03 = os.path.join(ROOT, "考试", "03_临床医学综合")
MARK = "> 教材出处:"

BOOKS = [  # (文件名关键词, 简名)
    ("内科学", "内科学10版"),
    ("外科学", "外科学10版"),
    ("传染病学", "传染病学10版"),
    ("精神病学", "精神病学9版"),
]

HEAD = re.compile(r"^第([一二三四五六七八九十百]+)([篇章节])\s*(\S.*)$")
OMIT = ("概述", "概论", "前言", "总论", "展望")
BANNED = ("概述", "概论", "总论", "前言", "展望", "定义", "病因", "发病机制",
          "临床表现", "治疗原则", "治疗", "诊断", "检查", "并发症", "预后",
          "护理", "康复", "随访", "分类", "分型", "流行病学")


def hit_ok(card, t):
    """节标题 t 是否指向卡 card。短词(≤3字)不允许反向包含,避免'窒息'误挂'新生儿窒息'。"""
    if card in t:
        return True
    if len(t) >= 4 and t in card and not any(b in t for b in BANNED):
        return True
    return False


def clean_title(t):
    t = t.strip()
    t = t.split("|")[0]            # 去页眉等 "|" 分隔噪声
    t = re.split(r"\s{2,}", t)[0]  # 去尾部作者等签名
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def scan_book(path, label):
    raw = open(path, encoding="utf-8-sig").read().split("\n")
    tree = []                      # (kind, cn, line, title)
    for i, s in enumerate(raw):
        s = s.strip()
        m = HEAD.match(s)
        if m:
            kind = m.group(2)
            cn = m.group(1)
            title = clean_title(m.group(3))
            tree.append((kind, cn, i + 1, title))
    return raw, tree


def build_index_entry(label, tree):
    """按出现顺序输出 篇>章>节 树形文本。返回 (lines, 平铺(路径字符串,line,title) 列表)"""
    out = []
    flat = []  # (路径字符串, kind, line, title)
    stack = []  # 每层当前节点标题
    for kind, cn, line, title in tree:
        if kind == "篇":
            stack = [title]
            out.append(f"- {title}(行{line})")
        elif kind == "章":
            stack = (stack[:1] if stack else []) + [title]
            ind = "  " * (1 if stack[:1] else 0)
            out.append(f"{ind}- 第{cn}章 {title}(行{line})")
        elif kind == "节":
            par = " > ".join(stack) if stack else ""
            path = f"{par} > 第{cn}节 {title}" if par else f"第{cn}节 {title}"
            flat.append((path, kind, line, title))
            ind = "  " * (len(stack))
            out.append(f"{ind}  - 第{cn}节 {title}(行{line})")
    return out, flat


def match_card():
    """卡名 → [(label, path, line, title)] 原文出自哪节。"""
    cards = {}
    for dirpath, _, files in os.walk(C03):
        for f in files:
            if f.lower().endswith(".md") and f.lower() != "readme.md":
                cards.setdefault(os.path.splitext(f)[0], os.path.join(dirpath, f))

    hits = {}
    for card in cards:
        if len(card) < 2:
            continue
        found = []
        for label in FLATS:
            flats = FLATS[label]
            for path, kind, line, title in flats:
                if hit_ok(card, title) and not any(b in title for b in BANNED):
                    found.append((label, path, line, title))
        if found:
            # 同书同节去重(取行号最小,即首次正文出现),并去掉目录/页眉重复
            best = {}
            for label, path, line, title in found:
                k = (label, title)
                if k not in best or line < best[k][0]:
                    best[k] = (line, path, title)
            rows = [(line, label, path, title) for (label, title), (line, path, _t) in best.items()]
            rows.sort()
            hits[card] = [(label, path, line, title) for line, label, path, title in rows]
    return cards, hits


def main():
    global TRESS, FLATS
    index_lines = ["# 教材索引(全书 txt 定位)", "",
                   "> 行号=文件内行(UTF-8,从1数)。卡内「教材出处」与本节互为指向;本表不进卡,仅仓库用。", ""]
    TRESS, FLATS, ORDER = {}, {}, []
    files = os.listdir(BOOK_DIR)
    for kw, label in BOOKS:
        fn = next((f for f in files if f.endswith(".txt") and kw in f), None)
        if not fn:
            print(f"[跳过] 未找到含「{kw}」的 txt")
            continue
        raw, tree = scan_book(os.path.join(BOOK_DIR, fn), label)
        TRESS[label] = tree
        flat_map = []
        ent_lines, flats = build_index_entry(label, tree)
        FLATS[label] = flats
        ORDER.append(label)
        index_lines.append(f"## {label}")
        index_lines.append("")
        index_lines.extend(ent_lines)
        index_lines.append("")
        print(f"[OK] {label}: 篇/章/节 标题 {len(tree)} 条")

    with open(OUT_INDEX, "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))
    print(f"[OK] 索引 -> {OUT_INDEX}")

    cards, hits = match_card()
    n_inject = 0
    for card, path in cards.items():
        if card not in hits:
            continue
        content = open(path, encoding="utf-8").read()
        if MARK in content:
            continue
        new_lines = []
        for label, p, line, title in hits[card][:3]:
            new_lines.append(f"{MARK}{label}·{p}(行{line})")
        # 插在 `> 大纲要求:` 行之后
        m = re.search(r"^> 大纲要求:.*$\n", content, re.M)
        if not m:
            continue
        pos = m.end()
        content = content[:pos] + "\n".join(new_lines) + "\n" + content[pos:]
        open(path, "w", encoding="utf-8").write(content)
        n_inject += 1
    print(f"[OK] 注入出处行: {n_inject} 张卡 (命中 {len(hits)})")
    nohit = [c for c in cards if c not in hits]
    print(f"未命中卡 {len(nohit)} 张(基础/人文/预防/法规等,不在4本书): 例 {nohit[:8]}")


if __name__ == "__main__":
    main()