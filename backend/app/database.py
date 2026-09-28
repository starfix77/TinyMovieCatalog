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
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "movies" not in inspector.get_table_names():
        return

    existing_columns = {c["name"] for c in inspector.get_columns("movies")}
    if "saga_id" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE movies ADD COLUMN saga_id INTEGER"))
