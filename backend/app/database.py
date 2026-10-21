from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# check_same_thread=False : necessaire car FastAPI peut utiliser plusieurs
# threads pour traiter les requetes (SQLite + un seul fichier local).
engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401 (assure l'enregistrement des modeles)
    Base.metadata.create_all(bind=engine)
    _run_light_migrations()


def _run_light_migrations():
    """SQLite + pas d'Alembic ici : create_all() cree les nouvelles tables
    mais n'ajoute pas de colonnes sur une table existante. On complete donc
    a la main les quelques colonnes ajoutees apres la premiere version du
    schema, pour ne pas casser une base library.db deja peuplee."""
    from sqlalchemy import Integer, inspect, text

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "movies" in tables:
        existing_columns = {c["name"] for c in inspector.get_columns("movies")}
        if "saga_id" not in existing_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE movies ADD COLUMN saga_id INTEGER"))
        if "vote_average" not in existing_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE movies ADD COLUMN vote_average FLOAT"))
        if "rating_perso" not in existing_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE movies ADD COLUMN rating_perso FLOAT NOT NULL DEFAULT 0"))

    if "video_files" in tables:
        existing_video_columns = {c["name"] for c in inspector.get_columns("video_files")}
        additions = {
            "frame_rate": "VARCHAR",
            "color_depth": "INTEGER",
            "hdr_info": "TEXT",
            "stream_metadata_json": "TEXT",
            "ffprobe_status": "VARCHAR",
            "ffprobe_error": "TEXT",
        }
        with engine.begin() as conn:
            for column, sql_type in additions.items():
                if column not in existing_video_columns:
                    conn.execute(text(f"ALTER TABLE video_files ADD COLUMN {column} {sql_type}"))

    if "libraries" in tables:
        existing = {c["name"]: c["type"] for c in inspector.get_columns("libraries")}
        if "media_type" not in existing:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE libraries ADD COLUMN media_type VARCHAR NOT NULL DEFAULT 'movie'"))
        for column in ("fs_total_size", "fs_free_size"):
            if column in existing and not isinstance(existing[column], Integer):
                # Version precedente : la colonne stockait un texte formate
                # ("1.82 TB"). Ces valeurs sont recalculables a tout moment
                # depuis le disque : on recree donc la colonne en BIGINT.
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE libraries DROP COLUMN {column}"))
                del existing[column]
            if column not in existing:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE libraries ADD COLUMN {column} BIGINT"))
