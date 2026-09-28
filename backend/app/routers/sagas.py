from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from app.database import get_db
from app.config import settings
from app.models import Saga, Movie
from app.schemas import SagaListItemOut, SagaDetailOut, SagaMovieEntryOut

router = APIRouter(prefix="/api/sagas", tags=["sagas"])


def _year_from_release(release_date: str | None) -> int | None:
    if release_date and len(release_date) >= 4 and release_date[:4].isdigit():
        return int(release_date[:4])
    return None


@router.get("", response_model=list[SagaListItemOut])
def list_sagas(library_id: int = Query(...), db: Session = Depends(get_db)):
    """Sagas ayant au moins un film present dans la bibliotheque donnee."""
    saga_ids = [
        row[0]
        for row in db.query(Movie.saga_id)
        .filter(Movie.library_id == library_id, Movie.saga_id.isnot(None))
        .distinct()
        .all()
    ]
    if not saga_ids:
        return []

    sagas = db.query(Saga).filter(Saga.id.in_(saga_ids)).order_by(asc(Saga.name)).all()

    in_library_counts = dict(
        db.query(Movie.saga_id, func.count(Movie.id))
        .filter(Movie.library_id == library_id, Movie.saga_id.in_(saga_ids))
        .group_by(Movie.saga_id)
        .all()
    )

    return [
        SagaListItemOut(
            id=saga.id,
            name=saga.name,
            poster_filename=saga.poster_filename,
            movies_in_library=in_library_counts.get(saga.id, 0),
            total_movies=len(saga.entries) or in_library_counts.get(saga.id, 0),
        )
        for saga in sagas
    ]


@router.get("/{saga_id}", response_model=SagaDetailOut)
def get_saga(saga_id: int, library_id: int = Query(...), db: Session = Depends(get_db)):
    saga = db.get(Saga, saga_id)
    if not saga:
        raise HTTPException(404, "Saga introuvable.")

    # Films de CETTE bibliotheque rattaches a la saga, indexes par tmdb_id :
    # la presence (coeur) est toujours relative a la bibliotheque active, pas
    # a une autre bibliotheque qui possederait le meme film.
    library_movies = {
        m.tmdb_id: m
        for m in db.query(Movie)
        .filter(Movie.library_id == library_id, Movie.saga_id == saga_id)
        .all()
        if m.tmdb_id
    }

    entries = sorted(
        saga.entries,
        key=lambda e: (e.order_index if e.order_index is not None else 999, e.release_date or ""),
    )

    movies_out: list[SagaMovieEntryOut] = []
    seen_tmdb_ids: set[int] = set()

    for entry in entries:
        seen_tmdb_ids.add(entry.tmdb_movie_id)
        local = library_movies.get(entry.tmdb_movie_id)
        movies_out.append(
            SagaMovieEntryOut(
                tmdb_movie_id=entry.tmdb_movie_id,
                title=entry.title,
                year=_year_from_release(entry.release_date),
                poster_filename=entry.poster_filename,
                in_library=local is not None,
                movie_id=local.id if local else None,
                folder_name=local.folder_name if local else None,
            )
        )

    # Filet de securite : un film de la bibliotheque rattache a la saga mais
    # absent du cache TMDb des "parts" (collection jamais entierement
    # synchronisee) doit quand meme apparaitre.
    for tmdb_id, local in library_movies.items():
        if tmdb_id not in seen_tmdb_ids:
            movies_out.append(
                SagaMovieEntryOut(
                    tmdb_movie_id=tmdb_id,
                    title=local.title,
                    year=local.year,
                    poster_filename=local.poster_filename,
                    in_library=True,
                    movie_id=local.id,
                    folder_name=local.folder_name,
                )
            )

    return SagaDetailOut(
        id=saga.id,
        name=saga.name,
        overview=saga.overview,
        poster_filename=saga.poster_filename,
        movies=movies_out,
    )


@router.get("/{saga_id}/poster")
def get_saga_poster(saga_id: int, db: Session = Depends(get_db)):
    saga = db.get(Saga, saga_id)
    if not saga or not saga.poster_filename:
        raise HTTPException(404, "Affiche indisponible.")
    path = settings.thumbnails_dir / saga.poster_filename
    if not path.exists():
        raise HTTPException(404, "Fichier d'affiche manquant sur le disque.")
    return FileResponse(path, media_type="image/jpeg")
