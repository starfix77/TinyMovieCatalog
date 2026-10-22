"""Aller-retour export -> import sur une base SQLite en memoire."""
import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import library_transfer as lt
from app.models import AudioTrack, Library, Movie, Saga, SagaMovie, Subtitle, VideoFile


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _populate(db):
    lib = Library(name="Films", root_path="/mnt/films", media_type="movie")
    db.add(lib)
    db.flush()
    saga = Saga(tmdb_collection_id=10, name="Saga X", poster_filename="saga_10.jpg")
    db.add(saga)
    db.flush()
    db.add(SagaMovie(saga_id=saga.id, tmdb_movie_id=1, title="X1", order_index=0, poster_filename="tmdb_1.jpg"))
    movie = Movie(library_id=lib.id, folder_name="X1 (2000)", folder_path="/mnt/films/X1 (2000)",
                  title="X1", year=2000, tmdb_id=1, poster_filename="tmdb_1.jpg", saga_id=saga.id,
                  rating_perso=3.5, cast='[{"name": "A"}]', tmdb_synced_at=datetime(2024, 1, 2, 3, 4, 5))
    db.add(movie)
    db.flush()
    video = VideoFile(movie_id=movie.id, filename="x1.mkv", filepath="/mnt/films/X1 (2000)/x1.mkv",
                      size_bytes=123456, width=1920, height=1080)
    db.add(video)
    db.flush()
    db.add(AudioTrack(video_file_id=video.id, track_index=0, language="fra", codec="ac3", channels=6))
    db.add(Subtitle(movie_id=movie.id, filename="x1.fr.srt", filepath="/mnt/films/X1 (2000)/x1.fr.srt",
                    language_guess="fr"))
    db.commit()
    return lib


def test_round_trip(db):
    lib = _populate(db)
    exported = json.loads(json.dumps(lt.export_library(db, lib)))  # passe par du vrai JSON
    assert exported["format"] == lt.FORMAT_NAME and len(exported["movies"]) == 1

    new_lib, stats = lt.import_library(db, exported, name="Copie", root_path="D:\\Films")
    assert stats == {"movies_imported": 1, "sagas_imported": 1}
    movie = db.query(Movie).filter(Movie.library_id == new_lib.id).one()
    assert movie.rating_perso == 3.5 and movie.saga.tmdb_collection_id == 10
    assert movie.tmdb_synced_at == datetime(2024, 1, 2, 3, 4, 5)
    assert movie.folder_path == "D:\\Films\\X1 (2000)"
    assert movie.video_files[0].filepath == "D:\\Films\\X1 (2000)\\x1.mkv"
    assert movie.video_files[0].audio_tracks[0].channels == 6
    assert movie.subtitles[0].language_guess == "fr"
    # La saga existante est reutilisee, pas dupliquee.
    assert db.query(Saga).count() == 1 and db.query(SagaMovie).count() == 1


def test_conflict_and_invalid(db):
    lib = _populate(db)
    exported = lt.export_library(db, lib)
    with pytest.raises(lt.ImportConflictError):
        lt.import_library(db, exported)  # meme dossier racine
    with pytest.raises(lt.ImportFormatError):
        lt.import_library(db, {"format": "autre"})
    exported["version"] = 99
    with pytest.raises(lt.ImportFormatError):
        lt.import_library(db, exported, root_path="/ailleurs")


def test_unsafe_poster_name_is_dropped(db):
    lib = _populate(db)
    exported = lt.export_library(db, lib)
    exported["movies"][0]["poster_filename"] = "../../evil.jpg"
    new_lib, _ = lt.import_library(db, exported, root_path="/autre")
    movie = db.query(Movie).filter(Movie.library_id == new_lib.id).one()
    assert movie.poster_filename is None
