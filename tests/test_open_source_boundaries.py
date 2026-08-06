from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "writing-serial-fiction"

EXPECTED_COPYRIGHT = "Copyright (c) 2026 dnggxiao and contributors"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_root_and_standalone_skill_have_detectable_mit_license():
    root_license = ROOT / "LICENSE"
    skill_license = SKILL / "LICENSE"

    assert root_license.is_file()
    assert skill_license.is_file()
    assert read(root_license) == read(skill_license)

    text = read(root_license)
    assert text.startswith("MIT License\n")
    assert EXPECTED_COPYRIGHT in text
    assert "Permission is hereby granted, free of charge" in text
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in text


def test_notice_keeps_user_manuscripts_outside_template_license():
    root_notice = ROOT / "NOTICE.md"
    skill_notice = SKILL / "NOTICE.md"

    assert root_notice.is_file()
    assert skill_notice.is_file()
    assert read(root_notice) == read(skill_notice)

    text = read(root_notice)
    assert EXPECTED_COPYRIGHT in text
    assert "原创代码、提示词、模板和文档" in text
    assert "MIT License" in text
    assert "小说正文、剧情设定、连续状态、文风样本" in text
    assert "不因放入本项目目录而自动采用 MIT License" in text
    assert "生成内容的权利归属" in text


def test_third_party_notice_documents_fanqie_boundary_and_no_affiliation():
    root_notice = ROOT / "THIRD_PARTY_NOTICES.md"
    skill_notice = SKILL / "THIRD_PARTY_NOTICES.md"

    assert root_notice.is_file()
    assert skill_notice.is_file()
    assert read(root_notice) == read(skill_notice)

    text = read(root_notice)
    assert "番茄小说网" in text
    assert "references/fanqie-cn-profile.md" in text
    assert "课程标题和页面主题的简短转述" in text
    assert "不包含课程原文" in text
    assert "非官方" in text
    assert "归各自权利人所有" in text


def test_readme_and_profile_link_to_legal_boundaries():
    readme = read(ROOT / "README.md")
    profile = read(SKILL / "references" / "fanqie-cn-profile.md")

    assert "## 许可证与内容权利" in readme
    assert "MIT License" in readme
    assert "NOTICE.md" in readme
    assert "THIRD_PARTY_NOTICES.md" in readme
    assert "../THIRD_PARTY_NOTICES.md" in profile


def test_current_release_version_and_historical_migration_note():
    assert read(ROOT / "VERSION").strip() == "1.6.0"
    migration = ROOT / "迁移" / "06_v1.4.1_开源许可与来源边界.md"
    assert migration.is_file()
    text = read(migration)
    assert "MIT License" in text
    assert "dnggxiao and contributors" in text
    assert "用户内容" in text
    assert "第三方资料" in text
