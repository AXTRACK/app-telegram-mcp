"""Regression coverage for read-only principals that may read every chat."""

from pathlib import Path

import pytest

from src.client.connection import set_request_token
from src.config.server_config import ServerConfig, ServerMode, set_config
from src.server_components.session_acl import (
    AclConfigError,
    check_mtproto_api_access,
    check_pre_tool_access,
    filter_tool_result,
    validate_acl_config,
)


@pytest.fixture
def all_chats_acl(tmp_path: Path):
    path = tmp_path / "acl.yaml"
    path.write_text(
        """blocked_peers:
  - 777000
principals:
  analyst:
    all_chats: true
    read_only: true
    allow_global_search: true
    allow_mtproto: false
  limited:
    chats:
      - me
    read_only: true
""",
        encoding="utf-8",
    )
    config = ServerConfig(_cli_parse_args=[])
    config.server_mode = ServerMode.HTTP_AUTH
    config.acl_enabled = True
    config.acl_config_path = str(path)
    config.acl_deny_unlisted_principals = True
    set_config(config)
    set_request_token("analyst")
    return path


def test_all_chats_read_only_validates_and_reads_any_chat(all_chats_acl):
    validate_acl_config()
    for operation in ("get_messages", "get_chat_info"):
        assert check_pre_tool_access(operation, {"chat_id": -1001234567890}) is None
        assert check_pre_tool_access(operation, {"chat_id": "@newchannel"}) is None
    assert check_pre_tool_access("find_chats", {"query": "new"}) is None
    assert check_pre_tool_access("search_messages_globally", {"query": "news"}) is None


def test_all_chats_does_not_filter_unblocked_results(all_chats_acl):
    chats = {"ok": True, "chats": [{"id": -100123}, {"id": -100456}]}
    assert filter_tool_result("find_chats", chats) == chats
    messages = {"ok": True, "messages": [{"chat_id": -100123, "id": 1}]}
    assert filter_tool_result("search_messages_globally", messages) == messages
    history = {"ok": True, "chat_id": -100456, "messages": [{"id": 2}]}
    assert filter_tool_result("get_messages", history) == history


def test_all_chats_keeps_write_and_raw_mtproto_denied(all_chats_acl):
    for operation in ("send_message", "edit_message", "send_message_to_phone"):
        denial = check_pre_tool_access(operation, {"chat_id": -100123})
        assert denial is not None and denial["ok"] is False
    assert check_pre_tool_access("invoke_mtproto", {"params_json": "{}"})["ok"] is False
    assert check_mtproto_api_access("analyst", allow_dangerous=False)["ok"] is False


def test_all_chats_still_blocks_sensitive_peers(all_chats_acl):
    assert check_pre_tool_access("get_messages", {"chat_id": 777000})["ok"] is False
    chats = {"ok": True, "chats": [{"id": 777000}, {"id": -100123}]}
    assert filter_tool_result("find_chats", chats)["chats"] == [{"id": -100123}]


def test_existing_limited_principal_still_restricted(all_chats_acl):
    set_request_token("limited")
    assert check_pre_tool_access("get_messages", {"chat_id": -100123})["ok"] is False


@pytest.mark.parametrize("value", ["yes", "1", "[]"])
def test_all_chats_requires_boolean_value(tmp_path: Path, value: str):
    path = tmp_path / "acl.yaml"
    path.write_text(
        f"principals:\n  analyst:\n    all_chats: {value}\n    read_only: true\n",
        encoding="utf-8",
    )
    config = ServerConfig(_cli_parse_args=[])
    config.server_mode = ServerMode.HTTP_AUTH
    config.acl_enabled = True
    config.acl_config_path = str(path)
    set_config(config)
    with pytest.raises(AclConfigError, match="all_chats"):
        validate_acl_config()
