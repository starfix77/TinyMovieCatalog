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

    # Type de contenu de la bibliotheque : "movie" (films) ou "tv" (series TV).
    # Dans une bibliotheque "tv", chaque entree de la table movies est une
    # serie ; ses video_files sont les episodes.
    media_type = Column(String, nullable=False, default="movie", server_default="movie")

    # Rang d'affichage dans le bandeau de gauche (tri personnalise par
    # glisser-deposer). Une nouvelle bibliotheque recoit max + 1 (= derniere).
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")

    # Filesystem hebergeant le dossier racine, en octets (entiers 64 bits).
    # Rafraichi a la creation, a chaque scan et a l'ouverture de la page "Info".
    fs_total_size = Column(BigInteger, nullable=True)
    fs_free_size = Column(BigInteger, nullable=True)

    movies = relationship("Movie", back_populates="library", cascade="all, delete-orphan")
    # Journal des evenements de la bibliotheque (creation, modification, scans).
    logs = relationship("LibraryLog", back_populates="library", cascade="all, delete-orphan",
                        order_by="LibraryLog.id.desc()")
    # Note libre (zone de texte) de la bibliotheque : table "librairies_notes".
    note_entry = relationship("LibraryNote", back_populates="library", uselist=False,
                              cascade="all, delete-orphan")


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

    # Note moyenne TMDb (0-10, 1 decimale). None = pas encore recuperee ;
    # 0 = film sans vote sur TMDb.
    vote_average = Column(Float, nullable=True)
    # Note personnelle de 0 a 5 par pas de 0.5 (0 = non notee).
    rating_perso = Column(Float, nullable=False, default=0.0, server_default="0")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    library = relationship("Library", back_populates="movies")

    @property
    def media_type(self) -> str:
        """"movie" ou "tv", herite de la bibliotheque."""
        return (self.library.media_type if self.library is not None else None) or "movie"

    video_files = relationship("VideoFile", back_populates="movie", cascade="all, delete-orphan")
    subtitles = relationship("Subtitle", back_populates="movie", cascade="all, delete-orphan")
    saga = relationship("Saga")
    # Note libre (zone de texte) associee au film / a la serie : table "notes".
    note_entry = relationship("Note", back_populates="movie", uselist=False,
                              cascade="all, delete-orphan")


class Note(Base):
    """Note libre (texte multi-lignes) associee a un film ou a une serie.
    Une seule note par film ; la ligne n'existe que si une note est saisie."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    movie = relationship("Movie", back_populates="note_entry")


class LibraryNote(Base):
    """Note libre (texte multi-lignes) associee a une bibliotheque.
    Une seule note par bibliotheque ; la ligne n'existe que si une note est saisie."""
    __tablename__ = "librairies_notes"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    library = relationship("Library", back_populates="note_entry")


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
    frame_rate = Column(String, nullable=True)
    color_depth = Column(Integer, nullable=True)
    hdr_info = Column(Text, nullable=True)
    stream_metadata_json = Column(Text, nullable=True)
    ffprobe_status = Column(String, nullable=True)
    ffprobe_error = Column(Text, nullable=True)

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


class LibraryLog(Base):
    """Journal au niveau bibliotheque : un evenement = une ligne.

    action : "create" (creation), "update" (modification des proprietes :
    nom, type, dossier racine) ou "scan" (scan, avec ses options et ses totaux
    de fichiers ajoutes / modifies / supprimes)."""
    __tablename__ = "library_logs"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"), nullable=False, index=True)

    action = Column(String, nullable=False)             # create | update | scan
    details = Column(Text, nullable=True)                # ex. "Nom : A -> B" ou message d'erreur de scan

    # Options de scan (uniquement pour action == "scan")
    compare_mode = Column(String, nullable=True)         # simple | deep
    structure_mode = Column(String, nullable=True)       # simple | mixed
    max_depth = Column(Integer, nullable=True)

    files_added = Column(Integer, nullable=False, default=0, server_default="0")
    files_modified = Column(Integer, nullable=False, default=0, server_default="0")
    files_deleted = Column(Integer, nullable=False, default=0, server_default="0")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    library = relationship("Library", back_populates="logs")
    files = relationship("LibraryLogFile", back_populates="log", cascade="all, delete-orphan",
                         order_by="LibraryLogFile.id")


class LibraryLogFile(Base):
    """Journal au niveau fichier (film / episode) rattache a un evenement de
    scan. Les informations sont copiees (instantane) pour rester lisibles
    meme si le fichier ou le film change ou disparait ensuite."""
    __tablename__ = "library_log_files"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("library_logs.id"), nullable=False, index=True)
    library_id = Column(Integer, nullable=False, index=True)

    status = Column(String, nullable=False)              # created | modified | deleted

    movie_id = Column(Integer, nullable=True)
    movie_title = Column(String, nullable=True)
    movie_year = Column(Integer, nullable=True)
    poster_filename = Column(String, nullable=True)

    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False, index=True)
    size_bytes = Column(BigInteger, nullable=True)
    video_codec = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    audio_json = Column(Text, nullable=True)             # [{language, codec, bitrate, channels}]
    subtitles_json = Column(Text, nullable=True)         # [langue, ...]

    created_at = Column(DateTime, default=datetime.utcnow)

    log = relationship("LibraryLog", back_populates="files")
