# sync_db.ps1
param (
    [ValidateSet("push", "pull")]
    [string]$Mode = "pull",
    [string]$ServerIP = "116.203.192.168"
)

$ContainerName = "cycling_postgres"
$DbUser = "cycling"
$DbName = "cycling_lineage"
$RemotePath = "/var/www/chainlines"
$TempDump = "sync_dump.sql"

if ($Mode -eq "pull") {
    Write-Host "⬇️  PULLING Database from Server ($ServerIP) to Local..." -ForegroundColor Cyan
    
    # 1. Dump Remote DB
    Write-Host "   Creating remote dump..."
    ssh "root@$ServerIP" "docker exec $ContainerName pg_dump -U $DbUser $DbName > /tmp/$TempDump"
    
    # 2. Download
    Write-Host "   Downloading dump..."
    scp "root@${ServerIP}:/tmp/$TempDump" "./$TempDump"
    
    # 3. Cleanup Remote
    ssh "root@$ServerIP" "rm /tmp/$TempDump"
    
    # 4. Restore Local
    Write-Host "   Restoring to local DB (Dropping existing)..."
    docker exec -i $ContainerName psql -U $DbUser -d postgres -c "DROP DATABASE IF EXISTS $DbName WITH (FORCE);"
    docker exec -i $ContainerName psql -U $DbUser -d postgres -c "CREATE DATABASE $DbName;"
    Get-Content "./$TempDump" | docker exec -i $ContainerName psql -U $DbUser $DbName
    
    # 5. Cleanup Local
    Remove-Item "./$TempDump"
    
    Write-Host "✅ Sync Complete! Your local DB is now a clone of the server." -ForegroundColor Green
}
elseif ($Mode -eq "push") {
    Write-Host "⚠️  WARNING: YOU ARE ABOUT TO OVERWRITE THE PRODUCTION SERVER DATABASE" -ForegroundColor Red
    Write-Host "   Server: $ServerIP"
    Write-Host "   Target DB: $DbName"
    
    $confirmation = Read-Host "Type 'OVERWRITE' to confirm"
    if ($confirmation -ne "OVERWRITE") {
        Write-Host "❌ Aborted." -ForegroundColor Yellow
        exit
    }
    
    Write-Host "⬆️  PUSHING Local Database to Server..." -ForegroundColor Cyan
    
    # 1. Dump Local DB
    Write-Host "   Creating local dump..."
    # Use cmd /c to avoid PowerShell encoding (UTF-16) issues with > redirection
    cmd /c "docker exec $ContainerName pg_dump -U $DbUser $DbName > $TempDump"
    
    # 2. Upload
    Write-Host "   Uploading dump..."
    scp "./$TempDump" "root@${ServerIP}:/tmp/$TempDump"
    
    # 3. Restore Remote
    # We stop the backend first to ensure no connections lock the DB
    Write-Host "   Stopping remote backend..."
    ssh "root@$ServerIP" "cd $RemotePath && docker compose stop backend"
    
    Write-Host "   Restoring to remote DB (Dropping existing)..."
    ssh "root@$ServerIP" "docker exec -i $ContainerName psql -U $DbUser -d postgres -c 'DROP DATABASE IF EXISTS $DbName WITH (FORCE);'"
    ssh "root@$ServerIP" "docker exec -i $ContainerName psql -U $DbUser -d postgres -c 'CREATE DATABASE $DbName;'"
    # We pipe the file on the remote server into psql
    ssh "root@$ServerIP" "cat /tmp/$TempDump | docker exec -i $ContainerName psql -U $DbUser $DbName"
    
    # 4. Cleanup
    Write-Host "   Cleaning up and restarting..."
    ssh "root@$ServerIP" "rm /tmp/$TempDump && cd $RemotePath && docker compose start backend"
    Remove-Item "./$TempDump"
    
    Write-Host "✅ Sync Complete! The server DB has been updated with your local data." -ForegroundColor Green
}
