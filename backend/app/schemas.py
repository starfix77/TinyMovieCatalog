from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ---------- Libraries ----------

class LibraryCreate(BaseModel):
    name: str
    root_path: str


class LibraryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    root_path: str
    created_at: datetime
    last_scanned_at: Optional[datetime] = None
    movie_count: int = 0


class LibraryInfoOut(BaseModel):
    """Fiche d'information d'une bibliotheque (page Info)."""
    id: int
    name: str
    root_path: str
    movie_count: int
    created_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    # Taille totale et espace libre du filesystem du dossier racine, en octets
    fs_total_size: Optional[int] = None
    fs_free_size: Optional[int] = None
    # False si le dossier racine est inaccessible : les valeurs ci-dessus sont
    # alors les dernieres connues (ou None si jamais lues).
    fs_available: bool = True


class ScanResult(BaseModel):
    library_id: int
    folders_scanned: int
    movies_added: int
    movies_updated: int
    movies_removed: int
    errors: List[str] = []


# ---------- Audio tracks ----------

class AudioTrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    track_index: int
    language: Optional[str] = None
    title: Optional[str] = None
    codec: Optional[str] = None
    channels: Optional[int] = None
    bitrate: Optional[int] = None


# ---------- Video files ----------

class VideoFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    container: Optional[str] = None
    size_bytes: int
    duration_sec: Optional[float] = None
    video_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    video_bitrate: Optional[int] = None
    audio_tracks: List[AudioTrackOut] = []


# ---------- Subtitles ----------

class SubtitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    language_guess: Optional[str] = None


# ---------- Movies ----------

class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    library_id: int
    folder_name: str
    title: str
    year: Optional[int] = None
    tmdb_id: Optional[int] = None
    original_title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_filename: Optional[str] = None
    cast: Optional[str] = None
    genres: Optional[str] = None
    video_files: List[VideoFileOut] = []
    subtitles: List[SubtitleOut] = []


class TmdbCandidateOut(BaseModel):
    tmdb_id: int
    title: str
    original_title: str
    overview: str
    release_date: str
    poster_path: Optional[str] = None
    genres: str
    cast: str


class MovieMetadataUpdate(BaseModel):
    tmdb_id: int


class MoviePage(BaseModel):
    total: int
    items: List[MovieOut]


# ---------- Sagas ----------

class SagaListItemOut(BaseModel):
    id: int
    name: str
    poster_filename: Optional[str] = None
    movies_in_library: int
    total_movies: int


class SagaMovieEntryOut(BaseModel):
    tmdb_movie_id: int
    title: str
    year: Optional[int] = None
    poster_filename: Optional[str] = None
    in_library: bool
    movie_id: Optional[int] = None
    folder_name: Optional[str] = None


class SagaDetailOut(BaseModel):
    id: int
    name: str
    overview: Optional[str] = None
    poster_filename: Optional[str] = None
    movies: List[SagaMovieEntryOut] = []
