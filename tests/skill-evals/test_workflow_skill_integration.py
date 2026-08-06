from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL_TOKEN = "$writing-serial-fiction"


class WorkflowSkillIntegrationTest(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_controller_routes_without_embedding_skill_references(self):
        text = self.read("AGENTS.md")
        self.assertIn(SKILL_TOKEN, text)
        self.assertIn("chapter-planning", text)
        self.assertIn("prose-writing", text)
        self.assertIn("工作流 03、04 不调用", text)
        self.assertNotIn("references/", text)

    def test_planning_workflow_invokes_skill_and_contains_failure_gates(self):
        text = self.read("工作流/01_准备资料.md")
        self.assertIn(SKILL_TOKEN, text)
        self.assertIn("mode=chapter-planning", text)
        self.assertIn("规划片段字数预算", text)
        self.assertIn("篇幅权重", text)
        self.assertIn("视角偏压", text)
        self.assertIn("整段总范围，不是逐场额度", text)
        self.assertIn("每场推进节点必须为 3～5 个按顺序编号的节点", text)
        self.assertRegex(text, r"完整执行卡.{0,24}500～800")
        self.assertIn("INPUT_ERROR:", text)
        self.assertIn("不得保存为场景执行卡", text)
        self.assertIn("BLOCKED:", text)
        self.assertIn("当前阶段设置为 `阻塞冲突`", text)

    def test_planning_skill_treats_fragment_budget_as_one_total_range(self):
        text = self.read(
            ".agents/skills/writing-serial-fiction/references/chapter-planning.md"
        )
        self.assertIn("规划片段字数预算", text)
        self.assertIn("450～700 个可见 CJK 字符", text)
        self.assertIn("绝不拆分成分场额度", text)
        self.assertIn("每场 `推进节点` 必须包含 3～5 个按顺序编号的节点", text)
        self.assertNotIn("各场之和必须等于目标正文字数", text)
        self.assertNotIn("按场景功能分配建议正文字数", text)

    def test_writer_facing_card_excludes_audit_shell(self):
        card = self.read("模板/场景执行卡模板.md")
        for forbidden_heading in ("连续性锁定", "禁止扩写", "放行结论"):
            self.assertNotIn(f"## {forbidden_heading}", card)

        packet = self.read("模板/本章资料包模板.md")
        self.assertIn("## 执行卡放行记录", packet)
        for release_check in (
            "- 新增重要事件：否",
            "- 改变细纲结果：否",
            "- 提前揭示后续：否",
            "- 结尾落点一致：是",
        ):
            self.assertIn(release_check, packet)

    def test_prose_workflow_invokes_skill_and_contains_failure_gates(self):
        text = self.read("工作流/02_生成正文.md")
        self.assertIn(SKILL_TOKEN, text)
        self.assertIn("mode=prose-writing", text)
        self.assertIn("INPUT_ERROR:", text)
        self.assertIn("不得保存为初稿", text)
        self.assertIn("当前阶段恢复为 `等待确认执行卡`", text)
        self.assertIn("BLOCKED:", text)
        self.assertIn("当前阶段设置为 `阻塞冲突`", text)
        self.assertIn("不得进入轻检", text)
        self.assertIn(
            "Skill 无法加载或调用失败时，不得保存初稿，不得进入轻检；"
            "将当前阶段恢复为 `等待确认执行卡`",
            text,
        )
        self.assertIn(
            "输出形状检查未通过时，将当前阶段恢复为 `等待确认执行卡`",
            text,
        )

    def test_prose_workflow_passes_only_the_two_approved_inputs(self):
        text = self.read("工作流/02_生成正文.md")
        match = re.search(
            r"显式调用 `\$writing-serial-fiction mode=prose-writing`，只提供："
            r"\n\n(?P<inputs>(?:- .+\n)+)",
            text,
        )
        self.assertIsNotNone(match)
        self.assertEqual(
            match.group("inputs").splitlines(),
            [
                "- 本章正文最小包；",
                "- 本章场景执行卡。",
            ],
        )

        allowed = text.split("正文生成阶段只允许读取：", 1)[1].split(
            "禁止打开", 1
        )[0]
        self.assertEqual(
            re.findall(r"- `([^`]+)`", allowed),
            [
                "工作区/第N章_正文最小包.md",
                "工作区/第N章_场景执行卡.md",
            ],
        )

    def test_whole_chapter_rewrite_cannot_read_planning_packet(self):
        text = self.read("工作流/04_修正.md")
        whole = text.split("## 整章重写", 1)[1].split("## 循环限制", 1)[0]
        self.assertIn("工作区/第N章_正文最小包.md", whole)
        self.assertIn("工作区/第N章_场景执行卡.md", whole)
        self.assertNotIn("重新读取本章资料包和执行卡", whole)

    def test_readme_documents_modes_and_independent_later_stages(self):
        text = self.read("README.md")
        self.assertIn(SKILL_TOKEN, text)
        self.assertIn("chapter-planning", text)
        self.assertIn("prose-writing", text)
        self.assertIn("readonly-diagnosis", text)
        self.assertIn("工作流 03、04", text)
        self.assertIn("正文模型只接收两个输入", text)
        self.assertIn("一轮静默删重", text)

    def test_packet_carries_style_anchors_without_extra_prose_inputs(self):
        packet = self.read("模板/本章资料包模板.md")
        prepare = self.read("工作流/01_准备资料.md")
        self.assertIn("文风锚点与人物声纹", packet)
        self.assertIn("最多 3 个作者认可的短文风锚点", prepare)

    def test_later_workflows_do_not_invoke_skill(self):
        for relative_path in ("工作流/03_轻检.md", "工作流/04_修正.md"):
            self.assertNotIn(SKILL_TOKEN, self.read(relative_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
