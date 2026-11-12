from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hibira_client import HibiraClient, HibiraError, split_list

MAX_CHANNELS = 100
MAX_DATA_BYTES = 10240


class PublishEventTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        channels = split_list(tool_parameters.get("channels"))
        event = str(tool_parameters.get("event") or "").strip()
        data = tool_parameters.get("data")
        data = "" if data is None else str(data)
        if not channels:
            yield self.create_text_message("Enter at least one channel.")
            return
        if len(channels) > MAX_CHANNELS:
            yield self.create_text_message(f"At most {MAX_CHANNELS} channels per event.")
            return
        if not event:
            yield self.create_text_message("Enter an event name.")
            return
        if len(data.encode()) > MAX_DATA_BYTES:
            yield self.create_text_message("Data must be at most 10 KB.")
            return
        body: dict[str, Any] = {"name": event, "channels": channels, "data": data}
        socket_id = str(tool_parameters.get("socket_id") or "").strip()
        if socket_id:
            body["socket_id"] = socket_id
        try:
            response = HibiraClient(self.runtime.credentials).app_request("POST", "/events", body)
        except HibiraError as exc:
            yield self.create_text_message(f"Publish failed: {exc}")
            return
        result = {"event": event, "channels": channels, **response}
        yield self.create_json_message(result)
        yield self.create_text_message(f"Published {event} to {len(channels)} channel(s).")
