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
#   RESTART_CMD="systemctl restart tinymoviecatalog"   # commande de redémarrage
#   BACKUP_DIR="/chemin/backups"                       # dossier des sauvegardes
# =============================================================================
set -euo pipefail

REPO_URL="https://github.com/starfix77/TinyMovieCatalog.git"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/../TinyMovieCatalog_backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
ZIP_FILE=""
DO_RESTART=1

log()  { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[ERR ]\033[0m %s\n' "$*" >&2; exit 1; }

# --- Arguments ---------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --zip)        ZIP_FILE="${2:-}"; [[ -f "$ZIP_FILE" ]] || err "Archive introuvable : $ZIP_FILE"; shift 2 ;;
    --no-restart) DO_RESTART=0; shift ;;
    -h|--help)    sed -n '2,13p' "$0"; exit 0 ;;
    *)            err "Option inconnue : $1" ;;
  esac
done

cd "$PROJECT_DIR"
[[ -d backend && -d frontend ]] || err "Lancez ce script à la racine du projet (dossiers backend/ et frontend/ introuvables)."

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
trap 'rm -rf "$TMP_KEEP" "${TMP_UNZIP:-}"' EXIT
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
  log "Étape 5/5 : redémarrage de l'application"
  if [[ -n "${RESTART_CMD:-}" ]]; then
    eval "$RESTART_CMD"
  else
    warn "RESTART_CMD non défini : redémarrez l'application manuellement."
    warn "Les nouvelles tables de la base sont créées automatiquement au démarrage."
  fi
else
  log "Étape 5/5 : redémarrage ignoré (--no-restart)."
fi

VERSION="$(grep -oE "TinyMovieCatalog v[0-9]+\.[0-9]+\.[0-9]+" \
  "$(find frontend -name 'library-selector.component.ts' -not -path '*/node_modules/*' | head -n1)" 2>/dev/null | head -n1 || true)"
log "Mise à jour terminée ${VERSION:+($VERSION)}."
log "Sauvegarde conservée dans : $BACKUP_DIR"
