# ==============================================================================
# Nexora AI - Automated PostgreSQL Restore Script (Windows PowerShell)
# ==============================================================================
param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$ContainerName = "nexora_postgres",
    [string]$DbUser = "nexora",
    [string]$DbName = "nexora_db"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $BackupFile)) {
    Write-Error "Backup file '$BackupFile' does not exist."
    exit 1
}

Write-Host "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Restoring database from: $BackupFile..." -ForegroundColor Cyan

$running = docker ps --format '{{.Names}}' | Select-String -Pattern "^$ContainerName$"
if ($running) {
    docker cp $BackupFile "$($ContainerName):/tmp/restore_target.dump"
    docker exec -t $ContainerName pg_restore -U $DbUser -d $DbName --clean --if-exists --no-owner -v /tmp/restore_target.dump
    docker exec $ContainerName rm "/tmp/restore_target.dump"
    Write-Host "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Database successfully restored." -ForegroundColor Green
} else {
    Write-Error "Container '$ContainerName' is not running."
    exit 1
}
