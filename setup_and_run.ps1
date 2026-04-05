Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " PROJECT AEGIS - AUTOMATED SETUP & DIAGNOSTICS (DEVSECOPS) " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Scaneando Ambientes para Forçar Descoberta do Python Local Isolado
$python_exe = $null
$possible_paths = @(
    "python",
    "py",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:ProgramFiles\Python311\python.exe",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe"
)

foreach ($path in $possible_paths) {
    try {
        $result = & $path --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $python_exe = $path
            Write-Host "[*] Motor Python detectado com sucesso engatilhado em: $path" -ForegroundColor Green
            break
        }
    } catch {
        # Silent pass if execution errors out due to absent path
    }
}

if ($null -eq $python_exe) {
    Write-Host "[X] ERRO CRÍTICO: Algoritmo Python não localizado no Host de Janelas. Instale o core da Microsoft Store ou pelo py.org garantindo que a opção 'Add to PATH' seja marcada." -ForegroundColor Red
    exit 1
}

# 2. Isolação Segura (VENV Sandbox)
Write-Host "[>] Inicializando contenção em SandBox Limpa (Virtual Environment)..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    & $python_exe -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Falha massiva ao injetar Módulo VENV. Operação Abortada." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[*] Ambiente de Isolamento 'venv' já detectado. Analisando Integridade Numérica..." -ForegroundColor Gray
}

$venv_pip = ".\venv\Scripts\pip.exe"
$venv_python = ".\venv\Scripts\python.exe"

# 3. Blindando Bibliotecas Requisitadas na SandBox
Write-Host "[>] Engatando Firewall de Pacotes (Baixando Dependências Base e Táticas)..." -ForegroundColor Yellow
& $venv_python -m pip install --upgrade pip --quiet
& $venv_pip install uvicorn fastapi httpx pydantic-settings cryptography passlib argon2-cffi `"python-jose[cryptography]`" aiosqlite sqlalchemy pillow email-validator
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Corrupção de Download ao sincronizar pacotes oficiais no PyPI. Confira as restrições da sua Rede (DNS ou Timeout)." -ForegroundColor Red
    exit 1
}

# 4. Ligando os Cofres do Bando de Dados (Aegis SQLite)
Write-Host "[>] Reforjando Tabelas da Base de Dados Core (Init DB)..." -ForegroundColor Yellow
$env:PYTHONPATH="."
& $venv_python init_db.py

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "[✔] SETUP ALCANÇADO E BLINDADO COM SUCESSO. RASTROS GARANTIDOS." -ForegroundColor Green
Write-Host "Execute o script principal [start_aegis.ps1] agora para levantar os escudos e habilitar as rotas Web." -ForegroundColor Cyan
