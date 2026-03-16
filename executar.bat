@echo off
chcp 65001 >nul

if not exist venv (
    echo ========================================
    echo  ERRO: Ambiente virtual não encontrado
    echo ========================================
    echo.
    echo Execute primeiro: instalar.bat
    echo.
    pause
    exit /b 1
)

echo Iniciando Rastreador de Atividade...
echo.
call venv\Scripts\activate.bat
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo  Erro ao executar a aplicação
    echo ========================================
    echo.
    echo Verifique se as dependências estão instaladas.
    echo Execute: instalar.bat
    echo.
    pause
)
