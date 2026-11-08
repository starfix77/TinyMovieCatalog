"""
Journal des evenements d'une bibliotheque (table library_logs) et de ses
fichiers films / series (table library_log_files).

- Niveau bibliotheque : creation, modification des proprietes, scans (avec
  options de scan et totaux ajoutes / modifies / supprimes).
- Niveau fichier : statut (cree / modifie / supprime) + instantane des
  caracteristiques techniques du fichier au moment de l'evenement.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Library, LibraryLog, LibraryLogFile, Movie, VideoFile

STATUS_CREATED = "created"
STATUS_MODIFIED = "modified"
STATUS_DELETED = "deleted"


# ---------- Evenements de niveau bibliotheque ----------

def log_library_event(db: Session, library: Library, action: str,
                      details: Optional[str] = None, commit: bool = True) -> LibraryLog:
    """Ajoute un evenement "create" ou "update" au journal de la bibliotheque."""
    entry = LibraryLog(library_id=library.id, action=action, details=details,
                       created_at=datetime.utcnow())
    db.add(entry)
    if commit:
        db.commit()
    return entry


def describe_library_changes(old: dict, new: dict) -> Optional[str]:
    """Liste lisible des proprietes modifiees (None si rien n'a change)."""
    labels = {"name": "Nom", "media_type": "Type", "root_path": "Dossier racine"}
    types = {"movie": "Films", "tv": "Séries"}
    parts = []
    for key, label in labels.items():
        before, after = old.get(key), new.get(key)
        if before != after:
            if key == "media_type":
                before, after = types.get(before, before), types.get(after, after)
            parts.append(f"{label} : {before} → {after}")
    return " ; ".join(parts) if parts else None


# ---------- Instantanes de fichiers ----------

def video_signature(video: Optional[VideoFile]) -> Optional[tuple]:
    """Signature comparable d'un fichier video (pour detecter une modification)."""
    if video is None:
        return None
    audio = tuple(
        (t.track_index, t.language, t.codec, t.bitrate, t.channels)
        for t in sorted(video.audio_tracks, key=lambda t: t.track_index)
    )
    return (video.size_bytes, video.video_codec, video.width, video.height, audio)


def _audio_payload(video: VideoFile) -> list[dict]:
    return [
        {"language": t.language, "codec": t.codec, "bitrate": t.bitrate, "channels": t.channels}
        for t in sorted(video.audio_tracks, key=lambda t: t.track_index)
    ]


class ScanJournal:
    """Collecte les evenements fichiers d'un scan puis ecrit l'entree de journal.

    last_status memorise le dernier statut journalise de chaque chemin de
    fichier : cela evite de re-journaliser a chaque scan un fichier deja
    signale supprime, et permet de signaler son retour (statut "cree")."""

    def __init__(self, db: Session, library: Library):
        self.db = db
        self.library_id = library.id
        self.events: list[dict] = []
        self.last_status: dict[str, str] = {}
        rows = (db.query(LibraryLogFile.filepath, LibraryLogFile.status)
                .filter(LibraryLogFile.library_id == library.id)
                .order_by(LibraryLogFile.id).all())
        for filepath, status in rows:
            self.last_status[filepath] = status

    def was_deleted(self, filepath: str) -> bool:
        return self.last_status.get(filepath) == STATUS_DELETED

    def add(self, status: str, movie: Optional[Movie], video: VideoFile,
            subtitles: list[str]) -> None:
        self.events.append({
            "status": status,
            "movie_id": movie.id if movie is not None else None,
            "movie_title": movie.title if movie is not None else None,
            "movie_year": movie.year if movie is not None else None,
            "poster_filename": movie.poster_filename if movie is not None else None,
            "filename": video.filename,
            "filepath": video.filepath,
            "size_bytes": video.size_bytes,
            "video_codec": video.video_codec,
            "width": video.width,
            "height": video.height,
            "audio_json": json.dumps(_audio_payload(video), ensure_ascii=False),
            "subtitles_json": json.dumps(subtitles, ensure_ascii=False),
        })
        self.last_status[video.filepath] = status

    def add_deleted(self, video: VideoFile) -> None:
        """Fichier present en base mais disparu du disque."""
        movie = video.movie
        parent = str(Path(video.filepath).parent)
        subs = [(s.language_guess or "?") for s in (movie.subtitles if movie else [])
                if str(Path(s.filepath).parent) == parent]
        self.add(STATUS_DELETED, movie, video, subs)

    def write(self, compare_mode: str, structure_mode: str, max_depth: int,
              details: Optional[str] = None) -> LibraryLog:
        """Ecrit l'entree "scan" et ses lignes de detail (sans commit)."""
        entry = LibraryLog(
            library_id=self.library_id, action="scan", details=details,
            compare_mode=compare_mode, structure_mode=structure_mode, max_depth=max_depth,
            files_added=sum(1 for e in self.events if e["status"] == STATUS_CREATED),
            files_modified=sum(1 for e in self.events if e["status"] == STATUS_MODIFIED),
            files_deleted=sum(1 for e in self.events if e["status"] == STATUS_DELETED),
            created_at=datetime.utcnow(),
        )
        for event in self.events:
            entry.files.append(LibraryLogFile(library_id=self.library_id, **event))
        self.db.add(entry)
        return entry
