# TinyMovieCatalog — Guide d'installation et de démarrage

Ce guide explique comment installer et lancer **TinyMovieCatalog** sur :

- [Windows](#windows)
- [Linux — distributions compatibles Debian (Debian, Ubuntu, Linux Mint…)](#linux--distributions-compatibles-debian)
- [Linux — distributions compatibles Red Hat (RHEL, Fedora, Rocky, AlmaLinux, CentOS Stream…)](#linux--distributions-compatibles-red-hat)
- [Linux — service systemd et mise à jour automatisée (toutes distributions)](#linux--service-systemd-et-mise-à-jour-automatisée)
- [macOS](#macos)


Voir le dossier /scripts par système d'exploitation pour les scripts d'installation / démarrage

```
/scripts                              
├──linux
│   ├── install.sh
│   └── start.sh
|   └── ...
├── macos
│   ├── install.sh
│   └── control.sh
|   └── laucnher.applescript
├── windows
    └── install.ps1
    └── start.ps1
    └── ...
```

Chaque section est autonome : lisez uniquement celle de votre système.
Sous Linux, une section supplémentaire (facultative) explique comment installer TinyMovieCatalog comme **service systemd** et le **mettre à jour avec un script**.
Les parties communes à tous les systèmes (configuration, première utilisation, dépannage) sont en fin de document.

---

## Vue d'ensemble

TinyMovieCatalog se compose de deux services qui tournent **en local** sur votre machine :

| Service | Technologie | Adresse par défaut |
|---|---|---|
| **Frontend** (interface) | Angular 19 | http://localhost:4200 |
| **Backend** (API) | Python / FastAPI (uvicorn) | http://localhost:8000 |

Documentation interactive de l'API : http://localhost:8000/docs

Les données (base SQLite et affiches) sont stockées dans `backend/data/`.v

### Prérequis (tous systèmes)

| Outil | Version | Rôle |
|---|---|---|
| **Python** | **3.10 ou plus récent** | Backend |
| **Node.js + npm** | 18.19+, 20.11+ ou 22+ (**20 ou 22 LTS recommandé**) | Frontend |
| **FFmpeg** (`ffprobe`, `ffplay`) | récent | Analyse des fichiers vidéo (`ffprobe`) et bouton PLAY (`ffplay`) |
| **Clé API TheMovieDB** | gratuite | Affiches, synopsis, distribution… (facultative, mais recommandée) |

> La clé TMDb se crée sur https://www.themoviedb.org/settings/api.
> Sans clé, les scans fonctionnent mais aucune affiche ni métadonnée n'est récupérée.

> **Connexion Internet** : nécessaire pour `npm install` / `pip install`, pour la compilation du frontend (`npm run build`, qui intègre des polices Google) et pour TheMovieDB.

---

## Windows

Testé avec Windows 10 et Windows 11. Utilisez **PowerShell** (pas l'invite de commandes `cmd`).

### 1. Installer les prérequis

**Option A — avec `winget`** (inclus dans Windows 10/11 récents), dans un PowerShell :

```powershell
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
```

**Option B — manuellement :**

| Outil | Téléchargement | Remarque |
|---|---|---|
| Python | https://www.python.org/downloads/ | Cochez **« Add python.exe to PATH »** dans l'installateur |
| Node.js (LTS) | https://nodejs.org/ | Installateur standard |
| FFmpeg | https://www.gyan.dev/ffmpeg/builds/ (version *release essentials*) | Extraire le zip, par exemple dans `C:\ffmpeg`, puis ajouter `C:\ffmpeg\bin` au `PATH` |

**Fermez puis rouvrez PowerShell**, puis vérifiez :

```powershell
python --version
node --version
npm --version
ffprobe -version
ffplay -version
```

> Si FFmpeg n'est pas dans le `PATH`, vous pourrez indiquer son chemin complet dans le fichier `.env` (voir [Configuration](#configuration-du-backend-env)).

### 2. Autoriser l'exécution des scripts PowerShell (une seule fois)

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3. Récupérer le projet

Décompressez `TinyMovieCatalog_x.y.z.zip` dans un dossier de votre choix, par exemple `C:\TinyMovieCatalog`, puis :

```powershell
cd C:\TinyMovieCatalog
```

### 4. Installer le backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
cd ..
```

Ouvrez ensuite `backend\.env` (Bloc-notes) et renseignez au minimum `TMDB_API_KEY` (voir [Configuration](#configuration-du-backend-env)).

> ⚠️ **N'utilisez pas `install.ps1` tel quel** : il crée l'environnement virtuel dans `backend\venv`, alors que `start.ps1` cherche `backend\.venv`. Suivez la procédure ci-dessus, qui crée bien `.venv`.

### 5. Installer le frontend

```powershell
cd frontend
npm install
cd ..
```

### 6. Démarrer l'application

**Méthode rapide** (les deux services dans la même console) :

```powershell
.\start.ps1
```

- Frontend : http://localhost:4200
- Backend : http://localhost:8000
- Journaux d'erreurs : `frontend.error.log` et `backend.error.log` à la racine du projet
- **Ctrl+C** arrête les deux services.

**Méthode manuelle** (deux fenêtres PowerShell) :

```powershell
# Fenêtre 1 — backend
cd C:\TinyMovieCatalog\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
# Fenêtre 2 — frontend
cd C:\TinyMovieCatalog\frontend
npm start
```

> Si `npm` est bloqué par la politique d'exécution, utilisez `npm.cmd start`.

Ouvrez ensuite http://localhost:4200 dans votre navigateur, puis passez à la [première utilisation](#première-utilisation).

---

## Linux — distributions compatibles Debian

Valable pour Debian, Ubuntu, Linux Mint, Pop!_OS, etc. (gestionnaire de paquets `apt`).

### 1. Installer les prérequis

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg curl git unzip
```

Vérifiez la version de Python (**3.10 minimum**) :

```bash
python3 --version
```

> Debian 11 et Ubuntu 20.04 fournissent Python 3.9 ou plus ancien : utilisez Debian 12 / Ubuntu 22.04 ou plus récent, ou installez un Python 3.10+ supplémentaire.

**Node.js** — les versions des dépôts Debian/Ubuntu sont souvent trop anciennes. Installez Node.js 22 LTS via NodeSource :

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

> Alternative : [nvm](https://github.com/nvm-sh/nvm) (`nvm install 22`), sans droits administrateur.

Vérifiez FFmpeg :

```bash
ffprobe -version
ffplay -version
```

### 2. Récupérer le projet

```bash
unzip TinyMovieCatalog_x.y.z.zip -d TinyMovieCatalog
cd TinyMovieCatalog
chmod +x *.sh
```

### 3. Installer

**Méthode rapide :**

```bash
./install.sh
```

Le script installe les dépendances npm, compile le frontend, crée `backend/.venv` et installe les dépendances Python.

**Méthode manuelle :**

```bash
# Frontend
cd frontend
npm install
cd ..

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
deactivate
cd ..
```

Éditez `backend/.env` et renseignez `TMDB_API_KEY` (voir [Configuration](#configuration-du-backend-env)) :

```bash
nano backend/.env
```

> Si vous utilisez `install.sh`, copiez aussi le fichier de configuration : `cp backend/.env.example backend/.env`.

### 4. Démarrer l'application

**Méthode rapide :**

```bash
./start.sh
```

- Frontend : http://localhost:4200
- Journaux : `frontend.log` et `backend.log` à la racine du projet
- **Ctrl+C** arrête les deux services.

**Méthode manuelle** (deux terminaux) :

```bash
# Terminal 1 — backend
cd TinyMovieCatalog/backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — frontend
cd TinyMovieCatalog/frontend
npm start
```

Ouvrez http://localhost:4200, puis passez à la [première utilisation](#première-utilisation).

> **Serveur sans interface graphique** : le bouton PLAY (`ffplay`) nécessite un affichage sur la machine qui exécute le backend. Le reste de l'application fonctionne depuis un navigateur.

### 5. (Facultatif) Service systemd et mise à jour automatisée

Pour lancer TinyMovieCatalog automatiquement au démarrage de la machine et le mettre à jour en une commande, voir la section [Linux — service systemd et mise à jour automatisée](#linux--service-systemd-et-mise-à-jour-automatisée).

---

## Linux — distributions compatibles Red Hat

Valable pour Fedora, RHEL, Rocky Linux, AlmaLinux, CentOS Stream, etc. (gestionnaire de paquets `dnf`).

### 1. Installer les prérequis

#### Python 3.10 ou plus récent

- **Fedora** : Python 3.10+ est déjà fourni.

  ```bash
  sudo dnf install -y python3 python3-pip git unzip curl
  python3 --version
  ```

- **RHEL / Rocky / AlmaLinux 8 et 9** : `python3` est **trop ancien** (3.6 ou 3.9). Installez une version récente en parallèle :

  ```bash
  sudo dnf install -y python3.12 python3.12-pip git unzip curl
  python3.12 --version
  ```

  (Si `python3.12` n'est pas disponible sur votre version, utilisez `python3.11`.)

  > Dans la suite, remplacez `python3` par `python3.12` (ou `python3.11`) à l'étape « créer l'environnement virtuel ». Le script `install.sh` utilise `python3` : sur RHEL/Rocky/Alma, utilisez la méthode manuelle.

#### Node.js 20 ou 22

- **Fedora** :

  ```bash
  sudo dnf install -y nodejs npm
  ```

- **RHEL / Rocky / AlmaLinux** :

  ```bash
  sudo dnf module enable -y nodejs:20
  sudo dnf install -y nodejs npm
  ```

  Ou, pour Node.js 22 LTS via NodeSource :

  ```bash
  curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
  sudo dnf install -y nodejs
  ```

Vérifiez : `node --version` et `npm --version`.

#### FFmpeg

Les dépôts Red Hat standard ne fournissent pas FFmpeg complet : activez **RPM Fusion** (et **EPEL** sur RHEL/Rocky/Alma).

- **Fedora** :

  ```bash
  sudo dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
  sudo dnf install -y ffmpeg
  ```

- **RHEL / Rocky / AlmaLinux 9** (remplacez `9` par `8` pour la version 8) :

  ```bash
  sudo dnf install -y epel-release
  sudo dnf install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm
  sudo dnf install -y ffmpeg
  ```

  Sur RHEL pur, activez d'abord EPEL selon la documentation Red Hat/Fedora (`epel-release` n'est pas dans les dépôts de base).

Vérifiez :

```bash
ffprobe -version
ffplay -version
```

> `ffprobe` est indispensable à l'analyse des vidéos ; `ffplay` ne sert qu'au bouton PLAY.

### 2. Récupérer le projet

```bash
unzip TinyMovieCatalog_x.y.z.zip -d TinyMovieCatalog
cd TinyMovieCatalog
chmod +x *.sh
```

### 3. Installer

**Fedora — méthode rapide :**

```bash
./install.sh
cp backend/.env.example backend/.env
```

**Toutes distributions — méthode manuelle** (obligatoire sur RHEL / Rocky / Alma) :

```bash
# Frontend
cd frontend
npm install
cd ..

# Backend (remplacez python3 par python3.12 si nécessaire)
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
deactivate
cd ..
```

Éditez `backend/.env` et renseignez `TMDB_API_KEY` (voir [Configuration](#configuration-du-backend-env)) :

```bash
nano backend/.env
```

### 4. Démarrer l'application

**Fedora — méthode rapide :**

```bash
./start.sh
```

**Toutes distributions — méthode manuelle** (deux terminaux ; indispensable avec un Python parallèle, car `start.sh` recrée l'environnement virtuel avec `python3`) :

```bash
# Terminal 1 — backend
cd TinyMovieCatalog/backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — frontend
cd TinyMovieCatalog/frontend
npm start
```

- Frontend : http://localhost:4200

> **Accès depuis un autre poste du réseau** : le pare-feu (`firewalld`) bloque par défaut les ports. Pour un usage uniquement local (`localhost`), rien à faire. SELinux n'a pas d'impact pour un usage local.

Ouvrez http://localhost:4200, puis passez à la [première utilisation](#première-utilisation).

### 5. (Facultatif) Service systemd et mise à jour automatisée

Pour lancer TinyMovieCatalog automatiquement au démarrage de la machine et le mettre à jour en une commande, voir la section [Linux — service systemd et mise à jour automatisée](#linux--service-systemd-et-mise-à-jour-automatisée). Lisez en particulier les remarques sur **SELinux** et sur le **Python parallèle** (RHEL / Rocky / AlmaLinux).

---

## Linux — service systemd et mise à jour automatisée

Valable pour **toutes les distributions Linux utilisant systemd** (Debian, Ubuntu, Linux Mint, Fedora, RHEL, Rocky, AlmaLinux…). Cette section est **facultative** : elle permet de lancer TinyMovieCatalog automatiquement au démarrage de la machine, et de le mettre à jour en une seule commande.

Trois fichiers sont utilisés ; ils doivent se trouver **à la racine du projet** (à côté de `start.sh`) :

| Fichier | Rôle |
|---|---|
| `tinymoviecatalog.service` | Modèle du service systemd |
| `install_service.sh` | Installe le service systemd (détecte automatiquement l'utilisateur et le dossier du projet) |
| `update_tinymoviecatalog.sh` | Met à jour l'application vers une nouvelle version (sauvegarde, récupération, dépendances, redémarrage) |

### Prérequis

- L'installation est terminée (étapes 1 à 3 de la section de votre distribution) et `backend/.env` est configuré.
- `./start.sh` fonctionne en lancement manuel : testez-le une fois, puis arrêtez-le avec **Ctrl+C**.
- Vous disposez des droits `sudo`.

```bash
cd TinyMovieCatalog
chmod +x install_service.sh update_tinymoviecatalog.sh
```

### 1. Installer le service systemd

```bash
sudo ./install_service.sh
sudo systemctl start tinymoviecatalog
```

`install_service.sh` :

- génère `/etc/systemd/system/tinymoviecatalog.service` à partir du modèle, avec votre nom d'utilisateur et le dossier du projet ;
- exécute `systemctl daemon-reload` ;
- active le service (`systemctl enable`) : il démarrera donc **automatiquement au démarrage de la machine**.

Le service lance `start.sh` (backend + frontend) avec votre compte utilisateur, et le redémarre automatiquement en cas d'arrêt anormal.

Commandes utiles :

| Action | Commande |
|---|---|
| Démarrer | `sudo systemctl start tinymoviecatalog` |
| Arrêter | `sudo systemctl stop tinymoviecatalog` |
| Redémarrer | `sudo systemctl restart tinymoviecatalog` |
| Voir l'état | `sudo systemctl status tinymoviecatalog` |
| Suivre les journaux en direct | `journalctl -u tinymoviecatalog -f` |
| Ne plus démarrer au boot | `sudo systemctl disable tinymoviecatalog` |

Les journaux applicatifs `backend.log` et `frontend.log` restent disponibles à la racine du projet.

> ⚠️ **Ne lancez pas `./start.sh` à la main pendant que le service tourne** : les ports 4200 et 8000 seraient déjà occupés. Arrêtez d'abord le service avec `sudo systemctl stop tinymoviecatalog`.

**Points d'attention**

- **`start.sh` doit rester au premier plan.** Si `start.sh` lance les deux processus en arrière-plan (`&`), il doit se terminer par `wait` ; sinon systemd considère que le service s'est arrêté et tue le backend et le frontend.
- **Node.js installé via nvm** : systemd ne connaît pas le `PATH` de votre terminal. Éditez `/etc/systemd/system/tinymoviecatalog.service`, ajoutez une ligne `Environment=PATH=/home/VOTRE_USER/.nvm/versions/node/vXX.X.X/bin:/usr/local/bin:/usr/bin:/bin` dans la section `[Service]`, puis exécutez `sudo systemctl daemon-reload && sudo systemctl restart tinymoviecatalog`.
- **RHEL / Rocky / AlmaLinux avec Python installé en parallèle** : `start.sh` utilise `python3` (voir la section Red Hat). Vérifiez que votre lancement fonctionne bien avec le `.venv` existant avant d'installer le service.
- **RHEL / Rocky / AlmaLinux / Fedora (SELinux)** : SELinux peut empêcher un service systemd d'exécuter des programmes situés dans `/home`. Si le service échoue avec « Permission denied » alors que `./start.sh` fonctionne en manuel, consultez `sudo ausearch -m avc -ts recent`, ou installez le projet en dehors de `/home` (par exemple dans `/opt`) et adaptez le contexte SELinux.
- **Changement d'emplacement du projet** : relancez `sudo ./install_service.sh` depuis le nouveau dossier pour régénérer le service.

### 2. Mettre à jour avec `update_tinymoviecatalog.sh`

Depuis la racine du projet :

```bash
./update_tinymoviecatalog.sh                                      # mise à jour via git pull
./update_tinymoviecatalog.sh --zip TinyMovieCatalog_0.9.25.zip    # mise à jour depuis une archive
./update_tinymoviecatalog.sh --no-restart                         # sans arrêt ni redémarrage
```

Le script exécute les étapes suivantes :

| Étape | Action |
|---|---|
| 0 | Arrête le service `tinymoviecatalog` s'il existe et s'il est actif (base de données cohérente pour la sauvegarde) |
| 1 | Sauvegarde `backend/data/` (base et affiches) et `backend/.env` dans une archive horodatée |
| 2 | **Mode git** : `git pull` depuis https://github.com/starfix77/TinyMovieCatalog.git |
| 3 | **Mode `--zip`** : décompresse l'archive en conservant votre `backend/data/` et votre `backend/.env` |
| 4 | Relance l'installation des dépendances : `npm install` (frontend) et `pip install -r requirements.txt` (backend, dans `.venv`) |
| 5 | Redémarre le service et vérifie qu'il est actif. Les nouvelles tables de la base sont créées automatiquement au démarrage |

Remarques :

- Les sauvegardes sont créées dans `../TinyMovieCatalog_backups/` (dossier parent du projet). Pour choisir un autre dossier : `BACKUP_DIR=/chemin/backups ./update_tinymoviecatalog.sh`.
- Si le script n'est pas lancé en `root`, il utilise `sudo` pour piloter le service et peut demander votre mot de passe.
- Le **mode git** nécessite que le projet soit un dépôt git cloné et sans modification locale conflictuelle. Si vous avez installé le projet depuis une archive `.zip`, utilisez plutôt le mode `--zip`.
- Si le service porte un autre nom : `SERVICE_NAME=monservice ./update_tinymoviecatalog.sh`. Pour utiliser votre propre commande de redémarrage à la place du service : `RESTART_CMD="..." ./update_tinymoviecatalog.sh`.
- En cas d'erreur pendant la mise à jour, le script vous indique que le service est resté arrêté et la commande pour le relancer (`sudo systemctl start tinymoviecatalog`).

**Restaurer une sauvegarde** (depuis la racine du projet) :

```bash
sudo systemctl stop tinymoviecatalog
tar -xzf ../TinyMovieCatalog_backups/TinyMovieCatalog_backup_AAAAMMJJ_HHMMSS.tar.gz
sudo systemctl start tinymoviecatalog
```

---

## macOS

Valable pour macOS sur Mac Intel et Apple Silicon (M1/M2/M3…). Utilisez l'application **Terminal**.

### 1. Installer les prérequis avec Homebrew

Si Homebrew n'est pas installé, suivez les instructions sur https://brew.sh. Puis :

```bash
brew install python node ffmpeg
```

Vérifiez :

```bash
python3 --version     # 3.10 minimum
node --version
npm --version
ffprobe -version
ffplay -version
```

> `brew install ffmpeg` fournit `ffprobe` et `ffplay`.

### 2. Récupérer le projet

Décompressez `TinyMovieCatalog_x.y.z.zip` (double-clic ou `unzip`), puis :

```bash
cd ~/TinyMovieCatalog
chmod +x *.sh
```

Si macOS bloque les scripts téléchargés (message « développeur non identifié »), retirez l'attribut de quarantaine :

```bash
xattr -dr com.apple.quarantine .
```

### 3. Installer

**Méthode rapide :**

```bash
./install.sh
cp backend/.env.example backend/.env
```

**Méthode manuelle :**

```bash
# Frontend
cd frontend
npm install
cd ..

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
deactivate
cd ..
```

Éditez `backend/.env` et renseignez `TMDB_API_KEY` (voir [Configuration](#configuration-du-backend-env)) :

```bash
open -e backend/.env
```

### 4. Démarrer l'application

**Méthode rapide :**

```bash
./start.sh
```

- Frontend : http://localhost:4200
- Journaux : `frontend.log` et `backend.log` à la racine du projet
- **Ctrl+C** arrête les deux services.

**Méthode manuelle** (deux fenêtres ou onglets du Terminal) :

```bash
# Terminal 1 — backend
cd ~/TinyMovieCatalog/backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — frontend
cd ~/TinyMovieCatalog/frontend
npm start
```

Ouvrez http://localhost:4200, puis passez à la [première utilisation](#première-utilisation).

> Au premier accès à un disque externe ou réseau, macOS peut demander l'autorisation d'accès aux fichiers pour le Terminal : acceptez-la, sinon le scan ne verra pas vos films.

---

# Informations communes

## Configuration du backend (`.env`)

Le fichier `backend/.env` (copie de `backend/.env.example`) contient :

```ini
TMDB_API_KEY=votre_cle_ici
TMDB_LANGUAGE=fr-FR
FFPROBE_PATH=ffprobe
FFPLAY_PATH=ffplay
```

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `TMDB_API_KEY` | Clé API TheMovieDB (gratuite) | vide |
| `TMDB_LANGUAGE` | Langue des métadonnées | `fr-FR` |
| `FFPROBE_PATH` | Chemin de `ffprobe` si absent du `PATH` | `ffprobe` |
| `FFPLAY_PATH` | Chemin de `ffplay` (bouton PLAY). Si `FFPROBE_PATH` est un chemin complet, `ffplay` est cherché dans le même dossier | `ffplay` |

Exemple Windows avec FFmpeg dans `C:\ffmpeg` :

```ini
FFPROBE_PATH=C:\ffmpeg\bin\ffprobe.exe
FFPLAY_PATH=C:\ffmpeg\bin\ffplay.exe
```

> Redémarrez le backend après toute modification du fichier `.env`.

## Première utilisation

1. Ouvrez http://localhost:4200.
2. Dans le panneau de gauche, cliquez sur **« + Nouvelle bibliothèque »**, donnez un nom, choisissez le type (**Films** ou **Séries TV**) et indiquez le **dossier racine** (ex. `C:\MesFilms`, `/home/user/MesFilms`, `/Users/moi/Films`).
3. Cliquez sur l'icône **⟳** pour lancer un scan.

Organisation attendue des dossiers :

```
MesFilms/
├── Inception (2010)/
│   ├── Inception.mkv
│   └── Inception.fr.srt        (optionnel)
├── Interstellar (2014)/
│   └── Interstellar.mkv
└── ...
```

Chaque film doit se trouver dans un dossier nommé **`Titre du film (Année)`**. Pour les séries : un dossier **`Titre de la série (Année)`** par série, avec les épisodes (éventuellement dans des sous-dossiers de saisons).

## Mode « release » (facultatif)

`npm start` lance le serveur de développement Angular. Pour servir la version compilée à la place :

```bash
cd frontend
npm run build
node server.js
```

L'application est alors disponible sur http://localhost:3000 (le backend reste sur le port 8000).

## Arrêter l'application

- Avec `start.sh` / `start.ps1` : **Ctrl+C** dans la console.
- En mode manuel : **Ctrl+C** dans chacune des deux fenêtres.
- Avec le service systemd (Linux) : `sudo systemctl stop tinymoviecatalog`.
- Si un processus reste actif :
  - Linux / macOS : `pkill -f uvicorn` puis `pkill -f "ng serve"`
  - Windows : `Get-Process python, node | Stop-Process`

## Mettre à jour vers une nouvelle version

> **Linux** : le script `update_tinymoviecatalog.sh` automatise toutes les étapes ci-dessous (arrêt du service, sauvegarde, mise à jour, dépendances, redémarrage). Voir [Mettre à jour avec `update_tinymoviecatalog.sh`](#2-mettre-à-jour-avec-update_tinymoviecatalogsh). Windows et macOS : suivez la procédure manuelle ci-dessous.

1. Arrêtez l'application.
2. **Sauvegardez** `backend/data/` (base et affiches) et `backend/.env`.
3. Décompressez la nouvelle version, en conservant votre `backend/data/` et votre `backend/.env`.
4. Relancez les installations de dépendances :
   - `cd frontend && npm install`
   - `cd backend`, activez `.venv`, puis `pip install -r requirements.txt`
5. Redémarrez l'application. Les nouvelles tables de la base sont créées automatiquement au démarrage.

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `python` / `python3` / `node` introuvable | Outil non installé ou `PATH` non à jour | Réinstallez, puis **rouvrez** le terminal |
| `TypeError: unsupported operand type(s) for \|` au démarrage du backend | Python trop ancien (< 3.10) | Installez Python 3.10 ou plus récent et recréez `backend/.venv` |
| Le frontend affiche « Impossible de charger… » | Backend arrêté ou sur un autre port | Vérifiez http://localhost:8000/api/health (doit répondre `{"status":"ok"}`) |
| `Address already in use` / port 4200 ou 8000 occupé | Une instance tourne déjà | Arrêtez-la (voir ci-dessus) ou changez de port (`--port` pour uvicorn, `npm start -- --port 4300` pour Angular) |
| Les détails vidéo (codec, résolution, pistes) sont vides | `ffprobe` introuvable | Vérifiez `ffprobe -version` ou renseignez `FFPROBE_PATH` dans `.env` |
| Aucune affiche ni synopsis | Clé TMDb absente ou invalide | Renseignez `TMDB_API_KEY` dans `.env`, redémarrez le backend, relancez un scan |
| Le bouton PLAY ne fait rien | `ffplay` introuvable ou pas d'affichage | Vérifiez `ffplay -version` ou renseignez `FFPLAY_PATH` |
| `npm run build` échoue sur les polices | Pas d'accès Internet (polices Google) | Vérifiez la connexion ; utilisez `npm start` en attendant |
| Windows : « l'exécution de scripts est désactivée » | Politique d'exécution PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Le scan ne trouve aucun film | Mauvaise structure de dossiers ou mauvais chemin | Vérifiez le dossier racine et le nommage `Titre (Année)` ; choisissez « Structure mixte » dans le dialogue de scan si nécessaire |
| Linux / macOS : `Permission denied` sur `./install.sh` | Scripts non exécutables | `chmod +x *.sh` |
| Linux : `Unit tinymoviecatalog.service not found` | Service systemd non installé | `sudo ./install_service.sh` (voir [service systemd](#linux--service-systemd-et-mise-à-jour-automatisée)) |
| Linux : le service s'arrête juste après `start` | `start.sh` rend la main immédiatement, ou `node` / `npm` introuvable (nvm) | Consultez `journalctl -u tinymoviecatalog -n 50` ; vérifiez que `start.sh` reste au premier plan ; ajoutez `Environment=PATH=...` au service |
| Linux (RHEL / Fedora…) : le service échoue avec `Permission denied` alors que `./start.sh` fonctionne | SELinux bloque l'exécution depuis `/home` | `sudo ausearch -m avc -ts recent` ; installez le projet hors de `/home` (ex. `/opt`) |
| Linux : `Address already in use` au démarrage du service | `./start.sh` lancé à la main ou autre instance active | `sudo systemctl stop tinymoviecatalog`, puis `pkill -f uvicorn` et `pkill -f "ng serve"` si nécessaire |
| Linux : mise à jour interrompue, application arrêtée | Erreur pendant `update_tinymoviecatalog.sh` | Corrigez l'erreur, relancez le script ou `sudo systemctl start tinymoviecatalog` ; sauvegarde dans `../TinyMovieCatalog_backups/` |

Les journaux sont dans `frontend.log` / `backend.log` (Linux, macOS) ou `frontend.error.log` / `backend.error.log` (Windows), à la racine du projet.
