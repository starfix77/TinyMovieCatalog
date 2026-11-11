"""
Description (lecture seule) des parametres du fichier backend/.env.

Alimente la boite de dialogue « Configuration » du frontend. Les parametres
sont lus une seule fois au demarrage du backend (objet `app.config.settings`) :
toute modification du fichier .env n'est prise en compte qu'apres un redemarrage.
"""
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import dotenv_values

from app.config import BACKEND_ROOT, Settings, settings as _settings
from app.schemas import SettingItem, SettingsOut

ENV_FILE: Path = BACKEND_ROOT / ".env"

# Description de chaque parametre connu (cle = nom du champ de `Settings`).
DESCRIPTIONS: Dict[str, str] = {
    "tmdb_api_key": "Clé API TheMovieDB (affiches et informations des films).",
    "tmdb_language": "Langue des métadonnées TMDb.",
    "ffprobe_path": "Chemin de l'exécutable ffprobe (analyse technique des vidéos).",
    "ffplay_path": "Chemin de l'exécutable ffplay (lecture via le bouton PLAY).",
    "data_dir": "Dossier de données (affiches, vignettes et base SQLite).",
    "max_cast": "Nombre maximum d'acteurs stockés par film.",
    "video_extensions": "Extensions reconnues comme fichier vidéo principal.",
    "scan_max_depth": "Profondeur maximale de parcours des dossiers lors d'un scan.",
    "subtitle_extensions": "Extensions reconnues comme sous-titres externes.",
}

# Un nom contenant l'un de ces mots est considere comme secret : la valeur est masquee.
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD")


def is_secret(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in _SECRET_MARKERS)


def mask_secret(value: str) -> str:
    """Masque une valeur secrete en ne laissant visibles que ses 4 derniers caracteres.

    Une valeur vide reste vide (permet d'afficher « non renseigné »). Les valeurs
    courtes sont entierement masquees. Le backend n'envoie jamais le secret en clair :
    l'API est accessible sans authentification (CORS ouvert), meme en usage local.
    """
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    return "••••••••" + value[-4:]


def _to_text(value: Any) -> str:
    if isinstance(value, (tuple, list, set)):
        return ", ".join(str(v) for v in value)
    return "" if value is None else str(value)


def describe_settings(settings: Settings = _settings, env_file: Path = ENV_FILE) -> SettingsOut:
    """Liste tous les parametres connus + les cles supplementaires presentes dans le .env."""
    exists = env_file.is_file()
    file_values: Dict[str, str] = {}
    if exists:
        for key, val in dotenv_values(env_file).items():
            if key:
                file_values[key.upper()] = val if val is not None else ""

    items: List[SettingItem] = []
    known_names = set()

    for field in type(settings).model_fields:
        name = field.upper()
        known_names.add(name)
        secret = is_secret(name)
        text = _to_text(getattr(settings, field))
        if name in os.environ:
            source = "environment"
        elif name in file_values:
            source = "env_file"
        else:
            source = "default"
        items.append(
            SettingItem(
                name=name,
                value=mask_secret(text) if secret else text,
                description=DESCRIPTIONS.get(field, ""),
                source=source,
                known=True,
                secret=secret,
            )
        )

    # Cles presentes dans le .env mais ignorees par l'application (faute de frappe, ancien parametre...).
    for name, raw in file_values.items():
        if name in known_names:
            continue
        secret = is_secret(name)
        items.append(
            SettingItem(
                name=name,
                value=mask_secret(raw) if secret else raw,
                description="Paramètre non reconnu par l'application (ignoré).",
                source="env_file",
                known=False,
                secret=secret,
            )
        )

    return SettingsOut(env_file=str(env_file), env_file_exists=exists, items=items)
