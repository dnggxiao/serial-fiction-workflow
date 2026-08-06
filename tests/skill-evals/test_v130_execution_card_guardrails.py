from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class V130ExecutionCardGuardrailTest(unittest.TestCase):
    def test_template_uses_weight_and_viewpoint_pressure(self):
        text = (ROOT / "模板" / "场景执行卡模板.md").read_text(encoding="utf-8")
        self.assertIn("篇幅权重：短／中／长", text)
        self.assertIn("- 视角偏压：", text)
        self.assertNotIn("建议字数", text)
        self.assertNotIn("- 必须呈现：", text)

    def test_planning_contract_does_not_sum_scene_budgets(self):
        text = (
            ROOT
            / ".agents"
            / "skills"
            / "writing-serial-fiction"
            / "references"
            / "chapter-planning.md"
        ).read_text(encoding="utf-8")
        self.assertIn("推进节点是因果检查点，不是段落", text)
        self.assertNotIn("各场之和必须等于目标正文字数", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
