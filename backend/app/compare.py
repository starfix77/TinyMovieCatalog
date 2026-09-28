"""
Comparaison de deux bibliotheques.

Module volontairement sans dependance FastAPI / SQLAlchemy : il travaille sur
des structures Python simples pour rester facile a tester.

Une bibliotheque est decrite par un dict :
    { "Inception (2010)": {("Inception.mkv", 8_123_456_789), ...}, ... }
cle    = nom du dossier du film ("Titre (Annee)")
valeur = ensemble des (nom de fichier video, taille en octets) du dossier
"""
import unicodedata
from typing import Dict, Iterable, List, Optional, Set, Tuple

VideoSet = Set[Tuple[str, int]]
Library = Dict[str, VideoSet]

# Statuts renvoyes au frontend
IDENTICAL = "identical"
IDENTICAL_DIFFERENT_FILE = "identical_different_file"
MISSING_RIGHT = "missing_right"
MISSING_LEFT = "missing_left"


def folder_key(name: str) -> str:
    """Cle de rapprochement des dossiers : sans espaces superflus et sans
    distinction de casse (le nom affiche reste celui du disque)."""
    return " ".join(name.split()).casefold()


def sort_key(name: str) -> str:
    """Tri alphabetique insensible a la casse et aux accents."""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


def _normalize_videos(videos: Iterable[Tuple[str, int]]) -> VideoSet:
    return {(" ".join(name.split()).casefold(), int(size or 0)) for name, size in videos}


def build_library(rows: Iterable[Tuple[str, Optional[str], Optional[int]]]) -> Dict[str, Tuple[str, VideoSet]]:
    """Construit {cle: (nom_affiche, fichiers)} a partir de lignes
    (folder_name, video_filename | None, size_bytes | None).
    Un film sans fichier video est conserve avec un ensemble vide."""
    out: Dict[str, Tuple[str, VideoSet]] = {}
    for folder_name, filename, size in rows:
        key = folder_key(folder_name)
        display, files = out.get(key, (folder_name, set()))
        if filename is not None:
            files = files | _normalize_videos([(filename, size or 0)])
        out[key] = (display, files)
    return out


def compare_libraries(
    left: Dict[str, Tuple[str, VideoSet]],
    right: Dict[str, Tuple[str, VideoSet]],
    mode: str,
    depth: str,
) -> List[dict]:
    """
    mode  : "identical" | "missing_right" | "missing_left"
    depth : "simple" (nom du dossier) | "deep" (+ nom et taille du fichier video)

    Retourne une liste de lignes {left, right, status}, triee par ordre
    alphabetique. `left` / `right` valent None quand le film est absent.
    """
    rows: List[dict] = []

    if mode == "identical":
        for key in left.keys() & right.keys():
            left_name, left_files = left[key]
            right_name, right_files = right[key]
            status = IDENTICAL
            if depth == "deep" and left_files != right_files:
                status = IDENTICAL_DIFFERENT_FILE
            rows.append({"left": left_name, "right": right_name, "status": status})

    elif mode == "missing_right":
        for key in left.keys() - right.keys():
            rows.append({"left": left[key][0], "right": None, "status": MISSING_RIGHT})

    elif mode == "missing_left":
        for key in right.keys() - left.keys():
            rows.append({"left": None, "right": right[key][0], "status": MISSING_LEFT})

    else:
        raise ValueError(f"Mode de comparaison inconnu : {mode}")

    rows.sort(key=lambda r: sort_key(r["left"] or r["right"] or ""))
    return rows
