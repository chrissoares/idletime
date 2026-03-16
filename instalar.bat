@echo off
chcp 65001 >nul
echo ========================================
echo  Instalador - Rastreador de Atividade
echo ========================================
echo.

echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python não está instalado ou não está no PATH
    echo Por favor, instale Python em: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

python --version
echo.

echo [2/4] Criando ambiente virtual...
if exist venv (
    echo Ambiente virtual já existe. Removendo...
    rmdir /s /q venv
)
python -m venv venv
if %errorlevel% neq 0 (
    echo ERRO ao criar ambiente virtual.
    echo.
    pause
    exit /b 1
)
echo Ambiente virtual criado com sucesso!
echo.

echo [3/4] Ativando ambiente virtual e instalando dependências...
echo.
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERRO ao instalar dependências.
    echo Tentando instalar individualmente...
    echo.
    pip install pywin32==311
    pip install "pillow==12.1.1" --only-binary=:all: || pip install pillow==12.1.1
    pip install pystray==0.19.5
)

echo.
echo [4/4] Configurando pywin32...
python -m pywin32_postinstall -install

echo.
echo ========================================
echo  Instalação concluída!
echo ========================================
echo.
echo O ambiente virtual foi criado na pasta 'venv'
echo.
echo Para executar: dê duplo clique em executar.bat
echo Ou execute: venv\Scripts\python.exe main.py
echo.
pause
