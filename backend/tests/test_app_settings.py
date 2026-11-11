"""Parametres du fichier backend/.env exposes en lecture seule (boite « Configuration »)."""
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.settings_info import describe_settings, mask_secret


def _by_name(result):
    return {item.name: item for item in result.items}


def test_mask_secret():
    assert mask_secret("") == ""
    assert mask_secret("abcd") == "••••••••"
    assert mask_secret("0123456789abcdef") == "••••••••cdef"


def test_all_known_parameters_are_listed(tmp_path, monkeypatch):
    for name in ("TMDB_API_KEY", "TMDB_LANGUAGE", "FFPROBE_PATH", "FFPLAY_PATH", "SCAN_MAX_DEPTH"):
        monkeypatch.delenv(name, raising=False)
    env = tmp_path / ".env"
    env.write_text("TMDB_API_KEY=supersecretkey1234\nTMDB_LANGUAGE=en-US\n", encoding="utf-8")
    result = describe_settings(Settings(_env_file=str(env)), env)
    items = _by_name(result)

    # Tous les champs de Settings sont presents, avec une description.
    assert set(items) == {f.upper() for f in Settings.model_fields}
    assert all(item.description for item in items.values())
    assert result.env_file_exists is True

    assert items["TMDB_LANGUAGE"].value == "en-US"
    assert items["TMDB_LANGUAGE"].source == "env_file"
    assert items["FFPROBE_PATH"].source == "default"
    assert items["VIDEO_EXTENSIONS"].value.startswith(".mkv, .mp4")


def test_secret_is_never_returned_in_clear(tmp_path, monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("TMDB_API_KEY=supersecretkey1234\nMY_TOKEN=abcdef123456\n", encoding="utf-8")
    result = describe_settings(Settings(_env_file=str(env)), env)
    items = _by_name(result)

    assert items["TMDB_API_KEY"].secret is True
    assert items["TMDB_API_KEY"].value == "••••••••1234"
    assert "supersecretkey" not in result.model_dump_json()
    assert "abcdef123456" not in result.model_dump_json()
    # Cle inconnue mais secrete : masquee aussi.
    assert items["MY_TOKEN"].known is False
    assert items["MY_TOKEN"].secret is True


def test_unknown_keys_and_missing_file(tmp_path, monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("# commentaire\nTMDB_LANGUAG=fr-FR\n", encoding="utf-8")
    result = describe_settings(Settings(_env_file=str(env)), env)
    unknown = [i for i in result.items if not i.known]
    assert [i.name for i in unknown] == ["TMDB_LANGUAG"]

    missing = tmp_path / "absent.env"
    result = describe_settings(Settings(_env_file=str(missing)), missing)
    assert result.env_file_exists is False
    assert all(i.known for i in result.items)


def test_environment_variable_has_priority(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("TMDB_LANGUAGE=en-US\n", encoding="utf-8")
    monkeypatch.setenv("TMDB_LANGUAGE", "de-DE")
    result = describe_settings(Settings(_env_file=str(env)), env)
    item = _by_name(result)["TMDB_LANGUAGE"]
    assert item.value == "de-DE"
    assert item.source == "environment"


def test_endpoint():
    r = TestClient(app).get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert {"env_file", "env_file_exists", "items"} <= set(body)
    names = [i["name"] for i in body["items"]]
    assert "TMDB_API_KEY" in names and "FFPLAY_PATH" in names
