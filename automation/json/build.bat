 @echo off

title Build json.exe

echo ========================================
echo Building json.exe
echo ========================================

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --clean ^
    --name json ^
    json.py

echo.
echo ========================================
echo Build finished.
echo.
echo EXE:
echo dist\json.exe
echo ========================================

pause