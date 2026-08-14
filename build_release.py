from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
ARCHIVE_NAME = "MATERIALS_ML_SCIENTIFIC_VERIFICATION_RERUNNER_V1_0_0_20260814.zip"
EXCLUDED_PARTS = {"build", "__pycache__", ".pytest_cache", ".git"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def selected_files() -> list[Path]:
    return [
        path for path in sorted(ROOT.rglob("*"))
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(ROOT).parts)
        and path.name != "MANIFEST.sha256"
    ]


def main() -> None:
    files = selected_files()
    manifest = ROOT / "MANIFEST.sha256"
    manifest.write_text(
        "".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files),
        encoding="utf-8",
    )
    files.append(manifest)
    BUILD.mkdir(parents=True, exist_ok=True)
    archive = BUILD / ARCHIVE_NAME
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            bundle.write(path, Path("materials-ml-scientific-rerunner") / path.relative_to(ROOT))
    checksum = BUILD / f"{ARCHIVE_NAME}.sha256"
    checksum.write_text(f"{digest(archive)}  {archive.name}\n", encoding="utf-8")
    print(f"archive={archive}")
    print(f"bytes={archive.stat().st_size}")
    print(f"sha256={digest(archive)}")


if __name__ == "__main__":
    main()
