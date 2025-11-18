@echo off
chcp 65001 > nul
cls
echo ═══════════════════════════════════════════════════════════
echo   📦 INSTALADOR ALTERNATIVO
echo ═══════════════════════════════════════════════════════════
echo.
echo Se o 1_INSTALAR.bat não funcionou, use este!
echo.
echo Instalando...
echo.

py -m pip install --upgrade pip
py -m pip install streamlit
py -m pip install cloudscraper
py -m pip install beautifulsoup4
py -m pip install pandas
py -m pip install lxml

echo.
echo ═══════════════════════════════════════════════════════════
echo   ✅ PRONTO!
echo ═══════════════════════════════════════════════════════════
echo.
echo Agora execute: 2_RODAR.bat
echo.
pause
