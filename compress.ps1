# Create-TinyMovieCatalogZip.ps1
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$source  = (Get-Location).Path
$zipPath = Join-Path (Split-Path $source -Parent) 'TinyMovieCatalog.zip'

# Motifs d'exclusion (regex appliquées sur le chemin relatif avec des "/")
$excludePatterns = @(
    '(^|/)\.git/',
    '^frontend/node_modules/',
    '^frontend/dist/',
    '^frontend/\.angular/',
    '^backend/\.env$',
    '^backend/data/db/',
    '^backend/data/thumbnails/',
    '^backend/\.?venv/',
    '(^|/)__pycache__/',
    '\.pyc$',
    '\.pyo$'
)
$excludeRegex = $excludePatterns -join '|'

# Dossiers à conserver dans le zip, mais vides (le "/" final est obligatoire)
$emptyDirs = @(
    'backend/data/db/',
    'backend/data/thumbnails/'
)

# Supprime l'archive existante pour repartir de zéro
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$zip = [System.IO.Compression.ZipFile]::Open($zipPath, 'Create')
try {
    # Fichiers (hors exclusions)
    Get-ChildItem -Path $source -Recurse -File -Force | ForEach-Object {
        $relative = $_.FullName.Substring($source.Length).TrimStart('\', '/') -replace '\\', '/'

        if ($relative -notmatch $excludeRegex) {
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $zip, $_.FullName, $relative, 'Optimal'
            ) | Out-Null
        }
    }

    # Dossiers vides conservés
    foreach ($dir in $emptyDirs) {
        $zip.CreateEntry($dir) | Out-Null
    }
}
finally {
    $zip.Dispose()
}

Write-Host "Archive créée : $zipPath"