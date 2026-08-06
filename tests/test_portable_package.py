from pathlib import Path
import unittest

from tools.manifest_policy import manifest_errors_for_directory
from tools.package_policy import generic_clean_errors


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "VERSION",
    "LICENSE",
    "NOTICE.md",
    "THIRD_PARTY_NOTICES.md",
    "README_迁移.md",
    "AGENTS.md",
    "README.md",
    "项目清单.md",
    "验证清单.md",
    "01_剧情主线.md",
    "02_连续状态表.md",
    "03_大纲.md",
    "04_章节细纲.md",
    "05_写作规则卡.md",
    "工作区/当前任务.md",
    "正文/README.md",
    ".agents/skills/writing-serial-fiction/SKILL.md",
    ".agents/skills/writing-serial-fiction/LICENSE",
    ".agents/skills/writing-serial-fiction/NOTICE.md",
    ".agents/skills/writing-serial-fiction/THIRD_PARTY_NOTICES.md",
    "工作流/01_准备资料.md",
    "工作流/02_生成正文.md",
    "工作流/03_轻检.md",
    "工作流/04_修正.md",
    "模板/正文最小包模板.md",
    "tests/skill-evals/test_v130_input_contract.py",
    "tests/skill-evals/test_v130_execution_card_guardrails.py",
    "tests/skill-evals/test_v130_prose_guardrails.py",
    "tests/skill-evals/test_v130_lightcheck_guardrails.py",
    "tests/test_generic_domain_content.py",
    "tests/test_open_source_boundaries.py",
}
class PortablePackageTest(unittest.TestCase):
    def test_required_structure(self):
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file()
        }
        self.assertTrue(REQUIRED <= actual)

    def test_generic_package_has_no_book_or_machine_leak(self):
        self.assertEqual(
            [],
            generic_clean_errors(ROOT, ignore_runtime_files=True),
        )

    def test_manifest(self):
        self.assertEqual(
            [],
            manifest_errors_for_directory(
                ROOT,
                excluded_root_names=("迁移配置",),
                ignore_runtime_files=True,
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
