@echo off
REM Motor Tool Build Script - Windows
REM Builds a single motor_tool.exe (auto-detects CANable / Damiao, --type to force)

echo ================================
echo   Motor Tool Build Script
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

REM Build motor_tool
echo.
echo Building motor_tool...
pyinstaller --onefile ^
    --name motor_tool ^
    --console ^
    --clean ^
    --paths src ^
    src\motor_tool.py

if %errorlevel% neq 0 (
    echo motor_tool build failed. Please check the error messages.
    if not defined CI pause
    exit /b 1
)

echo.
echo ================================
echo   Build Successful!
echo ================================
echo Executable: .\dist\motor_tool.exe
echo.
echo Usage:
echo   .\dist\motor_tool.exe                  REM auto-detect CANable / Damiao
echo   .\dist\motor_tool.exe --type canable   REM force CANable protocol
echo   .\dist\motor_tool.exe --type damiao    REM force Damiao protocol

if not defined CI pause
