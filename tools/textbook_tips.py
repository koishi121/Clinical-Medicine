#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
textbook_tips.py — 方案A「教材要点」流水线工具。
用法:
  python textbook_tips.py --extract "卡名,卡名,..." [--out <dir>]
从卡内 `> 教材出处:` 解析(书,行号)→ 抽取对应节正文 → 存 <out>/<卡名>.txt 供人工提炼。
"""
import os
import re
import sys
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\Clinical Medicine"
C03 = os.path.join(ROOT, "考试", "03_临床医学综合")
BOOK_DIR = os.path.join(ROOT, "资料", "教材")
HEAD = re.compile(r"^第[一二三四五六七八九十百]+[章节]\s*\S")
REF = re.compile(r"> 教材出处:(?P<book>[^·]+?10?版|内科学10版|外科学10版|传染病学10版|精神病学9版)")

BOOKFILES = [
    ("内科学", r"D:\Clinical Medicine\资料\教材\内科学第10版_(葛均波,_王辰,_王建安)_(z-library.sk,_1lib.sk,_z-lib.sk).txt"),
    ("外科学", r"D:\Clinical Medicine\资料\教材\外科学(第10版)_(吴在德_吴肇汉)_(z-library.sk,_1lib.sk,_z-lib.sk).txt"),
    ("传染病学", r"D:\Clinical Medicine\资料\教材\传染病学(第10版)_(未知)_(z-library.sk,_1lib.sk,_z-lib.sk).txt"),
    ("精神病学", r"D:\Clinical Medicine\资料\教材\精神病学(第9版)_(主_编__陆_林_李_涛_副主编__王高华_刘铁桥_方贻儒)_(z-library.sk,_1lib.sk,_z-lib.sk).txt"),
]
CACHE = {}


def find_file(book_label):
    if book_label in CACHE:
        return CACHE[book_label]
    for kw, p in BOOKFILES:
        if kw in book_label:
            CACHE[book_label] = p
            return p
    raise RuntimeError(f"未知教材: {book_label}")


def get_book_lines(label):
    p = find_file(label.replace("·", "10版").replace("内科学10版·", "内科学").split("·")[0])
    # 简化:直接按关键词
    for kw, fp in BOOKFILES:
        if kw in label or (kw + "10版") in label:
            if fp not in CACHE:
                CACHE[fp] = open(fp, encoding="utf-8-sig").read().split("\n")
            return CACHE[fp]
    raise RuntimeError("找不到教材文件")


def clean(s):
    return re.split(r"\s{2,}", s.strip().split("|")[0])[0]


def norm(s):
    return re.sub(r"[|\u3000\s]+|（.*?）|《.*?》", "", s)


def extract_body(label, line_no, seg_label, chap_label="", max_chars=2600):
    """节正文:优先节标题(正文区>600),否则章标题兜底,截到下一个 章/节 标题。"""
    lines = get_book_lines(label)
    nl = norm(seg_label)
    suffix = nl[3:] if nl.startswith("第") else nl  # 去“第X节”前缀
    cand = []
    for i, s in enumerate(lines):
        t = norm(s.strip())
        if i + 1 > 600 and t.startswith("第") and suffix and suffix in t:
            cand.append(i + 1)
    start = cand[0] if cand else None
    if start is None and chap_label:
        cl = norm(chap_label)
        for i, s in enumerate(lines):
            t = norm(s.strip())
            if i + 1 > 600 and t.startswith("第") and cl and cl in t:
                start = i + 1
                break
    if start is None:
        start = line_no
    end = None
    for j in range(start + 1, min(start + 800, len(lines))):
        t = lines[j].strip()
        if t and HEAD.match(t):
            end = j
            break
    seg = [clean(x) for x in lines[start + 1:end if end else start + 300] if x.strip()]
    body = "\n".join(seg)
    return body[:max_chars], start, end


def find_card_files():
    d = {}
    for dirpath, _, files in os.walk(C03):
        for f in files:
            if f.lower().endswith(".md") and f.lower() != "readme.md":
                d.setdefault(os.path.splitext(f)[0], os.path.join(dirpath, f))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", required=True, help="逗号分隔卡名")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "_tips_out"))
    a = ap.parse_args()
    cards = find_card_files()
    os.makedirs(a.out, exist_ok=True)
    for name in [x.strip() for x in a.extract.split(",")]:
        path = cards.get(name)
        if not path:
            print(f"[缺失卡] {name}")
            continue
        refs = [ln for ln in open(path, encoding="utf-8").read().split("\n") if ln.startswith("> 教材出处:")]
        print("=" * 80)
        print(f"[{name}] 出处行:")
        for r in refs:
            print("   ", r)
        if not refs:
            print("   无出处,跳过")
            continue
        # 取第一条(内科学优先)
        r = refs[0]
        m = re.search(r"内科学10版|外科学10版|传染病学10版|精神病学9版", r)
        book_label = m.group(0) if m else "?"
        mm = re.search(r"行(\d+)", r)
        line_no = int(mm.group(1)) if mm else None
        if line_no is None:
            print("   无行号,跳过")
            continue
        last = r.split(">")[-1] if ">" in r else r
        seg_label = last.split("(")[0].strip() or ""
        parts = [x.strip() for x in r.split(">") if x.strip()]
        chap_label = parts[-2].split("(")[0].strip() if len(parts) >= 2 else ""
        body, s0, e0 = extract_body(book_label, line_no, seg_label, chap_label)
        outp = os.path.join(a.out, name + ".txt")
        with open(outp, "w", encoding="utf-8") as f:
            f.write(f"# {name} 教材正文(首发 {book_label} 行{s0})\n\n{body}\n")
        print(f"   -> 存 {outp} ({len(body)} 字符, 正文行{s0})")
        print("   " + body[:150].replace("\n", " ") + " …")


if __name__ == "__main__":
    main()