"""
XMCP Configuration

Defines tool groups, profiles, and permission management.
"""

import os
from typing import Set, List, Dict, Tuple
from enum import Enum

class ToolGroup(str, Enum):
    """Tool groups that can be enabled/disabled."""
    RESEARCH = "research"
    ENGAGE = "engage"
    PUBLISH = "publish"
    SOCIAL = "social"
    CONVERSATIONS = "conversations"
    LISTS = "lists"
    DMS = "dms"
    ACCOUNT = "account"

class Profile(str, Enum):
    """Preset profiles for common use cases."""
    RESEARCHER = "researcher"
    CREATOR = "creator"
    MANAGER = "manager"
    AUTOMATION = "automation"
    CUSTOM = "custom"

# Tool group definitions - which tools belong to which group
TOOL_GROUPS: Dict[ToolGroup, List[str]] = {
    ToolGroup.RESEARCH: [
        # Search & Discovery
        "search_twitter",
        "search_articles",
        "get_trends",
        "get_article",
        # User lookup
        "get_user_profile",
        "get_user_by_screen_name",
        "get_user_by_id",
        "get_user_followers",
        "get_user_following",
        "get_user_followers_you_know",
        "get_user_subscriptions",
        # Tweet lookup
        "get_tweet_details",
        "get_user_tweets",
        "get_liked_tweets",
        # Timeline (read)
        "get_timeline",
        "get_latest_timeline",
        "get_user_mentions",
        "get_highlights_tweets",
    ],
    ToolGroup.ENGAGE: [
        # Likes
        "favorite_tweet",
        "unfavorite_tweet",
        # Bookmarks
        "bookmark_tweet",
        "delete_bookmark",
        "delete_all_bookmarks",
        "get_bookmarks",
        # Retweets
        "retweet",
        "unretweet",
        "get_retweets",
    ],
    ToolGroup.PUBLISH: [
        # Tweet creation
        "post_tweet",
        "delete_tweet",
        "quote_tweet",
        "create_thread",
        # Polls
        "create_poll_tweet",
        "vote_on_poll",
        # Scheduled (future)
        "schedule_tweet",
        "get_scheduled_tweets",
        "delete_scheduled_tweet",
    ],
    ToolGroup.SOCIAL: [
        # Follow
        "follow_user",
        "unfollow_user",
        # Block
        "block_user",
        "unblock_user",
        "get_blocked_users",
        # Mute
        "mute_user",
        "unmute_user",
        "get_muted_users",
    ],
    ToolGroup.CONVERSATIONS: [
        # Thread/conversation
        "get_conversation",
        "get_replies",
        "get_quote_tweets",
        # Reply management
        "hide_reply",
        "unhide_reply",
    ],
    ToolGroup.LISTS: [
        # List CRUD
        "create_list",
        "delete_list",
        "update_list",
        "get_list",
        "get_user_lists",
        "get_list_tweets",
        # List members
        "get_list_members",
        "add_list_member",
        "remove_list_member",
        # List following
        "follow_list",
        "unfollow_list",
        "pin_list",
        "unpin_list",
    ],
    ToolGroup.DMS: [
        "send_dm",
        "get_dm_conversations",
        "get_dm_events",
        "delete_dm",
    ],
    ToolGroup.ACCOUNT: [
        "get_me",
        "update_profile",
        "update_profile_image",
        "update_banner",
    ],
}

# Profile definitions - which groups each profile enables
PROFILES: Dict[Profile, List[ToolGroup]] = {
    Profile.RESEARCHER: [
        ToolGroup.RESEARCH,
        ToolGroup.CONVERSATIONS,
    ],
    Profile.CREATOR: [
        ToolGroup.RESEARCH,
        ToolGroup.ENGAGE,
        ToolGroup.PUBLISH,
        ToolGroup.CONVERSATIONS,
    ],
    Profile.MANAGER: [
        ToolGroup.RESEARCH,
        ToolGroup.ENGAGE,
        ToolGroup.PUBLISH,
        ToolGroup.SOCIAL,
        ToolGroup.CONVERSATIONS,
        ToolGroup.LISTS,
    ],
    Profile.AUTOMATION: [
        ToolGroup.RESEARCH,
        ToolGroup.ENGAGE,
        ToolGroup.PUBLISH,
        ToolGroup.SOCIAL,
        ToolGroup.CONVERSATIONS,
        ToolGroup.LISTS,
        ToolGroup.DMS,
        ToolGroup.ACCOUNT,
    ],
    Profile.CUSTOM: [],  # User specifies via X_MCP_GROUPS
}

# Profile descriptions for documentation
PROFILE_DESCRIPTIONS: Dict[Profile, str] = {
    Profile.RESEARCHER: "Read-only access for research, monitoring, and analysis. Safe for automation.",
    Profile.CREATOR: "Post content and engage with your audience. No social actions (follow/block).",
    Profile.MANAGER: "Full account management including social actions and lists.",
    Profile.AUTOMATION: "Full API access including DMs. Use with caution.",
    Profile.CUSTOM: "Specify exactly which tool groups to enable via X_MCP_GROUPS.",
}

# Group descriptions
GROUP_DESCRIPTIONS: Dict[ToolGroup, Dict] = {
    ToolGroup.RESEARCH: {
        "description": "Search, lookup users/tweets, read timelines",
        "risk": "safe",
        "tools_count": len(TOOL_GROUPS[ToolGroup.RESEARCH]),
    },
    ToolGroup.ENGAGE: {
        "description": "Like, bookmark, retweet",
        "risk": "low",
        "tools_count": len(TOOL_GROUPS[ToolGroup.ENGAGE]),
    },
    ToolGroup.PUBLISH: {
        "description": "Post tweets, threads, polls",
        "risk": "medium",
        "tools_count": len(TOOL_GROUPS[ToolGroup.PUBLISH]),
    },
    ToolGroup.SOCIAL: {
        "description": "Follow, block, mute users",
        "risk": "medium-high",
        "tools_count": len(TOOL_GROUPS[ToolGroup.SOCIAL]),
    },
    ToolGroup.CONVERSATIONS: {
        "description": "Read threads, manage replies",
        "risk": "safe",
        "tools_count": len(TOOL_GROUPS[ToolGroup.CONVERSATIONS]),
    },
    ToolGroup.LISTS: {
        "description": "Create and manage lists",
        "risk": "low",
        "tools_count": len(TOOL_GROUPS[ToolGroup.LISTS]),
    },
    ToolGroup.DMS: {
        "description": "Send and read direct messages",
        "risk": "high",
        "tools_count": len(TOOL_GROUPS[ToolGroup.DMS]),
    },
    ToolGroup.ACCOUNT: {
        "description": "Update profile and settings",
        "risk": "high",
        "tools_count": len(TOOL_GROUPS[ToolGroup.ACCOUNT]),
    },
}


class PermissionManager:
    """Manages which tools are enabled based on profile and groups."""

    def __init__(self):
        self._enabled_tools: Set[str] = set()
        self._profile: Profile = Profile.RESEARCHER
        self._load_configuration()

    def _load_configuration(self):
        """Load configuration from environment variables."""
        # Get profile (default: researcher for safety)
        profile_name = os.getenv("X_MCP_PROFILE", "researcher").lower()
        try:
            self._profile = Profile(profile_name)
        except ValueError:
            self._profile = Profile.RESEARCHER

        # Get enabled groups
        if self._profile == Profile.CUSTOM:
            # Custom profile: use X_MCP_GROUPS
            groups_str = os.getenv("X_MCP_GROUPS", "research")
            group_names = [g.strip().lower() for g in groups_str.split(",")]
            enabled_groups = []
            for name in group_names:
                try:
                    enabled_groups.append(ToolGroup(name))
                except ValueError:
                    pass  # Invalid group name, skip
        else:
            # Use profile's groups
            enabled_groups = PROFILES.get(self._profile, [ToolGroup.RESEARCH])

        # Build enabled tools set
        for group in enabled_groups:
            self._enabled_tools.update(TOOL_GROUPS.get(group, []))

        # Handle explicitly disabled tools
        disabled_str = os.getenv("X_MCP_DISABLED_TOOLS", "")
        if disabled_str:
            disabled_tools = [t.strip() for t in disabled_str.split(",")]
            self._enabled_tools -= set(disabled_tools)

        # Handle explicitly enabled tools (override)
        enabled_str = os.getenv("X_MCP_ENABLED_TOOLS", "")
        if enabled_str:
            enabled_tools = [t.strip() for t in enabled_str.split(",")]
            self._enabled_tools.update(enabled_tools)

    def is_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled."""
        return tool_name in self._enabled_tools

    def get_enabled_tools(self) -> Set[str]:
        """Get all enabled tool names."""
        return self._enabled_tools.copy()

    def get_profile(self) -> Profile:
        """Get the current profile."""
        return self._profile

    def get_status(self) -> Dict:
        """Get configuration status for debugging."""
        return {
            "profile": self._profile.value,
            "enabled_tools_count": len(self._enabled_tools),
            "enabled_tools": sorted(self._enabled_tools),
        }


# Global permission manager instance
_permission_manager: PermissionManager = None
_permission_env_signature: Tuple[str, str, str, str] | None = None


def _current_env_signature() -> Tuple[str, str, str, str]:
    """Capture current permission-related env values for change detection."""
    profile = os.getenv("X_MCP_PROFILE", "researcher").lower()
    groups = os.getenv("X_MCP_GROUPS", "research")
    disabled = os.getenv("X_MCP_DISABLED_TOOLS", "")
    enabled = os.getenv("X_MCP_ENABLED_TOOLS", "")
    return profile, groups, disabled, enabled

def get_permission_manager() -> PermissionManager:
    """Get or create the global permission manager, refreshing if env changed."""
    global _permission_manager, _permission_env_signature
    signature = _current_env_signature()
    if _permission_manager is None or signature != _permission_env_signature:
        _permission_manager = PermissionManager()
        _permission_env_signature = signature
    return _permission_manager

def is_tool_enabled(tool_name: str) -> bool:
    """Check if a tool is enabled (convenience function)."""
    return get_permission_manager().is_enabled(tool_name)
