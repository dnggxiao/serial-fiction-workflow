"""Strict SHA-256 manifest parsing and directory verification."""

from pathlib import Path, PurePosixPath
import hashlib
import re


MANIFEST_NAME = "MANIFEST.sha256"
MANIFEST_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_relative_path(relative):
    if "\\" in relative or ":" in relative:
        return False
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts:
        return False
    if any(part in {"", ".", ".."} for part in path.parts):
        return False
    if path.as_posix() != relative:
        return False
    return relative != MANIFEST_NAME


def parse_manifest(text):
    """Return ``(entries, errors)`` for a strict portable manifest."""
    entries = {}
    errors = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = MANIFEST_LINE.fullmatch(line)
        if match is None:
            errors.append(f"invalid manifest line {line_number}: {line}")
            continue
        digest, relative = match.groups()
        if not _safe_relative_path(relative):
            errors.append(f"unsafe manifest path on line {line_number}: {relative}")
            continue
        if relative in entries:
            errors.append(f"duplicate manifest path on line {line_number}: {relative}")
            continue
        entries[relative] = digest
    return entries, errors


def manifest_errors_for_directory(
    root,
    excluded_root_names=(),
    ignore_runtime_files=False,
):
    """Verify hashes and the exact file set under ``root``."""
    root = Path(root)
    manifest = root / MANIFEST_NAME
    if not manifest.is_file():
        return [f"{MANIFEST_NAME} missing"]
    try:
        text = manifest.read_text(encoding="utf-8", errors="strict")
    except UnicodeError as exc:
        return [f"{MANIFEST_NAME} is not valid UTF-8: {exc}"]

    entries, errors = parse_manifest(text)
    for relative, expected_digest in entries.items():
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file():
            errors.append(f"missing: {relative}")
        elif _sha256(path) != expected_digest:
            errors.append(f"hash mismatch: {relative}")

    excluded = set(excluded_root_names)
    actual = set()
    for path in root.rglob("*"):
        if not path.is_file() or path == manifest:
            continue
        relative_path = path.relative_to(root)
        if relative_path.parts and relative_path.parts[0] in excluded:
            continue
        if ignore_runtime_files and (
            any(part in {"__pycache__", ".pytest_cache"} for part in relative_path.parts)
            or path.suffix == ".pyc"
        ):
            continue
        actual.add(relative_path.as_posix())
    listed = set(entries)
    for relative in sorted(actual - listed):
        errors.append(f"unlisted: {relative}")
    for relative in sorted(listed - actual):
        if not any(error == f"missing: {relative}" for error in errors):
            errors.append(f"missing: {relative}")
    return errors
