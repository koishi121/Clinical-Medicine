#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_new_cards.py — 把新补病种卡自动挂进各系统 README(高频→🔷掌握、小众→◽熟悉),幂等。
用法: python sync_new_cards.py
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"d:\Clinical Medicine"
C03 = os.path.join(ROOT, "考试", "03_临床医学综合")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")

# (系统, 卡名, 掌握/熟悉)
NEW = [
    ("呼吸系统", "非特异性间质性肺炎", "熟悉"),
    ("呼吸系统", "肋骨骨折", "熟悉"),
    ("呼吸系统", "纵隔肿瘤", "熟悉"),
    ("心血管系统", "周围血管疾病", "熟悉"),
    ("消化系统", "肠结核", "熟悉"),
    ("消化系统", "腹外疝", "熟悉"),
    ("消化系统", "腹部损伤", "熟悉"),
    ("消化系统", "胆道肿瘤", "熟悉"),
    ("消化系统", "肝脓肿", "熟悉"),
    ("消化系统", "脂肪性肝病", "熟悉"),
    ("消化系统", "直肠肛管疾病", "熟悉"),
    ("泌尿系统", "男性生殖系统感染", "熟悉"),
    ("泌尿系统", "泌尿系梗阻", "熟悉"),
    ("泌尿系统", "泌尿系统外伤", "熟悉"),
    ("泌尿系统", "睾丸及阴茎肿瘤", "熟悉"),
    ("泌尿系统", "男生殖先天性疾病", "熟悉"),
    ("女性生殖系统", "妊娠合并内科疾病", "熟悉"),
    ("女性生殖系统", "异常分娩", "熟悉"),
    ("女性生殖系统", "生殖道炎症", "熟悉"),
    ("女性生殖系统", "生殖内分泌异常", "熟悉"),
    ("女性生殖系统", "妊娠滋养细胞疾病", "熟悉"),
    ("女性生殖系统", "妊娠期其他并发症", "熟悉"),
    ("血液系统", "白细胞减少和粒细胞缺乏症", "熟悉"),
    ("内分泌系统", "甲状旁腺功能亢进症", "掌握"),
    ("内分泌系统", "垂体瘤", "熟悉"),
    ("内分泌系统", "胰岛素瘤", "熟悉"),
    ("内分泌系统", "亚急性甲状腺炎", "熟悉"),
    ("神经精神系统", "双相障碍", "掌握"),
    ("神经精神系统", "惊恐障碍", "掌握"),
    ("神经精神系统", "酒精使用障碍", "掌握"),
    ("神经精神系统", "失眠障碍", "掌握"),
    ("神经精神系统", "三叉神经痛", "熟悉"),
    ("神经精神系统", "脊髓压迫症", "熟悉"),
    ("神经精神系统", "视神经脊髓炎", "熟悉"),
    ("神经精神系统", "颅内占位与颅高压", "熟悉"),
    ("神经精神系统", "单纯疱疹性脑炎", "熟悉"),
    ("神经精神系统", "颅脑损伤", "熟悉"),
    ("神经精神系统", "其他精神障碍", "熟悉"),
    ("运动系统", "骨与关节结核", "熟悉"),
    ("运动系统", "其他骨肿瘤", "熟悉"),
    ("运动系统", "运动系统慢性损伤", "熟悉"),
    ("儿科", "唐氏综合征", "熟悉"),
    ("儿科", "苯丙酮尿症", "熟悉"),
    ("儿科", "儿童单纯性肥胖", "熟悉"),
    ("儿科", "维生素D缺乏性手足搐搦", "熟悉"),
    ("传染病", "自然疫源性疾病", "熟悉"),
    ("其他", "乳房疾病", "熟悉"),
    ("其他", "创伤总论", "熟悉"),
    ("其他", "外科营养", "熟悉"),
]


def section_end(text, start_head):
    """从 start_head 位置起,返回该节内容结束位置(上一个空行/下一个 # 行)。"""
    lines = text.split("\n")
    idx = start_head
    # 收集直到下一个 '^#' 行
    out_end = None
    for j in range(start_head + 1, len(lines)):
        if lines[j].lstrip().startswith("#"):
            out_end = j
            break
    # 节尾=下一个标题前的最后非空行(或整行序)
    end = out_end if out_end is not None else len(lines)
    return end


def find_head(lines, pat):
    for i, ln in enumerate(lines):
        if re.match(pat, ln):
            return i
    return None


def main():
    by_sys = {}
    for sysname, card, lvl in NEW:
        by_sys.setdefault(sysname, []).append((card, lvl))

    for sysname, cards in by_sys.items():
        readme = os.path.join(C03, sysname, "README.md")
        if not os.path.isfile(readme):
            print(f"[跳过] 无 README: {sysname}")
            continue
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        lines = text.split("\n")
        changed = False

        # 定位高频与尾随节
        h_idx = find_head(lines, r"^## 高频卡片")
        n_idx = find_head(lines, r"^## 小众骨架")
        for card, lvl in cards:
            target = None
            if lvl == "掌握":
                hd = h_idx if h_idx is not None else 0
                target = ("high", hd)
            else:
                nd = n_idx if n_idx is not None else 0
                target = ("niche", hd if False else nd)
            # 若节缺失则在该文件末尾创建
            if lvl == "掌握" and h_idx is None:
                text = text.rstrip("\n") + "\n\n## 高频卡片(初稿,待教材校对)\n"
                lines = text.split("\n")
                h_idx = find_head(lines, r"^## 高频卡片")
            if lvl == "熟悉" and n_idx is None:
                text = text.rstrip("\n") + "\n\n## 小众骨架(仅骨架)\n"
                lines = text.split("\n")
                n_idx = find_head(lines, r"^## 小众骨架")
            # 重新取值
            h_idx = find_head(lines, r"^## 高频卡片")
            n_idx = find_head(lines, r"^## 小众骨架")
            if lvl == "掌握":
                sec_head = h_idx
                line = f"- [ ] 🔲 [{card}]({card}.md)"
            else:
                sec_head = n_idx
                line = f"- [ ] [{card}]({card}.md)"
            # 检查是否已在
            if any(f"{card}.md" in ln for ln in lines):
                continue
            # 找到节尾插入点:节尾前最后一个非空行
            end = section_end("\n".join(lines), sec_head)
            # 插入到节内末尾(在下一个标题前)
            # 寻找节内最后一个 '-' 列表行之后的空行前
            insert_at = sec_head + 1
            for j in range(sec_head + 1, end):
                if lines[j].strip() == "" and j + 1 < end and lines[j + 1].strip() != "":
                    insert_at = j + 1
            # 若节内没有任何条目,直接追加
            if end == sec_head + 1:
                insert_at = sec_head + 1
            lines.insert(insert_at, line)
            changed = True

        if changed:
            with open(readme, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"[已更新] {sysname}: +{len(cards)} 条")
        else:
            print(f"[无变化] {sysname}")


if __name__ == "__main__":
    main()