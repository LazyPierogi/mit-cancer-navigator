import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import versioning


class VersioningTest(unittest.TestCase):
    def test_package_local_manifest_is_loaded_when_available(self):
        with TemporaryDirectory() as tmp_dir:
            manifest_path = Path(tmp_dir) / "VERSION.json"
            manifest_path.write_text(
                '{"productVersion":"1.2.3","uiVersion":"1.2.3","backendVersion":"1.2.3","rulesetVersion":"rules","corpusVersion":"corpus","releaseDate":"2026-03-13","buildLabel":"package-manifest","notes":[]}',
                encoding="utf-8",
            )
            versioning.load_version_manifest.cache_clear()
            with patch.object(versioning, "VERSION_PATH_CANDIDATES", (manifest_path,)):
                manifest = versioning.load_version_manifest()

        self.assertEqual(manifest["backendVersion"], "1.2.3")
        self.assertEqual(manifest["buildLabel"], "package-manifest")
        versioning.load_version_manifest.cache_clear()

    def test_missing_manifest_uses_runtime_defaults_instead_of_unknown(self):
        versioning.load_version_manifest.cache_clear()
        with patch.object(versioning, "VERSION_PATH_CANDIDATES", tuple()):
            manifest = versioning.load_version_manifest()

        self.assertEqual(manifest["rulesetVersion"], "mvp-2026-02-28")
        self.assertEqual(manifest["corpusVersion"], "canonical-frozen-pack-v2")
        self.assertNotEqual(manifest["buildLabel"], "unknown")

        versioning.load_version_manifest.cache_clear()


if __name__ == "__main__":
    unittest.main()
