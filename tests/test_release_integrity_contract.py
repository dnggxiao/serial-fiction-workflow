from pathlib import Path
import hashlib
import zipfile

from tools.release_integrity import verify_release_directory


def _sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def _write_zip(path, members):
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def _build_release(tmp_path):
    portable_payload = b"portable-readme\n"
    manifest = f"{_sha256(portable_payload)}  README.md\n".encode()
    _write_zip(
        tmp_path / "codex-novel-workflow-portable-v1.6.1.zip",
        {
            "codex-novel-workflow-portable/README.md": portable_payload,
            "codex-novel-workflow-portable/MANIFEST.sha256": manifest,
        },
    )
    _write_zip(
        tmp_path / "serial-fiction-workflow-v1.6.1-official.zip",
        {
            "serial-fiction-workflow-v1.6.1/README.md": b"source\n",
            "serial-fiction-workflow-v1.6.1/VERSION": b"1.6.1\n",
        },
    )
    skill_members = {
        "writing-serial-fiction/SKILL.md": (
            b"---\nname: writing-serial-fiction\n---\n"
        ),
        "writing-serial-fiction/agents/openai.yaml": (
            b"interface:\n  display_name: test\n"
        ),
    }
    _write_zip(tmp_path / "skill.zip", skill_members)
    _write_zip(tmp_path / "writing-serial-fiction-v1.6.1.zip", skill_members)
    _rewrite_checksums(tmp_path)


def _rewrite_checksums(tmp_path):
    artifacts = sorted(tmp_path.glob("*.zip"))
    lines = [
        f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}"
        for artifact in artifacts
    ]
    (tmp_path / "SHA256SUMS-v1.6.1.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def test_current_release_asset_set_is_accepted(tmp_path):
    _build_release(tmp_path)
    assert verify_release_directory(tmp_path) == []


def test_checksum_file_must_cover_exactly_four_zip_assets(tmp_path):
    _build_release(tmp_path)
    sums = tmp_path / "SHA256SUMS-v1.6.1.txt"
    lines = sums.read_text(encoding="utf-8").splitlines()
    sums.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    errors = verify_release_directory(tmp_path)
    assert any(
        error.startswith("outer checksum file set mismatch:")
        for error in errors
    )


def test_skill_zip_rejects_unsafe_member(tmp_path):
    _build_release(tmp_path)
    _write_zip(tmp_path / "skill.zip", {"../escape.txt": b"bad"})
    _rewrite_checksums(tmp_path)
    errors = verify_release_directory(tmp_path)
    assert any("unsafe zip member in skill.zip" in error for error in errors)
