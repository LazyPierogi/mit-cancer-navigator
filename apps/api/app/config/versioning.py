from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
VERSION_PATH_CANDIDATES = (
    REPO_ROOT / "VERSION.json",
    PACKAGE_ROOT / "VERSION.json",
)


@lru_cache(maxsize=1)
def load_version_manifest() -> dict[str, object]:
    version_path = next((candidate for candidate in VERSION_PATH_CANDIDATES if candidate.exists()), None)
    if version_path is None:
        return {
            "productVersion": "0.0.0",
            "uiVersion": "0.0.0",
            "backendVersion": "0.0.0",
            "rulesetVersion": os.getenv("RULESET_VERSION", "mvp-2026-02-28"),
            "corpusVersion": os.getenv("CORPUS_VERSION", "canonical-frozen-pack-v2"),
            "releaseDate": None,
            "buildLabel": os.getenv("BUILD_LABEL", "runtime-fallback"),
            "notes": [],
        }
    return json.loads(version_path.read_text(encoding="utf-8"))
