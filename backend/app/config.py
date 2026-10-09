"""
Configuration de l'application.

Toutes les valeurs peuvent etre surchargees via un fichier .env place a la
racine du dossier backend/ (voir .env.example).
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du backend (dossier contenant app/, data/, requirements.txt, ...)
BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_ROOT / ".env"), extra="ignore")

    # Cle API TheMovieDB (https://www.themoviedb.org/settings/api)
    tmdb_api_key: str = ""
    tmdb_language: str = "fr-FR"

    # Chemin vers l'executable ffprobe (fourni avec ffmpeg). Sur Windows,
    # peut etre "C:\\ffmpeg\\bin\\ffprobe.exe" si ffprobe n'est pas dans le PATH.
    ffprobe_path: str = "ffprobe"

    # Chemin vers l'executable ffplay (lecture des films). Si laisse a "ffplay"
    # et que FFPROBE_PATH contient un dossier, ffplay est cherche dans le meme dossier.
    ffplay_path: str = "ffplay"

    # Dossier commun de donnees (affiches/vignettes) partage par toutes les
    # bibliotheques, + base SQLite.
    data_dir: Path = BACKEND_ROOT / "data"

    # Nombre max d'acteurs stockes par film
    max_cast: int = 12

    # Extensions video reconnues comme "fichier principal" d'un dossier film
    video_extensions: tuple = (".mkv", ".mp4", ".avi", ".m4v")
    subtitle_extensions: tuple = (".srt", ".ass", ".ssa", ".sub", ".vtt")

    @property
    def ffplay_executable(self) -> str:
        if self.ffplay_path == "ffplay":
            probe = Path(self.ffprobe_path)
            if probe.parent != Path("."):
                suffix = probe.suffix
                return str(probe.parent / f"ffplay{suffix}")
        return self.ffplay_path

    @property
    def thumbnails_dir(self) -> Path:
        p = self.data_dir / "thumbnails"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        p = self.data_dir / "db"
        p.mkdir(parents=True, exist_ok=True)
        return p / "library.db"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
