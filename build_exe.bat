@echo off
chcp 65001 >nul
echo ========================================
echo  Build do Executável (PyInstaller)
echo ========================================
echo.

REM Garante que o ambiente virtual exista
if not exist venv (
    echo Ambiente virtual não encontrado. Criando...
    call instalar.bat
)

if not exist venv (
    echo ERRO: Ambiente virtual ainda não existe. Verifique a instalacao.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Instala PyInstaller apenas para build
pip install --upgrade pip
pip install pyinstaller==6.19.0
if %errorlevel% neq 0 (
    echo ERRO ao instalar PyInstaller.
    pause
    exit /b 1
)

echo.
echo Gerando executável...
pyinstaller --noconfirm --clean --windowed --name "TempoInativo" main.py
if %errorlevel% neq 0 (
    echo ERRO na geração do executável.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Executável criado em dist\TempoInativo\TempoInativo.exe
echo  Copie toda a pasta dist\TempoInativo para distribuir.
echo ========================================
echo.
pause
