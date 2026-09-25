import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from inspect_pptx import inspect_pptx
from deck_doctor import diagnose


class ShowcaseTests(unittest.TestCase):
    def test_real_showcase_has_three_native_charts_and_readable_text(self):
        deck = inspect_pptx(ROOT / "examples" / "style-showcase.pptx")
        self.assertEqual(deck["slide_count"], 3)
        for slide in deck["slides"]:
            self.assertEqual(slide["objects"]["charts"], 1)
            self.assertGreater(len(slide["paragraphs"]), 3)
            self.assertIn("虚构数据", "".join(slide["notes"]))
        self.assertEqual(diagnose(deck, expected_slides=3)["summary"],
                         {"error": 0, "warning": 0, "info": 0})

    def test_preset_text_colors_have_readable_contrast(self):
        def luminance(hex_color):
            rgb = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
            return sum(x * weight for x, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
        for path in (ROOT / "presets").glob("*.json"):
            colors = json.loads(path.read_text(encoding="utf-8"))["colors"]
            for role in ("foreground", "muted", "accent"):
                with self.subTest(preset=path.stem, role=role):
                    a, b = sorted([luminance(colors[role]), luminance(colors["background"])])
                    self.assertGreaterEqual((b + 0.05) / (a + 0.05), 4.5)
