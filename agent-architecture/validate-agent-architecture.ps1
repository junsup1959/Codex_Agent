# 한국어 주석: canonical validator는 Python이며, 이 파일은 기존 ps1 호출 호환용 wrapper다.
param(
    [switch]$Explain
)

$ErrorActionPreference = 'Stop'
$Root = $env:CODEX_HOME
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = 'C:\Users\SECURUS\.codex'
}
$Validator = Join-Path $Root 'agent-architecture\validate-agent-architecture.py'
$Args = @($Validator)
if ($Explain) {
    $Args += '--explain'
}
# 한국어 주석: PowerShell ExecutionPolicy 영향을 줄이기 위해 실제 검증은 Python 프로세스에 위임한다.
& python @Args
exit $LASTEXITCODE
