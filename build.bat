@echo off
setlocal

title AutomationTest Builder

echo ==========================================
echo       AutomationTest EXE Builder
echo ==========================================
echo.

echo [1/6] Checking Python...
py --version
if errorlevel 1 (
    echo.
    echo ERROR: Python launcher not found.
    echo Please install Python 3.12 64-bit.
    pause
    exit /b 1
)

echo.
echo [2/6] Checking PyInstaller...
py -m PyInstaller --version
if errorlevel 1 (
    echo.
    echo PyInstaller not found.
    echo Installing PyInstaller...
    py -m pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo ERROR: PyInstaller installation failed.
        pause
        exit /b 1
    )
)

echo.
echo [3/6] Checking project files...

if not exist "automation_test.py" (
    echo ERROR: automation_test.py not found.
    pause
    exit /b 1
)

if not exist "adb\adb.exe" (
    echo ERROR: adb\adb.exe not found.
    pause
    exit /b 1
)

echo Project files OK.

echo.
echo [4/6] Cleaning old build...

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [5/6] Building AutomationTest.exe...

py -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name AutomationTest ^
    --add-data "adb;adb" ^
    automation_test.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo BUILD FAILED
    echo ==========================================
    pause
    exit /b 1
)

echo.
echo [6/6] Build completed.
echo.

if not exist "dist\AutomationTest.exe" (
    echo ERROR: EXE was not created.
    pause
    exit /b 1
)

echo ==========================================
echo SUCCESS!
echo ==========================================
echo.
echo EXE:
echo %CD%\dist\AutomationTest.exe
echo.

echo ADB:
echo %CD%\adb
echo.

echo ==========================================
echo You can now run AutomationTest.exe
echo ==========================================
echo.

pause
