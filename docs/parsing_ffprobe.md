# Organisation attendue des dossiers / fichiers de la bibliothèque

## 1. Principe général
L'application doit séparer le traitement des noms de fichiers de l'analyse technique des fichiers vidéo.

Deux composants indépendants doivent être utilisés :
- **Parseur de noms de fichiers ou dossiers** : extrait exclusivement le titre du film et son année de sortie à partir du nom du fichier ou du dossiers et, si nécessaire, du nom du dossier parent.
- **Analyseur technique FFprobe** : analyse le contenu réel du fichier vidéo pour identifier ses caractéristiques techniques et ses flux multimédias.


## 2. Exigences — Structure des dossiers de la bibliothèque de films
L'application doit prendre en charge deux modes d'organisation de la bibliothèque : structure simple et structure mixte. Le mode sélectionné détermine comment les films sont détectés et comment leurs titres et années sont extraits.



### 2.1. Structure simple — Un dossier par film

**EX-STR-001 — Organisation des dossiers**

Chaque film doit être stocké dans un dossier distinct, nommé selon la convention : `Titre du film (Année)`

Exemple :

```text
C:\MesFilms\
├── Inception (2010)\
│   ├── Inception.mkv
│   └── Inception.fr.srt
├── Interstellar (2014)\
│   └── Interstellar.mkv
└── Le Pacte (2023)\
    └── Le Pacte.mp4
```

**EX-STR-002 — Contenu d'un dossier de film**

Chaque dossier de film doit contenir au moins un fichier vidéo reconnu parmi les extensions suivantes :
- `.mkv`
- `.mp4`
- `.avi`
- `.m4v`
- `.dvix`

Les fichiers de sous-titres externes sont facultatifs. Les extensions prises en charge sont :
- `.srt`
- `.ass`
- `.ssa`
- `.sub`
- `.vtt`

Un dossier peut contenir plusieurs fichiers de sous-titres associés au même film.

**EX-STR-003 — Identification du film**

Le nom du dossier constitue la source prioritaire pour identifier le titre et l'année du film dans ce mode.
Si le nom du dossier contient une année valide, celle-ci doit être extraite et enregistrée.
Si l'année est absente ou ambiguë, elle doit rester inconnue ou être signalée pour vérification.

**EX-STR-004 — Plusieurs fichiers vidéo**

Si un dossier contient plusieurs fichiers vidéo, l'application doit signaler une anomalie de structure dans le mode simple, sauf si une configuration autorise explicitement plusieurs versions du même film.
Aucun fichier ne doit être supprimé, déplacé ou renommé automatiquement.

### 2.2. Structure mixte — Dossiers de films et fichiers vidéo dans le répertoire courant

**EX-STR-005 — Organisation mixte**

L'application doit également accepter une bibliothèque contenant simultanément :
- Des sous-dossiers dédiés à un film.
- Un ou plusieurs fichiers vidéo directement dans le répertoire courant.
- Des sous-titres externes associés aux fichiers vidéo.
- Des répertoires annexes qui ne contiennent aucun film.

Exemple :

```text
C:\MesFilms\
├── Inception (2010)\
│   ├── Inception.mkv
│   └── Inception.fr.srt
├── The.Dark.Knight.2008.1080p.BluRay.x265.mkv
├── Interstellar.2014.2160p.WEB-DL.mkv
├── Avatar.2009.2160p.Multi_RGABR_.mkv
├── Le_Pacte_2023.mp4
└── Sous-titres\
    └── ...
```

**EX-STR-006 — Détection des fichiers vidéo**

Dans le mode mixte, chaque fichier vidéo présent directement dans un répertoire constitue une entrée candidate du catalogue.
Le titre et l'année doivent être extraits du nom du fichier, selon les règles de parsing définies dans les exigences du moteur de parsing.
Pour un film stocké dans un sous-dossier, le nom du dossier doit être utilisé comme source prioritaire, avec le nom du fichier comme source secondaire.

**EX-STR-007 — Séparation entre parsing et analyse technique**

Le parsing du nom de fichier doit servir uniquement à déterminer le titre et l'année de sortie.
Les informations techniques, notamment le codec vidéo, la résolution, les pistes audio, les canaux audio, les langues déclarées et la durée, doivent être obtenues exclusivement par analyse du contenu réel avec FFprobe.
Les métadonnées techniques présentes dans les noms de fichiers ne doivent pas être enregistrées comme des caractéristiques techniques réelles du film.

**EX-STR-008 — Association des sous-titres**

L'application doit rechercher les fichiers de sous-titres externes et les associer au film correspondant, en privilégiant :
1. Une correspondance du nom de base avec le fichier vidéo.
2. Une correspondance avec le titre et l'année du dossier parent.
3. Une association manuelle en cas d'ambiguïté.

Les sous-titres non associés doivent être signalés, sans suppression automatique.

### 2.3. Règles communes aux deux modes

**EX-STR-009 — Répertoires accessibles**

La bibliothique doit permettre de sélectionner un  répertoire racine, sur un disque local ou un emplacement réseau accessible.

**EX-STR-010 — Parcours récursif**

L'application doit pouvoir parcourir les sous-dossiers selon une profondeur configurable et éviter les boucles de parcours dues aux liens symboliques ou aux jonctions de répertoires.

**EX-STR-011 — Gestion des anomalies**

L'application doit signaler :
- Les dossiers sans fichier vidéo.
- Les dossiers contenant plusieurs vidéos en mode simple.
- Les fichiers vidéo non accessibles ou illisibles.
- Les années manquantes ou ambiguës.
- Les sous-titres non associés.
- Les doublons possibles.
- Les conflits entre le titre ou l'année du dossier et ceux extraits du fichier.

**EX-STR-012 — Lecture seule par défaut**

L'analyse de la bibliothèque doit fonctionner en lecture seule. Toute opération de renommage, de déplacement ou de suppression doit faire l'objet d'une action explicite de l'utilisateur.

**EX-STR-013 — Idempotence du scan**

Une nouvelle analyse d'un même répertoire ne doit pas créer de doublons dans le catalogue. Les fichiers ajoutés, modifiés, déplacés ou devenus indisponibles doivent être détectés et traités sans perte des corrections manuelles déjà enregistrées.

**EX-STR-014 — Doublons**
Un film peut etre en doublons plusieurs fois
par exemple
```
C:\MesFilms\
├── Inception (2010)\
│   ├── Inception.mkv
│   └── Inception.fr.srt
├── Inception.2010.2160p.WEB-DL.mkv
└── Inception.mp4
```

la bibliothèque gére l'ensemble des films uniques et aussi l'ensemble des films en doublons
Les informations concernant le nom de fichier est sauvegardées en 2 parties
- le chemin complet du dossier
- le nom du fichier avec son extension


### 2.4. Exigences fonctionnelles — Parsing des noms de fichiers et analyse FFprobe

Le parseur ne doit pas tenter d'extraire, de normaliser ou de stocker les métadonnées techniques à partir du nom du fichier.

#### 2.4.1. Exigences du parseur de noms de fichiers

**EX-PAR-001 — Extraction du titre**

Le parseur doit extraire le titre du film en supprimant l'extension du fichier et les éléments clairement identifiés comme des séparateurs ou des métadonnées techniques de diffusion.

Les séparateurs suivants doivent être normalisés en espaces :
- Point .
- Tiret bas _
- Tiret 
- Espaces multiples

Les mots du titre doivent être conservés dans leur ordre d'origine.
Les accents, apostrophes, caractères Unicode et nombres faisant partie du titre doivent être préservés.

**EX-PAR-002 — Extraction de l'année**

Le parseur doit rechercher une année de sortie plausible, exprimée sur quatre chiffres, dans le nom du fichier.
Les formats suivants doivent être pris en charge :

`Inception.2010.mkv
Inception (2010).mkv
The.Dark.Knight.2008.1080p.BluRay.x265.mkv
Le_Pacte_2023.2160p.WEB-DL.mkv`

Si aucune année fiable n'est détectée, le champ année doit rester vide.
Le parseur ne doit jamais inventer une année.
Si plusieurs années sont possibles, le moteur doit appliquer une règle de priorité documentée ou signaler une ambiguïté.

**EX-PAR-003 — Ignorer les métadonnées techniques**

Le parseur ne doit pas analyser les informations techniques présentes dans le nom du fichier, notamment :
- Les codecs vidéo : H.264, H.265, HEVC, AV1, x264, x265.
- Les résolutions : 720p, 1080p, 1440p, 2160p, 4K.
- Les codecs audio : AC3, EAC3, DTS, DTS-HD, TrueHD, AAC, FLAC.
- Les configurations audio : 2.0, 5.1, 7.1.
- Les formats audio immersifs : Atmos.
- Les indications de profondeur de couleur : 8-bit, 10-bit.
- Les formats HDR : HDR, HDR10, HDR10+, Dolby Vision.
- Les sources : BluRay, BDRip, WEB-DL, WEBRip, HDTV.
- Les indications de langue ou de version : FR, EN, MULTI, - VFF, VFQ.
- Les informations de diffusion : PROPER, REPACK et noms de - groupes de diffusion.
- Ces éléments ne doivent produire aucune valeur dans les - champs techniques du catalogue.
- Le parseur peut uniquement les reconnaître comme des éléments à exclure du titre lorsqu'ils correspondent à des motifs connus et suffisamment fiables.

**EX-PAR-004 — Traitement des éléments inconnus**

Le parseur ne doit pas supprimer arbitrairement les mots inconnus.
Lorsqu'un élément ne peut pas être identifié avec suffisamment de certitude comme un élément technique ou un suffixe de diffusion, il doit être conservé dans le titre candidat ou signalé pour correction manuelle.
Les nombres et les mots appartenant réellement au titre doivent être préservés.

**EX-PAR-005 — Séparation des responsabilités**

Le parseur ne doit pas :
- Déterminer le codec vidéo réel.
- Déterminer la résolution réelle.
- Déterminer les codecs audio.
- Compter ou décrire les pistes audio.
- Déterminer les langues réellement présentes dans les flux.
- Déterminer la durée ou la fréquence d'images.

Déduire les caractéristiques réelles du fichier à partir de son nom.
Ces informations relèvent exclusivement de l'analyse FFprobe.




## 3. Exigences analyseur FFprobe

**EX-FFP-001 — Analyse du contenu réel**

L'application doit utiliser FFprobe pour analyser chaque fichier vidéo reconnu et récupérer les informations techniques à partir de son contenu réel.

Les informations doivent être obtenues à partir des flux et des métadonnées internes du fichier, et non à partir du nom de fichier.

**EX-FFP-002 — Informations à récupérer**

Selon les données disponibles dans le fichier, FFprobe doit permettre de récupérer :
Le format du conteneur.
Le codec vidéo.
La largeur et la hauteur de l'image.
La fréquence d'images.
La profondeur de couleur, lorsqu'elle est disponible.
Les informations HDR, lorsqu'elles sont disponibles.
Les codecs audio.
Le nombre de canaux audio et leur disposition.
Les langues déclarées des pistes audio.
Les langues déclarées des pistes de sous-titres intégrées.
Les types et le nombre de flux.
La durée du fichier.
La taille du fichier, complétée si nécessaire par les informations du système de fichiers.
Les métadonnées internes pertinentes.

L'application doit distinguer une information absente d'une valeur égale à zéro ou d'une erreur d'analyse.

**EX-FFP-003 — Fiabilité des données**

Les informations techniques extraites par FFprobe doivent être associées au fichier vidéo analysé.

Si FFprobe ne parvient pas à analyser un fichier, l'application doit conserver les informations de catalogue déjà disponibles, signaler l'erreur et permettre une nouvelle tentative.

L'échec de FFprobe ne doit pas empêcher l'extraction du titre et de l'année.

**EX-FFP-004 — Langues et pistes**

Les langues doivent être récupérées à partir des métadonnées des flux lorsqu'elles sont présentes.

Si aucune langue n'est déclarée, l'application doit enregistrer une valeur inconnue plutôt que de déduire la langue à partir du nom du fichier.

Les pistes audio et les pistes de sous-titres intégrées au conteneur doivent être distinguées des fichiers de sous-titres externes.

**EX-FFP-005 — Exécution et erreurs**

L'application doit :
- Vérifier la disponibilité de FFprobe.
- Gérer les erreurs d'exécution et les délais d'attente.
- Capturer et interpréter les résultats structurés, de préférence au format JSON.
- Éviter de bloquer l'analyse globale lorsqu'un fichier est illisible.
- Enregistrer le statut de l'analyse et la date de dernière vérification.

## 4. Exemple de traitement attendu

Fichier analysé :

`The.Dark.Knight.2008.1080p.BluRay.x265.DTS.5.1.mkv`

Résultat du parsing du nom

`Titre : The Dark Knight`

`Année : 2008`

Le parseur ignore les éléments techniques et ne remplit aucun champ relatif à la résolution, aux codecs ou à l'audio.

Résultat de l'analyse FFprobe
FFprobe analyse le contenu réel du fichier et renseigne séparément, si les informations sont disponibles :
- Codec vidéo réel.
- Largeur et hauteur réelles.
- Fréquence d'images.
- Codec audio de chaque piste.
- Nombre de canaux audio.
- Langues déclarées des flux.
- Durée.
- Informations sur les sous-titres intégrés.

Les informations annoncées dans le nom du fichier ne doivent pas remplacer les résultats de FFprobe.

## 5. Ordre de traitement obligatoire

- Détecter le fichier vidéo et son emplacement.
- Extraire le titre et l'année à partir du nom du fichier et, si nécessaire, du dossier parent.
- Créer ou mettre à jour l'entrée du catalogue.
- Lancer FFprobe pour analyser le contenu du fichier.
- Enregistrer les métadonnées techniques retournées par FFprobe.
- Enregistrer les erreurs ou les champs techniques indisponibles.
- Permettre une nouvelle analyse technique sans réexécuter obligatoirement le parsing du titre.

## 6. Critères d'acceptation

CA-001 : le parseur extrait correctement le titre et l'année sans dépendre de la résolution ou du codec annoncés dans le nom.

CA-002 : les informations techniques du catalogue proviennent de FFprobe et non du parsing.

CA-003 : deux fichiers portant des noms différents mais contenant des métadonnées techniques identiques sont analysés individuellement.

CA-004 : un fichier dont le nom annonce 2160p mais dont le contenu possède une résolution différente est catalogué avec la résolution réelle retournée par FFprobe.

CA-005 : une erreur FFprobe ne bloque pas l'enregistrement du titre et de l'année.

CA-006 : les informations absentes de FFprobe restent inconnues et ne sont jamais inventées.

CA-007 : une nouvelle analyse FFprobe peut être exécutée sans créer de doublon dans le catalogue.

CA-008 : les informations techniques et les informations issues du parsing restent identifiables par leur provenance.