@echo off
setlocal

echo ========================================
echo   AutomationTest EXE Builder
echo ========================================
echo.

echo [1] Checking Python...
py --version
if errorlevel 1 (
    echo Python not found.
    pause
    exit /b 1
)

echo.
echo [2] Checking PyInstaller...
py -m PyInstaller --version
if errorlevel 1 (
    echo PyInstaller not found.
    echo Installing...
    py -m pip install pyinstaller
    if errorlevel 1 (
        echo PyInstaller installation failed.
        pause
        exit /b 1
    )
)

echo.
echo [3] Building...

py -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --windowed ^
    --name AutomationTest ^
    --add-data "adb;adb" ^
    automation_test.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD FINISHED
echo ========================================
echo.

if exist "dist\AutomationTest.exe" (
    echo EXE created successfully:
    echo dist\AutomationTest.exe
) else (
    echo WARNING: EXE was not found.
)

echo.
pause
