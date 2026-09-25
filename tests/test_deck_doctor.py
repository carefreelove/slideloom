import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deck_doctor import diagnose, markdown
from test_inspect_pptx import fixture

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deck_doctor.py"


def slide(number=1, text="产品交付进度", hidden=False, pictures=0):
    return {"number": number, "paragraphs": [text] if text else [], "hidden": hidden,
            "notes": [], "objects": {"pictures": pictures, "shapes": 1, "charts": 0, "tables": 0}}


def deck(*slides):
    return {"slide_count": len(slides), "slides": list(slides)}


class DoctorTests(unittest.TestCase):
    def test_clean_deck_has_no_findings(self):
        self.assertEqual(diagnose(deck(slide()), 1)["findings"], [])

    def test_exact_page_count_and_empty_deck(self):
        self.assertEqual(diagnose(deck(slide()), 3)["summary"]["error"], 1)
        self.assertEqual(diagnose(deck())["findings"][0]["code"], "empty-deck")

    def test_density_threshold_is_configurable(self):
        source = deck(slide(text="中" * 321))
        self.assertEqual(diagnose(source)["findings"][0]["code"], "text-density")
        self.assertEqual(diagnose(source, max_chars=321)["findings"], [])

    def test_placeholder_word_boundaries(self):
        self.assertEqual(diagnose(deck(slide(text="TODO: 数据待补充")))["summary"]["warning"], 1)
        self.assertEqual(diagnose(deck(slide(text="TODOLIST 这个产品名")))["findings"], [])

    def test_image_page_is_candidate_not_editability_verdict(self):
        report = diagnose(deck(slide(text="", pictures=1)))
        self.assertEqual(report["findings"][0]["code"], "image-only-candidate")
        self.assertEqual(report["summary"]["error"], 0)

    def test_hidden_and_repeated_opening_are_informational(self):
        report = diagnose(deck(slide(1), slide(2), slide(3, hidden=True)))
        self.assertEqual(report["summary"], {"error": 0, "warning": 0, "info": 3})
        self.assertEqual(report["hidden_slide_count"], 1)

    def test_markdown_does_not_render_injected_html(self):
        report = diagnose(deck(slide(1, "<script>TODO</script>"), slide(2, "<script>TODO</script>")))
        self.assertNotIn("<script>", markdown(report))

    def test_bad_parameters(self):
        with self.assertRaises(ValueError):
            diagnose(deck(slide()), max_chars=0)
        with self.assertRaises(ValueError):
            diagnose(deck(slide()), expected_slides=-1)

    def test_cli_reports_failure_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deck.pptx"
            fixture(path)
            before = path.read_bytes()
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), "--expected-slides", "3", "--format", "json"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads(run.stdout)["summary"]["error"], 1)
            self.assertEqual(path.read_bytes(), before)
            strict = subprocess.run([sys.executable, str(SCRIPT), str(path), "--max-chars", "1", "--strict"], capture_output=True, text=True)
            self.assertEqual(strict.returncode, 1)
            missing = subprocess.run([sys.executable, str(SCRIPT), str(path.with_name("missing.pptx"))], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(missing.stdout, "")
