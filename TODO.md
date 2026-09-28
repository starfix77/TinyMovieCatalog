#1 Dans la vue "Acteur / Filmographie" 
- ajouter pendant la recherche, une animation icone qui tourne à gauche du texte "Chargement de la filmographie"
- ajouter une option case à cocher [X] "affiche  uniquement les films de la bibliothèque" à droite dans la zone de recherche. Cette case à cocher est par defaut coché/checked
    si l'option est cochée : affiche uniquement les films de la bibliothèqte pour l'acteur
    si l'option est décochée: affiche toute la filmographie de l'acteur



#2 Scanner cette bibliotheque
- Quand on clique sur l'icone **⟳** a coté de la bibliotheque pour lancer un scan, affiche une boite de dialogue "Voulez-vous scanner et/ou mettre à jour la bibliothèque "? 
    - Bouton "Oui" (ferme la boite de dialogue et lance le scan) (focus bouton par defaut)
    - Bouton "Annuler" (ferme la boite de dialogue)
    - Option mode de comparaison sous forme de bouton radio
        (*) Comparaison simple (basée uniquement sur le nom du dossier)   
        ( ) Comparaison approfondie (basée sur le contenu du dossier)

    L'option "Comparaison simple" est le mode de scan actuel
    L'option "Comparaison approfondie" permet d'effectuer les actions suivantes
        - si le dossier existe déjà dans la base SQLite, alors comparer le nom du fichier MKV/MP4 du dossier sur disque avec le nom du fichier film dans la base SQLite si le nom est différente mettre à jour la base et analyser analyse du fichier video via `ffprobe`