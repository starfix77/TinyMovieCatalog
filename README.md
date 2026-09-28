# TinyMovieCatalog — Gestionnaire de bibliotheques films MKV/MP4

Application locale de gestion de bibliotheques de films (MKV/MP4) :
- **Frontend** : Angular 19 (standalone components)
- **Backend** : Python (FastAPI) — scan des dossiers, analyse video via FFmpeg/ffprobe, enrichissement TheMovieDB, base SQLite locale
- **Usage 100% local**, aucune authentification

```
mkv-library/
├── backend/          API Python (FastAPI)
│   ├── app/
│   ├── data/          <- base SQLite + vignettes (partage entre bibliotheques)
│   ├── requirements.txt
│   └── .env.example
└── frontend/         Application Angular
    └── src/
```

## Structure de bibliotheque attendue

```
C:\MesFilms                              (ou /home/user/MesFilms sous Linux)
├── Inception (2010)\
│   ├── Inception.mkv
│   └── Inception.fr.srt        (optionnel)
├── Interstellar (2014)\
│   └── Interstellar.mkv
└── ...
```

Chaque film doit etre dans un dossier nomme `Titre du film (Annee)`, contenant
obligatoirement un fichier video (`.mkv`, `.mp4`, `.avi`, `.m4v`) et, en
option, un ou plusieurs fichiers de sous-titres (`.srt`, `.ass`, `.ssa`,
`.sub`, `.vtt`).

---

## 1. Prerequis

| Outil | Windows | Linux |
|---|---|---|
| Python 3.10+ | https://www.python.org/downloads/ | `sudo apt install python3 python3-pip python3-venv` |
| Node.js 18+ / npm | https://nodejs.org/ | `sudo apt install nodejs npm` (ou nvm) |
| FFmpeg (fournit `ffprobe`) | https://www.gyan.dev/ffmpeg/builds/ (ajouter `bin\` au PATH) | `sudo apt install ffmpeg` |
| Angular CLI | `npm install -g @angular/cli` | `npm install -g @angular/cli` |

Vous aurez egalement besoin d'une **cle API TheMovieDB** (gratuite) :
https://www.themoviedb.org/settings/api

---

## 2. Installation du backend

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

Editez `backend/.env` :

```ini
TMDB_API_KEY=votre_cle_ici
TMDB_LANGUAGE=fr-FR
FFPROBE_PATH=ffprobe   # ou chemin complet si ffprobe n'est pas dans le PATH
```

Lancer l'API :

```bash
uvicorn app.main:app --reload --port 8000
```

La documentation des API est disponible Swagger sur `http://localhost:8000/docs`.
Les API backend sont accèssibles depuis l'URL: http://localhost:8000

## 3. Installation du frontend

```bash
cd frontend
npm install
npm start
```

L'application est disponible sur `http://localhost:4200`.

> L'URL de l'API est definie dans `src/environments/environment.ts`
> (`apiUrl: 'http://localhost:8000/api'`). Modifiez-la si votre backend tourne sur une autre machine/port.
---

## 4. Utilisation

1. Ouvrez `http://localhost:4200`.
2. Dans le panneau de gauche, cliquez sur **"+ Nouvelle bibliotheque"**, donnez-lui
   un nom et indiquez le chemin du dossier racine (ex. `C:\movies` ou
   `/home/user/movie`).
3. Cliquez sur l'icone **⟳** a cote de la bibliotheque pour lancer un scan :
   - detection des dossiers de films,
   - analyse du fichier video via `ffprobe` (codec, resolution, pistes audio),
   - recherche TheMovieDB (titre original, acteurs, affiche),
   - telechargement de l'affiche dans `backend/data/thumbnails/` (dossier
     commun a toutes les bibliotheques).
4. Basculez entre les bibliotheques via le panneau de gauche.
5. Quatre vues sont disponibles en haut de la page :
   - **Vignettes** : grille d'affiches avec recherche, clic pour voir le detail
     (synopsis, distribution, pistes audio, sous-titres).
   - **Saga** : Liste des collection Saga avec la liste des films disponibles dans la   bibliothèques sous forme de grille
   - **Detail technique** : tableau tri­able (nom du film, fichier, encodage,
     resolution, taille, pistes audio) avec recherche.
   - **Info** : page d'information de la bibliothèque (nom, Dossier Racine, Taille disque, Taille disponible gauge d'utilisation)
   - **Comparaison** (bouton **Outils** du panneau de gauche) : compare deux bibliotheques (identique / manquant a droite / manquant a gauche), en comparaison simple (nom du dossier) ou approfondie (nom et taille du fichier video). La comparaison s'appuie sur le dernier scan de chaque bibliotheque.
     

Relancer un scan met a jour les films existants et retire de la base ceux
dont le dossier a ete supprime du disque (les fichiers eux-memes ne sont
jamais modifies ni supprimes par l'application).

---

## 5. Notes techniques

- La base SQLite est stockee dans `backend/data/db/library.db`.
- Les affiches sont stockees dans `backend/data/thumbnails/` et nommees
  `tmdb_<id>.jpg` : elles sont donc partagees et dedupliquees entre toutes
  les bibliotheques qui referencent le meme film.
- Le scan est synchrone (la requete HTTP attend la fin du scan) : pour de
  tres grosses bibliotheques (>500 films), prevoir un temps de reponse
  proportionnel au nombre de films et a la latence de l'API TMDb.
- Si `ffprobe` est introuvable, le film est tout de meme ajoute (dossier +
  nom de fichier + taille) mais sans les details video/audio ; un message
  d'erreur associe est renvoye dans le resultat du scan.
- Sans cle TMDb configuree, le scan fonctionne normalement mais aucune
  affiche/metadonnee (acteurs, synopsis...) n'est recuperee.



# Fonctionalités (features)
- Les scans de bibliotheques sont maintenant lances en tache de fond et ne bloquent plus la requete HTTP.
- La progression du scan est poussee au frontend via WebSocket avec une barre de progression et le dossier en cours.
- Le bandeau superieur affiche le nom de la bibliotheque active en gras et son nombre total de films.
- Scan en arriere-plan (tache asynchrone + barre de progression / websocket)
- Detection/rapprochement manuel quand TMDb ne trouve pas de correspondance
- Correction manuelle des informations TMDb
Depuis la fiche d’un film, le bouton **Modifier les informations** lance une recherche TMDb à partir du titre et de l’année du dossier. Les résultats sont affichés dans une fenêtre modale avec vignette, titre, année, titre original, genres et description. Le résultat sélectionné remplace les métadonnées TMDb du film et son affiche est enregistrée dans `backend/data/thumbnails/`. La base `backend/data/db/library.db` est mise à jour.
L’affiche précédente est supprimée automatiquement si elle n’est plus utilisée par aucun autre film.



# Pistes d'evolution possibles
- Edition manuelle des metadonnees d'un film
- Lecture video directe depuis l'interface (streaming du fichier local)




# Préparation projet TinyMovieCatalog.zip pour le soumettre à l'IA (Claude Code / Codex ...)
Compresser le projet au format ZIP et exclure tous les fichiers/dossiers inutiles (et régénérés après), ceci permet d'éviter de consommer trop de tokens et d'alourdir inutilement le ZIP

```bash
# BASH
./compress.sh

# WINDOWS POWERSHELL
./compress.ps1
```

