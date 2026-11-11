#!/usr/bin/env bash
# =============================================================================
# TinyMovieCatalog - Mise à jour vers une nouvelle version
#
# Usage :
#   ./update_tinymoviecatalog.sh                          # mise à jour via git pull
#   ./update_tinymoviecatalog.sh --zip TinyMovieCatalog_0.9.25.zip   # via archive
#   ./update_tinymoviecatalog.sh --no-restart             # sans redémarrage
#
# Variables optionnelles :
#   SERVICE_NAME="tinymoviecatalog"      # service systemd (défaut : tinymoviecatalog)
#   RESTART_CMD="..."                    # commande personnalisée (remplace le service)
#   BACKUP_DIR="/chemin/backups"         # dossier des sauvegardes
#
# Si le service systemd existe, il est arrêté avant la sauvegarde puis relancé
# à la fin (sudo requis si le script n'est pas lancé en root).
# =============================================================================
set -euo pipefail

REPO_URL="https://github.com/starfix77/TinyMovieCatalog.git"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/../TinyMovieCatalog_backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
ZIP_FILE=""
DO_RESTART=1
SERVICE_NAME="${SERVICE_NAME:-tinymoviecatalog}"
SERVICE_STOPPED=0

log()  { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[ERR ]\033[0m %s\n' "$*" >&2; exit 1; }

# systemctl avec sudo si nécessaire
svc() { if [[ $EUID -eq 0 ]]; then systemctl "$@"; else sudo systemctl "$@"; fi; }
service_exists() {
  command -v systemctl >/dev/null 2>&1 && systemctl cat "${SERVICE_NAME}.service" >/dev/null 2>&1
}

cleanup() {
  local rc=$?
  rm -rf "${TMP_KEEP:-}" "${TMP_UNZIP:-}"
  if [[ $SERVICE_STOPPED -eq 1 && $rc -ne 0 ]]; then
    warn "Erreur : le service ${SERVICE_NAME} est resté ARRÊTÉ."
    warn "Après correction : sudo systemctl start ${SERVICE_NAME}"
  fi
}
trap cleanup EXIT

# --- Arguments ---------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --zip)        ZIP_FILE="${2:-}"; [[ -f "$ZIP_FILE" ]] || err "Archive introuvable : $ZIP_FILE"; shift 2 ;;
    --no-restart) DO_RESTART=0; shift ;;
    -h|--help)    sed -n '2,17p' "$0"; exit 0 ;;
    *)            err "Option inconnue : $1" ;;
  esac
done

cd "$PROJECT_DIR"
[[ -d backend && -d frontend ]] || err "Lancez ce script à la racine du projet (dossiers backend/ et frontend/ introuvables)."

# --- 0. Arrêt du service (base de données cohérente pour la sauvegarde) ------
USE_SERVICE=0
if [[ $DO_RESTART -eq 1 && -z "${RESTART_CMD:-}" ]] && service_exists; then
  USE_SERVICE=1
  if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
    log "Étape 0/5 : arrêt du service ${SERVICE_NAME}"
    svc stop "${SERVICE_NAME}.service"
    SERVICE_STOPPED=1
  else
    log "Étape 0/5 : le service ${SERVICE_NAME} est déjà arrêté"
  fi
fi

# --- 1. Sauvegarde de backend/data et backend/.env ---------------------------
log "Étape 1/5 : sauvegarde de backend/data et backend/.env"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/TinyMovieCatalog_backup_${STAMP}.tar.gz"
TO_SAVE=()
[[ -d backend/data ]] && TO_SAVE+=("backend/data")
[[ -f backend/.env ]] && TO_SAVE+=("backend/.env")
if [[ ${#TO_SAVE[@]} -gt 0 ]]; then
  tar -czf "$BACKUP_FILE" "${TO_SAVE[@]}"
  log "Sauvegarde créée : $BACKUP_FILE"
else
  warn "Rien à sauvegarder (ni backend/data ni backend/.env)."
fi

# Copie de sécurité temporaire pour restauration en fin de mise à jour
TMP_KEEP="$(mktemp -d)"
[[ -d backend/data ]] && cp -a backend/data "$TMP_KEEP/data"
[[ -f backend/.env ]] && cp -a backend/.env "$TMP_KEEP/.env"

# --- 2/3. Récupération de la nouvelle version --------------------------------
if [[ -z "$ZIP_FILE" ]]; then
  log "Étape 2/5 : git pull depuis $REPO_URL"
  command -v git >/dev/null || err "git n'est pas installé."
  if [[ -d .git ]]; then
    git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REPO_URL"
    git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)"
  else
    warn "Pas de dépôt git ici : initialisation et récupération depuis le dépôt."
    git init -q
    git remote add origin "$REPO_URL"
    git fetch origin
    git checkout -f -B main origin/main
  fi
else
  log "Étape 3/5 : décompression de $ZIP_FILE (data et .env conservés)"
  command -v unzip >/dev/null || err "unzip n'est pas installé."
  TMP_UNZIP="$(mktemp -d)"
  unzip -q "$ZIP_FILE" -d "$TMP_UNZIP"
  # Si l'archive contient un unique dossier racine, on descend dedans
  mapfile -t ENTRIES < <(find "$TMP_UNZIP" -mindepth 1 -maxdepth 1)
  SRC="$TMP_UNZIP"
  [[ ${#ENTRIES[@]} -eq 1 && -d "${ENTRIES[0]}" ]] && SRC="${ENTRIES[0]}"
  [[ -d "$SRC/backend" && -d "$SRC/frontend" ]] || err "Archive invalide (backend/ ou frontend/ manquant)."

  if command -v rsync >/dev/null; then
    rsync -a --exclude 'backend/data/' --exclude 'backend/.env' \
          --exclude 'backend/.venv/' --exclude 'frontend/node_modules/' \
          "$SRC"/ "$PROJECT_DIR"/
  else
    warn "rsync absent : copie avec cp (data/.env seront restaurés ensuite)."
    cp -a "$SRC"/. "$PROJECT_DIR"/
  fi
fi

# --- Restauration de data et .env (sécurité) ---------------------------------
log "Restauration de backend/data et backend/.env"
if [[ -d "$TMP_KEEP/data" ]]; then
  mkdir -p backend/data
  cp -a "$TMP_KEEP/data"/. backend/data/
fi
[[ -f "$TMP_KEEP/.env" ]] && cp -a "$TMP_KEEP/.env" backend/.env

# --- 4. Dépendances ----------------------------------------------------------
log "Étape 4/5 : installation des dépendances"
( cd frontend && npm install )

(
  cd backend
  if [[ ! -d .venv ]]; then
    warn ".venv introuvable : création."
    python3 -m venv .venv 2>/dev/null || python -m venv .venv
  fi
  # shellcheck disable=SC1091
  if [[ -f .venv/bin/activate ]]; then source .venv/bin/activate
  elif [[ -f .venv/Scripts/activate ]]; then source .venv/Scripts/activate
  else err "Impossible d'activer .venv"; fi
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt
)

# --- 5. Redémarrage ----------------------------------------------------------
if [[ $DO_RESTART -eq 1 ]]; then
  if [[ -n "${RESTART_CMD:-}" ]]; then
    log "Étape 5/5 : redémarrage via RESTART_CMD"
    if ! eval "$RESTART_CMD"; then
      warn "La commande de redémarrage a échoué : $RESTART_CMD"
      warn "La mise à jour est terminée, redémarrez l'application manuellement."
    fi
  elif [[ $USE_SERVICE -eq 1 ]]; then
    log "Étape 5/5 : redémarrage du service ${SERVICE_NAME}"
    if svc restart "${SERVICE_NAME}.service"; then
      SERVICE_STOPPED=0
      sleep 3
      if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log "Service ${SERVICE_NAME} actif."
      else
        warn "Le service ne reste pas actif : journalctl -u ${SERVICE_NAME} -n 50"
      fi
    else
      warn "Échec du redémarrage du service ${SERVICE_NAME}."
    fi
  else
    warn "Service ${SERVICE_NAME} introuvable et RESTART_CMD non défini : redémarrez l'application manuellement."
    warn "Les nouvelles tables de la base sont créées automatiquement au démarrage."
  fi
else
  log "Étape 5/5 : redémarrage ignoré (--no-restart)."
fi

VERSION="$(grep -hoE "APP_VERSION = '[0-9]+\.[0-9]+\.[0-9]+'" \
  "$(find frontend/src -name 'app-settings.ts' | head -n1)" 2>/dev/null \
  | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1 || true)"
VERSION="${VERSION:+TinyMovieCatalog v$VERSION}"
log "Mise à jour terminée ${VERSION:+($VERSION)}."
log "Sauvegarde conservée dans : $BACKUP_DIR"
log "Lancer l'application  http://localhost:4200/"
