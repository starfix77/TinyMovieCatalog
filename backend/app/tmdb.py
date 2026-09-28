"""
Client minimal pour l'API TheMovieDB (TMDb).

Necessite une cle API valide dans settings.tmdb_api_key (voir .env.example).
Documentation: https://developer.themoviedb.org/docs
"""
import json
from dataclasses import dataclass
from typing import Optional

import requests

from app.config import settings

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class TmdbNotConfiguredError(RuntimeError):
    pass


@dataclass
class TmdbMovieMatch:
    tmdb_id: int
    title: str
    original_title: str
    overview: str
    release_date: str
    poster_path: Optional[str]
    genres: str
    cast_json: str  # JSON serialise: [{"name": "...", "character": "..."}]


def _check_configured():
    if not settings.tmdb_api_key:
        raise TmdbNotConfiguredError(
            "Cle API TheMovieDB non configuree (TMDB_API_KEY dans backend/.env)."
        )


def _headers():
    return {"Accept": "application/json"}


def search_movies(title: str, year: Optional[int]) -> list[TmdbMovieMatch]:
    """Recherche plusieurs films et retourne leurs details pour permettre un choix manuel."""
    _check_configured()

    params = {
        "api_key": settings.tmdb_api_key,
        "query": title,
        "language": settings.tmdb_language,
        "include_adult": "false",
    }
    if year:
        params["year"] = year

    resp = requests.get(f"{BASE_URL}/search/movie", params=params, headers=_headers(), timeout=20)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    if not results and year:
        params.pop("year", None)
        resp = requests.get(f"{BASE_URL}/search/movie", params=params, headers=_headers(), timeout=20)
        resp.raise_for_status()
        results = resp.json().get("results", [])

    matches: list[TmdbMovieMatch] = []
    for result in results[:12]:
        try:
            matches.append(_fetch_movie_details(result["id"]))
        except Exception:
            continue
    return matches


def search_movie(title: str, year: Optional[int]) -> Optional[TmdbMovieMatch]:
    """Compatibilite avec le scanner : retourne le premier resultat."""
    matches = search_movies(title, year)
    return matches[0] if matches else None

def _fetch_movie_details(tmdb_id: int) -> TmdbMovieMatch:
    params = {"api_key": settings.tmdb_api_key, "language": settings.tmdb_language,
              "append_to_response": "credits"}
    resp = requests.get(f"{BASE_URL}/movie/{tmdb_id}", params=params, headers=_headers(), timeout=20)
    resp.raise_for_status()
    data = resp.json()

    cast = [
        {"name": c.get("name"), "character": c.get("character")}
        for c in data.get("credits", {}).get("cast", [])[: settings.max_cast]
    ]
    genres = ", ".join(g["name"] for g in data.get("genres", []))

    return TmdbMovieMatch(
        tmdb_id=data["id"],
        title=data.get("title") or "",
        original_title=data.get("original_title") or "",
        overview=data.get("overview") or "",
        release_date=data.get("release_date") or "",
        poster_path=data.get("poster_path"),
        genres=genres,
        cast_json=json.dumps(cast, ensure_ascii=False),
    )


def download_poster(poster_path: str, dest_file) -> bool:
    """Telecharge l'affiche vers dest_file (Path). Retourne True si succes."""
    if not poster_path:
        return False
    url = f"{IMAGE_BASE_URL}{poster_path}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return False
    dest_file.write_bytes(resp.content)
    return True
