import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    import app.repositories.bootstrap as bootstrap_module


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "SQLAlchemy is not installed in this environment.")
class BootstrapDatabaseTest(unittest.TestCase):
    def test_bootstrap_skips_schema_work_for_ready_postgres_schema(self):
        session = MagicMock()
        session.execute.side_effect = [
            _ScalarResult(object()),
            _ScalarResult(object()),
            _ScalarResult(object()),
        ]
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session

        with (
            patch.object(bootstrap_module, "_BOOTSTRAP_COMPLETE", False),
            patch.object(bootstrap_module.settings, "database_url", "postgresql+psycopg://example"),
            patch.object(bootstrap_module, "_postgres_runtime_schema_ready", return_value=True),
            patch.object(bootstrap_module.Base.metadata, "create_all") as create_all_mock,
            patch.object(bootstrap_module, "_ensure_runtime_schema_extensions") as ensure_mock,
            patch.object(bootstrap_module, "SessionLocal", session_factory),
        ):
            bootstrap_module.bootstrap_database()

        create_all_mock.assert_not_called()
        ensure_mock.assert_not_called()
        session.add.assert_not_called()
        session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
