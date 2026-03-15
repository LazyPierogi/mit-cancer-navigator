from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_APP_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_APP_ROOT))

from app.services.import_pipeline import import_pipeline_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the validate -> normalize -> ingest import pipeline.")
    parser.add_argument("--dataset", choices=["esmo", "pubmed"], required=True, help="Dataset kind to import.")
    parser.add_argument("--path", help="Optional path to the dataset file. Defaults to the canonical preview file.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = import_pipeline_service.import_dataset(dataset_kind=args.dataset, path=args.path)

    if args.format == "json":
        print(json.dumps(result, indent=2, default=str, ensure_ascii=True))
    else:
        print(f"batchId: {result['batchId']}")
        print(f"datasetKind: {result['datasetKind']}")
        print(f"status: {result['status']}")
        print(f"sourcePath: {result['sourcePath']}")
        print(f"recordCount: {result['recordCount']}")
        print(f"importedCount: {result['importedCount']}")
        print(f"errors: {result['errorCount']} | warnings: {result['warningCount']}")
        for note in result["notes"]:
            print(f"note: {note}")

    return 0 if result["status"] in {"completed", "completed_with_warnings"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
