"""
Scan d'une bibliotheque : parcourt le dossier racine, detecte chaque
sous-dossier "Titre du film (Annee)", analyse le fichier video avec ffprobe,
et enrichit les metadonnees via TheMovieDB.
"""
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import tmdb, ffprobe_utils
from app.fs_utils import refresh_library_fs_stats
from app.config import settings
from app.models import Library, Movie, VideoFile, AudioTrack, Subtitle, Saga, SagaMovie
from app.schemas import ScanResult

# "Le Titre du Film (2010)" -> groupes: titre / annee
FOLDER_PATTERN = re.compile(r"^(?P<title>.+?)\s*\((?P<year>\d{4})\)\s*$")

SUBTITLE_LANG_HINTS = {
    "fr": "fr", "fre": "fr", "french": "fr", "vf": "fr", "vff": "fr",
    "en": "en", "eng": "en", "english": "en", "vo": "en", "vostfr": "en",
}


def parse_folder_name(folder_name: str):
    match = FOLDER_PATTERN.match(folder_name)
    if match:
        return match.group("title").strip(), int(match.group("year"))
    return folder_name.strip(), None


def _guess_subtitle_language(filename: str) -> str | None:
    stem = Path(filename).stem.lower()
    for token in re.split(r"[.\-_ ]+", stem):
        if token in SUBTITLE_LANG_HINTS:
            return SUBTITLE_LANG_HINTS[token]
    return None


def _find_main_video_file(folder: Path) -> Path | None:
    """Retourne le plus gros fichier video du dossier (le film), en ignorant
    les extraits/bandes-annonces si un fichier nettement plus gros existe."""
    candidates = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in settings.video_extensions
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_size)


def _find_subtitles(folder: Path) -> list[Path]:
    return [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in settings.subtitle_extensions
    ]


def sync_saga_for_match(db: Session, match) -> "int | None":
    """Cree/retrouve la Saga TMDb associee a un match de film, synchronise le
    detail complet de la collection (liste des films, affiche) au besoin, et
    retourne l'id local de la Saga (ou None si le film n'appartient a aucune
    collection TMDb)."""
    if not match.collection_id:
        return None

    saga = db.query(Saga).filter(Saga.tmdb_collection_id == match.collection_id).first()
    if saga is None:
        saga = Saga(tmdb_collection_id=match.collection_id, name=match.collection_name or "?")
        db.add(saga)
        db.flush()

    if saga.synced_at is None:
        _sync_saga_details(db, saga)

    return saga.id


def _sync_saga_details(db: Session, saga: Saga) -> None:
    """Recupere aupres de TMDb la liste complete des films de la collection
    (les 'parts', presents ou non dans une bibliotheque locale) et telecharge
    les affiches manquantes."""
    data = tmdb.fetch_collection(saga.tmdb_collection_id)

    saga.name = data.get("name") or saga.name
    saga.overview = data.get("overview") or None

    poster_path = data.get("poster_path")
    if poster_path:
        poster_filename = f"saga_{saga.tmdb_collection_id}.jpg"
        dest = settings.thumbnails_dir / poster_filename
        if not dest.exists():
            tmdb.download_poster(poster_path, dest)
        saga.poster_filename = poster_filename

    existing_by_tmdb_id = {entry.tmdb_movie_id: entry for entry in saga.entries}

    for index, part in enumerate(data.get("parts", [])):
        tmdb_movie_id = part.get("id")
        if tmdb_movie_id is None:
            continue

        entry = existing_by_tmdb_id.get(tmdb_movie_id)
        if entry is None:
            entry = SagaMovie(saga_id=saga.id, tmdb_movie_id=tmdb_movie_id, title="?")
            db.add(entry)
            existing_by_tmdb_id[tmdb_movie_id] = entry

        entry.title = part.get("title") or entry.title
        entry.release_date = part.get("release_date") or None
        entry.order_index = index

        # Meme convention de nom que l'affiche "principale" d'un Movie
        # (tmdb_<id>.jpg) : si ce film est deja dans une bibliotheque, son
        # affiche est reutilisee telle quelle, sans re-telechargement.
        part_poster_path = part.get("poster_path")
        if part_poster_path and not entry.poster_filename:
            poster_filename = f"tmdb_{tmdb_movie_id}.jpg"
            dest = settings.thumbnails_dir / poster_filename
            if not dest.exists():
                tmdb.download_poster(part_poster_path, dest)
            entry.poster_filename = poster_filename

    saga.synced_at = datetime.utcnow()
    db.flush()


def _sync_movie_from_disk(db: Session, library: Library, folder: Path, errors: list) -> tuple[Movie, bool]:
    """Cree ou met a jour un Movie a partir d'un dossier. Retourne (movie, was_created)."""
    title, year = parse_folder_name(folder.name)

    movie = (
        db.query(Movie)
        .filter(Movie.library_id == library.id, Movie.folder_name == folder.name)
        .first()
    )
    was_created = movie is None
    if movie is None:
        movie = Movie(library_id=library.id, folder_name=folder.name)
        db.add(movie)

    movie.folder_path = str(folder)
    movie.title = title
    movie.year = year

    video_path = _find_main_video_file(folder)
    if video_path is None:
        errors.append(f"Aucun fichier video trouve dans '{folder.name}'")
        db.flush()
        return movie, was_created

    # --- Analyse ffprobe du fichier video ---
    stat = video_path.stat()
    video_file = (
        db.query(VideoFile)
        .filter(VideoFile.movie_id == movie.id, VideoFile.filename == video_path.name)
        .first()
        if movie.id else None
    )
    if video_file is None:
        video_file = VideoFile(filename=video_path.name)
        movie.video_files.append(video_file)

    video_file.filepath = str(video_path)
    video_file.size_bytes = stat.st_size

    try:
        probe = ffprobe_utils.probe_file(str(video_path))
        video_file.container = probe.container
        video_file.duration_sec = probe.duration_sec
        video_file.video_codec = probe.video_codec
        video_file.width = probe.width
        video_file.height = probe.height
        video_file.video_bitrate = probe.video_bitrate

        # Remplace les pistes audio existantes par le resultat courant
        video_file.audio_tracks.clear()
        for track in probe.audio_tracks:
            video_file.audio_tracks.append(
                AudioTrack(
                    track_index=track.index,
                    language=track.language,
                    title=track.title,
                    codec=track.codec,
                    channels=track.channels,
                    bitrate=track.bitrate,
                )
            )
    except Exception as exc:  # ffprobe absent, fichier corrompu, etc.
        errors.append(f"ffprobe: {folder.name}: {exc}")

    video_file.scanned_at = datetime.utcnow()

    # --- Sous-titres ---
    movie.subtitles.clear()
    for sub_path in _find_subtitles(folder):
        movie.subtitles.append(
            Subtitle(
                filename=sub_path.name,
                filepath=str(sub_path),
                language_guess=_guess_subtitle_language(sub_path.name),
            )
        )

    db.flush()

    # --- Enrichissement TheMovieDB (uniquement si pas deja synchronise) ---
    if movie.tmdb_id is None and settings.tmdb_api_key:
        try:
            match = tmdb.search_movie(title, year)
            if match:
                movie.tmdb_id = match.tmdb_id
                movie.original_title = match.original_title
                movie.overview = match.overview
                movie.release_date = match.release_date
                movie.genres = match.genres
                movie.cast = match.cast_json
                movie.tmdb_synced_at = datetime.utcnow()

                try:
                    movie.saga_id = sync_saga_for_match(db, match)
                except Exception as saga_exc:
                    errors.append(f"TMDb saga: {folder.name}: {saga_exc}")

                if match.poster_path:
                    poster_filename = f"tmdb_{match.tmdb_id}.jpg"
                    dest = settings.thumbnails_dir / poster_filename
                    if not dest.exists():
                        tmdb.download_poster(match.poster_path, dest)
                    movie.poster_filename = poster_filename
            else:
                errors.append(f"TMDb: aucun resultat pour '{title}' ({year})")
        except Exception as exc:
            errors.append(f"TMDb: {folder.name}: {exc}")

    return movie, was_created


def scan_library(db: Session, library: Library, progress_callback=None) -> ScanResult:
    root = Path(library.root_path)
    errors: list[str] = []

    if not root.exists() or not root.is_dir():
        return ScanResult(
            library_id=library.id, folders_scanned=0, movies_added=0,
            movies_updated=0, movies_removed=0,
            errors=[f"Dossier racine introuvable: {library.root_path}"],
        )

    folders = [f for f in root.iterdir() if f.is_dir()]
    seen_folder_names = set()
    added, updated = 0, 0
    total_folders = len(folders)
    if progress_callback:
        progress_callback(0, total_folders, None)

    for index, folder in enumerate(folders, start=1):
        seen_folder_names.add(folder.name)
        existed = (
            db.query(Movie)
            .filter(Movie.library_id == library.id, Movie.folder_name == folder.name)
            .first()
            is not None
        )
        _sync_movie_from_disk(db, library, folder, errors)
        if existed:
            updated += 1
        else:
            added += 1
        if progress_callback:
            progress_callback(index, total_folders, folder.name)

    # Supprime de la base les films dont le dossier n'existe plus sur le disque
    removed = 0
    existing_movies = db.query(Movie).filter(Movie.library_id == library.id).all()
    for movie in existing_movies:
        if movie.folder_name not in seen_folder_names:
            db.delete(movie)
            removed += 1

    library.last_scanned_at = datetime.utcnow()
    refresh_library_fs_stats(library)
    db.commit()

    return ScanResult(
        library_id=library.id,
        folders_scanned=len(folders),
        movies_added=added,
        movies_updated=updated,
        movies_removed=removed,
        errors=errors,
    )
