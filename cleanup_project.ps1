# ThreatModelerX Project Cleanup Script
# This script cleans up temporary files, resets the database, and prepares the project for production

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ThreatModelerX Project Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Delete scan output and test output files
Write-Host "[1/5] Cleaning up scan and test output files..." -ForegroundColor Yellow

$filesToDelete = @(
    "retire_err.txt",
    "retire_out.json",
    "scan_output.txt",
    "scan_output_2.txt",
    "scan_output_3.txt",
    "semgrep_debug.txt",
    "semgrep_err.txt",
    "semgrep_out.json",
    "test_output.txt",
    "test_output_clean.txt",
    "test_output_utf8.txt",
    "test_output_utf8_2.txt",
    "retire_debug.log",
    "scanner_debug.log",
    "semgrep_debug.log",
    "demo_apps_vulnerabilities.json"
)

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  Deleted: $file" -ForegroundColor Green
    }
}

# 2. Clean up old HTML reports
Write-Host ""
Write-Host "[2/5] Cleaning up old scan reports..." -ForegroundColor Yellow

$reportsPath = "backend\reports"
if (Test-Path $reportsPath) {
    $reports = Get-ChildItem -Path $reportsPath -Filter "*.html" | Sort-Object LastWriteTime -Descending
    
    if ($reports.Count -gt 1) {
        $reportsToDelete = $reports | Select-Object -Skip 1
        foreach ($report in $reportsToDelete) {
            Remove-Item $report.FullName -Force
            Write-Host "  Deleted old report: $($report.Name)" -ForegroundColor Green
        }
        Write-Host "  Kept latest report: $($reports[0].Name)" -ForegroundColor Green
    } else {
        Write-Host "  Only one report found, keeping it" -ForegroundColor Green
    }
}

# 3. Reset scan results database
Write-Host ""
Write-Host "[3/5] Resetting scan results database..." -ForegroundColor Yellow

$scanResultsPath = "backend\app\scan_results.json"
if (Test-Path $scanResultsPath) {
    "{}" | Out-File -FilePath $scanResultsPath -Encoding UTF8 -Force
    Write-Host "  Reset scan_results.json - scan count starts from 0" -ForegroundColor Green
} else {
    Write-Host "  scan_results.json not found" -ForegroundColor Red
}

# 4. Clean up Python cache
Write-Host ""
Write-Host "[4/5] Cleaning up Python cache files..." -ForegroundColor Yellow

Get-ChildItem -Path "." -Include "__pycache__" -Recurse -Force | Remove-Item -Recurse -Force
Write-Host "  Removed all __pycache__ directories" -ForegroundColor Green

# 5. Summary
Write-Host ""
Write-Host "[5/5] Cleanup Summary" -ForegroundColor Yellow
Write-Host "  Deleted temporary scan/test output files" -ForegroundColor Green
Write-Host "  Cleaned up old scan reports" -ForegroundColor Green
Write-Host "  Reset scan results database" -ForegroundColor Green
Write-Host "  Removed Python cache files" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Review the consolidated README.md" -ForegroundColor White
Write-Host "2. Test the application to ensure everything works" -ForegroundColor White
Write-Host "3. Commit changes to Git" -ForegroundColor White
Write-Host "4. Push to GitHub" -ForegroundColor White
