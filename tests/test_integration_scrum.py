"""
test_integration_scrum.py -- Integration tests for Scrum Master tools.

All tests in this module are marked @pytest.mark.integration.
They are SKIPPED automatically in CI unless JIRA_URL is set.
Requires all three environment variables:
  JIRA_URL, JIRA_USER, JIRA_API_TOKEN

Windows-Safe: ASCII only (cp1252 compatible)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.mark.integration
def test_jira_health_check_live(jira_env):
    """Verify live Jira connection using env vars.

    Args:
        jira_env: pytest fixture setting JIRA_URL, JIRA_USER, JIRA_API_TOKEN.
    """
    import server
    result = server.jira_health_check()
    assert result.get("connected") is True
    assert "version" in result
    assert len(result.get("jira_url", "")) > 0


@pytest.mark.integration
def test_jira_get_boards_live(jira_env):
    """Verify boards are returned from a live Jira Software instance.

    Args:
        jira_env: pytest fixture setting Jira environment variables.
    """
    import server
    result = server.jira_get_boards(max_results=5)
    assert "boards" in result
    assert isinstance(result["boards"], list)
    assert "total" in result


@pytest.mark.integration
def test_jira_get_velocity_live(jira_env):
    """Verify velocity data is returned from the live Agile API.

    Requires at least one Scrum board with closed sprints.

    Args:
        jira_env: pytest fixture setting Jira environment variables.
    """
    import server
    boards_result = server.jira_get_boards(max_results=1)
    if not boards_result.get("boards"):
        pytest.skip("No boards available for live velocity test")

    board_id = boards_result["boards"][0]["board_id"]
    result = server.jira_get_velocity(board_id=board_id, num_sprints=3)

    assert "velocity_history" in result
    assert result["board_id"] == board_id


@pytest.mark.integration
def test_jira_get_sprints_live(jira_env):
    """Verify sprint list is returned from the live Agile API.

    Args:
        jira_env: pytest fixture setting Jira environment variables.
    """
    import server
    boards_result = server.jira_get_boards(max_results=1)
    if not boards_result.get("boards"):
        pytest.skip("No boards available for live sprint test")

    board_id = boards_result["boards"][0]["board_id"]
    result = server.jira_get_sprints(board_id=board_id, max_results=5)

    assert "sprints" in result
    assert result["board_id"] == board_id


@pytest.mark.integration
def test_jira_team_health_live(jira_env):
    """Verify team health report from live Agile API.

    Args:
        jira_env: pytest fixture setting Jira environment variables.
    """
    import server
    boards_result = server.jira_get_boards(max_results=1)
    if not boards_result.get("boards"):
        pytest.skip("No boards available for live team health test")

    board_id = boards_result["boards"][0]["board_id"]
    result = server.jira_team_health(board_id=board_id, num_sprints=3)

    valid_stages = {"Forming", "Storming", "Norming", "Performing"}
    assert result.get("tuckman_stage") in valid_stages
    assert "health_summary" in result
