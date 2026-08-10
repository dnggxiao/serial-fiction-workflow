"""Offline integrity verification for current release artifacts."""

from pathlib import Path, PurePosixPath
import hashlib
import re
import zipfile

from tools.manifest_policy import parse_manifest


SUM_LINE = re.compile(r"^([0-9a-f]{64})  ([^/\\]+)$")


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _one_match(root, pattern, label):
    matches = sorted(Path(root).glob(pattern))
    if len(matches) != 1:
        return None, [f"expected exactly one {label}; found {len(matches)}"]
    return matches[0], []


def _safe_zip_member(name):
    if "\\" in name or ":" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts:
        return False
    if any(part in {"", ".", ".."} for part in path.parts):
        return False
    return path.as_posix() == name


def _outer_sum_errors(sums_path, artifacts):
    errors = []
    entries = {}
    try:
        lines = sums_path.read_text(encoding="utf-8", errors="strict").splitlines()
    except UnicodeError as exc:
        return [f"{sums_path.name} is not valid UTF-8: {exc}"]
    for line_number, line in enumerate(lines, start=1):
        match = SUM_LINE.fullmatch(line)
        if match is None:
            errors.append(f"invalid outer checksum line {line_number}: {line}")
            continue
        digest, name = match.groups()
        if name in entries:
            errors.append(f"duplicate outer checksum path: {name}")
            continue
        entries[name] = digest

    expected_names = {path.name for path in artifacts}
    if set(entries) != expected_names:
        errors.append(
            "outer checksum file set mismatch: "
            f"expected={sorted(expected_names)}; actual={sorted(entries)}"
        )
    for artifact in artifacts:
        expected = entries.get(artifact.name)
        if expected is not None and _sha256_file(artifact) != expected:
            errors.append(f"hash mismatch: {artifact.name}")
    return errors


def _common_root(names):
    roots = {
        PurePosixPath(name).parts[0]
        for name in names
        if PurePosixPath(name).parts
    }
    if len(roots) != 1:
        return None
    return next(iter(roots))


def _base_zip_errors(zip_path):
    errors = []
    try:
        archive = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile) as exc:
        return None, [], [f"cannot open ZIP {zip_path.name}: {exc}"]

    corrupt = archive.testzip()
    if corrupt is not None:
        errors.append(f"corrupt zip member: {corrupt}")
    members = archive.infolist()
    names = [item.filename for item in members]
    if len(names) != len(set(names)):
        errors.append(f"duplicate zip member in {zip_path.name}")
    for item in members:
        if item.is_dir() or not _safe_zip_member(item.filename):
            errors.append(f"unsafe zip member in {zip_path.name}: {item.filename}")
    return archive, names, errors


def _portable_zip_errors(zip_path):
    archive, names, errors = _base_zip_errors(zip_path)
    if archive is None:
        return errors
    try:
        manifest_name = "codex-novel-workflow-portable/MANIFEST.sha256"
        if manifest_name not in names:
            errors.append(f"inner manifest missing: {manifest_name}")
            return errors
        try:
            manifest_text = archive.read(manifest_name).decode(
                "utf-8", errors="strict"
            )
        except (KeyError, UnicodeError) as exc:
            errors.append(f"cannot read inner manifest in {zip_path.name}: {exc}")
            return errors
        entries, manifest_errors = parse_manifest(manifest_text)
        errors.extend(f"{zip_path.name}: {error}" for error in manifest_errors)
        root = "codex-novel-workflow-portable"
        expected_members = {
            f"{root}/{relative}" for relative in entries
        } | {manifest_name}
        actual_members = set(names)
        if actual_members != expected_members:
            errors.append(
                f"zip member set mismatch in {zip_path.name}: "
                f"missing={sorted(expected_members - actual_members)}; "
                f"extra={sorted(actual_members - expected_members)}"
            )
        for relative, expected_digest in entries.items():
            member = f"{root}/{relative}"
            try:
                payload = archive.read(member)
            except KeyError:
                continue
            if _sha256_bytes(payload) != expected_digest:
                errors.append(f"inner hash mismatch: {zip_path.name}!{member}")
    finally:
        archive.close()
    return errors


def _source_zip_errors(zip_path):
    archive, names, errors = _base_zip_errors(zip_path)
    if archive is None:
        return errors
    try:
        root = _common_root(names)
        if root is None:
            errors.append(
                f"source archive must have one top-level root: {zip_path.name}"
            )
            return errors
        required = {f"{root}/README.md", f"{root}/VERSION"}
        missing = required - set(names)
        if missing:
            errors.append(
                f"source archive missing required members: {sorted(missing)}"
            )
    finally:
        archive.close()
    return errors


def _skill_zip_errors(zip_path):
    archive, names, errors = _base_zip_errors(zip_path)
    if archive is None:
        return errors
    try:
        required = {
            "writing-serial-fiction/SKILL.md",
            "writing-serial-fiction/agents/openai.yaml",
        }
        missing = required - set(names)
        if missing:
            errors.append(
                f"skill archive missing required members: {sorted(missing)}"
            )
        if any(not name.startswith("writing-serial-fiction/") for name in names):
            errors.append(
                f"skill archive has unexpected top-level member: {zip_path.name}"
            )
    finally:
        archive.close()
    return errors


def verify_release_directory(release_dir):
    """Return integrity errors for the four current release ZIP roles."""
    release_dir = Path(release_dir)
    if not release_dir.is_dir():
        return [f"release directory not found: {release_dir}"]

    portable, portable_errors = _one_match(
        release_dir,
        "codex-novel-workflow-portable-v*.zip",
        "portable package ZIP",
    )
    source, source_errors = _one_match(
        release_dir,
        "serial-fiction-workflow-v*-official.zip",
        "official source ZIP",
    )
    skill, skill_errors = _one_match(
        release_dir,
        "skill.zip",
        "unversioned Skill ZIP",
    )
    versioned_skill, versioned_skill_errors = _one_match(
        release_dir,
        "writing-serial-fiction-v*.zip",
        "versioned Skill ZIP",
    )
    sums, sums_errors = _one_match(
        release_dir,
        "SHA256SUMS-v*.txt",
        "outer checksum file",
    )
    errors = (
        portable_errors
        + source_errors
        + skill_errors
        + versioned_skill_errors
        + sums_errors
    )
    if errors:
        return errors

    artifacts = (portable, source, skill, versioned_skill)
    errors.extend(_outer_sum_errors(sums, artifacts))
    errors.extend(_portable_zip_errors(portable))
    errors.extend(_source_zip_errors(source))
    errors.extend(_skill_zip_errors(skill))
    errors.extend(_skill_zip_errors(versioned_skill))
    return errors
