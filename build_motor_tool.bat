@echo off
REM Motor Tool Build Script - Windows

echo ================================
echo   Motor Tool Build Script
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python first.
    pause
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

REM Start building
echo.
echo Building motor_tool...
pyinstaller --onefile ^
    --name motor_tool ^
    --console ^
    --clean ^
    --paths src ^
    src\motor_tool.py

if %errorlevel% equ 0 (
    echo.
    echo ================================
    echo   Build Successful!
    echo ================================
    echo Executable location: .\dist\motor_tool.exe
    echo.
    echo Usage:
    echo   .\dist\motor_tool.exe
) else (
    echo.
    echo Build failed. Please check the error messages.
    pause
    exit /b 1
)

pause
