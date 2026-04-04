$ErrorActionPreference = "Stop"

Write-Host "========== FDPAC Backend Container Starting ==========" -ForegroundColor Cyan

Write-Host "[INFO] Python version:"
python --version

Write-Host "`n[INFO] Current working directory:"
Get-Location

Write-Host "`n[INFO] Environment check:"

# Check DATABASE_URL
if ([string]::IsNullOrEmpty($env:DATABASE_URL)) {
    Write-Host "[ERROR] DATABASE_URL is not set!" -ForegroundColor Red
    exit 1
}
Write-Host "[INFO] DATABASE_URL is set" -ForegroundColor Green

# Accept either JWT_SECRET or SECRET_KEY (both are mapped by the Python config)
if ([string]::IsNullOrEmpty($env:JWT_SECRET) -and [string]::IsNullOrEmpty($env:SECRET_KEY)) {
    Write-Host "[ERROR] JWT_SECRET (or SECRET_KEY) is not set!" -ForegroundColor Red
    exit 1
}
Write-Host "[INFO] JWT secret is set" -ForegroundColor Green

Write-Host ""

if ($env:SKIP_MIGRATIONS -eq "true") {
    Write-Host '[MIGRATIONS] SKIP_MIGRATIONS=true — skipping migrations.' -ForegroundColor Yellow
    Write-Host '[MIGRATIONS] Run ''alembic upgrade head'' manually against the direct connection URL.' -ForegroundColor Yellow
}
elseif (-not [string]::IsNullOrEmpty($env:MIGRATION_DATABASE_URL)) {
    Write-Host '[MIGRATIONS] Using MIGRATION_DATABASE_URL for DDL (session/direct pooler).' -ForegroundColor Cyan
    Write-Host '[MIGRATIONS] Starting database migrations with 60s timeout...' -ForegroundColor Cyan
    
    try {
        $process = Start-Process -FilePath "alembic" -ArgumentList "upgrade head" -NoNewWindow -PassThru -ErrorAction Stop
        $process | Wait-Process -Timeout 60 -ErrorAction Stop
        
        if ($process.ExitCode -eq 0) {
            Write-Host '[MIGRATIONS] Migrations completed successfully!' -ForegroundColor Green
        } else {
            Write-Host '[ERROR] Migrations failed!' -ForegroundColor Red
            Write-Host '[HINT] Verify MIGRATION_DATABASE_URL is reachable (direct connection, not pooler).' -ForegroundColor Yellow
            exit 1
        }
    }
    catch {
        Write-Host '[ERROR] Migrations failed or timed out after 60s!' -ForegroundColor Red
        Write-Host '[HINT] Verify MIGRATION_DATABASE_URL is reachable (direct connection, not pooler).' -ForegroundColor Yellow
        exit 1
    }
}
else {
    Write-Host '[MIGRATIONS] MIGRATION_DATABASE_URL not set; using DATABASE_URL for migrations.' -ForegroundColor Yellow
    Write-Host '[MIGRATIONS] WARNING: if DATABASE_URL uses Supabase transaction pooler (port 6543)' -ForegroundColor Yellow
    Write-Host '[MIGRATIONS]          set MIGRATION_DATABASE_URL to the direct connection URL' -ForegroundColor Yellow
    Write-Host '[MIGRATIONS]          or set SKIP_MIGRATIONS=true and run migrations manually.' -ForegroundColor Yellow
    Write-Host '[MIGRATIONS] Starting database migrations with 60s timeout...' -ForegroundColor Cyan
    
    try {
        $process = Start-Process -FilePath "alembic" -ArgumentList "upgrade head" -NoNewWindow -PassThru -ErrorAction Stop
        $process | Wait-Process -Timeout 60 -ErrorAction Stop
        
        if ($process.ExitCode -eq 0) {
            Write-Host '[MIGRATIONS] Migrations completed successfully!' -ForegroundColor Green
        } else {
            Write-Host '[ERROR] Migrations failed!' -ForegroundColor Red
            Write-Host '[HINT] Verify DATABASE_URL is reachable and uses sslmode=require for Supabase.' -ForegroundColor Yellow
            exit 1
        }
    }
    catch {
        Write-Host '[ERROR] Migrations failed or timed out after 60s!' -ForegroundColor Red
        Write-Host '[HINT] Verify DATABASE_URL is reachable and uses sslmode=require for Supabase.' -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "[STARTUP] Starting Uvicorn server..." -ForegroundColor Cyan
$port = $env:PORT -or "10000"
Write-Host "[STARTUP] Binding to 0.0.0.0:$port" -ForegroundColor Cyan

uvicorn app.main:app `
    --host 0.0.0.0 `
    --port $port `
    --timeout-keep-alive 75
