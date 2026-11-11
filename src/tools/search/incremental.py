"""Read-only, ID-cursor Telegram history for reliable incremental consumers.

Uses Telethon's native reverse iter_messages(min_id=...) rather than
date-window slicing or assuming contiguous Telegram message IDs.
"""
from src.client.connection import get_connected_client
from src.utils.entity import get_entity_by_id
from .results import _build_result_for_message


async def read_messages_after_id(chat_id: str, after_id: int, limit: int = 50) -> dict:
    if isinstance(after_id, bool) or not isinstance(after_id, int) or after_id < 0:
        raise ValueError("after_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    entity = await get_entity_by_id(chat_id)
    if entity is None:
        raise ValueError("Chat not found")
    client = await get_connected_client()
    messages = []
    raw_seen = 0
    last_scanned_id = after_id
    async for message in client.iter_messages(
        entity, min_id=after_id, reverse=True, limit=limit + 1
    ):
        if message is None:
            continue
        raw_seen += 1
        if raw_seen > limit:
            break
        if message.id <= last_scanned_id:
            raise RuntimeError("Telegram history order is not strictly increasing")
        last_scanned_id = message.id
        built = await _build_result_for_message(message, entity)
        if built is not None:
            messages.append(built)
    return {
        "messages": messages,
        "has_more": raw_seen > limit,
        "last_scanned_id": last_scanned_id,
        "scanned_count": min(raw_seen, limit),
    }
