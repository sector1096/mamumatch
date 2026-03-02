import re
import subprocess
from datetime import datetime

from app.core.config import settings


def normalize_duration_iso8601(raw: str | None) -> int | None:
    if not raw:
        return None
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    m = pattern.fullmatch(raw)
    if not m:
        return None
    h = int(m.group(1) or 0)
    m_ = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + m_ * 60 + s


def guess_language(text: str) -> str | None:
    lower = text.lower()
    if any(k in lower for k in ["espanol", "latam", "spanish", "cast"]):
        return "es"
    if any(k in lower for k in ["english", "eng", "na dota"]):
        return "en"
    if any(k in lower for k in ["pt", "portuguese", "br"]):
        return "pt"
    if any(k in lower for k in ["ru", "russian"]):
        return "ru"
    return None


def build_query(equipos: str | None, evento: str | None, anio: int | None) -> str:
    chunks = [equipos or "", evento or "", str(anio) if anio else "", "dota 2"]
    query = " ".join(part.strip() for part in chunks if part and part.strip())
    return query.strip() or "dota 2 full match"


def search_ytdlp(query: str, limit: int = 10) -> list[dict]:
    cmd = [
        settings.yt_dlp_path,
        f"ytsearch{limit}:{query}",
        "--print",
        "%(id)s\t%(title)s\t%(duration)s\t%(uploader)s",
        "--skip-download",
        "--no-warnings",
        "--ignore-config",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return []

    items = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 3)
        if len(parts) != 4:
            continue
        video_id, title, duration_raw, uploader = (p.strip() for p in parts)
        if not video_id:
            continue

        duration = None
        if duration_raw.isdigit():
            duration = int(duration_raw)
        elif duration_raw:
            duration = normalize_duration_iso8601(duration_raw)

        items.append(
            {
                "title": title,
                "channel": uploader,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration_seconds": duration,
                "language_guess": guess_language(f"{title} {uploader}"),
            }
        )

    return items


def find_video_candidates(equipos: str | None, evento: str | None, anio: int | None, limit: int = 10) -> dict:
    query = build_query(equipos, evento, anio)
    items = search_ytdlp(query, limit=limit)
    return {"query": query, "items": items[:limit], "generated_at": datetime.utcnow().isoformat()}
