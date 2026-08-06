"""Offline integrity verification for portable release artifacts."""

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


def _zip_manifest_root(zip_path, member_names):
    if zip_path.name.startswith("codex-novel-workflow-portable-v"):
        expected = "codex-novel-workflow-portable/MANIFEST.sha256"
    elif (
        zip_path.name.startswith("novel-workflow-v")
        and zip_path.name.endswith("-update-overlay.zip")
    ):
        overlay_root = zip_path.name[:-4]
        expected = f"{overlay_root}/MANIFEST.sha256"
    elif "-migration-profile-v" in zip_path.name:
        candidates = sorted(
            name
            for name in member_names
            if name.startswith("迁移配置/") and name.endswith("/MANIFEST.sha256")
        )
        if len(candidates) != 1:
            return None, None, [
                f"expected exactly one profile manifest in {zip_path.name}; "
                f"found {len(candidates)}"
            ]
        expected = candidates[0]
    else:
        return None, None, [f"unknown release artifact: {zip_path.name}"]
    if expected not in member_names:
        return None, None, [f"inner manifest missing: {expected}"]
    return expected.rsplit("/", 1)[0], expected, []


def _zip_errors(zip_path):
    errors = []
    try:
        with zipfile.ZipFile(zip_path) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                errors.append(f"corrupt zip member: {corrupt}")
            members = archive.infolist()
            names = [item.filename for item in members]
            if len(names) != len(set(names)):
                errors.append(f"duplicate zip member in {zip_path.name}")
            for item in members:
                if item.is_dir():
                    errors.append(
                        f"unsafe zip member in {zip_path.name}: {item.filename}"
                    )
                elif not _safe_zip_member(item.filename):
                    errors.append(
                        f"unsafe zip member in {zip_path.name}: {item.filename}"
                    )

            root, manifest_name, root_errors = _zip_manifest_root(zip_path, set(names))
            errors.extend(root_errors)
            if root_errors:
                return errors
            try:
                manifest_text = archive.read(manifest_name).decode("utf-8", errors="strict")
            except (KeyError, UnicodeError) as exc:
                errors.append(f"cannot read inner manifest in {zip_path.name}: {exc}")
                return errors
            entries, manifest_errors = parse_manifest(manifest_text)
            errors.extend(f"{zip_path.name}: {error}" for error in manifest_errors)
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
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"cannot open ZIP {zip_path.name}: {exc}")
    return errors


def verify_release_directory(release_dir):
    """Return integrity errors for the generic, overlay, and profile ZIPs."""
    release_dir = Path(release_dir)
    if not release_dir.is_dir():
        return [f"release directory not found: {release_dir}"]

    generic, generic_errors = _one_match(
        release_dir,
        "codex-novel-workflow-portable-v*.zip",
        "generic package ZIP",
    )
    overlay, overlay_errors = _one_match(
        release_dir,
        "novel-workflow-v*-update-overlay.zip",
        "safe update overlay ZIP",
    )
    profile, profile_errors = _one_match(
        release_dir,
        "*-migration-profile-v*.zip",
        "migration profile ZIP",
    )
    sums, sums_errors = _one_match(
        release_dir,
        "SHA256SUMS-v*.txt",
        "outer checksum file",
    )
    errors = generic_errors + overlay_errors + profile_errors + sums_errors
    if errors:
        return errors

    artifacts = (generic, overlay, profile)
    errors.extend(_outer_sum_errors(sums, artifacts))
    for artifact in artifacts:
        errors.extend(_zip_errors(artifact))
    return errors
