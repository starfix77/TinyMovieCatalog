from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas import TmdbLanguagesOut
from app import tmdb

router = APIRouter(prefix="/api/tmdb", tags=["tmdb"])


@router.get("/languages", response_model=TmdbLanguagesOut)
def list_languages():
    """Langues disponibles dans TMDb + langue par defaut (TMDB_LANGUAGE du .env)."""
    try:
        languages = tmdb.fetch_available_languages()
    except tmdb.TmdbNotConfiguredError as exc:
        raise HTTPException(503, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Impossible de recuperer les langues TMDb : {exc}")
    return TmdbLanguagesOut(default=settings.tmdb_language, languages=languages)
