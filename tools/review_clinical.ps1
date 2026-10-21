[CmdletBinding()]
param(
    [ValidateSet("codex", "opencode")]
    [string]$Backend = "codex",

    [string]$Model,

    [string[]]$Paths = @(),

    [Parameter(Mandatory = $true)]
    [string]$Prompt
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$contractPath = Join-Path $repoRoot "docs\clinical-review-contract.md"
$contract = Get-Content -LiteralPath $contractPath -Raw -Encoding UTF8

$requestedPaths = @()
foreach ($pathItem in $Paths) {
    if (-not [string]::IsNullOrWhiteSpace($pathItem)) {
        $requestedPaths += $pathItem -split "[;`r`n]+" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }
}
if ($requestedPaths.Count -eq 0) {
    throw "Name one or more repository-relative files. Separate multiple paths with semicolons."
}

$resolvedPaths = @()
foreach ($relativePath in $requestedPaths) {
    $absolutePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $relativePath))
    if (-not $absolutePath.StartsWith($repoRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path must stay inside the Clinical Medicine repository: $relativePath"
    }
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
        throw "Review file does not exist: $relativePath"
    }
    $resolvedPaths += $relativePath
}

$pathSection = "`nFiles in scope:`n- " + ($resolvedPaths -join "`n- ")
$fullPrompt = @"
You are a read-only clinical learning-card reviewer.

$contract

Task:
$Prompt
$pathSection
"@

Push-Location $repoRoot
try {
    if ($Backend -eq "codex") {
        $codexCommand = Get-Command codex -ErrorAction SilentlyContinue
        $codexPath = if ($codexCommand) { $codexCommand.Source } else { $null }
        if (-not $codexCommand) {
            $codexShim = Join-Path $env:APPDATA "npm\codex.ps1"
            if (Test-Path -LiteralPath $codexShim -PathType Leaf) {
                $codexPath = $codexShim
            } else {
                throw "Codex CLI was not found. Install or sign in to Codex CLI, then retry."
            }
        }

        $arguments = @("exec", "--sandbox", "read-only", "-C", $repoRoot)
        if (-not [string]::IsNullOrWhiteSpace($Model)) {
            $arguments += @("--model", $Model)
        }
        $arguments += "-"
        $fullPrompt | & $codexPath @arguments
        exit $LASTEXITCODE
    }

    $opencodeCommand = Get-Command opencode -ErrorAction SilentlyContinue
    $opencodeExe = $null
    if ($opencodeCommand -and $opencodeCommand.Source -and $opencodeCommand.Source.EndsWith(".exe", [System.StringComparison]::OrdinalIgnoreCase)) {
        $opencodeExe = $opencodeCommand.Source
    }
    $npmRoot = if ($opencodeCommand -and $opencodeCommand.Source) { Split-Path -Parent $opencodeCommand.Source } else { Join-Path $env:APPDATA "npm" }
    $candidate = Join-Path $npmRoot "node_modules\@opencode\cli\bin\opencode.exe"
    if (-not $opencodeExe -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        $opencodeExe = $candidate
    }
    if (-not $opencodeExe) {
        throw "OpenCode native CLI was not found. Install or sign in to OpenCode, then retry."
    }

    if ([string]::IsNullOrWhiteSpace($Model)) {
        $Model = "opencode-go/deepseek-v4.1-flash"
    }

    $previousConfig = $env:OPENCODE_CONFIG_CONTENT
    $previousPwd = $env:PWD
    $env:OPENCODE_CONFIG_CONTENT = '{"permission":{"*":"deny","read":"allow","grep":"allow","glob":"allow","list":"allow"}}'
    $env:PWD = $repoRoot
    try {
        $arguments = @("run", "--standalone", "--format", "json", "--auto", "--model", $Model, $fullPrompt)
        & $opencodeExe @arguments
        exit $LASTEXITCODE
    }
    finally {
        $env:OPENCODE_CONFIG_CONTENT = $previousConfig
        $env:PWD = $previousPwd
    }
}
finally {
    Pop-Location
}
