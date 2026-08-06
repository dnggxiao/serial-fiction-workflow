from pathlib import Path

from tools.package_policy import generic_clean_errors


ROOT = Path(__file__).resolve().parents[1]
BANNED_PRIVATE_THEME_TERMS = (
    "战" + "雷",
    "War" + " Thunder",
    "官方 " + "War" + " Thunder Wiki",
    "战" + "雷硬核资料",
)


def test_release_content_has_no_private_theme_residue():
    errors = generic_clean_errors(
        ROOT,
        excluded_root_names=("迁移配置",),
        ignore_runtime_files=True,
        banned_terms=BANNED_PRIVATE_THEME_TERMS,
    )
    residue_errors = [
        error for error in errors if error.startswith("book-specific term:")
    ]
    assert residue_errors == []
