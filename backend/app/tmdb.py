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
    collection_id: Optional[int] = None
    collection_name: Optional[str] = None
    collection_poster_path: Optional[str] = None


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
    collection = data.get("belongs_to_collection") or {}

    return TmdbMovieMatch(
        tmdb_id=data["id"],
        title=data.get("title") or "",
        original_title=data.get("original_title") or "",
        overview=data.get("overview") or "",
        release_date=data.get("release_date") or "",
        poster_path=data.get("poster_path"),
        genres=genres,
        cast_json=json.dumps(cast, ensure_ascii=False),
        collection_id=collection.get("id"),
        collection_name=collection.get("name"),
        collection_poster_path=collection.get("poster_path"),
    )


@dataclass
class TmdbPersonMovie:
    tmdb_movie_id: int
    title: str
    release_date: str
    poster_path: Optional[str]
    character: str


def search_person(name: str) -> Optional[dict]:
    """Recherche une personne (acteur/actrice) par nom, retourne le meilleur
    resultat TMDb (dict brut avec au moins 'id' et 'name') ou None."""
    _check_configured()
    params = {
        "api_key": settings.tmdb_api_key,
        "query": name,
        "language": settings.tmdb_language,
        "include_adult": "false",
    }
    resp = requests.get(f"{BASE_URL}/search/person", params=params, headers=_headers(), timeout=20)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def fetch_person_movie_credits(person_id: int) -> list[TmdbPersonMovie]:
    """Retourne la filmographie complete (en tant qu'acteur) d'une personne TMDb."""
    _check_configured()
    params = {"api_key": settings.tmdb_api_key, "language": settings.tmdb_language}
    resp = requests.get(
        f"{BASE_URL}/person/{person_id}/movie_credits", params=params, headers=_headers(), timeout=20
    )
    resp.raise_for_status()
    data = resp.json()

    credits: list[TmdbPersonMovie] = []
    for c in data.get("cast", []):
        if not c.get("title"):
            continue
        credits.append(
            TmdbPersonMovie(
                tmdb_movie_id=c["id"],
                title=c.get("title") or "",
                release_date=c.get("release_date") or "",
                poster_path=c.get("poster_path"),
                character=c.get("character") or "",
            )
        )
    return credits


def fetch_collection(collection_id: int) -> dict:
    """Retourne le detail complet d'une collection TMDb, dont la liste des
    films qui la composent ('parts'), presents ou non dans une bibliotheque."""
    _check_configured()
    params = {"api_key": settings.tmdb_api_key, "language": settings.tmdb_language}
    resp = requests.get(f"{BASE_URL}/collection/{collection_id}", params=params, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


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
