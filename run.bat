@echo off
cd /d "%~dp0"
title MatchLink Company Templater Server
echo =========================================================
echo  Starting MatchLink Company Name Templater Server...
echo =========================================================
echo.

:: Detect Python executable
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py"
    ) else (
        echo ERROR: Python was not found on your system PATH.
        echo Please install Python 3 and ensure "Add Python to PATH" is checked.
        pause
        exit /b 1
    )
)

:: Check if dependencies are installed
echo Checking dependencies...
%PYTHON_CMD% -c "import fastapi, uvicorn, pandas, openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing missing requirements from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install Python dependencies.
        pause
        exit /b 1
    )
)

echo.
echo Opening browser to http://localhost:8001...
start "" "http://localhost:8001"
echo.
echo Launching FastAPI dev server...
%PYTHON_CMD% -m uvicorn main:app --port 8001 --reload
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start the server.
    pause
)

