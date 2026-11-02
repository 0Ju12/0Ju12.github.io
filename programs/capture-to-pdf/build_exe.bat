@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo [1/2] Installing packages...
python -m pip install --upgrade pyinstaller mss img2pdf pikepdf pynput pytesseract
if errorlevel 1 goto :fail

echo [2/2] Building CaptureToPDF.exe ...
python -m PyInstaller --noconfirm --onefile --windowed --name CaptureToPDF ^
  --hidden-import pynput.keyboard._win32 ^
  --hidden-import pynput.mouse._win32 ^
  --collect-all pikepdf ^
  capture_to_pdf.py
if errorlevel 1 goto :fail

echo.
echo Done: dist\CaptureToPDF.exe
echo Copy the exe anywhere. Capture folder and settings are created next to it.
pause
exit /b 0

:fail
echo.
echo Build failed. Check the messages above.
pause
exit /b 1
