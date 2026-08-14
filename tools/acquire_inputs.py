from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np


JARVIS_URL = "https://ndownloader.figshare.com/files/38521619"
JARVIS_FILENAME = "jdft_3d-12-12-2022.json.zip"
JARVIS_SHA256 = "d4c64660e9e1fa45c82bd8868a96ec10162195eed69636445972c05550d8d0d6"
MP_VIABILITY_FILES = {
    "materials_project_snapshot.csv": "e02083989c5f0dc029408eaf4b8634fe5557241a06e8e3ebd10c27693fa26b62",
    "COHORT_MEMBERSHIP.csv": "400477bf4ddad86ba1962e23ed4b482a3f72dc65327f0af6cf961f5d4d00b6bd",
    "SPLIT_MEMBERSHIP.csv": "bb3ed8b708b2ffffdb9f8d6aa6277ddaa3e0bcdd3e822d8bc9c204d53126f700",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _json_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _stable_input(value: Any) -> Any:
    return _json_value(value.as_dict()) if hasattr(value, "as_dict") else str(value)


def _array_sha256(array: np.ndarray, feature_names: list[str]) -> str:
    canonical = np.ascontiguousarray(array, dtype="<f8")
    digest = hashlib.sha256()
    digest.update(canonical_json({"shape": list(canonical.shape), "dtype": "<f8", "feature_names": feature_names}))
    digest.update(memoryview(canonical).cast("B"))
    return digest.hexdigest()


def build_matbench_cache(output: Path, task_name: str) -> dict[str, Any]:
    from matbench.bench import MatbenchBenchmark
    from matminer.featurizers.composition import ElementProperty, Stoichiometry, ValenceOrbital
    from pymatgen.core import Composition

    benchmark = MatbenchBenchmark(autoload=False, subset=[task_name])
    task = list(benchmark.tasks)[0]
    task.load()
    sample_ids = [str(value) for value in task.df.index.tolist()]
    inputs = task.df[task.metadata["input_type"]].tolist()
    targets = task.df[task.metadata["target"]].tolist()
    input_digest = hashlib.sha256()
    source_digest = hashlib.sha256()
    source_digest.update(canonical_json({
        "dataset_name": task.dataset_name,
        "benchmark_name": task.benchmark_name,
        "task_type": task.metadata["task_type"],
        "input_type": task.metadata["input_type"],
        "target": task.metadata["target"],
    }))
    for sample_id, value, target in zip(sample_ids, inputs, targets):
        row = canonical_json({"sample_id": sample_id, "input": _stable_input(value)})
        input_digest.update(row)
        input_digest.update(b"\n")
        source_digest.update(row)
        source_digest.update(canonical_json({"target": _json_value(target)}))
        source_digest.update(b"\n")

    featurizers = [ElementProperty.from_preset("magpie"), Stoichiometry(), ValenceOrbital(props=["avg"])]
    names = [label for item in featurizers for label in item.feature_labels()]
    rows: list[list[float]] = []
    for number, value in enumerate(inputs, start=1):
        composition = value.composition if hasattr(value, "composition") else Composition(str(value))
        rows.append([float(feature) for item in featurizers for feature in item.featurize(composition)])
        if number % 10000 == 0:
            print(f"matbench cache: {number}/{len(inputs)} rows", flush=True)
    array = np.asarray(rows, dtype=float)
    task_cache = output / task.dataset_name
    buffer = io.BytesIO()
    np.savez_compressed(buffer, x=array)
    atomic_bytes(task_cache / "full_features.npz", buffer.getvalue())
    metadata = {
        "task": task.dataset_name,
        "rows": len(rows),
        "sample_ids": sample_ids,
        "feature_names": names,
        "source_sha256": source_digest.hexdigest(),
        "input_sha256": input_digest.hexdigest(),
        "feature_sha256": _array_sha256(array, names),
        "feature_names_sha256": hashlib.sha256(canonical_json(names)).hexdigest(),
    }
    atomic_bytes(task_cache / "full_features.json", canonical_json(metadata) + b"\n")
    return {"status": "PASS", "output": str(task_cache), **{key: metadata[key] for key in ("rows", "source_sha256", "input_sha256", "feature_sha256", "feature_names_sha256")}}


def acquire_spatial_gil(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    destination = output / JARVIS_FILENAME
    if not destination.is_file() or sha256_file(destination) != JARVIS_SHA256:
        with urllib.request.urlopen(JARVIS_URL) as response:
            atomic_bytes(destination, response.read())
    actual = sha256_file(destination)
    if actual != JARVIS_SHA256:
        raise RuntimeError(f"JARVIS_INPUT_HASH_MISMATCH:{actual}")
    return {"status": "PASS", "output": str(destination), "bytes": destination.stat().st_size, "sha256": actual, "source": JARVIS_URL}


def verify_mp_viability(directory: Path) -> dict[str, Any]:
    files = []
    for filename, expected in MP_VIABILITY_FILES.items():
        path = directory / filename
        if not path.is_file():
            raise RuntimeError(f"MP_VIABILITY_INPUT_MISSING:{filename}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"MP_VIABILITY_INPUT_HASH_MISMATCH:{filename}:{actual}")
        files.append({"filename": filename, "bytes": path.stat().st_size, "sha256": actual})
    return {"status": "PASS", "files": files}


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire or verify third-party inputs without storing credentials")
    sub = parser.add_subparsers(dest="command", required=True)
    matbench = sub.add_parser("matbench-cache", help="Download Matbench through its package and build the frozen 142-feature cache")
    matbench.add_argument("--output", type=Path, required=True)
    matbench.add_argument("--task", default="matbench_mp_gap")
    spatial = sub.add_parser("spatial-gil", help="Download the official fixed JARVIS Figshare archive and verify its hash")
    spatial.add_argument("--output", type=Path, required=True)
    mp = sub.add_parser("verify-mp-viability", help="Verify an author-supplied frozen Materials Project snapshot directory")
    mp.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "matbench-cache":
        result = build_matbench_cache(args.output.resolve(), args.task)
    elif args.command == "spatial-gil":
        result = acquire_spatial_gil(args.output.resolve())
    else:
        result = verify_mp_viability(args.directory.resolve())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
