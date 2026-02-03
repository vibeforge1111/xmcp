from x_twitter_mcp.errors import RateLimitError, error_response, handle_exception


def test_error_response_shape():
    resp = error_response(
        "bad_request",
        "Invalid input",
        status=400,
        tool="search_twitter",
        details={"field": "query"},
    )
    assert resp["ok"] is False
    assert resp["error"]["type"] == "bad_request"
    assert resp["error"]["message"] == "Invalid input"
    assert resp["error"]["status"] == 400
    assert resp["error"]["details"]["field"] == "query"
    assert resp["tool"] == "search_twitter"
    assert "timestamp" in resp


def test_handle_exception_rate_limit():
    resp = handle_exception(
        RateLimitError("tweet_actions", retry_after_seconds=10),
        tool="post_tweet",
    )
    assert resp["error"]["type"] == "rate_limit_exceeded"
    assert resp["error"]["status"] == 429
    assert resp["error"]["details"]["action_type"] == "tweet_actions"
    assert resp["error"]["details"]["retry_after_seconds"] == 10
    assert resp["tool"] == "post_tweet"


def test_handle_exception_generic():
    resp = handle_exception(Exception("boom"), tool="get_tweet_details")
    assert resp["error"]["type"] == "internal_error"
    assert resp["error"]["status"] == 500
    assert resp["tool"] == "get_tweet_details"
