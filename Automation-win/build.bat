@echo off
setlocal EnableExtensions

title AutomationTest Build

echo.
echo ============================================================
echo              AutomationTest EXE Builder
echo ============================================================
echo.

REM ============================================================
REM 项目目录
REM ============================================================

set "ROOT=%~dp0"
set "PY=%ROOT%automation_test.py"
set "ADB=%ROOT%adb"
set "RECORDINGS=%ROOT%recordings"

REM 最终输出目录
set "OUTPUT=%ROOT%dist\AutomationTest"

echo 项目目录：
echo %ROOT%
echo.

REM ============================================================
REM 检查 Python
REM ============================================================

echo [1/7] 检查 Python...

where python >nul 2>nul

if errorlevel 1 (
    echo.
    echo [错误] 没有找到 Python。
    echo.
    echo 请先安装 Python。
    echo.
    pause
    exit /b 1
)

python --version

if errorlevel 1 (
    echo.
    echo [错误] Python 无法运行。
    pause
    exit /b 1
)

echo Python OK
echo.

REM ============================================================
REM 检查主程序
REM ============================================================

echo [2/7] 检查 automation_test.py...

if not exist "%PY%" (
    echo.
    echo [错误] 找不到：
    echo %PY%
    echo.
    pause
    exit /b 1
)

echo automation_test.py OK
echo.

REM ============================================================
REM 检查 ADB
REM ============================================================

echo [3/7] 检查 ADB...

if not exist "%ADB%\adb.exe" (
    echo.
    echo [错误] 找不到 adb.exe：
    echo %ADB%\adb.exe
    echo.
    echo 请确认完整 Platform-Tools 已放入 adb 文件夹。
    echo.
    pause
    exit /b 1
)

echo adb.exe OK
echo.

REM ============================================================
REM 检查必要 DLL
REM ============================================================

if not exist "%ADB%\AdbWinApi.dll" (
    echo.
    echo [错误] 找不到：
    echo AdbWinApi.dll
    echo.
    pause
    exit /b 1
)

if not exist "%ADB%\AdbWinUsbApi.dll" (
    echo.
    echo [错误] 找不到：
    echo AdbWinUsbApi.dll
    echo.
    pause
    exit /b 1
)

echo ADB DLL OK
echo.

REM ============================================================
REM 创建 recordings
REM ============================================================

echo [4/7] 检查 recordings...

if not exist "%RECORDINGS%" (
    mkdir "%RECORDINGS%"
)

echo recordings OK
echo.

REM ============================================================
REM 检查 PyInstaller
REM ============================================================

echo [5/7] 检查 PyInstaller...

python -m PyInstaller --version >nul 2>nul

if errorlevel 1 (
    echo.
    echo PyInstaller 未安装。
    echo 正在安装...
    echo.

    python -m pip install --upgrade pyinstaller

    if errorlevel 1 (
        echo.
        echo [错误] PyInstaller 安装失败。
        echo.
        pause
        exit /b 1
    )
)

python -m PyInstaller --version

echo PyInstaller OK
echo.

REM ============================================================
REM 清理旧版本
REM ============================================================

echo [6/7] 清理旧的编译文件...

if exist "%ROOT%build" (
    rmdir /s /q "%ROOT%build"
)

if exist "%ROOT%dist" (
    rmdir /s /q "%ROOT%dist"
)

if exist "%ROOT%automation_test.spec" (
    del /q "%ROOT%automation_test.spec"
)

mkdir "%OUTPUT%"

echo 清理完成
echo.

REM ============================================================
REM PyInstaller
REM ============================================================

echo.
echo ============================================================
echo 正在编译 EXE
echo ============================================================
echo.

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name AutomationTest ^
    "%PY%"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [错误] EXE 编译失败
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo.
echo EXE 编译成功。
echo.

REM ============================================================
REM 创建最终目录
REM ============================================================

echo [7/7] 整理最终文件...

if not exist "%OUTPUT%" (
    mkdir "%OUTPUT%"
)

REM ------------------------------------------------------------
REM 复制 EXE
REM ------------------------------------------------------------

copy /Y "%ROOT%dist\AutomationTest.exe" "%OUTPUT%\AutomationTest.exe" >nul

if errorlevel 1 (
    echo.
    echo [错误] EXE 复制失败。
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 复制 ADB
REM ------------------------------------------------------------

echo.
echo 正在复制 ADB...

if exist "%OUTPUT%\adb" (
    rmdir /s /q "%OUTPUT%\adb"
)

xcopy "%ADB%" "%OUTPUT%\adb\" /E /I /Y /Q >nul

if errorlevel 1 (
    echo.
    echo [错误] ADB 复制失败。
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 复制 recordings
REM ------------------------------------------------------------

echo 正在复制 recordings...

if exist "%OUTPUT%\recordings" (
    rmdir /s /q "%OUTPUT%\recordings"
)

mkdir "%OUTPUT%\recordings"

xcopy "%RECORDINGS%\*" "%OUTPUT%\recordings\" /E /I /Y /Q >nul 2>nul

REM ============================================================
REM 完成
REM ============================================================

echo.
echo ============================================================
echo                 BUILD SUCCESS
echo ============================================================
echo.
echo 最终程序目录：
echo.
echo %OUTPUT%
echo.
echo 文件结构：
echo.
echo AutomationTest\
echo │
echo ├─ AutomationTest.exe
echo │
echo ├─ adb\
echo │  ├─ adb.exe
echo │  ├─ AdbWinApi.dll
echo │  ├─ AdbWinUsbApi.dll
echo │  └─ ...
echo │
echo └─ recordings\
echo    ├─ process1.json
echo    └─ process2.json
echo.
echo ============================================================
echo.
echo 可以直接进入：
echo.
echo %OUTPUT%
echo.
echo 双击 AutomationTest.exe
echo.
echo ============================================================
echo.

pause
exit /b 0