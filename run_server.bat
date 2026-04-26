@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%\server"

where node >nul 2>&1
if errorlevel 1 (
    echo [ARI] ERROR: node is not in PATH. Please install Node.js and restart.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ARI] ERROR: npm is not in PATH. Please install Node.js and restart.
    pause
    exit /b 1
)

echo [ARI] Installing dependencies (if needed)...
if not exist "node_modules" (
    call npm install
    if errorlevel 1 (
        echo [ARI] npm install failed.
        echo Check: node -v  ^&^& npm -v
        pause
        exit /b 1
    )
)

if not exist "package.json" (
    echo [ARI] server package.json not found.
    pause
    exit /b 1
)

echo [ARI] Starting Node backend on http://localhost:3000
mkdir "%PROJECT_DIR%logs" 2>nul

set "RESTART_MAX=5"
set "RESTART_COUNT=0"

:loop
call npm start >> "%PROJECT_DIR%logs\server.log" 2>&1
set "EXITCODE=%errorlevel%"

if %EXITCODE% neq 0 (
    echo.
    echo [ARI] Server exited with code %EXITCODE%. Restarting in 5 seconds...
    echo Last log entries:
    powershell -Command "Get-Content '%PROJECT_DIR%logs\server.log' -Tail 10 -ErrorAction SilentlyContinue"
    timeout /t 5 >nul
    set /a RESTART_COUNT+=1
    if %RESTART_COUNT% GEQ %RESTART_MAX% (
        echo [ARI] Restart limit reached (%RESTART_MAX%). Check logs\server.log
        echo Last 30 lines of log:
        powershell -Command "Get-Content '%PROJECT_DIR%logs\server.log' -Tail 30 -ErrorAction SilentlyContinue"
        pause
        exit /b 1
    )
    goto :loop
)

exit /b %EXITCODE%
