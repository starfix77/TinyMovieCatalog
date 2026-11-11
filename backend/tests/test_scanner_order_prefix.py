"""Le prefixe numerique de classement n'est ignore que si le dossier contient
plusieurs fichiers video (integration : vraie arborescence + scan_library)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models, scanner  # noqa: F401
from app.database import Base
from app.models import Library


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _scan_titles(db, monkeypatch, root, media_type="movie", **kwargs):
    """Lance scan_library et retourne {nom de fichier: titre identifie}."""
    found = {}

    def fake_sync(db_, library, video_path, folder, title, year, errors, compare_mode, journal):
        found[video_path.name] = title
        return None, False

    monkeypatch.setattr(scanner, "_sync_candidate", fake_sync)
    library = Library(name="t", root_path=str(root), media_type=media_type)
    db.add(library)
    db.commit()
    scanner.scan_library(db, library, **kwargs)
    return found


def _touch(root, *relative_paths):
    for rel in relative_paths:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")


def test_count_video_files(tmp_path):
    _touch(tmp_path, "a.mkv", "b.MP4", "c.srt", "d.nfo")
    (tmp_path / "sub").mkdir()
    assert scanner.count_video_files(list(tmp_path.iterdir())) == 2


def test_several_files_in_folder_prefix_is_ignored(db, monkeypatch, tmp_path):
    _touch(tmp_path, "Alien Saga/01 Prometheus.mkv", "Alien Saga/002 - Alien.mkv",
           "Alien Saga/03. Aliens.mp4", "Alien Saga/04_Alien 3.mkv")
    found = _scan_titles(db, monkeypatch, tmp_path)
    assert found == {
        "01 Prometheus.mkv": "Prometheus",
        "002 - Alien.mkv": "Alien",
        "03. Aliens.mp4": "Aliens",
        "04_Alien 3.mkv": "Alien 3",
    }


def test_single_file_in_folder_prefix_is_kept(db, monkeypatch, tmp_path):
    _touch(tmp_path, "Solo/01 Prometheus.mkv")
    found = _scan_titles(db, monkeypatch, tmp_path)
    assert found == {"01 Prometheus.mkv": "01 Prometheus"}


def test_subtitles_and_other_files_do_not_count(db, monkeypatch, tmp_path):
    _touch(tmp_path, "Solo/01 Prometheus.mkv", "Solo/01 Prometheus.srt", "Solo/info.nfo")
    found = _scan_titles(db, monkeypatch, tmp_path)
    assert found == {"01 Prometheus.mkv": "01 Prometheus"}


def test_rule_is_evaluated_per_folder(db, monkeypatch, tmp_path):
    _touch(tmp_path, "Saga/01 Prometheus.mkv", "Saga/02 Alien.mkv", "Solo/01 Dune.mkv")
    found = _scan_titles(db, monkeypatch, tmp_path)
    assert found == {"01 Prometheus.mkv": "Prometheus", "02 Alien.mkv": "Alien",
                     "01 Dune.mkv": "01 Dune"}


def test_files_at_library_root(db, monkeypatch, tmp_path):
    _touch(tmp_path, "01 Prometheus.mkv", "02 Alien.mkv")
    found = _scan_titles(db, monkeypatch, tmp_path)
    assert found == {"01 Prometheus.mkv": "Prometheus", "02 Alien.mkv": "Alien"}


def test_title_numbers_survive_even_in_multi_file_folder(db, monkeypatch, tmp_path):
    _touch(tmp_path, "Mix/12 Years a Slave (2013).mkv", "Mix/01 Prometheus.mkv")
    found = _scan_titles(db, monkeypatch, tmp_path)
    assert found["12 Years a Slave (2013).mkv"] == "12 Years a Slave"
    assert found["01 Prometheus.mkv"] == "Prometheus"


def test_tv_library_root_files(db, monkeypatch, tmp_path):
    _touch(tmp_path, "01 - Breaking.Bad.S01E01.mkv", "01 - Breaking.Bad.S01E02.mkv")
    found = _scan_titles(db, monkeypatch, tmp_path, media_type="tv")
    assert set(found.values()) == {"Breaking Bad"}

    single = tmp_path / "single"
    _touch(single, "01 - Dark.S01E01.mkv")
    found = _scan_titles(db, monkeypatch, single, media_type="tv")
    assert found == {"01 - Dark.S01E01.mkv": "01 Dark"}
