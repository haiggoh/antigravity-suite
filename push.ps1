# Antigravity Suite - Quick Commit & Push (PowerShell)
param (
    [string]$Message = "feat: update antigravity-suite packages and rules"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       Antigravity Suite - Push Updates           " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "[=] Working tree clean, nothing to commit." -ForegroundColor Yellow
} else {
    Write-Host "[*] Committing changes: $Message" -ForegroundColor Green
    git commit -m $Message
}

Write-Host "[*] Pushing to origin main..." -ForegroundColor Green
git push origin main
Write-Host "[+] Push complete!" -ForegroundColor Green
