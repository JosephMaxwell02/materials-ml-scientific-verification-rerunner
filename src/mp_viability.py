from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.datasets import make_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .common import public_input_identity


SEED = 23
EXPECTED_SNAPSHOT_SHA256 = "e02083989c5f0dc029408eaf4b8634fe5557241a06e8e3ebd10c27693fa26b62"
COMMON_DESCRIPTORS = [
    "density", "volume_per_atom", "nsites", "total_magnetization",
    "lattice_a", "lattice_b", "lattice_c", "lattice_alpha",
    "lattice_beta", "lattice_gamma", "symmetry_crystal_system",
]


def _fit_scores(x: np.ndarray, y: np.ndarray, split: int, null_repetitions: int) -> dict[str, Any]:
    x_train, x_test = x[:split], x[split:]
    y_train, y_test = y[:split], y[split:]
    model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", Ridge(alpha=1.0)),
    ])
    model.fit(x_train, y_train)
    baseline_r2 = float(r2_score(y_test, model.predict(x_test)))
    null_scores: list[float] = []
    for repetition in range(null_repetitions):
        rng = np.random.default_rng(SEED * 1000 + repetition)
        shuffled = y_train[rng.permutation(len(y_train))]
        candidate = Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ])
        candidate.fit(x_train, shuffled)
        null_scores.append(float(r2_score(y_test, candidate.predict(x_test))))
    null_mean = float(np.mean(null_scores))
    return {
        "baseline_r2": baseline_r2,
        "target_permutation_r2_mean": null_mean,
        "r2_minus_null": baseline_r2 - null_mean,
        "positive_absolute_r2": baseline_r2 > 0,
        "positive_non_null_signal": baseline_r2 - null_mean > 0,
        "both_gates": baseline_r2 > 0 and baseline_r2 - null_mean > 0,
        "null_repetitions": null_repetitions,
    }


def smoke() -> dict[str, Any]:
    x, y = make_regression(n_samples=420, n_features=16, n_informative=5, noise=80.0, random_state=SEED)
    return {
        "route": "mp-viability",
        "classification": "SYNTHETIC_TWO_GATE_SMOKE_NOT_PUBLISHED_CLAIM",
        **_fit_scores(x, y, 320, 8),
    }


def _pipeline() -> Pipeline:
    preprocessing = ColumnTransformer([
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), [name for name in COMMON_DESCRIPTORS if name != "symmetry_crystal_system"]),
        ("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), ["symmetry_crystal_system"]),
    ])
    return Pipeline([("preprocessing", preprocessing), ("model", Ridge(alpha=1.0))])


def snapshot_probe(snapshot: Path) -> dict[str, Any]:
    identity = public_input_identity(snapshot)
    if identity["sha256"] != EXPECTED_SNAPSHOT_SHA256:
        raise RuntimeError(f"MATERIALS_PROJECT_INPUT_HASH_MISMATCH:{identity['sha256']}")
    membership_path = snapshot.parent / "COHORT_MEMBERSHIP.csv"
    splits_path = snapshot.parent / "SPLIT_MEMBERSHIP.csv"
    if not membership_path.is_file() or not splits_path.is_file():
        raise RuntimeError("MP_VIABILITY_MEMBERSHIP_OR_SPLIT_FILE_MISSING")

    target = "bulk_modulus"
    usecols = ["record_id", target, *COMMON_DESCRIPTORS]
    frame = pd.read_csv(snapshot, usecols=usecols)
    membership = pd.read_csv(
        membership_path,
        usecols=["source", "record_id", "target", "within_source_common"],
    )
    selected = membership.loc[
        (membership["source"] == "materials_project")
        & (membership["target"] == target)
        & (membership["within_source_common"] == 1),
        "record_id",
    ]
    frame = frame.loc[frame["record_id"].isin(set(selected))].copy()
    splits = pd.read_csv(
        splits_path,
        usecols=["source", "record_id", "row_random_seed_11"],
    )
    frame = frame.merge(
        splits.loc[splits["source"] == "materials_project", ["record_id", "row_random_seed_11"]],
        on="record_id",
        validate="one_to_one",
    )
    train = frame.loc[frame["row_random_seed_11"] == "train"]
    test = frame.loc[frame["row_random_seed_11"] == "test"]
    model = _pipeline()
    model.fit(train[COMMON_DESCRIPTORS], train[target])
    baseline_prediction = model.predict(test[COMMON_DESCRIPTORS])
    baseline_r2 = float(r2_score(test[target], baseline_prediction))
    null_scores: list[float] = []
    for repetition in range(30):
        shuffled = train[target].sample(frac=1.0, random_state=11 * 1000 + repetition).to_numpy()
        null_model = _pipeline()
        null_model.fit(train[COMMON_DESCRIPTORS], shuffled)
        null_scores.append(float(r2_score(test[target], null_model.predict(test[COMMON_DESCRIPTORS]))))
    null_mean = float(np.mean(null_scores))
    return {
        "route": "mp-viability",
        "classification": "BOUNDED_REAL_MATERIALS_PROJECT_FITTING_PROBE",
        "input": identity,
        "target": target,
        "cohort": "within_source_common",
        "lane": "causal_common",
        "split_view": "row_random",
        "seed": 11,
        "model": "ridge",
        "rows": len(frame),
        "baseline_r2": baseline_r2,
        "baseline_mae": float(mean_absolute_error(test[target], baseline_prediction)),
        "target_permutation_r2_mean": null_mean,
        "r2_minus_null": baseline_r2 - null_mean,
        "null_repetitions": 30,
    }


def compare_expected(result: dict[str, Any], expected_csv: Path, tolerance: float = 1e-10) -> dict[str, Any]:
    with expected_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = next(
        row for row in rows
        if row["target"] == result["target"]
        and row["cohort"] == result["cohort"]
        and row["lane"] == result["lane"]
        and row["split_view"] == result["split_view"]
        and int(row["seed"]) == int(result["seed"])
        and row["model"] == result["model"]
    )
    numeric = ("baseline_r2", "baseline_mae", "target_permutation_r2_mean", "r2_minus_null")
    deltas = {name: float(result[name]) - float(expected[name]) for name in numeric}
    rows_match = int(result["rows"]) == int(expected["rows"])
    return {
        "tolerance": tolerance,
        "numeric_deltas": deltas,
        "row_count_match": rows_match,
        "pass": all(abs(value) <= tolerance for value in deltas.values()) and rows_match,
    }
