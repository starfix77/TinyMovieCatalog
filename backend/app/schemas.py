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
