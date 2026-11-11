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

**v0.9.19**
- Vue « Doublons » (bibliothèques « Films » uniquement) : deux films de même titre mais d'années de sortie différentes ne sont plus considérés comme des doublons (ex. Papillon (1973) et Papillon (2018))
- Un film sans année est rattaché à l'unique année connue du même titre ; s'il existe plusieurs années, il reste dans un groupe à part
- Bibliothèques « Séries TV » : détection inchangée

**v0.9.20**
- Bibliothèques « Séries TV » : nouvelle vue « Détail technique » (composant `movie-detail-tv`) : une section dépliable / repliable par série (vignette + nom + nombre d'épisodes et taille cumulée), boutons « Tout déplier / Tout replier » et recherche « Rechercher une série TV… »
- Chaque section contient un tableau des épisodes (ordre alphabétique par défaut) : N° d'épisode (déduit du nom de fichier), fichier vidéo (tronqué si trop long), encodage, résolution, taille et pistes audio ; toutes les colonnes sont triables sauf « Pistes audio »
- Bibliothèques « Films » : vue « Détail technique » inchangée (la route `/technique` choisit la vue selon le type de la bibliothèque active)

**v0.9.21** - Notes sur les films et séries

- Fiche détaillée : bouton « Note » sous « Voir sur TMDB » ouvrant une boîte de dialogue « Notes » (texte libre multi-lignes, Annuler / Enregistrer) ; sauvegarde en base dans la table `notes`
- En-tête : nouvel onglet « Notes » (icône SVG) à droite de « Doublons »
- Nouvelle vue « Notes » : tableau des films / séries ayant une note (titre, bouton « Fiche », texte multi-lignes)
- Les notes sont incluses dans l’export et l’import de bibliothèque, comme la note personnelle en étoiles. Les anciens exports restent lisibles.

Backend
  - API : `GET /api/notes?library_id=`, `GET|PUT /api/movies/{id}/note` ; les notes sont incluses dans l'export / import de bibliothèque
  - Une nouvelle table notes stocke une note par film ou série. Elle se crée toute seule au démarrage, sans migration à lancer.
  - Enregistrer un texte vide supprime la note, et le film disparaît alors de la vue « Notes ».
  - Supprimer une bibliothèque supprime aussi ses notes.



**v0.9.22** - Modification des propriétés d’une librairie

Interface / Frontend

  - Un bouton avec une icône SVG de crayon se trouve à gauche du bouton « Scanner cette bibliotheque » (⟳), avec le titre « Editer cette bibliotheque ».
  - Le dialogue reprend le style de celui du scan : fond assombri, fermeture au clic extérieur.
  -Il contient le titre Modifier la librairie, le champ Nom, le choix Type (Films ou Séries) et le champ Dossier racine. Les champs sont préremplis avec les valeurs actuelles.
  - Annuler ferme le dialogue sans rien enregistrer. Modifier enregistre, puis la liste se rafraîchit toute seule, ainsi que la page Info.
  Si le nom ou le dossier est vide, ou si le serveur refuse (dossier déjà utilisé), un message d’erreur s’affiche dans le dialogue.

Backend

  - Nouvelle route PUT /api/libraries/{id}.
   Elle renvoie une erreur 409 si le dossier racine est déjà utilisé par une autre bibliothèque, 404 si la bibliothèque n’existe pas, et 400 si le nom ou le dossier est vide.
  Elle relit aussi la taille du disque pour le nouveau dossier racine.

*Avertissement: Changer le type ou le dossier racine ne relance pas de scan et ne modifie pas les films déjà en base. Après un changement de type ou de dossier, il faut donc relancer un scan pour que le contenu corresponde.*



**v0.9.23** - Sidebar Toogle button - Menu Burger

- *Icône du bouton sidebar-toggle*
  Le caractère ☰ est remplacé par une icône SVG « panneau latéral » : un rectangle avec un séparateur vertical.
  Le panneau de gauche est légèrement rempli quand le bandeau latéral est visible, et vide quand il est masqué.
- *navbar menu burger*
  Détection : le menu passe en burger quand les liens ne tiennent plus à l’horizontale, selon la place réellement disponible dans le bandeau (pas un seuil fixe en pixels). Cela prend en compte l’ouverture ou la fermeture de la sidebar, le nom de la bibliothèque active, le passage Films/Séries TV (le lien « Saga » disparaît) et le bouton de thème.
  Menu : un clic sur l’icône burger ouvre un panneau sous le bouton, avec les liens en colonne. L’icône devient une croix quand le menu est ouvert.
  Fermeture : le menu se ferme au clic sur un lien, au clic en dehors, avec la touche Échap, ou quand la largeur redevient suffisante.


**v0.9.24** - Fix clic sur l'icone du menu Burger

Correction die bug du burger : le menu s’ouvre maintenant aussi quand on clique au centre de l’icône.
Cause : en cliquant sur le SVG, le menu s’ouvrait, puis Angular remplaçait immédiatement l’icône burger par la croix. Le gestionnaire de clic « en dehors du menu » recevait alors un élément déjà retiré de la page, ne le trouvait plus dans le conteneur du menu et refermait aussitôt. Cliquer sur la marge du bouton marchait parce que le bouton lui-même n’est pas supprimé.


**v0.9.25** - Journal des modifications d'une bibliothèque

Interface / Frontend

- Nouvel onglet « Journal » (icône horloge) dans le menu, placé juste avant « Info » (route `/journal`, composant `journal-view`).
- Vue « Journal de la bibliothèque » : liste des évènements, du plus récent au plus ancien, avec pour chaque ligne : icône Masquer / Afficher les détails, date et heure, statut, total de fichiers films/séries ajoutés, modifiés et supprimés.
- Statuts : Création, Modification de la bibliothèque (nom, type, dossier racine, avec l'ancienne et la nouvelle valeur) et Scan (avec ses options : « Comparaison simple / approfondie », « Structure simple / mixte » ou profondeur pour les séries).
- Un clic sur l'icône Masquer / Afficher déplie le détail au niveau fichier (chargé à la demande). Pour chaque film / série : bloc de gauche avec la vignette, le titre et l'année ; bloc de droite avec un tableau : Statut, Nom du fichier, Encodage (hevc / h264…), Résolution (1920x800…), Taille (ex. 2.96GB), Pistes audio (langue, encodage, bitrate) et Sous-titres (langue).
- Pour une bibliothèque « Séries TV », les épisodes d'une même série sont regroupés sous la même vignette.
- La vue se recharge toute seule à la fin d'un scan, après une modification de la bibliothèque ou un changement de bibliothèque active.

Backend

- Nouvelles tables `library_logs` (journal bibliothèque) et `library_log_files` (journal fichier : instantané du nom, de la taille, de l'encodage, de la résolution, des pistes audio et des sous-titres au moment de l'évènement). Elles se créent toutes seules au démarrage, sans migration à lancer.
- API : `GET /api/journal?library_id=` (journal bibliothèque) et `GET /api/journal/{id}/files` (détail des fichiers d'un évènement).
- Nouveau module `app/journal.py`.
- Règles de journalisation d'un scan :
  - Fichier **créé** : nouveau fichier vidéo en base (ou fichier signalé supprimé qui réapparaît).
  - Fichier **modifié** : taille, encodage, résolution, pistes audio ou sous-titres différents de ceux déjà en base. Un fichier inchangé n'est pas journalisé, même en comparaison simple (qui ré-analyse pourtant le fichier).
  - Fichier **supprimé** : fichier présent en base mais disparu du disque. Il est signalé une seule fois (l'entrée reste en base, comme avant : un disque réseau débranché ne vide pas la bibliothèque).
  - Un scan impossible (dossier racine introuvable) est tout de même tracé, avec son message.
- Création d'une bibliothèque (y compris par import) et modification de ses propriétés (uniquement si une valeur a réellement changé) sont journalisées. Supprimer une bibliothèque supprime aussi son journal.
- Le scan valide maintenant chaque fichier au fur et à mesure : un fichier en erreur n'annule plus les fichiers déjà traités (ni leur journal).

*Remarque : le journal commence à partir de cette version. Le premier scan d'une bibliothèque déjà peuplée peut signaler quelques fichiers « modifiés » (informations techniques complétées par rapport à d'anciennes versions) ; les suivants ne signalent que les vrais changements.*


**v0.9.26** - Vue « Journal » : bouton Tout masquer / Tout afficher et vignettes

- Bouton « Tout afficher / Tout masquer » en haut de la vue, à gauche du compteur d'évènements, identique à celui de la vue « Doublons » : il déplie (ou replie) le détail de tous les évènements ayant des fichiers. Le libellé est « Tout afficher » tant que tous les détails sont masqués.
- Détail : la vignette du film / de la série s'affiche dès qu'elle existe. Backend : `GET /api/journal/{id}/files` renvoie maintenant l'affiche courante du film (et non plus seulement celle connue au moment du scan), ce qui corrige les vignettes absentes quand l'affiche TMDb arrivait après l'évènement.
- L'icône de remplacement n'apparaît plus que lorsque le film / la série est supprimé (tous ses fichiers du bloc ont le statut « Supprimé ») et qu'il n'y a pas de vignette. Sinon, sans vignette, seuls le titre et l'année sont affichés.


**v0.9.27** - Fenêtre « À propos » (double-clic sur le titre)

- Un double-clic sur le titre `<h1>` « TinyMovieCatalog v0.9.27 » du bandeau de gauche ouvre la fenêtre de dialogue « À propos ».
- Titre de la fenêtre : « À propos ».
- Section en-tête : bloc de gauche avec l'icône `favicon-128x128.png` ; bloc de droite avec « TinyMovieCatalog » en gros titre gras, une ligne de séparation, puis la version (v0.9.27).
- Section principale : description de l'application, liste des fonctionnalités, langages et technologies utilisés (Angular 19 / TypeScript, Python / FastAPI, SQLite, FFmpeg), systèmes d'exploitation supportés (Windows, Linux, macOS), et lien vers le dépôt GitHub `https://github.com/starfix77/TinyMovieCatalog/` qui s'ouvre dans un nouvel onglet du navigateur.
- Bouton « OK » pour fermer la fenêtre (il a le focus à l'ouverture ; la touche Échap ou un clic en dehors de la fenêtre la ferment aussi).
- Fichiers touchés : `components/library-selector/` (html, ts, css) et nouvelle image `frontend/src/assets/favicon-128x128.png` (copiée aussi dans `docs/`).
- Rappel : à chaque nouvelle version, mettre à jour la version dans le `<h1>` du template et la constante `APP_VERSION` de `library-selector.component.ts`.



**v0.9.28** - Mise à jour vers une nouvelle version (script BASH)

Le script bash **update_tinymoviecatalog.sh**  permet de mettre à jour une nouvelle version depuis GitHub et Il suit vos 5 étapes :

1. **Sauvegarde** : une archive .tar.gz horodatée de `backend/data/` et `backend/.env`, créée dans ../TinyMovieCatalog_backups/, plus une copie temporaire pour la restauration.
2. **Git pull** : depuis `https://github.com/starfix77/TinyMovieCatalog.git`, avec --ff-only pour éviter les merges automatiques. S’il n’y a pas encore de dépôt git, il en initialise un.
3. **Décompression** (option --zip) : vous pouvez fournir une archive, par exemple TinyMovieCatalog_0.9.28.zip, au lieu du git pull. Le script gère un dossier racine unique dans le zip et exclut data, .env, .venv et node_modules. Dans les deux modes, backend/data et backend/.env sont ensuite restaurés.
4. **Dépendances** : npm install dans frontend, puis activation de .venv (Linux/macOS bin/ et Windows Git Bash Scripts/) et pip install -r requirements.txt. Le .venv est créé s’il manque.
5. **Redémarrage** : le script exécute la commande définie dans RESTART_CMD, sinon il vous invite à redémarrer manuellement. Les nouvelles tables de la base sont créées automatiquement au démarrage. À la fin, il affiche la version lue dans APP_VERSION de library-selector.component.ts.

```bash
# Exemples d’utilisation :
./update_tinymoviecatalog.sh

./update_tinymoviecatalog.sh --zip TinyMovieCatalog_0.9.28.zip

RESTART_CMD="systemctl restart tinymoviecatalog" ./update_tinymoviecatalog.sh

./update_tinymoviecatalog.sh --no-restart

```



**v0.9.29** - Linux — service systemd et mise à jour automatisée (toutes distributions Linux)

Valable pour toutes les distributions Linux utilisant systemd (Debian, Ubuntu, Linux Mint, Fedora, RHEL, Rocky, AlmaLinux…). 
Cette section est *facultative* : elle permet de lancer TinyMovieCatalog automatiquement au démarrage de la machine, et de le mettre à jour en une seule commande.



**v0.9.30** - Notes au niveau de la bibliothèque

- Vue « Info » : nouveau bouton **« Notes »** (en haut à droite de l'en-tête) qui ouvre la boîte de dialogue **« Notes »** : zone de texte libre multi-lignes, boutons « Annuler » / « Enregistrer ». Enregistrer un texte vide supprime la note.
- Base de données : nouvelle table spécifique **`librairies_notes`** (une note par bibliothèque : `library_id` unique, `content`, `created_at`, `updated_at`). Elle est créée automatiquement au démarrage (pas de migration manuelle) et supprimée avec la bibliothèque.
- API : `GET /api/libraries/{id}/note` et `PUT /api/libraries/{id}/note` (corps `{ "content": "..." }`).
- Export / import de bibliothèque : la note est incluse dans l'export (clé optionnelle `library.note`), comme la note personnelle en étoiles, et restaurée à l'import. Le format reste en version 1 : les **anciens exports** (sans cette clé) restent lisibles et s'importent sans note.
- Tests : `backend/tests/test_library_transfer.py` complété (aller-retour avec note, export sans note, ancien export).
- Fichiers touchés : `backend/app/models.py`, `schemas.py`, `routers/libraries.py`, `library_transfer.py`, `components/library-info/` (html, ts, css), `services/library.service.ts`, `models/library.model.ts`.



**v0.9.31** - Réorganisation de l'ordre des bibliothèques (glisser-déposer)

- Bandeau de gauche (`library-selector.component`) : les bibliothèques peuvent être **réordonnées par glisser-déposer**. Un trait coloré indique la position de dépôt (avant / après la bibliothèque survolée) ; la bibliothèque déplacée est atténuée pendant le glissement. Un changement de bibliothèque active n'est pas déclenché par le glissement.
- L'ordre est **enregistré en base** (nouvelle colonne `libraries.sort_order`) et retrouvé à chaque démarrage. Il est aussi utilisé dans les listes déroulantes des outils (comparaison, export).
- **Suppression** d'une bibliothèque : l'ordre des autres bibliothèques est préservé (les rangs sont renumérotés sans modifier l'ordre relatif).
- **Nouvelle bibliothèque** (création ou import) : placée en **dernière position** de la liste.
- Migration automatique : la colonne est ajoutée au démarrage et initialisée avec l'ordre alphabétique précédemment affiché, de sorte que rien ne change tant que l'utilisateur ne réorganise pas la liste. Le rang n'est pas inclus dans les fichiers d'export (format inchangé, version 1).
- API : `PUT /api/libraries/order` (corps `{ "ids": [3, 1, 2] }`, retourne la liste ordonnée). Les identifiants inconnus sont ignorés et les bibliothèques absentes de la liste sont placées à la fin.
- Le tri alphabétique `ORDER BY name` de `GET /api/libraries` est remplacé par `ORDER BY sort_order, id`.
- Tests : nouveau fichier `backend/tests/test_library_order.py` (nouvelle bibliothèque en dernier, réordonnancement persistant, suppression, identifiants inconnus, migration).
- Fichiers touchés : `backend/app/models.py`, `database.py`, `schemas.py`, `library_order.py` (nouveau), `library_transfer.py`, `routers/libraries.py`, `components/library-selector/` (html, ts, css), `services/library.service.ts`, `models/library.model.ts`.



**v0.9.32** - Fichier de paramétrage de la version, section « Application » et boîte de dialogue « Configuration »

- **Version centralisée (frontend)** : la constante `APP_VERSION` quitte `library-selector.component.ts` et est désormais définie dans le fichier de paramétrage `frontend/src/app/config/app-settings.ts` (avec `APP_NAME` et `APP_REPOSITORY_URL`), importable par tous les composants.
- Vue « Outils des bibliothèques » : nouvelle section **« Application »** avec deux boutons : **« À propos »** (icône SVG « i ») qui affiche la fenêtre « À propos », et **« Paramètres »** (icône SVG engrenage) qui affiche la nouvelle boîte de dialogue **« Configuration »**.
- Boîte de dialogue **« Configuration »** (lecture seule) : tableau de tous les paramètres du fichier `backend/.env` (nom, description, valeur effective, origine : fichier .env / variable d'environnement / valeur par défaut). Les clés inconnues du `.env` sont signalées. **La clé API TMDb (et tout paramètre secret) est masquée** par le backend : seuls les 4 derniers caractères sont affichés. En bas du dialogue : « (ces paramètres sont modifiables dans le fichier /backend/.env et pris en compte après un redémarrage) ».
- Les fenêtres « À propos » et « Configuration » sont des composants indépendants (`about-dialog`, `settings-dialog`) déclarés une seule fois dans `AppComponent` et ouvertes via le service `AppDialogService` ; la fenêtre « À propos » (double-clic sur le titre du bandeau) est inchangée visuellement.
- API : nouveau `GET /api/settings` (`routers/app_settings.py`, `settings_info.py`).
- Script `update_tinymoviecatalog.sh` : la version affichée en fin de mise à jour est lue dans `app-settings.ts` (la lecture dans `library-selector.component.ts` ne fonctionnait plus).
- Tests : nouveau fichier `backend/tests/test_app_settings.py` (liste complète, masquage des secrets, clés inconnues, priorité des variables d'environnement, endpoint).
- **Rappel : à chaque nouvelle version, modifier uniquement la constante `APP_VERSION` de `frontend/src/app/config/app-settings.ts`.**
- Fichiers touchés : `config/app-settings.ts`, `components/about-dialog/`, `components/settings-dialog/`, `components/dialog-shared.css` (nouveaux), `services/app-dialog.service.ts`, `services/settings.service.ts`, `models/settings.model.ts` (nouveaux), `components/library-tools/`, `components/library-selector/`, `app.component.*`, `backend/app/schemas.py`, `main.py`.




**v0.9.33** - Scripts améliorés pour MacOS

- création dossier spécial par système d'exploitation `/scripts'
```
Projet
└── scripts/          scripts par OS install+start
   └── linux/
   └── macos/
   └── windows/

```

- création sous-dossier `/docs/img`



**v0.9.34** - Scan : ignorer les préfixes numériques de classement en début de nom de fichier

- **Parsing du nom de fichier** (`backend/app/filename_parser.py`) : avant toute analyse (titre, année, informations techniques), les séquences d'un ou plusieurs chiffres situées au début du nom et suivies immédiatement d'un séparateur (espace, point ou tiret) sont supprimées avec leur séparateur. Exemples : `01 Prometheus`, `001 - Prometheus`, `01. Prometheus`, `123 - Prometheus` → `Prometheus` ; `Alien 3 (1992)` reste inchangé.
- Un seul préfixe est retiré (`01 - 12 Monkeys` → `12 Monkeys`) ; les nombres du titre ou des informations descriptives sont conservés.
- Garde-fous : le nom est laissé intact si, après suppression, il ne resterait aucune lettre (`1917 (2019)`, `300`), et un point suivi d'un chiffre n'est pas un séparateur (`1.5 Hours`).
- S'applique aux bibliothèques de films (`parse_name`) et de séries TV (`parse_tv_name`) ; le préfixe est retiré une seule fois même pour les séries. Les dossiers au format `Titre (Année)` (reconnus par `FOLDER_PATTERN`) ne sont pas modifiés.
- Nouvelle fonction `strip_order_prefix()` ; `parse_name` s'appuie sur `_parse_stem()` pour éviter un double retrait.

- Scan : séparateur « _ » et protection des titres commençant par un nombre

- **Séparateur souligné** : `01_Prometheus` est désormais reconnu comme préfixe de classement (`backend/app/filename_parser.py`).
- **Règle plus prudente** (correction de la limite de la v0.9.34, qui retirait aussi les nombres faisant partie du titre) : le préfixe n'est retiré que si le séparateur est un **tiret** ou un **point** (`001 - `, `01. `, `12 - `, `01-`), **ou** si le nombre **commence par un zéro** (`01`, `001`) quel que soit le séparateur (espace, point, tiret, souligné).
- Conséquence : `12 Years a Slave (2013)`, `21 Jump Street (2012)`, `28 Days Later (2002)`, `10 Cloverfield Lane`, `2 Alien` et `12_Years_a_Slave_2013` ne sont plus modifiés. Le souligné étant fréquemment utilisé à la place de l'espace dans les noms de release, il compte comme un séparateur « faible » (comme l'espace). Contrepartie : un fichier de saga numéroté sans zéro initial et séparé par un simple espace (`1 Prometheus`, `12 Prometheus`) n'est plus nettoyé ; utiliser `01 Prometheus`, `12 - Prometheus` ou `12. Prometheus`.
- Inchangés : un seul préfixe retiré, nom conservé s'il ne resterait aucune lettre (`1917 (2019)`), point suivi d'un chiffre non considéré comme séparateur (`1.5 Hours`, `10.000 BC`).

