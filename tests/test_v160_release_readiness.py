from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_current_release_metadata_is_v160():
    assert read("VERSION").strip() == "1.6.0"
    assert "## v1.6.0" in read("CHANGELOG.md")
    assert (ROOT / "releases" / "v1.6.0_RELEASE.md").is_file()
    assert not (ROOT / "releases" / "v1.5.0_RELEASE.md").exists()
    assert "1.6.0" in read("项目清单.md")


def test_required_hidden_repository_directories_are_present():
    assert (ROOT / ".agents" / "skills" / "writing-serial-fiction" / "SKILL.md").is_file()
    assert (ROOT / ".agents" / "skills" / "writing-serial-fiction" / "agents" / "openai.yaml").is_file()
    assert (ROOT / ".github" / "ISSUE_TEMPLATE").is_dir()
    assert (ROOT / ".github" / "pull_request_template.md").is_file()


def test_real_github_actions_workflow_replaces_placeholder():
    workflow = ROOT / ".github" / "workflows" / "release-check.yml"
    assert workflow.is_file()
    text = workflow.read_text(encoding="utf-8")
    assert "python -m pytest" in text
    assert "actions/checkout" in text
    assert not (ROOT / ".github" / "workflows-release-check-placeholder.yml").exists()


def test_upload_and_repository_setup_guides_exist():
    assert (ROOT / "UPLOAD_GUIDE_ZH.md").is_file()
    assert (ROOT / "docs" / "REPOSITORY_SETTINGS_ZH.md").is_file()
    assert (ROOT / "CONTRIBUTING.md").is_file()
    assert (ROOT / "ROADMAP.md").is_file()


def test_repository_contains_no_generated_python_artifacts():
    forbidden = []
    for path in ROOT.rglob("*"):
        if "__pycache__" in path.parts or path.name == ".pytest_cache" or path.suffix in {".pyc", ".pyo"}:
            forbidden.append(path.relative_to(ROOT).as_posix())
    assert forbidden == []


def test_gitignore_blocks_common_generated_artifacts():
    text = read(".gitignore")
    for token in ("__pycache__/", "*.py[cod]", ".pytest_cache/", ".DS_Store"):
        assert token in text
