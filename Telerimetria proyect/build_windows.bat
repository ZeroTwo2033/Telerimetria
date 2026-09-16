@echo off
title GameHW Monitor - Compilador
echo ============================================
echo   Compilando GameHW Monitor para Windows...
echo   Esto puede tardar 1-2 minutos. No cierres esta ventana.
echo ============================================
echo.

python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Compilando el ejecutable...
python -m PyInstaller --noconfirm --onefile --windowed --name "GameHWMonitor" main.py

echo.
echo ============================================
echo   LISTO!
echo   Tu aplicacion esta en la carpeta "dist"
echo   Archivo: dist\GameHWMonitor.exe
echo.
echo   Puedes copiar ese .exe a tu Escritorio y
echo   hacerle doble clic para abrir el programa.
echo ============================================
pause
