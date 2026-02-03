# X-Twitter MCP - AI Agent Instructions

This file provides instructions for AI agents (Claude, GPT, etc.) using the X-Twitter MCP.

## CRITICAL: Article Fetching Requires Playwright

**IMPORTANT**: When fetching X/Twitter articles, you MUST use the `get_article` tool which uses Playwright.

Regular HTTP requests (WebFetch, curl, requests) will NOT work for X articles because:
- X articles require JavaScript to render
- Simple HTTP returns empty/incomplete content
- The `get_article` tool uses Playwright to properly render the page

### Correct Usage

```
# When user asks to read an X article:
1. Use get_article tool with the URL
2. DO NOT use WebFetch - it will fail
3. DO NOT try to scrape with requests - it will fail
```

### Example

User: "Read this article: https://x.com/elonmusk/status/123456789"

CORRECT:
```python
result = await get_article("https://x.com/elonmusk/status/123456789")
# Returns: {title, author, content, url}
```

WRONG:
```python
# These will NOT work for X articles:
WebFetch("https://x.com/...")  # Fails - needs JS
requests.get("https://x.com/...")  # Fails - needs JS
```

---

## Available Tool Groups

The MCP has 8 tool groups. Which are available depends on the configured profile.

### Check What's Enabled

The profile is set via `X_MCP_PROFILE` environment variable:
- `researcher` (default): read-only, safe for automation
- `creator`: can post and engage
- `manager`: full account control
- `automation`: everything including DMs

### Group Reference

| Group | Key Tools | When to Use |
|-------|-----------|-------------|
| **research** | `search_twitter`, `get_user_profile`, `get_article` | Finding information, monitoring |
| **engage** | `favorite_tweet`, `retweet`, `bookmark_tweet` | Engaging with content |
| **publish** | `post_tweet`, `create_thread`, `quote_tweet` | Creating content |
| **social** | `follow_user`, `block_user`, `mute_user` | Managing relationships |
| **conversations** | `get_conversation`, `get_replies` | Reading threads |
| **lists** | `create_list`, `get_list_tweets` | List management |
| **dms** | `send_dm`, `get_dm_conversations` | Direct messages |

---

## Common Tasks

### Search for Tweets
```python
result = await search_twitter(query="AI agents", product="Top", count=20)
# Returns tweets with: id, text, author info, likes, retweets, replies
```

### Get User Info
```python
# By username
user = await get_user_by_screen_name("elonmusk")

# By ID
user = await get_user_profile("44196397")
```

### Read an Article (USES PLAYWRIGHT)
```python
article = await get_article("https://x.com/user/status/123")
# Returns: {title, author, content, url}
```

### Post a Tweet
```python
# Simple tweet
result = await post_tweet("Hello world!")

# With hashtags
result = await post_tweet("Check this out", tags=["AI", "Tech"])

# Reply to another tweet
result = await post_tweet("Great point!", reply_to="1234567890")
```

### Create a Thread
```python
result = await create_thread([
    "Thread: Why AI agents are the future 🧵",
    "1/ First point here...",
    "2/ Second point here...",
    "3/ Final thoughts..."
])
```

### Get a Full Conversation/Thread
```python
result = await get_conversation(tweet_id="1234567890")
# Returns all tweets in the thread
```

### Engage with Content
```python
await favorite_tweet("1234567890")  # Like
await retweet("1234567890")  # Retweet
await bookmark_tweet("1234567890")  # Bookmark
```

---

## Error Handling

### "Tool not enabled"
The tool isn't available in the current profile. Check `X_MCP_PROFILE`.

### "Rate limit exceeded"
Wait before retrying. Built-in limits:
- Tweet actions: 300 per 15 min
- Likes: 1000 per 24 hours
- Follows: 400 per 24 hours

### "Playwright not installed" (for get_article)
Article fetching requires Playwright. The user needs to run:
```bash
pip install playwright
playwright install chromium
```

---

## Best Practices

1. **For articles**: Always use `get_article`, never WebFetch
2. **For search**: Use `search_twitter` with metrics, not just text search
3. **For threads**: Use `get_conversation` to get the full context
4. **For posting**: Check if `publish` group is enabled first
5. **Pagination**: Use the `next_cursor` returned in results for more data

---

## Quick Reference

| Task | Tool | Group |
|------|------|-------|
| Search tweets | `search_twitter` | research |
| Read article | `get_article` | research |
| Get user | `get_user_by_screen_name` | research |
| Get tweet | `get_tweet_details` | research |
| Get thread | `get_conversation` | conversations |
| Like | `favorite_tweet` | engage |
| Retweet | `retweet` | engage |
| Bookmark | `bookmark_tweet` | engage |
| Post | `post_tweet` | publish |
| Thread | `create_thread` | publish |
| Quote | `quote_tweet` | publish |
| Follow | `follow_user` | social |
| Block | `block_user` | social |
