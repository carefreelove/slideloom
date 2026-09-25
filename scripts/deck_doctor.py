#!/usr/bin/env python3
"""Actionable, offline PPTX checks. Visual inspection is still required."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

from inspect_pptx import inspect_pptx

PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|lorem ipsum)\b|待补充|待填写|单击此处|click to (?:edit|add)", re.I)


def diagnose(deck, expected_slides=None, max_chars=320):
    if expected_slides is not None and expected_slides < 1:
        raise ValueError("expected_slides must be positive")
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    findings = []

    def add(code, severity, slide, evidence, suggestion):
        findings.append(dict(code=code, severity=severity, slide=slide,
                             evidence=evidence, suggestion=suggestion))

    if deck["slide_count"] == 0:
        add("empty-deck", "error", None, "演示文稿没有页面", "确认输入文件和导出结果。")
    if expected_slides is not None and deck["slide_count"] != expected_slides:
        add("slide-count", "error", None,
            f"实际 {deck['slide_count']} 页，要求 {expected_slides} 页（均含隐藏页）",
            "核对封面、结束页和隐藏页，不自动删页。")
    first_paragraphs = Counter(
        slide["paragraphs"][0].strip() for slide in deck["slides"]
        if slide["paragraphs"] and not slide["hidden"]
    )
    for slide in deck["slides"]:
        number = slide["number"]
        text = "\n".join(slide["paragraphs"])
        if slide["hidden"]:
            add("hidden-slide", "info", number, "页面设置为隐藏", "确认这是预期行为，放映通常不会展示该页。")
        match = PLACEHOLDER.search(text)
        if match:
            add("placeholder", "warning", number, f"检测到候选占位文本：{match.group(0)}",
                "若属于未完成内容，请补充或删除；若是教学示例，请保留。")
        char_count = len(re.sub(r"\s", "", text))
        if char_count > max_chars:
            add("text-density", "warning", number, f"抽取到 {char_count} 个非空白字符，阈值 {max_chars}",
                "优先精简或分层呈现；结合语言、版式与观看距离判断，字符数不代表溢出。")
        objects = slide["objects"]
        if not text.strip() and objects["pictures"] and not (objects["tables"] or objects["charts"]):
            add("image-only-candidate", "warning", number, "有图片，但没有抽取到普通文本或原生表格、图表",
                "确认该页是有意的图片页；如要求编辑其中的文字或图表，请检查原始对象。")
        if slide["paragraphs"] and not slide["hidden"]:
            first = slide["paragraphs"][0].strip()
            if first_paragraphs[first] > 1:
                add("repeated-opening", "info", number, f"多个可见页面首段相同：{first[:80]}",
                    "核对是否误复制了页面；重复品牌文字也会触发提示，不能据此判定标题重复。")
    counts = {level: sum(item["severity"] == level for item in findings)
              for level in ("error", "warning", "info")}
    return {
        "schema_version": 1,
        "slide_count": deck["slide_count"],
        "hidden_slide_count": sum(slide["hidden"] for slide in deck["slides"]),
        "rules": {"expected_slides": expected_slides, "max_chars": max_chars},
        "summary": counts,
        "findings": findings,
        "limitations": "仅读取 OOXML；不验证渲染、视觉阅读顺序、文本溢出、事实正确性或所有对象的可编辑性。",
    }


def markdown(report):
    counts = report["summary"]
    lines = ["# Deck Doctor", "", f"页面：{report['slide_count']} · 隐藏页：{report['hidden_slide_count']}",
             f"错误：{counts['error']} · 提醒：{counts['warning']} · 信息：{counts['info']}", ""]
    if not report["findings"]:
        lines.append("当前规则未发现问题。仍需逐页渲染检查。")
    for item in report["findings"]:
        location = f"第 {item['slide']} 页" if item["slide"] is not None else "全稿"
        # Escape user text before placing it in a Markdown report.
        evidence = re.sub(r"([\\`*_{}\[\]()<>#!|])", r"\\\1", item["evidence"]).replace("\n", " ")
        lines.extend([f"## {location} · {item['code']} · {item['severity']}", "",
                      evidence, "", item["suggestion"], ""])
    lines.extend(["", report["limitations"], ""])
    return "\n".join(lines)


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--expected-slides", type=positive)
    parser.add_argument("--max-chars", type=positive, default=320)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--strict", action="store_true", help="Exit 1 for warnings as well as errors")
    args = parser.parse_args(argv)
    try:
        report = diagnose(inspect_pptx(args.pptx), args.expected_slides, args.max_chars)
    except (OSError, ValueError, TypeError, zipfile.BadZipFile,
            ET.ParseError, RuntimeError, NotImplementedError) as exc:
        print("Deck Doctor could not read the file: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown(report))
    return 1 if report["summary"]["error"] or (args.strict and report["summary"]["warning"]) else 0


if __name__ == "__main__":
    sys.exit(main())
