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