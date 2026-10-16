<#
.SYNOPSIS
    TinyMovieCatalog - Installation du backend puis du frontend.

.USAGE
    .\install.ps1

 Si PowerShell refuse l’exécution, utilisez une fois:  
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned


#>

$ErrorActionPreference = "Stop"

# Répertoire racine du projet
$ProjectDir = $PSScriptRoot

function Write-Title([string]$Text) {
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "   $Text"
    Write-Host "=========================================="
    Write-Host ""
}

# Exécute une commande native et s'arrête si elle échoue (équivalent de "set -e")
function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Exe, [string[]]$Arguments = @())
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "La commande a échoué (code $LASTEXITCODE) : $Exe $($Arguments -join ' ')"
    }
}

try {
    Write-Title "TinyMovieCatalog - Installation"

    # ------------------------------------------
    # Vérification Node.js / npm
    # ------------------------------------------
    Write-Host ">> Vérification de Node.js et npm..."

    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        throw "Node.js n'est pas installé."
    }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm n'est pas installé."
    }

    Write-Host "Node.js : $(node --version)"
    Write-Host "npm     : $(npm --version)"
    Write-Host ""

    # ------------------------------------------
    # Installation backend
    # ------------------------------------------
    Write-Title "Installation du backend"

    $BackendDir = Join-Path $ProjectDir "backend"
    Set-Location $BackendDir

    Write-Host "Répertoire : $(Get-Location)"
    Write-Host ""

    # Vérification de Python (py launcher, python ou python3)
    $PythonCmd = $null
    foreach ($candidate in @("py", "python", "python3")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            $PythonCmd = $candidate
            break
        }
    }
    if (-not $PythonCmd) {
        throw "Python 3 n'est pas installé."
    }

    $PythonArgs = @()
    if ($PythonCmd -eq "py") { $PythonArgs = @("-3") }

    Write-Host "Python : $(& $PythonCmd @PythonArgs --version)"
    Write-Host ""

    # Création de l'environnement virtuel
    if (-not (Test-Path ".venv")) {
        Write-Host ">> Création de l'environnement virtuel Python..."
        Invoke-Checked $PythonCmd ($PythonArgs + @("-m", "venv", ".venv"))
    }
    else {
        Write-Host ">> Environnement virtuel .venv déjà présent."
    }
    Write-Host ""

    # Python du venv (appelé directement : pas besoin d'activer, ce qui évite
    # aussi les problèmes de politique d'exécution sur Activate.ps1)
    $VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $VenvPython)) {
        throw "Python introuvable dans l'environnement virtuel : $VenvPython"
    }

    Write-Host ">> Environnement virtuel utilisé..."
    Write-Host "Python utilisé : $VenvPython"
    Write-Host ""

    # Mise à jour de pip
    Write-Host ">> Mise à jour de pip..."
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip")
    Write-Host ""

    # Installation des dépendances Python
    Write-Host ">> Installation des dépendances Python..."
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", "requirements.txt")
    Write-Host ""

    Write-Host ">> Installation backend terminée."
    Write-Host ""

    # ------------------------------------------
    # Installation frontend
    # ------------------------------------------
    Write-Title "Installation du frontend"

    $FrontendDir = Join-Path $ProjectDir "frontend"
    Set-Location $FrontendDir

    Write-Host "Répertoire : $(Get-Location)"
    Write-Host ""
    Write-Host ">> Installation des dépendances npm..."
    Write-Host ""

    Invoke-Checked "npm" @("install")
    Invoke-Checked "npm" @("run", "build")

    Write-Host ""
    Write-Host ">> Installation frontend terminée."
    Write-Host ""

    # ------------------------------------------
    # Fin
    # ------------------------------------------
    Write-Title "Installation terminée avec succès"

    Write-Host "Backend  : $BackendDir"
    Write-Host "Frontend : $FrontendDir"
    Write-Host "Python   : $VenvPython"
    Write-Host ""
    Write-Host "Pour démarrer le projet :"
    Write-Host ""
    Write-Host "    .\start.ps1"
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "ERREUR : $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Set-Location $ProjectDir
}
