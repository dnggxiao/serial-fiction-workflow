"""Shared content policy for the generic portable package."""

from pathlib import Path
import re


ALLOWED_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".py", ".svg"}
ALLOWED_NAMES = {"VERSION", ".gitignore", "MANIFEST.sha256", "LICENSE"}
DRIVE_PATH_RE = re.compile(r"[A-Za-z]:[\\/]")


def generic_clean_errors(
    root,
    excluded_root_names=("迁移配置",),
    ignore_runtime_files=False,
    banned_terms=(),
):
    root = Path(root)
    excluded = set(excluded_root_names)
    errors = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in excluded:
            continue
        if any(part in {".git", "__pycache__", ".pytest_cache", "dist"} for part in relative.parts):
            if ignore_runtime_files and any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts):
                continue
            errors.append("excluded path: " + relative.as_posix())
            continue
        if path.suffix == ".pyc":
            if ignore_runtime_files:
                continue
            errors.append("excluded file type: " + relative.as_posix())
            continue
        if path.name not in ALLOWED_NAMES and path.suffix not in ALLOWED_SUFFIXES:
            errors.append("unapproved file type: " + relative.as_posix())
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append("non-UTF-8 text: " + relative.as_posix())
            continue
        text_without_urls = re.sub(r"https?://\S+", "", text)
        if DRIVE_PATH_RE.search(text_without_urls):
            errors.append("absolute drive path: " + relative.as_posix())
        folded = text.casefold()
        for term in banned_terms:
            if term.casefold() in folded:
                errors.append(
                    "book-specific term: " + relative.as_posix() + " [" + term + "]"
                )
    return errors
