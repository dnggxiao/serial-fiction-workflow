from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class V130LightcheckGuardrailTest(unittest.TestCase):
    def test_lightcheck_has_seventh_category_and_boundaries(self):
        text = (ROOT / "工作流" / "03_轻检.md").read_text(encoding="utf-8")
        for phrase in (
            "只检查七类明确问题",
            "叙事自证过度／状态表渗漏",
            "人物已经拥有足以采取当前动作的证据",
            "其他状态未变",
            "固定结尾前集中回收两个以上未决状态",
            "同一根因只报告一项",
        ):
            self.assertIn(phrase, text)

    def test_necessary_technical_evidence_is_exempt(self):
        text = (ROOT / "工作流" / "03_轻检.md").read_text(encoding="utf-8")
        for phrase in (
            "提高证据等级",
            "改变下一步动作",
            "一次必要技术限定",
            "实际变化",
            "固定结尾中的否定动作",
        ):
            self.assertIn(phrase, text)

    def test_repair_keeps_one_round_and_prefers_deletion(self):
        text = (ROOT / "工作流" / "04_修正.md").read_text(encoding="utf-8")
        self.assertIn("叙事自证过度", text)
        self.assertIn("删除、合并和缩短", text)
        self.assertIn("自动修正次数上限为 1", text)

    def test_report_template_exposes_new_type(self):
        text = (ROOT / "模板" / "轻检报告模板.md").read_text(encoding="utf-8")
        self.assertIn("叙事自证过度／状态表渗漏", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
