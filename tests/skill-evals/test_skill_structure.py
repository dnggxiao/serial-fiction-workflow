from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "writing-serial-fiction"
REQUIRED = {
    "SKILL.md",
    "LICENSE",
    "NOTICE.md",
    "THIRD_PARTY_NOTICES.md",
    "agents/openai.yaml",
    "references/fanqie-cn-profile.md",
    "references/technique-selector.md",
    "references/chapter-planning.md",
    "references/prose-writing.md",
    "references/natural-prose-patterns.md",
    "references/readonly-diagnosis.md",
}
MODES = {"chapter-planning", "prose-writing", "readonly-diagnosis"}


class SkillStructureTest(unittest.TestCase):
    def _require_skill(self):
        self.assertTrue(SKILL.is_dir(), "skill directory missing")

    def test_required_files_exist_without_extra_skill_docs(self):
        self._require_skill()
        actual = {
            path.relative_to(SKILL).as_posix()
            for path in SKILL.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, REQUIRED)
        self.assertFalse((SKILL / "scripts").exists())
        self.assertFalse((SKILL / "assets").exists())

    def test_frontmatter_and_size(self):
        self._require_skill()
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match, "frontmatter missing")
        keys = {
            line.split(":", 1)[0].strip()
            for line in match.group(1).splitlines()
            if ":" in line
        }
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: writing-serial-fiction", match.group(1))
        description = next(
            line.split(":", 1)[1].strip()
            for line in match.group(1).splitlines()
            if line.startswith("description:")
        )
        self.assertTrue(description.lstrip('\"').startswith("Use when"))
        cjk_count = len(re.findall(r"[\u3400-\u4DBF\u4E00-\u9FFF]", text))
        english_word_count = len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text))
        self.assertLessEqual(cjk_count, 1500)
        self.assertLessEqual(english_word_count, 500)

    def test_modes_and_progressive_disclosure(self):
        self._require_skill()
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for mode in MODES:
            self.assertIn(mode, text)
        for reference in REQUIRED:
            if reference.startswith("references/"):
                self.assertIn(reference, text)
        nested_refs = [
            path for path in (SKILL / "references").rglob("*")
            if path.is_file() and path.parent != SKILL / "references"
        ]
        self.assertEqual(nested_refs, [])

    def test_explicit_invocation_policy(self):
        self._require_skill()
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", text)
        self.assertIn("$writing-serial-fiction", text)

    def test_error_contracts_and_mode_specific_shapes(self):
        main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("INPUT_ERROR: multiple_modes", main)
        self.assertIn("INPUT_ERROR: mode", main)
        self.assertIn("INPUT_ERROR: missing=<字段1>,<字段2>", main)
        self.assertIn("BLOCKED: <最短冲突说明>", main)

        planning = (
            SKILL / "references" / "chapter-planning.md"
        ).read_text(encoding="utf-8")
        self.assertIn("每场 `推进节点` 必须包含 3～5 个按顺序编号的节点", planning)
        self.assertIn("篇幅权重", planning)
        success_shape = planning.split("## 成功输出形状", 1)[1]
        example = re.search(r"```markdown\s*(.*?)```", success_shape, re.S)
        self.assertIsNotNone(example, "planning success-shape example missing")
        fields = re.findall(r"^- ([^：\r\n]+)：", example.group(1), re.M)
        self.assertEqual(
            fields,
            [
                "起始刺激",
                "眼前动作",
                "推进节点",
                "视角偏压",
                "场景结果",
                "衔接方式",
            ],
        )
        for field in (
            "起始刺激",
            "眼前动作",
            "推进节点",
            "视角偏压",
            "场景结果",
            "衔接方式",
        ):
            self.assertIn(f"- {field}：", planning)
        for forbidden in ("建议字数", "人物即时目标", "必须呈现"):
            self.assertNotIn(forbidden, planning)

        prose = (SKILL / "references" / "prose-writing.md").read_text(
            encoding="utf-8"
        )
        required_inputs = [
            "1. 本章正文最小包；",
            "2. 本章场景执行卡。",
        ]
        positions = [prose.index(item) for item in required_inputs]
        self.assertEqual(positions, sorted(positions))
        for forbidden_input in (
            "3. 章节标题；",
            "3. 目标字数；",
            "3. 停止条件。",
        ):
            self.assertNotIn(forbidden_input, prose)
        self.assertIn("# <章节标题>", prose)
        self.assertIn("<小说正文>", prose)

        diagnosis = (
            SKILL / "references" / "readonly-diagnosis.md"
        ).read_text(encoding="utf-8")
        for label in (
            "位置：",
            "类型：",
            "可观察证据：",
            "对阅读推进的影响：",
            "最小调整方向：",
        ):
            self.assertIn(label, diagnosis)

    def test_skill_is_portable(self):
        self._require_skill()
        for path in SKILL.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            text_without_urls = re.sub(r"https?://\S+", "", text)
            self.assertNotRegex(text_without_urls, r"[A-Za-z]:[\\/]")
            self.assertNotRegex(text, r"(?:工作区|正文)[\\/]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
