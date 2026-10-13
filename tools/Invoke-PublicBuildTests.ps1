$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
python -m pip install --disable-pip-version-check uv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv sync --group dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv run pytest -m 'not integration and not slow' -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'TELEGRAM_MCP_PUBLIC_BUILD_TESTS_PASS'
