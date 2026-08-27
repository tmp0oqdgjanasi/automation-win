@echo off

title Build auto.exe

echo ========================================
echo Building auto.exe
echo ========================================

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --clean ^
    --name auto ^
    auto.py

echo.
echo ========================================
echo Build finished.
echo.
echo EXE:
echo dist\auto.exe
echo ========================================

pause