#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
outline_md.py — 在根目录生成「大纲导航.md」:2026 大纲六部分总览 + 临床 13 系统全部病种卡链接,
并给每张正库卡头部注入反向链接「> 大纲导航:」(互相链接)。
用法: python outline_md.py [<根目录>]
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else r"d:\Clinical Medicine")
OUT_NAME = "大纲导航.md"
C03 = os.path.join("考试", "03_临床医学综合")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")


def relh(path):
    return path.replace("\\", "/")


def read_sections(system_dir):
    """返回 (high, niche):卡文件名列表(按 README 高频/小众节)。"""
    readme = os.path.join(system_dir, "README.md")
    high, niche = [], []
    if os.path.isfile(readme):
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        mh = re.search(r"## 高频卡片.*?(?=\n## |\Z)", text, re.S)
        mn = re.search(r"## 小众骨架.*?(?=\n## |\Z)", text, re.S)
        if mh:
            high = [os.path.splitext(os.path.basename(p))[0] for p in LINK_RE.findall(mh.group(0))]
        if mn:
            niche = [os.path.splitext(os.path.basename(p))[0] for p in LINK_RE.findall(mn.group(0))]
    return high, niche


def card_level(path):
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        m = re.search(r">\s*大纲要求\s*:([^\n]*)", src)
        lv = m.group(1).strip() if m else ""
        if lv.startswith("🔷"):
            return "🔷"
        if lv.startswith("◽"):
            return "◽"
    except OSError:
        pass
    return ""


def validate_path(p):
    return os.path.isfile(os.path.join(ROOT, p))


def main():
    card_ok = 0
    high_total = niche_total = 0
    parts_body = []
    # 六部分总览
    overview = []
    overview.append("| 部分 | 内容 | 工作区 |")
    overview.append("|---|---|---|")
    overview.append(f"| 一、医学人文综合 | 医学心理/伦理/卫生法规 25 部/人文素养(**2026 修订**) | [`02_医学人文综合`]({relh(os.path.join('考试','02_医学人文综合','README.md'))}) |")
    overview.append(f"| 二、基础医学综合 | 8 科:解剖/生化/生理/微生物/免疫/病理/病理生理/药理 | [`01_基础医学综合`]({relh(os.path.join('考试','01_基础医学综合','README.md'))}) |")
    overview.append(f"| 三、预防医学综合 | 绪论/医学统计/流行病学/临床预防/社区公卫/卫生服务 | [`04_预防医学综合`]({relh(os.path.join('考试','04_预防医学综合','README.md'))}) |")
    overview.append("| 四、临床医学综合 | **13 系统 (正库 14 目录 ↔ 拆分口径),病种卡见下** | [`03_临床医学综合`](考试/03_临床医学综合/README.md) |")
    overview.append(f"| 五、中医学基础 | **3 单元**:基本特点/基础理论/四诊 | [`06_中医学基础`]({relh(os.path.join('考试','06_中医学基础','README.md'))}) |")
    overview.append(f"| 六、实践综合 | 临床思维/体格检查/基本操作 | [`05_实践技能`]({relh(os.path.join('考试','05_实践技能','README.md'))}) |")

    # 第四部分:13 系统 → 全部病种卡
    systems = []
    c03 = os.path.join(ROOT, C03)
    for sysname in sorted(os.listdir(c03)):
        sdir = os.path.join(c03, sysname)
        if not os.path.isdir(sdir):
            continue
        high, niche = read_sections(sdir)
        lines = [f"### 💾 {sysname}"]
        lines.append(f"- 系统 README:[`{relh(os.path.join(C03, sysname, 'README.md'))}`]({relh(os.path.join(C03, sysname, 'README.md'))})")
        items = []
        for name in high:
            items.append((name, "🔷"))
        for name in niche:
            items.append((name, "◽"))
        # 兜底:README 未列但存在且带等级的卡
        seen = {n for n, _ in items}
        for f in sorted(os.listdir(sdir)):
            base = os.path.splitext(f)[0]
            if f.lower().endswith(".md") and f.lower() != "readme.md" and base not in seen:
                lvl = card_level(os.path.join(sdir, f))
                if lvl:
                    items.append((base, lvl))
        # 按 掌握 在前、熟悉 在后
        items.sort(key=lambda x: (0 if x[1] == "🔷" else 1, x[0]))
        for name, lvl in items:
            fp = os.path.join(C03, sysname, name + ".md")
            if validate_path(fp):
                items_md = f"- [ ] {lvl} [{name}]({relh(fp)})"
                lines.append(items_md)
                if lvl == "🔷":
                    high_total += 1
                else:
                    niche_total += 1
            else:
                lines.append(f"- ⚠️ [{name}]({relh(fp)}) 文件缺失")
        card_ok += len(items)
        systems.append("\n".join(lines))

    head = [
        "# 🧭 大纲导航 · 2026 临床执业医师资格考试",
        "",
        "> 依据:**2024 年修订临床执业医师大纲**(六部分)+ **2026 年修订医学人文部分**(国卫医考委发〔2026〕1号)。",
        "> 大纲文件与抽文本:`资料\\执业医师大纲\\_txt\\`;覆盖度对账:[`资料\\覆盖度对账.md`](资料/覆盖度对账.md)。",
        "> 本页为**大纲 ↔ 病种卡**互相跳转入口:左侧到各单元与全部病种卡;每张卡头部亦有返回本页的「大纲导航」链接。",
        "",
        "## 考试框架与 2026 时间线",
        f"- 实践技能考试 + 医学综合笔试(4 单元:基础/人文/临床/预防);时间线见 [`00_大纲与计划`]({relh(os.path.join('考试','00_大纲与计划','README.md'))})。",
        "",
        "## 大纲六部分 ↔ 工作区单元",
        *overview,
        "",
    ]
    content = "\n".join(head)
    content += "\n\n## 第四部分 临床医学综合 · 13 系统病种卡(双向链接)\n"
    content += "\n\n".join(systems)
    content += "\n\n## 其余单元直达\n"
    content += (f"- [`01_基础医学综合`]({relh(os.path.join('考试','01_基础医学综合','README.md'))}) · "
                f"[`02_医学人文综合`]({relh(os.path.join('考试','02_医学人文综合','README.md'))}) · "
                f"[`04_预防医学综合`]({relh(os.path.join('考试','04_预防医学综合','README.md'))}) · "
                f"[`05_实践技能`]({relh(os.path.join('考试','05_实践技能','README.md'))}) · "
                f"[`06_中医学基础`]({relh(os.path.join('考试','06_中医学基础','README.md'))})\n")
    content += "\n> 病种卡标注:🔷 掌握(高频) / ◽ 熟悉(小众);完整缺卡与建议见覆盖度对账。\n"

    with open(os.path.join(ROOT, OUT_NAME), "w", encoding="utf-8") as f:
        f.write(content)

    # === 反向链接:给每张卡注入 `> 大纲导航:` ===
    injected = 0
    back = "> 大纲导航:[大纲导航.md](../../../大纲导航.md)"
    for sysname in sorted(os.listdir(c03)):
        sdir = os.path.join(c03, sysname)
        if not os.path.isdir(sdir):
            continue
        for f in sorted(os.listdir(sdir)):
            if not f.lower().endswith(".md") or f.lower() == "readme.md":
                continue
            fp = os.path.join(sdir, f)
            with open(fp, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
            if any(ln.startswith("> 大纲导航:") for ln in lines):
                continue
            target = None
            for i, ln in enumerate(lines):
                if ln.startswith(("> 大纲要求:", "> 来源:")):
                    target = i
                    break  # 插到 大纲要求 或 来源 之后
            if target is None:
                continue
            lines.insert(target + 1, back)
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
            injected += 1
    print(f"wrote: {os.path.join(ROOT, OUT_NAME)}  (病种卡 {card_ok} 链接, 掌握{high_total}/熟悉{niche_total})")
    print(f"为 {injected} 张卡注入返回链接")


if __name__ == "__main__":
    main()