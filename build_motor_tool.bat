@echo off
REM Motor Tool Build Script - Windows
REM Builds two versions: motor_tool_canable.exe and motor_tool_damiao.exe

echo ================================
echo   Motor Tool Build Script
echo   Dual Version Build
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python first.
    if not defined CI pause
    exit /b 1
)

echo Python version:
python --version

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Install PyInstaller
echo.
echo Installing PyInstaller...
pip install pyinstaller

set BUILD_FAILED=0

REM Build CANable version
echo.
echo Building motor_tool_canable...
pyinstaller --onefile ^
    --name motor_tool_canable ^
    --console ^
    --clean ^
    --paths src ^
    src\motor_tool_canable.py

if %errorlevel% neq 0 (
    echo motor_tool_canable build failed. Please check the error messages.
    set BUILD_FAILED=1
)

REM Build Damiao version
echo.
echo Building motor_tool_damiao...
pyinstaller --onefile ^
    --name motor_tool_damiao ^
    --console ^
    --clean ^
    --paths src ^
    src\motor_tool_damiao.py

if %errorlevel% neq 0 (
    echo motor_tool_damiao build failed. Please check the error messages.
    set BUILD_FAILED=1
)

if "%BUILD_FAILED%"=="0" (
    echo.
    echo ================================
    echo   Build Successful!
    echo ================================
    echo Executable locations:
    echo   CANable: .\dist\motor_tool_canable.exe
    echo   Damiao : .\dist\motor_tool_damiao.exe
    echo.
    echo Usage:
    echo   .\dist\motor_tool_canable.exe
    echo   .\dist\motor_tool_damiao.exe
) else (
    echo.
    echo One or more builds failed. Please check the error messages.
    if not defined CI pause
    exit /b 1
)

if not defined CI pause
