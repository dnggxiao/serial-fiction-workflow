from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCES = (
    PROJECT_ROOT
    / ".agents"
    / "skills"
    / "writing-serial-fiction"
    / "references"
)


def read_reference(name):
    return (REFERENCES / name).read_text(encoding="utf-8")


class V110QualityGuardrailsTest(unittest.TestCase):
    def test_planning_keeps_promises_reachable_and_constraints_silent(self):
        text = read_reference("chapter-planning.md")
        for phrase in (
            "承诺不得超过固定事件实际能到达的结果",
            "不能冒充本章兑现",
            "作为静默约束",
            "不能用同一说明拆出多个场景",
            "不是正文必须出现固定数量技巧的质量标准",
        ):
            self.assertIn(phrase, text)

    def test_selector_does_not_force_a_technique_or_pre_spend_the_ending(self):
        text = read_reference("technique-selector.md")
        for phrase in (
            "无需额外手法",
            "一主一辅",
            "仅在固定事件允许时",
            "不在前文完整重复同一落点",
        ):
            self.assertIn(phrase, text)

    def test_prose_rules_cover_observed_v100_regressions(self):
        text = read_reference("prose-writing.md")
        for phrase in (
            "作为静默约束",
            "亲见、他人陈述与推断",
            "合同式台词",
            "最低充分证据",
            "未变化状态默认静默",
        ):
            self.assertIn(phrase, text)

    def test_diagnosis_has_matching_readonly_signals(self):
        text = read_reference("readonly-diagnosis.md")
        for phrase in (
            "同一根因",
            "连续免责声明",
            "反复报相同数值",
            "亲见、他人陈述与推断",
            "同一种完整分析语气",
            "不添加总体结论、无硬冲突声明",
        ):
            self.assertIn(phrase, text)

    def test_official_reference_separates_source_tiers(self):
        text = read_reference("fanqie-cn-profile.md")
        for phrase in (
            "## 方法分层",
            "## 新手专区补充来源",
            "稳定原则",
            "条件性方法",
            "排除项",
            "不套固定频率、奖励或数量公式",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
