from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Library, Movie, Note
from app.schemas import NoteListItem, NoteListOut, NoteOut, NoteUpdate

router = APIRouter(prefix="/api", tags=["notes"])


@router.get("/notes", response_model=NoteListOut)
def list_notes(
    library_id: int = Query(..., description="Identifiant de la bibliotheque"),
    db: Session = Depends(get_db),
):
    """Tous les films / series de la bibliotheque ayant une note, tries par titre."""
    library = db.get(Library, library_id)
    if not library:
        raise HTTPException(404, "Bibliotheque introuvable.")
    rows = (
        db.query(Note)
        .join(Movie, Movie.id == Note.movie_id)
        .options(joinedload(Note.movie))
        .filter(Movie.library_id == library_id)
        .order_by(Movie.title, Movie.year)
        .all()
    )
    items = [
        NoteListItem(
            movie_id=n.movie_id,
            title=n.movie.title,
            year=n.movie.year,
            folder_name=n.movie.folder_name,
            media_type=library.media_type or "movie",
            content=n.content,
        )
        for n in rows
        if n.content and n.content.strip()
    ]
    return NoteListOut(total=len(items), items=items)


@router.get("/movies/{movie_id}/note", response_model=NoteOut)
def get_note(movie_id: int, db: Session = Depends(get_db)):
    if not db.get(Movie, movie_id):
        raise HTTPException(404, "Film introuvable.")
    note = db.query(Note).filter(Note.movie_id == movie_id).first()
    return NoteOut(movie_id=movie_id, content=note.content if note else "")


@router.put("/movies/{movie_id}/note", response_model=NoteOut)
def save_note(movie_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    """Enregistre la note du film/de la serie. Un texte vide supprime la note
    (le film disparait alors de la vue 'Notes')."""
    if not db.get(Movie, movie_id):
        raise HTTPException(404, "Film introuvable.")
    note = db.query(Note).filter(Note.movie_id == movie_id).first()
    content = payload.content.replace("\r\n", "\n")

    if not content.strip():
        if note:
            db.delete(note)
            db.commit()
        return NoteOut(movie_id=movie_id, content="")

    if note:
        note.content = content
        note.updated_at = datetime.utcnow()
    else:
        note = Note(movie_id=movie_id, content=content)
        db.add(note)
    db.commit()
    return NoteOut(movie_id=movie_id, content=content)
