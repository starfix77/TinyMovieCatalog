import json
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Library, LibraryLog, LibraryLogFile, Movie
from app.schemas import JournalEntryOut, JournalFileAudio, JournalFileOut, JournalOut

router = APIRouter(prefix="/api/journal", tags=["journal"])


def _utc(entry: JournalEntryOut | JournalFileOut):
    """Les dates sont stockees en UTC naif : on ajoute le fuseau pour que le
    JSON contienne un 'Z' et que le navigateur affiche l'heure locale."""
    if entry.created_at.tzinfo is None:
        entry.created_at = entry.created_at.replace(tzinfo=timezone.utc)
    return entry


def _loads(raw: str | None) -> list:
    try:
        return json.loads(raw) if raw else []
    except ValueError:
        return []


@router.get("", response_model=JournalOut)
def list_journal(
    library_id: int = Query(..., description="Identifiant de la bibliotheque"),
    db: Session = Depends(get_db),
):
    """Journal de la bibliotheque (niveau bibliotheque), du plus recent au plus ancien."""
    if not db.get(Library, library_id):
        raise HTTPException(404, "Bibliotheque introuvable.")
    rows = (db.query(LibraryLog).filter(LibraryLog.library_id == library_id)
            .order_by(LibraryLog.created_at.desc(), LibraryLog.id.desc()).all())
    items = [_utc(JournalEntryOut.model_validate(r)) for r in rows]
    return JournalOut(total=len(items), items=items)


@router.get("/{log_id}/files", response_model=list[JournalFileOut])
def journal_files(log_id: int, db: Session = Depends(get_db)):
    """Detail d'un evenement : fichiers films / series ajoutes, modifies ou supprimes."""
    if not db.get(LibraryLog, log_id):
        raise HTTPException(404, "Evenement de journal introuvable.")
    rows = (db.query(LibraryLogFile).filter(LibraryLogFile.log_id == log_id)
            .order_by(LibraryLogFile.movie_title, LibraryLogFile.filename).all())
    # Affiche courante du film / de la serie (elle peut avoir ete renseignee ou
    # changee apres l'evenement) ; a defaut, l'instantane enregistre.
    movie_ids = {r.movie_id for r in rows if r.movie_id is not None}
    current_posters = dict(
        db.query(Movie.id, Movie.poster_filename).filter(Movie.id.in_(movie_ids)).all()
    ) if movie_ids else {}
    out = []
    for r in rows:
        out.append(_utc(JournalFileOut(
            id=r.id, status=r.status, movie_id=r.movie_id, movie_title=r.movie_title,
            movie_year=r.movie_year, poster_filename=current_posters.get(r.movie_id) or r.poster_filename, filename=r.filename,
            size_bytes=r.size_bytes, video_codec=r.video_codec, width=r.width, height=r.height,
            audio_tracks=[JournalFileAudio(**a) for a in _loads(r.audio_json)],
            subtitles=[str(x) for x in _loads(r.subtitles_json)],
            created_at=r.created_at,
        )))
    return out
