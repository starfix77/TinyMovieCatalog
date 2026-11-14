# Raccourci (launcher) sous GNOME


Sous GNOME, créer un raccourci (launcher) au format .desktop qui permet de :
1. Exécuter ton script Bash start.sh.
2. Ouvrir automatiquement Firefox sur http://localhost:4200/.
3. Afficher une icône dans le menu des applications ou sur le bureau.




## 1. Créer le fichier launcher
Ouvre un terminal et exécute :

```bash
nano ~/.local/share/applications/tinymoviecatalog.desktop
```

Coller le code suivant

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Tiny Movie Catalog
Comment=Start Tiny Movie Catalog and open Firefox
Exec=bash -c '"$HOME/Applications/TinyMovieCatalog/scripts/linux/start.sh" & until curl -fsS http://localhost:4200/ >/dev/null; do sleep 1; done; firefox htt>
Icon=tinymoviecatalog
Terminal=false
Categories=Network;Utility;
StartupNotify=true
```

Enregistree avec Ctrl+O, puis quitte avec Ctrl+X.


## 2. Rendre le launcher exécutable, actualiser sous Fedora Gnome

```bash
chmod +x ~/.local/share/applications/tinymoviecatalog.desktop

update-desktop-database ~/.local/share/applications/
```

## 3. Icone pour le launcher

```bash
# recopie de l'icone solution plus propre GNOME Fedora
sudo ln -s "$HOME/Applications/TinyMovieCatalog/docs/img/favicon-128x128.png" /usr/local/share/icons/tinymoviecatalog.png
```

## 4. Tester le launcher
Maintenant on peut faire:
- Appuyer sur la touche [**Super**].
- Rechercher Tiny Movie Catalog.
- Cliquer sur son icône.

![TinyMovieCatalog](../../docs/img/favicon-64x64.png) 


Le comportement sera :
- Exécution du script 'start.sh'
- Attente de 3 secondes.
- Ouverture de Firefox sur 'http://localhost:4200/'