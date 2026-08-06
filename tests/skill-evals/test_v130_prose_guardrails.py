from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / ".agents" / "skills" / "writing-serial-fiction" / "references"


class V130ProseGuardrailTest(unittest.TestCase):
    def test_prose_contains_five_integrated_rules(self):
        text = (REFS / "prose-writing.md").read_text(encoding="utf-8")
        for phrase in (
            "最低充分证据",
            "限知限制信息来源，不限制人物主观经验",
            "未变化状态默认静默",
            "推进节点是因果检查点，不是段落",
            "固定结尾前后不得",
        ):
            self.assertIn(phrase, text)
        self.assertIn("不得写成“其余数值未变”", text)
        self.assertIn("提高证据等级", text)
        self.assertIn("安全关键或顺序依赖的技术步骤", text)

    def test_examples_cover_v130_failures(self):
        text = (REFS / "natural-prose-patterns.md").read_text(encoding="utf-8")
        for heading in (
            "证据足够后停止",
            "未核验只证明一次",
            "状态表信息不进入正文",
            "限知不等于摄像机",
            "固定结尾前不盘点未决事项",
        ):
            self.assertIn(heading, text)

    def test_skill_description_names_minimal_packet(self):
        text = (
            ROOT / ".agents" / "skills" / "writing-serial-fiction" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("正文最小包", text)

    def test_readonly_diagnosis_adds_signals_without_taking_lightcheck_authority(self):
        text = (REFS / "readonly-diagnosis.md").read_text(encoding="utf-8")
        for phrase in (
            "当前决定已经得到充分支持",
            "未变化数值",
            "多个未决状态",
            "可错的工作假设",
        ):
            self.assertIn(phrase, text)
        for forbidden in ("局部修补", "重写场景", "整章重写", "自动修正"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
