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


class CompareAudioTrack(BaseModel):
    language: Optional[str] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    title: Optional[str] = None


class CompareVideoDetail(BaseModel):
    """Detail du fichier video principal d'un film (vue Comparaison, mode details)."""
    filename: str
    video_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: int = 0
    duration_sec: Optional[float] = None
    audio_tracks: List[CompareAudioTrack] = []
    subtitles: List[str] = []


class CompareRow(BaseModel):
    """Une ligne du tableau de comparaison (film a gauche / statut / film a droite)."""
    left: Optional[str] = None    # "Titre (Annee)" dans la bibliotheque #1, None si absent
    right: Optional[str] = None   # "Titre (Annee)" dans la bibliotheque #2, None si absent
    left_movie_id: Optional[int] = None    # id du film en base (ouverture de la fiche detail)
    right_movie_id: Optional[int] = None
    status: str                   # identical | identical_different_file | missing_right | missing_left
    left_detail: Optional[CompareVideoDetail] = None    # renseigne uniquement en mode "details"
    right_detail: Optional[CompareVideoDetail] = None


class CompareOut(BaseModel):
    left_library_id: int
    left_library_name: str
    right_library_id: int
    right_library_name: str
    mode: str
    depth: str
    total: int
    rows: List[CompareRow]


class ScanRequest(BaseModel):
    # "simple" (defaut, mode historique) : identification des films par nom
    # de dossier uniquement.
    # "deep" : compare en plus le nom du fichier video principal avec celui
    # deja enregistre en base ; ne relance ffprobe que si celui-ci differe.
    compare_mode: str = "simple"


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


# ---------- Acteurs / Filmographie ----------

class ActorSearchResult(BaseModel):
    name: str
    movie_count: int  # nombre de films de CETTE bibliotheque ou l'acteur apparait


class ActorFilmographyEntry(BaseModel):
    tmdb_movie_id: int
    title: str
    year: Optional[int] = None
    poster_filename: Optional[str] = None
    in_library: bool
    movie_id: Optional[int] = None
    folder_name: Optional[str] = None


class ActorFilmographyOut(BaseModel):
    name: str
    # "tmdb" (filmographie complete recuperee depuis TheMovieDB),
    # "local" (TMDb interroge mais indisponible/acteur non trouve -> repli bibliotheque),
    # "local_only" (TMDb non interroge du tout, mode bibliotheque uniquement demande explicitement)
    source: str
    movies_in_library: int
    total_movies: int
    movies: List[ActorFilmographyEntry] = []
