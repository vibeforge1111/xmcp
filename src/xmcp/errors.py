from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from tweepy.errors import (
    Forbidden,
    NotFound,
    TooManyRequests,
    TweepyException,
    Unauthorized,
)


@dataclass
class MCPError(Exception):
    error_type: str
    message: str
    status: int = 500
    details: Optional[Dict[str, Any]] = None


class RateLimitError(MCPError):
    def __init__(self, action_type: str, retry_after_seconds: Optional[int] = None) -> None:
        details: Dict[str, Any] = {"action_type": action_type}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            error_type="rate_limit_exceeded",
            message="Rate limit exceeded",
            status=429,
            details=details,
        )


class PermissionDeniedError(MCPError):
    def __init__(self, tool_name: str, profile: Optional[str] = None) -> None:
        details: Dict[str, Any] = {"tool": tool_name}
        if profile:
            details["profile"] = profile
        super().__init__(
            error_type="permission_denied",
            message="Tool is disabled by the current permission profile",
            status=403,
            details=details,
        )


class DependencyMissingError(MCPError):
    def __init__(self, dependency: str, hint: Optional[str] = None) -> None:
        details: Dict[str, Any] = {"dependency": dependency}
        if hint:
            details["hint"] = hint
        super().__init__(
            error_type="dependency_missing",
            message="Required dependency is not installed",
            status=501,
            details=details,
        )


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def error_response(
    error_type: str,
    message: str,
    *,
    status: Optional[int] = None,
    tool: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ok": False,
        "error": {
            "type": error_type,
            "message": message,
        },
        "timestamp": _utc_timestamp(),
    }
    if status is not None:
        payload["error"]["status"] = status
    if details is not None:
        payload["error"]["details"] = details
    if tool is not None:
        payload["tool"] = tool
    return payload


def handle_exception(err: Exception, *, tool: Optional[str] = None) -> Dict[str, Any]:
    if isinstance(err, MCPError):
        return error_response(
            err.error_type,
            err.message,
            status=err.status,
            tool=tool,
            details=err.details,
        )

    if isinstance(err, EnvironmentError):
        return error_response(
            "configuration_error",
            str(err),
            status=500,
            tool=tool,
        )

    if isinstance(err, TooManyRequests):
        return error_response(
            "rate_limit_exceeded",
            str(err),
            status=429,
            tool=tool,
        )
    if isinstance(err, Unauthorized):
        return error_response(
            "unauthorized",
            str(err),
            status=401,
            tool=tool,
        )
    if isinstance(err, Forbidden):
        return error_response(
            "forbidden",
            str(err),
            status=403,
            tool=tool,
        )
    if isinstance(err, NotFound):
        return error_response(
            "not_found",
            str(err),
            status=404,
            tool=tool,
        )
    if isinstance(err, TweepyException):
        return error_response(
            "twitter_api_error",
            str(err),
            status=502,
            tool=tool,
        )

    return error_response(
        "internal_error",
        str(err),
        status=500,
        tool=tool,
    )
