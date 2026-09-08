@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment was not found.
    echo Run the Windows installation steps first, then run this file again.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

pyinstaller --clean --noconfirm LuckyNumbersBot.spec

echo.
echo Build complete.
echo App file:
echo dist\LuckyNumbersBot.exe
echo.
echo Give the client LuckyNumbersBot.exe from the dist folder.
pause
