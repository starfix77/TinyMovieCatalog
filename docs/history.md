# Historique

**v0.1** - alpha

**v0.2** - Ajout Collection Sagas

**v0.3** - Informations de la bibliothèque

**v0.3.1** - Informations de la bibliothèque : correction mineure taille espace disque

**v0.3.2** - Informations de la bibliothèque : ajout section utilisation disque

**v0.4** - Ajout filmographie d'un acteur/actrice

**v0.5** - Ajout option scan mise à jour simple vs approfondie basée sur le contenu du dossier

**v0.6** - Ajout filmographie d'un acteur/actrice : option TMDB filmographie complète 

**v0.7** - Détail du film : ajout lien vers le site TheMovieDb

**v0.8** - Ajout de la vue « Genre » est ajoutée juste après « Films » 

- En-tête : le titre « Films par genre » et le sous-titre demandés s'affichent en haut de la page, sur le modèle de votre image.
- Sections : chaque genre présent dans la bibliothèque a sa propre section, avec « Action (48) » aligné à gauche et « Voir tout › » aligné à droite sur la même ligne. Les genres sont triés par nombre de films décroissant, puis par ordre alphabétique.
- Aperçu : chaque section montre d'abord une seule ligne de vignettes, avec le titre du film et l'année en dessous. Le nombre de vignettes visibles s'adapte à la largeur de l'écran.
- « Voir tout » : le clic déploie la section sur place, sans rechargement, et le lien devient « Réduire ». Les autres sections ne bougent pas.
- Fiche film : cliquer sur une vignette ouvre la fiche détaillée existante.
- Thèmes : les couleurs suivent le thème clair ou sombre de l'application, et pas seulement le sombre de votre image.

**v0.8.1** 
- Ajout de la vue « Genre » tri des sections genre
- centrage verticale icone Loupe dans la zeone recherche

**v0.8.2**
Adaptation du tableau dans la vue "Détail technique", 
si le contenu du tableau est plus large que la largeur de la fenêtre
- supprime barre de scroll horizontale 
- reduit la largeur de la 2eme colonne "Fichier vidéo" largeur mini 200px et si le nom du fichier est trop long pour la largeur de colonne 
ajoute le principe  l'ellipsis (ou troncature avec points de suspension).


**v0.9** - Ajout Outils comparaison de bibliothèques
1. Bouton « Outils » : dans le bandeau de gauche, sous « TinyMovieCatalog / Collection de films locales », avec une icône de clé. 
Il ouvre la nouvelle vue comparaison et se met en surbrillance quand la vue est active.
2. Description de vue « Comparaison » :
- Le bloc de choix suit votre description : bibliothèque #1, mode de comparaison (avec icônes =, >, <), bibliothèque #2, bouton Exécuter, puis les deux options radio (simple par défaut).
- Exécuter n'est actif que si les deux bibliothèques sont choisies et différentes.
- Le tableau de résultats a trois colonnes : film, statut, film. Les en-têtes des colonnes 1 et 3 affichent le nom des bibliothèques.
- Le tableau est trié par ordre alphabétique, sans tenir compte des accents ni de la casse.
3. Règles de comparaison :
Le mode « Identique » affiche « identique » ou, en approfondie, « identique, fichier vidéo différent » quand le nom ou la taille du fichier vidéo diffère.
Les modes « Manquant à droite » et « Manquant à gauche » listent uniquement les films absents de l'autre côté, avec « — » dans la colonne vide.
Fichiers touchés : les nouveaux fichiers sont backend/app/compare.py et components/library-compare/. Les autres modifications portent sur schemas.py, routers/libraries.py, le service, le modèle, les routes et le bandeau.
La comparaison lit la base de données, donc le dernier scan de chaque bibliothèque, pas les disques. Cela marche même si un disque est débranché, 
mais il faut rescanner une bibliothèque modifiée avant de la comparer.
Les noms de dossiers sont rapprochés sans tenir compte de la casse ni des espaces en trop, et le tableau affiche le nom réel de chaque côté.
Changer un paramètre efface le tableau affiché, pour ne pas montrer un résultat qui ne correspond plus aux choix.

modification la vue « Comparaison » : le statut est renommé et la case « Voir les détails des différences uniquement » est ajoutée. 

**v0.9.1** - correction petit bug Vue Genre (Voir tout quand pour la section 1 film  par d'affichage "Voir tout")

- .gitignore ajout /frontend/dist/
- modification README.md (2 modes frontend developpement ou build + express)

**v0.9.2** - ajout lien pour obtenir le detail du film dans les vues Comparaison et Détail Technique

 - Dialogue "Detail film" ajout subrillance sur survol acteur et sous-titre

**v0.9.3** - Dialogue "Detail film" : ajout du bouton "Change pochette" (dialogue "Choisir une pochette" : choix de la langue avec suggestions, recherche des pochettes TMDb, double-clic pour remplacer la vignette)

- Cote Frontend 
Dans le dialogue "Détail film"
Bouton : il est sous la pochette, au-dessus de « Voir sur TMDB ». Il est grisé si le film n’est pas associé à TheMovieDB.
Liste des langues : un champ de saisie propose des suggestions au fur et à mesure que tu tapes, avec navigation aux flèches et validation par Entrée. Les entrées sont au format « Anglais (en-US) », « Français (fr-FR) », et la liste vient de TMDb. La langue proposée par défaut est TMDB_LANGUAGE de backend/.env.
Bouton « Recherche » : il récupère les pochettes du film dans la langue choisie, triées par note décroissante.
Affichage : une grille de vignettes avec la taille de chaque image. Un clic sélectionne, un double-clic remplace la vignette du film. Le dialogue se ferme, et la grille, le tableau et les autres vues se mettent à jour.

- Côté serveur
GET /api/tmdb/languages renvoie les langues et la langue par défaut (nouveau fichier routers/tmdb_info.py).
GET /api/movies/{id}/posters?language=fr-FR liste les pochettes du film.
PUT /api/movies/{id}/poster télécharge la pochette choisie et l’enregistre sous tmdb_{id}_{hash}.jpg. L’ancienne vignette est supprimée seulement si aucun autre film ni aucune saga ne l’utilise, et le chemin envoyé est validé.
Le reste du code est dans tmdb.py, schemas.py, routers/movies.py, main.py, ainsi que le service, le modèle et le composant movie-detail côté Angular.

- À savoir
Les pochettes TMDb sont étiquetées par langue seule (fr, en…), pas par pays. Choisir « fr-CA » ou « fr-FR » donne donc les mêmes résultats. Les pochettes sans texte ne sont pas incluses.
Un rescan ne remet pas l’ancienne pochette, car il ne retouche pas un film déjà associé à TMDb.
Les noms de langues viennent de Intl.DisplayNames (navigateur), avec repli sur le nom TMDb si le navigateur ne le gère pas.


**v0.9.4** - Dialogue "Detail film" : ajout du bouton "PLAY" (lecture du film avec ffplay, message d'erreur si le fichier est indisponible), variable `FFPLAY_PATH` dans .env

Le bouton « ▶ PLAY » est ajouté dans « Détail film », juste au-dessus de « Change pochette ». Il lance le film avec ffplay dans sa propre fenêtre. 

Film indisponible : si le fichier vidéo est introuvable (disque débranché, fichier déplacé ou supprimé), un message rouge s’affiche sous le bouton : « Film non disponible : le fichier vidéo est introuvable… ». Un message demande d’installer FFmpeg ou de renseigner FFPLAY_PATH dans backend/.env.
Si ffplay se ferme tout de suite : le bouton affiche une erreur au lieu de ne rien faire.
Lancement : la fenêtre s’ouvre sur la machine qui fait tourner le backend, ce qui convient pour ton usage local. Elle porte le titre du film et se ferme à la fin de la lecture. Le bouton passe à « Lancement… » le temps du démarrage.
Configuration : *FFPLAY_PATH* est une nouvelle variable de backend/.env.example, par défaut ffplay. Si FFPROBE_PATH est un chemin complet, ffplay est cherché dans le même dossier (par exemple C:\ffmpeg\bin\), donc rien à changer dans ce cas. 


**v0.9.5** Structure dossier simple + mixte + gestion des doublons en base
Modifications apportées
- Deux modes de bibliothèque : structure simple (un dossier par film) et structure mixte (dossiers et fichiers vidéo directement dans les répertoires).
- Parseur indépendant : extraction du titre et de l’année, normalisation des séparateurs et exclusion des suffixes techniques reconnus.
- Analyse FFprobe : récupération des caractéristiques techniques depuis le contenu réel du fichier, indépendamment de son nom.
- Gestion des doublons : regroupement des copies d'un même film dans une fiche commune, avec conservation des différents fichiers vidéo et de leurs chemins.
- Sous-titres externes : association par nom de base et prise en compte des variantes linguistiques.
- Analyse plus robuste : gestion des erreurs FFprobe, conservation des entrées existantes, profondeur de parcours configurable et exclusion des liens symboliques.


**v0.9.6** - Modifications apportées
- Navigation : ajout de l’onglet « Doublons » et de la route /doublons.
- Regroupement des films : création d’une section par titre de film, affichant le nombre de fichiers associés.
- Sections repliables : bouton pour développer ou réduire chaque section.
- Vignette : affiche du film et titre dans le bloc de gauche.
- Tableau technique : affichage des informations suivantes pour chaque fichier :
  - Fichier : chemin complet.
  - Encodage vidéo.
  - Résolution, par exemple 1920x802.
  - Taille, par exemple 3.49 GB.
  - Pistes audio sur plusieurs lignes, avec langue, encodage et débit.

**v0.9.7**
- Détail du film : ajout de la note TMDB (`vote_average`, affichée « 8,3 /10 TMDB » au-dessus de « Distribution », adaptée aux thèmes clair/sombre)
- Détail du film : ajout de la note personnelle (`rating_perso`, 0 à 5 par pas de 0,5, étoiles jaunes modifiables sous « Voir sur TMDB »). Un clic sur la note actuelle la remet à 0.
- Page « Films » : nouveaux tris « Vote TMDB » et « Rating »
- Les notes TMDB des films déjà présents en base sont récupérées automatiquement au démarrage du backend et à la fin de chaque scan.

**v0.9.8**
- Bibliothèques : choix du type **Films** ou **Séries TV** à la création (colonne `libraries.media_type`, ajoutée automatiquement aux bases existantes, qui restent en « Films »)
- Séries TV : même principe de parsing que les films (dossier « Titre (Année) » par série, épisodes dans les sous-dossiers de saisons, fichiers à la racine rattachés par le titre avant S01E02 / 1x02 / Saison 2), données TMDB via l'API `/tv`
- Icône Film / TV pour chaque bibliothèque dans le bandeau de gauche, et à gauche du nom de la bibliothèque dans l'en-tête
- Fiche détail : lien « Voir sur TMDB » vers la bonne page (film ou série) et nombre d'épisodes

Les bibliothèques ont maintenant un type Films ou Séries TV, choisi à la création, avec une icône dans le bandeau de gauche et dans l’en-tête. J’ai testé le scan sur des arborescences de films et de séries, et vérifié le rendu en thèmes clair et sombre dans un navigateur headless. Je n’ai pas testé les appels TMDB réels (pas de clé API ici) ni ffprobe.

*Création et icônes*

Le formulaire « + Nouvelle bibliothèque » propose un choix Films / Séries TV.
Chaque bibliothèque du bandeau de gauche affiche une icône de pellicule ou de téléviseur à gauche de son nom.
L’en-tête affiche la même icône à gauche du nom de la bibliothèque active. Les icônes suivent la couleur du thème.
Les compteurs indiquent « série(s) » au lieu de « film(s) » pour une bibliothèque de séries.
Les bases existantes migrent automatiquement : toutes les bibliothèques actuelles restent en « Films ».

*Parsing des séries*

Le principe est le même que pour les films : un dossier Titre (Année) par série, l’année étant celle de la première diffusion.
Les épisodes sont les fichiers vidéo du dossier, y compris dans des sous-dossiers de saisons. Les sous-titres sont repérés à côté de chaque épisode.
Un fichier posé à la racine, comme Lost.S01E01.mkv, est rattaché à sa série : le titre s’arrête avant S01E02, 1x02 ou Saison 2.
Une série est enregistrée comme une entrée du catalogue, avec ses épisodes comme fichiers vidéo.
La profondeur de parcours est d’au moins 2 niveaux pour les séries. La fenêtre de scan propose cette profondeur à la place des options « structure simple/mixte ».
Toutes les données TMDB d’une série (recherche, affiche, genres, distribution, note, changement de pochette) viennent des endpoints /tv. Le lien « Voir sur TMDB » pointe vers la bonne page, et la fiche indique le nombre d’épisodes avec leur taille cumulée.
La filmographie complète d’un acteur utilise aussi les crédits TV dans une bibliothèque de séries. Sans cela, des identifiants de séries auraient pu être confondus avec des identifiants de films.

*Points à connaître*

ffprobe analyse chaque épisode, ce qui peut être long sur une grosse série. Le mode « comparaison approfondie » saute les fichiers inchangés lors des scans suivants.
Les onglets de la barre du haut gardent leurs libellés actuels (« Films », « Saga »…). Les sagas n’existent pas pour les séries, donc cet onglet sera vide.

**v0.9.9**
- Bibliothèque de type Séries TV : onglet « Films » renommé « Séries TV », onglet « Saga » masqué (redirection vers l'accueil si on s'y trouve), titre de la page de la grille et texte de la vue Genre adaptés

**v0.9.10**
- Fiche détail : bouton « Recherche manuelle » (mis en évidence quand le film n'est pas identifié) pour chercher sur TMDB à partir d'un titre saisi (année facultative) quand le nom du dossier/fichier ne permet pas l'identification. Résultats en vignettes + synopsis, comme « Choisir le bon film » ; le choix remplace les informations et est enregistré en base. Fonctionne pour les films et les séries TV.
- API : `GET /api/movies/{id}/tmdb-search` accepte `query` et `year` (recherche manuelle)

**v0.9.11**
- « Recherche manuelle » et « Modifier les informations » : un double-clic sur un film/une série proposé(e) le sélectionne, enregistre les informations en base SQLite et ferme la boîte de dialogue

**v0.9.12**
- Bouton « Outils » : ouvre la vue « Outil des bibliothèques » (3 gros boutons : Comparer, Exporter, Importer). La comparaison est désormais accessible via `/outils/comparaison` (l'ancienne URL `/comparaison` redirige)
- Vue « Exporter une bibliothèque » : export complet d'une bibliothèque dans un fichier `.tmcatalog.json` (JSON versionné)
- Vue « Importer une bibliothèque » : import d'un fichier d'export dans la base SQLite, téléchargement en arrière-plan des vignettes absentes de `data/thumbnails` (avec progression) et actualisation du bandeau de gauche
- API : `GET /api/libraries/{id}/export`, `POST /api/libraries/import`, `GET /api/libraries/import/thumbnails/{job_id}`

**v0.9.13**
- Fix minor favicon multi-resolution
- Lance ffplay 'Play' en fullscreen

**v0.9.14**
- Fix minor search icon modify to SVG icon
- ignore frontend.log et backend.log, docs/*.png scripts 'compress'

**v0.9.15**
- Ajouté le bouton « Tout masquer / Tout afficher » dans la vue Doublons, sur le même modèle que la vue Genre

**v0.9.16**
- Pour les bibliothèques « Séries TV », la vue movie-detail change ainsi :
Section « Fichier vidéo » : elle est remplacée par une section « Épisodes », placée sous « Distribution ». Les pistes audio et sous-titres de cette section disparaissent avec elle pour les séries.
Résumé : il s’affiche au format de votre exemple, 9 fichiers - 12.24Go.
Tableau : il est trié par ordre d’épisode.
Colonne 1 : un petit bouton ▶ qui lance l’épisode avec ffplay.
Colonne 2 : le numéro d’épisode.
Colonne 3 : le nom du fichier, tronqué avec « … » s’il est trop long, le nom complet apparaissant au survol.
Colonne 4 : la durée, par exemple 1 h 12 min ou 49 min.

- Pour les bibliothèques « Films », la vue reste identique.

- API : `POST /api/movies/{id}/play` accepte le paramètre facultatif `video_id` (lecture d'un fichier précis)

- Quelques précisions choix par défaut :
Numéro d’épisode : il est lu dans le nom du fichier (S01E02, 1x02, E02, Episode 02). Sans motif reconnu, le fichier passe après les autres, classé par nom, et son numéro est sa position dans la liste. Quand la série compte plusieurs saisons, le numéro s’affiche sous la forme S02E05.

**v0.9.17**
- Vue « Doublons » pour les bibliothèques « Séries TV » : la liste devient un tableau unique (mêmes colonnes : Fichier, Encodage, Résolution, Taille, Pistes Audios), avec une ligne repliable par épisode en double (ex. « 1883 — S01E01 », 3 fichiers)
- Détection des doublons d'épisodes : seuls les épisodes présents dans 2 fichiers ou plus sont listés, tous leurs fichiers sont affichés
- Saison/épisode lus dans le nom du fichier (S01E01, 1x01, E01, Ep01, Episode 01) ; si la saison est absente du nom, elle est déduite du dossier (« Saison 1 », « Season 01 », « S01 »), sinon saison 1. Les fichiers sans numéro d'épisode sont ignorés
- Bibliothèques « Films » : affichage et détection des doublons inchangés

**v0.9.18**
- movie-detail : les boutons « Play » (film et épisodes) utilisent une icône SVG « play » centrée verticalement (et horizontalement) à la place du caractère ▶
