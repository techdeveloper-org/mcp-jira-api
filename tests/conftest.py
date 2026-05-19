"""
conftest.py -- Shared pytest fixtures for mcp-jira-api test suite.

Provides fixture_loader helper and jira_env fixture for unit tests.
Integration tests must be marked with @pytest.mark.integration.

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import os
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fixture_loader(category, name):
    """Load a JSON fixture file from tests/fixtures/{category}/{name}.json.

    Args:
        category: Subdirectory name (agile or rest).
        name: Fixture filename without .json extension.

    Returns:
        Parsed JSON dict.
    """
    path = FIXTURES_DIR / category / (name + ".json")
    with open(path, "r") as f:
        return json.load(f)


@pytest.fixture
def jira_env(monkeypatch):
    """Set required Jira environment variables for unit tests.

    Args:
        monkeypatch: pytest monkeypatch fixture.
    """
    monkeypatch.setenv("JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_USER", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token-ascii-only")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as requiring live Jira")


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if JIRA_URL env var not set."""
    if not os.environ.get("JIRA_URL"):
        skip_int = pytest.mark.skip(reason="JIRA_URL not set -- skipping integration test")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_int)
