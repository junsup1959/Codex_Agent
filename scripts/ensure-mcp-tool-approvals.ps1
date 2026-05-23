param(
    [string]$ConfigPath = $(if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "config.toml" } else { Join-Path $HOME ".codex\config.toml" }),
    [string[]]$Servers = @("MCP_DOCKER", "codex-context-ledger"),
    [switch]$Check,
    [switch]$PrintOnly,
    [switch]$SelfTest,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"

$KnownTools = @{
    "MCP_DOCKER" = @(
        "sequentialthinking",
        "get_library_docs",
        "execute_code",
        "resolve_library_id",
        "tdd_refactoring_guidance",
        "code_mode",
        "analyze_python_package",
        "analyze_python_file",
        "find_package_issues",
        "mcp_activate_profile",
        "mcp_create_profile",
        "fetch",
        "mcp_exec",
        "mcp_find",
        "read_graph",
        "find_long_functions",
        "delete_relations",
        "delete_observations",
        "create_entities",
        "get_package_metrics",
        "search_nodes",
        "open_nodes",
        "add_observations",
        "delete_entities",
        "analyze_test_coverage",
        "mcp_remove",
        "get_extraction_guidance",
        "create_relations"
    )
    "codex-context-ledger" = @(
        "initialize_run",
        "read_context_packet",
        "append_stage_pass",
        "record_artifact_ref",
        "write_context_packet",
        "mark_stale",
        "set_role_pass_readiness",
        "validate_stage_packet",
        "validate_stage_completion",
        "validate_context_revision",
        "record_mcp_quiescence",
        "validate_tool_sequence",
        "close_run",
        "query_run_ledger"
    )
}

function Escape-RegexLiteral {
    param([string]$Value)
    return [regex]::Escape($Value)
}

function Get-ToolTablePattern {
    param(
        [string]$ServerName,
        [string]$ToolName
    )
    $server = Escape-RegexLiteral $ServerName
    $tool = Escape-RegexLiteral $ToolName
    return ('(?ms)^\[mcp_servers\.{0}\.tools\.{1}\]\s*(.*?)(?=^\[|\z)' -f $server, $tool)
}

function Ensure-ApprovalBlock {
    param(
        [string]$Content,
        [string]$ServerName,
        [string]$ToolName
    )

    $header = "[mcp_servers.$ServerName.tools.$ToolName]"
    $pattern = Get-ToolTablePattern -ServerName $ServerName -ToolName $ToolName
    $match = [regex]::Match($Content, $pattern)

    if (-not $match.Success) {
        $append = "`r`n$header`r`napproval_mode = `"approve`"`r`n"
        return @{
            Content = $Content.TrimEnd() + $append
            Changed = $true
            Action = "added"
        }
    }

    $block = $match.Value
    if ($block -match '(?m)^\s*approval_mode\s*=\s*"approve"\s*$') {
        return @{
            Content = $Content
            Changed = $false
            Action = "present"
        }
    }

    if ($block -match '(?m)^\s*approval_mode\s*=.*$') {
        $newBlock = [regex]::Replace($block, '(?m)^\s*approval_mode\s*=.*$', 'approval_mode = "approve"', 1)
    } else {
        $newBlock = $block.TrimEnd() + "`r`napproval_mode = `"approve`"`r`n"
    }
    $newBlock = $newBlock -replace "`r?`n", "`r`n"

    return @{
        Content = $Content.Substring(0, $match.Index) + $newBlock + $Content.Substring($match.Index + $match.Length)
        Changed = $true
        Action = "updated"
    }
}

function Remove-StaleApprovalBlocks {
    param(
        [string]$Content,
        [string]$ServerName,
        [string[]]$AllowedTools
    )

    $allowed = @{}
    foreach ($tool in $AllowedTools) {
        $allowed[$tool] = $true
    }

    $server = Escape-RegexLiteral $ServerName
    $pattern = ('(?ms)^\[mcp_servers\.{0}\.tools\.([^\]]+)\]\s*(.*?)(?=^\[|\z)' -f $server)
    $matches = @([regex]::Matches($Content, $pattern))

    $removed = New-Object System.Collections.Generic.List[string]
    for ($i = $matches.Count - 1; $i -ge 0; $i--) {
        $match = $matches[$i]
        $toolName = $match.Groups[1].Value
        if (-not $allowed.ContainsKey($toolName)) {
            $Content = $Content.Remove($match.Index, $match.Length)
            $removed.Add($toolName)
        }
    }

    return @{
        Content = $Content
        RemovedTools = @($removed)
        Changed = ($removed.Count -gt 0)
    }
}

function Assert-StringEqual {
    param(
        [string]$Name,
        [string]$Actual,
        [string]$Expected
    )

    if ($Actual -cne $Expected) {
        throw "SelfTest failed: $Name"
    }
}

function Assert-ArrayEqual {
    param(
        [string]$Name,
        [string[]]$Actual,
        [string[]]$Expected
    )

    $actualText = $Actual -join "|"
    $expectedText = $Expected -join "|"
    if ($actualText -cne $expectedText) {
        throw "SelfTest failed: $Name"
    }
}

function Invoke-SelfTest {
    $server = "codex-context-ledger"
    $tool = "initialize_run"

    $missingInput = "[mcp_servers.$server]`r`n"
    $missingExpected = "[mcp_servers.$server]`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"approve`"`r`n"
    $missingResult = Ensure-ApprovalBlock -Content $missingInput -ServerName $server -ToolName $tool
    Assert-StringEqual "missing tool block" $missingResult.Content $missingExpected

    $wrongModeInput = "[mcp_servers.$server]`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"ask`"`r`n"
    $wrongModeExpected = "[mcp_servers.$server]`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"approve`"`r`n"
    $wrongModeResult = Ensure-ApprovalBlock -Content $wrongModeInput -ServerName $server -ToolName $tool
    Assert-StringEqual "wrong approval mode" $wrongModeResult.Content $wrongModeExpected

    $commentInput = "[mcp_servers.$server]`r`n# [mcp_servers.$server.tools.$tool]`r`n# approval_mode = `"ask`"`r`n"
    $commentExpected = "[mcp_servers.$server]`r`n# [mcp_servers.$server.tools.$tool]`r`n# approval_mode = `"ask`"`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"approve`"`r`n"
    $commentResult = Ensure-ApprovalBlock -Content $commentInput -ServerName $server -ToolName $tool
    Assert-StringEqual "commented table ignored" $commentResult.Content $commentExpected

    $staleInput = "[mcp_servers.$server]`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"approve`"`r`n[mcp_servers.$server.tools.initialize_run_extra]`r`napproval_mode = `"approve`"`r`n"
    $staleExpected = "[mcp_servers.$server]`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"approve`"`r`n"
    $staleResult = Remove-StaleApprovalBlocks -Content $staleInput -ServerName $server -AllowedTools @($tool)
    Assert-StringEqual "stale tool removed" $staleResult.Content $staleExpected
    Assert-ArrayEqual "stale tool classified" $staleResult.RemovedTools @("initialize_run_extra")

    $duplicateLookingInput = "[mcp_servers.$server]`r`n[mcp_servers.$server.tools.$tool]`r`napproval_mode = `"approve`"`r`n[mcp_servers.$server.tools.initialize_run_v2]`r`napproval_mode = `"approve`"`r`n"
    $duplicateLookingResult = Remove-StaleApprovalBlocks -Content $duplicateLookingInput -ServerName $server -AllowedTools @($tool)
    Assert-ArrayEqual "duplicate-looking tool treated as stale" $duplicateLookingResult.RemovedTools @("initialize_run_v2")

    $missingServerPattern = "(?m)^\[mcp_servers\.$(Escape-RegexLiteral $server)\]\s*$"
    if ("[mcp_servers.other]`r`n" -match $missingServerPattern) {
        throw "SelfTest failed: missing server detection"
    }

    Write-Host "SelfTest passed: ensure-mcp-tool-approvals fixtures"
}

if ($SelfTest) {
    Invoke-SelfTest
    exit 0
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "ConfigPath does not exist: $ConfigPath"
}

$config = [System.IO.File]::ReadAllText($ConfigPath)
$resultRows = New-Object System.Collections.Generic.List[object]
$changed = $false

foreach ($server in $Servers) {
    if (-not $KnownTools.ContainsKey($server)) {
        throw "Unknown server '$server'. Known servers: $($KnownTools.Keys -join ', ')"
    }

    $serverPattern = "(?m)^\[mcp_servers\.$(Escape-RegexLiteral $server)\]\s*$"
    if ($config -notmatch $serverPattern) {
        $resultRows.Add([pscustomobject]@{
            Server = $server
            Tool = "*"
            Action = "server_missing"
        })
        continue
    }

    $prune = Remove-StaleApprovalBlocks -Content $config -ServerName $server -AllowedTools $KnownTools[$server]
    $config = $prune.Content
    if ($prune.Changed) {
        $changed = $true
    }
    foreach ($tool in $prune.RemovedTools) {
        $resultRows.Add([pscustomobject]@{
            Server = $server
            Tool = $tool
            Action = "removed_stale"
        })
    }

    foreach ($tool in $KnownTools[$server]) {
        $ensure = Ensure-ApprovalBlock -Content $config -ServerName $server -ToolName $tool
        $config = $ensure.Content
        if ($ensure.Changed) {
            $changed = $true
        }
        $resultRows.Add([pscustomobject]@{
            Server = $server
            Tool = $tool
            Action = $ensure.Action
        })
    }
}

$missingOrChanged = @($resultRows | Where-Object { $_.Action -ne "present" })

if ($Check) {
    $resultRows | Format-Table -AutoSize
    if ($missingOrChanged.Count -gt 0) {
        Write-Error "MCP approval config needs updates."
    }
    exit 0
}

if ($PrintOnly) {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    Write-Output $config
    exit 0
}

if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($OutputPath, $config, [System.Text.UTF8Encoding]::new($false))
    $resultRows | Format-Table -AutoSize
    Write-Host "Wrote updated config to $OutputPath"
    exit 0
}

if ($changed) {
    [System.IO.File]::WriteAllText($ConfigPath, $config, [System.Text.UTF8Encoding]::new($false))
}

$resultRows | Format-Table -AutoSize
if ($changed) {
    Write-Host "Updated $ConfigPath"
} else {
    Write-Host "No changes needed in $ConfigPath"
}
