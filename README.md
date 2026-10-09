# TinyMovieCatalog

Application locale de gestion de bibliotheques de films (MKV/MP4) :
- **Frontend** : Angular 19 (standalone components)
- **Backend** : Python (FastAPI) — scan des dossiers, analyse video via FFmpeg/ffprobe, enrichissement TheMovieDB, base SQLite locale
- **Usage 100% local**, aucune authentification

```
project/
├── backend/          API Python (FastAPI)
│   ├── app/
│   ├── data/          <- base SQLite + vignettes (partage entre bibliotheques)
│   ├── requirements.txt
│   └── .env.example
└── frontend/         Application Angular
    └── src/
```

## Structure de dossiers de bibliotheque attendue
Exemple de structure de dossiers
```
C:\MesFilms                              (ou /home/user/MesFilms sous Linux)
├── Inception (2010)\
│   ├── Inception.mkv
│   └── Inception.fr.srt        (optionnel)
├── Interstellar (2014)\
│   └── Interstellar.mkv
└── ...
```

<span style="color:red">IMPORTANT</span>: Chaque film doit être dans un dossier nommé</span> **Titre du film (Annee)**, contenant
obligatoirement un fichier video (`.mkv`, `.mp4`, `.avi`, `.m4v`) et, en
option, un ou plusieurs fichiers de sous-titres (`.srt`, `.ass`, `.ssa`,
`.sub`, `.vtt`).



## 1. Prérequis

| Outil | Windows | Linux |
|---|---|---|
| Python 3.10+ | https://www.python.org/downloads/ | `sudo apt install python3 python3-pip python3-venv` |
| Node.js 18+ / npm | https://nodejs.org/ | `sudo apt install nodejs npm` (ou nvm) |
| FFmpeg (fournit `ffprobe`) | https://www.gyan.dev/ffmpeg/builds/ (ajouter `bin\` au PATH) | `sudo apt install ffmpeg` |
| Angular CLI | `npm install -g @angular/cli` | `npm install -g @angular/cli` |

Vous aurez également besoin d'une **clé API TheMovieDB** (gratuite) :
https://www.themoviedb.org/settings/api

---

<span style="color:darkgreen">**Astuce installation et lancement RAPIDE pour LINUX**</span>

```bash
chmod +x *.sh
./install.sh
./start.sh
```
sinon suivre les étapes suivantes voir chapitre Installation et lancement (backend + frontend) 


## 2. Installation

**Installation du backend**

Editez le fichier de configuration `backend/.env` :

```ini
TMDB_API_KEY=votre_cle_ici
TMDB_LANGUAGE=fr-FR
FFPROBE_PATH=ffprobe   # ou chemin complet si ffprobe n'est pas dans le PATH
FFPLAY_PATH=ffplay     # utilise par le bouton PLAY (ou chemin complet si ffplay n'est pas dans le PATH)
```



```bash
cd backend
python -m venv venv

# LINUX
source venv/bin/activate                 
# Windows 
venv\Scripts\activate

pip install -r requirements.txt

# Copier le fichier d'exemple et renseigner la cle TMDb
cp .env.example .env      # Windows : copy .env.example .env
```


La documentation des API est disponible Swagger sur `http://localhost:8000/docs`.
Les API backend sont accèssibles depuis l'URL: http://localhost:8000

Pour information, l'URL de l'API est définie dans `src/environments/environment.ts`
(`apiUrl: 'http://localhost:8000/api'`). Modifiez-la si votre backend tourne sur une autre machine/port.

---

**Installation du frontend**

```bash
cd frontend

# mode  'developement'
npm install
# ou mode  'build/release'
npm run build
```


## 4. Utilisation

### 4.1 démarrage du Backend
Lancer l'API backend:

```bash
cd backend

# LINUX
source venv/bin/activate                 
# Windows 
venv\Scripts\activate

uvicorn app.main:app --reload --port 8000
```

### 4.2 démarrage Frontend 


```bash
cd frontend

# mode debug (developement)
npm start
# ou mode build
node server.js
```

Puis suivre les étapes ci-dessous:
1. L'application est disponible sur `http://localhost:4200` en mode developement ou `http://localhost:3000` en mode build

2. Dans le panneau de gauche, cliquez sur **"+ Nouvelle bibliotheque"**, donnez-lui
   un nom et indiquez le chemin du dossier racine (ex. `C:\movies` ou
   `/home/user/movie`).
3. Cliquez sur l'icone **⟳** a cote de la bibliotheque pour lancer un scan :
   - détection des dossiers de films,
   - analyse du fichier video via `ffprobe` (codec, résolution, pistes audio),
   - recherche TheMovieDB (titre original, acteurs, affiche),
   - téléchargement de l'affiche dans `backend/data/thumbnails/` (dossier
     commun a toutes les bibliothèques).
4. Basculez entre les bibliotheques via le panneau de gauche.
5. Quatre vues sont disponibles en haut de la page :
   - **Vignettes** : grille d'affiches avec recherche, clic pour voir le detail
     (synopsis, distribution, pistes audio, sous-titres).
   - **Genre** : Explorez tous vos films classés par genre 
   - **Saga** : Liste des collection Saga avec la liste des films disponibles dans la   bibliothèques sous forme de grille
   - **Acteur / filmographie** : filmographie d'un acteur/actrice
   - **Detail technique** : tableau tri­able (nom du film, fichier, encodage,
     resolution, taille, pistes audio) avec recherche.
   - **Info** : page d'information de la bibliothèque (nom, Dossier Racine, Taille disque, Taille disponible gauge d'utilisation)
   - **Comparaison** (bouton **Outils** du panneau de gauche) : compare deux bibliotheques (identique / manquant a droite / manquant a gauche), en comparaison simple (nom du dossier) ou approfondie (nom et taille du fichier video). La comparaison s'appuie sur le dernier scan de chaque bibliotheque.
     

Relancer un scan met a jour les films existants et retire de la base ceux
dont le dossier a ete supprime du disque (les fichiers eux-memes ne sont
jamais modifies ni supprimes par l'application).



## 5. Notes techniques

- La base SQLite est stockée dans `backend/data/db/library.db`.
- Les affiches sont stockées dans `backend/data/thumbnails/` et nommées
  `tmdb_<id>.jpg` : elles sont donc partagées et dédupliquées entre toutes
  les bibliothèques qui referencent le meme film.
- Le scan est synchrone (la requete HTTP attend la fin du scan) : pour de
  très grosses bibliothèques (>500 films), prevoir un temps de reponse
  proportionnel au nombre de films et a la latence de l'API TMDb.
- Si `ffprobe` est introuvable, le film est tout de meme ajoute (dossier +
  nom de fichier + taille) mais sans les details video/audio ; un message
  d'erreur associé est renvoyé dans le résultat du scan.
- Sans cle TMDb configurée, le scan fonctionne normalement mais aucune
  affiche/metadonnée (acteurs, synopsis...) n'est récuperée.



# Fonctionalités (features)
- Les scans de bibliotheques sont lancés en tâche de fond et ne bloquent pas la requete HTTP.
- La progression du scan est poussée au frontend via WebSocket avec une barre de progression et le dossier en cours.
- Le bandeau supérieur affiche le nom de la bibliotheque active en gras et son nombre total de films.
- Scan en arriere-plan (tache asynchrone + barre de progression / websocket)
- Detection/rapprochement manuel quand TMDb ne trouve pas de correspondance
- Correction manuelle des informations TMDb
Depuis la fiche d’un film, le bouton **Modifier les informations** lance une recherche TMDb à partir du titre et de l’année du dossier. Les résultats sont affichés dans une fenêtre modale avec vignette, titre, année, titre original, genres et description. Le résultat sélectionné remplace les métadonnées TMDb du film et son affiche est enregistrée dans `backend/data/thumbnails/`. La base `backend/data/db/library.db` est mise à jour.
L’affiche précédente est supprimée automatiquement si elle n’est plus utilisée par aucun autre film.
- Comparaison simple ou approfondie entre 2 bibliothèques.


# Pistes d'evolution possibles
- Passage en multi-langues / Angular i18n
- Edition manuelle des metadonnees d'un film
- Lecture video directe depuis l'interface (streaming du fichier local)




# Extraire le code source uniquement pour le soumettre à l'IA 
Compresser le projet au format ZIP et exclure tous les fichiers/dossiers inutiles (et régénérés après), ceci permet d'éviter de consommer trop de tokens et d'alourdir inutilement le ZIP.

```bash
# BASH
./compress.sh

# WINDOWS POWERSHELL
./compress.ps1
```

