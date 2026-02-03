# XMCP - LLM Context Block

**Copy this into your system prompt or context when using XMCP.**

---

## XMCP Available

You have access to the XMCP with the following capabilities:

### CRITICAL: Article Fetching
- Use `get_article` tool for ANY X/Twitter article URL
- DO NOT use WebFetch - it fails because X requires JavaScript
- `get_article` uses Playwright internally to render properly

### Search & Research
- `search_twitter(query, product="Top"|"Latest", count)` - Search with metrics
- `search_articles(query)` - Find tweets containing X articles
- `get_trends()` - Trending topics
- `get_article(url)` - Fetch full article content (PLAYWRIGHT)

### User Info
- `get_user_by_screen_name(username)` - Get user by @handle
- `get_user_profile(user_id)` - Get user by ID
- `get_user_tweets(user_id)` - User's tweets
- `get_user_followers(user_id)` - Who follows them
- `get_user_following(user_id)` - Who they follow

### Tweet Info
- `get_tweet_details(tweet_id)` - Full tweet info
- `get_conversation(tweet_id)` - Full thread
- `get_replies(tweet_id)` - Replies to tweet
- `get_quote_tweets(tweet_id)` - Quotes of tweet

### Engagement (if enabled)
- `favorite_tweet(tweet_id)` - Like
- `unfavorite_tweet(tweet_id)` - Unlike
- `retweet(tweet_id)` - Retweet
- `unretweet(tweet_id)` - Remove retweet
- `bookmark_tweet(tweet_id)` - Bookmark

### Publishing (if enabled)
- `post_tweet(text, media_paths?, reply_to?, tags?)` - Post tweet
- `create_thread(tweets_list)` - Post thread
- `quote_tweet(text, quoted_tweet_id)` - Quote tweet
- `delete_tweet(tweet_id)` - Delete tweet
Guidance: Use AI for research and drafts, but keep human review for posts and replies.

### Social Actions (if enabled)
- `follow_user(user_id)` - Follow
- `unfollow_user(user_id)` - Unfollow
- `block_user(user_id)` - Block
- `mute_user(user_id)` - Mute

### Permission Profiles
- `researcher`: Read-only (default)
- `creator`: + engage + publish
- `manager`: + social + lists
- `automation`: Full access

### URL Patterns for get_article
Use `get_article` for:
- `https://x.com/*/status/*`
- `https://twitter.com/*/status/*`
- `https://x.com/i/article/*`

---

**Remember: X articles need `get_article` (Playwright), not WebFetch!**
