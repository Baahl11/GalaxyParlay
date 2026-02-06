# Run backtest with venv Python
$ErrorActionPreference = "Continue"

Write-Host "==================================="
Write-Host "Running Real Backtest"
Write-Host "==================================="

& "c:\Users\gm_me\GalaxyParlay\apps\worker\venv\Scripts\python.exe" -m app.ml.run_backtest

Write-Host ""
Write-Host "Backtest complete! Check backtest_results.json for details."
