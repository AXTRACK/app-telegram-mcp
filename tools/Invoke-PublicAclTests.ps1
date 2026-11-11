$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

python -m pip install --disable-pip-version-check uv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv sync --group dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv run pytest tests/test_session_acl.py tests/test_acl_all_chats.py tests/test_incremental_history.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'TELEGRAM_ACL_AND_HISTORY_PUBLIC_BUILD_TESTS_PASS'
