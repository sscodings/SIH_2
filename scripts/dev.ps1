# PowerShell wrapper for ChainNetra dev tasks
param (
    [Parameter(Position=0, Mandatory=$false)]
    [string]$Action = "dev"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

# Find python
$Python = "python"
if (Test-Path "$RepoRoot\.venv\Scripts\python.exe") {
    $Python = "$RepoRoot\.venv\Scripts\python.exe"
} elseif (Test-Path "$RepoRoot\backend\venv\Scripts\python.exe") {
    $Python = "$RepoRoot\backend\venv\Scripts\python.exe"
}

& $Python "$ScriptDir\dev.py" $Action
exit $LASTEXITCODE
