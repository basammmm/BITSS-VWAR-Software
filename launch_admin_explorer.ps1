# Launch File Explorer with Administrator privileges
# Use this to drag files into VWAR when VWAR is running as admin

Write-Host "Launching File Explorer as Administrator..." -ForegroundColor Green
Write-Host "Drag files from THIS explorer window to VWAR for drag-drop to work!" -ForegroundColor Yellow
Write-Host ""

# Start a new elevated File Explorer
Start-Process explorer -Verb RunAs

Write-Host "Done! The new Explorer window has admin privileges." -ForegroundColor Green
Write-Host "Now you can drag files from it to VWAR." -ForegroundColor Cyan
