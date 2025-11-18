@echo off
chcp 65001 > nul
cls
echo ═══════════════════════════════════════════════════════════
echo   🚀 BOT FBREF - Iniciando...
echo ═══════════════════════════════════════════════════════════
echo.
echo O navegador vai abrir automaticamente!
echo.
echo 💡 DICA: Deixe esta janela aberta
echo          Para fechar o bot: Aperte Ctrl+C aqui
echo.
echo ═══════════════════════════════════════════════════════════
echo.
pause
cls

REM Tentar com python -m streamlit
echo Iniciando o bot...
echo.
python -m streamlit run app.py

IF %ERRORLEVEL% EQU 0 (
    exit /b 0
)

REM Se falhou, tentar com py -m streamlit
cls
echo Tentando forma alternativa...
echo.
py -m streamlit run app.py

IF %ERRORLEVEL% EQU 0 (
    exit /b 0
)

REM Se falhou, tentar com streamlit direto
cls
echo Tentando mais uma forma...
echo.
streamlit run app.py

IF %ERRORLEVEL% EQU 0 (
    exit /b 0
)

REM Se ainda não funcionou, mostrar erro
cls
echo ═══════════════════════════════════════════════════════════
echo   ❌ ERRO!
echo ═══════════════════════════════════════════════════════════
echo.
echo O Streamlit não está instalado corretamente.
echo.
echo Execute primeiro: 1_INSTALAR.bat
echo.
echo Se já executou e ainda não funciona:
echo Execute: 1B_INSTALAR_ALTERNATIVO.bat
echo.
pause
