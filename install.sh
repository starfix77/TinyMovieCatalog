#!/bin/bash

# Arrêter immédiatement en cas d'erreur
set -e

# Répertoire racine du projet
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=========================================="
echo "   TinyMovieCatalog - Installation"
echo "=========================================="
echo ""

# Vérification Node.js / npm
echo ">> Vérification de Node.js et npm..."

if ! command -v node >/dev/null 2>&1; then
    echo "ERREUR : Node.js n'est pas installé."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "ERREUR : npm n'est pas installé."
    exit 1
fi

echo "Node.js : $(node --version)"
echo "npm     : $(npm --version)"
echo ""

# ------------------------------------------
# Installation frontend
# ------------------------------------------

echo "=========================================="
echo "   Installation du frontend"
echo "=========================================="

cd "$PROJECT_DIR/frontend"

echo "Répertoire : $(pwd)"
echo ""
echo ">> Installation des dépendances npm..."
echo ""

npm install

echo ""
echo ">> Installation frontend terminée."
echo ""

# ------------------------------------------
# Installation backend
# ------------------------------------------

echo "=========================================="
echo "   Installation du backend"
echo "=========================================="

cd "$PROJECT_DIR/backend"

echo "Répertoire : $(pwd)"
echo ""

# Vérification de Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERREUR : Python 3 n'est pas installé."
    exit 1
fi

echo "Python : $(python3 --version)"
echo ""

# ------------------------------------------
# Création environnement virtuel
# ------------------------------------------

if [ ! -d ".venv" ]; then
    echo ">> Création de l'environnement virtuel Python..."

    python3 -m venv .venv
else
    echo ">> Environnement virtuel .venv déjà présent."
fi

echo ""

# ------------------------------------------
# Activation environnement virtuel
# ------------------------------------------

echo ">> Activation de l'environnement virtuel..."

source .venv/bin/activate

echo "Python utilisé : $(which python)"
echo ""

# ------------------------------------------
# Mise à jour pip
# ------------------------------------------

echo ">> Mise à jour de pip..."

python -m pip install --upgrade pip

echo ""

# ------------------------------------------
# Installation dépendances Python
# ------------------------------------------

echo ">> Installation des dépendances Python..."

python -m pip install -r requirements.txt

echo ""

# ------------------------------------------
# Fin
# ------------------------------------------

echo "=========================================="
echo "   Installation terminée avec succès"
echo "=========================================="
echo ""
echo "Frontend : $PROJECT_DIR/frontend"
echo "Backend  : $PROJECT_DIR/backend"
echo "Python   : $PROJECT_DIR/backend/.venv/bin/python"
echo ""
echo "Pour démarrer le projet :"
echo ""
echo "    ./start.sh"
echo ""


