$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$env:CODEX_CONTEXT_LEDGER_DB = if ($env:CODEX_CONTEXT_LEDGER_DB) {
  $env:CODEX_CONTEXT_LEDGER_DB
} elseif ($env:CODEX_HOME) {
  Join-Path $env:CODEX_HOME 'state\context-ledger.sqlite'
} else {
  Join-Path $HOME '.codex\state\context-ledger.sqlite'
}
$env:PYTHONPATH = Join-Path $ProjectRoot 'src'

& (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -m context_ledger_mcp.server `
  --transport streamable-http `
  --host 127.0.0.1 `
  --port 8765 `
  --path /mcp
