# Idle Time (TempoInativo)

> Aplicativo desktop para Windows que registra automaticamente tempo ativo/inativo, categoriza pausas, gera relatórios e fica na bandeja do sistema. Todos os dados ficam **locais** em SQLite — nenhuma informação sai do seu computador.

Autor: **Christiano Ribeiro Soares**

## Visão Geral

O Idle Time monitora sua presença no computador, identifica períodos de inatividade e permite classificar pausas (café, almoço, banheiro, descanso etc.). Ele funciona em segundo plano (bandeja) e oferece relatórios de produtividade, sem depender de internet.

## Principais Funcionalidades

- ⏱️ **Detecção automática de inatividade** (API do Windows, GetLastInputInfo)
- 💤 **Sessões ativas vs. inativas** registradas em banco local SQLite
- 🏷️ **Categorias de pausas** (café, almoço, banheiro, lanche, descanso, outro) com notas opcionais
- 📊 **Relatórios** por período (Hoje, 7 dias, 30 dias, tudo) com percentuais e tempos por categoria
- 🪟 **Minimizar para bandeja** e abrir com clique no ícone
- ⚙️ **Configurações**: tempo de inatividade (sensibilidade) e iniciar com Windows
- 🔒 **Privacidade total**: dados 100% locais, sem telemetria

## Requisitos

- Windows 10 ou superior
- Python 3.11 ou 3.12 (funciona em 3.14 com versões ajustadas de dependências)

## Instalação (Recomendado)

1. Baixe/clone o repositório.
2. Dê duplo clique em `instalar.bat`.
   - Cria o ambiente virtual `venv/`.
   - Instala dependências: `pywin32==311`, `pillow==12.1.1`, `pystray==0.19.5`.
3. Dê duplo clique em `executar.bat` para iniciar.

### Instalação Manual (Cmd)

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Uso

1. Abra o app (`executar.bat` ou `python main.py`).
2. O monitoramento inicia automaticamente (padrão: inativo após 60s sem entrada).
3. Minimize: o app vai para a bandeja; clique no ícone para reabrir.
4. Categorize pausas na aba **Categorizar Pausas**; notas são opcionais.
5. Gere relatórios na aba **Relatórios** por período.
6. Ajuste sensibilidade e início com Windows na aba **Configurações**.

> Se políticas bloquearem `.ps1`, use o `executar.bat` (Cmd) ou ative o venv manualmente e rode `python main.py`.

## Gerar Executável (.exe)

### Via PowerShell (quando política permitir)
```powershell
PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

### Via Cmd
```cmd
build_exe.bat
```

### Manual (se scripts forem bloqueados)
```cmd
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install pyinstaller==6.19.0
pyinstaller --noconfirm --clean --windowed --name "TempoInativo" main.py
```

> Política bloqueando `.ps1`? Use o método via Cmd ou o manual acima. Se necessário, remova bloqueio só no processo: `PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1`.

O executável ficará em `dist/TempoInativo/TempoInativo.exe`. Distribua a **pasta inteira** `dist/TempoInativo`.

## Estrutura do Projeto

```
TempoInativo/
├── main.py                # Entrada da aplicação
├── gui.py                 # Interface Tkinter + bandeja
├── monitor.py             # Monitor de atividade/inatividade
├── idle_detector.py       # Leitura do GetLastInputInfo (Windows)
├── database.py            # SQLite e operações de sessões/categorias
├── requirements.txt       # Dependências
├── instalar.bat           # Instala venv e deps
├── executar.bat           # Executa usando o venv
├── build_exe.bat          # Build via Cmd (PyInstaller)
├── build_exe.ps1          # Build via PowerShell
├── activity_tracker.db    # Banco local (gerado em runtime)
└── README.md
```

## Comportamento de Bandeja

- Minimizar esconde a janela e mantém o ícone na bandeja.
- Clique simples ou duplo no ícone: reabre a janela.
- Menu de contexto (botão direito): Abrir / Sair.

## Como Funciona (em alto nível)

1. A cada 5 segundos, lê o tempo desde a última entrada de mouse/teclado.
2. Se ultrapassar o limite configurado (padrão 60s), abre uma sessão “inativa”.
3. Ao voltar a interagir, fecha a sessão inativa e inicia uma sessão ativa.
4. Tudo é salvo em SQLite (`activity_tracker.db`).
5. Pausas podem ser categorizadas a qualquer momento.

## Solução de Problemas

- **ModuleNotFound / dependências**: delete `venv/` e rode `instalar.bat`.
- **pywin32_postinstall**: ative o venv e rode `python -m pywin32_postinstall -install`.
- **Pillow falha ao compilar**: verifique se há wheel para sua versão de Python; se estiver em 3.14 e falhar, use uma versão suportada (3.11/3.12) ou tente `--only-binary=:all:`.
- **Política do PowerShell**: use `-ExecutionPolicy Bypass` ou rode comandos via Cmd.
- **Build PyInstaller**: use `pyinstaller==6.19.0` (compatível com Python 3.14). Distribua a pasta `dist/TempoInativo` inteira.

## Contribuindo

1. Faça um fork e crie um branch: `git checkout -b feature/sua-feature`.
2. Mantenha mudanças focadas e pequenas.
3. Atualize o README se adicionar/alterar funcionalidades.
4. Abra um PR descrevendo claramente o que mudou e como testar.

## Licença

Uso permitido **apenas para fins pessoais e não comerciais**. Modificações ou redistribuições devem manter a mesma licença (share-alike) e creditar o autor. Não é permitido uso comercial por terceiros sem autorização expressa.

## Autor

**Christiano Ribeiro Soares**

---

“Idle Time” ajuda você a entender e equilibrar tempo de trabalho e pausas — com privacidade total, rodando apenas no seu computador.
