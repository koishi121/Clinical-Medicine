import sys
import tempfile
import unittest
import re
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import make_reader  # noqa: E402


class ReaderCollectionTests(unittest.TestCase):
    def write(self, root: Path, relpath: str, content: str = "# Test\n") -> None:
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_collects_nested_exam_and_residency_markdown_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = {
                "考试/05_实践技能/内科/README.md",
                "考试/05_实践技能/内科/操作/腰穿.md",
                "规培/内科/README.md",
                "规培/内科/消化内科/README.md",
                "规培/内科/消化内科/用药速查/抑酸药.md",
            }
            for relpath in expected:
                self.write(root, relpath)

            idmap = {}
            entries = make_reader.collect(str(root), idmap)
            indexed_paths = [entry.path for entry in entries]

            for relpath in expected:
                with self.subTest(path=relpath):
                    self.assertEqual(indexed_paths.count(relpath), 1)

    def test_excludes_all_materials_from_entries_and_built_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "考试/05_实践技能/README.md",
                "# Skill\n\n题目来源：`资料/secret.md`\n",
            )
            self.write(root, "资料/private-material.md", "UNIQUE_LOCAL_MATERIAL_SENTINEL")
            self.write(
                root,
                "tools/local_paths.py",
                'BOOK = r"D:\\Clinical Medicine\\资料\\教材\\book.txt"\n',
            )

            entries = make_reader.collect(str(root), {})
            page = make_reader.build(str(root))

            self.assertFalse(any(entry.path.startswith("资料/") for entry in entries))
            self.assertNotIn("资料/", page)
            self.assertNotIn("资料\\", page)
            self.assertNotIn("D:\\Clinical Medicine", page)
            self.assertNotIn("📂 资料", page)
            self.assertNotIn("UNIQUE_LOCAL_MATERIAL_SENTINEL", page)
            self.assertIn("本地资料路径已省略", page)

    def test_builds_when_exam_and_residency_sections_are_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "考试").mkdir()
            (root / "规培").mkdir()

            page = make_reader.build(str(root))

            self.assertIn("<html", page)
            self.assertIn('id="viewer"', page)
            self.assertNotIn("考试·备考", page)
            self.assertNotIn("规培·内科轮转", page)
            self.assertNotIn("文档·决策", page)
            self.assertIn('<div id="ph">', page)

    def test_external_link_escapes_ampersands_only_once(self):
        rendered = make_reader.inline(
            "[A & B](https://example.test/read?a=1&b=2)", {}, "README.md"
        )

        self.assertIn('href="https://example.test/read?a=1&amp;b=2"', rendered)
        self.assertIn('>A &amp; B</a>', rendered)
        self.assertNotIn('&amp;amp;', rendered)

    def test_build_includes_accessible_navigation_search_checkboxes_and_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "考试/05_实践技能/检查表.md",
                "# 检查表\n\n- [ ] 未完成\n- [x] 已完成\n\n| 项目 | 内容 |\n| --- | --- |\n| A | 宽表格 |\n",
            )

            page = make_reader.build(str(root))

            self.assertIn('href="#viewer"', page)
            self.assertIn('<nav id="nav" aria-label=', page)
            self.assertIn('<main id="viewer" tabindex="-1">', page)
            self.assertIn('aria-current="page"', page)
            self.assertIn('id="res" role="status" aria-live="polite"', page)
            self.assertIn('aria-label="未完成"', page)
            self.assertIn('aria-label="已完成"', page)
            self.assertIn('class="table-wrap"', page)
            self.assertNotIn("autofocus", page)

    def test_navigation_contains_each_indexed_entry_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "考试/03_临床医学综合/消化系统/消化病.md",
                "> 大纲要求: 🔷掌握\n# 消化病\n",
            )
            self.write(root, "考试/05_实践技能/内科/README.md")

            entries = make_reader.collect(str(root), {})
            page = make_reader.build(str(root))
            nav_ids = re.findall(r'<a class="it" data-id="(\d+)"', page)

            self.assertEqual(len(nav_ids), len(entries))
            self.assertEqual(len(nav_ids), len(set(nav_ids)))

    def test_navigation_links_are_keyboard_focusable_and_article_clicks_do_not_intercept_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "规培/内科/README.md")
            page = make_reader.build(str(root))

            self.assertRegex(page, r'<a class="it" data-id="\d+"[^>]*href="#d-\d+"')
            self.assertIn("document.querySelectorAll('a[data-id]')", page)
            self.assertNotIn("document.querySelectorAll('[data-id]')", page)

    def test_relative_markdown_links_resolve_against_source_directory_and_full_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "规培/内科/README.md",
                "[科室](内科/README.md) [实训](内科/接诊.md) [重名错误](其他/README.md)",
            )
            self.write(root, "规培/内科/内科/README.md")
            self.write(root, "规培/内科/内科/接诊.md")
            self.write(root, "规培/内科/其他/README.md")

            idmap = {}
            entries = make_reader.collect(str(root), idmap)
            page = make_reader.build(str(root))
            hub_id = next(entry.id for entry in entries if entry.path == "规培/内科/README.md")
            hub_article = re.search(rf'<article class="doc" id="d-{hub_id}".*?</article>', page, re.S).group(0)
            link_ids = re.findall(r'<a href="#" data-id="(\d+)">', hub_article)
            expected_ids = [idmap[path] for path in (
                "规培/内科/内科/README.md",
                "规培/内科/内科/接诊.md",
                "规培/内科/其他/README.md",
            )]

            self.assertEqual(link_ids, [str(eid) for eid in expected_ids])
            self.assertNotIn('class="muted-link"', hub_article)

    def test_root_exam_and_residency_markdown_have_navigation_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "考试/README.md")
            self.write(root, "规培/README.md")

            page = make_reader.build(str(root))
            nav_paths = re.findall(r'<span class="sub">([^<]+)</span>', page)

            self.assertIn("考试/README.md", nav_paths)
            self.assertIn("规培/README.md", nav_paths)

    def test_portable_reader_has_mobile_navigation_and_reading_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "规培/内科/README.md", "# 轮转总览\n")

            page = make_reader.build(str(root))

            self.assertIn('id="menuToggle" aria-controls="nav" aria-expanded="false"', page)
            self.assertIn('id="navClose"', page)
            self.assertIn('id="fontInc"', page)
            self.assertIn('id="fontDec"', page)
            self.assertIn('<details class="grp"', page)
            self.assertIn('aria-label="关闭目录"', page)
            self.assertNotIn('<script src=', page)
            self.assertNotIn('<link rel="stylesheet"', page)


if __name__ == "__main__":
    unittest.main()
