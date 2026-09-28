"""
Utilitaires sur le filesystem qui heberge le dossier racine d'une bibliotheque.
"""
import shutil


def refresh_library_fs_stats(library) -> bool:
    """Met a jour, sur l'objet Library, la taille totale et l'espace libre (en
    octets) du filesystem contenant son dossier racine.

    Ne fait pas de commit : c'est a l'appelant de valider la session.
    Retourne True si la lecture a reussi ; sinon (dossier/disque inaccessible)
    les dernieres valeurs connues sont conservees et la fonction retourne False.
    """
    try:
        usage = shutil.disk_usage(library.root_path)
    except (OSError, ValueError):
        return False

    library.fs_total_size = usage.total
    library.fs_free_size = usage.free
    return True
