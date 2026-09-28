"""
Utilitaires d'analyse video via ffprobe (fourni avec FFmpeg).

ffprobe doit etre installe et accessible (soit dans le PATH, soit via le
chemin configure dans app.config.settings.ffprobe_path).
"""
import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings


class FFprobeNotFoundError(RuntimeError):
    pass


@dataclass
class AudioTrackInfo:
    index: int
    language: Optional[str]
    title: Optional[str]
    codec: Optional[str]
    channels: Optional[int]
    bitrate: Optional[int]


@dataclass
class VideoProbeResult:
    container: Optional[str] = None
    duration_sec: Optional[float] = None
    video_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    video_bitrate: Optional[int] = None
    audio_tracks: list = field(default_factory=list)  # list[AudioTrackInfo]


def probe_file(filepath: str) -> VideoProbeResult:
    """Lance ffprobe sur le fichier et retourne les infos video/audio."""
    cmd = [
        settings.ffprobe_path,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        filepath,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, check=False
        )
    except FileNotFoundError as exc:
        raise FFprobeNotFoundError(
            f"ffprobe introuvable ('{settings.ffprobe_path}'). "
            "Installez FFmpeg et/ou configurez FFPROBE_PATH dans le .env."
        ) from exc

    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe a echoue sur {filepath}: {proc.stderr.strip()}")

    data = json.loads(proc.stdout or "{}")
    result = VideoProbeResult()

    fmt = data.get("format", {})
    result.container = fmt.get("format_name")
    if fmt.get("duration"):
        try:
            result.duration_sec = float(fmt["duration"])
        except ValueError:
            pass

    audio_index = 0
    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and result.video_codec is None:
            # ignore les flux video de type "mjpeg"/image (souvent la cover embarquee)
            if stream.get("codec_name") in ("mjpeg", "png", "bmp"):
                continue
            result.video_codec = stream.get("codec_name")
            result.width = stream.get("width")
            result.height = stream.get("height")
            br = stream.get("bit_rate")
            result.video_bitrate = int(br) if br else None
        elif codec_type == "audio":
            tags = stream.get("tags", {}) or {}
            br = stream.get("bit_rate")
            result.audio_tracks.append(
                AudioTrackInfo(
                    index=audio_index,
                    language=tags.get("language"),
                    title=tags.get("title"),
                    codec=stream.get("codec_name"),
                    channels=stream.get("channels"),
                    bitrate=int(br) if br else None,
                )
            )
            audio_index += 1

    # Bitrate video absent au niveau du flux (frequent en MKV) -> estimation
    # a partir du bitrate global du conteneur moins l'audio.
    if result.video_bitrate is None and fmt.get("bit_rate"):
        try:
            total_bitrate = int(fmt["bit_rate"])
            audio_total = sum(t.bitrate or 0 for t in result.audio_tracks)
            estimated = total_bitrate - audio_total
            result.video_bitrate = estimated if estimated > 0 else total_bitrate
        except ValueError:
            pass

    return result
