"""Command-line verifier for a portable novel-workflow release."""

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.release_integrity import verify_release_directory


def main():
    parser = argparse.ArgumentParser(
        description="Verify all release ZIPs, outer hashes, and inner manifests."
    )
    parser.add_argument("--release-dir", required=True, type=Path)
    args = parser.parse_args()
    errors = verify_release_directory(args.release_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RELEASE_INTEGRITY_OK=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
