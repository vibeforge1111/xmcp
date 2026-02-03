# XMCP

The most comprehensive MCP server for X/Twitter with **permission-based access control**, **70+ tools**, and **Playwright-powered article fetching**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Highlights

- 70+ tools across research, engagement, publishing, social, lists, DMs
- Permission profiles with runtime enforcement
- Playwright-powered article fetching for X articles
- Full engagement metrics and thread support
- Broad MCP client compatibility

---

## Quick Start

### 1. Install

```bash
pip install "xmcp[articles] @ git+https://github.com/vibeforge1111/xmcp.git"
python -m playwright install chromium
```

Note: The package name is `xmcp` and the server command is `xmcp-server`.

### 2. Get API Keys (Required)

XMCP requires X/Twitter API credentials to run.
Get your credentials from [developer.twitter.com](https://developer.twitter.com):
- API Key & Secret
- Access Token & Secret
- Bearer Token

You can store them in a local `.env` file:

```bash
# Windows (PowerShell)
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Do not commit `.env`. It is ignored by default.

### 3. Configure

Add to your Claude settings (`~/.claude.json`):

```json
{
  "mcpServers": {
    "xmcp": {
      "type": "stdio",
      "command": "xmcp-server",
      "env": {
        "TWITTER_API_KEY": "your_key",
        "TWITTER_API_SECRET": "your_secret",
        "TWITTER_ACCESS_TOKEN": "your_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_token_secret",
        "TWITTER_BEARER_TOKEN": "your_bearer",
        "X_MCP_PROFILE": "researcher"
      }
    }
  }
}
```

If you name the server `xmcp`, tools will appear as `mcp__xmcp__*` in clients that show tool prefixes.

### 4. Use

```
"Search for tweets about AI"        -> search_twitter
"Read this article: x.com/..."      -> get_article (Playwright)
"Post: Hello world!"                -> post_tweet (requires creator profile)
```

---

## Permission Profiles

Choose what capabilities to enable:

| Profile | Tools | Use Case |
|---------|-------|----------|
| **researcher** | 23 | Monitoring, analysis, research (read-only) |
| **creator** | 41 | Content creation, audience engagement |
| **manager** | 55 | Full account management |
| **automation** | 70 | Bots, full automation (including DMs) |
| **custom** | varies | Pick exactly what you need |

### Setting a Profile

```json
"env": {
  "X_MCP_PROFILE": "creator"
}
```

Permissions are evaluated at runtime. You can switch profiles or groups without restarting the server.

### Custom Profile

```json
"env": {
  "X_MCP_PROFILE": "custom",
  "X_MCP_GROUPS": "research,engage,publish"
}
```

---

## Tool Groups

### research (18 tools) - Read-only, safe
Search, user lookup, tweet details, timelines, trends, **article fetching**

### engage (9 tools) - Low risk
Like, unlike, bookmark, retweet, unretweet

### publish (7 tools) - Medium risk
Post tweet, delete, quote, create thread, polls

### social (8 tools) - Medium-high risk
Follow, unfollow, block, unblock, mute, unmute

### conversations (5 tools) - Safe
Get full threads, replies, quote tweets, hide/unhide replies

### lists (14 tools) - Low risk
Create, delete, manage lists and members

### dms (3 tools) - High risk
Send and read direct messages

### account (1 tool) - High risk
Get authenticated user profile

---

## Key Tools

### Search & Discovery

| Tool | Description |
|------|-------------|
| `search_twitter` | Search with full engagement metrics |
| `search_articles` | Find tweets containing X articles |
| `get_trends` | Worldwide trending topics |
| `get_article` | **Fetch article content (Playwright)** |

### User & Tweet Info

| Tool | Description |
|------|-------------|
| `get_user_by_screen_name` | User by @handle |
| `get_user_profile` | User by ID with metrics |
| `get_tweet_details` | Full tweet info |
| `get_conversation` | Complete thread |
| `get_replies` | Replies to a tweet |

### Engagement

| Tool | Description |
|------|-------------|
| `favorite_tweet` | Like |
| `retweet` | Retweet |
| `bookmark_tweet` | Bookmark |
| `quote_tweet` | Quote with comment |

### Publishing

| Tool | Description |
|------|-------------|
| `post_tweet` | Post with media, tags, reply |
| `create_thread` | Post multiple tweets as thread |
| `create_poll_tweet` | Create a poll |

### Social

| Tool | Description |
|------|-------------|
| `follow_user` / `unfollow_user` | Follow management |
| `block_user` / `unblock_user` | Block management |
| `mute_user` / `unmute_user` | Mute management |

---

## Human-In-The-Loop Advisory

This MCP is designed to improve research and workflows, not to replace human judgment.
Publishing tools return an `advisory` field that recommends a human review for posts and replies.

---

## Real-Time Use Cases (No Extra Telemetry)

You can drive real-time workflows by polling tools on a schedule from your client or a cron job.
Common patterns:

- Trend snapshots every hour using `get_trends`
- Keyword monitoring using `search_twitter`
- Article tracking using `search_articles` + `get_article`

This keeps the server simple while still enabling real-time visibility.

---

## Article Fetching

**X articles require JavaScript to render.** This MCP uses Playwright.

```python
# Correct - uses Playwright internally
result = await get_article("https://x.com/user/status/123")
# Returns: {title, author, content, url}

# WRONG - will fail
WebFetch("https://x.com/...")  # Returns empty content
```

### Setup

```bash
pip install playwright
python -m playwright install chromium
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `X_MCP_PROFILE` | Permission profile | `researcher` |
| `X_MCP_GROUPS` | Groups for custom profile | `research` |
| `X_MCP_DISABLED_TOOLS` | Tools to disable | none |
| `X_MCP_ENABLED_TOOLS` | Tools to force-enable | none |

Credentials are read locally and only used to authenticate requests to X/Twitter.

### Examples

**Research only (safest):**
```json
"X_MCP_PROFILE": "researcher"
```

**Content creator:**
```json
"X_MCP_PROFILE": "creator"
```

**Custom - research + likes only:**
```json
"X_MCP_PROFILE": "custom",
"X_MCP_GROUPS": "research,engage",
"X_MCP_DISABLED_TOOLS": "retweet,unretweet"
```

---

## Runtime Permissions

Permissions are evaluated at runtime. This means you can:

- Switch profiles or groups without restarting the server
- Use different profiles per request in HTTP mode

---

## Error Responses

Errors return a consistent envelope:

```json
{
  "ok": false,
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "status": 429,
    "details": {
      "action_type": "tweet_actions",
      "retry_after_seconds": 10
    }
  },
  "tool": "post_tweet",
  "timestamp": "2026-02-03T12:00:00+00:00"
}
```

---

## Rate Limits

Built-in protection:

| Action | Limit | Window |
|--------|-------|--------|
| Tweets | 300 | 15 min |
| Likes | 1000 | 24 hours |
| Follows | 400 | 24 hours |
| DMs | 1000 | 15 min |

Note: These limits are local guardrails, not official Twitter API limits.

---

## Limitations

- `get_user_followers_you_know` and `get_highlights_tweets` are simulated with available API data
- `vote_on_poll` returns `not_supported` because the API does not support programmatic voting
- Article fetching requires Playwright and a Chromium install

---

## Compatible Clients

Works with **all major MCP clients**. See [COMPATIBILITY.md](./COMPATIBILITY.md) for full setup guides.

| Client | Config Location | Status |
|--------|----------------|--------|
| **Claude Desktop** | `~/.claude.json` | Native |
| **Claude Code** | `CLAUDE.md` | Native |
| **Cursor** | `.cursorrules` | Native |
| **Cline** | `.clinerules` | Native |
| **Windsurf** | `.windsurfrules` | Native |
| **Continue.dev** | `.continue/mcpServers/` | Native |
| **OpenClaw** | `~/.openclaw/skills/` | Native |
| **Zed** | `.zed/settings.json` | Native |
| **ChatGPT Desktop** | `~/.chatgpt/mcp.json` | Native |
| **Sourcegraph Cody** | OpenCTX | Native |
| **Firebase Genkit** | genkitx-mcp plugin | Plugin |
| **Taal** | `taal.yaml` (sync all) | Sync |
| **VS Code + OpenMCP** | Extension settings | Plugin |
| **Ollama + Continue** | Continue config | Native |

### Pre-made Config Files

Ready-to-use configs in `configs/` directory:

```
configs/
|-- continue.yaml              # Continue.dev (YAML)
|-- continue.json              # Continue.dev (JSON)
|-- openclaw-skill.yaml        # OpenClaw skill
|-- zed-settings.json          # Zed editor
|-- chatgpt-mcp.json           # ChatGPT Desktop
|-- taal.yaml                  # Taal cross-client sync
|-- sourcegraph-openctx.json   # Sourcegraph Cody
|-- genkit-plugin.ts           # Firebase Genkit
`-- vscode-openmcp.json        # VS Code OpenMCP
```

---

## For AI Agents

This package includes rules files for AI code editors:

| File | Editor |
|------|--------|
| `.cursorrules` | Cursor |
| `.clinerules` | Cline |
| `.windsurfrules` | Windsurf |
| `CLAUDE.md` | Claude Code |
| `LLM_CONTEXT.md` | Any LLM (copy to prompt) |
| `docs/AGENT_RULES.md` | Comprehensive rules |

**Key rule:** Use `get_article` for X URLs, not WebFetch.

---

## HTTP Server Mode

For cloud deployments:

```bash
xmcp-http  # Runs on port 8081
PORT=8080 xmcp-http  # Custom port
```

---

## Installation Options

### From GitHub (recommended)
```bash
pip install "xmcp[articles] @ git+https://github.com/vibeforge1111/xmcp.git"
```

### From PyPI (when published)
```bash
pip install xmcp[articles]
```

### From Source
```bash
git clone https://github.com/vibeforge1111/xmcp.git
cd xmcp
pip install -e .[articles]
python -m playwright install chromium
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | This file - full documentation |
| [QUICKSTART.md](./QUICKSTART.md) | 5-minute setup guide |
| [CLAUDE.md](./CLAUDE.md) | Instructions for AI agents |
| [LLM_CONTEXT.md](./LLM_CONTEXT.md) | Context block for LLM prompts |
| [docs/AGENT_RULES.md](./docs/AGENT_RULES.md) | Rules for all AI editors |

---

## Credits

Built on the upstream project by Rafal Janicki:
`https://github.com/rafaljanicki/x-twitter-mcp-server`

## Update Log

See `CHANGELOG.md` for a summary of enhancements made in XMCP.

Enhanced by [VibeShip](https://github.com/vibeforge1111) with:
- Permission-based access control (5 profiles, 8 groups)
- 70+ tools (vs ~20 original)
- Playwright article fetching
- Thread creation and reading
- Full Lists, DMs, Social actions
- Comprehensive engagement metrics
- AI agent documentation

---

## License

MIT License - see [LICENSE](./LICENSE)
