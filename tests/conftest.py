"""pytest configuration shared across all test modules."""

import os


def pytest_configure(config):
    """Set env vars before any test module is loaded."""
    os.environ.setdefault("LOG_LEVEL", "WARNING")
