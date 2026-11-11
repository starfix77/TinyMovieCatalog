#!/bin/bash
# Used by the Dock app and optionally by a per-user LaunchAgent.
set -euo pipefail
SUPPORT_DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.tinymoviecatalog.server"
DOMAIN="gui/$(id -u)"
JOB="$DOMAIN/$LABEL"
PLIST="$SUPPORT_DIR/$LABEL.plist"
LOGIN_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/TinyMovieCatalog"
# Finder and launchd do not inherit an interactive shell's PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}"

loaded() { /bin/launchctl print "$JOB" >/dev/null 2>&1; }

start() {
    if ! loaded; then
        /bin/launchctl enable "$JOB"
        /bin/launchctl bootstrap "$DOMAIN" "$PLIST" || loaded
    fi
}

case "${1:-open}" in
    serve)
        mkdir -p "$LOG_DIR"
        export TMC_FRONTEND_DIR="$SUPPORT_DIR/frontend"
        cd "$SUPPORT_DIR/backend"
        # No reload watcher or development frontend in the installed app.
        exec .venv/bin/python -m uvicorn app.desktop:app --host 127.0.0.1 --port 8000
        ;;
    open)
        start
        for ((attempt=0; attempt<60; attempt++)); do
            if /usr/bin/curl --noproxy '*' -fsS --max-time 1 http://localhost:8000/openapi.json \
                | "$SUPPORT_DIR/backend/.venv/bin/python" -c \
                'import json,sys; assert json.load(sys.stdin)["info"]["title"] == "TinyMovieCatalog Library Manager API"' \
                >/dev/null 2>&1 \
                && /usr/bin/curl --noproxy '*' -fsS --max-time 1 http://localhost:8000/ \
                | /usr/bin/grep -q '<app-root'; then
                /usr/bin/open http://localhost:8000
                exit 0
            fi
            sleep 0.5
        done
        echo "Démarrage impossible. Vérifiez que le port 8000 est libre et consultez $LOG_DIR/server.error.log" >&2
        exit 1
        ;;
    start) start ;;
    stop) if loaded; then /bin/launchctl bootout "$JOB"; fi ;;
    restart)
        if loaded; then /bin/launchctl bootout "$JOB"; fi
        start
        ;;
    enable)
        mkdir -p "$(dirname "$LOGIN_PLIST")"
        cp "$PLIST" "$LOGIN_PLIST"
        chmod 644 "$LOGIN_PLIST"
        if loaded; then /bin/launchctl bootout "$JOB"; fi
        /bin/launchctl enable "$JOB"
        /bin/launchctl bootstrap "$DOMAIN" "$LOGIN_PLIST"
        echo "TinyMovieCatalog démarrera à l'ouverture de votre session macOS."
        echo "Pour l'ouvrir : Applications > TinyMovieCatalog."
        ;;
    disable)
        if loaded; then /bin/launchctl bootout "$JOB"; fi
        rm -f "$LOGIN_PLIST"
        echo "Démarrage automatique désactivé et serveur arrêté. L'icône reste utilisable."
        ;;
    *) echo "Usage : $0 {open|start|stop|restart|enable|disable}" >&2; exit 1 ;;
esac
