#!/bin/bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SUPPORT_DIR="$HOME/Library/Application Support/TinyMovieCatalog"
LOG_DIR="$HOME/Library/Logs/TinyMovieCatalog"
LABEL="com.tinymoviecatalog.server"
APPLICATIONS_DIR="${TMC_APPLICATIONS_DIR:-/Applications}"

[[ $EUID -ne 0 ]] || { echo "Lancez ./install.sh sans sudo (installation pour votre compte)." >&2; exit 1; }
for tool in python3 node npm osacompile sips iconutil; do
    command -v "$tool" >/dev/null || { echo "Outil requis introuvable : $tool" >&2; exit 1; }
done
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 minimum requis"'
if [[ ! -w "$APPLICATIONS_DIR" ]]; then
    if [[ -n "${TMC_APPLICATIONS_DIR:-}" ]]; then
        mkdir -p "$APPLICATIONS_DIR"
    else
        APPLICATIONS_DIR="$HOME/Applications"
        mkdir -p "$APPLICATIONS_DIR"
        echo "/Applications n'est pas accessible en écriture ; installation dans $APPLICATIONS_DIR."
    fi
fi
APP_PATH="$APPLICATIONS_DIR/TinyMovieCatalog.app"
[[ ! -e "$APP_PATH" || -f "$APP_PATH/Contents/Resources/tinymoviecatalog-launcher" ]] || {
    echo "Application existante non reconnue : $APP_PATH. Déplacez-la avant de continuer." >&2; exit 1;
}

echo ">> Compilation de l'interface…"
(cd "$PROJECT_DIR/frontend" && npm install && npm run build)

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
APP_BUILD="$TEMP_DIR/TinyMovieCatalog.app"
osacompile -s -o "$APP_BUILD" "$PROJECT_DIR/scripts/macos/launcher.applescript"
touch "$APP_BUILD/Contents/Resources/tinymoviecatalog-launcher"
ICONSET="$TEMP_DIR/AppIcon.iconset"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
    sips -z "$size" "$size" "$PROJECT_DIR/docs/favicon-256x256.png" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z "$double" "$double" "$PROJECT_DIR/docs/favicon-256x256.png" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP_BUILD/Contents/Resources/AppIcon.icns"
python3 - "$APP_BUILD/Contents/Info.plist" <<'PY'
import plistlib
import sys
from pathlib import Path
path = Path(sys.argv[1])
info = plistlib.loads(path.read_bytes())
info.update(CFBundleIdentifier="com.tinymoviecatalog.app", CFBundleName="TinyMovieCatalog",
            CFBundleDisplayName="TinyMovieCatalog", CFBundleIconFile="AppIcon.icns")
path.write_bytes(plistlib.dumps(info))
PY

printf '>> Installation dans %s...\n' "$SUPPORT_DIR"
mkdir -p "$SUPPORT_DIR/backend" "$SUPPORT_DIR/frontend" "$LOG_DIR"
# Stop only our own registered server before updating its files.
WAS_RUNNING=0
if /bin/launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
    WAS_RUNNING=1
    /bin/launchctl bootout "gui/$(id -u)/$LABEL"
fi
# Preserve the installed configuration and catalogue on every reinstall.
if [[ ! -f "$SUPPORT_DIR/backend/.env" ]]; then
    if [[ -f "$PROJECT_DIR/backend/.env" ]]; then
        cp "$PROJECT_DIR/backend/.env" "$SUPPORT_DIR/backend/.env"
    else
        cp "$PROJECT_DIR/backend/.env.example" "$SUPPORT_DIR/backend/.env"
    fi
    chmod 600 "$SUPPORT_DIR/backend/.env"
fi
if [[ ! -e "$SUPPORT_DIR/backend/data" && -d "$PROJECT_DIR/backend/data" ]]; then
    # SQLite's backup API includes committed WAL content without copying live journals.
    python3 - "$PROJECT_DIR/backend/data" "$SUPPORT_DIR/backend/data" <<'PY'
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
source, target = map(Path, sys.argv[1:])
# Publish the migrated data only after every copy succeeds, so a failed install
# can be retried without mistaking a partial directory for an existing catalogue.
with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
    staged = Path(temporary) / "data"
    shutil.copytree(source, staged, ignore=shutil.ignore_patterns("library.db", "library.db-wal", "library.db-shm"))
    database = source / "db/library.db"
    if database.is_file():
        (staged / "db").mkdir(exist_ok=True)
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as src:
            with sqlite3.connect(staged / "db/library.db") as dest:
                src.backup(dest)
    staged.rename(target)
PY
fi
mkdir -p "$SUPPORT_DIR/backend/data"
cp -R "$PROJECT_DIR/backend/app" "$SUPPORT_DIR/backend/"
cp "$PROJECT_DIR/backend/requirements.txt" "$SUPPORT_DIR/backend/"
cp -R "$PROJECT_DIR/frontend/dist/tinymoviecatalog-frontend/browser/." "$SUPPORT_DIR/frontend/"
cp "$PROJECT_DIR/scripts/macos/control.sh" "$SUPPORT_DIR/control.sh"
chmod +x "$SUPPORT_DIR/control.sh"
# Create the venv at its final path: a copied venv retains obsolete absolute paths.
if [[ ! -x "$SUPPORT_DIR/backend/.venv/bin/python" ]]; then
    python3 -m venv "$SUPPORT_DIR/backend/.venv"
fi
"$SUPPORT_DIR/backend/.venv/bin/python" -m pip install --upgrade pip
"$SUPPORT_DIR/backend/.venv/bin/python" -m pip install -r "$SUPPORT_DIR/backend/requirements.txt"

python3 - "$SUPPORT_DIR" "$LOG_DIR" "$LABEL" "$PATH" <<'PY'
import plistlib
import sys
from pathlib import Path
support, logs, label, shell_path = sys.argv[1:]
job = {
    "Label": label,
    "ProgramArguments": ["/bin/bash", str(Path(support) / "control.sh"), "serve"],
    "WorkingDirectory": str(Path(support) / "backend"),
    "EnvironmentVariables": {"PATH": shell_path},
    "RunAtLoad": True,
    "KeepAlive": True,
    "ThrottleInterval": 10,
    "StandardOutPath": str(Path(logs) / "server.log"),
    "StandardErrorPath": str(Path(logs) / "server.error.log"),
    "AssociatedBundleIdentifiers": ["com.tinymoviecatalog.app"],
}
(Path(support) / f"{label}.plist").write_bytes(plistlib.dumps(job))
PY
# Refresh the app signature after changing its icon and bundle metadata.
/usr/bin/codesign --force --sign - "$APP_BUILD"
if [[ -d "$APP_PATH" ]]; then rm -rf "$APP_PATH"; fi
/usr/bin/ditto "$APP_BUILD" "$APP_PATH"

if [[ -f "$HOME/Library/LaunchAgents/$LABEL.plist" ]]; then
    /bin/bash "$SUPPORT_DIR/control.sh" enable
elif [[ $WAS_RUNNING -eq 1 ]]; then
    /bin/bash "$SUPPORT_DIR/control.sh" start
fi
echo
echo "Installation terminée : $APP_PATH"
echo "Ouvrez l'application, puis clic droit sur son icône > Options > Garder dans le Dock."
echo "Configuration : $SUPPORT_DIR/backend/.env"
echo "Interface et API : http://localhost:8000"
echo "Démarrage à l'ouverture de session (facultatif) : ./install_service.sh (sans sudo)"
