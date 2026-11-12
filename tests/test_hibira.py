import json
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import hibira_client  # noqa: E402
from dify_plugin.entities.tool import ToolInvokeMessage  # noqa: E402
from hibira_client import HibiraClient, sign_query, split_list, summarize_approval, wait_minutes  # noqa: E402
from tools.get_approval import GetApprovalTool  # noqa: E402
from tools.publish_event import PublishEventTool  # noqa: E402
from tools.request_approval import RequestApprovalTool  # noqa: E402
from tools.send_push import SendPushTool  # noqa: E402

CREDS = {"app_id": "3", "key": "278d425bdf160c739803", "secret": "7ad3773142a6692b25b8",
         "push_instance_id": "inst", "push_secret_key": "psk"}


def test_signature_matches_pusher_reference():
    body = b'{"name":"foo","channels":["project-3"],"data":"{\\"some\\":\\"data\\"}"}'
    q = sign_query("POST", "/apps/3/events", CREDS["key"], CREDS["secret"], body, now=1353088179)
    assert q["body_md5"] == "ec365a775a4cd0599faeb73354201b6f"
    assert q["auth_signature"] == "da454824c97ba181a32ccc17a72625ba02771f50b50e1e7430e47a1f3f457e6c"


def test_helpers():
    assert split_list("a, b\n,c,") == ["a", "b", "c"]
    assert wait_minutes(None, 5) == 5
    assert wait_minutes(99, 5) == 9
    assert wait_minutes(-1, 5) == 0
    assert summarize_approval({"status": "approved", "choice": "Refund"}) == "Approved: Refund"


class Recorder:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, content=None, headers=None, timeout=None, json=None):
        self.calls.append(SimpleNamespace(method=method, url=url, content=content, headers=headers, json=json))
        status, data = self.responses.pop(0)
        return httpx.Response(status, json=data, request=httpx.Request(method, url))


def run(tool_cls, params):
    tool = tool_cls.__new__(tool_cls)
    tool.runtime = SimpleNamespace(credentials=CREDS)
    tool.response_type = ToolInvokeMessage
    msgs = list(tool._invoke(params))
    return [m.message for m in msgs]


@pytest.fixture
def http(monkeypatch):
    def install(responses):
        rec = Recorder(responses)
        monkeypatch.setattr(hibira_client.httpx, "request", rec)
        monkeypatch.setattr(hibira_client.httpx, "post", lambda url, **kw: rec("POST", url, **kw))
        return rec
    return install


def test_publish_event(http):
    rec = http([(200, {})])
    out = run(PublishEventTool, {"channels": "orders, private-a", "event": "order-updated", "data": '{"a":1}'})
    call = rec.calls[0]
    assert call.method == "POST" and call.url.startswith("https://ws.hibira.io/apps/3/events?")
    assert "auth_signature=" in call.url and "body_md5=" in call.url
    assert json.loads(call.content) == {"name": "order-updated", "channels": ["orders", "private-a"], "data": '{"a":1}'}
    assert out[0].json_object["channels"] == ["orders", "private-a"]


def test_publish_event_validates(http):
    rec = http([])
    out = run(PublishEventTool, {"channels": "", "event": "x", "data": ""})
    assert "at least one channel" in out[0].text and not rec.calls


def test_send_push_users(http):
    rec = http([(200, {"publishId": "pub-1"})])
    out = run(SendPushTool, {"target": "users", "recipients": "u1,u2", "title": "Hi", "body": "There",
                             "deep_link": "https://example.com", "data": '{"k":"v"}'})
    call = rec.calls[0]
    assert call.url == "https://ws.hibira.io/publish_api/v1/instances/inst/publishes/users"
    assert call.headers["Authorization"] == "Bearer psk"
    assert call.json["users"] == ["u1", "u2"]
    assert call.json["web"]["notification"]["deep_link"] == "https://example.com"
    assert call.json["fcm"]["data"] == {"k": "v"}
    assert out[0].json_object["publishId"] == "pub-1"


def test_request_approval_waits(http):
    created = {"approval_id": "apr_1", "status": "pending", "url": "https://hibira.io/approve/apr_1/t"}
    answered = {"approval_id": "apr_1", "status": "approved", "choice": "Approve"}
    rec = http([(201, created), (200, {**created}), (200, answered)])
    out = run(RequestApprovalTool, {"title": "Refund?", "options": "Approve, Reject", "wait_minutes": 1})
    assert json.loads(rec.calls[0].content) == {"title": "Refund?", "agent": "Dify", "options": ["Approve", "Reject"]}
    assert "wait=25" in rec.calls[1].url
    assert out[0].json_object["status"] == "approved"
    assert out[0].json_object["url"] == created["url"]
    assert out[1].text == "Approved: Approve"


def test_request_approval_no_wait_and_error(http):
    rec = http([(501, {"error": "this server does not offer approvals"})])
    out = run(RequestApprovalTool, {"title": "Refund?", "wait_minutes": 0})
    assert "501" in out[0].text and len(rec.calls) == 1


def test_get_approval(http):
    http([(200, {"approval_id": "apr_1", "status": "rejected", "choice": "Reject", "comment": "no"})])
    out = run(GetApprovalTool, {"approval_id": "apr_1"})
    assert out[1].text == "Rejected: Reject (comment: no)"
