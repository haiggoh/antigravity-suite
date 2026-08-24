@echo off
:: Antigravity Suite - Quick Commit & Push (cmd.exe fallback)
:: Usage: push.bat
::        push.bat "Optional custom commit message"

setlocal enabledelayedexpansion
cd /d "%~dp0"

set MESSAGE=%~1
if "%MESSAGE%"=="" set MESSAGE=feat: update antigravity-suite packages and rules

echo ==================================================
echo        Antigravity Suite - Push Updates
echo ==================================================

git add -A

git diff --cached --quiet
if %errorlevel%==0 (
    echo [=] Working tree clean, nothing to commit.
) else (
    echo [*] Committing: %MESSAGE%
    git commit -m "%MESSAGE%"
)

echo [*] Pushing to origin main...
git push origin main

if %errorlevel%==0 (
    echo [+] Push complete!
) else (
    echo [-] Push failed. Check output above.
    exit /b 1
)
