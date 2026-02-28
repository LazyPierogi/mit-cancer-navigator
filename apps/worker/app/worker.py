from __future__ import annotations

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[3]
    manifest = {
        "worker": "navigator-worker",
        "status": "idle",
        "datasets": sorted(str(path.relative_to(root)) for path in (root / "datasets").rglob("*.json")),
    }
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
