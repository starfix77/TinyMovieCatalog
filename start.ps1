# ======================================
#   TinyMovieCatalog - Démarrage
# ======================================

$ErrorActionPreference = "Stop"

# Répertoire racine du projet (là où se trouve ce script)
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================"
Write-Host "   TinyMovieCatalog - Demarrage"
Write-Host "======================================"

$FrontendProcess = $null
$BackendProcess = $null

# --------------------------------------
# Fonction de nettoyage à la fermeture
# --------------------------------------
function Cleanup {
    Write-Host ""
    Write-Host "Arret des serveurs..."

    if ($null -ne $FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

# Intercepter CTRL+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }
try {

    # --------------------------------------
    # Lancer le backend
    # --------------------------------------
    Write-Host "Demarrage du backend..."

    $activateScript = Join-Path $ProjectDir "backend\.venv\Scripts\Activate.ps1"
    $backendErrLog = Join-Path $ProjectDir "backend.error.log"

    $BackendProcess = Start-Process -FilePath "powershell" `
        -ArgumentList "-NoExit", "-Command", "& { . '$activateScript'; python -m uvicorn app.main:app --reload --port 8000 }" `
        -RedirectStandardError $backendErrLog `
        -PassThru -NoNewWindow `
        -WorkingDirectory (Join-Path $ProjectDir "backend")

    Write-Host "Backend demarre (PID: $($BackendProcess.Id))"


    # --------------------------------------
    # Attendre quelques secondes
    # --------------------------------------
    Start-Sleep -Seconds 2


    # --------------------------------------
    # Lancer le frontend
    # --------------------------------------
    Write-Host "Demarrage du frontend..."

    $frontendErrLog = Join-Path $ProjectDir "frontend.error.log"

    $FrontendProcess = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm start" `
        -RedirectStandardError $frontendErrLog `
        -PassThru -NoNewWindow -WorkingDirectory (Join-Path $ProjectDir "frontend")

    Write-Host "Frontend demarre (PID: $($FrontendProcess.Id))"



    Write-Host ""
    Write-Host "======================================"
    Write-Host "   Serveurs demarres"
    Write-Host "======================================"
    Write-Host ""
    Write-Host "Frontend : http://localhost:4200"
    Write-Host "Backend  : http://localhost:8000"
    Write-Host ""
    Write-Host "Log erreurs frontend : $ProjectDir\frontend.error.log"
    Write-Host "Log erreurs backend  : $ProjectDir\backend.error.log"
    Write-Host ""
    Write-Host "Appuyez sur CTRL+C pour arreter les deux serveurs."
    Write-Host ""

    # --------------------------------------
    # Attendre les deux processus
    # --------------------------------------
    Wait-Process -Id $FrontendProcess.Id, $BackendProcess.Id
}
finally {
    Cleanup
}