from __future__ import annotations

import csv
import json
import math
import zipfile
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
from pymatgen.core import Element, Lattice, Structure
from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .common import public_input_identity


SEED = 20260809
NULL_SEEDS = (20260809, 20260810, 20260811)
EXPECTED_JARVIS_SHA256 = "d4c64660e9e1fa45c82bd8868a96ec10162195eed69636445972c05550d8d0d6"


def _metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(math.sqrt(mean_squared_error(y, pred))),
    }


def _fit(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
    model = Ridge(alpha=1e-6)
    model.fit(x_train, y_train)
    return _metrics(y_test, model.predict(x_test))


def smoke() -> dict[str, Any]:
    x, y = make_regression(n_samples=256, n_features=24, n_informative=9, noise=20.0, random_state=SEED)
    folds = []
    for fold in range(4):
        test = np.arange(fold * 64, (fold + 1) * 64)
        train = np.setdiff1d(np.arange(256), test)
        valid = _fit(x[train], y[train], x[test], y[test])
        null = []
        for seed in NULL_SEEDS:
            rng = np.random.default_rng(seed + fold)
            null.append(_fit(x[train], y[train][rng.permutation(len(train))], x[test], y[test])["r2"])
        folds.append({**valid, "valid_minus_null_r2": valid["r2"] - float(np.median(null))})
    return {
        "route": "spatial-gil",
        "classification": "SYNTHETIC_SPATIAL_MECHANISM_SMOKE_NOT_PUBLISHED_CLAIM",
        "folds": folds,
        "mean_valid_r2": float(np.mean([row["r2"] for row in folds])),
        "mean_valid_minus_null_r2": float(np.mean([row["valid_minus_null_r2"] for row in folds])),
    }


def _primitive(row: dict[str, Any]) -> Structure:
    atoms = row["atoms"]
    lattice = Lattice(np.asarray(atoms["lattice_mat"], dtype=float))
    coords = np.asarray(atoms["coords"], dtype=float)
    fractional = lattice.get_fractional_coords(coords) if atoms.get("cartesian", False) else coords
    return Structure(lattice, atoms["elements"], fractional, coords_are_cartesian=False).get_primitive_structure(tolerance=1e-5)


def _edges(structure: Structure, cutoff: float = 6.0) -> list[list[tuple[int, float, np.ndarray]]]:
    fractional = np.asarray(structure.frac_coords, dtype=float)
    lattice = np.asarray(structure.lattice.matrix, dtype=float)
    lengths = np.linalg.norm(lattice, axis=1)
    limits = tuple(int(math.ceil(cutoff / max(length, 1e-12))) + 1 for length in lengths)
    raw: list[tuple[int, int, tuple[int, int, int], float, np.ndarray]] = []
    for centre in range(len(fractional)):
        for neighbour in range(len(fractional)):
            for image in product(*(range(-limit, limit + 1) for limit in limits)):
                if centre == neighbour and image == (0, 0, 0):
                    continue
                vector = (fractional[neighbour] + np.asarray(image, dtype=float) - fractional[centre]) @ lattice
                distance = float(np.linalg.norm(vector))
                if 1e-10 < distance <= cutoff + 1e-12:
                    raw.append((centre, neighbour, image, distance, vector))
    raw.sort(key=lambda edge: (edge[0], round(edge[3], 12), edge[1], edge[2]))
    result: list[list[tuple[int, float, np.ndarray]]] = []
    for centre in range(len(fractional)):
        local = [edge for edge in raw if edge[0] == centre]
        boundary = local[-1][3] if len(local) <= 12 else local[11][3]
        tolerance = max(1e-10, abs(boundary) * 1e-10)
        result.append([(edge[1], edge[3], edge[4]) for edge in local if edge[3] <= boundary + tolerance])
    return result


def _features(row: dict[str, Any], configuration: str) -> np.ndarray:
    structure = _primitive(row)
    z = np.asarray([site.specie.Z for site in structure], dtype=float)
    masses = np.asarray([float(site.specie.atomic_mass) for site in structure], dtype=float)
    baseline = np.asarray([z.mean(), z.std(), z.min(), z.max(), masses.mean(), masses.std()])
    local = _edges(structure)
    distances = np.asarray([item[1] for shell in local for item in shell], dtype=float)
    c = np.asarray([structure.volume / len(structure), distances.mean(), distances.std(), distances.min(), distances.max()])
    x = np.asarray([Element(str(site.specie)).X for site in structure], dtype=float)
    pair_delta: list[float] = []
    weighted: list[float] = []
    asymmetry: list[float] = []
    local_coord: list[float] = []
    for centre, shell in enumerate(local):
        vector_sum = np.zeros(3, dtype=float)
        local_delta: list[float] = []
        for neighbour, distance, vector in shell:
            delta = abs(float(x[centre] - x[neighbour]))
            pair_delta.append(delta)
            weighted.append(delta / max(distance, 1e-12))
            local_delta.append(delta)
            vector_sum += delta * vector / max(distance, 1e-12)
        asymmetry.append(float(np.linalg.norm(vector_sum)) / max(len(shell), 1))
        local_coord.append(float(np.mean(local_delta)) if local_delta else 0.0)
    p = np.asarray(pair_delta or [0.0]); w = np.asarray(weighted or [0.0])
    a = np.asarray(asymmetry or [0.0]); lc = np.asarray(local_coord or [0.0])
    e = np.asarray([x.mean(), x.std(), np.ptp(x), p.mean(), p.std(), p.max(), w.mean(), w.std(), a.mean(), a.std(), a.max(), lc.mean(), lc.std()])
    blocks = {"BASE": baseline, "C": np.concatenate([baseline, c]), "C_E": np.concatenate([baseline, c, e]), "E": np.concatenate([baseline, e])}
    return blocks[configuration]


def jarvis_probe(dataset: Path, split_csv: Path, target: str = "bulk_modulus_kv", split_view: str = "jid_order_contiguous_4fold", configuration: str = "C") -> dict[str, Any]:
    identity = public_input_identity(dataset)
    if identity["sha256"] != EXPECTED_JARVIS_SHA256:
        raise RuntimeError(f"JARVIS_INPUT_HASH_MISMATCH:{identity['sha256']}")
    with zipfile.ZipFile(dataset) as archive:
        source = json.loads(archive.read(archive.namelist()[0]))
    accepted = [row for row in source if row.get("jid") and row.get("atoms") and row.get("bulk_modulus_kv") is not None and row.get("shear_modulus_gv") is not None]
    accepted.sort(key=lambda row: str(row["jid"]))
    by_jid = {str(row["jid"]): row for row in accepted}
    with split_csv.open("r", encoding="utf-8", newline="") as handle:
        splits = list(csv.DictReader(handle))
    rows = [by_jid[item["jid"]] for item in splits]
    x = np.vstack([_features(row, configuration) for row in rows])
    y = np.asarray([float(row[target]) for row in rows], dtype=float)
    fold_column = "jid_order_fold" if split_view == "jid_order_contiguous_4fold" else "chemical_system_fold"
    fold_results = []
    for fold in range(4):
        test = np.asarray([i for i, item in enumerate(splits) if int(item[fold_column]) == fold])
        train = np.asarray([i for i in range(len(splits)) if i not in set(test.tolist())])
        valid = _fit(x[train], y[train], x[test], y[test])
        null_scores = []
        for seed in NULL_SEEDS:
            order = sorted(range(len(train)), key=lambda local: __import__("hashlib").sha256(f"{seed}|{target}|{split_view}|{fold}|{splits[train[local]]['jid']}".encode()).hexdigest())
            null_scores.append(_fit(x[train], y[train][np.asarray(order)], x[test], y[test])["r2"])
        fold_results.append({**valid, "valid_minus_null_r2": valid["r2"] - float(np.median(null_scores))})
    return {
        "route": "spatial-gil",
        "classification": "BOUNDED_REAL_JARVIS_FITTING_PROBE",
        "input": identity,
        "target": target,
        "split_view": split_view,
        "configuration": configuration,
        "folds": fold_results,
        "mean_valid_r2": float(np.mean([row["r2"] for row in fold_results])),
        "sd_valid_r2": float(np.std([row["r2"] for row in fold_results], ddof=1)),
        "mean_valid_mae": float(np.mean([row["mae"] for row in fold_results])),
        "mean_valid_rmse": float(np.mean([row["rmse"] for row in fold_results])),
        "mean_valid_minus_null_r2": float(np.mean([row["valid_minus_null_r2"] for row in fold_results])),
        "positive_null_gap_folds": int(sum(row["valid_minus_null_r2"] > 0 for row in fold_results)),
    }


def compare_expected(result: dict[str, Any], expected_csv: Path, tolerance: float = 1e-10) -> dict[str, Any]:
    with expected_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = next(
        row for row in rows
        if row["target"] == result["target"]
        and row["split_view"] == result["split_view"]
        and row["configuration"] == result["configuration"]
    )
    numeric = ("mean_valid_r2", "sd_valid_r2", "mean_valid_mae", "mean_valid_rmse", "mean_valid_minus_null_r2")
    deltas = {name: float(result[name]) - float(expected[name]) for name in numeric}
    fold_match = int(result["positive_null_gap_folds"]) == int(expected["positive_null_gap_folds"])
    return {
        "tolerance": tolerance,
        "numeric_deltas": deltas,
        "positive_null_gap_folds_match": fold_match,
        "pass": all(abs(value) <= tolerance for value in deltas.values()) and fold_match,
    }
