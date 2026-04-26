@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv\Scripts\python.exe" (
    echo [ARI] .venv not found. Run setup first.
    pause
    exit /b 1
)

if "%ARI_MODEL%"=="" set "ARI_MODEL=qwen3.5:9b"
if "%ARI_THINK%"=="" set "ARI_THINK=0"

echo [ARI] Starting with model %ARI_MODEL%
echo [ARI] ARI_THINK=%ARI_THINK%

".venv\Scripts\python.exe" main.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ARI] Process exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
