# PBJ scanner no Windows. Uso: powershell -File run_local.ps1 -Mode scan|hurst|returns|all
param([string]$Mode = "all")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Sync = if ($env:PBJ_SYNC_DIR) { $env:PBJ_SYNC_DIR } else { Join-Path $HOME "Google Drive\PBJ-scanner" }
New-Item -ItemType Directory -Force -Path $Sync, "history" | Out-Null
python -m pip install -q -r requirements.txt
if ($Mode -in "scan","all") {
  python scan.py
  Copy-Item scan_results.csv, relatorio.md $Sync -Force
}
if ($Mode -in "hurst","all") {
  if (-not (Test-Path scan_results.csv)) { Copy-Item (Join-Path $Sync "scan_results.csv") . }
  python hurst_scan.py
  Copy-Item hurst_results.csv $Sync -Force
}
if ($Mode -in "returns","all") {
  python ret_scan.py
  Copy-Item returns_results.csv $Sync -Force
}
"ultima execucao: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm')) UTC (modo $Mode)" | Set-Content (Join-Path $Sync "ULTIMA_EXECUCAO.txt")
Write-Host "ok: arquivos em $Sync"
