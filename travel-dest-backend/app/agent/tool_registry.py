"""Explicit tool allowlist and dispatch helpers for the travel planner agent."""

from collections.abc import Awaitable, Callable
from typing import Any


TOOL_ALLOWLIST = {
    "retrieve_destinations",
    "classify_travel_style",
    "get_live_conditions",
}


def ensure_allowed_tool(tool_name: str) -> None:
    """Refuse any invented tool name outside the required allowlist."""
    if tool_name not in TOOL_ALLOWLIST:
        raise ValueError(f"Tool '{tool_name}' is not allowed.")


async def dispatch_tool(
    tool_name: str,
    runner: Callable[[], Awaitable[Any]],
) -> Any:
    """Validate one tool name and then execute it."""
    ensure_allowed_tool(tool_name)
    return await runner()

