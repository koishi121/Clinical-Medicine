#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_exam_summary.py (v2) — 解析模拟试卷 OCR,生成「题目+答案+解析精要+关联卡」汇总。
关键发现:
  · 书为 3 套卷 × 4 单元 ×150 题 = 1800 题 + 每套答案及精析 + 书末「临考抢分考点」。
  · 正确答案以「绿色」印刷,OCR 丢色;答案区题号行 NN.ABCDE 中 ABCDE 为选项桩,非答案。
  · 答案需从解析中提取显式信号(答案为X / 故答X / 最佳答案为X / (X) / 故选X 等),
    或经「排除式」推导(故不答 A、B、C、D → 余 E);无信号者标 ⚠️待核对(附解析首句)。
用法: python gen_exam_summary.py
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"D:\Clinical Medicine"
SRC = os.path.join(ROOT, "资料", "模拟试卷", "_txt",
                   "国家临床执业医师资格考试全真模拟试卷及精析.txt")
OUT_DIR = os.path.join(ROOT, "资料", "模拟试卷", "汇总")
OUT = os.path.join(OUT_DIR, "模拟试卷汇总.md")
C03 = os.path.join(ROOT, "考试", "03_临床医学综合")

CN = "一二三四五六七八九十"

HEAD_Q = re.compile(r"^2026国家临床执业医师资格考试全真模拟试卷（([一二三])）第([一二三四])单元$")
HEAD_A = re.compile(r"^2026国家临床执业医师资格考试全真模拟试卷（([一二三])）答案及精析第([一二三四])单元$")
PAGE_NO = re.compile(r"^\d{1,3}$")
QNO = re.compile(r"^(?P<no>\d{1,3})\s*[.．、]\s*(?P<body>.+)$")

# 显式答案信号(按优先级)
EXPLICIT = [
    (re.compile(r"最佳答案为\s*([A-E])", re.I), "最佳"),
    (re.compile(r"答案为\s*([A-E])", re.I), "显式"),
    (re.compile(r"故答案为\s*([A-E])", re.I), "显式"),
    (re.compile(r"答案\s*[:：]\s*([A-E])", re.I), "显式"),
    (re.compile(r"故答\s*([A-E])", re.I), "显式"),
    (re.compile(r"故选\s*([A-E])", re.I), "显式"),
    (re.compile(r"应选\s*([A-E])", re.I), "显式"),
    (re.compile(r"（\s*([A-E])\s*）", re.I), "显式"),
    (re.compile(r"选(?:其)?\s*([A-E])\b", re.I), "显式"),
]

# 排除式:故不答/不选 后紧跟的字母集
EXCL = re.compile(r"故不(?:答|选|是|属于)([A-E、,，和及\s]{1,40})")
ALL_L = {"A", "B", "C", "D", "E"}

# ---------- 卡片索引 ----------
CARDS = {}
for sysname in sorted(os.listdir(C03)):
    sdir = os.path.join(C03, sysname)
    if not os.path.isdir(sdir):
        continue
    for f in os.listdir(sdir):
        if f.lower().endswith(".md") and f.lower() != "readme.md":
            CARDS.setdefault(os.path.splitext(f)[0],
                             os.path.join("考试", "03_临床医学综合", sysname, f))

ALIAS = {
    "慢性阻塞性肺疾病": ["慢阻肺", "COPD"],
    "肺血栓栓塞症": ["肺栓塞"],
    "消化性溃疡": ["胃十二指肠溃疡", "十二指肠溃疡"],
    "特发性血小板减少性紫癜": ["ITP"],
    "原发免疫性血小板减少症": ["免疫性血小板减少"],
    "慢性粒细胞白血病": ["慢粒"],
    "心力衰竭": ["心衰"],
    "甲状腺功能亢进症": ["甲亢"],
    "单纯性甲状腺肿与甲状腺结节": ["单纯性甲状腺肿", "甲状腺结节"],
    "急性肾小球肾炎": ["急性肾炎"],
    "肾病综合征": ["肾综"],
    "系统性红斑狼疮": ["SLE", "红斑狼疮"],
    "精神分裂症": ["精分"],
    "短暂性脑缺血发作": ["TIA"],
}


def link_card(qtext):
    """用题干+选项匹配正库卡,返回卡名或 None。"""
    for card in CARDS:
        if len(card) >= 2 and card in qtext:
            return card
    for card, als in ALIAS.items():
        for a in als:
            if len(a) >= 2 and a in qtext and card in CARDS:
                return card
    return None


def extract_ans(text):
    """返回 (letter|None, mode)。mode: 显式/推导/None"""
    for pat, mode in EXPLICIT:
        m = pat.search(text)
        if m:
            return m.group(1).upper(), mode
    m = EXCL.search(text)
    if m:
        letters = set(ch.upper() for ch in re.findall(r"[A-Ea-e]", m.group(1)))
        if letters and len(letters) == 4:
            rest = ALL_L - letters
            if len(rest) == 1:
                return rest.pop(), "推导"
    return None, None


def parse():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    qunits = {}            # (套,单元) -> [q]
    q_cur = None
    ans = {}               # (套,单元) -> {no: (letter, mode, text)}
    a_cur = None
    a_no = None
    a_buf = []
    zone = None
    cur_type = "A1"
    pend = None

    def flush_q():
        nonlocal pend
        if pend is not None:
            qunits.setdefault(q_cur, []).append(pend)
        pend = None

    def flush_a():
        nonlocal a_no, a_buf
        if a_no is not None:
            text = "\n".join(a_buf)
            letter, mode = extract_ans(text)
            ans.setdefault(a_cur, {})[a_no] = (letter, mode, text)
        a_no = None
        a_buf = []

    for ln in lines:
        s = ln.strip()
        if not s or PAGE_NO.match(s) or "www.yixucks" in s or "=== 第" in s:
            continue
        m = HEAD_Q.match(s)
        if m:
            flush_q(); flush_a()
            zone = "q"
            q_cur = (m.group(1), m.group(2))
            continue
        m = HEAD_A.match(s)
        if m:
            flush_q(); flush_a()
            zone = "a"
            a_cur = (m.group(1), m.group(2))
            a_no = None
            continue
        if re.match(r"^临考抢分考点", s):
            flush_q(); flush_a()
            zone = "cram"
            continue
        if zone == "q":
            tm = re.match(r"^([AB][1234]?)型题", s)
            if tm:
                cur_type = tm.group(1)
                continue
            qm = QNO.match(s)
            if qm:
                no = int(qm.group("no"))
                if no <= 500:
                    flush_q()
                    pend = {
                        "no": no, "type": cur_type, "题干": qm.group("body"),
                        "ops": [],
                        "图": any(k in s for k in ("图", "X线", "CT", "MRI", "心电", "超声")),
                    }
                continue
            if pend is not None:
                om = re.match(r"^([A-E])\s*[.．、:：]\s*(.*)$", s)
                if om and 0 < len(om.group(2)) <= 120:
                    pend["ops"].append(om.group(1) + "." + om.group(2))
                elif not pend["ops"]:
                    pend["题干"] += s[:120]
        elif zone == "a":
            am = re.match(r"^(\d{1,3})[.．、]\s*[A-K]", s) or \
                 re.match(r"^(\d{1,3})[.．、]\s*[A-K]*①", s)
            if am:
                flush_a()
                a_no = int(am.group(1))
                a_buf = [s]
            elif a_no is not None:
                a_buf.append(s)
    flush_q(); flush_a()
    return qunits, ans


def cram_summary():
    lines = open(SRC, encoding="utf-8").read().split("\n")
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^临考抢分考点", ln.strip()):
            start = i
            break
    if start is None:
        return ["(未提取到抢分考点区)"]
    out = []
    for ln in lines[start + 1:start + 500]:
        s = ln.strip()
        m = re.match(r"^([一二三四五六七八九十]+)、", s)
        if m and len(s) < 42:
            out.append("- " + s[:40])
    return out


def main():
    qunits, ans = parse()
    out = []
    out.append("# 模拟试卷汇总 · 贺银成《2026 国家临床执业医师资格考试全真模拟试卷及精析》")
    out.append("")
    out.append("> 来源:OCR `资料\\模拟试卷\\_txt\\国家临床执业医师资格考试全真模拟试卷及精析.txt`(364 页全量识别)。")
    out.append("> 结构:**3 套卷 × 4 单元 × 150 题 = 1800 题** + 每套答案及精析 + 书末「临考抢分考点」。")
    out.append("> ⚠️ 原书正确答案为**绿色印刷**,OCR 会丢色;本汇总答案提取自解析文本:")
    out.append("> ① 明确写出「答案为X/故答X/(X)/故选X」→ **可靠**;②「故不答A、B、C、D」排除式 → **推导**;")
    out.append("> ③ 无信号 → **待核对**(附解析首句,请回原书核对)。选项字母顺序 OCR 偶有错乱,以原书为准。")
    out.append("")

    total_q = 0
    ans_ok = ans_derive = ans_miss = 0
    linked = 0
    per_unit = {}

    ck = []  # 待核对清单行
    for key in sorted(qunits, key=lambda k: (CN.index(k[0]), CN.index(k[1]))):
        套, 单元 = key
        qs = sorted(qunits[key], key=lambda x: x["no"])
        qs = [q for q in qs if q["no"] > 0]   # 过滤 OCR 残片题号 0
        per_unit[key] = len(qs)
        out.append(f"## 卷{套} · 第{单元}单元 — {len(qs)} 题")
        a_map = ans.get(key, {})
        for q in qs:
            no = q["no"]
            total_q += 1
            letter, mode, text = a_map.get(no, (None, None, ""))
            if letter:
                if mode == "推导":
                    ans_derive += 1
                else:
                    ans_ok += 1
            else:
                ans_miss += 1
                te0 = text.replace("\n", "").strip()
                ck.append(f"| 卷{套}·第{单元}·{no} | {q['题干'][:46]} | {te0[:90]} |")
            qt = q["题干"] + " " + " ".join(q["ops"])
            card = link_card(qt)
            if card and card in CARDS:
                linked += 1
            out.append("")
            out.append(f"### 卷{套}·第{单元}单元·第{no}题 ({q['type']})")
            if q["图"]:
                out.append("- 🖼 题干含影像/图示 → 建议翻原书看图")
            igt = q["题干"] if len(q["题干"]) <= 120 else q["题干"][:120] + "…"
            out.append(f"- **题干**:{igt}")
            if q["ops"]:
                out.append(f"- **选项**:{' / '.join(q['ops'])}  *(OCR 顺序以原书为准)*")
            if letter:
                tag = "推导" if mode == "推导" else "可靠"
                out.append(f"- **答案**:{letter} ({tag})")
            else:
                out.append("- **答案**:⚠️ 待核对(解析未给出明确字母)")
            te = text.replace("\n", "").strip()
            if te:
                out.append(f"- **解析精要**:{te[:150]}" + ("…" if len(te) > 150 else ""))
            if card and card in CARDS:
                out.append(f"- **关联卡**:[{card}](../../../{CARDS[card].replace(chr(92), '/')})")
        out.append("")

    out.append("## 📊 结构检查")
    out.append("")
    out.append(f"- 题目总数:**{total_q}** (期望 1800 = 3×4×150;OCR 断行/重页可能略差异数)")
    out.append(f"- 答案 **可靠(显式)**:{ans_ok} · **推导(排除式)**:{ans_derive} · **待核对**:{ans_miss}")
    cover = total_q - ans_miss if total_q else 0
    out.append(f"- 答案可获得率(含推导):约 {cover / total_q * 100:.1f}%")
    out.append(f"- 关联正库卡:{linked} 题(其余为基础医学/人文/预防/法规题,不逐病建卡,属正常)")
    out.append("- 各单元题数:")
    for key in sorted(per_unit, key=lambda k: (CN.index(k[0]), CN.index(k[1]))):
        want = 150
        n = per_unit[key]
        flag = "" if n == want else f" ⚠️(偏差{want - n})"
        out.append(f"  - 卷{key[0]}·第{key[1]}单元:{n} 题{flag}")
    out.append("")

    out.append("## 📖 书末「临考抢分考点」章节索引")
    out.append("")
    out.extend(cram_summary())
    out.append("")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    # 答案核对清单(待核题)——便于对照原书回填
    CK = os.path.join(OUT_DIR, "答案核对清单.md")
    ck_out = ["# 答案核对清单（OCR 未提取到明确答案字母，请对照原书绿色答案回填）", "",
              "> 使用方法:对照原书答案及精析（正确答案为绿色）,在「参考答案」列写 A~E;",
              "> 之后可用脚本回填到《模拟试卷汇总.md》。",
              "",
              "| 题位 | 题干（≤46字） | 解析首句（≤90字） | 参考答案 |",
              "| --- | --- | --- | --- |"]
    ck_out.extend(ck)
    ck_out.append("")
    with open(CK, "w", encoding="utf-8") as f:
        f.write("\n".join(ck_out))

    print(f"[OK] wrote: {OUT}")
    print(f"[OK] wrote: {CK}")
    print(f"[OK] wrote: {OUT}")
    print(f"[OK] wrote: {CK}")
    print(f"题目={total_q} 可靠={ans_ok} 推导={ans_derive} 待核={ans_miss} 关联卡={linked}")


if __name__ == "__main__":
    main()