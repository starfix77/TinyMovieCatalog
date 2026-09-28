"""
Utilitaires sur le filesystem qui heberge le dossier racine d'une bibliotheque.
"""
import shutil

_GB = 1024 ** 3
_TB = 1024 ** 4


def format_size(num_bytes: int) -> str:
    """Formate une taille en octets en \"xxx.xx GB\" ou \"x.xx TB\".

    Base 1024, comme l'explorateur Windows (qui affiche des GiB/TiB sous
    l'etiquette \"Go\"/\"GB\"), pour retrouver les memes chiffres que le
    systeme.
    """
    if num_bytes >= _TB:
        return f"{num_bytes / _TB:.2f} TB"
    return f"{num_bytes / _GB:.2f} GB"


def refresh_library_fs_stats(library) -> bool:
    """Met a jour, sur l'objet Library, la taille totale et l'espace libre du
    filesystem contenant son dossier racine.

    Ne fait pas de commit : c'est a l'appelant de valider la session.
    Retourne True si la lecture a reussi ; sinon (dossier/disque inaccessible)
    les dernieres valeurs connues sont conservees et la fonction retourne False.
    """
    try:
        usage = shutil.disk_usage(library.root_path)
    except (OSError, ValueError):
        return False

    library.fs_total_size = format_size(usage.total)
    library.fs_free_size = format_size(usage.free)
    return True
