from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class Library(Base):
    """Une bibliotheque = un dossier racine contenant des sous-dossiers de films."""
    __tablename__ = "libraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    root_path = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scanned_at = Column(DateTime, nullable=True)

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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    library = relationship("Library", back_populates="movies")
    video_files = relationship("VideoFile", back_populates="movie", cascade="all, delete-orphan")
    subtitles = relationship("Subtitle", back_populates="movie", cascade="all, delete-orphan")


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
