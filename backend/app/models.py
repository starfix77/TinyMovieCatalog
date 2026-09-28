from datetime import datetime

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, ForeignKey, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class Saga(Base):
    """Une saga/collection de films telle que definie par TheMovieDB
    (ex: 'Harry Potter Collection'). Mise en cache localement pour pouvoir
    afficher tous les films de la saga, meme ceux absents des bibliotheques."""
    __tablename__ = "sagas"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_collection_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    overview = Column(Text, nullable=True)
    poster_filename = Column(String, nullable=True)  # nom de fichier dans data/thumbnails
    synced_at = Column(DateTime, nullable=True)

    entries = relationship("SagaMovie", back_populates="saga", cascade="all, delete-orphan")


class SagaMovie(Base):
    """Un film appartenant a une saga TMDb (cache des 'parts' de la collection),
    qu'il soit present ou non dans une bibliotheque locale."""
    __tablename__ = "saga_movies"
    __table_args__ = (UniqueConstraint("saga_id", "tmdb_movie_id", name="uq_saga_tmdb_movie"),)

    id = Column(Integer, primary_key=True, index=True)
    saga_id = Column(Integer, ForeignKey("sagas.id"), nullable=False)

    tmdb_movie_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    release_date = Column(String, nullable=True)
    poster_filename = Column(String, nullable=True)
    order_index = Column(Integer, nullable=True)  # position dans la saga (ordre TMDb)

    saga = relationship("Saga", back_populates="entries")


class Library(Base):
    """Une bibliotheque = un dossier racine contenant des sous-dossiers de films."""
    __tablename__ = "libraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    root_path = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scanned_at = Column(DateTime, nullable=True)

    # Filesystem hebergeant le dossier racine, en octets (entiers 64 bits).
    # Rafraichi a la creation, a chaque scan et a l'ouverture de la page "Info".
    fs_total_size = Column(BigInteger, nullable=True)
    fs_free_size = Column(BigInteger, nullable=True)

    movies = relationship("Movie", back_populates="library", cascade="all, delete-orphan")


class Movie(Base):
    """Un film = un dossier 'Titre (Annee)' au sein d'une bibliotheque."""
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("library_id", "folder_name", name="uq_library_folder"),)

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"), nullable=False)

    folder_name = Column(String, nullable=False)   # "Inception (2010)"
    folder_path = Column(String, nullable=False)    # chemin absolu complet
    title = Column(String, nullable=False)           # parse depuis le dossier
    year = Column(Integer, nullable=True)             # parse depuis le dossier

    # Metadonnees TMDb
    tmdb_id = Column(Integer, nullable=True)
    original_title = Column(String, nullable=True)
    overview = Column(Text, nullable=True)
    release_date = Column(String, nullable=True)
    poster_filename = Column(String, nullable=True)  # nom de fichier dans data/thumbnails
    cast = Column(Text, nullable=True)                 # JSON: liste d'acteurs
    genres = Column(String, nullable=True)             # "Action, Science-fiction"
    tmdb_synced_at = Column(DateTime, nullable=True)
    saga_id = Column(Integer, ForeignKey("sagas.id"), nullable=True)  # collection TMDb

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    library = relationship("Library", back_populates="movies")
    video_files = relationship("VideoFile", back_populates="movie", cascade="all, delete-orphan")
    subtitles = relationship("Subtitle", back_populates="movie", cascade="all, delete-orphan")
    saga = relationship("Saga")


class VideoFile(Base):
    """Le fichier video principal (MKV/MP4/...) trouve dans le dossier du film."""
    __tablename__ = "video_files"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    container = Column(String, nullable=True)     # matroska, mp4, ...
    size_bytes = Column(Integer, nullable=False, default=0)
    duration_sec = Column(Float, nullable=True)

    video_codec = Column(String, nullable=True)     # h264, hevc, ...
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    video_bitrate = Column(Integer, nullable=True)  # bits/s

    scanned_at = Column(DateTime, default=datetime.utcnow)

    movie = relationship("Movie", back_populates="video_files")
    audio_tracks = relationship("AudioTrack", back_populates="video_file", cascade="all, delete-orphan")

    @property
    def resolution(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "?"


class AudioTrack(Base):
    """Une piste audio du fichier video (langue, encodage, bitrate)."""
    __tablename__ = "audio_tracks"

    id = Column(Integer, primary_key=True, index=True)
    video_file_id = Column(Integer, ForeignKey("video_files.id"), nullable=False)

    track_index = Column(Integer, nullable=False)
    language = Column(String, nullable=True)   # code ISO ou "und"
    title = Column(String, nullable=True)        # titre de piste s'il existe
    codec = Column(String, nullable=True)         # aac, ac3, dts, eac3, ...
    channels = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)      # bits/s

    video_file = relationship("VideoFile", back_populates="audio_tracks")


class Subtitle(Base):
    """Fichier de sous-titres optionnel present dans le dossier du film."""
    __tablename__ = "subtitles"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    language_guess = Column(String, nullable=True)  # devine depuis le nom de fichier

    movie = relationship("Movie", back_populates="subtitles")
