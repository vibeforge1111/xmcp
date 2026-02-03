# XMCP Quick Start

Get up and running in 5 minutes.

## 1. Install

```bash
# With article support (recommended)
pip install "xmcp[articles] @ git+https://github.com/vibeforge1111/xmcp.git"
python -m playwright install chromium
```

Note: The package name is `xmcp` and the server command is `xmcp-server`.

## 2. Get Twitter API Keys (Required)

XMCP requires X/Twitter API credentials to run. Quick guide:

1. Go to https://developer.twitter.com and sign in.
2. Create a Project and App.
3. In the App Keys and Tokens tab, generate:
   - API Key and API Secret
   - Access Token and Access Token Secret
   - Bearer Token
4. Copy `.env.example` to `.env` and paste your keys.

Common error messages and fixes:
- "Missing required environment variable" -> add the missing key to `.env` or your MCP config.
- "403 Forbidden" / "Error 453" -> your X API access tier does not include that endpoint.

XMCP will not work without valid API credentials.
Copy the example environment file and fill it in:

```bash
# Windows (PowerShell)
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Do not commit `.env`. It is ignored by default.

## 3. Configure Claude

Add to `~/.claude.json`:

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

## 4. Choose Your Profile

| Profile | What You Can Do |
|---------|-----------------|
| `researcher` | Search, read tweets/articles (read-only) |
| `creator` | + Post tweets, like, retweet |
| `manager` | + Follow/block users, manage lists |
| `automation` | Everything including DMs |

Change `X_MCP_PROFILE` in config to switch.

## 5. Start Using

Restart Claude Code, then:

```
"Search for tweets about AI agents"
-> Uses search_twitter

"Read this article: https://x.com/user/status/123"
-> Uses get_article (Playwright)

"Post a tweet saying hello"
-> Uses post_tweet (requires creator+ profile)
```

## Common Commands

| Task | Example |
|------|---------|
| Search | "Find tweets about #crypto" |
| Read article | "Read the article at x.com/..." |
| Get user | "Get info about @elonmusk" |
| See thread | "Show me the full thread" |
| Post (creator) | "Tweet: Hello world!" |
| Like (creator) | "Like that tweet" |

## Troubleshooting

**"Tool not enabled"**: Change to a higher-access profile

**"Playwright not installed"**: Run `pip install playwright && python -m playwright install chromium`

**"Rate limit exceeded"**: Wait and try again

**Advisory note**: Publishing tools return an `advisory` recommending human review for authenticity.

## Need More?

See [README.md](./README.md) for full documentation.
