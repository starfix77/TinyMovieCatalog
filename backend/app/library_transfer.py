"""
Export / import d'une bibliotheque.

Format d'echange : un fichier JSON (UTF-8) unique, extension recommandee
``.tmcatalog.json``. Pourquoi JSON :
  * texte lisible et diffable, independant de la plateforme (Windows/Linux/macOS) ;
  * versionne (``format`` + ``version``) : le format peut evoluer sans casser
    les anciens exports ;
  * se lit/ecrit nativement des deux cotes (Python et navigateur), sans
    dependance supplementaire ;
  * contrairement a une copie du fichier SQLite, il ne contient que la
    bibliotheque choisie et se fusionne dans une base existante.

Les vignettes ne sont PAS embarquees (elles se retelechargent depuis TMDb) :
l'export ne contient que leurs noms de fichier ; a l'import, celles qui
manquent dans data/thumbnails sont retelechargees en arriere-plan.

Ce module ne depend pas de FastAPI : il travaille sur une Session SQLAlchemy.
"""
from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from app import tmdb
from app.config import settings
from app.models import (
    AudioTrack, Library, Movie, Saga, SagaMovie, Subtitle, VideoFile,
)

FORMAT_NAME = "TinyMovieCatalog.library"
FORMAT_VERSION = 1

# Colonnes exportees pour chaque table (cles etrangeres / id exclus : elles
# sont reconstruites a l'import).
LIBRARY_FIELDS = ("name", "root_path", "media_type", "created_at", "last_scanned_at",
                  "fs_total_size", "fs_free_size")
SAGA_FIELDS = ("tmdb_collection_id", "name", "overview", "poster_filename", "synced_at")
SAGA_MOVIE_FIELDS = ("tmdb_movie_id", "title", "release_date", "poster_filename", "order_index")
MOVIE_FIELDS = ("folder_name", "folder_path", "title", "year", "tmdb_id", "original_title",
                "overview", "release_date", "poster_filename", "cast", "genres",
                "tmdb_synced_at", "vote_average", "rating_perso", "created_at", "updated_at")
VIDEO_FIELDS = ("filename", "filepath", "container", "size_bytes", "duration_sec", "video_codec",
                "width", "height", "video_bitrate", "frame_rate", "color_depth", "hdr_info",
                "stream_metadata_json", "ffprobe_status", "ffprobe_error", "scanned_at")
AUDIO_FIELDS = ("track_index", "language", "title", "codec", "channels", "bitrate")
SUBTITLE_FIELDS = ("filename", "filepath", "language_guess")

_DATETIME_FIELDS = {"created_at", "last_scanned_at", "synced_at", "tmdb_synced_at",
                    "updated_at", "scanned_at"}

# Un nom de vignette importe est utilise tel quel comme nom de fichier dans
# data/thumbnails : on refuse tout ce qui ressemble a un chemin.
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


class ImportFormatError(ValueError):
    """Fichier d'import invalide ou non supporte."""


class ImportConflictError(ValueError):
    """Le dossier racine est deja utilise par une autre bibliotheque."""


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

def _dump(obj: Any, fields: tuple[str, ...]) -> dict:
    out = {}
    for name in fields:
        value = getattr(obj, name)
        out[name] = value.isoformat() if isinstance(value, datetime) else value
    return out


def export_library(db: Session, library: Library) -> dict:
    """Serialise toute la bibliotheque (films, fichiers video, pistes audio,
    sous-titres, sagas associees) dans un dict JSON-compatible."""
    movies = (
        db.query(Movie)
        .options(joinedload(Movie.video_files).joinedload(VideoFile.audio_tracks),
                 joinedload(Movie.subtitles),
                 joinedload(Movie.saga).joinedload(Saga.entries))
        .filter(Movie.library_id == library.id)
        .order_by(Movie.id)
        .all()
    )

    sagas: dict[int, Saga] = {}
    movies_out = []
    for movie in movies:
        item = _dump(movie, MOVIE_FIELDS)
        item["saga_tmdb_collection_id"] = movie.saga.tmdb_collection_id if movie.saga else None
        if movie.saga:
            sagas[movie.saga.id] = movie.saga
        item["video_files"] = []
        for video in movie.video_files:
            v = _dump(video, VIDEO_FIELDS)
            v["audio_tracks"] = [
                _dump(t, AUDIO_FIELDS) for t in sorted(video.audio_tracks, key=lambda t: t.track_index)
            ]
            item["video_files"].append(v)
        item["subtitles"] = [_dump(s, SUBTITLE_FIELDS) for s in movie.subtitles]
        movies_out.append(item)

    sagas_out = []
    for saga in sorted(sagas.values(), key=lambda s: s.tmdb_collection_id):
        s = _dump(saga, SAGA_FIELDS)
        s["movies"] = [
            _dump(e, SAGA_MOVIE_FIELDS)
            for e in sorted(saga.entries, key=lambda e: (e.order_index is None, e.order_index or 0))
        ]
        sagas_out.append(s)

    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "exported_at": datetime.utcnow().isoformat(),
        "library": _dump(library, LIBRARY_FIELDS),
        "sagas": sagas_out,
        "movies": movies_out,
    }


def export_filename(library: Library) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", library.name).strip("_") or "bibliotheque"
    return f"{slug}.tmcatalog.json"


# --------------------------------------------------------------------------
# Import
# --------------------------------------------------------------------------

def validate_export(data: Any) -> None:
    if not isinstance(data, dict) or data.get("format") != FORMAT_NAME:
        raise ImportFormatError("Ce fichier n'est pas un export de bibliotheque TinyMovieCatalog.")
    version = data.get("version")
    if not isinstance(version, int) or version < 1:
        raise ImportFormatError("Version de format invalide.")
    if version > FORMAT_VERSION:
        raise ImportFormatError(
            f"Ce fichier utilise le format v{version}, plus recent que celui supporte "
            f"par cette application (v{FORMAT_VERSION}). Mettez l'application a jour."
        )
    lib = data.get("library")
    if not isinstance(lib, dict) or not str(lib.get("name") or "").strip() \
            or not str(lib.get("root_path") or "").strip():
        raise ImportFormatError("Informations de bibliotheque manquantes (nom / dossier racine).")
    if lib.get("media_type") not in ("movie", "tv"):
        raise ImportFormatError("Type de bibliotheque invalide (attendu : movie ou tv).")
    if not isinstance(data.get("movies"), list) or not isinstance(data.get("sagas", []), list):
        raise ImportFormatError("Contenu du fichier invalide (films / sagas).")


def _values(raw: dict, fields: tuple[str, ...]) -> dict:
    """Extrait uniquement les colonnes connues (les cles inconnues sont ignorees)
    et reconvertit les dates ISO."""
    out = {}
    for name in fields:
        if name not in raw:
            continue
        value = raw[name]
        if name in _DATETIME_FIELDS and isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                value = None
        out[name] = value
    return out


def _safe_poster(name: Optional[str]) -> Optional[str]:
    return name if isinstance(name, str) and _SAFE_FILENAME_RE.match(name) else None


def _rebase(path: Optional[str], old_root: str, new_root: str) -> Optional[str]:
    """Remplace le dossier racine d'origine par le nouveau dans un chemin absolu."""
    if not path or old_root == new_root:
        return path
    old = old_root.rstrip("/\\")
    if not path.startswith(old):
        return path
    rest = path[len(old):]
    new = new_root.rstrip("/\\")
    sep = "\\" if ("\\" in new and "/" not in new) else "/"
    return new + rest.replace("\\", sep).replace("/", sep)


def library_summary(data: dict) -> dict:
    """Resume d'un export (utilise pour l'affichage avant import)."""
    validate_export(data)
    return {
        "name": data["library"]["name"],
        "root_path": data["library"]["root_path"],
        "media_type": data["library"]["media_type"],
        "movie_count": len(data["movies"]),
    }


def import_library(db: Session, data: dict, name: Optional[str] = None,
                   root_path: Optional[str] = None) -> tuple[Library, dict]:
    """Cree une nouvelle bibliotheque a partir d'un export.

    Retourne (bibliotheque, stats). Leve ImportFormatError / ImportConflictError.
    Toute l'operation est atomique : en cas d'erreur, rien n'est ecrit.
    """
    validate_export(data)
    src = data["library"]
    new_name = (name or src["name"]).strip()
    new_root = (root_path or src["root_path"]).strip()
    if not new_name or not new_root:
        raise ImportFormatError("Le nom et le dossier racine sont obligatoires.")
    if db.query(Library).filter(Library.root_path == new_root).first():
        raise ImportConflictError("Une bibliotheque pointe deja vers ce dossier racine.")
    old_root = src["root_path"]

    try:
        library = Library(**{
            **_values(src, LIBRARY_FIELDS),
            "name": new_name,
            "root_path": new_root,
        })
        db.add(library)
        db.flush()

        # Sagas : reutilise celles deja connues (cle = collection TMDb).
        saga_ids: dict[int, int] = {}
        sagas_created = 0
        for raw in data.get("sagas", []):
            cid = raw.get("tmdb_collection_id")
            if not isinstance(cid, int):
                continue
            saga = db.query(Saga).filter(Saga.tmdb_collection_id == cid).first()
            if saga is None:
                values = _values(raw, SAGA_FIELDS)
                values["poster_filename"] = _safe_poster(values.get("poster_filename"))
                values["name"] = values.get("name") or "?"
                saga = Saga(**values)
                db.add(saga)
                db.flush()
                sagas_created += 1
            known = {e.tmdb_movie_id for e in saga.entries}
            for entry in raw.get("movies", []):
                if entry.get("tmdb_movie_id") in known or not isinstance(entry.get("tmdb_movie_id"), int):
                    continue
                values = _values(entry, SAGA_MOVIE_FIELDS)
                values["poster_filename"] = _safe_poster(values.get("poster_filename"))
                values["title"] = values.get("title") or "?"
                db.add(SagaMovie(saga_id=saga.id, **values))
            saga_ids[cid] = saga.id

        seen_folders: set[str] = set()
        movies_count = 0
        for raw in data["movies"]:
            values = _values(raw, MOVIE_FIELDS)
            folder = values.get("folder_name")
            if not folder or folder in seen_folders:
                continue
            seen_folders.add(folder)
            values["title"] = values.get("title") or folder
            values["folder_path"] = _rebase(values.get("folder_path"), old_root, new_root) or ""
            values["poster_filename"] = _safe_poster(values.get("poster_filename"))
            if values.get("rating_perso") is None:
                values["rating_perso"] = 0.0

            movie = Movie(library_id=library.id,
                          saga_id=saga_ids.get(raw.get("saga_tmdb_collection_id")),
                          **values)
            db.add(movie)
            db.flush()
            movies_count += 1

            for rv in raw.get("video_files", []):
                v = _values(rv, VIDEO_FIELDS)
                if not v.get("filename"):
                    continue
                v["filepath"] = _rebase(v.get("filepath"), old_root, new_root) or v["filename"]
                v["size_bytes"] = v.get("size_bytes") or 0
                video = VideoFile(movie_id=movie.id, **v)
                db.add(video)
                db.flush()
                for rt in rv.get("audio_tracks", []):
                    t = _values(rt, AUDIO_FIELDS)
                    t["track_index"] = t.get("track_index") or 0
                    db.add(AudioTrack(video_file_id=video.id, **t))

            for rs in raw.get("subtitles", []):
                s = _values(rs, SUBTITLE_FIELDS)
                if not s.get("filename"):
                    continue
                s["filepath"] = _rebase(s.get("filepath"), old_root, new_root) or s["filename"]
                db.add(Subtitle(movie_id=movie.id, **s))

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(library)
    return library, {"movies_imported": movies_count, "sagas_imported": len(saga_ids)}


# --------------------------------------------------------------------------
# Restauration des vignettes manquantes
# --------------------------------------------------------------------------

def build_thumbnail_tasks(data: dict) -> list[dict]:
    """Liste (dedoublonnee) des vignettes referencees par l'export et absentes
    de data/thumbnails."""
    media_type = data["library"]["media_type"]
    tasks: dict[str, dict] = {}

    def add(filename: Optional[str], **spec) -> None:
        fn = _safe_poster(filename)
        if not fn or fn in tasks or (settings.thumbnails_dir / fn).exists():
            return
        tasks[fn] = {"filename": fn, **spec}

    for saga in data.get("sagas", []):
        cid = saga.get("tmdb_collection_id")
        if not isinstance(cid, int):
            continue
        add(saga.get("poster_filename"), kind="saga", collection_id=cid)
        for entry in saga.get("movies", []):
            add(entry.get("poster_filename"), kind="saga_movie", collection_id=cid,
                tmdb_id=entry.get("tmdb_movie_id"))
    for movie in data["movies"]:
        add(movie.get("poster_filename"), kind="movie", tmdb_id=movie.get("tmdb_id"),
            media_type=media_type)
    return list(tasks.values())


@dataclass
class ThumbnailJob:
    id: str
    library_id: int
    total: int
    done: int = 0
    downloaded: int = 0
    failed: int = 0
    status: str = "running"   # running | completed
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "library_id": self.library_id, "status": self.status,
            "total": self.total, "done": self.done, "downloaded": self.downloaded,
            "failed": self.failed, "errors": self.errors[:20],
        }


_jobs: dict[str, ThumbnailJob] = {}
_jobs_lock = threading.Lock()

_MOVIE_POSTER_RE = re.compile(r"^tmdb_(?:tv_)?(\d+)(?:_(.+))?\.jpg$")


def get_job(job_id: str) -> Optional[ThumbnailJob]:
    return _jobs.get(job_id)


def start_thumbnail_job(library_id: int, tasks: list[dict]) -> Optional[ThumbnailJob]:
    """Lance le telechargement en arriere-plan. Retourne None s'il n'y a rien a faire."""
    if not tasks:
        return None
    job = ThumbnailJob(id=uuid.uuid4().hex, library_id=library_id, total=len(tasks))
    with _jobs_lock:
        # Garde l'historique court : on oublie les anciens jobs termines.
        for old_id in [j.id for j in _jobs.values() if j.status == "completed"][:-9]:
            _jobs.pop(old_id, None)
        _jobs[job.id] = job
    threading.Thread(target=_run_thumbnail_job, args=(job, tasks), daemon=True).start()
    return job


def _download_variant(variant: str, dest) -> bool:
    for ext in (".jpg", ".png", ".jpeg"):
        if tmdb.download_poster(f"/{variant}{ext}", dest):
            return True
    return False


def _run_thumbnail_job(job: ThumbnailJob, tasks: list[dict]) -> None:
    collections: dict[int, Optional[dict]] = {}
    api_key_missing_reported = False

    def collection(cid: int) -> Optional[dict]:
        if cid not in collections:
            try:
                collections[cid] = tmdb.fetch_collection(cid)
            except Exception:
                collections[cid] = None
        return collections[cid]

    def fail(message: str) -> None:
        job.failed += 1
        if len(job.errors) < 50:
            job.errors.append(message)

    # Les vignettes de sagas d'abord : une seule requete par collection.
    tasks = sorted(tasks, key=lambda t: 0 if t["kind"] in ("saga", "saga_movie") else 1)

    for task in tasks:
        filename = task["filename"]
        dest = settings.thumbnails_dir / filename
        try:
            ok = False
            if dest.exists():
                ok = True
            elif task["kind"] == "saga":
                data = collection(task["collection_id"])
                ok = bool(data and tmdb.download_poster(data.get("poster_path"), dest))
            elif task["kind"] == "saga_movie":
                data = collection(task["collection_id"])
                part = next((p for p in (data or {}).get("parts", [])
                             if p.get("id") == task.get("tmdb_id")), None)
                if part and tmdb.download_poster(part.get("poster_path"), dest):
                    ok = True
                elif task.get("tmdb_id"):
                    match = tmdb._fetch_movie_details(task["tmdb_id"], "movie")
                    ok = tmdb.download_poster(match.poster_path, dest)
            else:  # film / serie
                m = _MOVIE_POSTER_RE.match(filename)
                variant = m.group(2) if m else None
                if variant:
                    # Pochette choisie manuellement : le nom contient le chemin TMDb.
                    ok = _download_variant(variant, dest)
                else:
                    tmdb_id = task.get("tmdb_id") or (int(m.group(1)) if m else None)
                    if tmdb_id:
                        match = tmdb._fetch_movie_details(tmdb_id, task.get("media_type", "movie"))
                        ok = tmdb.download_poster(match.poster_path, dest)
            if ok:
                job.downloaded += 1
            else:
                fail(f"{filename} : vignette introuvable sur TMDb.")
        except tmdb.TmdbNotConfiguredError:
            if not api_key_missing_reported:
                api_key_missing_reported = True
                if len(job.errors) < 50:
                    job.errors.append("Cle API TMDb non configuree (TMDB_API_KEY dans backend/.env) : "
                                      "certaines vignettes n'ont pas pu etre telechargees.")
            job.failed += 1
        except Exception as exc:
            fail(f"{filename} : {exc}")
        finally:
            job.done += 1

    job.status = "completed"
