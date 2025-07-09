@ECHO OFF

REM Claude Multi-Agent PM Framework - Windows CLI Wrapper
REM Provides Windows compatibility for the claude-pm command

SETLOCAL EnableDelayedExpansion

REM Get the directory where this batch file is located
SET "BIN_DIR=%~dp0"
SET "PACKAGE_DIR=%BIN_DIR%.."

REM Check if Node.js is available
WHERE node >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO Error: Node.js is required but not found in PATH
    ECHO Please install Node.js 16.0.0 or higher
    EXIT /B 1
)

REM Check Node.js version
FOR /F "tokens=1" %%i IN ('node --version') DO SET NODE_VERSION=%%i
SET NODE_VERSION=%NODE_VERSION:v=%

REM Basic version check (simplified)
FOR /F "tokens=1 delims=." %%i IN ("%NODE_VERSION%") DO SET MAJOR_VERSION=%%i
IF %MAJOR_VERSION% LSS 16 (
    ECHO Error: Node.js 16.0.0 or higher is required. Found: v%NODE_VERSION%
    EXIT /B 1
)

REM Execute the main CLI script
node "%BIN_DIR%claude-pm" %*

REM Exit with the same error code as the Node.js process
EXIT /B %ERRORLEVEL%