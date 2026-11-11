"""Regression tests for native ID-cursor history pagination."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.tools.search import incremental


class FakeClient:
    def __init__(self, ids):
        self.ids = ids
        self.calls = []

    def iter_messages(self, entity, **kwargs):
        self.calls.append(kwargs)

        async def messages():
            for mid in self.ids:
                if mid > kwargs["min_id"]:
                    yield SimpleNamespace(id=mid)
        return messages()


@pytest.mark.asyncio
async def test_incremental_skips_noncontiguous_ids_without_losing_position(monkeypatch):
    client = FakeClient([101, 105, 109, 120])
    monkeypatch.setattr(incremental, "get_entity_by_id", AsyncMock(return_value=object()))
    monkeypatch.setattr(incremental, "get_connected_client", AsyncMock(return_value=client))
    monkeypatch.setattr(incremental, "_build_result_for_message", AsyncMock(side_effect=lambda m, e: {"id": m.id}))
    first = await incremental.read_messages_after_id("channel", 100, 2)
    assert [m["id"] for m in first["messages"]] == [101, 105]
    assert first["has_more"] is True
    assert first["last_scanned_id"] == 105
    second = await incremental.read_messages_after_id("channel", first["last_scanned_id"], 2)
    assert [m["id"] for m in second["messages"]] == [109, 120]
    assert second["has_more"] is False
    assert client.calls[0]["reverse"] is True
    assert client.calls[0]["limit"] == 3


@pytest.mark.asyncio
async def test_non_displayable_messages_still_advance_scanned_cursor(monkeypatch):
    client = FakeClient([5, 7])
    monkeypatch.setattr(incremental, "get_entity_by_id", AsyncMock(return_value=object()))
    monkeypatch.setattr(incremental, "get_connected_client", AsyncMock(return_value=client))
    monkeypatch.setattr(incremental, "_build_result_for_message", AsyncMock(side_effect=lambda m, e: None if m.id == 7 else {"id": m.id}))
    result = await incremental.read_messages_after_id("channel", 0, 2)
    assert result["last_scanned_id"] == 7
    assert result["scanned_count"] == 2
    assert result["messages"] == [{"id": 5}]


@pytest.mark.asyncio
async def test_invalid_cursor_fails_closed():
    with pytest.raises(ValueError):
        await incremental.read_messages_after_id("channel", -1)
    with pytest.raises(ValueError):
        await incremental.read_messages_after_id("channel", 0, 0)
