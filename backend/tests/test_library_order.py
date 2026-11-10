"""Ordre d'affichage personnalise des bibliotheques (glisser-deposer)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app), tmp_path
    app.dependency_overrides.clear()


def _create(c, tmp_path, name):
    folder = tmp_path / name
    folder.mkdir()
    r = c.post("/api/libraries", json={"name": name, "root_path": str(folder), "media_type": "movie"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _ids(c):
    return [lib["id"] for lib in c.get("/api/libraries").json()]


def test_new_library_is_last_even_if_alphabetically_first(client):
    c, tmp = client
    z = _create(c, tmp, "Zebre")
    a = _create(c, tmp, "Alpha")
    assert _ids(c) == [z, a]


def test_reorder_and_persist(client):
    c, tmp = client
    a, b, d = (_create(c, tmp, n) for n in ("A", "B", "C"))
    r = c.put("/api/libraries/order", json={"ids": [d, a, b]})
    assert r.status_code == 200
    assert [x["id"] for x in r.json()] == [d, a, b]
    assert _ids(c) == [d, a, b]


def test_delete_preserves_order_and_new_goes_last(client):
    c, tmp = client
    a, b, d = (_create(c, tmp, n) for n in ("A", "B", "C"))
    c.put("/api/libraries/order", json={"ids": [d, a, b]})
    assert c.delete(f"/api/libraries/{a}").status_code == 204
    assert _ids(c) == [d, b]
    e = _create(c, tmp, "E")
    assert _ids(c) == [d, b, e]


def test_reorder_ignores_unknown_and_appends_missing(client):
    c, tmp = client
    a, b, d = (_create(c, tmp, n) for n in ("A", "B", "C"))
    c.put("/api/libraries/order", json={"ids": [d, 9999, d, a]})
    assert _ids(c) == [d, a, b]


def test_migration_initialises_from_alphabetical_order(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:  # ancienne base sans sort_order
        conn.execute(text("CREATE TABLE libraries (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, "
                          "root_path VARCHAR NOT NULL, created_at DATETIME, last_scanned_at DATETIME, "
                          "media_type VARCHAR NOT NULL DEFAULT 'movie', fs_total_size BIGINT, fs_free_size BIGINT)"))
        conn.execute(text("INSERT INTO libraries (id, name, root_path) VALUES (1,'zeta','/z'),(2,'Alpha','/a'),(3,'beta','/b')"))
    monkeypatch.setattr(database, "engine", engine)
    database._run_light_migrations()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT name FROM libraries ORDER BY sort_order")).fetchall()
    assert [r[0] for r in rows] == ["Alpha", "beta", "zeta"]
    database._run_light_migrations()  # idempotent
