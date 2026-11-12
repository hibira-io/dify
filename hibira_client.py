"""Small client for the Hibira HTTP API.

Channel and approval requests are signed with the app key and secret, the
same scheme as the Pusher Channels HTTP API: auth_key, auth_timestamp,
auth_version, body_md5 and an HMAC-SHA256 auth_signature in the query
string. Push requests use the Push instance's secret key as a Bearer token.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import quote, urlencode

import httpx

API_URL = "https://ws.hibira.io"
TIMEOUT = 30.0
MAX_WAIT_SECONDS = 25


MAX_WAIT_MINUTES = 9


def summarize_approval(approval: dict[str, Any]) -> str:
    status = approval.get("status", "unknown")
    if status == "pending":
        return f"Waiting for an answer. Answer link: {approval.get('url', '')}".strip()
    if status in ("approved", "rejected"):
        text = f"{status.capitalize()}: {approval.get('choice', '')}".rstrip(": ")
        if approval.get("comment"):
            text += f" (comment: {approval['comment']})"
        return text
    return f"Approval {status}."


def wait_minutes(value: Any, default: float) -> float:
    try:
        minutes = float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        minutes = default
    return min(max(minutes, 0.0), MAX_WAIT_MINUTES)


class HibiraError(Exception):
    """A failed request, with a message that is safe to show to the user."""


def split_list(value: Any) -> list[str]:
    """Splits a comma or newline separated list, dropping empty entries."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value]
    else:
        items = str(value).replace("\n", ",").split(",")
    return [item.strip() for item in items if item.strip()]


def sign_query(
    method: str,
    path: str,
    key: str,
    secret: str,
    body: bytes | None,
    query: dict[str, str] | None = None,
    now: float | None = None,
) -> dict[str, str]:
    """Returns the query parameters, including auth_signature, for a request."""
    params: dict[str, str] = {k: str(v) for k, v in (query or {}).items()}
    params["auth_key"] = key
    params["auth_timestamp"] = str(int(now if now is not None else time.time()))
    params["auth_version"] = "1.0"
    if body:
        params["body_md5"] = hashlib.md5(body).hexdigest()  # noqa: S324 - required by the protocol
    canonical = "&".join(f"{k.lower()}={params[k]}" for k in sorted(params, key=str.lower))
    to_sign = f"{method.upper()}\n{path}\n{canonical}"
    params["auth_signature"] = hmac.new(secret.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
    return params


def _error_message(response: httpx.Response) -> str:
    text = response.text.strip()
    try:
        data = response.json()
        if isinstance(data, dict):
            text = str(data.get("error") or data.get("message") or data.get("description") or text)
    except ValueError:
        pass
    hints = {
        401: "check the app ID, key and secret",
        403: "the account is suspended or the key lacks access",
        404: "not found",
        429: "rate limited, try again shortly",
        501: "this app does not offer this feature (approvals need an app in a Hibira account)",
    }
    hint = hints.get(response.status_code)
    message = f"Hibira answered {response.status_code}"
    if text:
        message += f": {text[:300]}"
    if hint and hint not in message:
        message += f" ({hint})"
    return message


class HibiraClient:
    def __init__(self, credentials: dict[str, Any]):
        self.app_id = str(credentials.get("app_id") or "").strip()
        self.key = str(credentials.get("key") or "").strip()
        self.secret = str(credentials.get("secret") or "").strip()
        self.push_instance_id = str(credentials.get("push_instance_id") or "").strip()
        self.push_secret_key = str(credentials.get("push_secret_key") or "").strip()

    def app_request(
        self,
        method: str,
        resource: str,
        body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        timeout: float = TIMEOUT,
    ) -> dict[str, Any]:
        if not (self.app_id and self.key and self.secret):
            raise HibiraError("Set the App ID, Key and Secret in the Hibira credentials")
        path = f"/apps/{quote(self.app_id, safe='')}{resource}"
        raw = json.dumps(body, separators=(",", ":")).encode() if body is not None else None
        params = sign_query(method, path, self.key, self.secret, raw, query)
        headers = {"Content-Type": "application/json"} if raw is not None else {}
        try:
            response = httpx.request(
                method,
                f"{API_URL}{path}?{urlencode(params)}",
                content=raw,
                headers=headers,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            raise HibiraError(f"Could not reach Hibira: {type(exc).__name__}") from exc
        return self._parse(response)

    def push_request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if not (self.push_instance_id and self.push_secret_key):
            raise HibiraError(
                "Set the Push Instance ID and Push Secret Key in the Hibira credentials to send push notifications"
            )
        url = f"{API_URL}{path.replace('{instance}', quote(self.push_instance_id, safe=''))}"
        try:
            response = httpx.post(
                url,
                json=body,
                headers={"Authorization": f"Bearer {self.push_secret_key}"},
                timeout=TIMEOUT,
            )
        except httpx.HTTPError as exc:
            raise HibiraError(f"Could not reach Hibira: {type(exc).__name__}") from exc
        return self._parse(response)

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise HibiraError(_error_message(response))
        if not response.content:
            return {}
        try:
            data = response.json()
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {"result": data}

    def wait_for_approval(self, approval: dict[str, Any], wait_minutes: float) -> dict[str, Any]:
        """Long-polls a pending approval until it is answered, expires or time runs out."""
        deadline = time.monotonic() + max(0.0, wait_minutes) * 60
        current = approval
        url = approval.get("url")
        approval_id = str(approval.get("approval_id") or "")
        while current.get("status") == "pending" and approval_id:
            left = int(deadline - time.monotonic())
            if left <= 0:
                break
            wait = min(MAX_WAIT_SECONDS, left)
            current = self.app_request(
                "GET",
                f"/approvals/{quote(approval_id, safe='')}",
                query={"wait": str(wait)},
                timeout=wait + 15,
            )
        if url and "url" not in current:
            current = {**current, "url": url}
        return current
