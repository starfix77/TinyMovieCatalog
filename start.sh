#!/bin/bash

# Arrêter le script en cas d'erreur
set -e

# Répertoire racine du projet
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "======================================"
echo "   TinyMovieCatalog - Démarrage"
echo "======================================"

# Fonction de nettoyage à la fermeture du script
cleanup() {
    echo ""
    echo "Arrêt des serveurs..."

    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true

    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# --------------------------------------
# Lancer le frontend
# --------------------------------------

echo "Démarrage du frontend..."

cd "$PROJECT_DIR/frontend"

# mode dev
npm start > "$PROJECT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!


# mode build 
# node server.js > "$PROJECT_DIR/frontend.log" 2>&1 & FRONTEND_PID=$!

echo "Frontend démarré (PID: $FRONTEND_PID)"

# --------------------------------------
# Attendre quelques secondes
# --------------------------------------

sleep 2

# --------------------------------------
# Lancer le backend
# --------------------------------------

echo "Démarrage du backend..."

cd "$PROJECT_DIR/backend"

source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000 \
    > "$PROJECT_DIR/backend.log" 2>&1 &

BACKEND_PID=$!

echo "Backend démarré (PID: $BACKEND_PID)"

echo ""
echo "======================================"
echo "   Serveurs démarrés"
echo "======================================"
echo ""
echo "Frontend : http://localhost:4200"
echo "Backend  : http://localhost:8000"
echo ""
echo "Logs frontend : $PROJECT_DIR/frontend.log"
echo "Logs backend  : $PROJECT_DIR/backend.log"
echo ""
echo "Appuyez sur CTRL+C pour arrêter les deux serveurs."
echo ""

# --------------------------------------
# Attendre les deux processus
# --------------------------------------

wait "$FRONTEND_PID" "$BACKEND_PID"


