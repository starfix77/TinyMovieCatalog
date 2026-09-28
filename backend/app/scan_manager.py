"""
Gestionnaire de scans asynchrones et de leur progression.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.database import SessionLocal
from app.models import Library
from app.scanner import scan_library


@dataclass
class ScanState:
    library_id: int
    status: str = "queued"  # queued, running, completed, failed
    current: int = 0
    total: int = 0
    current_folder: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    clients: set = field(default_factory=set)


class ScanManager:
    def __init__(self):
        self._states: dict[int, ScanState] = {}
        self._lock = asyncio.Lock()

    async def start(self, library_id: int) -> ScanState:
        async with self._lock:
            state = self._states.get(library_id)
            if state and state.status in ("queued", "running"):
                return state
            state = ScanState(library_id=library_id, status="queued")
            self._states[library_id] = state
        asyncio.create_task(self._run(state))
        return state

    async def get(self, library_id: int) -> Optional[ScanState]:
        async with self._lock:
            return self._states.get(library_id)

    async def _update(self, state: ScanState, **values):
        async with self._lock:
            for key, value in values.items():
                setattr(state, key, value)
            clients = list(state.clients)
        message = self._serialize(state)
        if clients:
            await asyncio.gather(
                *(self._send(client, message) for client in clients),
                return_exceptions=True,
            )

    async def _send(self, websocket, message):
        try:
            await websocket.send_json(message)
        except Exception:
            async with self._lock:
                for state in self._states.values():
                    state.clients.discard(websocket)

    @staticmethod
    def _serialize(state: ScanState) -> dict:
        return {
            "library_id": state.library_id,
            "status": state.status,
            "current": state.current,
            "total": state.total,
            "progress": round((state.current / state.total) * 100) if state.total else (
                100 if state.status == "completed" else 0
            ),
            "current_folder": state.current_folder,
            "result": state.result,
            "error": state.error,
            "started_at": state.started_at,
            "finished_at": state.finished_at,
        }

    async def _run(self, state: ScanState):
        await self._update(
            state,
            status="running",
            started_at=datetime.utcnow().isoformat(),
        )

        db = SessionLocal()
        try:
            library = db.get(Library, state.library_id)
            if not library:
                raise RuntimeError("Bibliothèque introuvable.")

            loop = asyncio.get_running_loop()

            def progress(current, total, folder):
                asyncio.run_coroutine_threadsafe(
                    self._update(
                        state,
                        current=current,
                        total=total,
                        current_folder=folder,
                    ),
                    loop,
                )

            result = await asyncio.to_thread(scan_library, db, library, progress)
            await self._update(
                state,
                status="completed",
                current=result.folders_scanned,
                total=result.folders_scanned,
                current_folder=None,
                result=result.model_dump(),
                finished_at=datetime.utcnow().isoformat(),
            )
        except Exception as exc:
            db.rollback()
            await self._update(
                state,
                status="failed",
                error=str(exc),
                finished_at=datetime.utcnow().isoformat(),
            )
        finally:
            db.close()

    async def connect(self, library_id: int, websocket):
        state = await self.get(library_id)
        if state is None:
            await websocket.send_json({
                "library_id": library_id,
                "status": "idle",
                "current": 0,
                "total": 0,
                "progress": 0,
                "current_folder": None,
            })
            return
        async with self._lock:
            state.clients.add(websocket)
        await websocket.send_json(self._serialize(state))

    async def disconnect(self, library_id: int, websocket):
        async with self._lock:
            state = self._states.get(library_id)
            if state:
                state.clients.discard(websocket)


scan_manager = ScanManager()
