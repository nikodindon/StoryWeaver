# Monitor HP Extraction Progress
# Usage: powershell -ExecutionPolicy Bypass -File scripts/monitor_extraction.ps1

$CacheDir = "C:\storyweaver\data\cache\harry_potter_1"
$ProcessedDir = "C:\storyweaver\data\processed\harry_potter_1"
$LogFile = "C:\storyweaver\data\extraction_monitor.log"
$IntervalSeconds = 600  # 10 minutes
$LastCount = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Harry Potter Extraction Monitor" -ForegroundColor Cyan
Write-Host "  Checking every $([math]::Floor($IntervalSeconds/60)) minutes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

do {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Count cache files
    if (Test-Path $CacheDir) {
        $CacheFiles = Get-ChildItem -Path $CacheDir -Filter "*.json"
        $CurrentCount = $CacheFiles.Count
    } else {
        $CurrentCount = 0
    }
    
    # Check if extraction.json exists
    $ExtractionDone = Test-Path "$ProcessedDir\extraction.json"
    
    # Check if python process is running
    $PythonProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 30056 }
    $ProcessRunning = $null -ne $PythonProcess
    
    # Display status
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  [$Timestamp]" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Cache files : $CurrentCount" -ForegroundColor $(if ($CurrentCount -gt $LastCount) { "Green" } else { "White" })
    if ($CurrentCount -gt $LastCount -and $LastCount -gt 0) {
        Write-Host "              +$($CurrentCount - $LastCount) since last check" -ForegroundColor Green
    }
    Write-Host "  Python PID  : $(if ($ProcessRunning) { '✅ Running (30056)' } else { '❌ Not running' })" -ForegroundColor $(if ($ProcessRunning) { "Green" } else { "Red" })
    Write-Host "  extraction.json : $(if ($ExtractionDone) { '✅ DONE!' } else { '⏳ Pending' })" -ForegroundColor $(if ($ExtractionDone) { "Green" } else { "Yellow" })
    Write-Host ""
    
    # Log to file
    "$Timestamp | Cache: $CurrentCount | Process: $ProcessRunning | Done: $ExtractionDone" | Out-File -FilePath $LogFile -Append
    
    # Alert if done
    if ($ExtractionDone) {
        Write-Host "  🎉 EXTRACTION COMPLETE!" -ForegroundColor Green -BackgroundColor DarkGreen
        Write-Host "  Next step: python scripts/compile_hp_world.py" -ForegroundColor Cyan
        [System.Windows.Forms.MessageBox]::Show("Harry Potter extraction is complete! You can now compile the world.", "Extraction Done!", 0, 64) | Out-Null
        break
    }
    
    # Alert if process died
    if (-not $ProcessRunning -and -not $ExtractionDone) {
        Write-Host "  ⚠️  WARNING: Python process stopped!" -ForegroundColor Red -BackgroundColor DarkRed
        Write-Host "  Extraction may have failed. Check logs." -ForegroundColor Red
        break
    }
    
    $LastCount = $CurrentCount
    
    # Wait for next check (with progress dots)
    Write-Host "  Next check in $([math]::Floor($IntervalSeconds/60)) minutes..." -ForegroundColor DarkGray
    Write-Host ""
    
    for ($i = 1; $i -le $IntervalSeconds; $i++) {
        Start-Sleep -Seconds 1
        if ($i % 60 -eq 0) {
            $MinsLeft = [math]::Floor(($IntervalSeconds - $i) / 60)
            Write-Host "`r  ⏱️  $MinsLeft min remaining...   " -NoNewline -ForegroundColor DarkGray
        }
    }
    Write-Host ""
    
} while ($true)

Write-Host ""
Write-Host "Monitor stopped." -ForegroundColor Yellow
