# ================================================
# Project Handover Portal - Mobile Access Script
# ================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Project Handover Portal - Mobile Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: ngrok is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please do the following:" -ForegroundColor Yellow
    Write-Host "1. Go to `https://ngrok.com/download` " -ForegroundColor White
    Write-Host "2. Download ngrok for Windows" -ForegroundColor White
    Write-Host "3. Extract ngrok.exe to this folder or add it to PATH" -ForegroundColor White
    Write-Host "4. Create a free account at `https://ngrok.com` " -ForegroundColor White
    Write-Host "5. Run: ngrok config add-authtoken YOUR_TOKEN_HERE" -ForegroundColor White
    Write-Host "6. Run this script again" -ForegroundColor White
    Write-Host ""
    pause
    exit
}

# Check if docker-compose is running
Write-Host "Checking if the project is running..." -ForegroundColor Yellow
$running = docker ps --filter "name=backend" --filter "status=running" -q
if (-not $running) {
    Write-Host ""
    Write-Host "Project is not running! Starting it now..." -ForegroundColor Yellow
    Write-Host ""
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker-compose up" -WorkingDirectory $PSScriptRoot
    Write-Host "Waiting 20 seconds for containers to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20

}

Write-Host ""
Write-Host "Starting ngrok tunnel on port 80..." -ForegroundColor Green
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Your app will be accessible at:" -ForegroundColor Green
Write-Host "  Check the Forwarding URL below" -ForegroundColor Green
Write-Host "  Share that URL with your Android device" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Red
Write-Host ""

ngrok http 80

