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

@dataclass(frozen=True)
class ParsedName:
    title: str
    year: int | None
    ambiguous_year: bool = False

def parse_name(name: str) -> ParsedName:
    """Extrait titre/annee. Aucun champ technique n'est produit."""
    stem = Path(name).stem if Path(name).suffix.lower() in VIDEO_EXTENSIONS else Path(name).name
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
