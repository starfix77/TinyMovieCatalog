from fastapi import APIRouter

from app.schemas import SettingsOut
from app.settings_info import describe_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings():
    """Parametres du fichier backend/.env (lecture seule, secrets masques).

    Les valeurs sont celles chargees au demarrage du backend : une modification du
    fichier .env n'est prise en compte qu'apres un redemarrage.
    """
    return describe_settings()
