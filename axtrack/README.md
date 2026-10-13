# AXTRACK Telegram MCP integration

This repository is a fork of `leshchenko1979/fast-mcp-telegram`; upstream Git history remains authoritative for the imported core. The Synology deployment currently remains owned by `AXTRACK/agent-gateway`.

## Source and deployment boundaries

- This fork owns future AXTRACK Telegram user-account MCP extensions and regression tests.
- `AXTRACK/app-agent-notifications` owns fixed-destination Bot API notification and emergency behavior. Do not merge that runtime into this MTProto fork.
- `AXTRACK/agent-gateway` owns Compose, runtime volumes, session persistence, tunnel endpoints, credentials, image pinning, backup and rollback.

## Read-state extension acceptance contract (not yet implemented)

1. `list_dialogs` enumerates the authenticated user's dialogs with bounded pagination and applies the existing principal/session ACL **before returning any peer or metadata**.
2. `get_read_state(chat_id)` returns Telegram read state only after the same ACL check. It must never acknowledge or advance the read cursor.
3. `mark_chat_read(chat_id, max_id)` is a separately permissioned **write** capability, disabled for read-only profiles. It checks chat ACL, validates the bounded target message ID, records an audit event and advances the cursor only after an explicit tool call. No read or digest operation invokes it implicitly.
4. Raw MTProto remains disabled in normal ChatGPT profiles; no generic write permissions are granted by these helpers.
5. Regression coverage must include forbidden chats, bot sessions, pagination boundaries, read-only profiles, absent/invalid message IDs, and verification that read calls do not change unread state.

## Migration gates

No new read-state tool is claimed as available by this document. Before release: implement against current upstream registration/auth/ACL abstractions, validate deterministic tests through `AXTRACK/build-tests` at the exact candidate SHA, perform selected live Telegram account acceptance checks, then publish an immutable image and switch `AXTRACK/agent-gateway` by explicit image pin with rollback.
