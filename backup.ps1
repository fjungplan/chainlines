# backup.ps1
$serverIP = "116.203.192.168"
$date = Get-Date -Format "yyyy-MM-dd_HH-mm"
$backupDir = "backups"

# 1. Create the backups folder if it doesn't exist
if (-not (Test-Path -Path $backupDir)) {
    Write-Host "Creating '$backupDir' folder..." -ForegroundColor Gray
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

$backupFile = "$backupDir\chainlines_backup_$date.sql"

Write-Host "Starting Database Backup..." -ForegroundColor Cyan

# 2. Dump data on Server to a temp file
# We use ${serverIP} to prevent PowerShell syntax errors
ssh "root@${serverIP}" "cd /var/www/chainlines && docker compose exec -T postgres pg_dump -U cycling cycling_lineage > /tmp/temp_backup.sql"

# 3. Download to the specific folder
Write-Host "Downloading to $backupFile..." -ForegroundColor Cyan
scp "root@${serverIP}:/tmp/temp_backup.sql" "./$backupFile"

# 4. Clean up Server
ssh "root@${serverIP}" "rm /tmp/temp_backup.sql"

if (Test-Path "./$backupFile") {
    Write-Host "Backup Saved: $backupFile" -ForegroundColor Green
} else {
    Write-Host "Backup Failed." -ForegroundColor Red
}