"""Audit the per-card clinical coverage ledger; it does not verify medical accuracy."""
from __future__ import annotations

import csv
import re
from pathlib import Path

SYSTEMS = (
    "传染病", "儿科", "风湿免疫性疾病", "呼吸系统", "泌尿系统",
    "内分泌系统", "女性生殖系统", "其他", "神经精神系统",
    "消化系统", "心血管系统", "性传播疾病", "血液系统", "运动系统",
)
FIELDS = ("path", "system", "card_type", "work_status", "source_status", "reviewed_on", "notes")
CARD_TYPES = {"disease", "combined", "non_disease"}
STATUSES = {"pending", "drafted", "source_checked", "needs_review"}
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")
LINK_RE = re.compile(r"https://[^)\s>]+")


def card_paths(root: Path) -> set[str]:
    base = root / "考试" / "03_临床医学综合"
    return {
        path.relative_to(root).as_posix()
        for system in SYSTEMS
        for path in (base / system).glob("*.md")
        if path.name.lower() != "readme.md"
    }


def audit(root: Path) -> list[str]:
    issues: list[str] = []
    manifest = root / "docs" / "clinical-card-coverage.tsv"
    if not manifest.is_file():
        return [f"台账不存在：{manifest}"]
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != list(FIELDS):
            return [f"台账列名不符：需要 {','.join(FIELDS)}"]
        rows = list(reader)
    seen: set[str] = set()
    for index, row in enumerate(rows, 2):
        if None in row or any(row.get(field) is None for field in FIELDS):
            issues.append(f"第 {index} 行列数不符")
            continue
        path = row["path"]
        if path in seen:
            issues.append(f"第 {index} 行重复路径：{path}")
        seen.add(path)
        if row["card_type"] not in CARD_TYPES or row["work_status"] not in STATUSES:
            issues.append(f"第 {index} 行类型或状态无效：{path}")
            continue
        if row["system"] not in SYSTEMS or not path.startswith(f"考试/03_临床医学综合/{row['system']}/"):
            issues.append(f"第 {index} 行系统与路径不符：{path}")
        source = root / path
        if not source.is_file():
            issues.append(f"第 {index} 行文件不存在：{path}")
            continue
        if row["work_status"] == "pending":
            continue
        body = source.read_text(encoding="utf-8-sig")
        if row["card_type"] == "non_disease":
            headings = ("初评与危险信号", "必要检查与分流", "关键鉴别诊断", "核查来源")
        else:
            headings = ("首诊辅助检查", "确诊依据与参考标准", "关键鉴别诊断", "核查来源")
        for heading in headings:
            if f"## {heading}" not in body:
                issues.append(f"缺栏目 {heading}：{path}")
        if row["work_status"] == "source_checked":
            section = body.split("## 核查来源", 1)[-1]
            if not LINK_RE.search(section) or not DATE_RE.search(section) or not DATE_RE.fullmatch(row["reviewed_on"]):
                issues.append(f"来源链接或核查日期不全：{path}")
    actual = card_paths(root)
    for path in sorted(actual - seen):
        issues.append(f"漏卡：{path}")
    for path in sorted(seen - actual):
        issues.append(f"台账多余路径：{path}")
    return issues


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    issues = audit(root)
    if issues:
        for issue in issues:
            print(issue)
        print(f"发现 {len(issues)} 个问题")
        return 1
    print(f"覆盖审计通过：{len(card_paths(root))} 张卡")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
