# ==============================================================================
# Nexora AI - Automated PostgreSQL Backup Script (Windows PowerShell)
# ==============================================================================
param (
    [string]$BackupDir = ".\backups",
    [string]$ContainerName = "nexora_postgres",
    [string]$DbUser = "nexora",
    [string]$DbName = "nexora_db",
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "nexora_${DbName}_${Timestamp}.dump"

if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Host "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Starting Nexora AI PostgreSQL backup..." -ForegroundColor Cyan

$running = docker ps --format '{{.Names}}' | Select-String -Pattern "^$ContainerName$"
if ($running) {
    docker exec -t $ContainerName pg_dump -U $DbUser -d $DbName -F c -b -v -f "/tmp/nexora_backup_$Timestamp.dump"
    docker cp "$($ContainerName):/tmp/nexora_backup_$Timestamp.dump" $BackupFile
    docker exec $ContainerName rm "/tmp/nexora_backup_$Timestamp.dump"
    Write-Host "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Backup successfully created: $BackupFile" -ForegroundColor Green
} else {
    Write-Error "Container '$ContainerName' is not running."
    exit 1
}

# Apply retention policy
$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupDir -Filter "nexora_${DbName}_*.dump" | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force
Write-Host "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Backup retention applied ($RetentionDays days kept)." -ForegroundColor Cyan
