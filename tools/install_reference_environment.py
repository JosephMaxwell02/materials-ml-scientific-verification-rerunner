"""Install the exact published top-level environment without changing versions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "environment" / "requirements.txt"


def main() -> None:
    specifications = [
        line.strip()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    metadata_conflicts = [
        spec
        for spec in specifications
        if spec.lower().startswith(("matbench==", "matminer=="))
    ]
    compatible = [spec for spec in specifications if spec not in metadata_conflicts]
    if len(metadata_conflicts) != 2:
        raise SystemExit("Expected pinned matbench and matminer specifications")

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            *compatible,
            "monty",
            "pymongo",
            "requests",
            "sympy",
            "tqdm",
        ]
    )
    # The published environment intentionally preserves pandas 3.0.2 with
    # matminer 0.10.1, while matminer metadata requests pandas<3. Matbench 0.6
    # also pins matminer 0.7.4. Install both packages without replacing the
    # receipted top-level versions; their runtime dependencies were installed
    # above.
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--no-deps", *metadata_conflicts]
    )


if __name__ == "__main__":
    main()
