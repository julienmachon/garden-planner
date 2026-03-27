"""
Contract tests for the MCP server.

These tests verify that all expected tools are registered and accessible.
If a tool is accidentally renamed or removed, these tests will catch it
before the change reaches users.
"""
import asyncio

import pytest

from garden_planner.server import mcp

# The full set of tools users depend on.
# Adding a new tool is fine — removing or renaming one is a breaking change.
EXPECTED_TOOLS = {
    "add_planting_material",
    "list_planting_materials",
    "log_planting",
    "log_transplant",
    "log_event",
    "log_harvest",
    "end_planting",
    "get_planting_history",
    "list_active_plantings",
    "get_season_summary",
    "search_plantings",
}


@pytest.fixture
def registered_tools():
    return {t.name for t in asyncio.run(mcp.list_tools())}


def test_no_expected_tools_missing(registered_tools):
    missing = EXPECTED_TOOLS - registered_tools
    assert not missing, f"Tools removed or renamed (breaking change): {missing}"


def test_no_unexpected_tools_added_silently(registered_tools):
    # Not a hard failure — just a reminder to update EXPECTED_TOOLS
    # when a new tool is intentionally added.
    new_tools = registered_tools - EXPECTED_TOOLS
    assert not new_tools, (
        f"New tools registered but not listed in EXPECTED_TOOLS: {new_tools}\n"
        "If intentional, add them to EXPECTED_TOOLS in this file."
    )
