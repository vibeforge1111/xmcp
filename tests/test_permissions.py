from xmcp.config import is_tool_enabled


def test_permission_refresh(monkeypatch):
    monkeypatch.setenv("X_MCP_PROFILE", "researcher")
    assert is_tool_enabled("search_twitter") is True
    assert is_tool_enabled("post_tweet") is False

    monkeypatch.setenv("X_MCP_PROFILE", "creator")
    assert is_tool_enabled("post_tweet") is True


def test_custom_groups(monkeypatch):
    monkeypatch.setenv("X_MCP_PROFILE", "custom")
    monkeypatch.setenv("X_MCP_GROUPS", "research,engage")
    assert is_tool_enabled("search_twitter") is True
    assert is_tool_enabled("favorite_tweet") is True
    assert is_tool_enabled("post_tweet") is False
