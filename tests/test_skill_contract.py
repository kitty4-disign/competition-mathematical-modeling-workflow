#!/usr/bin/env python3
"""Zero-dependency contract tests for the installable skill package."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "competition-mathematical-modeling-workflow"
SKILL_MD = SKILL / "SKILL.md"
EXPECTED_NAME = "competition-mathematical-modeling-workflow"
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def read_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"missing YAML frontmatter: {path}")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise AssertionError(f"unterminated YAML frontmatter: {path}")
    fields: dict[str, str] = {}
    for line in text[4:marker].splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"invalid frontmatter line: {line!r}")
        fields[key.strip()] = value.strip().strip('"')
    return fields, text[marker + 5 :]


class SkillContractTests(unittest.TestCase):
    def test_package_identity_and_frontmatter(self) -> None:
        self.assertEqual(SKILL.name, EXPECTED_NAME)
        self.assertTrue(SKILL_MD.is_file())
        fields, body = read_frontmatter(SKILL_MD)
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], EXPECTED_NAME)
        self.assertIn("Use when", fields["description"])
        self.assertIn("Do not use", fields["description"])
        self.assertLessEqual(len(body.splitlines()), 500)

    def test_single_discoverable_skill_and_ui_metadata(self) -> None:
        discovered = list(SKILL.rglob("SKILL.md"))
        self.assertEqual(discovered, [SKILL_MD])
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Competition Mathematical Modeling"', metadata)
        self.assertIn("$competition-mathematical-modeling-workflow", metadata)

    def test_core_invariants_are_explicit(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        for required in (
            "证据先于主张",
            "基线先于复杂度",
            "验证先于结果",
            "单一事实源",
            "变更向下游失效",
            "GateSpec",
            "completed",
            "invalidated",
        ):
            self.assertIn(required, text)
        self.assertNotIn("至少完成基线比较", text)
        self.assertNotIn("templates/agent-loop-state", text)
        self.assertNotIn("task-method-result-map", text)

    def test_all_relative_markdown_links_resolve(self) -> None:
        broken: list[str] = []
        for markdown in SKILL.rglob("*.md"):
            for raw_target in LINK_RE.findall(markdown.read_text(encoding="utf-8")):
                target = raw_target.strip().strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_part = unquote(target.split("#", 1)[0])
                if not path_part:
                    continue
                resolved = (markdown.parent / path_part).resolve()
                if not resolved.exists():
                    broken.append(f"{markdown.relative_to(REPO)} -> {target}")
        self.assertEqual(broken, [], "broken relative links:\n" + "\n".join(broken))

    def test_markdown_fences_and_long_reference_navigation(self) -> None:
        failures: list[str] = []
        for markdown in SKILL.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8")
            if text.count("```") % 2:
                failures.append(f"unbalanced fence: {markdown.relative_to(REPO)}")
        for reference in (SKILL / "references").glob("*.md"):
            lines = reference.read_text(encoding="utf-8").splitlines()
            if len(lines) > 100 and "## 目录" not in lines:
                failures.append(f"long reference lacks TOC: {reference.relative_to(REPO)}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_vendor_is_outside_installable_skill(self) -> None:
        self.assertFalse((SKILL / "third_party").exists())
        self.assertFalse((SKILL / "vendor").exists())
        self.assertTrue((REPO / "vendor" / "mathhub" / "NOTICE.md").is_file())

    def test_checked_in_json_is_strict(self) -> None:
        for result in (REPO / "tests" / "results").glob("*.json"):
            with self.subTest(result=result.name):
                json.loads(result.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
