"""
X-Twitter MCP - Comprehensive Twitter/X API access with permission-based profiles.

Configuration via environment variables:
- X_MCP_PROFILE: researcher|creator|manager|automation|custom (default: researcher)
- X_MCP_GROUPS: comma-separated groups for custom profile
- X_MCP_DISABLED_TOOLS: comma-separated tools to disable
- X_MCP_ENABLED_TOOLS: comma-separated tools to force-enable

Profiles:
- researcher: Read-only (search, get users/tweets, trends, articles)
- creator: + engage (like, bookmark, retweet) + publish (post, thread)
- manager: + social (follow, block, mute) + lists
- automation: Full access including DMs
- custom: Specify your own groups

Tool Groups:
- research: Search, lookup, timelines (read-only)
- engage: Like, bookmark, retweet
- publish: Post, delete, threads, polls
- social: Follow, block, mute
- conversations: Threads, replies
- lists: Create/manage lists
- dms: Direct messages
- account: Profile management
"""

from .config import (
    ToolGroup,
    Profile,
    TOOL_GROUPS,
    PROFILES,
    PROFILE_DESCRIPTIONS,
    GROUP_DESCRIPTIONS,
    PermissionManager,
    get_permission_manager,
    is_tool_enabled,
)

from .server import server, run

__version__ = "0.2.1"
__all__ = [
    # Main entry point
    "main",
    "run",
    "server",
    # Configuration
    "ToolGroup",
    "Profile",
    "TOOL_GROUPS",
    "PROFILES",
    "PROFILE_DESCRIPTIONS",
    "GROUP_DESCRIPTIONS",
    "PermissionManager",
    "get_permission_manager",
    "is_tool_enabled",
]


def main():
    """Main entry point for the package."""
    return run()
