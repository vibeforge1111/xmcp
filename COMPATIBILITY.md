# X-Twitter MCP Compatibility Guide

This MCP server is compatible with **all major MCP clients**. This guide shows how to configure it for each platform.

---

## Quick Reference

| Client | Config File | Status |
|--------|------------|--------|
| **Claude Desktop** | `~/.claude.json` | Native |
| **Claude Code** | `CLAUDE.md` | Native |
| **Cursor** | `.cursorrules` | Native |
| **Cline** | `.clinerules` | Native |
| **Windsurf** | `.windsurfrules` | Native |
| **Continue.dev** | `.continue/mcpServers/` | Native |
| **OpenClaw** | Skills system | Native |
| **Zed** | `.zed/settings.json` | Native |
| **ChatGPT Desktop** | MCP settings | Native |
| **Sourcegraph Cody** | OpenCTX | Native |
| **Firebase Genkit** | genkitx-mcp | Plugin |
| **Taal** | `taal.yaml` | Sync |
| **VS Code + OpenMCP** | Extension | Plugin |

---

## Claude Desktop / Claude Code

### Configuration (`~/.claude.json` or `claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "x-twitter": {
      "type": "stdio",
      "command": "x-twitter-mcp-server",
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

### Agent Instructions

Copy `CLAUDE.md` to your project root or include `LLM_CONTEXT.md` in your system prompt.

---

## Continue.dev

Continue supports MCP natively. Create a config file in `.continue/mcpServers/`.

### YAML Format (`.continue/mcpServers/x-twitter.yaml`)

```yaml
name: X-Twitter MCP
command: x-twitter-mcp-server
env:
  TWITTER_API_KEY: ${TWITTER_API_KEY}
  TWITTER_API_SECRET: ${TWITTER_API_SECRET}
  TWITTER_ACCESS_TOKEN: ${TWITTER_ACCESS_TOKEN}
  TWITTER_ACCESS_TOKEN_SECRET: ${TWITTER_ACCESS_TOKEN_SECRET}
  TWITTER_BEARER_TOKEN: ${TWITTER_BEARER_TOKEN}
  X_MCP_PROFILE: researcher
```

### JSON Format (`.continue/mcpServers/x-twitter.json`)

```json
{
  "x-twitter": {
    "command": "x-twitter-mcp-server",
    "env": {
      "TWITTER_API_KEY": "${TWITTER_API_KEY}",
      "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
      "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
      "TWITTER_ACCESS_TOKEN_SECRET": "${TWITTER_ACCESS_TOKEN_SECRET}",
      "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}",
      "X_MCP_PROFILE": "researcher"
    }
  }
}
```

### HTTP Transport (Remote/Cloud)

```yaml
name: X-Twitter MCP
type: streamable-http
url: http://your-server:8081/mcp
```

---

## OpenClaw

OpenClaw uses skills to connect to MCP servers via the MCPorter system.

### Skill Configuration (`~/.openclaw/skills/x-twitter-mcp.yaml`)

```yaml
name: x-twitter-mcp
description: X/Twitter integration via MCP - search, post, engage, manage
version: 1.0.0
author: vibeforge1111

mcp:
  server: x-twitter-mcp-server
  transport: stdio
  env:
    TWITTER_API_KEY: ${TWITTER_API_KEY}
    TWITTER_API_SECRET: ${TWITTER_API_SECRET}
    TWITTER_ACCESS_TOKEN: ${TWITTER_ACCESS_TOKEN}
    TWITTER_ACCESS_TOKEN_SECRET: ${TWITTER_ACCESS_TOKEN_SECRET}
    TWITTER_BEARER_TOKEN: ${TWITTER_BEARER_TOKEN}
    X_MCP_PROFILE: researcher

capabilities:
  - search_twitter
  - get_article
  - get_user_profile
  - post_tweet
  - favorite_tweet
  - retweet

triggers:
  - "search twitter"
  - "post tweet"
  - "read x article"
  - "twitter analytics"
  - "x engagement"

instructions: |
  Use get_article for X/Twitter article URLs - WebFetch will fail.
  Check X_MCP_PROFILE to see which tools are available.
  Default profile is 'researcher' (read-only).
```

### MCPorter Integration

If using MCPorter skill directly:

```yaml
# In your agent config
skills:
  - mcporter:
      server: x-twitter-mcp-server
      tools: [search_twitter, get_article, get_user_profile]
```

---

## Zed Editor

Zed has built-in MCP support via settings.

### Project Settings (`.zed/settings.json`)

```json
{
  "mcp": {
    "servers": {
      "x-twitter": {
        "command": "x-twitter-mcp-server",
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
}
```

### Global Settings (`~/.config/zed/settings.json`)

Same format, placed in user settings for all projects.

---

## ChatGPT Desktop (OpenAI)

OpenAI adopted MCP in March 2025. Configuration is similar to Claude Desktop.

### Configuration (`~/.chatgpt/mcp.json`)

```json
{
  "servers": {
    "x-twitter": {
      "command": "x-twitter-mcp-server",
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

---

## Sourcegraph Cody

Cody uses OpenCTX for MCP integration.

### Configuration (`.sourcegraph/openctx.json`)

```json
{
  "providers": {
    "mcp-x-twitter": {
      "type": "mcp",
      "command": "x-twitter-mcp-server",
      "env": {
        "TWITTER_API_KEY": "${env:TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${env:TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${env:TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_TOKEN_SECRET": "${env:TWITTER_ACCESS_TOKEN_SECRET}",
        "TWITTER_BEARER_TOKEN": "${env:TWITTER_BEARER_TOKEN}",
        "X_MCP_PROFILE": "researcher"
      }
    }
  }
}
```

---

## Firebase Genkit

Use the `genkitx-mcp` plugin.

### Installation

```bash
npm install genkitx-mcp
```

### Configuration

```typescript
import { genkit } from 'genkit';
import { mcpClient } from 'genkitx-mcp';

const ai = genkit({
  plugins: [
    mcpClient({
      name: 'x-twitter',
      command: 'x-twitter-mcp-server',
      env: {
        TWITTER_API_KEY: process.env.TWITTER_API_KEY,
        TWITTER_API_SECRET: process.env.TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN: process.env.TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET: process.env.TWITTER_ACCESS_TOKEN_SECRET,
        TWITTER_BEARER_TOKEN: process.env.TWITTER_BEARER_TOKEN,
        X_MCP_PROFILE: 'researcher',
      },
    }),
  ],
});
```

---

## Taal (Cross-Client Sync)

Taal synchronizes MCP configs across multiple AI assistants.

### Central Configuration (`taal.yaml`)

```yaml
version: 1
servers:
  x-twitter:
    command: x-twitter-mcp-server
    env:
      TWITTER_API_KEY: ${TWITTER_API_KEY}
      TWITTER_API_SECRET: ${TWITTER_API_SECRET}
      TWITTER_ACCESS_TOKEN: ${TWITTER_ACCESS_TOKEN}
      TWITTER_ACCESS_TOKEN_SECRET: ${TWITTER_ACCESS_TOKEN_SECRET}
      TWITTER_BEARER_TOKEN: ${TWITTER_BEARER_TOKEN}
      X_MCP_PROFILE: researcher

    # Sync to these clients
    sync:
      - claude
      - cursor
      - continue
      - zed
```

### Sync Command

```bash
taal sync
```

---

## VS Code + OpenMCP Extension

### Extension Settings

1. Install "OpenMCP" extension from VS Code marketplace
2. Open Settings (Ctrl+,)
3. Search for "OpenMCP"
4. Add server configuration:

```json
{
  "openmcp.servers": {
    "x-twitter": {
      "command": "x-twitter-mcp-server",
      "env": {
        "TWITTER_API_KEY": "${env:TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${env:TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${env:TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_TOKEN_SECRET": "${env:TWITTER_ACCESS_TOKEN_SECRET}",
        "TWITTER_BEARER_TOKEN": "${env:TWITTER_BEARER_TOKEN}",
        "X_MCP_PROFILE": "researcher"
      }
    }
  }
}
```

---

## HTTP Mode (Any Client)

For clients that support HTTP-based MCP or cloud deployments:

### Start HTTP Server

```bash
# Default port 8081
x-twitter-mcp-http

# Custom port
PORT=8080 x-twitter-mcp-http
```

### Connect via HTTP

```yaml
# Any client supporting HTTP transport
type: http
url: http://localhost:8081/mcp

# Or with streaming
type: streamable-http
url: http://localhost:8081/mcp
```

### Cloud Deployment

```yaml
# Docker
docker run -p 8081:8081 \
  -e TWITTER_API_KEY=xxx \
  -e TWITTER_API_SECRET=xxx \
  -e TWITTER_ACCESS_TOKEN=xxx \
  -e TWITTER_ACCESS_TOKEN_SECRET=xxx \
  -e TWITTER_BEARER_TOKEN=xxx \
  vibeforge/x-twitter-mcp

# Then connect from any client
url: https://your-server.com/mcp
```

---

## Ollama + Continue.dev

For local LLMs via Ollama with MCP:

### Setup

1. Install Ollama and pull a model:
   ```bash
   ollama pull llama3.2
   ```

2. Configure Continue with Ollama + MCP:
   ```yaml
   # .continue/config.yaml
   models:
     - name: Ollama Llama
       provider: ollama
       model: llama3.2

   mcpServers:
     - name: X-Twitter
       command: x-twitter-mcp-server
       env:
         TWITTER_BEARER_TOKEN: ${TWITTER_BEARER_TOKEN}
         X_MCP_PROFILE: researcher
   ```

---

## Environment Variables

All clients use the same environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `TWITTER_API_KEY` | Yes | Twitter API key |
| `TWITTER_API_SECRET` | Yes | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | Yes | Access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | Yes | Access token secret |
| `TWITTER_BEARER_TOKEN` | Yes | Bearer token |
| `X_MCP_PROFILE` | No | Permission profile (default: researcher) |
| `X_MCP_GROUPS` | No | Custom groups (for custom profile) |

### Setting Environment Variables

**Unix/macOS:**
```bash
export TWITTER_API_KEY="your_key"
export TWITTER_API_SECRET="your_secret"
# ... etc
```

**Windows:**
```cmd
set TWITTER_API_KEY=your_key
set TWITTER_API_SECRET=your_secret
```

**`.env` file:**
```env
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
TWITTER_BEARER_TOKEN=your_bearer
X_MCP_PROFILE=researcher
```

---

## Agent Rules Files

Pre-configured rules for AI assistants:

| File | Client | Description |
|------|--------|-------------|
| `CLAUDE.md` | Claude Code | Full instructions |
| `.cursorrules` | Cursor | IDE-specific rules |
| `.clinerules` | Cline | CLI-specific rules |
| `.windsurfrules` | Windsurf | IDE-specific rules |
| `LLM_CONTEXT.md` | Any LLM | Generic context block |
| `docs/AGENT_RULES.md` | All | Comprehensive rules |

**Key Rule for All Agents:**
> Use `get_article` for X/Twitter article URLs. WebFetch will fail because X articles require JavaScript rendering.

---

## Testing Your Setup

### Verify Installation

```bash
# Check if server starts
x-twitter-mcp-server --help

# Test with a simple query (if installed globally)
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | x-twitter-mcp-server
```

### From Any MCP Client

Once configured, test with:
- "Search for tweets about AI"
- "Get user @elonmusk"
- "What's trending on Twitter?"

---

## Troubleshooting

### "Command not found"

```bash
# Install globally
pip install x-twitter-mcp

# Or use full path
command: python -m x_twitter_mcp.server
```

### "Tool not enabled"

Check your `X_MCP_PROFILE`. Default is `researcher` (read-only).

### "Playwright not installed"

For article fetching:
```bash
pip install playwright
playwright install chromium
```

### "Rate limit exceeded"

Built-in rate limiting. Wait before retrying.

---

## Resources

- [MCP Official Docs](https://modelcontextprotocol.io)
- [Continue.dev MCP Guide](https://docs.continue.dev/customize/deep-dives/mcp)
- [OpenClaw Skills](https://github.com/VoltAgent/awesome-openclaw-skills)
- [PulseMCP Client List](https://www.pulsemcp.com/clients)
- [MCP Servers Directory](https://mcpservers.org)
