#!/usr/bin/env bash
# PBJ scanner no seu computador (Linux/Mac). Uso: ./run_local.sh scan | hurst | returns | all
# Grava os resultados numa pasta sincronizada com o Google Drive (Google Drive para computador),
# de onde as rotinas leem pelo conector do Drive. Ajuste PBJ_SYNC_DIR se precisar.
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-all}"
SYNC_DIR="${PBJ_SYNC_DIR:-$HOME/Google Drive/PBJ-scanner}"
mkdir -p "$SYNC_DIR" history
python3 -m pip install -q -r requirements.txt
if [[ "$MODE" == "scan" || "$MODE" == "all" ]]; then
  python3 scan.py
  cp scan_results.csv relatorio.md "$SYNC_DIR/"
fi
if [[ "$MODE" == "hurst" || "$MODE" == "all" ]]; then
  [[ -f scan_results.csv ]] || cp "$SYNC_DIR/scan_results.csv" .
  python3 hurst_scan.py
  cp hurst_results.csv "$SYNC_DIR/"
fi
if [[ "$MODE" == "returns" || "$MODE" == "all" ]]; then
  python3 ret_scan.py
  cp returns_results.csv "$SYNC_DIR/"
fi
date -u +"ultima execucao: %Y-%m-%d %H:%M UTC (modo $MODE)" > "$SYNC_DIR/ULTIMA_EXECUCAO.txt"
echo "ok: arquivos em $SYNC_DIR"
