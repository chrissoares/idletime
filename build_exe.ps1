$ErrorActionPreference = 'Stop'
Write-Host "========================================"
Write-Host " Build do Executável (PyInstaller)"
Write-Host "========================================"

# Garantir venv
if (-not (Test-Path -Path "venv")) {
    Write-Host "Ambiente virtual não encontrado. Executando instalar.bat..."
    & cmd /c "instalar.bat"
}

if (-not (Test-Path -Path "venv")) {
    Write-Error "ERRO: Ambiente virtual ainda não existe. Verifique a instalação."
    exit 1
}

# Ativar venv
& "$PSScriptRoot/venv/Scripts/Activate.ps1"

# Instalar PyInstaller apenas para build
python -m pip install --upgrade pip
python -m pip install pyinstaller==6.19.0

# Gerar executável
Write-Host "Gerando executável..."
pyinstaller --noconfirm --clean --windowed --name "TempoInativo" main.py

Write-Host "========================================"
Write-Host " Executável criado em dist/TempoInativo/TempoInativo.exe"
Write-Host " Copie a pasta dist/TempoInativo inteira para distribuir."
Write-Host "========================================"
