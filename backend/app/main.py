from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import settings
from app.routers import libraries, movies

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

# Sert directement les vignettes en statique (alternative a /api/movies/{id}/poster)
app.mount("/data/thumbnails", StaticFiles(directory=str(settings.thumbnails_dir)), name="thumbnails")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
