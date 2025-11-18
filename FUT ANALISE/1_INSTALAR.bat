@echo off
chcp 65001 > nul
cls
echo ═══════════════════════════════════════════════════════════
echo   📦 INSTALADOR - Bot FBref
echo ═══════════════════════════════════════════════════════════
echo.
echo Instalando bibliotecas necessárias...
echo Isso pode demorar 1-2 minutos
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM Tentar com python -m pip (mais confiável)
echo Tentando instalar com: python -m pip
echo.
python -m pip install --upgrade pip
python -m pip install streamlit cloudscraper beautifulsoup4 pandas requests lxml

IF %ERRORLEVEL% EQU 0 (
    goto :sucesso
)

REM Se falhou, tentar com py -m pip
echo.
echo Tentando com: py -m pip
echo.
py -m pip install --upgrade pip
py -m pip install streamlit cloudscraper beautifulsoup4 pandas requests lxml

IF %ERRORLEVEL% EQU 0 (
    goto :sucesso
)

REM Se ainda falhou, mostrar erro
goto :erro

:sucesso
echo.
echo ═══════════════════════════════════════════════════════════
echo   ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ═══════════════════════════════════════════════════════════
echo.
echo Agora execute: 2_RODAR.bat
echo.
pause
exit /b 0

:erro
echo.
echo ═══════════════════════════════════════════════════════════
echo   ❌ ERRO NA INSTALAÇÃO
echo ═══════════════════════════════════════════════════════════
echo.
echo O Python pode não estar instalado corretamente.
echo.
echo Tente instalar o Python de novo:
echo https://www.python.org/downloads/
echo.
echo ⚠️  IMPORTANTE: Marque "Add Python to PATH" na instalação!
echo.
pause
exit /b 1
