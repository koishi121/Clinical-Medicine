import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_clinical_cards import audit

HEADER = "path\tsystem\tcard_type\twork_status\tsource_status\treviewed_on\tnotes\n"
CARD = "# 示例\n\n## 首诊辅助检查\n- 实验室：按病情。\n- 影像/其他：按病情。\n\n## 确诊依据与参考标准\n无单一金标准。\n\n## 关键鉴别诊断\n- 其他疾病。\n\n## 核查来源\n- [原始资料](https://example.org/source)（2024；核查：2026-10-20）。\n"
ADAPTED = "# 技能\n\n## 初评与危险信号\n- 稳定。\n\n## 必要检查与分流\n- 评估。\n\n## 关键鉴别诊断\n- 其他。\n\n## 核查来源\n- [原始资料](https://example.org/source)（2024；核查：2026-10-20）。\n"

class AuditTests(unittest.TestCase):
    def setup_root(self, root, card_name="示例.md", content=CARD):
        folder = root / "考试/03_临床医学综合/消化系统"
        folder.mkdir(parents=True)
        (folder / card_name).write_text(content, encoding="utf-8")
        (root / "docs").mkdir()
        return folder

    def row(self, card_name="示例.md", card_type="disease", status="pending"):
        return f"考试/03_临床医学综合/消化系统/{card_name}\t消化系统\t{card_type}\t{status}\tpending\t\t\n"

    def manifest(self, root, rows):
        (root / "docs/clinical-card-coverage.tsv").write_text(HEADER + rows, encoding="utf-8")

    def test_unlisted_new_card_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root)
            self.manifest(root, "")
            self.assertTrue(any("漏卡" in issue for issue in audit(root)))

    def test_duplicate_manifest_path_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root)
            self.manifest(root, self.row() + self.row())
            self.assertTrue(any("重复" in issue for issue in audit(root)))

    def test_non_disease_adapted_sections_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, content=ADAPTED)
            self.manifest(root, self.row(card_type="non_disease", status="drafted"))
            self.assertEqual(audit(root), [])

    def test_source_checked_needs_source_link_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, content=CARD.replace("https://example.org/source", "无链接").replace("2026-10-20", "未核"))
            self.manifest(root, self.row(status="source_checked"))
            self.assertTrue(any("来源" in issue for issue in audit(root)))

if __name__ == "__main__":
    unittest.main()
