"""Supplement the original content validator with career-document link checks."""

from pathlib import Path
import re

from tools.course import ROOT, catalog, manifest


def validate() -> list[str]:
    errors: list[str] = []
    chapters = catalog()
    numbers = [item["number"] for item in chapters]
    if numbers != list(range(1, len(chapters) + 1)):
        errors.append("chapter numbers must be consecutive and ordered")
    for chapter in chapters:
        entry = ROOT / chapter["entry"]
        if not entry.is_file():
            errors.append(f"missing chapter entry: {entry}")
            continue
        if any(n >= chapter["number"] or n not in numbers for n in chapter["prerequisites"]):
            errors.append(f"invalid prerequisites: {entry}")
        data = manifest(chapter)
        if data["chapter_id"] != chapter["chapter_id"]:
            errors.append(f"inconsistent chapter ID: {entry}")
        paths = [example["source"] for example in data["examples"]]
        paths += [exercise["entry"] for exercise in data["exercises"]]
        for relative in paths:
            if not (ROOT / relative).is_file():
                errors.append(f"missing manifest target: {relative}")
        number = chapter["number"]
        if len(list((ROOT / "solutions").glob(f"ch{number:02d}_*.py"))) != 1:
            errors.append(f"CH{number:02d}: missing or ambiguous reference answer")
    markdown = [ROOT / "README.md", ROOT / "INDEX.md"]
    for directory in ("chapters", "career", "capstone"):
        markdown.extend((ROOT / directory).rglob("*.md"))
    for file in markdown:
        if not file.is_file():
            errors.append(f"missing document: {file}")
            continue
        content = file.read_text(encoding="utf-8")
        for destination in re.findall(r"\]\(([^)]+)\)", content):
            if destination.startswith(("https://", "http://", "#", "mailto:")):
                continue
            relative = destination.split("#", 1)[0]
            if relative and not (file.parent / Path(relative)).exists():
                errors.append(f"broken link in {file.relative_to(ROOT)}: {relative}")
    return errors


def main() -> int:
    errors = validate()
    for error in errors:
        print(error)
    print(f"content: {'FAILED' if errors else 'passed'} ({len(catalog())} chapters)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
