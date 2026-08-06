from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "writing-serial-fiction"
REFERENCES = SKILL / "references"


def read(path):
    return Path(path).read_text(encoding="utf-8")


class V120NaturalnessGuardrailsTest(unittest.TestCase):
    def test_planning_compresses_same_function_events_and_hides_methods(self):
        text = read(REFERENCES / "chapter-planning.md")
        for phrase in (
            "同一事实或边界只选择一处最有摩擦的事件完整证明",
            "不得连续安排“再次确认仍未解决”",
            "功能相同且结果相同的平行事件不得各占一个场景",
            "不得把课程术语、审校术语或管理语言直接交给正文模型",
        ):
            self.assertIn(phrase, text)

    def test_prose_has_single_pass_naturalization(self):
        text = read(REFERENCES / "prose-writing.md")
        for phrase in (
            "最低充分证据",
            "合并连续证明同一状态或规则的平行小场面",
            "对白允许不完整",
            "旁白不做课后总结",
            "输出前的一次静默去机械化",
            "不进行第二轮重写",
        ):
            self.assertIn(phrase, text)

    def test_examples_cover_observed_ai_feel_patterns(self):
        text = read(REFERENCES / "natural-prose-patterns.md")
        for heading in (
            "未核验只证明一次",
            "证据足够后停止",
            "让对白带着人物自己的麻烦",
            "动作证明后，不加课后总结",
            "把规划词换成镜头里的结果",
        ):
            self.assertIn(heading, text)

    def test_diagnosis_requires_evidence_not_word_blacklists(self):
        text = read(REFERENCES / "readonly-diagnosis.md")
        for phrase in (
            "所谓“AI感”不按某个词判定",
            "多个小场面是否只是用不同物品反复证明同一规则",
            "执行卡中的“目标、边界、状态变化、可行性、候选、确认条件”",
            "不要把同一“解释过度”拆成多项",
        ):
            self.assertIn(phrase, text)

    def test_workflow_catches_only_severe_mechanical_patterns(self):
        light = read(ROOT / "工作流" / "03_轻检.md")
        repair = read(ROOT / "工作流" / "04_修正.md")
        for phrase in (
            "第 6 类必须给出至少三处分离证据",
            "不得凭“像AI”下结论",
        ):
            self.assertIn(phrase, light)
        for phrase in (
            "机械化问题优先用删除、合并和缩短解决",
            "不得用景物、心理或解释把删掉的字数补回来",
        ):
            self.assertIn(phrase, repair)

    def test_style_card_and_packet_use_approved_samples(self):
        style = read(ROOT / "05_写作规则卡.md")
        packet = read(ROOT / "模板" / "本章资料包模板.md")
        self.assertIn("作者认可的正式正文", style)
        self.assertIn("文风锚点与人物声纹", packet)
        self.assertIn("不得复制样本事件", packet)


if __name__ == "__main__":
    unittest.main(verbosity=2)
