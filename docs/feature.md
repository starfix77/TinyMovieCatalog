# TinyMovieCatalog — Liste des fonctionnalités

> Document généré à partir de l'analyse du code source de **TinyMovieCatalog v0.9.19** (README, `docs/history.md`, backend FastAPI, frontend Angular).
> Les points où le code diffère de la documentation sont signalés dans la section [Écarts constatés](#13-écarts-constatés-entre-documentation-et-code).

---

## 1. Présentation

TinyMovieCatalog est une application web **100 % locale** de gestion de bibliothèques de **films** et de **séries TV** (fichiers vidéo `.mkv`, `.mp4`, `.avi`, `.m4v`, `.dvix`). Elle propose une interface de type médiathèque, centrée sur les affiches.

| Élément | Détail |
|---|---|
| Frontend | Angular 19 (composants standalone), TypeScript |
| Backend | Python, FastAPI, SQLAlchemy |
| Base de données | SQLite locale (`backend/data/db/library.db`) |
| Métadonnées | API TheMovieDB (TMDb), clé API gratuite requise |
| Analyse technique | `ffprobe` (FFmpeg) |
| Lecture vidéo | `ffplay` (FFmpeg) |
| Authentification | Aucune (usage local uniquement) |
| Systèmes | Windows 10/11, Linux, macOS |
| Ports par défaut | Frontend `4200` (dev) ou `3000` (build + Express) ; backend `8000` ; Swagger sur `/docs` |

---

## 2. Gestion des bibliothèques

- **Création** d'une bibliothèque via « + Nouvelle bibliothèque » : nom, dossier racine, et **type** (*Films* ou *Séries TV*).
- **Plusieurs bibliothèques** simultanées, avec bascule en un clic depuis le panneau latéral gauche.
- **Unicité du dossier racine** : une seule bibliothèque par dossier (erreur 409 sinon).
- **Icône de type** (pellicule / téléviseur) dans le panneau latéral et dans l'en-tête.
- **Compteurs** adaptés au type : « film(s) » ou « série(s) ».
- **Suppression** d'une bibliothèque avec confirmation. Seules les entrées de la base sont supprimées ; **les fichiers sur disque ne sont jamais modifiés ni supprimés**.
- **Panneau latéral repliable** (bouton ☰), état mémorisé dans le navigateur.
- **Thème clair / sombre** commutable, choix mémorisé dans le navigateur.
- **En-tête** affichant l'icône, le nom en gras et le nombre total de films/séries de la bibliothèque active.
- **Migration automatique** des bases existantes (la colonne `media_type` est ajoutée ; les anciennes bibliothèques restent en « Films »).

---

## 3. Scan des bibliothèques

### 3.1 Déclenchement et options
- Bouton **⟳** à côté de chaque bibliothèque, ouvrant un dialogue de confirmation.
- **Mode de comparaison** :
  - *Simple* : basé uniquement sur le nom du dossier.
  - *Approfondie* : basé sur le contenu du dossier (les fichiers inchangés sont ignorés lors des scans suivants).
- **Structure** (bibliothèques Films) :
  - *Simple* : un dossier par film, titre et année lus depuis le nom du dossier.
  - *Mixte* : dossiers de films **et** fichiers vidéo placés directement dans les répertoires.
- **Profondeur de parcours** configurable (0 à 20 pour les films ; minimum 2 pour les séries).

### 3.2 Exécution
- Scan **en tâche de fond**, sans bloquer la requête HTTP.
- **Progression en temps réel via WebSocket** : barre de progression, pourcentage, compteur « n / total », dossier en cours.
- Gestion des **erreurs non bloquantes** : elles sont collectées et renvoyées dans le résultat du scan.
- **Lecture seule du disque** : aucune opération de déplacement, de renommage ou de suppression.
- **Liens symboliques ignorés** et protection contre les boucles de répertoires.
- Mise à jour de la date du dernier scan et de l'espace disque de la bibliothèque.
- Récupération automatique des notes TMDb manquantes à la fin de chaque scan.

### 3.3 Détection et regroupement
- Extraction du **titre et de l'année** à partir des noms de dossiers/fichiers (format `Titre (Année)` ou analyse du nom du fichier).
- Normalisation des séparateurs et **exclusion des suffixes techniques** (résolution, codecs, sources, HDR, langues, etc.).
- Signalement des **années ambiguës**.
- **Regroupement des doublons** : les copies d'un même titre/année sont rattachées à une seule fiche, chaque fichier vidéo conservant son chemin complet.
- Un fichier sans année peut rejoindre un film déjà identifié.
- Détection des **sous-titres externes** (`.srt`, `.ass`, `.ssa`, `.sub`, `.vtt`) avec estimation de la langue (français / anglais) d'après le nom du fichier.

### 3.4 Bibliothèques de séries TV
- Un dossier `Titre (Année)` par série (année = première diffusion).
- **Épisodes** = fichiers vidéo du dossier, y compris dans les sous-dossiers de saisons (`Saison 1`, `Season 01`, `S01`…).
- Reconnaissance des marqueurs `S01E02`, `1x02`, `Saison 2` / `Season 2`.
- Fichiers placés à la racine rattachés à leur série par le titre précédant le marqueur d'épisode.
- Une série est une entrée du catalogue ; ses épisodes sont ses fichiers vidéo.

---

## 4. Analyse technique des fichiers (FFprobe)

Pour chaque fichier vidéo, les données proviennent du **contenu réel du fichier** (et non du nom) :

- Conteneur, durée, taille.
- Codec vidéo, résolution (largeur × hauteur), débit vidéo.
- Fréquence d'images, profondeur de couleur, informations HDR.
- Résumé des flux (JSON brut conservé).
- **Pistes audio** : index, langue, titre, codec, nombre de canaux, débit.
- **Statut et message d'erreur FFprobe** conservés pour chaque fichier.
- Si `ffprobe` est introuvable ou échoue, l'entrée est **quand même créée** (dossier, nom de fichier, taille), sans les détails vidéo/audio.

---

## 5. Enrichissement TheMovieDB

- Recherche automatique du film (`/movie`) ou de la série (`/tv`) selon le type de bibliothèque.
- Récupération : titre original, synopsis, date de sortie, genres, **distribution** (12 acteurs maximum par défaut), **note moyenne TMDb**.
- **Téléchargement des affiches** dans `backend/data/thumbnails/` (`tmdb_<id>.jpg`), **partagées et dédupliquées** entre toutes les bibliothèques.
- **Détection automatique des sagas** (collections TMDb) pour les films.
- Langue des métadonnées configurable (`TMDB_LANGUAGE`, `fr-FR` par défaut).
- **Sans clé API** : le scan fonctionne mais sans affiche ni métadonnées.
- Les notes TMDb manquantes sont récupérées en arrière-plan **au démarrage du backend** et après chaque scan.

---

## 6. Vues de consultation

La barre d'onglets supérieure propose les vues suivantes.

### 6.1 Films / Séries TV (grille de vignettes) — `/`
- Grille d'**affiches** avec titre et année.
- **Recherche** par titre (avec temporisation de saisie de 250 ms).
- **Tri** : Titre, Genre, Année, Durée, Taille du fichier, Vote TMDB, Rating (note personnelle).
- Bouton d'inversion du sens du tri (croissant / décroissant).
- Les films sans note TMDb sont toujours placés en fin de liste lors d'un tri par vote.
- Clic sur une vignette : ouverture de la **fiche détaillée**.
- Onglet renommé « **Séries TV** » dans une bibliothèque de séries.

### 6.2 Genre — `/genres`
- Une section par genre présent dans la bibliothèque, au format « Action (48) ».
- Sections triées par **nombre de films décroissant**, puis ordre alphabétique.
- Aperçu d'une ligne de vignettes, dont le nombre **s'adapte à la largeur de l'écran**.
- Lien **« Voir tout » / « Réduire »** par section (déploiement sur place).
- Bouton **« Tout masquer / Tout afficher »**.

### 6.3 Saga — `/sagas` (bibliothèques Films uniquement)
- Bandeau horizontal de sagas avec affiche et compteur « films présents / total ».
- Détail d'une saga : synopsis et grille de **tous les films de la saga**, y compris ceux **absents** de la bibliothèque.
- Indicateur ♥ (présent) / ♡ (absent) ; les films absents sont grisés et non cliquables.
- Onglet masqué dans une bibliothèque de séries (redirection vers l'accueil).

### 6.4 Acteur / Filmographie — `/acteurs`
- **Autocomplétion** du nom d'un acteur (à partir de 2 caractères, 20 suggestions maximum, insensible aux accents et à la casse), classée par nombre de films dans la bibliothèque.
- Filmographie **locale** (hors ligne, sans appel TMDb) par défaut.
- Case **« Voir toute la filmographie »** : interroge TMDb pour afficher toute la carrière de l'acteur (films ou crédits TV selon le type de bibliothèque), avec téléchargement des vignettes manquantes.
- Indication de présence dans la bibliothèque pour chaque titre ; clic pour ouvrir la fiche des titres présents.

### 6.5 Détail technique — `/technique`
- **Tableau triable** : nom du film (année), fichier vidéo, encodage, résolution (triée par nombre de pixels), taille.
- Recherche intégrée.
- Colonne « Fichier vidéo » tronquée avec points de suspension si nécessaire (largeur minimale 200 px), sans barre de défilement horizontale.
- Lien vers la fiche détaillée depuis le tableau.

### 6.6 Doublons — `/doublons`
- **Films** : une section repliable par titre, avec le nombre de fichiers associés ; deux films de même titre mais d'années différentes ne sont **pas** considérés comme doublons (ex. *Papillon* 1973 / 2018). Un film sans année est rattaché à l'unique année connue du même titre.
- **Séries TV** : tableau unique avec une ligne repliable par épisode en double (ex. « 1883 — S01E01 », 3 fichiers) ; seuls les épisodes présents dans 2 fichiers ou plus sont listés.
- Pour chaque fichier : chemin complet, encodage vidéo, résolution, taille, pistes audio (langue, codec, débit).
- Vignette et titre dans le bloc de gauche (films).
- Bouton **« Tout masquer / Tout afficher »**.
- Saison et épisode lus dans le nom du fichier (`S01E01`, `1x01`, `E01`, `Ep01`, `Episode 01`), sinon saison déduite du dossier, sinon saison 1.

### 6.7 Info — `/info`
- Nom, **dossier racine**, type, nombre d'éléments, date de création et de dernier scan.
- **Espace disque** : taille totale, espace disponible, **jauge d'utilisation** (relue à chaque ouverture de la page).

---

## 7. Fiche détaillée d'un film / d'une série

Fenêtre modale accessible depuis la plupart des vues.

**Informations affichées**
- Affiche, titre, année, titre original, genres, synopsis.
- **Note TMDb** (ex. « 8,3 /10 TMDB »), adaptée aux thèmes clair/sombre.
- **Distribution** (survol des acteurs mis en évidence).
- **Fichier vidéo** : conteneur, codec, résolution, taille, durée, etc. (films).
- **Pistes audio** : langue, titre, codec, canaux, débit.
- **Sous-titres** détectés (survol mis en évidence).
- Lien **« Voir sur TMDB »** vers la bonne page (film ou série).

**Notation personnelle**
- Étoiles de **0 à 5 par pas de 0,5**, modifiables directement.
- Un clic sur la note actuelle la remet à 0.
- Utilisable comme critère de tri (« Rating »).

**Lecture**
- Bouton **PLAY** : lance le film avec `ffplay` en **plein écran** sur la machine qui héberge le backend, fermeture automatique en fin de lecture.
- Messages d'erreur explicites si le fichier est indisponible (disque débranché, fichier déplacé) ou si `ffplay` est introuvable ou échoue.

**Séries TV**
- Section **« Épisodes »** (remplace « Fichier vidéo », pistes audio et sous-titres) : résumé « 9 fichiers - 12.24 Go », tableau trié par ordre d'épisode.
- Colonnes : bouton ▶ de lecture de l'épisode, numéro (affiché `S02E05` pour plusieurs saisons), nom du fichier (tronqué, nom complet au survol), durée.

**Correction des métadonnées TMDb**
- **« Modifier les informations »** : recherche TMDb à partir du titre et de l'année du dossier ; résultats avec vignette, titre, année, titre original, genres et synopsis.
- **« Recherche manuelle »** : recherche à partir d'un titre saisi (année facultative) quand le nom ne permet pas l'identification ; le bouton est **mis en évidence** lorsque le film n'est pas identifié.
- Sélection par simple clic, ou **double-clic pour choisir et enregistrer immédiatement**.
- Remplace les métadonnées en base ; l'ancienne affiche est supprimée si plus aucun film ne l'utilise.
- Fonctionne pour les films et les séries.

**Changement de pochette**
- Bouton **« Change pochette »** (grisé si le film n'est pas associé à TMDb).
- Sélection de la **langue** avec suggestions au fil de la saisie (navigation clavier, validation par Entrée) ; langue par défaut issue de `TMDB_LANGUAGE`.
- Grille des pochettes TMDb triées par note décroissante, avec dimensions de l'image.
- Clic pour sélectionner, **double-clic pour remplacer** la vignette ; toutes les vues sont mises à jour.
- L'ancienne vignette n'est supprimée que si aucun autre film ni aucune saga ne l'utilise.

---

## 8. Outils des bibliothèques — `/outils`

Page avec trois gros boutons, accessible depuis le bouton **Outils** (icône de clé) du panneau latéral.

### 8.1 Comparer des bibliothèques — `/outils/comparaison`
- Choix de la **bibliothèque #1**, du **mode** et de la **bibliothèque #2** ; le bouton « Exécuter » n'est actif que si deux bibliothèques différentes sont choisies.
- **Modes** : *Identique* (=), *Manquant à droite* (>), *Manquant à gauche* (<).
- **Profondeur** : *Simple* (nom du dossier, par défaut) ou *Approfondie* (nom et taille du fichier vidéo).
- En approfondie, le statut « identique, fichier vidéo différent » signale les écarts de nom ou de taille.
- Case **« Voir les détails des différences uniquement »**.
- Tableau à trois colonnes (film, statut, film), **trié alphabétiquement** sans tenir compte des accents ni de la casse ; rapprochement des noms insensible à la casse et aux espaces superflus.
- Lien vers la fiche détaillée de chaque film depuis le tableau.
- Le tableau est effacé quand un paramètre change.
- S'appuie sur la **base de données** (dernier scan) : fonctionne même si un disque est débranché, mais exige de rescanner une bibliothèque modifiée.
- L'ancienne URL `/comparaison` redirige vers `/outils/comparaison`.

### 8.2 Exporter une bibliothèque — `/outils/export`
- Choix d'une bibliothèque puis export vers un fichier **`<nom>.tmcatalog.json`**.
- JSON UTF-8 **versionné** (`TinyMovieCatalog.library`, version 1), lisible et portable entre Windows, Linux et macOS.
- Contenu : films, fichiers vidéo, pistes audio, sous-titres, sagas, **notes personnelles**.
- Les vignettes ne sont **pas incluses** (seuls leurs noms de fichier le sont).

### 8.3 Importer une bibliothèque — `/outils/import`
- Sélection d'un fichier d'export, validation du format et résumé du contenu.
- **Gestion des conflits** : si le dossier racine existe déjà, le **nom et le dossier racine peuvent être modifiés** avant l'import (les chemins enregistrés sont recalculés).
- Les **vignettes absentes** sont **retéléchargées en arrière-plan depuis TMDb** (clé API nécessaire), avec progression affichée.
- Protection contre les noms de fichiers de vignettes malveillants (rejet de tout ce qui ressemble à un chemin).
- Le panneau latéral est actualisé et un bouton « Ouvrir la bibliothèque » est proposé.

---

## 9. API REST (backend)

Documentation Swagger sur `http://localhost:8000/docs`.

| Domaine | Endpoints principaux |
|---|---|
| Santé | `GET /api/health` |
| Bibliothèques | `GET/POST /api/libraries`, `DELETE /api/libraries/{id}`, `GET /api/libraries/{id}/info` |
| Scan | `POST /api/libraries/{id}/scan`, `WS /api/libraries/{id}/scan/ws` |
| Comparaison | `GET /api/libraries/compare` |
| Export / import | `GET /api/libraries/{id}/export`, `POST /api/libraries/import`, `GET /api/libraries/import/thumbnails/{job_id}` |
| Films / séries | `GET /api/movies` (recherche + tri), `GET /api/movies/{id}`, `PUT /api/movies/{id}/rating`, `GET /api/movies/{id}/tmdb-search`, `PUT /api/movies/{id}/metadata`, `GET /api/movies/{id}/posters`, `PUT /api/movies/{id}/poster`, `POST /api/movies/{id}/play`, `GET /api/movies/{id}/poster` |
| Sagas | `GET /api/sagas`, `GET /api/sagas/{id}`, `GET /api/sagas/{id}/poster` |
| Acteurs | `GET /api/actors/search`, `GET /api/actors/filmography` |
| TMDb | `GET /api/tmdb/languages` |
| Statique | `/data/thumbnails/*` (vignettes) |

---

## 10. Configuration (`backend/.env`)

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `TMDB_API_KEY` | Clé API TheMovieDB | vide |
| `TMDB_LANGUAGE` | Langue des métadonnées | `fr-FR` |
| `FFPROBE_PATH` | Chemin de `ffprobe` | `ffprobe` |
| `FFPLAY_PATH` | Chemin de `ffplay` (si `FFPROBE_PATH` est un chemin complet, `ffplay` est cherché dans le même dossier) | `ffplay` |

Paramètres internes (`config.py`) : 12 acteurs max par film, extensions vidéo et sous-titres reconnues, profondeur de scan par défaut.

---

## 11. Installation, démarrage et outillage

- Scripts d'installation : `install.sh` (Linux/macOS) et `install.ps1` (Windows).
- Scripts de démarrage : `start.sh` et `start.ps1` (lancement du backend et du frontend).
- **Deux modes frontend** : développement (`npm start`, port 4200) ou build + serveur Express (`server.js`, port 3000).
- Scripts `compress.sh` / `compress.ps1` : génèrent un ZIP du code source allégé (utile pour le soumettre à une IA).
- **Tests unitaires** (`backend/tests/`) : parseur de noms de fichiers et export/import de bibliothèque (`python -m unittest discover -s tests`).
- Documentation : `docs/history.md` (historique des versions), `docs/parsing_ffprobe.md` (exigences de parsing et FFprobe), `docs/build_frontend.md`, `docs/make_favicon.md`.

---

## 12. Garanties et limites

- **Aucune écriture sur les fichiers vidéo** : l'application ne déplace, ne renomme et ne supprime jamais rien sur le disque.
- Usage **local uniquement** : CORS ouvert et aucune authentification.
- La lecture (`PLAY`) s'ouvre sur la machine qui exécute le backend.
- Les pochettes TMDb sont étiquetées par langue seule (`fr`, `en`…), pas par pays : `fr-FR` et `fr-CA` donnent les mêmes résultats ; les pochettes sans texte ne sont pas incluses.
- Un nouveau scan **ne remet pas** l'ancienne pochette d'un film déjà associé à TMDb.
- Les sagas n'existent pas pour les séries TV.
- Les noms de langues du sélecteur de pochettes viennent de `Intl.DisplayNames` du navigateur (repli sur le nom TMDb).
- Le scan d'une grosse série ou d'une grande bibliothèque peut être long (un appel `ffprobe` par fichier, latence TMDb).
- L'interface est en français uniquement (l'internationalisation est une évolution envisagée).

---

## 13. Écarts constatés entre documentation et code

Points relevés lors de l'analyse et à vérifier :

1. **Suppression des entrées disparues** : le README indique que relancer un scan « retire de la base » les films dont le dossier a été supprimé. Dans le code (`scanner.py`), le scan **ne supprime pas** ces entrées : il signale seulement « Fichier vidéo devenu indisponible » et renvoie `movies_removed = 0`. Le chapitre « Scan des bibliothèques » du README décrit ce second comportement, qui est le bon.
2. **Édition manuelle des métadonnées** : le README la liste parmi les « pistes d'évolution », alors que la correction manuelle des informations TMDb (« Modifier les informations », « Recherche manuelle », « Change pochette ») existe bien depuis les versions 0.9.3 à 0.9.11. La note personnelle est également modifiable.
3. **Version de l'API** : le backend annonce la version `1.0.0` dans FastAPI alors que l'application affiche `v0.9.19`.
4. **Commandes d'installation du backend** : dans le README, les commandes d'activation de l'environnement virtuel des blocs « Linux / macOS » et « Windows » sont inversées, et le dossier est nommé `venv` à certains endroits et `.venv` à d'autres.
5. **Images de documentation** : le README référence `docs/schema.png` et `docs/favicon-128x128.png`, absents de l'archive analysée (les scripts de compression excluent `docs/*.png`).
