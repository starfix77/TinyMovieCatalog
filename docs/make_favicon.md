# Génération du Favicon.ico multi-dimensions 16x16, 24x24, 32x32 et 48x48

```bash
# Installation ImageMagick

# linux Debian / Ubuntu ...
sudo apt install imagemagick
# linux Fedora / RedHat / Rocky
sudo dnf install imagemagick
# macOS
sudo brew install imagemagick


# Création favicon.ico
magick favicon-256x256.png  \
 -background none \
 -define icon:auto-resize=48,32,24,16 \
 favicon.ico

# Vérification des dimensions présentes dans le fichier ICO
magick identify favicon.ico

# Recopie dans le dossier cible
cp favicon.ico ../frontend/src

```