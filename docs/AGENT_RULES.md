# Agent Rules for X-Twitter MCP

Copy the relevant section to your AI editor's rules file.

---

## For Claude Code (~/.claude/CLAUDE.md or project CLAUDE.md)

Add this to your CLAUDE.md:

```markdown
## X-Twitter MCP

When working with X/Twitter:

### CRITICAL: Articles Need Playwright
- For X article URLs (x.com/*/status/*, twitter.com/*/status/*), use `get_article` MCP tool
- DO NOT use WebFetch - X articles require JavaScript rendering
- `get_article` uses Playwright internally

### Available Tools
| Task | Tool |
|------|------|
| Search | mcp__x-twitter__search_twitter |
| Read article | mcp__x-twitter__get_article |
| Get user | mcp__x-twitter__get_user_by_screen_name |
| Get thread | mcp__x-twitter__get_conversation |
| Post tweet | mcp__x-twitter__post_tweet |
| Like | mcp__x-twitter__favorite_tweet |

### Permission Levels
- researcher: read-only (default)
- creator: + post, engage
- manager: + follow, block
- automation: full access

Guidance: Use AI for research and drafts, but keep human review for posts and replies.
```

---

## For Cursor (.cursorrules)

Add this to your `.cursorrules`:

```
# X-Twitter MCP Rules

When fetching X/Twitter articles:
1. Use mcp__x-twitter__get_article - NOT WebFetch
2. X articles require JavaScript (Playwright)
3. Pattern: x.com/*/status/* or twitter.com/*/status/*

Quick reference:
- Search: mcp__x-twitter__search_twitter
- Article: mcp__x-twitter__get_article (PLAYWRIGHT!)
- User: mcp__x-twitter__get_user_by_screen_name
- Thread: mcp__x-twitter__get_conversation
- Post: mcp__x-twitter__post_tweet
```

---

## For Cline (.clinerules)

Add this to your `.clinerules`:

```
# X-Twitter MCP

IMPORTANT: Use get_article MCP tool for X/Twitter articles (uses Playwright).
WebFetch fails because X requires JavaScript.

Tools: search_twitter, get_article, get_user_by_screen_name,
       get_conversation, post_tweet, favorite_tweet, retweet
```

---

## For Windsurf (.windsurfrules)

Add this to your `.windsurfrules`:

```
# X-Twitter MCP

Use get_article for X articles (Playwright-based).
Do not use WebFetch for x.com URLs.

Key tools: search_twitter, get_article, get_user_by_screen_name
```

---

## For Aider (.aider.conf.yml)

```yaml
# X-Twitter MCP context
extra-context: |
  X-Twitter MCP available. For X articles, use get_article tool (Playwright).
  Do not use HTTP fetch for x.com URLs - they need JavaScript.
```

---

## For Custom LLM Prompts

Add to your system prompt:

```
You have access to X-Twitter MCP. Key rules:
1. For X/Twitter articles (x.com/*/status/*), use get_article tool
2. Do NOT use WebFetch for X URLs - they require JavaScript
3. get_article uses Playwright internally to render properly
4. Other tools: search_twitter, get_user_by_screen_name, get_conversation
```

---

## Why Playwright for Articles?

X/Twitter articles are rendered client-side with JavaScript. When you make a simple HTTP request:

```
curl https://x.com/user/status/123
# Returns: Empty shell, no content
```

The `get_article` tool launches a headless browser, waits for JavaScript to render, then extracts the content:

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(url)
    await page.wait_for_timeout(3000)  # Wait for JS
    content = await page.evaluate('() => document.body.innerText')
```

This is why you MUST use `get_article` and cannot use WebFetch or similar tools.
