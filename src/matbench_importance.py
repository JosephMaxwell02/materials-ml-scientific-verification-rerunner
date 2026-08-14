from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr
from sklearn.datasets import make_regression
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


SEED = 11


def _model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", MLPRegressor(
            hidden_layer_sizes=(128, 64), alpha=1e-4,
            learning_rate_init=1e-3, max_iter=300,
            early_stopping=True, validation_fraction=0.15,
            n_iter_no_change=20, random_state=SEED,
        )),
    ])


def _score(model: Any, x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    pred = model.predict(x)
    return {"mae": float(mean_absolute_error(y, pred)), "r2": float(r2_score(y, pred))}


def _analyse(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray, feature_names: list[str], limit: int) -> dict[str, Any]:
    baseline_model = _model()
    baseline_model.fit(x_train, y_train)
    baseline = _score(baseline_model, x_test, y_test)
    count = min(limit, x_train.shape[1])
    permutation: list[float] = []
    removal: list[float] = []
    for index in range(count):
        shuffled = np.asarray(x_test, dtype=float).copy()
        token = hashlib.sha256(f"{SEED}|matbench-importance|{index}".encode()).hexdigest()
        rng = np.random.default_rng(int(token[:8], 16))
        shuffled[:, index] = shuffled[rng.permutation(len(shuffled)), index]
        permutation.append(_score(baseline_model, shuffled, y_test)["mae"] - baseline["mae"])
        keep = np.ones(x_train.shape[1], dtype=bool)
        keep[index] = False
        removed_model = _model()
        removed_model.fit(x_train[:, keep], y_train)
        removal.append(_score(removed_model, x_test[:, keep], y_test)["mae"] - baseline["mae"])
    rho, _ = spearmanr(permutation, removal)
    return {
        "baseline": baseline,
        "features_total": int(x_train.shape[1]),
        "features_probed": count,
        "feature_names_probed": feature_names[:count],
        "permutation_mae_increase": permutation,
        "retrained_removal_mae_increase": removal,
        "spearman_permutation_vs_retrained_removal": float(rho),
    }


def smoke() -> dict[str, Any]:
    x, y = make_regression(n_samples=360, n_features=20, n_informative=8, noise=12.0, random_state=991)
    return {
        "route": "matbench-importance",
        "classification": "SYNTHETIC_MECHANISM_SMOKE_NOT_PUBLISHED_CLAIM",
        **_analyse(x[:280], y[:280], x[280:], y[280:], [f"f{i}" for i in range(20)], 6),
    }


def matbench_probe(task_name: str = "matbench_mp_gap", fold: int = 0, train_rows: int = 320, test_rows: int = 96, feature_limit: int = 3) -> dict[str, Any]:
    from matbench.bench import MatbenchBenchmark
    from matminer.featurizers.composition import ElementProperty, Stoichiometry, ValenceOrbital
    from pymatgen.core import Composition

    benchmark = MatbenchBenchmark(autoload=False, subset=[task_name])
    task = list(benchmark.tasks)[0]
    task.load()
    train_inputs, train_targets = task.get_train_and_val_data(fold)
    test_inputs, test_targets = task.get_test_data(fold, include_target=True)
    train_inputs, train_targets = list(train_inputs)[:train_rows], np.asarray(train_targets)[:train_rows]
    test_inputs, test_targets = list(test_inputs)[:test_rows], np.asarray(test_targets)[:test_rows]
    featurizers = [ElementProperty.from_preset("magpie"), Stoichiometry(), ValenceOrbital(props=["avg"])]
    names = [label for item in featurizers for label in item.feature_labels()]

    def vector(value: Any) -> list[float]:
        comp = value.composition if hasattr(value, "composition") else Composition(str(value))
        return [float(v) for item in featurizers for v in item.featurize(comp)]

    x_train = np.asarray([vector(value) for value in train_inputs], dtype=float)
    x_test = np.asarray([vector(value) for value in test_inputs], dtype=float)
    return {
        "route": "matbench-importance",
        "classification": "BOUNDED_REAL_MATBENCH_FITTING_PROBE_NOT_FULL_CAMPAIGN",
        "task": task_name,
        "fold": fold,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        **_analyse(x_train, train_targets, x_test, test_targets, names, feature_limit),
    }


def matbench_exact_probe(cache_root: Path, task_name: str = "matbench_mp_gap", fold: int = 0, feature_index: int = 0) -> dict[str, Any]:
    from matbench.bench import MatbenchBenchmark

    benchmark = MatbenchBenchmark(autoload=False, subset=[task_name])
    task = list(benchmark.tasks)[0]
    task.load()
    cache = cache_root / task.dataset_name
    array_path = cache / "full_features.npz"
    meta_path = cache / "full_features.json"
    if not array_path.is_file() or not meta_path.is_file():
        raise RuntimeError(
            "MATBENCH_FULL_FEATURE_CACHE_REQUIRED: generate the frozen 142-feature cache before the exact computation"
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    full_x = np.load(array_path, allow_pickle=False)["x"]
    names = list(meta["feature_names"])
    if full_x.shape[1] != 142 or len(names) != 142:
        raise RuntimeError(f"MATBENCH_FEATURE_REGISTRY_MISMATCH:{full_x.shape}:{len(names)}")
    positions = {str(sample_id): pos for pos, sample_id in enumerate(task.df.index.tolist())}
    fold_key = task.folds_map[fold]
    train_ids = [str(value) for value in task.validation[fold_key].train]
    test_ids = [str(value) for value in task.validation[fold_key].test]
    train_pos = [positions[value] for value in train_ids]
    test_pos = [positions[value] for value in test_ids]
    target = task.metadata["target"]
    y_train = np.asarray(task.df.loc[train_ids, target].tolist())
    y_test = np.asarray(task.df.loc[test_ids, target].tolist())
    x_train, x_test = full_x[train_pos], full_x[test_pos]
    baseline_model = _model()
    baseline_model.fit(x_train, y_train)
    baseline = _score(baseline_model, x_test, y_test)
    keep = np.ones(full_x.shape[1], dtype=bool)
    keep[feature_index] = False
    removal_model = _model()
    removal_model.fit(x_train[:, keep], y_train)
    removal = _score(removal_model, x_test[:, keep], y_test)
    return {
        "route": "matbench-importance",
        "classification": "BOUNDED_EXACT_MATBENCH_FITTING_PROBE",
        "task": task_name,
        "fold": fold,
        "train_rows": len(train_ids),
        "test_rows": len(test_ids),
        "feature_index_removed": feature_index,
        "feature_removed": names[feature_index],
        "baseline": baseline,
        "removal": removal,
        "retrained_removal_mae_increase": removal["mae"] - baseline["mae"],
        "cache_identity": {
            "feature_sha256": meta.get("feature_sha256"),
            "feature_names_sha256": meta.get("feature_names_sha256"),
        },
    }


def compare_expected(result: dict[str, Any], expected_json: Path, tolerance: float = 1e-10) -> dict[str, Any]:
    expected = json.loads(expected_json.read_text(encoding="utf-8"))
    deltas = {
        "baseline_mae": result["baseline"]["mae"] - expected["baseline"]["mae"],
        "baseline_r2": result["baseline"]["r2"] - expected["baseline"]["r2"],
        "removal_mae": result["removal"]["mae"] - expected["removal"]["mae"],
        "removal_r2": result["removal"]["r2"] - expected["removal"]["r2"],
    }
    identities = {
        "feature_sha256": result["cache_identity"].get("feature_sha256") == expected["feature_sha256"],
        "feature_names_sha256": result["cache_identity"].get("feature_names_sha256") == expected["feature_names_sha256"],
    }
    return {
        "tolerance": tolerance,
        "observed_reference_difference": deltas,
        "identity_matches": identities,
        "pass": all(abs(value) <= tolerance for value in deltas.values()) and all(identities.values()),
    }
