from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class V130InputContractTest(unittest.TestCase):
    def test_prose_minimal_template_has_unique_sections(self):
        template = ROOT / "模板" / "正文最小包模板.md"
        self.assertTrue(template.is_file(), "prose minimal template missing")
        text = template.read_text(encoding="utf-8")
        for heading in (
            "## 开场接口",
            "## 决策相关状态",
            "## 静默禁区",
            "## 视角偏压与人物声纹",
            "## 已核验专业事实",
        ):
            self.assertIn(heading, text)
        for forbidden in ("本章完整细纲", "资料来源", "状态变更补丁", "放行结论"):
            self.assertNotIn(forbidden, text)

    def test_prose_workflow_reads_minimal_packet_not_planning_packet(self):
        text = read("工作流/02_生成正文.md")
        self.assertIn("工作区/第N章_正文最小包.md", text)
        allowed = text.split("## 上下文限制", 1)[1].split("## Skill 调用", 1)[0]
        self.assertNotIn("工作区/第N章_资料包.md", allowed)

    def test_full_rewrite_cannot_fall_back_to_planning_packet(self):
        text = read("工作流/04_修正.md")
        whole = text.split("## 整章重写", 1)[1].split("## 循环限制", 1)[0]
        self.assertIn("第N章_正文最小包.md", whole)
        self.assertNotIn("重新读取本章资料包和执行卡", whole)

    def test_current_task_records_minimal_packet(self):
        relatives = ["工作区/当前任务.md"]
        portable_task = ROOT / "portable" / "generic" / "当前任务.md"
        if portable_task.is_file():
            relatives.append("portable/generic/当前任务.md")
        for relative in relatives:
            self.assertIn("正文最小包:", read(relative))

    def test_author_commands_remain_two_step(self):
        agents = read("AGENTS.md")
        self.assertIn("准备第N章", agents)
        self.assertIn("确认执行卡，生成正文", agents)

    def test_prose_title_and_word_target_only_come_from_minimal_packet(self):
        text = read("工作流/02_生成正文.md")
        self.assertIn("章节标题和总字数目标从正文最小包读取", text)

        hard_coded_ranges = re.findall(r"\d{3,5}\s*[～~-]\s*\d{3,5}\s*字", text)
        self.assertEqual(["3000～5000 字"], hard_coded_ranges)

        boundary_line = next(
            line for line in text.splitlines() if "3000～5000 字" in line
        )
        self.assertIn("合法范围校验边界", boundary_line)
        self.assertIn("不作为独立目标", boundary_line)

    def test_prose_skill_call_has_exactly_two_semantic_inputs(self):
        text = read("工作流/02_生成正文.md")
        call = text.split("显式调用 `$writing-serial-fiction mode=prose-writing`，只提供：", 1)[1]
        call = call.split("章节标题和总字数目标从正文最小包读取", 1)[0]
        inputs = [line.strip() for line in call.splitlines() if line.startswith("- ")]
        self.assertEqual(
            ["- 本章正文最小包；", "- 本章场景执行卡。"],
            inputs,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
