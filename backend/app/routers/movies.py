from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc

from app.database import get_db
from app.config import settings
from app.models import Movie, VideoFile
from app.schemas import MovieOut, MoviePage, TmdbCandidateOut, MovieMetadataUpdate
from app import tmdb
from app.scanner import sync_saga_for_match
from datetime import datetime

router = APIRouter(prefix="/api/movies", tags=["movies"])

SORTABLE_FIELDS = {
    "title": Movie.title,
    "filename": VideoFile.filename,
    "video_codec": VideoFile.video_codec,
    "size": VideoFile.size_bytes,
    "genre": Movie.genres,
    "year": Movie.year,
    "duration": VideoFile.duration_sec,
    # la resolution est triee sur le nombre de pixels (largeur * hauteur)
    "resolution": (VideoFile.width, VideoFile.height),
}


@router.get("", response_model=MoviePage)
def list_movies(
    library_id: int = Query(..., description="Identifiant de la bibliotheque"),
    search: Optional[str] = Query(None, description="Recherche sur le titre du film"),
    sort_by: Optional[str] = Query(None, description="title|filename|video_codec|size|resolution|genre|year|duration"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Movie)
        .options(joinedload(Movie.video_files).joinedload(VideoFile.audio_tracks),
                 joinedload(Movie.subtitles))
        .outerjoin(VideoFile, VideoFile.movie_id == Movie.id)
        .filter(Movie.library_id == library_id)
    )

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(Movie.title.ilike(like))

    if sort_by and sort_by in SORTABLE_FIELDS:
        field = SORTABLE_FIELDS[sort_by]
        direction = desc if sort_dir == "desc" else asc
        if isinstance(field, tuple):
            for f in field:
                query = query.order_by(direction(f))
        else:
            query = query.order_by(direction(field))
    else:
        query = query.order_by(asc(Movie.title))

    query = query.distinct()
    total = query.count()
    items = query.all()

    return MoviePage(total=total, items=[MovieOut.model_validate(m) for m in items])


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = (
        db.query(Movie)
        .options(joinedload(Movie.video_files).joinedload(VideoFile.audio_tracks),
                 joinedload(Movie.subtitles))
        .filter(Movie.id == movie_id)
        .first()
    )
    if not movie:
        raise HTTPException(404, "Film introuvable.")
    return movie


@router.get("/{movie_id}/tmdb-search", response_model=list[TmdbCandidateOut])
def search_tmdb_candidates(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Film introuvable.")
    try:
        matches = tmdb.search_movies(movie.title, movie.year)
    except tmdb.TmdbNotConfiguredError as exc:
        raise HTTPException(503, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Recherche TMDb impossible : {exc}")

    return [
        TmdbCandidateOut(
            tmdb_id=m.tmdb_id,
            title=m.title,
            original_title=m.original_title,
            overview=m.overview,
            release_date=m.release_date,
            poster_path=m.poster_path,
            genres=m.genres,
            cast=m.cast_json,
        )
        for m in matches
    ]


@router.put("/{movie_id}/metadata", response_model=MovieOut)
def update_movie_metadata(
    movie_id: int,
    payload: MovieMetadataUpdate,
    db: Session = Depends(get_db),
):
    movie = (
        db.query(Movie)
        .options(joinedload(Movie.video_files).joinedload(VideoFile.audio_tracks),
                 joinedload(Movie.subtitles))
        .filter(Movie.id == movie_id)
        .first()
    )
    if not movie:
        raise HTTPException(404, "Film introuvable.")

    try:
        match = tmdb._fetch_movie_details(payload.tmdb_id)
    except tmdb.TmdbNotConfiguredError as exc:
        raise HTTPException(503, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Impossible de recuperer les informations TMDb : {exc}")

    old_poster = movie.poster_filename
    new_poster = f"tmdb_{match.tmdb_id}.jpg" if match.poster_path else None

    # Telecharge l'affiche avant de modifier la DB : si le telechargement echoue,
    # aucune metadonnee n'est modifiee.
    if new_poster:
        dest = settings.thumbnails_dir / new_poster
        if not dest.exists() and not tmdb.download_poster(match.poster_path, dest):
            raise HTTPException(502, "Impossible de telecharger la nouvelle affiche.")

    try:
        movie.tmdb_id = match.tmdb_id
        movie.original_title = match.original_title
        movie.overview = match.overview
        movie.release_date = match.release_date
        movie.genres = match.genres
        movie.cast = match.cast_json
        movie.poster_filename = new_poster
        movie.tmdb_synced_at = datetime.utcnow()
        try:
            movie.saga_id = sync_saga_for_match(db, match)
        except Exception:
            pass  # la fiche du film reste enregistree meme si la saga echoue
        db.commit()
    except Exception as exc:
        db.rollback()
        # Ne laisse pas une nouvelle vignette orpheline si la transaction DB echoue.
        if new_poster and new_poster != old_poster:
            new_path = settings.thumbnails_dir / new_poster
            if new_path.exists():
                try:
                    new_path.unlink()
                except OSError:
                    pass
        raise HTTPException(500, f"Impossible d'enregistrer les informations du film : {exc}")

    # Relecture complete avec les relations necessaires : le frontend reçoit
    # exactement l'etat persiste dans data/db/library.db.
    updated_movie = (
        db.query(Movie)
        .options(joinedload(Movie.video_files).joinedload(VideoFile.audio_tracks),
                 joinedload(Movie.subtitles))
        .filter(Movie.id == movie_id)
        .first()
    )
    if not updated_movie:
        raise HTTPException(500, "Le film a été mis à jour mais ne peut pas être relu.")

    if old_poster and old_poster != new_poster:
        # Supprime uniquement une ancienne vignette qui n'est plus utilisee par un autre film.
        still_used = db.query(Movie).filter(
            Movie.poster_filename == old_poster,
            Movie.id != movie_id,
        ).first()
        old_path = settings.thumbnails_dir / old_poster
        if still_used is None and old_path.exists():
            try:
                old_path.unlink()
            except OSError:
                pass

    return updated_movie


@router.get("/{movie_id}/poster")
def get_poster(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie or not movie.poster_filename:
        raise HTTPException(404, "Affiche indisponible.")
    path = settings.thumbnails_dir / movie.poster_filename
    if not path.exists():
        raise HTTPException(404, "Fichier d'affiche manquant sur le disque.")
    return FileResponse(path, media_type="image/jpeg")
