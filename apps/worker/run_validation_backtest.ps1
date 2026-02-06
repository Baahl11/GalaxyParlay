# FASE 5 Validation Backtest
# Run this script after API-Football resets (90 minutes from now)

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "FASE 5 VALIDATION BACKTEST" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This backtest will validate the league-specific calibrations:" -ForegroundColor Yellow
Write-Host "  - Champions League: 63.89% -> 68-70% (target)" -ForegroundColor Yellow
Write-Host "  - Bundesliga: 68.50% -> 71-73% (target)" -ForegroundColor Yellow
Write-Host "  - Europa League: 68.75% -> 71-73% (target)" -ForegroundColor Yellow
Write-Host "  - Overall: 72.18% -> 73-74% (target)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Dataset: 1,000 fixtures from 2024-2026" -ForegroundColor White
Write-Host "Duration: ~60-90 minutes" -ForegroundColor White
Write-Host "Output: backtest_results.json + backtest_log.txt" -ForegroundColor White
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:SUPABASE_URL = "https://jssjwjsuqmkzidigjpwj.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impzc2p3anN1cW1remlkaWdqcHdqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQzNDQwMiwiZXhwIjoyMDg1MDEwNDAyfQ.iir_GtLYUZmAL66C_7BZJITxkq8rRQklWPqBS_Qp7io"

# Change to worker directory
Set-Location "C:\Users\gm_me\GalaxyParlay\apps\worker"

Write-Host "Starting backtest..." -ForegroundColor Green
Write-Host ""

# Run backtest
.\venv\Scripts\python.exe -m app.ml.run_backtest --num-fixtures 1000 2>&1 | Tee-Object -FilePath backtest_validation_log.txt

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "BACKTEST COMPLETE" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results saved to:" -ForegroundColor Green
Write-Host "  - backtest_results.json (full results)" -ForegroundColor White
Write-Host "  - backtest_validation_log.txt (execution log)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: python -m app.ml.analyze_backtest" -ForegroundColor White
Write-Host "  2. Compare with FASE_5_REPORT.md baseline" -ForegroundColor White
Write-Host "  3. Verify improvements in CL, Bundesliga, EL" -ForegroundColor White
Write-Host ""
