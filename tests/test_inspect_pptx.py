"""Minimal OOXML fixtures test extraction, not PowerPoint compatibility."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inspect_pptx.py"
SPEC = importlib.util.spec_from_file_location("inspect_pptx", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture(path, strict=False, broken=False):
    base = "http://purl.oclc.org/ooxml" if strict else "http://schemas.openxmlformats.org"
    suffix = "/main" if strict else "/2006/main"
    p = base + "/presentationml" + suffix
    a = base + "/drawingml" + suffix
    r = base + ("/officeDocument/relationships" if strict else "/officeDocument/2006/relationships")
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    parts = {
        "ppt/presentation.xml": f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst><p:sldId id="256" r:id="r2"/><p:sldId id="257" r:id="r1"/></p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/></p:presentation>',
        "ppt/_rels/presentation.xml.rels": f'<Relationships xmlns="{rel_ns}"><Relationship Id="r1" Type="{r}/slide" Target="slides/slide1.xml"/><Relationship Id="r2" Type="{r}/slide" Target="/ppt/slides/slide2.xml"/></Relationships>',
        "ppt/slides/slide1.xml": f'<p:sld xmlns:p="{p}" xmlns:a="{a}" show="0"><p:sp><a:p><a:r><a:t>第二页</a:t></a:r></a:p></p:sp></p:sld>',
        "ppt/slides/slide2.xml": f'<p:sld xmlns:p="{p}" xmlns:a="{a}"><p:sp><a:p><a:r><a:t>季度</a:t></a:r><a:r><a:t>汇报</a:t></a:r><a:br/><a:r><a:t>增长 20%</a:t></a:r></a:p></p:sp><p:pic/><a:tbl/><c:chart xmlns:c="{a}/chart"/></p:sld>',
        "ppt/slides/_rels/slide2.xml.rels": f'<Relationships xmlns="{rel_ns}"><Relationship Id="n1" Type="{r}/notesSlide" Target="../notesSlides/notesSlide1.xml"/><Relationship Id="link" Type="{r}/hyperlink" Target="https://example.com" TargetMode="External"/></Relationships>',
        "ppt/notesSlides/notesSlide1.xml": f'<p:notes xmlns:p="{p}" xmlns:a="{a}"><p:sp><p:ph type="body"/><a:p><a:r><a:t>来源：用户资料</a:t></a:r></a:p></p:sp><p:sp><p:ph type="sldNum"/><a:p><a:r><a:t>1</a:t></a:r></a:p></p:sp></p:notes>',
    }
    if broken:
        del parts["ppt/slides/slide2.xml"]
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in parts.items():
            archive.writestr(name, content)


class InspectTests(unittest.TestCase):
    def test_order_text_notes_and_objects(self):
        for strict in (False, True):
            with self.subTest(strict=strict), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "deck.pptx"
                fixture(path, strict=strict)
                original = path.read_bytes()
                report = MODULE.inspect_pptx(path)
                self.assertEqual(report["slide_count"], 2)
                self.assertEqual(report["slides"][0]["part"], "ppt/slides/slide2.xml")
                self.assertEqual(report["slides"][0]["paragraphs"], ["季度汇报\n增长 20%"])
                self.assertEqual(report["slides"][0]["notes"], ["来源：用户资料"])
                self.assertEqual(report["slides"][0]["objects"], {"shapes": 1, "pictures": 1, "tables": 1, "charts": 1})
                self.assertTrue(report["slides"][1]["hidden"])
                self.assertEqual(report["size"]["height_inches"], 7.5)
                self.assertEqual(path.read_bytes(), original)

    def test_missing_part_fails_clearly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.pptx"
            fixture(path, broken=True)
            with self.assertRaisesRegex(ValueError, "Missing package part"):
                MODULE.inspect_pptx(path)

    def test_invalid_input_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.pptx"
            path.write_text("Not a ZIP file", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertIn("PPTX inspection failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
