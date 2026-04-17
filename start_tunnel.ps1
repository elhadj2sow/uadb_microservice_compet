param(
    [string]$CloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe",
    [int]$Port             = 3000,
    [int]$TimeoutSeconds   = 90
)

$ErrorActionPreference = "Stop"
$scriptDir     = $PSScriptRoot
$envFile       = Join-Path $scriptDir "inscription_service\inscription_service\.env"
$tunnelUrlFile = Join-Path $scriptDir "tunnel_url.txt"

Write-Host ""
Write-Host "=== UADB - Demarrage du tunnel Cloudflare ===" -ForegroundColor Cyan
Write-Host ""

# 1. Verifier cloudflared
if (-not (Test-Path $CloudflaredPath)) {
    $found = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($found) {
        $CloudflaredPath = $found.Source
    } else {
        Write-Host "[ERREUR] cloudflared introuvable." -ForegroundColor Red
        exit 1
    }
}
Write-Host "[1/4] cloudflared : $CloudflaredPath" -ForegroundColor Green

# 2. Tuer les anciens processus cloudflared
Write-Host "[2/4] Arret des tunnels existants..." -ForegroundColor Cyan
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-Item $tunnelUrlFile -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 3. Demarrer cloudflared en arriere-plan
Write-Host "[3/4] Demarrage du tunnel (port $Port)..." -ForegroundColor Cyan

$job = Start-Job -Name "CloudflaredJob" -ScriptBlock {
    param($cfPath, $cfPort)
    & $cfPath tunnel --url "http://localhost:$cfPort" 2>&1
} -ArgumentList $CloudflaredPath, $Port

$foundUrl = $null
$elapsed  = 0
$interval = 3
Write-Host "   Attente de l URL" -NoNewline -ForegroundColor Yellow

while ($elapsed -lt $TimeoutSeconds -and -not $foundUrl) {
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    Write-Host "." -NoNewline -ForegroundColor Yellow

    $lines = Receive-Job -Name "CloudflaredJob" -Keep 2>&1
    foreach ($line in $lines) {
        if ($line -match 'https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com') {
            $foundUrl = $Matches[0].TrimEnd('/')
            break
        }
    }
}
Write-Host ""

if (-not $foundUrl) {
    Write-Host "[ERREUR] URL non obtenue apres ${TimeoutSeconds}s." -ForegroundColor Red
    Stop-Job   -Name "CloudflaredJob" -ErrorAction SilentlyContinue
    Remove-Job -Name "CloudflaredJob" -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "   OK Tunnel actif : $foundUrl" -ForegroundColor Green

$foundUrl | Out-File -FilePath $tunnelUrlFile -Encoding utf8 -NoNewline
Write-Host "   OK tunnel_url.txt mis a jour" -ForegroundColor Green

# 4. Mettre a jour le .env
Write-Host "[4/4] Mise a jour du .env..." -ForegroundColor Cyan

if (-not (Test-Path $envFile)) {
    Write-Host "   [ATTENTION] .env introuvable : $envFile" -ForegroundColor Yellow
} else {
    # Lire ligne par ligne pour eviter tout probleme d'encodage avec Set-Content -Raw
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $lines = [System.IO.File]::ReadAllLines($envFile, [System.Text.Encoding]::UTF8)
    $updated = for ($i = 0; $i -lt $lines.Length; $i++) {
        $l = $lines[$i]
        if     ($l -match '^PAYTECH_SUCCESS_URL=') { "PAYTECH_SUCCESS_URL=$foundUrl/paiement/success" }
        elseif ($l -match '^PAYTECH_CANCEL_URL=')  { "PAYTECH_CANCEL_URL=$foundUrl/paiement/cancel" }
        elseif ($l -match '^PAYTECH_WEBHOOK_URL=') { "PAYTECH_WEBHOOK_URL=$foundUrl/api/paiements/paytech/webhook/" }
        else   { $l }
    }
    [System.IO.File]::WriteAllLines($envFile, $updated, $utf8NoBom)
    Write-Host "   OK .env mis a jour" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Tunnel pret ===" -ForegroundColor Green
Write-Host "  Frontend  : $foundUrl" -ForegroundColor White
Write-Host "  Webhook   : $foundUrl/api/paiements/paytech/webhook/" -ForegroundColor White
Write-Host "  Success   : $foundUrl/paiement/success" -ForegroundColor White
Write-Host "  Cancel    : $foundUrl/paiement/cancel" -ForegroundColor White
Write-Host ""
Write-Host "Demarrez Django apres ce script :" -ForegroundColor Yellow
Write-Host "  cd inscription_service\inscription_service" -ForegroundColor Yellow
Write-Host "  python manage.py runserver 0.0.0.0:8002" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pour arreter le tunnel :"
Write-Host "  Stop-Job -Name CloudflaredJob"
Write-Host "  Get-Process cloudflared | Stop-Process"
Write-Host ""