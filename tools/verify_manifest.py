"""Verify the canonical Git-tree manifest from a clean repository checkout."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache"}
LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")


def ignored(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    return bool(IGNORED_PARTS.intersection(parts)) or any(
        part.startswith(".pytest-") for part in parts
    )


def release_files() -> dict[str, Path]:
    return {
        path.relative_to(ROOT).as_posix(): path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path != MANIFEST
        and not ignored(path)
    }


def main() -> None:
    expected: dict[str, str] = {}
    for number, raw in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        match = LINE.fullmatch(raw)
        if not match:
            raise SystemExit(f"Malformed manifest line {number}: {raw!r}")
        digest, relative = match.groups()
        expected[relative] = digest

    actual = release_files()
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatched = sorted(
        relative
        for relative in set(expected).intersection(actual)
        if hashlib.sha256(actual[relative].read_bytes()).hexdigest() != expected[relative]
    )
    if missing or extra or mismatched:
        raise SystemExit(
            f"Manifest verification failed: missing={missing}, extra={extra}, "
            f"mismatched={mismatched}"
        )
    print(f"PASS: verified {len(expected)} canonical Git-tree files")


if __name__ == "__main__":
    main()
