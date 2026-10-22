#!/bin/bash

zip -r ../TinyMovieCatalog.zip . \
    -x \
    '*/.git/*' \
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
