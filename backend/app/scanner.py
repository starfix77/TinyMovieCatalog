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
from app.filename_parser import parse_name, VIDEO_EXTENSIONS
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


def _sync_movie_from_disk(
    db: Session,
    library: Library,
    folder: Path,
    errors: list,
    compare_mode: str = "simple",
) -> tuple[Movie, bool]:
    """Cree ou met a jour un Movie a partir d'un dossier. Retourne (movie, was_created).

    compare_mode :
      - "simple" (par defaut, comportement historique) : le film est
        identifie uniquement par le nom du dossier ; le fichier video
        principal est systematiquement ré-analyse (ffprobe) a chaque scan.
      - "deep" : si le dossier existait deja en base, on compare en plus le
        nom du fichier MKV/MP4 sur le disque avec celui deja enregistre.
        S'il est identique, rien n'a change : l'analyse ffprobe est sautee.
        S'il differe (fichier renomme/remplace), la base est mise a jour et
        le fichier est ré-analyse via ffprobe.
    """
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

    db.flush()  # garantit movie.id (necessaire pour la recherche ci-dessous)

    existing_video_file = (
        db.query(VideoFile)
        .filter(VideoFile.movie_id == movie.id, VideoFile.filename == video_path.name)
        .first()
    )

    if compare_mode == "deep" and not was_created:
        if existing_video_file is not None:
            # Comparaison approfondie : meme nom de fichier video que lors du
            # dernier scan -> rien n'a change, on ne relance pas ffprobe.
            return movie, was_created
        # Le nom du fichier video principal a change depuis le dernier scan
        # (renommage, remplacement...) : on purge les anciennes entrees
        # video devenues obsoletes avant de mettre a jour la base.
        for stale_video_file in list(movie.video_files):
            db.delete(stale_video_file)
        db.flush()

    # --- Analyse ffprobe du fichier video ---
    stat = video_path.stat()
    video_file = existing_video_file
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



def _movie_for_candidate(db: Session, library: Library, title: str, year: int | None,
                         folder: Path, video_path: Path) -> tuple[Movie, bool]:
    """Regroupe les copies d'un même film, sans confondre les chemins des fichiers."""
    normalized = re.sub(r"\s+", " ", title).strip().casefold()
    candidates = db.query(Movie).filter(Movie.library_id == library.id).all()
    same_title = [m for m in candidates
                  if re.sub(r"\s+", " ", (m.title or "")).strip().casefold() == normalized]
    exact = [m for m in same_title if m.year == year]
    if exact:
        movie = exact[0]
    elif year is None and len(same_title) == 1:
        # Une année absente peut rejoindre un seul film déjà identifié sans année
        # ambiguë; si plusieurs années existent, on ne devine pas.
        movie = same_title[0]
    elif year is not None and len([m for m in same_title if m.year is None]) == 1 and len(same_title) == 1:
        movie = same_title[0]
    else:
        movie = None
    created = movie is None
    if movie is None:
        display_name = f"{title} ({year})" if year else title
        # Le champ historique folder_name est conservé pour compatibilité UI/API.
        existing_names = {m.folder_name for m in candidates}
        if display_name in existing_names:
            display_name = f"{display_name} [{video_path.parent.name}]"
        movie = Movie(library_id=library.id, folder_name=display_name,
                      folder_path=str(folder), title=title, year=year)
        db.add(movie)
        db.flush()
    elif not movie.video_files:
        # Garde le premier emplacement connu comme chemin canonique.
        movie.folder_path = str(folder)
    return movie, created


def _sync_candidate(db: Session, library: Library, video_path: Path, folder: Path,
                    parsed_title: str, parsed_year: int | None, errors: list[str],
                    compare_mode: str = "simple") -> tuple[Movie, bool]:
    title = parsed_title.strip() or video_path.stem
    movie, created = _movie_for_candidate(db, library, title, parsed_year, folder, video_path)
    existing = db.query(VideoFile).filter(VideoFile.movie_id == movie.id,
                                           VideoFile.filepath == str(video_path)).first()
    try:
        stat = video_path.stat()
    except OSError as exc:
        errors.append(f"Fichier vidéo inaccessible '{video_path}': {exc}")
        return movie, created

    if existing is not None and compare_mode == "deep":
        try:
            if existing.size_bytes == stat.st_size and existing.scanned_at and existing.scanned_at >= datetime.fromtimestamp(stat.st_mtime):
                return movie, created
        except (OSError, TypeError):
            pass
    video_file = existing or VideoFile(filename=video_path.name, filepath=str(video_path), size_bytes=stat.st_size)
    if existing is None:
        movie.video_files.append(video_file)
    video_file.filename = video_path.name
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
        video_file.frame_rate = probe.frame_rate
        video_file.color_depth = probe.color_depth
        video_file.hdr_info = probe.hdr_info
        video_file.stream_metadata_json = probe.stream_metadata_json
        video_file.ffprobe_status = "success"
        video_file.ffprobe_error = None
        video_file.audio_tracks.clear()
        for track in probe.audio_tracks:
            video_file.audio_tracks.append(AudioTrack(
                track_index=track.index, language=track.language, title=track.title,
                codec=track.codec, channels=track.channels, bitrate=track.bitrate))
    except Exception as exc:
        errors.append(f"ffprobe: {video_path}: {exc}")
    video_file.scanned_at = datetime.utcnow()

    # Sous-titres externes associés au même dossier; pas de suppression sur disque.
    subtitles = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in settings.subtitle_extensions] if folder.exists() else []
    video_base = video_path.stem.casefold()
    title_base = re.sub(r"[^a-z0-9]+", "", title.casefold())
    known = {sub.filepath for sub in movie.subtitles}
    for sub_path in subtitles:
        sub_base = sub_path.stem.casefold()
        # Accept exact basename or language-tagged variants such as Film.fr.srt.
        normalized_sub = re.sub(r"[._ -](fr|fre|en|eng|vf|vff|vfq|vostfr|multi)$", "", sub_base)
        normalized_video = re.sub(r"[._ -]+", "", video_base)
        normalized_sub_compact = re.sub(r"[._ -]+", "", normalized_sub)
        if normalized_sub_compact not in (normalized_video, title_base):
            continue
        if str(sub_path) not in known:
            movie.subtitles.append(Subtitle(filename=sub_path.name, filepath=str(sub_path),
                                            language_guess=_guess_subtitle_language(sub_path.name)))
    db.flush()

    if movie.tmdb_id is None and settings.tmdb_api_key:
        try:
            match = tmdb.search_movie(title, parsed_year)
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
                    errors.append(f"TMDb saga: {title}: {saga_exc}")
                if match.poster_path:
                    poster_filename = f"tmdb_{match.tmdb_id}.jpg"
                    dest = settings.thumbnails_dir / poster_filename
                    if not dest.exists():
                        tmdb.download_poster(match.poster_path, dest)
                    movie.poster_filename = poster_filename
        except Exception as exc:
            errors.append(f"TMDb: {title}: {exc}")
    return movie, created


def scan_library(db: Session, library: Library, progress_callback=None,
                 compare_mode: str = "simple", structure_mode: str = "mixed",
                 max_depth: int = 1) -> ScanResult:
    """Scan en lecture seule du disque: les noms ne fournissent que titre/année;
    les caractéristiques techniques proviennent uniquement de FFprobe."""
    root = Path(library.root_path)
    errors: list[str] = []
    if not root.exists() or not root.is_dir():
        return ScanResult(library_id=library.id, folders_scanned=0, movies_added=0,
                          movies_updated=0, movies_removed=0,
                          errors=[f"Dossier racine introuvable: {library.root_path}"])

    candidates: list[tuple[Path, Path, str, int | None]] = []
    seen_dirs: set[str] = set()
    folders_scanned = 0
    # Parcours contrôlé sans suivre les liens symboliques/jonctions.
    def walk(directory: Path, depth: int):
        nonlocal folders_scanned
        try:
            real = str(directory.resolve())
            if real in seen_dirs:
                return
            seen_dirs.add(real)
            children = list(directory.iterdir())
        except OSError as exc:
            errors.append(f"Répertoire inaccessible '{directory}': {exc}")
            return
        folders_scanned += 1
        for child in children:
            try:
                if child.is_symlink():
                    continue
                if child.is_dir():
                    if depth < max_depth:
                        walk(child, depth + 1)
                    continue
                if not child.is_file() or child.suffix.lower() not in settings.video_extensions:
                    continue
                parent_parse = parse_name(directory.name)
                if directory != root and structure_mode == "simple":
                    # En mode simple, le dossier parent est la source prioritaire.
                    folder_match = FOLDER_PATTERN.match(directory.name)
                    if not folder_match:
                        errors.append(f"Année/titre de dossier ambigu ou non conforme: {directory}")
                        parsed = parse_name(child.name)
                    else:
                        from app.filename_parser import ParsedName
                        parsed = ParsedName(folder_match.group("title").strip(), int(folder_match.group("year")))
                elif directory != root and FOLDER_PATTERN.match(directory.name):
                    folder_match = FOLDER_PATTERN.match(directory.name)
                    from app.filename_parser import ParsedName
                    parsed = ParsedName(folder_match.group("title").strip(), int(folder_match.group("year")))
                else:
                    if structure_mode == "simple":
                        continue
                    parsed = parse_name(child.name)
                if parsed.ambiguous_year:
                    errors.append(f"Année ambiguë dans '{child.name}'")
                candidates.append((child, directory, parsed.title, parsed.year))
            except OSError as exc:
                errors.append(f"Impossible de lire '{child}': {exc}")

    walk(root, 0)
    # Structure simple : seuls les dossiers directement sous la racine sont des films.
    if structure_mode == "simple":
        candidates = [c for c in candidates if c[1] != root and c[1].parent == root]

    # Les candidats dont le dossier fournit une année fiable sont traités en premier
    # afin que les copies sans année puissent rejoindre le film déjà identifié.
    candidates.sort(key=lambda item: (item[3] is None, item[1] == root, str(item[0]).casefold()))
    added, updated = 0, 0
    for index, (video_path, folder, title, year) in enumerate(candidates, start=1):
        try:
            movie, created = _sync_candidate(db, library, video_path, folder, title, year, errors, compare_mode)
            added += int(created)
            updated += int(not created)
        except Exception as exc:
            db.rollback()
            errors.append(f"Erreur de scan '{video_path}': {exc}")
        if progress_callback:
            progress_callback(index, len(candidates), str(video_path))
    # Les entrées absentes ne sont pas supprimées : elles restent récupérables si un
    # disque réseau est temporairement indisponible ou si le fichier est déplacé.
    discovered_paths = {str(item[0]) for item in candidates}
    for video in (db.query(VideoFile).join(Movie).filter(Movie.library_id == library.id).all()):
        if video.filepath not in discovered_paths and not Path(video.filepath).exists():
            errors.append(f"Fichier vidéo devenu indisponible: {video.filepath}")
    library.last_scanned_at = datetime.utcnow()
    refresh_library_fs_stats(library)
    db.commit()
    return ScanResult(library_id=library.id, folders_scanned=folders_scanned,
                      movies_added=added, movies_updated=updated, movies_removed=0, errors=errors)
