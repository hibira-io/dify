import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hibira_client import HibiraClient, HibiraError, split_list

LIMITS = {"interests": 100, "users": 1000}


def build_payload(title: str, body: str, deep_link: str, data: dict[str, Any] | None) -> dict[str, Any]:
    extra = {"data": data} if data else {}
    web_notification: dict[str, Any] = {"title": title, "body": body}
    if deep_link:
        web_notification["deep_link"] = deep_link
    return {
        "apns": {"aps": {"alert": {"title": title, "body": body}}, **extra},
        "fcm": {"notification": {"title": title, "body": body}, **extra},
        "web": {"notification": web_notification, **extra},
    }


class SendPushTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        target = tool_parameters.get("target") or "interests"
        if target not in LIMITS:
            yield self.create_text_message("Send To must be interests or users.")
            return
        recipients = split_list(tool_parameters.get("recipients"))
        title = str(tool_parameters.get("title") or "").strip()
        if not recipients:
            yield self.create_text_message(f"Enter at least one of the {target}.")
            return
        if len(recipients) > LIMITS[target]:
            yield self.create_text_message(f"At most {LIMITS[target]} {target} per notification.")
            return
        if not title:
            yield self.create_text_message("Enter a title.")
            return
        deep_link = str(tool_parameters.get("deep_link") or "").strip()
        if deep_link and not deep_link.startswith("https://"):
            yield self.create_text_message("The link must start with https://.")
            return
        data = None
        raw = tool_parameters.get("data")
        if raw not in (None, ""):
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                yield self.create_text_message("Custom Data must be a JSON object.")
                return
            if not isinstance(data, dict):
                yield self.create_text_message("Custom Data must be a JSON object.")
                return
        payload = build_payload(title, str(tool_parameters.get("body") or ""), deep_link, data)
        payload[target] = recipients
        try:
            response = HibiraClient(self.runtime.credentials).push_request(
                f"/publish_api/v1/instances/{{instance}}/publishes/{target}", payload
            )
        except HibiraError as exc:
            yield self.create_text_message(f"Push failed: {exc}")
            return
        yield self.create_json_message({"target": target, "recipients": recipients, **response})
        yield self.create_text_message(f"Push sent to {len(recipients)} {target}.")
