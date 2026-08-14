from __future__ import annotations

from pathlib import Path

from src import matbench_importance, mp_viability, spatial_gil


def test_matbench_importance_smoke() -> None:
    result = matbench_importance.smoke()
    assert result["features_probed"] == 6
    assert -1.0 <= result["spearman_permutation_vs_retrained_removal"] <= 1.0


def test_mp_viability_smoke() -> None:
    result = mp_viability.smoke()
    assert result["null_repetitions"] == 8
    assert isinstance(result["both_gates"], bool)


def test_spatial_gil_smoke() -> None:
    result = spatial_gil.smoke()
    assert len(result["folds"]) == 4
    assert all("valid_minus_null_r2" in row for row in result["folds"])


def test_spatial_gil_expected_comparison(tmp_path: Path) -> None:
    expected = tmp_path / "expected.csv"
    expected.write_text(
        "target,split_view,configuration,mean_valid_r2,sd_valid_r2,mean_valid_mae,mean_valid_rmse,mean_valid_minus_null_r2,positive_null_gap_folds\n"
        "bulk_modulus_kv,jid_order_contiguous_4fold,C,0.4,0.1,2.0,3.0,0.5,4\n",
        encoding="utf-8",
    )
    result = {
        "target": "bulk_modulus_kv", "split_view": "jid_order_contiguous_4fold", "configuration": "C",
        "mean_valid_r2": 0.4, "sd_valid_r2": 0.1, "mean_valid_mae": 2.0,
        "mean_valid_rmse": 3.0, "mean_valid_minus_null_r2": 0.5, "positive_null_gap_folds": 4,
    }
    assert spatial_gil.compare_expected(result, expected)["pass"] is True
