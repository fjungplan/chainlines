# deploy.ps1
$serverIP = "116.203.192.168"

Write-Host "🚀 Starting Deployment to Chainlines ($serverIP)..." -ForegroundColor Cyan

# 1. SSH into the server and run the update commands in one go
# The quotes "" group the commands together so they run strictly on the server
ssh "root@$serverIP" "cd /var/www/chainlines && git pull origin main && docker compose up -d --build"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment Successful!" -ForegroundColor Green
} else {
    Write-Host "❌ Deployment Failed. Check the logs above." -ForegroundColor Red
}