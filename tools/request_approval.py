from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hibira_client import HibiraClient, HibiraError, split_list, summarize_approval, wait_minutes

class RequestApprovalTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        title = str(tool_parameters.get("title") or "").strip()
        if not title:
            yield self.create_text_message("Enter the question to approve.")
            return
        options = split_list(tool_parameters.get("options"))
        if options and not 2 <= len(options) <= 4:
            yield self.create_text_message("Options needs 2 to 4 choices.")
            return
        interests = split_list(tool_parameters.get("push_interests"))
        users = split_list(tool_parameters.get("push_users"))
        if interests and users:
            yield self.create_text_message("Use Push to Interests or Push to User IDs, not both.")
            return
        body: dict[str, Any] = {
            "title": title,
            "agent": str(tool_parameters.get("agent") or "").strip() or "Dify",
        }
        if options:
            body["options"] = options
        details = str(tool_parameters.get("details") or "").strip()
        if details:
            body["details"] = details
        expires = tool_parameters.get("expires_in_minutes")
        if expires not in (None, ""):
            body["expires_in_minutes"] = int(float(expires))
        channel = str(tool_parameters.get("channel") or "").strip()
        if channel:
            body["channel"] = channel
        if interests:
            body["push_interests"] = interests
        if users:
            body["push_users"] = users

        client = HibiraClient(self.runtime.credentials)
        try:
            approval = client.app_request("POST", "/approvals", body)
            approval = client.wait_for_approval(approval, wait_minutes(tool_parameters.get("wait_minutes"), 5))
        except HibiraError as exc:
            yield self.create_text_message(f"Approval request failed: {exc}")
            return
        yield self.create_json_message(approval)
        yield self.create_text_message(summarize_approval(approval))
