"""pytest configuration shared across all test modules."""

import os
import sys

# Each function folder is a self-contained deployment package that uses bare
# imports (e.g. `from logging_utils import ...`).  Add them to sys.path so
# those imports resolve correctly when tests run from the repo root.
_ROOT = os.path.dirname(os.path.dirname(__file__))
for _folder in (
    "functions/fridge_report_consumer",
    "functions/get_user_action_stats",
    "functions/user_deletion_handler",
):
    _path = os.path.join(_ROOT, _folder)
    if _path not in sys.path:
        sys.path.append(_path)


def pytest_configure(config):
    """Set env vars before any test module is loaded."""
    os.environ.setdefault("LOG_LEVEL", "WARNING")
    os.environ.setdefault("USER_ACTION_STATS_TABLE", "test")
    os.environ.setdefault("USER_POINTS_HISTORY_TABLE", "test")