from collections.abc import Generator
from typing import Any
from urllib.parse import quote

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hibira_client import HibiraClient, HibiraError, summarize_approval, wait_minutes


class GetApprovalTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        approval_id = str(tool_parameters.get("approval_id") or "").strip()
        if not approval_id:
            yield self.create_text_message("Enter the approval ID.")
            return
        client = HibiraClient(self.runtime.credentials)
        try:
            approval = client.app_request("GET", f"/approvals/{quote(approval_id, safe='')}")
            approval = client.wait_for_approval(approval, wait_minutes(tool_parameters.get("wait_minutes"), 0))
        except HibiraError as exc:
            yield self.create_text_message(f"Could not read the approval: {exc}")
            return
        yield self.create_json_message(approval)
        yield self.create_text_message(summarize_approval(approval))
