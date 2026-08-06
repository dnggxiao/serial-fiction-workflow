from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
SKILL = SKILLS / "writing-serial-fiction"
OLD_SKILL_NAME = "writing-" + "fanqie-serial-fiction"
OLD_TOKEN = "$" + OLD_SKILL_NAME
OLD_SKILL = SKILLS / OLD_SKILL_NAME
PROFILE = SKILL / "references" / "fanqie-cn-profile.md"


def test_core_skill_uses_generic_identity():
    assert SKILL.is_dir()
    assert not OLD_SKILL.exists()

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert "name: writing-serial-fiction" in skill_text
    assert "$writing-serial-fiction" in skill_text
    assert f"name: {OLD_SKILL_NAME}" not in skill_text
    assert OLD_TOKEN not in skill_text
    assert 'display_name: "中文连载小说写作引擎"' in metadata
    assert "$writing-serial-fiction" in metadata
    assert "番茄连载小说写作引擎" not in metadata


def test_fanqie_material_is_an_optional_profile():
    assert PROFILE.is_file()
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "references/fanqie-cn-profile.md" in skill_text
    assert "可选平台参考" in skill_text
    assert "默认不读取" in skill_text


def test_workflow_uses_new_token_and_documents_migration():
    runtime_files = [
        ROOT / "AGENTS.md",
        ROOT / "工作流" / "01_准备资料.md",
        ROOT / "工作流" / "02_生成正文.md",
    ]
    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        assert "$writing-serial-fiction" in text
        assert OLD_TOKEN not in text

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "$writing-serial-fiction" in readme
    assert OLD_TOKEN in readme

    migration = ROOT / "迁移" / "05_v1.4.0_技能命名迁移.md"
    migration_text = migration.read_text(encoding="utf-8")
    assert OLD_TOKEN in migration_text
    assert "$writing-serial-fiction" in migration_text


def test_identity_migration_remains_documented_after_patch_release():
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "1.6.0"
    assert (ROOT / "迁移" / "05_v1.4.0_技能命名迁移.md").is_file()
