@echo off
setlocal
chcp 65001 >nul
echo ========================================
echo  Build do Executavel (PyInstaller)
echo ========================================
echo.

REM Garante que o ambiente virtual exista
if not exist venv (
    echo Ambiente virtual nao encontrado. Criando...
    call instalar.bat
)

if not exist venv (
    echo ERRO: Ambiente virtual ainda nao existe. Verifique a instalacao.
    exit /b 1
)

call "%~dp0venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERRO ao ativar o ambiente virtual.
    exit /b 1
)

REM Instala PyInstaller apenas para build
pip install --upgrade pip
pip install pyinstaller==6.19.0
if errorlevel 1 (
    echo ERRO ao instalar PyInstaller.
    exit /b 1
)

echo.
echo Gerando executavel...
pyinstaller --noconfirm --clean --windowed --name "TempoInativo" main.py
if errorlevel 1 (
    echo ERRO na geracao do executavel.
    exit /b 1
)

echo.
echo ========================================
echo  Executavel criado em dist\TempoInativo\TempoInativo.exe
echo  Copie toda a pasta dist\TempoInativo para distribuir.
echo ========================================
echo.
endlocal
exit /b 0
