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
    matbench = [spec for spec in specifications if spec.lower().startswith("matbench==")]
    compatible = [spec for spec in specifications if spec not in matbench]
    if len(matbench) != 1:
        raise SystemExit("Expected exactly one pinned matbench specification")

    subprocess.check_call([sys.executable, "-m", "pip", "install", *compatible])
    # matbench 0.6 metadata pins an older matminer than the frozen, receipted
    # environment. Install its package without replacing the declared matminer.
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--no-deps", matbench[0]]
    )


if __name__ == "__main__":
    main()
