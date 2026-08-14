from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import matbench_importance, mp_viability, spatial_gil
from src.common import ROOT, write_receipt


ROUTES = ("matbench-importance", "mp-viability", "spatial-gil")
RECEIPT_NAMES = {
    "matbench-importance": "MATBENCH_IMPORTANCE_COMPUTED_RECEIPT",
    "mp-viability": "MP_VIABILITY_COMPUTED_RECEIPT",
    "spatial-gil": "SPATIAL_GIL_COMPUTED_RECEIPT",
}


def compute(route: str, dataset: Path | None, cache: Path | None) -> dict:
    if route == "matbench-importance":
        return matbench_importance.matbench_exact_probe(cache) if cache else matbench_importance.matbench_probe()
    if route == "mp-viability":
        if dataset is None:
            raise RuntimeError("MP_VIABILITY_DATASET_REQUIRED")
        return mp_viability.snapshot_probe(dataset)
    if dataset is None:
        raise RuntimeError("SPATIAL_GIL_DATASET_REQUIRED")
    split_csv = ROOT / "protocols" / "spatial-gil" / "SPATIAL_GIL_V0_6_SPLIT_MEMBERSHIP.csv"
    return spatial_gil.jarvis_probe(dataset, split_csv)


def verify(result: dict) -> dict:
    route = result.get("route")
    if route == "matbench-importance":
        expected = ROOT / "expected" / "MATBENCH_IMPORTANCE_REFERENCE_PROBE.json"
        return matbench_importance.compare_expected(result, expected)
    if route == "mp-viability":
        expected = ROOT / "expected" / "PAPER2_ELASTIC_NULL_COMPARABLE_CELLS.csv"
        return mp_viability.compare_expected(result, expected)
    if route == "spatial-gil":
        expected = ROOT / "expected" / "SPATIAL_GIL_V0_6_1_SCIENTIFIC_RESULT_TABLE.csv"
        return spatial_gil.compare_expected(result, expected)
    raise RuntimeError(f"UNKNOWN_ROUTE:{route}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone scientific verification rerunner for Materials ML Failure Analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("smoke", help="Run deterministic synthetic mechanism checks")
    compute_parser = sub.add_parser("compute", help="Compute a bounded real-data result without loading frozen expected outputs")
    compute_parser.add_argument("--route", choices=ROUTES, required=True)
    compute_parser.add_argument("--dataset", type=Path)
    compute_parser.add_argument("--cache", type=Path, help="Matbench feature-cache root for the exact reference computation")
    verify_parser = sub.add_parser("verify", help="Compare an existing computed receipt with frozen expected evidence")
    verify_parser.add_argument("--receipt", type=Path, required=True)
    full_parser = sub.add_parser("full", help="Emit a structured refusal for an unavailable complete campaign")
    full_parser.add_argument("--route", choices=ROUTES, required=True)
    args = parser.parse_args()

    if args.command == "smoke":
        results = [matbench_importance.smoke(), mp_viability.smoke(), spatial_gil.smoke()]
        path = write_receipt("SMOKE_RECEIPT", {"decision": "PASS", "mode": "smoke", "results": results})
        status = "PASS"
    elif args.command == "compute":
        result = compute(args.route, args.dataset, args.cache)
        path = write_receipt(RECEIPT_NAMES[args.route], {"decision": "COMPUTED_NOT_YET_VERIFIED", "mode": "compute", "result": result})
        status = "COMPUTED"
    elif args.command == "verify":
        payload = json.loads(args.receipt.read_text(encoding="utf-8"))
        result = payload["result"]
        comparison = verify(result)
        status = "PASS" if comparison["pass"] else "FAIL"
        path = write_receipt(f"{result['route'].replace('-', '_').upper()}_VERIFICATION_RECEIPT", {
            "decision": status,
            "mode": "verify",
            "computed_receipt": args.receipt.name,
            "route": result["route"],
            "comparison": comparison,
        })
        if status != "PASS":
            raise RuntimeError(f"EXPECTED_RESULT_MISMATCH:{result['route']}")
    else:
        refusal = {
            "decision": "REFUSED",
            "mode": "full",
            "route": args.route,
            "reason": "FULL_PUBLICATION_CAMPAIGN_NOT_BOUND",
            "missing": "all frozen third-party inputs, complete campaign plans and full expected-output contracts",
        }
        path = write_receipt("FULL_CAMPAIGN_REFUSAL_RECEIPT", refusal)
        status = "REFUSED"
    print(json.dumps({"receipt": str(path), "status": status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
