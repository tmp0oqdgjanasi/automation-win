@echo off
chcp 65001 >nul
setlocal

echo.
echo ========================================================
echo        Automation Test EXE Builder
echo ========================================================
echo.

echo [1/5] 检查 Python...

where python >nul 2>&1

if errorlevel 1 (
    echo.
    echo 错误：没有找到 Python。
    echo.
    echo 打包电脑需要安装 Python。
    echo 最终生成的 EXE 不需要 Python。
    echo.
    pause
    exit /b 1
)

echo Python OK
echo.

echo [2/5] 检查 ADB 文件...

if not exist "adb\adb.exe" (
    echo.
    echo 错误：缺少 adb\adb.exe
    echo.
    pause
    exit /b 1
)

if not exist "adb\AdbWinApi.dll" (
    echo.
    echo 错误：缺少 adb\AdbWinApi.dll
    echo.
    pause
    exit /b 1
)

if not exist "adb\AdbWinUsbApi.dll" (
    echo.
    echo 错误：缺少 adb\AdbWinUsbApi.dll
    echo.
    pause
    exit /b 1
)

echo ADB OK
echo.

echo [3/5] 安装 Python 依赖...

python -m pip install --upgrade pip

if errorlevel 1 (
    echo pip 更新失败。
    pause
    exit /b 1
)

python -m pip install ^
    pyinstaller ^
    pillow ^
    pynput ^
    pywin32

if errorlevel 1 (
    echo.
    echo Python 依赖安装失败。
    echo.
    pause
    exit /b 1
)

echo.
echo 依赖安装完成。
echo.

echo [4/5] 清理旧的打包文件...

if exist build (
    rmdir /s /q build
)

if exist dist (
    rmdir /s /q dist
)

if exist AutomationTest.spec (
    del /f /q AutomationTest.spec
)

echo 清理完成。
echo.

echo [5/5] 开始生成 EXE...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name AutomationTest ^
    --add-binary "adb\adb.exe;adb" ^
    --add-binary "adb\AdbWinApi.dll;adb" ^
    --add-binary "adb\AdbWinUsbApi.dll;adb" ^
    automation_test.py

if errorlevel 1 (
    echo.
    echo ========================================================
    echo                 打包失败
    echo ========================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo                 打包成功
echo ========================================================
echo.
echo EXE 文件：
echo.
echo     dist\AutomationTest.exe
echo.
echo 这个 EXE 可以复制到没有 Python 的 Windows 电脑运行。
echo.
echo ========================================================
echo.

pause