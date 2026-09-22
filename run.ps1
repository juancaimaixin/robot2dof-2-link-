param(
    [string]$Python = 'python',
    [string[]]$Arguments = @('-m', 'pytest', '-p', 'no:cacheprovider', '-q')
)
$ErrorActionPreference = 'Stop'
$previousPythonPath = $env:PYTHONPATH
$previousEncoding = $env:PYTHONUTF8
$previousGitCeiling = $env:GIT_CEILING_DIRECTORIES
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
    $env:PYTHONUTF8 = '1'
    $env:GIT_CEILING_DIRECTORIES = Split-Path -Parent $PSScriptRoot
    & $Python @Arguments
    $resultCode = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $previousPythonPath
    $env:PYTHONUTF8 = $previousEncoding
    $env:GIT_CEILING_DIRECTORIES = $previousGitCeiling
    Pop-Location
}
exit $resultCode
