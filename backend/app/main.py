from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import threading

from app.database import init_db, SessionLocal
from app.scanner import backfill_vote_averages
from app.config import settings
from app.routers import libraries, movies, sagas, actors, tmdb_info

app = FastAPI(
    title="TinyMovieCatalog Library Manager API",
    description="API locale pour gerer des bibliotheques de films MKV/MP4.",
    version="1.0.0",
)

# Usage local uniquement : CORS ouvert pour simplifier le dev (Angular sur
# localhost:4200 -> API sur localhost:8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(libraries.router)
app.include_router(movies.router)
app.include_router(sagas.router)
app.include_router(actors.router)
app.include_router(tmdb_info.router)

# Sert directement les vignettes en statique (alternative a /api/movies/{id}/poster)
app.mount("/data/thumbnails", StaticFiles(directory=str(settings.thumbnails_dir)), name="thumbnails")


@app.on_event("startup")
def on_startup():
    init_db()
    # Recupere en arriere-plan la note TMDb des films qui n'en ont pas encore.
    threading.Thread(target=_backfill_votes, daemon=True).start()


def _backfill_votes():
    db = SessionLocal()
    try:
        backfill_vote_averages(db)
    except Exception:
        pass
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}
