import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from app.main import startup_event


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI is not installed in this environment.")
class MainRuntimePrewarmTest(unittest.TestCase):
    def test_startup_schedules_post_deploy_prewarm_on_vercel_production(self):
        with (
            patch("app.main.os.getenv", side_effect=lambda key, default=None: {
                "VERCEL": "1",
                "VERCEL_ENV": "production",
            }.get(key, default)),
            patch("app.main.runtime_prewarm_service.schedule_post_deploy_prewarm", return_value=True) as schedule_mock,
        ):
            startup_event()

        schedule_mock.assert_called_once()
        self.assertEqual(schedule_mock.call_args.kwargs["include_semantic"], True)
        self.assertEqual(schedule_mock.call_args.kwargs["include_benchmark"], True)
        self.assertIn(":", schedule_mock.call_args.kwargs["build_key"])


if __name__ == "__main__":
    unittest.main()
