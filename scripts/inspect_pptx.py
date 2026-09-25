#!/usr/bin/env python3
"""Read slide order, text, notes and object counts without changing a PPTX."""

import argparse
import json
import posixpath
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def elements(root, name):
    return [element for element in root.iter() if local_name(element.tag) == name]


def read_xml(archive, part):
    try:
        return ET.fromstring(archive.read(part))
    except KeyError as exc:
        raise ValueError("Missing package part: " + part) from exc


def relationships(archive, part):
    directory, filename = posixpath.split(part)
    rel_part = posixpath.join(directory, "_rels", filename + ".rels")
    if rel_part not in archive.namelist():
        return {}
    result = {}
    for relation in read_xml(archive, rel_part):
        if relation.get("TargetMode") == "External":
            continue
        target = unquote(relation.get("Target", ""))
        if not target:
            raise ValueError("Empty relationship target: " + rel_part)
        resolved = posixpath.normpath(
            target.lstrip("/") if target.startswith("/")
            else posixpath.join(directory, target)
        )
        if resolved == ".." or resolved.startswith("../"):
            raise ValueError("Relationship target escapes package: " + rel_part)
        result[relation.get("Id")] = (relation.get("Type", ""), resolved)
    return result


def paragraphs(root):
    lines = []
    for paragraph in elements(root, "p"):
        fragments = []
        for element in paragraph.iter():
            if local_name(element.tag) == "t":
                fragments.append(element.text or "")
            elif local_name(element.tag) == "br":
                fragments.append("\n")
        text = "".join(fragments)
        if text.strip():
            lines.append(text)
    return lines


def inspect_pptx(path):
    with zipfile.ZipFile(path) as archive:
        part = "ppt/presentation.xml"
        presentation = read_xml(archive, part)
        rels = relationships(archive, part)
        sizes = elements(presentation, "sldSz")
        size = None
        if sizes:
            size = {
                "width_inches": round(int(sizes[0].get("cx")) / 914400, 4),
                "height_inches": round(int(sizes[0].get("cy")) / 914400, 4),
            }
        slides = []
        for slide_id in elements(presentation, "sldId"):
            # The relationship id is namespaced; the numeric slide id is not.
            rid = next((value for key, value in slide_id.attrib.items()
                        if key.startswith("{") and local_name(key) == "id"), None)
            relation = rels.get(rid)
            if relation is None or not relation[0].endswith("/slide"):
                raise ValueError("Missing or invalid slide relationship: " + str(rid))
            slide_part = relation[1]
            slide = read_xml(archive, slide_part)
            notes = []
            for relation_type, target in relationships(archive, slide_part).values():
                if relation_type.endswith("/notesSlide"):
                    notes_root = read_xml(archive, target)
                    for shape in elements(notes_root, "sp"):
                        placeholder_types = {p.get("type") for p in elements(shape, "ph")}
                        if placeholder_types & {"sldImg", "sldNum", "hdr", "ftr", "dt"}:
                            continue
                        notes.extend(paragraphs(shape))
            slides.append({
                "number": len(slides) + 1,
                "part": slide_part,
                "hidden": slide.get("show", "1").lower() in {"0", "false", "off"},
                "paragraphs": paragraphs(slide),
                "notes": notes,
                "objects": {
                    "shapes": len(elements(slide, "sp")),
                    "pictures": len(elements(slide, "pic")),
                    "tables": len(elements(slide, "tbl")),
                    "charts": len(elements(slide, "chart")),
                },
            })
        return {"slide_count": len(slides), "size": size, "slides": slides}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="Path to an unencrypted .pptx file")
    args = parser.parse_args()
    try:
        report = inspect_pptx(args.pptx)
    except (OSError, ValueError, TypeError, zipfile.BadZipFile,
            ET.ParseError, RuntimeError, NotImplementedError) as exc:
        print("PPTX inspection failed: " + str(exc), file=sys.stderr)
        return 1
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
