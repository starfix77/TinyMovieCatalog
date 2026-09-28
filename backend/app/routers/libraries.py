from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Library, Movie
from app.schemas import LibraryCreate, LibraryInfoOut, LibraryOut, ScanRequest, ScanResult
from app.fs_utils import refresh_library_fs_stats
from app.scan_manager import scan_manager

router = APIRouter(prefix="/api/libraries", tags=["libraries"])


@router.get("", response_model=list[LibraryOut])
def list_libraries(db: Session = Depends(get_db)):
    libraries = db.query(Library).order_by(Library.name).all()
    counts = dict(
        db.query(Movie.library_id, func.count(Movie.id)).group_by(Movie.library_id).all()
    )
    out = []
    for lib in libraries:
        item = LibraryOut.model_validate(lib)
        item.movie_count = counts.get(lib.id, 0)
        out.append(item)
    return out


@router.post("", response_model=LibraryOut, status_code=201)
def create_library(payload: LibraryCreate, db: Session = Depends(get_db)):
    existing = db.query(Library).filter(Library.root_path == payload.root_path).first()
    if existing:
        raise HTTPException(409, "Une bibliotheque pointe deja vers ce dossier racine.")

    library = Library(name=payload.name.strip(), root_path=payload.root_path.strip())
    refresh_library_fs_stats(library)
    db.add(library)
    db.commit()
    db.refresh(library)

    out = LibraryOut.model_validate(library)
    out.movie_count = 0
    return out


def _as_utc(value: datetime | None) -> datetime | None:
    """Les dates sont stockees en UTC naif (datetime.utcnow) : on les marque
    explicitement UTC pour que le JSON contienne un "Z" et que le navigateur
    les convertisse correctement en heure locale."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


@router.get("/{library_id}/info", response_model=LibraryInfoOut)
def library_info(library_id: int, db: Session = Depends(get_db)):
    library = db.get(Library, library_id)
    if not library:
        raise HTTPException(404, "Bibliotheque introuvable.")

    # L'espace libre varie en permanence : on relit le filesystem a chaque
    # ouverture de la page et on met la base a jour.
    fs_available = refresh_library_fs_stats(library)
    if fs_available:
        db.commit()

    movie_count = db.query(func.count(Movie.id)).filter(Movie.library_id == library.id).scalar()

    return LibraryInfoOut(
        id=library.id,
        name=library.name,
        root_path=library.root_path,
        movie_count=movie_count or 0,
        created_at=_as_utc(library.created_at),
        last_scanned_at=_as_utc(library.last_scanned_at),
        fs_total_size=library.fs_total_size,
        fs_free_size=library.fs_free_size,
        fs_available=fs_available,
    )


@router.delete("/{library_id}", status_code=204)
def delete_library(library_id: int, db: Session = Depends(get_db)):
    library = db.get(Library, library_id)
    if not library:
        raise HTTPException(404, "Bibliotheque introuvable.")
    db.delete(library)  # cascade -> movies / video_files / audio_tracks / subtitles
    db.commit()
    return None


@router.post("/{library_id}/scan")
async def trigger_scan(library_id: int, payload: ScanRequest = ScanRequest(), db: Session = Depends(get_db)):
    library = db.get(Library, library_id)
    if not library:
        raise HTTPException(404, "Bibliotheque introuvable.")
    compare_mode = payload.compare_mode if payload.compare_mode in ("simple", "deep") else "simple"
    state = await scan_manager.start(library_id, compare_mode)
    return scan_manager._serialize(state)


@router.websocket("/{library_id}/scan/ws")
async def scan_progress(library_id: int, websocket: WebSocket):
    await websocket.accept()
    await scan_manager.connect(library_id, websocket)
    try:
        # Les mises a jour sont poussees par le ScanManager.
        # On garde la connexion ouverte en attendant une fermeture client.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await scan_manager.disconnect(library_id, websocket)
    except Exception:
        await scan_manager.disconnect(library_id, websocket)
