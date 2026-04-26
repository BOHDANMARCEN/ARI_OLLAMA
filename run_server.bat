@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%\server"

if not exist "package.json" (
    echo [ARI] server package not found.
    pause
    exit /b 1
)

echo [ARI] Starting Node backend on http://localhost:3000
npm start

if not "%ERRORLEVEL%"=="0" (
    echo.
    echo [ARI] Server exited with code %ERRORLEVEL%.
    pause
)

exit /b %ERRORLEVEL%
