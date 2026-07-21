# Claude2AGY & AGY2Claude One-Line Installer for Windows PowerShell

$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:USERPROFILE ".claude2agy"
$BinDir = Join-Path $env:USERPROFILE ".local\bin"

Write-Host "Installing Claude2AGY & AGY2Claude for Windows..." -ForegroundColor Cyan

# 1. Check Python
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $PythonCmd) {
    Write-Error "Python is required but not installed or not in PATH."
    exit 1
}

# 2. Setup directory
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

$ScriptDir = $PSScriptRoot
if ($ScriptDir -and (Test-Path (Join-Path $ScriptDir "claude2agy"))) {
    Copy-Item -Path (Join-Path $ScriptDir "claude2agy") -Destination $InstallDir -Recurse -Force
} else {
    Write-Host "Downloading source code..."
    $ZipUrl = "https://github.com/Antigravity/claude2agy/archive/refs/heads/main.zip"
    $ZipPath = Join-Path $env:TEMP "claude2agy.zip"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath
    Expand-Archive -Path $ZipPath -DestinationPath $env:TEMP -Force
    Copy-Item -Path (Join-Path $env:TEMP "claude2agy-main\*") -Destination $InstallDir -Recurse -Force
    Remove-Item $ZipPath -Force
}

# 3. Create Bin Directory
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

# 4. Create CMD wrappers
$Claude2AgyCmd = @"
@echo off
set PYTHONPATH=%USERPROFILE%\.claude2agy
python -m claude2agy.cli %*
"@

$Agy2ClaudeCmd = @"
@echo off
set PYTHONPATH=%USERPROFILE%\.claude2agy
python -m claude2agy.cli --reverse %*
"@

Set-Content -Path (Join-Path $BinDir "claude2agy.cmd") -Value $Claude2AgyCmd
Set-Content -Path (Join-Path $BinDir "agy2claude.cmd") -Value $Agy2ClaudeCmd

# 5. Add BinDir to User PATH if missing
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
    Write-Host "Added $BinDir to User PATH." -ForegroundColor Yellow
}

Write-Host "`nInstallation completed successfully!" -ForegroundColor Green
Write-Host "Commands installed:"
Write-Host "  - claude2agy (Claude Code -> Antigravity)"
Write-Host "  - agy2claude (Antigravity -> Claude Code)"
Write-Host "`nNote: Please restart your PowerShell terminal for PATH changes to take effect." -ForegroundColor Yellow
