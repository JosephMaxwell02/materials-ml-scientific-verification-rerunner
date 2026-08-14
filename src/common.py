from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


for _key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_key, "1")


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def environment_receipt() -> dict[str, Any]:
    versions: dict[str, str] = {}
    for package in ("numpy", "pandas", "scipy", "scikit-learn", "matbench", "matminer", "pymatgen"):
        try:
            from importlib.metadata import version
            versions[package] = version(package)
        except Exception:
            versions[package] = "NOT_INSTALLED"
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": versions,
        "threads": 1,
    }


def write_receipt(name: str, payload: dict[str, Any]) -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    complete = {
        "schema": "materials_ml_failure_analysis.rerunner_receipt.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment_receipt(),
        **payload,
    }
    path = OUTPUTS / f"{name}.json"
    path.write_text(json.dumps(complete, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def public_input_identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}

