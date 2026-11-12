from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from hibira_client import HibiraClient, HibiraError


class HibiraProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        client = HibiraClient(credentials)
        try:
            client.app_request("GET", "/channels")
        except HibiraError as exc:
            raise ToolProviderCredentialValidationError(str(exc)) from exc
        if bool(client.push_instance_id) != bool(client.push_secret_key):
            raise ToolProviderCredentialValidationError(
                "Fill in both Push Instance ID and Push Secret Key, or leave both empty"
            )
