Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "[!] ACORDANDO SERVIDOR PROJECT AEGIS (OSINT MIDDLEWALL)" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[X] Falha no Boot: A SandBox de proteção (VENV) está ausente. Impossível iniciar." -ForegroundColor Red
    Write-Host "[!] Comando: Execute .\setup_and_run.ps1 antes de iniciar a rede primária." -ForegroundColor Red
    exit 1
}

# Injeta a Virtualização Limpa no Shell atual forçadamente
Write-Host "[>] Engatando Ambiente SandBox..." -ForegroundColor Gray
. .\venv\Scripts\Activate.ps1

Write-Host "[>] Injetando Roteamento Direto da Aplicação C:\\... ($env:PYTHONPATH) na RAM..." -ForegroundColor Yellow
$env:PYTHONPATH="."

Write-Host "[>] Destrancando as Portas UVICORN em Regime Vigília (Watch Mode)..." -ForegroundColor Green
# Chama o Uvicorn garantindo que ele execute EXTRITAMENTE a partir do binário selado no Sandbox criado.
& .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
