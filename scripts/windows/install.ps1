<#
.SYNOPSIS
    TinyMovieCatalog - Installation du backend puis du frontend.

.USAGE
    .\install.ps1

 Si PowerShell refuse l’exécution, utilisez une fois:  
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned


#>

# install.ps1

$ErrorActionPreference = "Stop"

# Répertoire racine du projet
$ProjectRoot = $PSScriptRoot

try {
    # Installation du backend Python
    Write-Host "`n=== Installation du backend Python Patience... ===" -ForegroundColor Cyan

    Set-Location "$ProjectRoot\backend"

    # Création de l'environnement virtuel
    if (-not (Test-Path ".\venv\Scripts\python.exe")) {
        python -m venv venv
    }

    # Activation de l'environnement virtuel
    . .\venv\Scripts\Activate.ps1

    # Mise à jour de pip
    python -m pip install --upgrade pip

    # Installation des dépendances Python
    if (Test-Path ".\requirements.txt") {
        python -m pip install -r requirements.txt
    }
    else {
        throw "Le fichier requirements.txt est introuvable dans le dossier backend."
    }

    Write-Host "`nBackend installe avec succes !" -ForegroundColor Green

    # Installation du frontend Node.js
    Write-Host "`n=== Installation du frontend Patience ===" -ForegroundColor Cyan

    Set-Location "$ProjectRoot\frontend"

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm est introuvable. Installe Node.js puis relance le script."
    }

    if (-not (Test-Path ".\package.json")) {
        throw "Le fichier package.json est introuvable dans le dossier frontend."
    }

    # Installation des dépendances frontend
    npm install

    if ($LASTEXITCODE -ne 0) {
        throw "L'installation des dependances frontend a echoue."
    }

    Write-Host "`nInstallation de Patience terminee avec succes !" -ForegroundColor Green
}
catch {
    Write-Host "`nERREUR : $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Set-Location $ProjectRoot
}