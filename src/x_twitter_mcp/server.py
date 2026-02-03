"""
X-Twitter MCP Server

A comprehensive, modular MCP server for X/Twitter with permission-based tool access.

Configuration via environment variables:
- X_MCP_PROFILE: researcher|creator|manager|automation|custom (default: researcher)
- X_MCP_GROUPS: comma-separated groups for custom profile
- X_MCP_DISABLED_TOOLS: comma-separated tools to disable
- X_MCP_ENABLED_TOOLS: comma-separated tools to force-enable
"""

import logging
import os
import warnings
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Any
from functools import wraps

from fastmcp import FastMCP
import tweepy
from dotenv import load_dotenv

from .config import (
    is_tool_enabled,
    get_permission_manager,
    ToolGroup,
    TOOL_GROUPS,
    PROFILE_DESCRIPTIONS,
    GROUP_DESCRIPTIONS,
)
from .errors import (
    PermissionDeniedError,
    RateLimitError,
    error_response,
    handle_exception,
)

# Optional: playwright for article fetching
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress SyntaxWarning from Tweepy docstrings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
server = FastMCP(name="X-Twitter-MCP")

# Twitter API client setup (lazy-loaded, credential-aware)
TWITTER_ENV_VARS = [
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
    "TWITTER_BEARER_TOKEN",
]
_twitter_clients_cache: dict[tuple[str, ...], tuple[tweepy.Client, tweepy.API]] = {}


def _get_twitter_credentials() -> tuple[str, ...]:
    """Fetch required Twitter credentials from environment variables."""
    missing = [var for var in TWITTER_ENV_VARS if not os.getenv(var)]
    if missing:
        missing_str = ", ".join(missing)
        raise EnvironmentError(f"Missing required environment variable(s): {missing_str}")
    return tuple(os.getenv(var) for var in TWITTER_ENV_VARS)  # type: ignore[return-value]


def initialize_twitter_clients() -> tuple[tweepy.Client, tweepy.API]:
    """Initialize Twitter API clients on-demand, keyed by credentials."""
    creds = _get_twitter_credentials()
    cached = _twitter_clients_cache.get(creds)
    if cached is not None:
        return cached

    api_key, api_secret, access_token, access_token_secret, bearer_token = creds

    twitter_client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token,
    )

    auth = tweepy.OAuth1UserHandler(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    twitter_v1_api = tweepy.API(auth)

    _twitter_clients_cache[creds] = (twitter_client, twitter_v1_api)
    return twitter_client, twitter_v1_api


# Rate limiting
RATE_LIMITS = {
    "tweet_actions": {"limit": 300, "window": timedelta(minutes=15)},
    "dm_actions": {"limit": 1000, "window": timedelta(minutes=15)},
    "follow_actions": {"limit": 400, "window": timedelta(hours=24)},
    "like_actions": {"limit": 1000, "window": timedelta(hours=24)},
    "list_actions": {"limit": 300, "window": timedelta(minutes=15)},
}

rate_limit_counters = defaultdict(lambda: {"count": 0, "reset_time": datetime.now()})

HUMAN_TOUCH_ADVISORY = (
    "Recommendation: Use AI to assist with research and drafts, "
    "but keep a human review for posts and replies to preserve authenticity."
)
HUMAN_TOUCH_TOOLS = {
    "post_tweet",
    "quote_tweet",
    "create_thread",
    "create_poll_tweet",
    "schedule_tweet",
}


def check_rate_limit(action_type: str) -> bool:
    """Check if the action is within rate limits."""
    config = RATE_LIMITS.get(action_type)
    if not config:
        return True
    counter = rate_limit_counters[action_type]
    now = datetime.now()
    if now >= counter["reset_time"]:
        counter["count"] = 0
        counter["reset_time"] = now + config["window"]
    if counter["count"] >= config["limit"]:
        return False
    counter["count"] += 1
    return True


def conditional_tool(name: str, description: str):
    """Decorator to register tools and enforce permissions at runtime."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if not is_tool_enabled(name):
                    profile = get_permission_manager().get_profile().value
                    raise PermissionDeniedError(name, profile=profile)
                result = await func(*args, **kwargs)
                if isinstance(result, dict) and name in HUMAN_TOUCH_TOOLS and "advisory" not in result:
                    return {**result, "advisory": HUMAN_TOUCH_ADVISORY}
                return result
            except Exception as exc:
                return handle_exception(exc, tool=name)

        return server.tool(name=name, description=description)(wrapper)
    return decorator


def enforce_rate_limit(action_type: str) -> None:
    """Raise a structured error if the action is rate limited."""
    if check_rate_limit(action_type):
        return
    reset_time = rate_limit_counters[action_type]["reset_time"]
    retry_after = max(0, int((reset_time - datetime.now()).total_seconds()))
    raise RateLimitError(action_type, retry_after_seconds=retry_after)


# =============================================================================
# RESEARCH GROUP - Search, lookup, read-only operations
# =============================================================================

@conditional_tool("get_user_profile", "Get detailed profile information for a user")
async def get_user_profile(user_id: str) -> Dict:
    """Fetches user profile by user ID."""
    client, _ = initialize_twitter_clients()
    user = client.get_user(
        id=user_id,
        user_fields=["id", "name", "username", "profile_image_url", "description",
                     "public_metrics", "verified", "created_at", "location", "url"]
    )
    return user.data if user.data else None


@conditional_tool("get_user_by_screen_name", "Fetches a user by screen name")
async def get_user_by_screen_name(screen_name: str) -> Dict:
    """Fetches user by screen name/username."""
    client, _ = initialize_twitter_clients()
    user = client.get_user(
        username=screen_name,
        user_fields=["id", "name", "username", "profile_image_url", "description",
                     "public_metrics", "verified", "created_at", "location", "url"]
    )
    return user.data if user.data else None


@conditional_tool("get_user_by_id", "Fetches a user by ID")
async def get_user_by_id(user_id: str) -> Dict:
    """Fetches user by ID."""
    client, _ = initialize_twitter_clients()
    user = client.get_user(
        id=user_id,
        user_fields=["id", "name", "username", "profile_image_url", "description",
                     "public_metrics", "verified", "created_at", "location", "url"]
    )
    return user.data if user.data else None


@conditional_tool("get_user_followers", "Retrieves a list of followers for a given user")
async def get_user_followers(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Retrieves followers for a user with pagination."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    followers = client.get_users_followers(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username", "profile_image_url", "public_metrics"]
    )
    return {
        "users": [user.data for user in (followers.data or [])],
        "next_cursor": followers.meta.get("next_token") if followers.meta else None
    }


@conditional_tool("get_user_following", "Retrieves users the given user is following")
async def get_user_following(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Retrieves users that a user follows with pagination."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    following = client.get_users_following(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username", "profile_image_url", "public_metrics"]
    )
    return {
        "users": [user.data for user in (following.data or [])],
        "next_cursor": following.meta.get("next_token") if following.meta else None
    }


@conditional_tool("get_user_followers_you_know", "Retrieves common followers between you and a user")
async def get_user_followers_you_know(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Retrieves common/mutual followers (simulated - API doesn't directly support)."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    followers = client.get_users_followers(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username"]
    )
    return {
        "users": [user.data for user in (followers.data or [])][:count],
        "note": "Simulated - full mutual follower check requires comparing follower lists"
    }


@conditional_tool("get_user_subscriptions", "Retrieves users a user is subscribed to")
async def get_user_subscriptions(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Retrieves subscriptions (uses following as proxy)."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    subscriptions = client.get_users_following(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username"]
    )
    return {
        "users": [user.data for user in (subscriptions.data or [])],
        "next_cursor": subscriptions.meta.get("next_token") if subscriptions.meta else None
    }


@conditional_tool("get_tweet_details", "Get detailed information about a specific tweet")
async def get_tweet_details(tweet_id: str) -> Dict:
    """Fetches full tweet details including metrics."""
    client, _ = initialize_twitter_clients()
    tweet = client.get_tweet(
        id=tweet_id,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics",
                      "entities", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
        expansions=["author_id", "referenced_tweets.id"],
        user_fields=["id", "name", "username", "profile_image_url"]
    )

    result = tweet.data if tweet.data else None
    if result and tweet.includes:
        users = {u.id: u.data for u in tweet.includes.get("users", [])}
        result["author"] = users.get(result.get("author_id"))
    return result


@conditional_tool("get_user_tweets", "Get tweets posted by a specific user")
async def get_user_tweets(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None,
                          exclude_replies: bool = False, exclude_retweets: bool = False) -> Dict:
    """Fetches tweets from a user's timeline."""
    client, _ = initialize_twitter_clients()

    exclude = []
    if exclude_replies:
        exclude.append("replies")
    if exclude_retweets:
        exclude.append("retweets")

    tweets = client.get_users_tweets(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        exclude=exclude if exclude else None,
        tweet_fields=["id", "text", "created_at", "public_metrics", "entities"]
    )
    return {
        "tweets": [tweet.data for tweet in (tweets.data or [])],
        "next_cursor": tweets.meta.get("next_token") if tweets.meta else None
    }


@conditional_tool("get_liked_tweets", "Get tweets liked by a specific user")
async def get_liked_tweets(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Fetches tweets that a user has liked."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_liked_tweets(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"]
    )
    return {
        "tweets": [tweet.data for tweet in (tweets.data or [])],
        "next_cursor": tweets.meta.get("next_token") if tweets.meta else None
    }


@conditional_tool("get_timeline", "Get tweets from your home timeline (For You)")
async def get_timeline(count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Fetches home timeline tweets."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_home_timeline(
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"],
        expansions=["author_id"],
        user_fields=["id", "name", "username", "profile_image_url"]
    )

    users = {}
    if tweets.includes and "users" in tweets.includes:
        users = {u.id: {"name": u.name, "username": u.username} for u in tweets.includes["users"]}

    result = []
    for tweet in (tweets.data or []):
        t = tweet.data if hasattr(tweet, 'data') else tweet
        author = users.get(t.get('author_id'), {})
        result.append({**t, "author_name": author.get("name"), "author_username": author.get("username")})

    return {
        "tweets": result,
        "next_cursor": tweets.meta.get("next_token") if tweets.meta else None
    }


@conditional_tool("get_latest_timeline", "Get tweets from your home timeline (Following)")
async def get_latest_timeline(count: Optional[int] = 100) -> Dict:
    """Fetches latest timeline (chronological from followed accounts)."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_home_timeline(
        max_results=min(count, 100),
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"],
        exclude=["replies", "retweets"]
    )
    return {
        "tweets": [tweet.data for tweet in (tweets.data or [])]
    }


@conditional_tool("get_user_mentions", "Get tweets mentioning a specific user")
async def get_user_mentions(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Fetches tweets mentioning a user."""
    client, _ = initialize_twitter_clients()
    mentions = client.get_users_mentions(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"]
    )
    return {
        "tweets": [tweet.data for tweet in (mentions.data or [])],
        "next_cursor": mentions.meta.get("next_token") if mentions.meta else None
    }


@conditional_tool("get_highlights_tweets", "Retrieves highlighted tweets from a user's timeline")
async def get_highlights_tweets(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Fetches highlighted/pinned tweets (simulated using user timeline)."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_users_tweets(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "public_metrics"]
    )
    return {
        "tweets": [tweet.data for tweet in (tweets.data or [])],
        "note": "Simulated - returns user's recent tweets"
    }


@conditional_tool("search_twitter", "Search Twitter with a query, includes engagement metrics and author info")
async def search_twitter(query: str, product: Optional[str] = "Top", count: Optional[int] = 100,
                         cursor: Optional[str] = None) -> Dict:
    """Searches Twitter for recent tweets with full metrics."""
    sort_order = "relevancy" if product == "Top" else "recency"
    effective_count = max(10, min(count or 100, 100))

    client, _ = initialize_twitter_clients()
    response = client.search_recent_tweets(
        query=query,
        max_results=effective_count,
        sort_order=sort_order,
        next_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics", "entities"],
        expansions=["author_id"],
        user_fields=["id", "name", "username", "profile_image_url"]
    )

    users = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            users[user.id] = {
                "id": user.id,
                "name": user.name,
                "username": user.username,
                "profile_image_url": getattr(user, 'profile_image_url', None)
            }

    tweets = []
    for tweet in (response.data or []):
        tweet_data = tweet.data if hasattr(tweet, 'data') else tweet
        author_id = tweet_data.get('author_id') or getattr(tweet, 'author_id', None)
        author = users.get(author_id, {})
        metrics = tweet_data.get('public_metrics', {}) or {}

        tweets.append({
            "id": tweet_data.get('id') or tweet.id,
            "text": tweet_data.get('text') or tweet.text,
            "created_at": str(tweet_data.get('created_at') or getattr(tweet, 'created_at', '')),
            "author_id": author_id,
            "author_name": author.get('name', ''),
            "author_username": author.get('username', ''),
            "likes": metrics.get('like_count', 0),
            "retweets": metrics.get('retweet_count', 0),
            "replies": metrics.get('reply_count', 0),
            "quotes": metrics.get('quote_count', 0),
            "has_article": '/i/article/' in str(tweet_data.get('entities', {}).get('urls', []))
        })

    return {
        "tweets": tweets,
        "next_cursor": response.meta.get('next_token') if response.meta else None
    }


@conditional_tool("search_articles", "Search for tweets that contain X articles on a topic")
async def search_articles(query: str, count: Optional[int] = 50, cursor: Optional[str] = None) -> Dict:
    """Searches for tweets containing X articles."""
    search_count = min((count or 50) * 2, 100)

    client, _ = initialize_twitter_clients()
    response = client.search_recent_tweets(
        query=f"{query} has:links",
        max_results=search_count,
        sort_order="relevancy",
        next_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics", "entities"],
        expansions=["author_id"],
        user_fields=["id", "name", "username", "profile_image_url"]
    )

    users = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            users[user.id] = {"name": user.name, "username": user.username}

    articles = []
    for tweet in (response.data or []):
        tweet_data = tweet.data if hasattr(tweet, 'data') else tweet
        entities = tweet_data.get('entities', {}) or {}
        urls = entities.get('urls', []) or []

        for url_obj in urls:
            expanded_url = url_obj.get('expanded_url', '') if isinstance(url_obj, dict) else ''
            if '/i/article/' in expanded_url:
                author_id = tweet_data.get('author_id')
                author = users.get(author_id, {})
                metrics = tweet_data.get('public_metrics', {}) or {}

                articles.append({
                    "tweet_id": tweet_data.get('id'),
                    "text": tweet_data.get('text'),
                    "created_at": str(tweet_data.get('created_at', '')),
                    "author_id": author_id,
                    "author_name": author.get('name', ''),
                    "author_username": author.get('username', ''),
                    "article_title": url_obj.get('title', ''),
                    "article_url": expanded_url,
                    "likes": metrics.get('like_count', 0),
                    "retweets": metrics.get('retweet_count', 0),
                })
                break

        if len(articles) >= (count or 50):
            break

    return {
        "articles": articles,
        "count": len(articles),
        "next_cursor": response.meta.get('next_token') if response.meta else None
    }


@conditional_tool("get_trends", "Retrieves trending topics on Twitter")
async def get_trends(woeid: Optional[int] = 1, count: Optional[int] = 50) -> List[Dict]:
    """Fetches trending topics. WOEID 1 = Worldwide."""
    _, v1_api = initialize_twitter_clients()
    trends = v1_api.get_place_trends(id=woeid)
    trends = trends[0]["trends"]
    return trends[:count]


@conditional_tool("get_article", "Fetch full content of an X/Twitter article from a tweet or article URL")
async def get_article(url: str) -> Dict:
    """Fetches article content using Playwright (required for JS rendering)."""
    if not PLAYWRIGHT_AVAILABLE:
        return error_response(
            "dependency_missing",
            "Playwright not installed",
            status=501,
            tool="get_article",
            details={
                "url": url,
                "hint": "Run: pip install playwright && playwright install chromium",
            },
        )

    article_url = url
    tweet_match = re.search(r'(?:twitter\.com|x\.com)/\w+/status/(\d+)', url)

    if tweet_match and '/i/article/' not in url:
        tweet_id = tweet_match.group(1)
        client, _ = initialize_twitter_clients()
        tweet = client.get_tweet(id=tweet_id, tweet_fields=["id", "text", "entities"])

        if tweet.data and hasattr(tweet.data, 'entities') and tweet.data.entities:
            urls = tweet.data.entities.get('urls', [])
            for u in urls:
                expanded = u.get('expanded_url', '')
                if '/i/article/' in expanded:
                    article_url = expanded
                    break

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()

            if article_url.startswith('http://'):
                article_url = article_url.replace('http://', 'https://')

            await page.goto(article_url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)

            content = await page.evaluate('''() => {
                const selectors = ['article[data-testid="article"]', '[data-testid="article-content"]',
                                   'article', '[role="article"]', '.article-content', 'main'];
                let articleElement = null;
                for (const selector of selectors) {
                    articleElement = document.querySelector(selector);
                    if (articleElement) break;
                }
                if (!articleElement) articleElement = document.body;

                const titleEl = document.querySelector('h1') || document.querySelector('[data-testid="article-title"]');
                const authorEl = document.querySelector('[data-testid="User-Name"]') || document.querySelector('a[href*="/"]');
                const paragraphs = articleElement.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li');
                const textContent = Array.from(paragraphs).map(p => p.innerText.trim()).filter(t => t.length > 0).join('\\n\\n');

                return {
                    title: titleEl ? titleEl.innerText : '',
                    author: authorEl ? authorEl.innerText : '',
                    content: textContent || articleElement.innerText,
                    url: window.location.href
                };
            }''')

            await browser.close()

            return {
                "title": content.get('title', ''),
                "author": content.get('author', ''),
                "content": content.get('content', ''),
                "url": content.get('url', article_url),
                "source": "x_article"
            }

    except Exception as e:
        logger.error(f"Error fetching article: {str(e)}")
        return error_response(
            "article_fetch_failed",
            "Failed to fetch article content",
            status=502,
            tool="get_article",
            details={"url": article_url, "error": str(e)},
        )


# =============================================================================
# ENGAGE GROUP - Likes, bookmarks, retweets
# =============================================================================

@conditional_tool("favorite_tweet", "Like a tweet")
async def favorite_tweet(tweet_id: str) -> Dict:
    """Likes a tweet."""
    enforce_rate_limit("like_actions")
    client, _ = initialize_twitter_clients()
    result = client.like(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "liked": result.data["liked"]}


@conditional_tool("unfavorite_tweet", "Unlike a tweet")
async def unfavorite_tweet(tweet_id: str) -> Dict:
    """Unlikes a tweet."""
    enforce_rate_limit("like_actions")
    client, _ = initialize_twitter_clients()
    result = client.unlike(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "liked": False}


@conditional_tool("bookmark_tweet", "Add a tweet to bookmarks")
async def bookmark_tweet(tweet_id: str) -> Dict:
    """Bookmarks a tweet."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.bookmark(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "bookmarked": result.data["bookmarked"]}


@conditional_tool("delete_bookmark", "Remove a tweet from bookmarks")
async def delete_bookmark(tweet_id: str) -> Dict:
    """Removes a bookmark."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.remove_bookmark(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "bookmarked": False}


@conditional_tool("get_bookmarks", "Get your bookmarked tweets")
async def get_bookmarks(count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Fetches bookmarked tweets."""
    client, _ = initialize_twitter_clients()
    bookmarks = client.get_bookmarks(
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"]
    )
    return {
        "tweets": [tweet.data for tweet in (bookmarks.data or [])],
        "next_cursor": bookmarks.meta.get("next_token") if bookmarks.meta else None
    }


@conditional_tool("delete_all_bookmarks", "Delete all bookmarks")
async def delete_all_bookmarks() -> Dict:
    """Deletes all bookmarks (iterates through all)."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    deleted = 0
    cursor = None
    while True:
        bookmarks = client.get_bookmarks(max_results=100, pagination_token=cursor)
        for bookmark in (bookmarks.data or []):
            client.remove_bookmark(tweet_id=bookmark.id)
            deleted += 1

        cursor = bookmarks.meta.get("next_token") if bookmarks.meta else None
        if not cursor:
            break
    return {"status": "completed", "deleted_count": deleted}


@conditional_tool("retweet", "Retweet a tweet")
async def retweet(tweet_id: str) -> Dict:
    """Retweets a tweet."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.retweet(tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "retweeted": result.data["retweeted"]}


@conditional_tool("unretweet", "Remove a retweet")
async def unretweet(tweet_id: str) -> Dict:
    """Removes a retweet."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.unretweet(source_tweet_id=tweet_id)
    return {"tweet_id": tweet_id, "retweeted": False}


@conditional_tool("get_retweets", "Get users who retweeted a tweet")
async def get_retweets(tweet_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets users who retweeted a specific tweet."""
    client, _ = initialize_twitter_clients()
    retweeters = client.get_retweeters(
        id=tweet_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username", "profile_image_url"]
    )
    return {
        "users": [user.data for user in (retweeters.data or [])],
        "next_cursor": retweeters.meta.get("next_token") if retweeters.meta else None
    }


# =============================================================================
# PUBLISH GROUP - Post, delete, threads
# =============================================================================

@conditional_tool("post_tweet", "Post a tweet with optional media, reply, and tags")
async def post_tweet(text: str, media_paths: Optional[List[str]] = None,
                     reply_to: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict:
    """Posts a tweet."""
    enforce_rate_limit("tweet_actions")

    client, v1_api = initialize_twitter_clients()
    tweet_data = {"text": text}

    if reply_to:
        tweet_data["in_reply_to_tweet_id"] = reply_to
    if tags:
        tweet_data["text"] += " " + " ".join(f"#{tag}" for tag in tags)
    if media_paths:
        media_ids = []
        for path in media_paths:
            media = v1_api.media_upload(filename=path)
            media_ids.append(media.media_id_string)
        tweet_data["media_ids"] = media_ids

    tweet = client.create_tweet(**tweet_data)
    return tweet.data if tweet.data else None


@conditional_tool("delete_tweet", "Delete a tweet by its ID")
async def delete_tweet(tweet_id: str) -> Dict:
    """Deletes a tweet."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.delete_tweet(id=tweet_id)
    return {"id": tweet_id, "deleted": result.data["deleted"]}


@conditional_tool("quote_tweet", "Quote tweet with your comment")
async def quote_tweet(text: str, quoted_tweet_id: str, media_paths: Optional[List[str]] = None) -> Dict:
    """Creates a quote tweet."""
    enforce_rate_limit("tweet_actions")

    client, v1_api = initialize_twitter_clients()
    tweet_data = {"text": text, "quote_tweet_id": quoted_tweet_id}

    if media_paths:
        media_ids = []
        for path in media_paths:
            media = v1_api.media_upload(filename=path)
            media_ids.append(media.media_id_string)
        tweet_data["media_ids"] = media_ids

    tweet = client.create_tweet(**tweet_data)
    return tweet.data if tweet.data else None


@conditional_tool("create_thread", "Post a thread of multiple tweets")
async def create_thread(tweets: List[str], media_paths_per_tweet: Optional[List[List[str]]] = None) -> Dict:
    """Creates a thread of tweets. Each tweet replies to the previous one."""
    enforce_rate_limit("tweet_actions")

    client, v1_api = initialize_twitter_clients()
    posted_tweets = []
    reply_to = None

    for i, text in enumerate(tweets):
        tweet_data = {"text": text}

        if reply_to:
            tweet_data["in_reply_to_tweet_id"] = reply_to

        if media_paths_per_tweet and i < len(media_paths_per_tweet) and media_paths_per_tweet[i]:
            media_ids = []
            for path in media_paths_per_tweet[i]:
                media = v1_api.media_upload(filename=path)
                media_ids.append(media.media_id_string)
            tweet_data["media_ids"] = media_ids

        tweet = client.create_tweet(**tweet_data)
        if tweet.data:
            posted_tweets.append(tweet.data)
            reply_to = tweet.data.get("id")

    return {
        "thread_length": len(posted_tweets),
        "tweets": posted_tweets,
        "first_tweet_id": posted_tweets[0].get("id") if posted_tweets else None
    }


@conditional_tool("create_poll_tweet", "Create a tweet with a poll")
async def create_poll_tweet(text: str, choices: List[str], duration_minutes: int) -> Dict:
    """Creates a poll tweet."""
    enforce_rate_limit("tweet_actions")

    client, _ = initialize_twitter_clients()
    poll_data = {
        "text": text,
        "poll_options": choices,
        "poll_duration_minutes": max(5, min(duration_minutes, 10080))
    }
    tweet = client.create_tweet(**poll_data)
    return tweet.data if tweet.data else None


@conditional_tool("vote_on_poll", "Vote on a poll (not supported by API)")
async def vote_on_poll(tweet_id: str, choice: str) -> Dict:
    """Note: Twitter API v2 doesn't support programmatic poll voting."""
    return {
        "tweet_id": tweet_id,
        "choice": choice,
        "status": "not_supported",
        "message": "Twitter API v2 does not support programmatic poll voting"
    }


# =============================================================================
# SOCIAL GROUP - Follow, block, mute
# =============================================================================

@conditional_tool("follow_user", "Follow a user")
async def follow_user(user_id: str) -> Dict:
    """Follows a user."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    result = client.follow_user(target_user_id=user_id)
    return {"user_id": user_id, "following": result.data["following"]}


@conditional_tool("unfollow_user", "Unfollow a user")
async def unfollow_user(user_id: str) -> Dict:
    """Unfollows a user."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    result = client.unfollow_user(target_user_id=user_id)
    return {"user_id": user_id, "following": False}


@conditional_tool("block_user", "Block a user")
async def block_user(user_id: str) -> Dict:
    """Blocks a user."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    result = client.block(target_user_id=user_id)
    return {"user_id": user_id, "blocking": result.data["blocking"]}


@conditional_tool("unblock_user", "Unblock a user")
async def unblock_user(user_id: str) -> Dict:
    """Unblocks a user."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    result = client.unblock(target_user_id=user_id)
    return {"user_id": user_id, "blocking": False}


@conditional_tool("get_blocked_users", "Get list of blocked users")
async def get_blocked_users(count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets list of blocked users."""
    client, _ = initialize_twitter_clients()
    blocked = client.get_blocked(
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username"]
    )
    return {
        "users": [user.data for user in (blocked.data or [])],
        "next_cursor": blocked.meta.get("next_token") if blocked.meta else None
    }


@conditional_tool("mute_user", "Mute a user")
async def mute_user(user_id: str) -> Dict:
    """Mutes a user."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    result = client.mute(target_user_id=user_id)
    return {"user_id": user_id, "muting": result.data["muting"]}


@conditional_tool("unmute_user", "Unmute a user")
async def unmute_user(user_id: str) -> Dict:
    """Unmutes a user."""
    enforce_rate_limit("follow_actions")
    client, _ = initialize_twitter_clients()
    result = client.unmute(target_user_id=user_id)
    return {"user_id": user_id, "muting": False}


@conditional_tool("get_muted_users", "Get list of muted users")
async def get_muted_users(count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets list of muted users."""
    client, _ = initialize_twitter_clients()
    muted = client.get_muted(
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username"]
    )
    return {
        "users": [user.data for user in (muted.data or [])],
        "next_cursor": muted.meta.get("next_token") if muted.meta else None
    }


# =============================================================================
# CONVERSATIONS GROUP - Threads, replies
# =============================================================================

@conditional_tool("get_conversation", "Get full conversation/thread for a tweet")
async def get_conversation(tweet_id: str, count: Optional[int] = 100) -> Dict:
    """Gets all tweets in a conversation thread."""
    client, _ = initialize_twitter_clients()

    # First get the tweet to find conversation_id
    tweet = client.get_tweet(id=tweet_id, tweet_fields=["conversation_id", "author_id"])
    if not tweet.data:
        return error_response(
            "not_found",
            "Tweet not found",
            status=404,
            tool="get_conversation",
            details={"tweet_id": tweet_id},
        )

    conv_id = tweet.data.conversation_id

    # Search for all tweets in the conversation
    response = client.search_recent_tweets(
        query=f"conversation_id:{conv_id}",
        max_results=min(count, 100),
        tweet_fields=["id", "text", "created_at", "author_id", "in_reply_to_user_id", "public_metrics"],
        expansions=["author_id"],
        user_fields=["id", "name", "username"]
    )

    users = {}
    if response.includes and "users" in response.includes:
        users = {u.id: {"name": u.name, "username": u.username} for u in response.includes["users"]}

    tweets = []
    for t in (response.data or []):
        tweet_data = t.data if hasattr(t, 'data') else t
        author = users.get(tweet_data.get('author_id'), {})
        tweets.append({
            **tweet_data,
            "author_name": author.get("name"),
            "author_username": author.get("username")
        })

    return {
        "conversation_id": conv_id,
        "tweet_count": len(tweets),
        "tweets": tweets
    }


@conditional_tool("get_replies", "Get replies to a specific tweet")
async def get_replies(tweet_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets replies to a tweet."""
    client, _ = initialize_twitter_clients()

    # Get conversation_id first
    tweet = client.get_tweet(id=tweet_id, tweet_fields=["conversation_id"])
    if not tweet.data:
        return error_response(
            "not_found",
            "Tweet not found",
            status=404,
            tool="get_replies",
            details={"tweet_id": tweet_id},
        )

    conv_id = tweet.data.conversation_id

    # Search for replies (tweets in conversation that are replies)
    response = client.search_recent_tweets(
        query=f"conversation_id:{conv_id} is:reply",
        max_results=min(count, 100),
        next_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"],
        expansions=["author_id"],
        user_fields=["id", "name", "username"]
    )

    users = {}
    if response.includes and "users" in response.includes:
        users = {u.id: {"name": u.name, "username": u.username} for u in response.includes["users"]}

    replies = []
    for t in (response.data or []):
        tweet_data = t.data if hasattr(t, 'data') else t
        author = users.get(tweet_data.get('author_id'), {})
        replies.append({
            **tweet_data,
            "author_name": author.get("name"),
            "author_username": author.get("username")
        })

    return {
        "tweet_id": tweet_id,
        "reply_count": len(replies),
        "replies": replies,
        "next_cursor": response.meta.get("next_token") if response.meta else None
    }


@conditional_tool("get_quote_tweets", "Get tweets that quote a specific tweet")
async def get_quote_tweets(tweet_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets tweets that quote a specific tweet."""
    client, _ = initialize_twitter_clients()
    quotes = client.get_quote_tweets(
        id=tweet_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"],
        expansions=["author_id"],
        user_fields=["id", "name", "username"]
    )

    users = {}
    if quotes.includes and "users" in quotes.includes:
        users = {u.id: {"name": u.name, "username": u.username} for u in quotes.includes["users"]}

    result = []
    for t in (quotes.data or []):
        tweet_data = t.data if hasattr(t, 'data') else t
        author = users.get(tweet_data.get('author_id'), {})
        result.append({
            **tweet_data,
            "author_name": author.get("name"),
            "author_username": author.get("username")
        })

    return {
        "tweet_id": tweet_id,
        "quote_count": len(result),
        "quotes": result,
        "next_cursor": quotes.meta.get("next_token") if quotes.meta else None
    }


@conditional_tool("hide_reply", "Hide a reply to your tweet")
async def hide_reply(tweet_id: str) -> Dict:
    """Hides a reply to one of your tweets."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.hide_reply(id=tweet_id)
    return {"tweet_id": tweet_id, "hidden": result.data["hidden"]}


@conditional_tool("unhide_reply", "Unhide a previously hidden reply")
async def unhide_reply(tweet_id: str) -> Dict:
    """Unhides a reply."""
    enforce_rate_limit("tweet_actions")
    client, _ = initialize_twitter_clients()
    result = client.unhide_reply(id=tweet_id)
    return {"tweet_id": tweet_id, "hidden": False}


# =============================================================================
# LISTS GROUP - Create and manage lists
# =============================================================================

@conditional_tool("create_list", "Create a new list")
async def create_list(name: str, description: Optional[str] = None, private: bool = False) -> Dict:
    """Creates a new list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.create_list(name=name, description=description, private=private)
    return result.data if result.data else None


@conditional_tool("delete_list", "Delete a list")
async def delete_list(list_id: str) -> Dict:
    """Deletes a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.delete_list(id=list_id)
    return {"list_id": list_id, "deleted": result.data["deleted"]}


@conditional_tool("update_list", "Update a list's name, description, or privacy")
async def update_list(list_id: str, name: Optional[str] = None,
                      description: Optional[str] = None, private: Optional[bool] = None) -> Dict:
    """Updates a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.update_list(id=list_id, name=name, description=description, private=private)
    return {"list_id": list_id, "updated": result.data["updated"]}


@conditional_tool("get_list", "Get details about a specific list")
async def get_list(list_id: str) -> Dict:
    """Gets list details."""
    client, _ = initialize_twitter_clients()
    result = client.get_list(id=list_id, list_fields=["id", "name", "description", "member_count", "owner_id", "private"])
    return result.data if result.data else None


@conditional_tool("get_user_lists", "Get lists owned by a user")
async def get_user_lists(user_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets lists owned by a user."""
    client, _ = initialize_twitter_clients()
    lists = client.get_owned_lists(
        id=user_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        list_fields=["id", "name", "description", "member_count", "private"]
    )
    return {
        "lists": [l.data for l in (lists.data or [])],
        "next_cursor": lists.meta.get("next_token") if lists.meta else None
    }


@conditional_tool("get_list_tweets", "Get tweets from a list's timeline")
async def get_list_tweets(list_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets tweets from a list."""
    client, _ = initialize_twitter_clients()
    tweets = client.get_list_tweets(
        id=list_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        tweet_fields=["id", "text", "created_at", "author_id", "public_metrics"]
    )
    return {
        "tweets": [tweet.data for tweet in (tweets.data or [])],
        "next_cursor": tweets.meta.get("next_token") if tweets.meta else None
    }


@conditional_tool("get_list_members", "Get members of a list")
async def get_list_members(list_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets members of a list."""
    client, _ = initialize_twitter_clients()
    members = client.get_list_members(
        id=list_id,
        max_results=min(count, 100),
        pagination_token=cursor,
        user_fields=["id", "name", "username", "profile_image_url"]
    )
    return {
        "users": [user.data for user in (members.data or [])],
        "next_cursor": members.meta.get("next_token") if members.meta else None
    }


@conditional_tool("add_list_member", "Add a user to a list")
async def add_list_member(list_id: str, user_id: str) -> Dict:
    """Adds a user to a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.add_list_member(id=list_id, user_id=user_id)
    return {"list_id": list_id, "user_id": user_id, "is_member": result.data["is_member"]}


@conditional_tool("remove_list_member", "Remove a user from a list")
async def remove_list_member(list_id: str, user_id: str) -> Dict:
    """Removes a user from a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.remove_list_member(id=list_id, user_id=user_id)
    return {"list_id": list_id, "user_id": user_id, "is_member": False}


@conditional_tool("follow_list", "Follow a list")
async def follow_list(list_id: str) -> Dict:
    """Follows a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.follow_list(list_id=list_id)
    return {"list_id": list_id, "following": result.data["following"]}


@conditional_tool("unfollow_list", "Unfollow a list")
async def unfollow_list(list_id: str) -> Dict:
    """Unfollows a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.unfollow_list(list_id=list_id)
    return {"list_id": list_id, "following": False}


@conditional_tool("pin_list", "Pin a list to your profile")
async def pin_list(list_id: str) -> Dict:
    """Pins a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.pin_list(list_id=list_id)
    return {"list_id": list_id, "pinned": result.data["pinned"]}


@conditional_tool("unpin_list", "Unpin a list from your profile")
async def unpin_list(list_id: str) -> Dict:
    """Unpins a list."""
    enforce_rate_limit("list_actions")
    client, _ = initialize_twitter_clients()
    result = client.unpin_list(list_id=list_id)
    return {"list_id": list_id, "pinned": False}


# =============================================================================
# DMS GROUP - Direct messages
# =============================================================================

@conditional_tool("send_dm", "Send a direct message to a user")
async def send_dm(participant_id: str, text: str) -> Dict:
    """Sends a direct message."""
    enforce_rate_limit("dm_actions")
    client, _ = initialize_twitter_clients()
    result = client.create_direct_message(participant_id=participant_id, text=text)
    return result.data if result.data else None


@conditional_tool("get_dm_conversations", "Get your DM conversations")
async def get_dm_conversations(count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets DM conversations."""
    client, _ = initialize_twitter_clients()
    conversations = client.get_direct_message_events(
        max_results=min(count, 100),
        pagination_token=cursor
    )
    return {
        "events": [e.data for e in (conversations.data or [])],
        "next_cursor": conversations.meta.get("next_token") if conversations.meta else None
    }


@conditional_tool("get_dm_events", "Get messages in a DM conversation")
async def get_dm_events(dm_conversation_id: str, count: Optional[int] = 100, cursor: Optional[str] = None) -> Dict:
    """Gets messages in a DM conversation."""
    client, _ = initialize_twitter_clients()
    events = client.get_direct_message_events(
        dm_conversation_id=dm_conversation_id,
        max_results=min(count, 100),
        pagination_token=cursor
    )
    return {
        "events": [e.data for e in (events.data or [])],
        "next_cursor": events.meta.get("next_token") if events.meta else None
    }


# =============================================================================
# ACCOUNT GROUP - Profile management
# =============================================================================

@conditional_tool("get_me", "Get your own user profile")
async def get_me() -> Dict:
    """Gets the authenticated user's profile."""
    client, _ = initialize_twitter_clients()
    user = client.get_me(
        user_fields=["id", "name", "username", "profile_image_url", "description",
                     "public_metrics", "verified", "created_at", "location", "url"]
    )
    return user.data if user.data else None


# =============================================================================
# Server entry point
# =============================================================================

def run():
    """Entry point for running the FastMCP server."""
    pm = get_permission_manager()
    logger.info(f"Starting X-Twitter-MCP with profile: {pm.get_profile().value}")
    logger.info(f"Enabled tools: {len(pm.get_enabled_tools())}")
    return server.run()

