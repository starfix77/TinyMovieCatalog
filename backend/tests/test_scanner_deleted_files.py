"""Un fichier / dossier supprime du disque est retire de la base au scan suivant."""
import shutil

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models, scanner  # noqa: F401
from app.database import Base
from app.models import Library, LibraryLogFile, Movie, VideoFile


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _add_movie(db, library, folder, name):
    movie = Movie(library_id=library.id, folder_name=folder.name, folder_path=str(folder),
                  title=name, year=2000)
    movie.video_files.append(VideoFile(filename=f"{name}.mkv", filepath=str(folder / f"{name}.mkv"),
                                       size_bytes=1))
    db.add(movie)
    db.commit()
    return movie


def _scan(db, monkeypatch, library):
    monkeypatch.setattr(scanner, "backfill_vote_averages", lambda *a, **k: [])
    monkeypatch.setattr(scanner, "_sync_candidate", lambda *a, **k: (None, False))
    return scanner.scan_library(db, library)


def test_deleted_folder_removes_movie_and_is_journaled(db, monkeypatch, tmp_path):
    keep, gone = tmp_path / "Keep (2000)", tmp_path / "Gone (2000)"
    for f, n in ((keep, "Keep"), (gone, "Gone")):
        f.mkdir()
        (f / f"{n}.mkv").write_bytes(b"x")
    library = Library(name="t", root_path=str(tmp_path), media_type="movie")
    db.add(library)
    db.commit()
    _add_movie(db, library, keep, "Keep")
    _add_movie(db, library, gone, "Gone")

    shutil.rmtree(gone)
    result = _scan(db, monkeypatch, library)

    assert result.movies_removed == 1
    assert [m.title for m in db.query(Movie).all()] == ["Keep"]
    assert db.query(VideoFile).count() == 1
    deleted = db.query(LibraryLogFile).filter_by(status="deleted").all()
    assert [d.movie_title for d in deleted] == ["Gone"]

    # Un second scan ne journalise plus rien et ne supprime rien d'autre.
    assert _scan(db, monkeypatch, library).movies_removed == 0
    assert db.query(LibraryLogFile).filter_by(status="deleted").count() == 1


def test_empty_root_deletes_nothing(db, monkeypatch, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    library = Library(name="t", root_path=str(root), media_type="movie")
    db.add(library)
    db.commit()
    _add_movie(db, library, root / "Gone (2000)", "Gone")

    result = _scan(db, monkeypatch, library)

    assert result.movies_removed == 0
    assert db.query(Movie).count() == 1
