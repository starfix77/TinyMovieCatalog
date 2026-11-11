#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

# Compress only source code
zip -r "$PROJECT_DIR/../TinyMovieCatalog.zip" . \
    -x \
    '.git/*' \
    'frontend.log' \
    'backend.log' \
    'docs/img/*' \
    'frontend/node_modules/*' \
    'frontend/dist/*' \
    'frontend/.angular/*' \
    'backend/.env' \
    'backend/data/db/*' \
    'backend/data/thumbnails/*' \
    'backend/venv/*' \
    'backend/.venv/*' \
    '*/__pycache__/*' \
    '*.pyc' \
    '*.pyo'
