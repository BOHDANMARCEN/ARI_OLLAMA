@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%\frontend"

if not exist "package.json" (
    echo [ARI] frontend package not found.
    pause
    exit /b 1
)

echo [ARI] Starting frontend dev server on http://localhost:5173
npm run dev

if not "%ERRORLEVEL%"=="0" (
    echo.
    echo [ARI] Frontend exited with code %ERRORLEVEL%.
    pause
)

exit /b %ERRORLEVEL%
