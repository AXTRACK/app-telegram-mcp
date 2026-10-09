# AXTRACK Telegram MCP integration

This repository is the source-owned fork of `leshchenko1979/fast-mcp-telegram`; keep the upstream Git history and license intact. The current production NAS image remains pinned to upstream commit `c3779a2f4abf093b8fac9d6776b5ad097ff73df5` until a new exact-SHA build and runtime acceptance succeed.

## Scoped capabilities

1. `list_dialogs`: paginated discovery of Telegram dialogs visible to the authenticated principal. Filter every result through the existing per-principal session ACL; do not expose unauthorized chat identifiers, titles, counts or preview messages. Never implicitly mark a dialog read.
2. `get_read_state`: return bounded per-dialog unread/read cursor metadata, only for an ACL-authorized chat. Reading metadata must not change Telegram read state.
3. `mark_chat_read`: explicit **write** operation with chat binding and optional bounded `max_id`, separately disabled for ordinary digest principals. Reuse the existing auth/session ACL and tool restriction framework; enforce write permission *before* any Telegram RPC, and audit the principal, chat and requested cursor. Never mark as read during `get_messages`, `list_dialogs`, or digest collection.

## Security and tests

- The user-account MTProto plane must not gain fixed-owner Bot API authority; that belongs to `AXTRACK/app-agent-notifications`.
- No raw MTProto bypass of read/write ACL, and no unauthorized chat enumeration through pagination, counts or errors.
- Regression tests must cover allowed/denied chat, ACL-filtered pagination, read-state side-effect absence, opt-in write grant, bounded cursor, audit event, Telegram RPC failure, and no implicit mark-read during retrieval.
- Preserve existing high-level tools and upstream behavior for current principals.

## Migration gates

Implement against the current fork's tool registration, auth, ACL and Telethon client abstractions; avoid parallel authorization infrastructure. Route deterministic tests through `AXTRACK/build-tests` after allowlisting (tracking issue: `AXTRACK/build-tests#226`). Production Compose/image pin changes belong to `AXTRACK/agent-gateway` and require separate rollout and rollback verification.

**Status:** migration contract only. These three tools are not implemented by this document.
