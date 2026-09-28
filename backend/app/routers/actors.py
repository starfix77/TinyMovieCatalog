import json
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import Movie
from app.schemas import ActorSearchResult, ActorFilmographyEntry, ActorFilmographyOut
from app import tmdb

router = APIRouter(prefix="/api/actors", tags=["actors"])

# Nombre minimum de caracteres saisis avant de declencher la recherche
# d'acteurs (evite de scanner tout le cast pour 1 seule lettre).
MIN_QUERY_LENGTH = 2
MAX_SUGGESTIONS = 20


def _normalize(text: str) -> str:
    """Minuscules + suppression des accents, pour une comparaison tolerante."""
    text = text or ""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()


def _cast_names(movie: Movie) -> list[str]:
    if not movie.cast:
        return []
    try:
        cast_list = json.loads(movie.cast)
    except (json.JSONDecodeError, TypeError):
        return []
    return [m.get("name") for m in cast_list if isinstance(m, dict) and m.get("name")]


def _year_from_release(release_date: Optional[str]) -> Optional[int]:
    if release_date and len(release_date) >= 4 and release_date[:4].isdigit():
        return int(release_date[:4])
    return None


@router.get("/search", response_model=list[ActorSearchResult])
def search_actors(
    library_id: int = Query(...),
    q: str = Query(..., description="Fragment de nom saisi par l'utilisateur"),
    db: Session = Depends(get_db),
):
    """Autocompletion 'Google suggest' sur les acteurs presents dans le cast
    des films de la bibliotheque (propriete Movie.cast)."""
    query_norm = _normalize(q.strip())
    if len(query_norm) < MIN_QUERY_LENGTH:
        return []

    movies = (
        db.query(Movie)
        .filter(Movie.library_id == library_id, Movie.cast.isnot(None))
        .all()
    )

    counts: dict[str, int] = {}
    for movie in movies:
        names_in_movie = {name for name in _cast_names(movie) if query_norm in _normalize(name)}
        for name in names_in_movie:
            counts[name] = counts.get(name, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], _normalize(kv[0])))[:MAX_SUGGESTIONS]
    return [ActorSearchResult(name=name, movie_count=count) for name, count in ranked]


@router.get("/filmography", response_model=ActorFilmographyOut)
def get_filmography(
    library_id: int = Query(...),
    name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Filmographie complete d'un acteur (via TheMovieDB si disponible), avec
    pour chaque film un indicateur de presence dans la bibliotheque active."""
    name_norm = _normalize(name)

    library_movies = db.query(Movie).filter(Movie.library_id == library_id).all()
    local_matches = [m for m in library_movies if name_norm in {_normalize(n) for n in _cast_names(m)}]
    local_by_tmdb_id = {m.tmdb_id: m for m in local_matches if m.tmdb_id}
    local_without_tmdb_id = [m for m in local_matches if not m.tmdb_id]

    entries: list[ActorFilmographyEntry] = []
    source = "local"

    person = None
    try:
        person = tmdb.search_person(name)
    except tmdb.TmdbNotConfiguredError:
        person = None
    except Exception:
        person = None

    if person:
        try:
            credits = tmdb.fetch_person_movie_credits(person["id"])
            credits.sort(key=lambda c: c.release_date or "", reverse=True)
            source = "tmdb"

            seen_tmdb_ids: set[int] = set()
            for credit in credits:
                if credit.tmdb_movie_id in seen_tmdb_ids:
                    continue
                seen_tmdb_ids.add(credit.tmdb_movie_id)

                local = local_by_tmdb_id.get(credit.tmdb_movie_id)
                poster_filename = local.poster_filename if local else None
                if not poster_filename and credit.poster_path:
                    poster_filename = f"tmdb_{credit.tmdb_movie_id}.jpg"
                    dest = settings.thumbnails_dir / poster_filename
                    if not dest.exists():
                        try:
                            tmdb.download_poster(credit.poster_path, dest)
                        except Exception:
                            poster_filename = None

                entries.append(
                    ActorFilmographyEntry(
                        tmdb_movie_id=credit.tmdb_movie_id,
                        title=credit.title,
                        year=_year_from_release(credit.release_date),
                        poster_filename=poster_filename,
                        in_library=local is not None,
                        movie_id=local.id if local else None,
                        folder_name=local.folder_name if local else None,
                    )
                )

            # Filet de securite : un film local de cet acteur absent de la
            # reponse TMDb (ex. tmdb_id local non reconnu par /person/credits)
            # doit quand meme apparaitre.
            for tmdb_id, local in local_by_tmdb_id.items():
                if tmdb_id not in seen_tmdb_ids:
                    entries.append(
                        ActorFilmographyEntry(
                            tmdb_movie_id=tmdb_id,
                            title=local.title,
                            year=local.year,
                            poster_filename=local.poster_filename,
                            in_library=True,
                            movie_id=local.id,
                            folder_name=local.folder_name,
                        )
                    )
        except Exception:
            person = None  # bascule sur le mode local ci-dessous
            entries = []

    if not person:
        # TMDb indisponible / acteur non trouve : on se limite aux films de
        # la bibliotheque locale ou l'acteur apparait dans le cast.
        source = "local"
        entries = []
        for movie in local_matches:
            entries.append(
                ActorFilmographyEntry(
                    tmdb_movie_id=movie.tmdb_id or 0,
                    title=movie.title,
                    year=movie.year,
                    poster_filename=movie.poster_filename,
                    in_library=True,
                    movie_id=movie.id,
                    folder_name=movie.folder_name,
                )
            )
        entries.sort(key=lambda e: (e.year or 0), reverse=True)

    # Films locaux sans tmdb_id : toujours presents dans local_matches mais
    # jamais dans les credits TMDb (pas d'id commun) -> on les ajoute a part.
    if source == "tmdb":
        already_movie_ids = {e.movie_id for e in entries if e.movie_id}
        for movie in local_without_tmdb_id:
            if movie.id in already_movie_ids:
                continue
            entries.append(
                ActorFilmographyEntry(
                    tmdb_movie_id=0,
                    title=movie.title,
                    year=movie.year,
                    poster_filename=movie.poster_filename,
                    in_library=True,
                    movie_id=movie.id,
                    folder_name=movie.folder_name,
                )
            )

    if not entries:
        raise HTTPException(404, "Aucun film trouve pour cet acteur.")

    return ActorFilmographyOut(
        name=name,
        source=source,
        movies_in_library=sum(1 for e in entries if e.in_library),
        total_movies=len(entries),
        movies=entries,
    )
