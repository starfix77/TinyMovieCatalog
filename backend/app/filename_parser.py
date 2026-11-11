"""Parsing strictement limite au titre candidat et a l'annee depuis le nom."""
from dataclasses import dataclass
from pathlib import Path
import re

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".dvix"}
TECHNICAL_MARKERS = re.compile(
    r"(?i)(?:^|[\s._-])(?:"
    r"\d{3,4}p|4k|8k|x264|x265|h\.?264|h\.?265|hevc|av1|"
    r"ac3|eac3|dts(?:-hd)?|truehd|aac|flac|atmos|"
    r"bluray|bdrip|webrip|web-dl|hdtv|hdr10?\+?|hdr|"
    r"dolby[ ._-]?vision|proper|repack|remux|"
    r"multi|vff|vfq|vostfr|"
    r"\d{1,2}\.\d|8-bit|10-bit"
    r")(?:$|[\s._-])"
)
YEAR = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")

# Marqueurs d'episode / saison : S01E02, s1e2, 1x02, "Season 3", "Saison 3"...
EPISODE_MARKER = re.compile(
    r"(?i)(?:^|[\s._-])(?:s\d{1,2}[\s._-]?e\d{1,3}|\d{1,2}x\d{2,3}|(?:season|saison)[\s._-]?\d{1,2})(?=$|[\s._-]|e\d)"
)

# Prefixe numerique de classement en debut de nom ("01 ", "001 - ", "01.", "01_", "123 -") :
# un ou plusieurs chiffres suivis immediatement d'un separateur.
#  - separateur FORT : tiret (avec ou sans espaces) ou point -> "- " / "." ;
#    un point suivi d'un chiffre ("1.5 ...", "10.000 BC") n'est pas un separateur ;
#  - separateur FAIBLE : espace ou souligne "_" (le "_" remplace souvent l'espace dans
#    les noms de release : "12_Years_a_Slave_2013").
ORDER_PREFIX = re.compile(
    r"^(?P<num>\d+)(?:(?P<strong>\s*-\s*|\s*\.(?!\d)\s*)|(?P<weak>[\s_]+))"
)


def strip_order_prefix(stem: str) -> str:
    """Supprime le prefixe numerique de classement (et son separateur) en debut de nom.

    Retire le prefixe si :
      - le separateur est un tiret ou un point : "001 - Prometheus", "01. Prometheus",
        "12 - Prometheus", "01-Prometheus" ;
      - ou le nombre commence par un zero (numerotation "01", "001") quel que soit le
        separateur (espace, point, tiret ou souligne) : "01 Prometheus", "01_Prometheus".
    Un nombre SANS zero initial suivi d'un simple espace ou d'un souligne reste intact : il
    fait vraisemblablement partie du titre ("12 Years a Slave", "21 Jump Street",
    "28 Days Later", "2 Alien", "12_Years_a_Slave").

    Un seul prefixe est retire ("01 - 12 Monkeys" -> "12 Monkeys"). Les nombres situes
    ailleurs dans le nom ("Alien 3 (1992)") sont conserves. Si le suffixe restant ne
    contient aucune lettre ("1917 (2019)"), le nom est laisse tel quel : il n'y aurait
    plus de titre a identifier.
    """
    match = ORDER_PREFIX.match(stem)
    if not match:
        return stem
    if match.group("weak") and not match.group("num").startswith("0"):
        return stem
    rest = stem[match.end():]
    if not any(ch.isalpha() for ch in rest):
        return stem
    return rest


@dataclass(frozen=True)
class ParsedName:
    title: str
    year: int | None
    ambiguous_year: bool = False

def _stem_of(name: str) -> str:
    return Path(name).stem if Path(name).suffix.lower() in VIDEO_EXTENSIONS else Path(name).name


def parse_name(name: str, strip_order: bool = False) -> ParsedName:
    """Extrait titre/annee. Aucun champ technique n'est produit.

    strip_order=True : le prefixe numerique de classement ("01 ", "001 - ", "01.",
    "01_") est ignore avant toute analyse (voir strip_order_prefix). Le scanner ne
    l'active que si le dossier contient PLUSIEURS fichiers video : un fichier seul n'a
    aucun ordre a respecter, son nom est donc laisse intact."""
    stem = _stem_of(name).strip()
    return _parse_stem(strip_order_prefix(stem) if strip_order else stem)


def _parse_stem(stem: str) -> ParsedName:
    """Parsing d'un nom deja depouille de son extension et de son prefixe de classement."""
    stem = stem.strip()
    years = list(YEAR.finditer(stem))
    plausible = [m for m in years if 1870 <= int(m.group(1)) <= 2099]
    year = int(plausible[0].group(1)) if plausible else None
    ambiguous = len({m.group(1) for m in plausible}) > 1
    cut = plausible[0].start() if plausible else len(stem)
    candidate = stem[:cut]
    # Drop a recognized technical suffix even when year is absent.
    marker = TECHNICAL_MARKERS.search(candidate)
    if marker:
        candidate = candidate[:marker.start()]
    candidate = re.sub(r"[\s._-]+", " ", candidate).strip(" -_.()[]")
    return ParsedName(candidate or stem, None if ambiguous else year, ambiguous)


def parse_tv_name(name: str, strip_order: bool = False) -> ParsedName:
    """Meme principe que parse_name, pour une serie : le titre s'arrete au
    marqueur d'episode (S01E02, 1x02, Saison 2...) et l'annee est celle du
    titre de la serie (annee de premiere diffusion)."""
    stem = _stem_of(name).strip()
    if strip_order:
        stem = strip_order_prefix(stem)
    marker = EPISODE_MARKER.search(stem)
    if marker:
        stem = stem[:marker.start()]
    return _parse_stem(stem)
