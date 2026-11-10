"""Ordre d'affichage personnalise des bibliotheques (colonne libraries.sort_order)."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Library


def ordered_libraries(db: Session) -> list[Library]:
    """Bibliotheques dans l'ordre d'affichage (egalite -> ordre de creation)."""
    return db.query(Library).order_by(Library.sort_order, Library.id).all()


def next_sort_order(db: Session) -> int:
    """Rang d'une nouvelle bibliotheque : toujours la derniere de la liste."""
    return (db.query(func.max(Library.sort_order)).scalar() or 0) + 1


def normalize_sort_order(db: Session, commit: bool = True) -> None:
    """Renumerote 1..n en conservant l'ordre relatif actuel (supprime les trous
    laisses par les suppressions)."""
    for rank, library in enumerate(ordered_libraries(db), start=1):
        if library.sort_order != rank:
            library.sort_order = rank
    if commit:
        db.commit()


def apply_order(db: Session, ids: list[int]) -> None:
    """Applique l'ordre demande. Les bibliotheques absentes de `ids` (creees
    entre-temps) gardent leur ordre relatif et passent apres les autres ; les
    identifiants inconnus sont ignores."""
    libraries = {lib.id: lib for lib in ordered_libraries(db)}
    final: list[int] = []
    for library_id in ids:
        if library_id in libraries and library_id not in final:
            final.append(library_id)
    final += [lib_id for lib_id in libraries if lib_id not in final]
    for rank, library_id in enumerate(final, start=1):
        libraries[library_id].sort_order = rank
    db.commit()
