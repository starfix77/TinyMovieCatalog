#!/usr/bin/env bash
# Installe le service systemd "tinymoviecatalog" à partir du modèle
# tinymoviecatalog.service (utilisateur et dossier détectés automatiquement).
#
# Usage (depuis la racine du projet) : sudo ./install_service.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$PROJECT_DIR/tinymoviecatalog.service"
TARGET="/etc/systemd/system/tinymoviecatalog.service"
SERVICE_USER="${SUDO_USER:-$(id -un)}"

[[ $EUID -eq 0 ]] || { echo "Lancez avec sudo : sudo $0" >&2; exit 1; }
[[ -f "$TEMPLATE" ]] || { echo "Modèle introuvable : $TEMPLATE" >&2; exit 1; }
[[ -f "$PROJECT_DIR/start.sh" ]] || { echo "start.sh introuvable dans $PROJECT_DIR" >&2; exit 1; }
chmod +x "$PROJECT_DIR/start.sh"

sed -e "s|__USER__|$SERVICE_USER|g" -e "s|__DIR__|$PROJECT_DIR|g" "$TEMPLATE" > "$TARGET"
echo "Service écrit dans $TARGET (utilisateur : $SERVICE_USER, dossier : $PROJECT_DIR)"

systemctl daemon-reload
systemctl enable tinymoviecatalog
echo
echo "Terminé. Commandes utiles :"
echo "  sudo systemctl start tinymoviecatalog"
echo "  sudo systemctl restart tinymoviecatalog"
echo "  sudo systemctl status tinymoviecatalog"
echo "  journalctl -u tinymoviecatalog -f"
